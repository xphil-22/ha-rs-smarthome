"""RS SmartHome (Expertan / LUNVON / RisingSun) cloud integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import RSAuthError, RSError, RSSmartHomeApi
from .coordinator import RSCoordinator

PLATFORMS = [Platform.SWITCH]

type RSConfigEntry = ConfigEntry[RSCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: RSConfigEntry) -> bool:
    # Own session so the server's session cookie does not leak into other integrations
    api = RSSmartHomeApi(async_create_clientsession(hass), entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    try:
        await api.login()
    except RSAuthError as err:
        raise ConfigEntryAuthFailed from err
    except RSError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = RSCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RSConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
