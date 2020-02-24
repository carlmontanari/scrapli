import os

host = os.getenv("SCRAPLI_SMOKE_HOST", None)
port = os.getenv("SCRAPLI_SMOKE_PORT", None)
user = os.getenv("SCRAPLI_SMOKE_USER", None)
password = os.getenv("SCRAPLI_SMOKE_PASS", None)

device = {
    "host": host or "172.31.254.1",
    "port": port or 22,
    "auth_username": user or "scrapli",
    "auth_password": password or "scrapli",
    "auth_strict_key": False,
    "transport": "system",
    "keepalive": True,
    "keepalive_interval": 1,
}
