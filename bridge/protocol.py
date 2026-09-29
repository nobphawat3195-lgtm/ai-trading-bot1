"""Wire protocol shared by the backend and XAU_ControlBridge.mq5.

EA -> server: JSON body, authenticated with headers
    X-Account: <login>
    X-Ts:      <unix seconds, GMT>
    X-Nonce:   <random string, unique per request>
    X-Sig:     hex(HMAC-SHA256(secret, ts + "\n" + nonce + "\n" + body))

server -> EA: plain text, one directive per line (MQL5 has no JSON parser):
    OK <server_ts>
    CFG <version> key=value|key=value|...
    CMD <id> <PAUSE|RESUME|CLOSE_ALL>
    SIG <hex(HMAC-SHA256(secret, every line above joined with "\n"))>
The EA must reject a response whose SIG does not verify.
"""
import hashlib
import hmac

MAX_CLOCK_SKEW_SEC = 120
COMMAND_TYPES = ("PAUSE", "RESUME", "CLOSE_ALL")


def sign(secret: str, message: str) -> str:
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


def request_message(ts: str, nonce: str, body: str) -> str:
    return f"{ts}\n{nonce}\n{body}"


def verify_request(secret: str, ts: str, nonce: str, body: str, sig: str) -> bool:
    return hmac.compare_digest(sign(secret, request_message(ts, nonce, body)), sig.lower())


def build_response(secret: str, server_ts: int, config: dict | None, commands: list[dict]) -> str:
    lines = [f"OK {server_ts}"]
    if config is not None:
        pairs = "|".join(f"{k}={v}" for k, v in sorted(config["values"].items()))
        lines.append(f"CFG {config['version']} {pairs}")
    for cmd in commands:
        lines.append(f"CMD {cmd['id']} {cmd['type']}")
    payload = "\n".join(lines)
    return payload + "\nSIG " + sign(secret, payload) + "\n"
