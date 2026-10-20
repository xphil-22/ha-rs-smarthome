#!/usr/bin/env python3
"""Minimal RS-SmartHome CLI for testing the API outside Home Assistant.

Needs only `pip install cryptography`. Credentials come from the environment:

    export RS_USER=you@example.com RS_PASS=secret
    ./rs_cli.py list
    ./rs_cli.py on  <MAC>
    ./rs_cli.py off <MAC>
"""

import base64
import http.cookiejar
import json
import os
import sys
import urllib.request

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

URL = "https://service.rs-smarthome.com:8433/AppService.asmx/Execute"
KEY, IV = b"YAOb+cjChf34qxWZ", b"VG9x1XfbCQZgDFf1"

opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def encrypt(obj):
    padder = padding.PKCS7(128).padder()
    data = padder.update(json.dumps(obj, separators=(",", ":")).encode()) + padder.finalize()
    enc = Cipher(algorithms.AES(KEY), modes.CBC(IV)).encryptor()
    return base64.b64encode(enc.update(data) + enc.finalize()).decode()


def decrypt(value):
    dec = Cipher(algorithms.AES(KEY), modes.CBC(IV)).decryptor()
    raw = dec.update(base64.b64decode(value)) + dec.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return json.loads(unpadder.update(raw) + unpadder.finalize())


def call(code, value):
    body = json.dumps({"code": code, "value": encrypt(value)}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json", "Accept": "application/json"})
    with opener.open(req, timeout=30) as resp:
        return decrypt(json.loads(resp.read())["d"])


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("list", "on", "off"):
        sys.exit(__doc__)
    login = call(21001, {"loginname": os.environ["RS_USER"], "password": os.environ["RS_PASS"], "type": 2001,
                         "token": "", "CustomerID": 1, "Language": 49, "AppVersion": "5.7"})
    if login.get("Result") != 1:
        sys.exit(f"Login failed: {login}")
    devices = call(21101, login["Data"]["AccountID"]).get("Data") or []

    if sys.argv[1] == "list":
        for d in devices:
            state = "on" if d.get("PowerState") == 1 else "off"
            online = "online" if d.get("IsOnline") else "offline"
            print(f"{d['Mac']}  {state:3}  {online:7}  type={d.get('Type')}  {d.get('Name')}")
        return

    dev = next((d for d in devices if d["Mac"].lower() == sys.argv[2].lower()), None)
    if dev is None:
        sys.exit("Unknown MAC")
    code, data = 21190, {"id": dev["ID"], "mac": dev["Mac"], "cmd": 1 if sys.argv[1] == "on" else 2}
    if dev.get("Type") in (7, 8):
        code, data["index"] = 21401, 0
    print(call(code, data))


if __name__ == "__main__":
    main()
