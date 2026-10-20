"""Client for the RS SmartHome cloud API."""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

import aiohttp
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .const import (
    AES_IV,
    AES_KEY,
    API_URL,
    APP_VERSION,
    CMD_OFF,
    CMD_ON,
    CODE_DEVICES,
    CODE_LOGIN,
    CODE_SWITCH,
    CODE_SWITCH_MULTI,
    CUSTOMER_ID,
    LANGUAGE_DE,
    RESULT_OK,
    RESULT_TOKEN_EXPIRED,
)

_LOGGER = logging.getLogger(__name__)


class RSError(Exception):
    """Generic API error."""


class RSAuthError(RSError):
    """Invalid credentials."""


def _encrypt(obj: Any) -> str:
    padder = padding.PKCS7(128).padder()
    data = padder.update(json.dumps(obj, separators=(",", ":")).encode()) + padder.finalize()
    enc = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV)).encryptor()
    return base64.b64encode(enc.update(data) + enc.finalize()).decode()


def _decrypt(value: str) -> Any:
    dec = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV)).decryptor()
    raw = dec.update(base64.b64decode(value)) + dec.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return json.loads(unpadder.update(raw) + unpadder.finalize())


class RSSmartHomeApi:
    """Talks to the RS SmartHome cloud like the Android app does."""

    def __init__(self, session: aiohttp.ClientSession, username: str, password: str) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._user: dict[str, Any] | None = None

    @property
    def account_id(self) -> Any:
        return self._user["AccountID"] if self._user else None

    async def _post(self, code: int, value: Any) -> dict[str, Any]:
        try:
            async with self._session.post(
                API_URL,
                json={"code": code, "value": _encrypt(value)},
                headers={"Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                resp.raise_for_status()
                body = json.loads(await resp.text())
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise RSError(f"Request {code} failed: {err}") from err
        try:
            return _decrypt(body["d"])
        except (KeyError, ValueError) as err:
            raise RSError(f"Cannot decode response for {code}") from err

    async def login(self) -> dict[str, Any]:
        res = await self._post(
            CODE_LOGIN,
            {
                "loginname": self._username,
                "password": self._password,
                "type": 2001,
                "token": "",
                "CustomerID": CUSTOMER_ID,
                "Language": LANGUAGE_DE,
                "AppVersion": APP_VERSION,
            },
        )
        if res.get("Result") != RESULT_OK or not res.get("Data"):
            raise RSAuthError("Login rejected")
        self._user = res["Data"]
        return self._user

    async def _execute(self, code: int, data: Any) -> dict[str, Any]:
        """Run a request, re-login and retry wrapped with the token on expiry (like the app)."""
        if self._user is None:
            await self.login()
        res = await self._post(code, data)
        if res.get("Result") == RESULT_TOKEN_EXPIRED:
            _LOGGER.debug("Session expired, logging in again")
            user = await self.login()
            res = await self._post(-code, {"token": json.dumps(user), "data": json.dumps(data)})
        if res.get("Result") != RESULT_OK:
            raise RSError(f"Request {code} returned {res.get('Result')}")
        return res

    async def get_devices(self) -> list[dict[str, Any]]:
        if self._user is None:
            await self.login()
        res = await self._execute(CODE_DEVICES, self.account_id)
        return res.get("Data") or []

    async def set_power(self, device: dict[str, Any], on: bool) -> None:
        code = CODE_SWITCH
        data: dict[str, Any] = {"id": device["ID"], "mac": device["Mac"], "cmd": CMD_ON if on else CMD_OFF}
        if device.get("Type") in (7, 8):
            code = CODE_SWITCH_MULTI
            data["index"] = 0
        await self._execute(code, data)
