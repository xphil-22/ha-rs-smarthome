"""Polling coordinator for RS SmartHome."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RSAuthError, RSError, RSSmartHomeApi
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class RSCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetches all devices, keyed by MAC."""

    def __init__(self, hass: HomeAssistant, api: RSSmartHomeApi) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.api = api

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            devices = await self.api.get_devices()
        except RSAuthError as err:
            raise ConfigEntryAuthFailed from err
        except RSError as err:
            raise UpdateFailed(str(err)) from err
        return {d["Mac"]: d for d in devices if d.get("Mac")}
