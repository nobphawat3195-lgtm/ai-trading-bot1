"""Control-plane backend for XAU_ControlBridge.mq5.

The EA owns every trading and risk decision. This service only stores telemetry,
serves a dashboard, and hands the EA versioned config and one-shot commands.
Run:  BRIDGE_SECRETS="12345678:long-random-secret" BRIDGE_ADMIN_TOKEN=... \
      uvicorn bridge.app:app --host 127.0.0.1 --port 8765
"""
import json
import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from bridge import protocol

ONLINE_WINDOW_SEC = 30
DEFAULT_COMMAND_TTL_SEC = 600

# Server-side bounds. The EA clamps again against its own hard inputs.
CONFIG_BOUNDS = {
    "trading_enabled": (0, 1),
    "risk_pct": (0.01, 2.0),
    "daily_loss_pct": (0.5, 10.0),
    "max_dd_pct": (1.0, 30.0),
    "max_positions": (1, 5),
    "max_spread_pts": (1, 200),
    "min_entry_gap_sec": (0, 3600),
}
DEFAULT_CONFIG = {
    "trading_enabled": 0,
    "risk_pct": 0.5,
    "daily_loss_pct": 3.0,
    "max_dd_pct": 10.0,
    "max_positions": 1,
    "max_spread_pts": 40,
    "min_entry_gap_sec": 60,
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS state (account TEXT PRIMARY KEY, body TEXT, updated_at INTEGER);
CREATE TABLE IF NOT EXISTS deals (
  account TEXT, ticket INTEGER, position_id INTEGER, symbol TEXT, type TEXT, entry TEXT,
  volume REAL, price REAL, profit REAL, commission REAL, swap REAL, time INTEGER,
  config_version INTEGER, PRIMARY KEY (account, ticket));
CREATE TABLE IF NOT EXISTS commands (
  id TEXT PRIMARY KEY, account TEXT, type TEXT, created_at INTEGER, expires_at INTEGER,
  delivered_at INTEGER, acked_at INTEGER, ok INTEGER, msg TEXT);
CREATE TABLE IF NOT EXISTS config (
  account TEXT, version INTEGER, body TEXT, created_at INTEGER, PRIMARY KEY (account, version));
CREATE TABLE IF NOT EXISTS nonces (account TEXT, nonce TEXT, ts INTEGER, PRIMARY KEY (account, nonce));
"""


class Deal(BaseModel):
    ticket: int
    position_id: int = 0
    symbol: str
    type: str
    entry: str
    volume: float
    price: float
    profit: float
    commission: float = 0.0
    swap: float = 0.0
    time: int
    config_version: int = 0


class Ack(BaseModel):
    id: str
    ok: bool
    msg: str = ""


class SyncBody(BaseModel):
    account: int
    deals: list[Deal] = Field(default_factory=list, max_length=200)
    acks: list[Ack] = Field(default_factory=list, max_length=100)
    config_version: int = 0
    model_config = {"extra": "allow"}  # balance/equity/positions/risk are stored as-is


class CommandIn(BaseModel):
    type: str
    ttl_sec: int = Field(DEFAULT_COMMAND_TTL_SEC, ge=10, le=3600)


def validate_config(values: dict) -> dict:
    unknown = set(values) - set(CONFIG_BOUNDS)
    if unknown:
        raise HTTPException(422, f"unknown config keys: {sorted(unknown)}")
    out = {}
    for key, (lo, hi) in CONFIG_BOUNDS.items():
        v = values.get(key, DEFAULT_CONFIG[key])
        if isinstance(v, bool):
            if key != "trading_enabled":
                raise HTTPException(422, f"{key} must be a number")
            v = int(v)
        if not isinstance(v, (int, float)):
            raise HTTPException(422, f"{key} must be a number")
        if not lo <= v <= hi:
            raise HTTPException(422, f"{key} must be within [{lo}, {hi}]")
        integer_key = isinstance(lo, int) and isinstance(hi, int)
        if integer_key and v != int(v):
            raise HTTPException(422, f"{key} must be an integer")
        out[key] = int(v) if integer_key else float(v)
    return out


def trade_stats(rows: list[sqlite3.Row]) -> dict:
    # Closed-trade P/L = profit + commission + swap on exit deals (entry OUT / INOUT / OUT_BY).
    pnl = [r["profit"] + r["commission"] + r["swap"] for r in rows if r["entry"] != "in"]
    wins = [p for p in pnl if p > 0]
    losses = [p for p in pnl if p < 0]
    gross_win, gross_loss = sum(wins), -sum(losses)
    return {
        "trades": len(pnl),
        "net": round(sum(pnl), 2),
        "win_rate_pct": round(100 * len(wins) / len(pnl), 1) if pnl else None,
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss > 0 else None,
        "avg_win": round(gross_win / len(wins), 2) if wins else None,
        "avg_loss": round(-gross_loss / len(losses), 2) if losses else None,
        "expectancy": round(sum(pnl) / len(pnl), 3) if pnl else None,
    }


def create_app(db_path: str, secrets: dict[str, str], admin_token: str) -> FastAPI:
    if not admin_token:
        raise RuntimeError("BRIDGE_ADMIN_TOKEN must be set")
    db = sqlite3.connect(db_path, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    lock = threading.Lock()
    app = FastAPI(title="XAU Control Bridge")

    def require_admin(authorization: str = Header("")):
        if not protocol.hmac.compare_digest(authorization, f"Bearer {admin_token}"):
            raise HTTPException(401, "bad admin token")

    def latest_config(account: str) -> dict:
        row = db.execute(
            "SELECT version, body FROM config WHERE account=? ORDER BY version DESC LIMIT 1", (account,)
        ).fetchone()
        if row is None:
            return {"version": 0, "values": dict(DEFAULT_CONFIG)}
        return {"version": row["version"], "values": json.loads(row["body"])}

    @app.post("/v1/ea/sync", response_class=PlainTextResponse)
    async def ea_sync(
        request: Request,
        x_account: str = Header(...),
        x_ts: str = Header(...),
        x_nonce: str = Header(..., min_length=8, max_length=64),
        x_sig: str = Header(...),
    ):
        secret = secrets.get(x_account)
        raw = (await request.body()).decode("utf-8")
        if secret is None or not protocol.verify_request(secret, x_ts, x_nonce, raw, x_sig):
            raise HTTPException(401, "bad signature")
        now = int(time.time())
        if not x_ts.isdigit() or abs(now - int(x_ts)) > protocol.MAX_CLOCK_SKEW_SEC:
            raise HTTPException(401, "stale timestamp")
        body = SyncBody.model_validate_json(raw)
        if str(body.account) != x_account:
            raise HTTPException(401, "account mismatch")

        with lock, db:
            db.execute("DELETE FROM nonces WHERE ts < ?", (now - 2 * protocol.MAX_CLOCK_SKEW_SEC,))
            try:
                db.execute("INSERT INTO nonces VALUES (?,?,?)", (x_account, x_nonce, now))
            except sqlite3.IntegrityError:
                raise HTTPException(401, "replayed nonce")
            db.execute("INSERT OR REPLACE INTO state VALUES (?,?,?)", (x_account, raw, now))
            for d in body.deals:  # idempotent: EA may resend after a failed round-trip
                db.execute(
                    "INSERT OR IGNORE INTO deals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (x_account, d.ticket, d.position_id, d.symbol, d.type, d.entry, d.volume,
                     d.price, d.profit, d.commission, d.swap, d.time, d.config_version),
                )
            for a in body.acks:
                db.execute(
                    "UPDATE commands SET acked_at=?, ok=?, msg=? WHERE id=? AND account=? AND acked_at IS NULL",
                    (now, int(a.ok), a.msg[:200], a.id, x_account),
                )
            pending = db.execute(
                "SELECT id, type FROM commands WHERE account=? AND acked_at IS NULL AND expires_at>=? "
                "ORDER BY created_at",
                (x_account, now),
            ).fetchall()
            if pending:
                db.execute(
                    f"UPDATE commands SET delivered_at=? WHERE id IN ({','.join('?' * len(pending))})",
                    (now, *[p["id"] for p in pending]),
                )
            cfg = latest_config(x_account)
        send_cfg = cfg if cfg["version"] != body.config_version else None
        return protocol.build_response(secret, now, send_cfg, [dict(p) for p in pending])

    @app.get("/v1/accounts", dependencies=[Depends(require_admin)])
    def list_accounts():
        now = int(time.time())
        rows = db.execute("SELECT account, updated_at FROM state").fetchall()
        known = {r["account"]: r["updated_at"] for r in rows}
        return [
            {"account": a, "last_sync": known.get(a), "online": now - known.get(a, 0) <= ONLINE_WINDOW_SEC}
            for a in sorted(secrets)
        ]

    @app.get("/v1/accounts/{account}/state", dependencies=[Depends(require_admin)])
    def get_state(account: str):
        row = db.execute("SELECT body, updated_at FROM state WHERE account=?", (account,)).fetchone()
        if row is None:
            raise HTTPException(404, "no state yet")
        age = int(time.time()) - row["updated_at"]
        return {"online": age <= ONLINE_WINDOW_SEC, "age_sec": age, "state": json.loads(row["body"])}

    @app.get("/v1/accounts/{account}/deals", dependencies=[Depends(require_admin)])
    def get_deals(account: str, limit: int = 200):
        rows = db.execute(
            "SELECT * FROM deals WHERE account=? ORDER BY time DESC, ticket DESC LIMIT ?",
            (account, min(limit, 2000)),
        ).fetchall()
        return [dict(r) for r in rows]

    @app.get("/v1/accounts/{account}/stats", dependencies=[Depends(require_admin)])
    def get_stats(account: str):
        rows = db.execute("SELECT * FROM deals WHERE account=?", (account,)).fetchall()
        return trade_stats(rows)

    @app.post("/v1/accounts/{account}/commands", dependencies=[Depends(require_admin)])
    def post_command(account: str, cmd: CommandIn):
        if account not in secrets:
            raise HTTPException(404, "unknown account")
        if cmd.type not in protocol.COMMAND_TYPES:
            raise HTTPException(422, f"type must be one of {protocol.COMMAND_TYPES}")
        now = int(time.time())
        cid = uuid.uuid4().hex[:16]
        with lock, db:
            db.execute(
                "INSERT INTO commands (id, account, type, created_at, expires_at) VALUES (?,?,?,?,?)",
                (cid, account, cmd.type, now, now + cmd.ttl_sec),
            )
        return {"id": cid, "type": cmd.type, "expires_at": now + cmd.ttl_sec}

    @app.get("/v1/accounts/{account}/commands", dependencies=[Depends(require_admin)])
    def get_commands(account: str, limit: int = 50):
        rows = db.execute(
            "SELECT * FROM commands WHERE account=? ORDER BY created_at DESC LIMIT ?", (account, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    @app.get("/v1/accounts/{account}/config", dependencies=[Depends(require_admin)])
    def get_config(account: str):
        return latest_config(account) | {"bounds": CONFIG_BOUNDS}

    @app.put("/v1/accounts/{account}/config", dependencies=[Depends(require_admin)])
    def put_config(account: str, values: dict):
        if account not in secrets:
            raise HTTPException(404, "unknown account")
        clean = validate_config(values)
        with lock, db:
            version = latest_config(account)["version"] + 1
            db.execute(
                "INSERT INTO config VALUES (?,?,?,?)", (account, version, json.dumps(clean), int(time.time()))
            )
        return {"version": version, "values": clean}

    @app.get("/")
    def dashboard():
        return FileResponse(Path(__file__).with_name("static") / "index.html")

    return app


def _secrets_from_env() -> dict[str, str]:
    pairs = [p for p in os.environ.get("BRIDGE_SECRETS", "").split(",") if p.strip()]
    out = {}
    for p in pairs:
        account, _, secret = p.partition(":")
        if len(secret) < 32:
            raise RuntimeError(f"secret for {account} must be >= 32 chars")
        out[account.strip()] = secret.strip()
    return out


if os.environ.get("BRIDGE_ADMIN_TOKEN"):
    app = create_app(
        os.environ.get("BRIDGE_DB", "bridge.db"), _secrets_from_env(), os.environ["BRIDGE_ADMIN_TOKEN"]
    )
