"""Switch entities for RS SmartHome sockets."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import RSConfigEntry
from .api import RSError
from .const import DOMAIN, MANUFACTURER
from .coordinator import RSCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: RSConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    known: set[str] = set()

    @callback
    def _add_new() -> None:
        new = [mac for mac in coordinator.data if mac not in known]
        known.update(new)
        if new:
            async_add_entities(RSSwitch(coordinator, mac) for mac in new)

    _add_new()
    entry.async_on_unload(coordinator.async_add_listener(_add_new))


class RSSwitch(CoordinatorEntity[RSCoordinator], SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = SwitchDeviceClass.OUTLET

    def __init__(self, coordinator: RSCoordinator, mac: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        dev = coordinator.data[mac]
        self._attr_unique_id = f"{DOMAIN}_{mac}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            connections={(CONNECTION_NETWORK_MAC, mac.replace("-", ":").lower())},
            name=dev.get("Name") or mac,
            manufacturer=MANUFACTURER,
            model=f"Type {dev.get('Type')}",
        )

    @property
    def _dev(self) -> dict[str, Any] | None:
        return self.coordinator.data.get(self._mac)

    @property
    def available(self) -> bool:
        return super().available and self._dev is not None and bool(self._dev.get("IsOnline"))

    @property
    def is_on(self) -> bool | None:
        return self._dev.get("PowerState") == 1 if self._dev else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        dev = self._dev or {}
        return {"mac": self._mac, "rs_id": dev.get("ID"), "type": dev.get("Type"), "status": dev.get("Status")}

    async def _set(self, on: bool) -> None:
        try:
            await self.coordinator.api.set_power(self._dev, on)
        except RSError as err:
            raise HomeAssistantError(f"Schalten fehlgeschlagen: {err}") from err
        # Optimistic update; the cloud reflects the new state after a short delay
        self._dev["PowerState"] = 1 if on else 2
        self.async_write_ha_state()
        await asyncio.sleep(3)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)
