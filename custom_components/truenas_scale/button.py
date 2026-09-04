"""Button platform for TrueNAS Scale 26 integration."""

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_APPS, DATA_SERVICES, DATA_SYSTEM_INFO, DATA_VMS, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TrueNAS Scale buttons."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = []

    # Service restart buttons
    services = coordinator.data.get(DATA_SERVICES, {})
    for service_name in services:
        entities.append(TrueNASServiceRestartButton(coordinator, entry, service_name))

    # App restart buttons
    apps = coordinator.data.get(DATA_APPS, {})
    for app_name in apps:
        entities.append(TrueNASAppRestartButton(coordinator, entry, app_name))

    # Virtual Machine restart buttons
    vms = coordinator.data.get(DATA_VMS, {})
    for vm_key, vm in vms.items():
        vm_name = vm.get("name") or vm_key
        vm_id = vm.get("id") or vm_key
        entities.append(TrueNASVMRestartButton(coordinator, entry, vm_key, vm_id, vm_name))

    async_add_entities(entities)


class TrueNASBaseButton(CoordinatorEntity, ButtonEntity):
    """Base class for TrueNAS buttons."""

    def __init__(self, coordinator, entry: ConfigEntry, key: str, name: str) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._key = key
        self._attr_name = name
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        sys_info = self.coordinator.data.get(DATA_SYSTEM_INFO, {})
        hostname = sys_info.get("hostname", self.entry.data["host"])
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": f"TrueNAS ({hostname})",
            "manufacturer": "iXsystems",
            "model": sys_info.get("model", "TrueNAS Scale"),
            "sw_version": sys_info.get("version", "26.0"),
        }


class TrueNASServiceRestartButton(TrueNASBaseButton):
    """Button for restarting TrueNAS system services."""

    def __init__(self, coordinator, entry, service_name: str) -> None:
        super().__init__(coordinator, entry, f"service_restart_{service_name}", f"Service {service_name} Restart")
        self.service_name = service_name
        self._attr_unique_id = f"{entry.entry_id}_service_restart_{service_name}"
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def icon(self) -> str:
        return "mdi:restart"

    async def async_press(self) -> None:
        """Press the restart button."""
        try:
            await self.coordinator.client.call("service.control", [self.service_name, {"action": "RESTART"}])
            _LOGGER.info("Restarted service %s", self.service_name)
        except Exception as err:
            _LOGGER.error("Failed to restart service %s: %s", self.service_name, err)
        await self.coordinator.async_request_refresh()


class TrueNASAppRestartButton(TrueNASBaseButton):
    """Button for restarting TrueNAS applications/containers."""

    def __init__(self, coordinator, entry, app_name: str) -> None:
        super().__init__(coordinator, entry, f"app_restart_{app_name}", f"App {app_name} Restart")
        self.app_name = app_name
        self._attr_unique_id = f"{entry.entry_id}_app_restart_{app_name}"

    @property
    def icon(self) -> str:
        return "mdi:restart"

    @property
    def entity_picture(self) -> Any:
        """Return app logo URL if available."""
        apps = self.coordinator.data.get(DATA_APPS, {})
        app = apps.get(self.app_name, {})
        icon_url = app.get("icon_url") or app.get("icon") or app.get("logo")
        if not icon_url and isinstance(app.get("metadata"), dict):
            icon_url = app["metadata"].get("icon")
        if isinstance(icon_url, str) and (icon_url.startswith("http://") or icon_url.startswith("https://")):
            return icon_url
        return None

    async def async_press(self) -> None:
        """Press the restart app button."""
        try:
            try:
                await self.coordinator.client.call("app.redeploy", [self.app_name])
            except Exception:
                await self.coordinator.client.call("app.stop", [self.app_name])
                await self.coordinator.client.call("app.start", [self.app_name])
            _LOGGER.info("Restarted app %s", self.app_name)
        except Exception as err:
            _LOGGER.error("Failed to restart app %s: %s", self.app_name, err)
        await self.coordinator.async_request_refresh()


class TrueNASVMRestartButton(TrueNASBaseButton):
    """Button for restarting Virtual Machines."""

    def __init__(self, coordinator, entry, vm_key: str, vm_id: Any, vm_name: str) -> None:
        super().__init__(coordinator, entry, f"vm_restart_{vm_key}", f"VM {vm_name} Restart")
        self.vm_key = vm_key
        self.vm_id = vm_id
        self.vm_name = vm_name
        self._attr_unique_id = f"{entry.entry_id}_vm_restart_{vm_key}"

    @property
    def icon(self) -> str:
        return "mdi:restart"

    async def async_press(self) -> None:
        """Press the restart VM button."""
        try:
            await self.coordinator.client.call("vm.restart", [self.vm_id])
            _LOGGER.info("Restarted VM %s (ID %s)", self.vm_name, self.vm_id)
        except Exception as err:
            _LOGGER.error("Failed to restart VM %s (ID %s): %s", self.vm_name, self.vm_id, err)
        await self.coordinator.async_request_refresh()
