"""Update platform for TrueNAS Scale 26 integration."""

from typing import Any, Dict, Optional

from homeassistant.components.update import (
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_APPS, DATA_SYSTEM_INFO, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TrueNAS Scale update entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = []

    # App updates
    apps = coordinator.data.get(DATA_APPS, {})
    for app_name in apps:
        entities.append(TrueNASAppUpdateEntity(coordinator, entry, app_name))

    async_add_entities(entities)


class TrueNASAppUpdateEntity(CoordinatorEntity, UpdateEntity):
    """Update entity for TrueNAS applications."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, app_name: str) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self.app_name = app_name
        self._attr_name = f"App {app_name}"
        self._attr_unique_id = f"{entry.entry_id}_app_update_{app_name}"
        self._attr_supported_features = UpdateEntityFeature.RELEASE_NOTES

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

    @property
    def icon(self) -> str:
        """Return default icon for app updates."""
        return "mdi:cube-outline"

    @property
    def entity_picture(self) -> Optional[str]:
        """Return app logo URL if available."""
        apps = self.coordinator.data.get(DATA_APPS, {})
        app = apps.get(self.app_name, {})
        icon_url = app.get("icon_url") or app.get("icon") or app.get("logo")
        if not icon_url and isinstance(app.get("metadata"), dict):
            icon_url = app["metadata"].get("icon")
        if isinstance(icon_url, str) and (icon_url.startswith("http://") or icon_url.startswith("https://")):
            return icon_url
        return None

    @property
    def installed_version(self) -> Optional[str]:
        apps = self.coordinator.data.get(DATA_APPS, {})
        app = apps.get(self.app_name, {})
        return app.get("version") or app.get("human_version")

    @property
    def latest_version(self) -> Optional[str]:
        apps = self.coordinator.data.get(DATA_APPS, {})
        app = apps.get(self.app_name, {})
        upgrade_version = app.get("upgrade_available_version") or app.get("latest_version")
        if upgrade_version:
            return upgrade_version
        return self.installed_version
