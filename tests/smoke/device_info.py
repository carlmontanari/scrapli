import os

host = os.getenv("SCRAPLI_SMOKE_HOST", None)
port = os.getenv("SCRAPLI_SMOKE_PORT", None)
user = os.getenv("SCRAPLI_SMOKE_USER", None)
password = os.getenv("SCRAPLI_SMOKE_PASS", None)

iosxe_device = {
    "host": host or "172.18.0.11",
    "port": port or 22,
    "auth_username": user or "vrnetlab",
    "auth_password": password or "VR-netlab9",
    "auth_strict_key": False,
    "transport": "system",
    "keepalive": True,
    "keepalive_interval": 1,
}

nxos_device = {
    "host": "172.18.0.12",
    "port": 22,
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
    "transport": "system",
    "keepalive": True,
    "keepalive_interval": 1,
}

iosxr_device = {
    "host": "172.18.0.13",
    "port": 22,
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
    "transport": "system",
    "keepalive": True,
    "keepalive_interval": 1,
}

eos_device = {
    "host": "172.18.0.14",
    "port": 22,
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
    "transport": "system",
    "keepalive": True,
    "keepalive_interval": 1,
    "comms_ansi": True,
}

junos_device = {
    "host": "172.18.0.15",
    "port": 22,
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
    "transport": "system",
    "keepalive": True,
    "keepalive_interval": 1,
}
