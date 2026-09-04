"""TrueNAS Scale 26 Integration for Home Assistant."""

import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TrueNASAPIError, TrueNASScaleClient
from .const import (
    CONF_API_KEY,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    DATA_ALERTS,
    DATA_APPS,
    DATA_DATASETS,
    DATA_DISKS,
    DATA_DISK_TEMPS,
    DATA_INTERFACES,
    DATA_POOLS,
    DATA_REALTIME,
    DATA_SERVICES,
    DATA_SYSTEM_INFO,
    DATA_VMS,
    DEFAULT_USERNAME,
    DOMAIN,
    UPDATE_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.UPDATE,
    Platform.SWITCH,
    Platform.BUTTON,
]


class TrueNASCoordinator(DataUpdateCoordinator):
    """Coordinator for fetching TrueNAS Scale data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TrueNASScaleClient,
        config_entry: ConfigEntry | None = None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        """Fetch all TrueNAS data in parallel."""
        tasks = {
            DATA_SYSTEM_INFO: self.client.async_get_system_info(),
            DATA_POOLS: self.client.async_get_pools(),
            DATA_DATASETS: self.client.async_get_datasets(),
            DATA_DISKS: self.client.async_get_disks(),
            DATA_DISK_TEMPS: self.client.async_get_disk_temperatures(),
            DATA_SERVICES: self.client.async_get_services(),
            DATA_APPS: self.client.async_get_apps(),
            DATA_ALERTS: self.client.async_get_alerts(),
            DATA_REALTIME: self.client.async_get_realtime_cache(),
            DATA_INTERFACES: self.client.async_get_interfaces(),
            DATA_VMS: self.client.async_get_vms(),
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        res_dict = dict(zip(tasks.keys(), results))

        # Check if core endpoints failed completely
        if isinstance(res_dict[DATA_SYSTEM_INFO], Exception) and isinstance(res_dict[DATA_POOLS], Exception):
            raise UpdateFailed(f"Error fetching core data from TrueNAS Scale: {res_dict[DATA_SYSTEM_INFO]}")

        sys_info = res_dict[DATA_SYSTEM_INFO] if not isinstance(res_dict[DATA_SYSTEM_INFO], Exception) else {}
        pools = res_dict[DATA_POOLS] if not isinstance(res_dict[DATA_POOLS], Exception) else []
        datasets = res_dict[DATA_DATASETS] if not isinstance(res_dict[DATA_DATASETS], Exception) else []
        disks = res_dict[DATA_DISKS] if not isinstance(res_dict[DATA_DISKS], Exception) else []
        disk_temps = res_dict[DATA_DISK_TEMPS] if not isinstance(res_dict[DATA_DISK_TEMPS], Exception) else {}
        services = res_dict[DATA_SERVICES] if not isinstance(res_dict[DATA_SERVICES], Exception) else []
        apps = res_dict[DATA_APPS] if not isinstance(res_dict[DATA_APPS], Exception) else []
        alerts = res_dict[DATA_ALERTS] if not isinstance(res_dict[DATA_ALERTS], Exception) else []
        realtime = res_dict[DATA_REALTIME] if not isinstance(res_dict[DATA_REALTIME], Exception) else {}
        interfaces = res_dict[DATA_INTERFACES] if not isinstance(res_dict[DATA_INTERFACES], Exception) else []
        vms = res_dict[DATA_VMS] if not isinstance(res_dict[DATA_VMS], Exception) else []

        if isinstance(res_dict[DATA_APPS], Exception):
            _LOGGER.warning("Could not fetch apps data: %s", res_dict[DATA_APPS])
        if isinstance(res_dict[DATA_SERVICES], Exception):
            _LOGGER.warning("Could not fetch services data: %s", res_dict[DATA_SERVICES])
        if isinstance(res_dict[DATA_ALERTS], Exception):
            _LOGGER.warning("Could not fetch alerts data: %s", res_dict[DATA_ALERTS])
        if isinstance(res_dict[DATA_VMS], Exception):
            _LOGGER.warning("Could not fetch VMs data: %s", res_dict[DATA_VMS])

        return {
            DATA_SYSTEM_INFO: sys_info if isinstance(sys_info, dict) else {},
            DATA_POOLS: {p["name"]: p for p in pools if isinstance(p, dict) and "name" in p} if isinstance(pools, list) else {},
            DATA_DATASETS: {d["id"]: d for d in datasets if isinstance(d, dict) and "id" in d} if isinstance(datasets, list) else {},
            DATA_DISKS: {dk["name"]: dk for dk in disks if isinstance(dk, dict) and "name" in dk} if isinstance(disks, list) else {},
            DATA_DISK_TEMPS: disk_temps if isinstance(disk_temps, dict) else {},
            DATA_SERVICES: {s["service"]: s for s in services if isinstance(s, dict) and "service" in s} if isinstance(services, list) else {},
            DATA_APPS: {a["name"]: a for a in apps if isinstance(a, dict) and "name" in a} if isinstance(apps, list) else {},
            DATA_ALERTS: alerts if isinstance(alerts, list) else [],
            DATA_REALTIME: realtime if isinstance(realtime, dict) else {},
            DATA_INTERFACES: {i["id"]: i for i in interfaces if isinstance(i, dict) and "id" in i} if isinstance(interfaces, list) else {},
            DATA_VMS: {str(v.get("name") or v.get("id")): v for v in vms if isinstance(v, dict) and ("name" in v or "id" in v)} if isinstance(vms, list) else {},
        }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TrueNAS Scale from a config entry."""
    session = async_get_clientsession(hass)

    client = TrueNASScaleClient(
        host=entry.data[CONF_HOST],
        api_key=entry.data[CONF_API_KEY],
        username=entry.data.get(CONF_USERNAME, DEFAULT_USERNAME),
        port=entry.data[CONF_PORT],
        use_ssl=entry.data[CONF_SSL],
        verify_ssl=entry.data[CONF_VERIFY_SSL],
        session=session,
    )

    try:
        await client.connect()
        try:
            await client.subscribe("*")
        except Exception as err:
            _LOGGER.warning("Could not subscribe to events: %s", err)
    except Exception as err:
        raise ConfigEntryNotReady(f"Could not connect to TrueNAS Scale: {err}") from err

    coordinator = TrueNASCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    def handle_event(params: dict) -> None:
        """Handle push notification from TrueNAS."""
        _LOGGER.debug("Received WebSocket event notification: %s", params)
        hass.async_create_task(coordinator.async_request_refresh())

    client.register_callback(handle_event)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data["client"].close()

    return unload_ok
