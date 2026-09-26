import json
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from bridge import protocol
from bridge.app import create_app

ACC = "12345678"
SECRET = "s" * 40
ADMIN = {"Authorization": "Bearer admin-token"}


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(str(tmp_path / "t.db"), {ACC: SECRET}, "admin-token"))


def sync(client, body: dict, *, ts=None, nonce=None, secret=SECRET, account=ACC):
    raw = json.dumps(body)
    ts = str(int(time.time()) if ts is None else ts)
    nonce = nonce or uuid.uuid4().hex
    sig = protocol.sign(secret, protocol.request_message(ts, nonce, raw))
    headers = {"X-Account": account, "X-Ts": ts, "X-Nonce": nonce, "X-Sig": sig}
    return client.post("/v1/ea/sync", content=raw, headers=headers)


def parse(text: str) -> tuple[list[str], str]:
    lines = text.rstrip("\n").split("\n")
    assert lines[-1].startswith("SIG ")
    return lines[:-1], lines[-1][4:]


def deal(ticket, profit, entry="out"):
    return {"ticket": ticket, "symbol": "XAUUSD", "type": "sell", "entry": entry,
            "volume": 0.01, "price": 4270.0, "profit": profit, "time": 1_790_000_000 + ticket}


def test_hmac_matches_known_vector():
    # Same vector the EA self-test checks in OnInit.
    assert protocol.sign("key", "The quick brown fox jumps over the lazy dog") == (
        "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8"
    )


def test_sync_returns_signed_default_config(client):
    r = sync(client, {"account": int(ACC), "config_version": 0, "equity": 100})
    assert r.status_code == 200
    lines, sig = parse(r.text)
    assert sig == protocol.sign(SECRET, "\n".join(lines))
    assert lines[0].startswith("OK ")
    # Version 0 is the default and the EA already starts from it, so nothing is sent.
    assert not any(line.startswith("CFG") for line in lines)


def test_rejects_bad_signature_stale_ts_replay_and_account_mismatch(client):
    body = {"account": int(ACC)}
    assert sync(client, body, secret="x" * 40).status_code == 401
    assert sync(client, body, ts=int(time.time()) - 1000).status_code == 401
    assert sync(client, body, nonce="fixednonce1").status_code == 200
    assert sync(client, body, nonce="fixednonce1").status_code == 401
    assert sync(client, {"account": 999}).status_code == 401


def test_deals_are_idempotent_and_stats(client):
    body = {"account": int(ACC), "deals": [deal(1, 1.2), deal(2, -3.5), deal(3, 4.74), deal(4, 0, "in")]}
    assert sync(client, body).status_code == 200
    assert sync(client, body).status_code == 200  # resend after lost response
    assert len(client.get(f"/v1/accounts/{ACC}/deals", headers=ADMIN).json()) == 4
    stats = client.get(f"/v1/accounts/{ACC}/stats", headers=ADMIN).json()
    assert stats["trades"] == 3
    assert stats["net"] == 2.44
    assert stats["profit_factor"] == round(5.94 / 3.5, 2)


def test_command_delivered_until_acked_then_gone(client):
    cid = client.post(f"/v1/accounts/{ACC}/commands", json={"type": "CLOSE_ALL"}, headers=ADMIN).json()["id"]
    for _ in range(2):  # redelivered while unacked
        lines, _ = parse(sync(client, {"account": int(ACC)}).text)
        assert f"CMD {cid} CLOSE_ALL" in lines
    sync(client, {"account": int(ACC), "acks": [{"id": cid, "ok": True, "msg": "closed 2"}]})
    lines, _ = parse(sync(client, {"account": int(ACC)}).text)
    assert not any(line.startswith("CMD") for line in lines)
    cmd = client.get(f"/v1/accounts/{ACC}/commands", headers=ADMIN).json()[0]
    assert cmd["ok"] == 1 and cmd["msg"] == "closed 2"


def test_expired_command_is_not_delivered(client, monkeypatch):
    client.post(f"/v1/accounts/{ACC}/commands", json={"type": "PAUSE", "ttl_sec": 10}, headers=ADMIN)
    real = time.time
    monkeypatch.setattr(time, "time", lambda: real() + 60)
    lines, _ = parse(sync(client, {"account": int(ACC)}).text)
    assert not any(line.startswith("CMD") for line in lines)


def test_config_versioning_and_bounds(client):
    r = client.put(f"/v1/accounts/{ACC}/config", json={"risk_pct": 0.8, "trading_enabled": True}, headers=ADMIN)
    assert r.status_code == 200 and r.json()["version"] == 1
    lines, _ = parse(sync(client, {"account": int(ACC), "config_version": 0}).text)
    cfg = next(line for line in lines if line.startswith("CFG "))
    assert cfg.startswith("CFG 1 ") and "risk_pct=0.8" in cfg and "trading_enabled=1" in cfg
    lines, _ = parse(sync(client, {"account": int(ACC), "config_version": 1}).text)
    assert not any(line.startswith("CFG") for line in lines)

    for bad in ({"risk_pct": 5}, {"max_positions": 2.5}, {"lot": 1}, {"max_dd_pct": "10"}):
        assert client.put(f"/v1/accounts/{ACC}/config", json=bad, headers=ADMIN).status_code == 422


def test_admin_endpoints_require_token(client):
    assert client.get(f"/v1/accounts/{ACC}/deals").status_code == 401
    assert client.post(f"/v1/accounts/{ACC}/commands", json={"type": "PAUSE"}).status_code == 401
    assert client.post(f"/v1/accounts/{ACC}/commands", json={"type": "BUY"}, headers=ADMIN).status_code == 422
