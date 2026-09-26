"""Stand-in for XAU_ControlBridge.mq5 to exercise the backend without MT5.

Mirrors the EA side of the protocol: signs requests, verifies the response SIG,
applies CFG, executes and acks commands. Trades are fake.
    python -m bridge.ea_sim --url http://127.0.0.1:8765/v1/ea/sync --account 12345678 --secret ...
"""
import argparse
import json
import random
import time
import urllib.request
import uuid

from bridge import protocol


def run(url: str, account: int, secret: str, rounds: int, interval: float):
    cfg_version, acks, deals, next_ticket = 0, [], [], 1000
    balance, paused = 72.74, False
    for _ in range(rounds):
        if not paused and random.random() < 0.5:  # fake closed trade
            next_ticket += 2
            pnl = random.choice([0.2, 0.2, 1.2, -3.5, 4.7])
            balance += pnl
            now = int(time.time())
            deals += [
                {"ticket": next_ticket - 1, "position_id": next_ticket - 1, "symbol": "XAUUSD", "type": "sell",
                 "entry": "in", "volume": 0.01, "price": 4271.25, "profit": 0, "time": now - 60},
                {"ticket": next_ticket, "position_id": next_ticket - 1, "symbol": "XAUUSD", "type": "buy",
                 "entry": "out", "volume": 0.01, "price": 4271.25 - pnl, "profit": pnl, "time": now},
            ]
        body = json.dumps({
            "account": account, "server": "Exness-MT5Trial6", "ea_version": "sim", "config_version": cfg_version,
            "symbol": "XAUUSD", "balance": round(balance, 2), "equity": round(balance, 2), "spread_pts": 18,
            "positions": [], "deals": deals, "acks": acks,
            "risk": {"halted": False, "reason": "", "paused": paused, "offline": False,
                     "day_pnl": round(balance - 72.74, 2)},
        })
        ts, nonce = str(int(time.time())), uuid.uuid4().hex
        req = urllib.request.Request(url, data=body.encode(), method="POST", headers={
            "Content-Type": "application/json", "X-Account": str(account), "X-Ts": ts, "X-Nonce": nonce,
            "X-Sig": protocol.sign(secret, protocol.request_message(ts, nonce, body))})
        text = urllib.request.urlopen(req, timeout=5).read().decode()
        lines = text.rstrip("\n").split("\n")
        payload = "\n".join(lines[:-1])
        if lines[-1] != "SIG " + protocol.sign(secret, payload):
            raise SystemExit("response signature invalid")
        deals, acks = [], []
        for line in lines[1:-1]:
            if line.startswith("CFG "):
                cfg_version = int(line.split()[1])
                print("config", line)
            elif line.startswith("CMD "):
                _, cid, ctype = line.split()
                paused = ctype in ("PAUSE", "CLOSE_ALL")
                acks.append({"id": cid, "ok": True, "msg": f"sim {ctype.lower()}"})
                print("command", ctype)
        time.sleep(interval)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8765/v1/ea/sync")
    ap.add_argument("--account", type=int, required=True)
    ap.add_argument("--secret", required=True)
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--interval", type=float, default=1.0)
    a = ap.parse_args()
    run(a.url, a.account, a.secret, a.rounds, a.interval)
