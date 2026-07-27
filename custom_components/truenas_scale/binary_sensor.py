"""Binary sensor platform for TrueNAS Scale 26 integration."""

from typing import Any, Dict

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_ALERTS,
    DATA_APPS,
    DATA_POOLS,
    DATA_SERVICES,
    DATA_SYSTEM_INFO,
    DATA_VMS,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TrueNAS Scale binary sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = []

    # Alerts binary sensor
    entities.append(TrueNASSystemAlertsBinarySensor(coordinator, entry))

    # Pool health binary sensors
    pools = coordinator.data.get(DATA_POOLS, {})
    for pool_name in pools:
        entities.append(TrueNASPoolHealthyBinarySensor(coordinator, entry, pool_name))

    # Services binary sensors
    services = coordinator.data.get(DATA_SERVICES, {})
    for service_name in services:
        entities.append(TrueNASServiceBinarySensor(coordinator, entry, service_name))

    # Applications binary sensors
    apps = coordinator.data.get(DATA_APPS, {})
    for app_name in apps:
        entities.append(TrueNASAppBinarySensor(coordinator, entry, app_name))

    # Virtual Machines binary sensors
    vms = coordinator.data.get(DATA_VMS, {})
    for vm_key, vm in vms.items():
        vm_name = vm.get("name") or vm_key
        entities.append(TrueNASVMBinarySensor(coordinator, entry, vm_key, vm_name))

    async_add_entities(entities)


class TrueNASBaseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base class for TrueNAS binary sensors."""

    def __init__(self, coordinator, entry: ConfigEntry, key: str, name: str) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._key = key
        self._attr_name = name
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> Dict[str, Any]:
        sys_info = self.coordinator.data.get(DATA_SYSTEM_INFO, {})
        hostname = sys_info.get("hostname", self.entry.data["host"])
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": f"TrueNAS ({hostname})",
            "manufacturer": "iXsystems",
            "model": sys_info.get("model", "TrueNAS Scale"),
            "sw_version": sys_info.get("version", "26.0"),
        }


class TrueNASSystemAlertsBinarySensor(TrueNASBaseBinarySensor):
    """Binary sensor for system alerts."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "system_alerts", "System Alerts")
        self._attr_unique_id = f"{entry.entry_id}_system_alerts"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:alert-circle-outline"

    @property
    def is_on(self) -> bool:
        alerts = self.coordinator.data.get(DATA_ALERTS, [])
        return len(alerts) > 0


class TrueNASPoolHealthyBinarySensor(TrueNASBaseBinarySensor):
    """Binary sensor for storage pool health."""

    def __init__(self, coordinator, entry, pool_name: str) -> None:
        super().__init__(coordinator, entry, f"pool_{pool_name}_healthy", f"Pool {pool_name} Healthy")
        self.pool_name = pool_name
        self._attr_unique_id = f"{entry.entry_id}_pool_{pool_name}_healthy"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def icon(self) -> str:
        return "mdi:database-alert" if self.is_on else "mdi:database-check"

    @property
    def is_on(self) -> bool:
        pools = self.coordinator.data.get(DATA_POOLS, {})
        pool = pools.get(self.pool_name, {})
        status = pool.get("status", "ONLINE")
        healthy = pool.get("healthy", True)
        # DeviceClass.PROBLEM is ON when unhealthy
        return not (healthy and status == "ONLINE")


class TrueNASServiceBinarySensor(TrueNASBaseBinarySensor):
    """Binary sensor for system services status."""

    def __init__(self, coordinator, entry, service_name: str) -> None:
        super().__init__(coordinator, entry, f"service_{service_name}", f"Service {service_name}")
        self.service_name = service_name
        self._attr_unique_id = f"{entry.entry_id}_service_{service_name}"
        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        srv = self.service_name.lower()
        if "smb" in srv or "cifs" in srv:
            return "mdi:folder-network"
        if "ssh" in srv:
            return "mdi:console-network"
        if "nfs" in srv:
            return "mdi:share-network"
        if "ftp" in srv:
            return "mdi:file-transfer"
        if "iscsi" in srv:
            return "mdi:harddisk-network"
        return "mdi:cog-network"

    @property
    def is_on(self) -> bool:
        services = self.coordinator.data.get(DATA_SERVICES, {})
        service = services.get(self.service_name, {})
        return service.get("state") == "RUNNING"


class TrueNASAppBinarySensor(TrueNASBaseBinarySensor):
    """Binary sensor for application/container status."""

    def __init__(self, coordinator, entry, app_name: str) -> None:
        super().__init__(coordinator, entry, f"app_{app_name}", f"App {app_name}")
        self.app_name = app_name
        self._attr_unique_id = f"{entry.entry_id}_app_{app_name}"
        self._attr_device_class = BinarySensorDeviceClass.RUNNING

    @property
    def icon(self) -> str:
        return "mdi:cube-outline"

    @property
    def entity_picture(self) -> Any:
        apps = self.coordinator.data.get(DATA_APPS, {})
        app = apps.get(self.app_name, {})
        icon_url = app.get("icon_url") or app.get("icon") or app.get("logo")
        if not icon_url and isinstance(app.get("metadata"), dict):
            icon_url = app["metadata"].get("icon")
        if isinstance(icon_url, str) and (icon_url.startswith("http://") or icon_url.startswith("https://")):
            return icon_url
        return None

    @property
    def is_on(self) -> bool:
        apps = self.coordinator.data.get(DATA_APPS, {})
        app = apps.get(self.app_name, {})
        return app.get("state") in ("RUNNING", "ACTIVE")


class TrueNASVMBinarySensor(TrueNASBaseBinarySensor):
    """Binary sensor for Virtual Machine status."""

    def __init__(self, coordinator, entry, vm_key: str, vm_name: str) -> None:
        super().__init__(coordinator, entry, f"vm_{vm_key}", f"VM {vm_name}")
        self.vm_key = vm_key
        self.vm_name = vm_name
        self._attr_unique_id = f"{entry.entry_id}_vm_{vm_key}"
        self._attr_device_class = BinarySensorDeviceClass.RUNNING

    @property
    def icon(self) -> str:
        return "mdi:server" if self.is_on else "mdi:server-off"

    @property
    def is_on(self) -> bool:
        vms = self.coordinator.data.get(DATA_VMS, {})
        vm = vms.get(self.vm_key, {})
        status = vm.get("status", {})
        state = status.get("state") if isinstance(status, dict) else vm.get("state") or vm.get("status")
        return str(state).upper() in ("RUNNING", "ACTIVE")
