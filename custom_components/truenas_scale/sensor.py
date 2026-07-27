"""Sensor platform for TrueNAS Scale 26 integration."""

from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfDataRate,
    UnitOfInformation,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_DATASETS,
    DATA_DISKS,
    DATA_DISK_TEMPS,
    DATA_INTERFACES,
    DATA_POOLS,
    DATA_REALTIME,
    DATA_SYSTEM_INFO,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TrueNAS Scale sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = []

    # System sensors
    entities.append(TrueNASUptimeSensor(coordinator, entry))
    entities.append(TrueNASCPUUsageSensor(coordinator, entry))
    entities.append(TrueNASCPUTemperatureSensor(coordinator, entry))
    entities.append(TrueNASCPULoad1mSensor(coordinator, entry))
    entities.append(TrueNASCPULoad5mSensor(coordinator, entry))
    entities.append(TrueNASCPULoad15mSensor(coordinator, entry))
    entities.append(TrueNASMemoryUsageSensor(coordinator, entry))
    entities.append(TrueNASMemoryUsedSensor(coordinator, entry))
    entities.append(TrueNASMemoryAvailableSensor(coordinator, entry))
    entities.append(TrueNASMemoryTotalSensor(coordinator, entry))
    entities.append(TrueNASZFSARCSizeSensor(coordinator, entry))
    entities.append(TrueNASSystemDiskReadRateSensor(coordinator, entry))
    entities.append(TrueNASSystemDiskWriteRateSensor(coordinator, entry))
    entities.append(TrueNASSystemDiskReadIOPSSensor(coordinator, entry))
    entities.append(TrueNASSystemDiskWriteIOPSSensor(coordinator, entry))

    # Storage Pool sensors
    pools = coordinator.data.get(DATA_POOLS, {})
    for pool_name in pools:
        entities.append(TrueNASPoolUsageSensor(coordinator, entry, pool_name))
        entities.append(TrueNASPoolFreeSensor(coordinator, entry, pool_name))
        entities.append(TrueNASPoolUsedSpaceSensor(coordinator, entry, pool_name))
        entities.append(TrueNASPoolUsableCapacitySensor(coordinator, entry, pool_name))
        entities.append(TrueNASPoolReadRateSensor(coordinator, entry, pool_name))
        entities.append(TrueNASPoolWriteRateSensor(coordinator, entry, pool_name))
        entities.append(TrueNASPoolReadIOPSSensor(coordinator, entry, pool_name))
        entities.append(TrueNASPoolWriteIOPSSensor(coordinator, entry, pool_name))

    # Dataset sensors
    datasets = coordinator.data.get(DATA_DATASETS, {})
    for dataset_id in datasets:
        entities.append(TrueNASDatasetUsedSensor(coordinator, entry, dataset_id))

    # Disk sensors (Only Temperature per disk)
    disks = coordinator.data.get(DATA_DISKS, {})
    for disk_name in disks:
        entities.append(TrueNASDiskTemperatureSensor(coordinator, entry, disk_name))

    # Network interface sensors (Download / Upload Rates)
    interfaces = coordinator.data.get(DATA_INTERFACES, {})
    for iface_name in interfaces:
        entities.append(TrueNASNetworkRxSensor(coordinator, entry, iface_name))
        entities.append(TrueNASNetworkTxSensor(coordinator, entry, iface_name))

    async_add_entities(entities)


class TrueNASBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for TrueNAS sensors."""

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
        version = sys_info.get("version", "26.0")
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": f"TrueNAS ({hostname})",
            "manufacturer": "iXsystems",
            "model": sys_info.get("model", "TrueNAS Scale"),
            "sw_version": version,
        }


class TrueNASUptimeSensor(TrueNASBaseSensor):
    """System Uptime sensor."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "uptime", "System Uptime")
        self._attr_unique_id = f"{entry.entry_id}_uptime"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:clock-outline"

    @property
    def native_value(self) -> Optional[float]:
        sys_info = self.coordinator.data.get(DATA_SYSTEM_INFO, {})
        uptime_val = sys_info.get("uptime_seconds")
        if uptime_val is not None:
            try:
                return float(uptime_val)
            except (ValueError, TypeError):
                pass
        raw_uptime = sys_info.get("uptime")
        if raw_uptime is not None:
            try:
                return float(raw_uptime)
            except (ValueError, TypeError):
                pass
        return None


class TrueNASCPULoad1mSensor(TrueNASBaseSensor):
    """System CPU Load Average (1 min) sensor."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "cpu_load_1m", "CPU Load Average (1m)")
        self._attr_unique_id = f"{entry.entry_id}_cpu_load_1m"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:cpu-64-bit"

    @property
    def native_value(self) -> Optional[float]:
        sys_info = self.coordinator.data.get(DATA_SYSTEM_INFO, {})
        loadavg = sys_info.get("loadavg")
        if isinstance(loadavg, list) and len(loadavg) > 0:
            try:
                return round(float(loadavg[0]), 2)
            except (ValueError, TypeError):
                pass
        return None


class TrueNASCPULoad5mSensor(TrueNASBaseSensor):
    """System CPU Load Average (5 min) sensor."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "cpu_load_5m", "CPU Load Average (5m)")
        self._attr_unique_id = f"{entry.entry_id}_cpu_load_5m"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:cpu-64-bit"

    @property
    def native_value(self) -> Optional[float]:
        sys_info = self.coordinator.data.get(DATA_SYSTEM_INFO, {})
        loadavg = sys_info.get("loadavg")
        if isinstance(loadavg, list) and len(loadavg) > 1:
            try:
                return round(float(loadavg[1]), 2)
            except (ValueError, TypeError):
                pass
        return None


class TrueNASCPULoad15mSensor(TrueNASBaseSensor):
    """System CPU Load Average (15 min) sensor."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "cpu_load_15m", "CPU Load Average (15m)")
        self._attr_unique_id = f"{entry.entry_id}_cpu_load_15m"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:cpu-64-bit"

    @property
    def native_value(self) -> Optional[float]:
        sys_info = self.coordinator.data.get(DATA_SYSTEM_INFO, {})
        loadavg = sys_info.get("loadavg")
        if isinstance(loadavg, list) and len(loadavg) > 2:
            try:
                return round(float(loadavg[2]), 2)
            except (ValueError, TypeError):
                pass
        return None


class TrueNASMemoryUsageSensor(TrueNASBaseSensor):
    """Realtime RAM Memory Usage sensor in %."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "memory_usage", "RAM Usage")
        self._attr_unique_id = f"{entry.entry_id}_memory_usage"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:memory"

    @property
    def native_value(self) -> Optional[float]:
        # 1. Realtime telemetry payload
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            mem = realtime.get("memory", {})
            if isinstance(mem, dict):
                usage_pct = mem.get("usage_percent") or mem.get("percent")
                if usage_pct is not None:
                    try:
                        return round(float(usage_pct), 1)
                    except (ValueError, TypeError):
                        pass
                total = mem.get("physical_memory_total")
                avail = mem.get("physical_memory_available")
                if total is not None and avail is not None:
                    try:
                        tot_f = float(total)
                        avail_f = float(avail)
                        if tot_f > 0:
                            return round(((tot_f - avail_f) / tot_f) * 100.0, 1)
                    except (ValueError, TypeError):
                        pass

        # 2. Fallback using system_info physmem if available
        return None


class TrueNASMemoryUsedSensor(TrueNASBaseSensor):
    """Realtime Used RAM Memory sensor in GB."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "memory_used", "Used RAM")
        self._attr_unique_id = f"{entry.entry_id}_memory_used"
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_native_unit_of_measurement = UnitOfInformation.GIGABYTES
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:memory"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            mem = realtime.get("memory", {})
            if isinstance(mem, dict):
                total = mem.get("physical_memory_total")
                avail = mem.get("physical_memory_available")
                if total is not None and avail is not None:
                    try:
                        used_bytes = float(total) - float(avail)
                        return round(used_bytes / (1024**3), 2)
                    except (ValueError, TypeError):
                        pass
        return None


class TrueNASMemoryAvailableSensor(TrueNASBaseSensor):
    """Realtime Available RAM Memory sensor in GB."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "memory_available", "Available RAM")
        self._attr_unique_id = f"{entry.entry_id}_memory_available"
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_native_unit_of_measurement = UnitOfInformation.GIGABYTES
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:memory"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            mem = realtime.get("memory", {})
            if isinstance(mem, dict):
                avail = mem.get("physical_memory_available")
                if avail is not None:
                    try:
                        return round(float(avail) / (1024**3), 2)
                    except (ValueError, TypeError):
                        pass
        return None


class TrueNASMemoryTotalSensor(TrueNASBaseSensor):
    """Total RAM Memory sensor in GB."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "memory_total", "Total RAM")
        self._attr_unique_id = f"{entry.entry_id}_memory_total"
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_native_unit_of_measurement = UnitOfInformation.GIGABYTES
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:memory"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            mem = realtime.get("memory", {})
            if isinstance(mem, dict):
                total = mem.get("physical_memory_total")
                if total is not None:
                    try:
                        return round(float(total) / (1024**3), 2)
                    except (ValueError, TypeError):
                        pass

        sys_info = self.coordinator.data.get(DATA_SYSTEM_INFO, {})
        physmem = sys_info.get("physmem")
        if physmem is not None:
            try:
                return round(float(physmem) / (1024**3), 2)
            except (ValueError, TypeError):
                pass
        return None


class TrueNASZFSARCSizeSensor(TrueNASBaseSensor):
    """Realtime ZFS ARC Cache Size sensor in GB."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "zfs_arc_size", "ZFS ARC Size")
        self._attr_unique_id = f"{entry.entry_id}_zfs_arc_size"
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_native_unit_of_measurement = UnitOfInformation.GIGABYTES
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:database-clock"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            mem = realtime.get("memory", {})
            if isinstance(mem, dict):
                arc = mem.get("arc_size")
                if arc is not None:
                    try:
                        return round(float(arc) / (1024**3), 2)
                    except (ValueError, TypeError):
                        pass
            zfs = realtime.get("zfs", {})
            if isinstance(zfs, dict):
                arc = zfs.get("arc_size")
                if arc is not None:
                    try:
                        return round(float(arc) / (1024**3), 2)
                    except (ValueError, TypeError):
                        pass
        return None


def _get_pool_dataset_bytes(coordinator, pool_name: str):
    """Extract usable used_bytes and avail_bytes for a pool from root dataset or pool object."""
    used_bytes = None
    avail_bytes = None

    # 1. Search in DATA_DATASETS
    datasets = coordinator.data.get(DATA_DATASETS, {})
    ds = datasets.get(pool_name)
    if not ds:
        for d in datasets.values():
            if isinstance(d, dict):
                if d.get("id") == pool_name or d.get("name") == pool_name or d.get("mountpoint") == f"/{pool_name}":
                    ds = d
                    break

    # 2. Search inside DATA_POOLS (pool.query object often embeds dataset info)
    if not ds:
        pools = coordinator.data.get(DATA_POOLS, {})
        pool_obj = pools.get(pool_name, {})
        if isinstance(pool_obj, dict):
            ds = pool_obj.get("dataset") or pool_obj.get("root_dataset") or pool_obj.get("properties")

    if isinstance(ds, dict):
        # Extract used
        u = ds.get("used")
        if isinstance(u, dict):
            used_bytes = u.get("parsed") if u.get("parsed") is not None else u.get("rawvalue")
        elif isinstance(u, (int, float)):
            used_bytes = u

        # Extract available
        a = ds.get("available")
        if isinstance(a, dict):
            avail_bytes = a.get("parsed") if a.get("parsed") is not None else a.get("rawvalue")
        elif isinstance(a, (int, float)):
            avail_bytes = a

    return used_bytes, avail_bytes


class TrueNASPoolUsageSensor(TrueNASBaseSensor):
    """Storage pool usable usage percentage sensor."""

    def __init__(self, coordinator, entry, pool_name: str) -> None:
        super().__init__(coordinator, entry, f"pool_{pool_name}_usage", f"Pool {pool_name} Usage")
        self.pool_name = pool_name
        self._attr_unique_id = f"{entry.entry_id}_pool_{pool_name}_usage"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def icon(self) -> str:
        return "mdi:database"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        used_bytes, avail_bytes = _get_pool_dataset_bytes(self.coordinator, self.pool_name)
        attrs: Dict[str, Any] = {}
        if avail_bytes is not None:
            attrs["available_bytes"] = int(avail_bytes)
            attrs["available_gb"] = round(float(avail_bytes) / (1024**3), 2)
        if used_bytes is not None:
            attrs["used_bytes"] = int(used_bytes)
            attrs["used_gb"] = round(float(used_bytes) / (1024**3), 2)
        if used_bytes is not None and avail_bytes is not None:
            tot = float(used_bytes) + float(avail_bytes)
            attrs["total_usable_gb"] = round(tot / (1024**3), 2)
        return attrs

    @property
    def native_value(self) -> Optional[float]:
        # 1. Primary: Use usable root dataset metrics (matches TrueNAS Storage GUI)
        used_bytes, avail_bytes = _get_pool_dataset_bytes(self.coordinator, self.pool_name)
        if used_bytes is not None and avail_bytes is not None:
            try:
                u_f = float(used_bytes)
                a_f = float(avail_bytes)
                tot = u_f + a_f
                if tot > 0:
                    return round((u_f / tot) * 100.0, 1)
            except (ValueError, TypeError):
                pass

        # 2. Fallback: Raw ZFS Pool capacity
        pools = self.coordinator.data.get(DATA_POOLS, {})
        pool = pools.get(self.pool_name, {})
        try:
            size = float(pool.get("size", 0))
            allocated = float(pool.get("allocated", 0))
            if size > 0:
                return round((allocated / size) * 100, 1)
        except (ValueError, TypeError):
            pass
        return None


class TrueNASPoolFreeSensor(TrueNASBaseSensor):
    """Storage pool usable free space sensor."""

    def __init__(self, coordinator, entry, pool_name: str) -> None:
        super().__init__(coordinator, entry, f"pool_{pool_name}_free", f"Pool {pool_name} Free Space")
        self.pool_name = pool_name
        self._attr_unique_id = f"{entry.entry_id}_pool_{pool_name}_free"
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_native_unit_of_measurement = UnitOfInformation.BYTES
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def icon(self) -> str:
        return "mdi:database-search"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        used_bytes, avail_bytes = _get_pool_dataset_bytes(self.coordinator, self.pool_name)
        attrs: Dict[str, Any] = {}
        if avail_bytes is not None:
            attrs["available_bytes"] = int(avail_bytes)
            attrs["available_gb"] = round(float(avail_bytes) / (1000**3), 2)
            attrs["available_tib"] = round(float(avail_bytes) / (1024**4), 2)
        if used_bytes is not None:
            attrs["used_bytes"] = int(used_bytes)
            attrs["used_gb"] = round(float(used_bytes) / (1000**3), 2)
            attrs["used_tib"] = round(float(used_bytes) / (1024**4), 2)
        if used_bytes is not None and avail_bytes is not None:
            tot = float(used_bytes) + float(avail_bytes)
            attrs["total_usable_gb"] = round(tot / (1000**3), 2)
            attrs["total_usable_tib"] = round(tot / (1024**4), 2)
        return attrs

    @property
    def native_value(self) -> Optional[int]:
        # 1. Primary: Use usable root dataset available space (matches TrueNAS Storage GUI)
        _, avail_bytes = _get_pool_dataset_bytes(self.coordinator, self.pool_name)
        if avail_bytes is not None:
            try:
                return int(avail_bytes)
            except (ValueError, TypeError):
                pass

        # 2. Fallback: Raw ZFS Pool free space
        pools = self.coordinator.data.get(DATA_POOLS, {})
        pool = pools.get(self.pool_name, {})
        free_bytes = pool.get("free")
        if free_bytes is not None:
            try:
                return int(free_bytes)
            except (ValueError, TypeError):
                pass
        return None


class TrueNASPoolUsedSpaceSensor(TrueNASBaseSensor):
    """Storage pool usable used space sensor."""

    def __init__(self, coordinator, entry, pool_name: str) -> None:
        super().__init__(coordinator, entry, f"pool_{pool_name}_used", f"Pool {pool_name} Used Space")
        self.pool_name = pool_name
        self._attr_unique_id = f"{entry.entry_id}_pool_{pool_name}_used"
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_native_unit_of_measurement = UnitOfInformation.BYTES
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def icon(self) -> str:
        return "mdi:database-arrow-right"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        used_bytes, avail_bytes = _get_pool_dataset_bytes(self.coordinator, self.pool_name)
        attrs: Dict[str, Any] = {}
        if used_bytes is not None:
            attrs["used_bytes"] = int(used_bytes)
            attrs["used_gb"] = round(float(used_bytes) / (1000**3), 2)
            attrs["used_tib"] = round(float(used_bytes) / (1024**4), 2)
        if avail_bytes is not None:
            attrs["available_bytes"] = int(avail_bytes)
            attrs["available_gb"] = round(float(avail_bytes) / (1000**3), 2)
            attrs["available_tib"] = round(float(avail_bytes) / (1024**4), 2)
        return attrs

    @property
    def native_value(self) -> Optional[int]:
        used_bytes, _ = _get_pool_dataset_bytes(self.coordinator, self.pool_name)
        if used_bytes is not None:
            try:
                return int(used_bytes)
            except (ValueError, TypeError):
                pass

        pools = self.coordinator.data.get(DATA_POOLS, {})
        pool = pools.get(self.pool_name, {})
        allocated = pool.get("allocated")
        if allocated is not None:
            try:
                return int(allocated)
            except (ValueError, TypeError):
                pass
        return None


class TrueNASPoolUsableCapacitySensor(TrueNASBaseSensor):
    """Storage pool total usable capacity sensor."""

    def __init__(self, coordinator, entry, pool_name: str) -> None:
        super().__init__(coordinator, entry, f"pool_{pool_name}_usable_capacity", f"Pool {pool_name} Usable Capacity")
        self.pool_name = pool_name
        self._attr_unique_id = f"{entry.entry_id}_pool_{pool_name}_usable_capacity"
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_native_unit_of_measurement = UnitOfInformation.BYTES
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def icon(self) -> str:
        return "mdi:database"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        used_bytes, avail_bytes = _get_pool_dataset_bytes(self.coordinator, self.pool_name)
        attrs: Dict[str, Any] = {}
        if used_bytes is not None and avail_bytes is not None:
            tot = float(used_bytes) + float(avail_bytes)
            attrs["total_usable_bytes"] = int(tot)
            attrs["total_usable_gb"] = round(tot / (1000**3), 2)
            attrs["total_usable_tib"] = round(tot / (1024**4), 2)
        return attrs

    @property
    def native_value(self) -> Optional[int]:
        used_bytes, avail_bytes = _get_pool_dataset_bytes(self.coordinator, self.pool_name)
        if used_bytes is not None and avail_bytes is not None:
            try:
                tot = int(used_bytes) + int(avail_bytes)
                if tot > 0:
                    return tot
            except (ValueError, TypeError):
                pass

        pools = self.coordinator.data.get(DATA_POOLS, {})
        pool = pools.get(self.pool_name, {})
        size = pool.get("size")
        if size is not None:
            try:
                return int(size)
            except (ValueError, TypeError):
                pass
        return None


class TrueNASDatasetUsedSensor(TrueNASBaseSensor):
    """Dataset used space sensor."""

    def __init__(self, coordinator, entry, dataset_id: str) -> None:
        super().__init__(coordinator, entry, f"dataset_{dataset_id}_used", f"Dataset {dataset_id} Used")
        self.dataset_id = dataset_id
        self._attr_unique_id = f"{entry.entry_id}_dataset_{dataset_id}_used"
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_native_unit_of_measurement = UnitOfInformation.BYTES
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def icon(self) -> str:
        return "mdi:folder-database"

    @property
    def native_value(self) -> Optional[int]:
        datasets = self.coordinator.data.get(DATA_DATASETS, {})
        dataset = datasets.get(self.dataset_id, {})
        used_dict = dataset.get("used", {})
        used_bytes = used_dict.get("parsed") if isinstance(used_dict, dict) else used_dict
        if used_bytes is not None:
            try:
                return int(used_bytes)
            except (ValueError, TypeError):
                pass
        return None


class TrueNASDiskTemperatureSensor(TrueNASBaseSensor):
    """Disk temperature sensor."""

    def __init__(self, coordinator, entry, disk_name: str) -> None:
        super().__init__(coordinator, entry, f"disk_{disk_name}_temp", f"Disk {disk_name} Temperature")
        self.disk_name = disk_name
        self._attr_unique_id = f"{entry.entry_id}_disk_{disk_name}_temp"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:harddisk"

    @property
    def native_value(self) -> Optional[float]:
        disk_temps = self.coordinator.data.get(DATA_DISK_TEMPS, {})
        if isinstance(disk_temps, dict):
            temp = disk_temps.get(self.disk_name)
            if temp is not None:
                try:
                    return float(temp)
                except (ValueError, TypeError):
                    pass
        disks = self.coordinator.data.get(DATA_DISKS, {})
        disk = disks.get(self.disk_name, {})
        temp = disk.get("temp") if disk.get("temp") is not None else disk.get("temperature")
        if temp is not None:
            try:
                return float(temp)
            except (ValueError, TypeError):
                pass
        return None


class TrueNASCPUUsageSensor(TrueNASBaseSensor):
    """Realtime CPU Usage sensor in %."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "cpu_usage", "CPU Usage")
        self._attr_unique_id = f"{entry.entry_id}_cpu_usage"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:cpu-64-bit"

    @property
    def native_value(self) -> Optional[float]:
        # 1. Primary: Realtime telemetry payload
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            cpu_data = realtime.get("cpu", {})
            if isinstance(cpu_data, dict):
                # 1a. Check aggregate 'cpu' object
                agg_cpu = cpu_data.get("cpu")
                if isinstance(agg_cpu, dict):
                    usage = agg_cpu.get("usage") or agg_cpu.get("percent")
                    if usage is not None:
                        try:
                            return round(float(usage), 1)
                        except (ValueError, TypeError):
                            pass

                # 1b. Per-core usages (cpu0, cpu1, cpu2, ...)
                core_usages = []
                for k, core in cpu_data.items():
                    if isinstance(core, dict):
                        u = core.get("usage") or core.get("percent")
                        if u is not None:
                            try:
                                core_usages.append(float(u))
                            except (ValueError, TypeError):
                                pass
                    elif isinstance(core, (int, float)) and k.startswith("cpu") and k != "cpu":
                        core_usages.append(float(core))

                if core_usages:
                    return round(sum(core_usages) / len(core_usages), 1)

                usage = cpu_data.get("usage") or cpu_data.get("percent")
                if usage is not None:
                    try:
                        return round(float(usage), 1)
                    except (ValueError, TypeError):
                        pass
            elif isinstance(cpu_data, (int, float)):
                return round(float(cpu_data), 1)

        # 2. Fallback: Estimate CPU usage from 1m loadavg and CPU cores
        sys_info = self.coordinator.data.get(DATA_SYSTEM_INFO, {})
        loadavg = sys_info.get("loadavg")
        cores = sys_info.get("cores") or sys_info.get("physical_cores") or 1
        if isinstance(loadavg, list) and len(loadavg) > 0 and isinstance(cores, (int, float)) and cores > 0:
            try:
                est_usage = (float(loadavg[0]) / float(cores)) * 100.0
                return round(min(est_usage, 100.0), 1)
            except (ValueError, TypeError):
                pass

        return None


class TrueNASCPUTemperatureSensor(TrueNASBaseSensor):
    """Realtime CPU Temperature sensor in °C (aggregated across CPU cores)."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "cpu_temperature", "CPU Temperature")
        self._attr_unique_id = f"{entry.entry_id}_cpu_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:thermometer"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            cpu_data = realtime.get("cpu", {})
            if isinstance(cpu_data, dict):
                # 1a. Check aggregate 'cpu' object
                agg_cpu = cpu_data.get("cpu")
                if isinstance(agg_cpu, dict):
                    temp = agg_cpu.get("temp") or agg_cpu.get("temperature")
                    if temp is not None:
                        try:
                            return round(float(temp), 1)
                        except (ValueError, TypeError):
                            pass

                # 1b. Per-core temperatures (cpu0, cpu1, cpu2, ...)
                core_temps = []
                for k, core in cpu_data.items():
                    if isinstance(core, dict):
                        ctemp = core.get("temp") or core.get("temperature")
                        if ctemp is not None:
                            try:
                                core_temps.append(float(ctemp))
                            except (ValueError, TypeError):
                                pass
                    elif isinstance(core, (int, float)) and k.startswith("cpu") and k != "cpu":
                        core_temps.append(float(core))

                if core_temps:
                    # Return average core temperature
                    return round(sum(core_temps) / len(core_temps), 1)

                temp = cpu_data.get("temp") or cpu_data.get("temperature")
                if temp is not None:
                    try:
                        return round(float(temp), 1)
                    except (ValueError, TypeError):
                        pass
            elif isinstance(cpu_data, (int, float)):
                return round(float(cpu_data), 1)

        return None


class TrueNASNetworkRxSensor(TrueNASBaseSensor):
    """Realtime Network Download (Rx) sensor in MB/s."""

    def __init__(self, coordinator, entry, iface_name: str) -> None:
        super().__init__(coordinator, entry, f"net_{iface_name}_rx", f"Network {iface_name} Download")
        self.iface_name = iface_name
        self._attr_unique_id = f"{entry.entry_id}_net_{iface_name}_rx"
        self._attr_device_class = SensorDeviceClass.DATA_RATE
        self._attr_native_unit_of_measurement = UnitOfDataRate.MEGABYTES_PER_SECOND
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:download-network"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            ifaces = realtime.get("interfaces", {})
            if isinstance(ifaces, dict) and self.iface_name in ifaces:
                iface_info = ifaces[self.iface_name]
                if isinstance(iface_info, dict):
                    rx_rate = iface_info.get("received_bytes_rate") or iface_info.get("rx_bytes_rate") or iface_info.get("received_bytes")
                    if rx_rate is not None:
                        try:
                            return round(float(rx_rate) / (1024 * 1024), 2)
                        except (ValueError, TypeError):
                            pass
        return 0.0


class TrueNASNetworkTxSensor(TrueNASBaseSensor):
    """Realtime Network Upload (Tx) sensor in MB/s."""

    def __init__(self, coordinator, entry, iface_name: str) -> None:
        super().__init__(coordinator, entry, f"net_{iface_name}_tx", f"Network {iface_name} Upload")
        self.iface_name = iface_name
        self._attr_unique_id = f"{entry.entry_id}_net_{iface_name}_tx"
        self._attr_device_class = SensorDeviceClass.DATA_RATE
        self._attr_native_unit_of_measurement = UnitOfDataRate.MEGABYTES_PER_SECOND
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:upload-network"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            ifaces = realtime.get("interfaces", {})
            if isinstance(ifaces, dict) and self.iface_name in ifaces:
                iface_info = ifaces[self.iface_name]
                if isinstance(iface_info, dict):
                    tx_rate = iface_info.get("sent_bytes_rate") or iface_info.get("tx_bytes_rate") or iface_info.get("sent_bytes")
                    if tx_rate is not None:
                        try:
                            return round(float(tx_rate) / (1024 * 1024), 2)
                        except (ValueError, TypeError):
                            pass
        return 0.0


class TrueNASPoolReadRateSensor(TrueNASBaseSensor):
    """Pool Read Rate sensor in MB/s."""

    def __init__(self, coordinator, entry, pool_name: str) -> None:
        super().__init__(coordinator, entry, f"pool_{pool_name}_read_rate", f"Pool {pool_name} Read Rate")
        self.pool_name = pool_name
        self._attr_unique_id = f"{entry.entry_id}_pool_{pool_name}_read_rate"
        self._attr_device_class = SensorDeviceClass.DATA_RATE
        self._attr_native_unit_of_measurement = UnitOfDataRate.MEGABYTES_PER_SECOND
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:database-arrow-down"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            pools = realtime.get("pools", {})
            if isinstance(pools, dict) and self.pool_name in pools:
                pinfo = pools[self.pool_name]
                if isinstance(pinfo, dict):
                    rb = pinfo.get("read_bytes") or pinfo.get("bytes_read") or pinfo.get("read_bytes_rate")
                    if rb is not None:
                        try:
                            return round(float(rb) / (1024 * 1024), 2)
                        except (ValueError, TypeError):
                            pass
        return 0.0


class TrueNASPoolWriteRateSensor(TrueNASBaseSensor):
    """Pool Write Rate sensor in MB/s."""

    def __init__(self, coordinator, entry, pool_name: str) -> None:
        super().__init__(coordinator, entry, f"pool_{pool_name}_write_rate", f"Pool {pool_name} Write Rate")
        self.pool_name = pool_name
        self._attr_unique_id = f"{entry.entry_id}_pool_{pool_name}_write_rate"
        self._attr_device_class = SensorDeviceClass.DATA_RATE
        self._attr_native_unit_of_measurement = UnitOfDataRate.MEGABYTES_PER_SECOND
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:database-arrow-up"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            pools = realtime.get("pools", {})
            if isinstance(pools, dict) and self.pool_name in pools:
                pinfo = pools[self.pool_name]
                if isinstance(pinfo, dict):
                    wb = pinfo.get("write_bytes") or pinfo.get("bytes_written") or pinfo.get("write_bytes_rate")
                    if wb is not None:
                        try:
                            return round(float(wb) / (1024 * 1024), 2)
                        except (ValueError, TypeError):
                            pass
        return 0.0


class TrueNASPoolReadIOPSSensor(TrueNASBaseSensor):
    """Pool Read IOPS sensor."""

    def __init__(self, coordinator, entry, pool_name: str) -> None:
        super().__init__(coordinator, entry, f"pool_{pool_name}_read_iops", f"Pool {pool_name} Read IOPS")
        self.pool_name = pool_name
        self._attr_unique_id = f"{entry.entry_id}_pool_{pool_name}_read_iops"
        self._attr_native_unit_of_measurement = "ops/s"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:database-search"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            pools = realtime.get("pools", {})
            if isinstance(pools, dict) and self.pool_name in pools:
                pinfo = pools[self.pool_name]
                if isinstance(pinfo, dict):
                    ro = pinfo.get("read_ops") or pinfo.get("reads") or pinfo.get("read_iops")
                    if ro is not None:
                        try:
                            return round(float(ro), 1)
                        except (ValueError, TypeError):
                            pass
        return 0.0


class TrueNASPoolWriteIOPSSensor(TrueNASBaseSensor):
    """Pool Write IOPS sensor."""

    def __init__(self, coordinator, entry, pool_name: str) -> None:
        super().__init__(coordinator, entry, f"pool_{pool_name}_write_iops", f"Pool {pool_name} Write IOPS")
        self.pool_name = pool_name
        self._attr_unique_id = f"{entry.entry_id}_pool_{pool_name}_write_iops"
        self._attr_native_unit_of_measurement = "ops/s"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:database-edit"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            pools = realtime.get("pools", {})
            if isinstance(pools, dict) and self.pool_name in pools:
                pinfo = pools[self.pool_name]
                if isinstance(pinfo, dict):
                    wo = pinfo.get("write_ops") or pinfo.get("writes") or pinfo.get("write_iops")
                    if wo is not None:
                        try:
                            return round(float(wo), 1)
                        except (ValueError, TypeError):
                            pass
        return 0.0


class TrueNASSystemDiskReadRateSensor(TrueNASBaseSensor):
    """Aggregated System Disk Read Rate sensor across all disks/pools in MB/s."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "system_disk_read_rate", "System Disk Read Rate")
        self._attr_unique_id = f"{entry.entry_id}_system_disk_read_rate"
        self._attr_device_class = SensorDeviceClass.DATA_RATE
        self._attr_native_unit_of_measurement = UnitOfDataRate.MEGABYTES_PER_SECOND
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:harddisk-remove"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            total_rb = 0.0
            found = False
            # Check disks
            disks = realtime.get("disks", {})
            if isinstance(disks, dict) and disks:
                for dinfo in disks.values():
                    if isinstance(dinfo, dict):
                        rb = dinfo.get("read_bytes") or dinfo.get("read_bytes_rate")
                        if rb is not None:
                            try:
                                total_rb += float(rb)
                                found = True
                            except (ValueError, TypeError):
                                pass
            if found:
                return round(total_rb / (1024 * 1024), 2)

            # Fallback check pools
            pools = realtime.get("pools", {})
            if isinstance(pools, dict) and pools:
                for pinfo in pools.values():
                    if isinstance(pinfo, dict):
                        rb = pinfo.get("read_bytes") or pinfo.get("bytes_read") or pinfo.get("read_bytes_rate")
                        if rb is not None:
                            try:
                                total_rb += float(rb)
                                found = True
                            except (ValueError, TypeError):
                                pass
            if found:
                return round(total_rb / (1024 * 1024), 2)
        return 0.0


class TrueNASSystemDiskWriteRateSensor(TrueNASBaseSensor):
    """Aggregated System Disk Write Rate sensor across all disks/pools in MB/s."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "system_disk_write_rate", "System Disk Write Rate")
        self._attr_unique_id = f"{entry.entry_id}_system_disk_write_rate"
        self._attr_device_class = SensorDeviceClass.DATA_RATE
        self._attr_native_unit_of_measurement = UnitOfDataRate.MEGABYTES_PER_SECOND
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:harddisk-plus"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            total_wb = 0.0
            found = False
            # Check disks
            disks = realtime.get("disks", {})
            if isinstance(disks, dict) and disks:
                for dinfo in disks.values():
                    if isinstance(dinfo, dict):
                        wb = dinfo.get("write_bytes") or dinfo.get("write_bytes_rate")
                        if wb is not None:
                            try:
                                total_wb += float(wb)
                                found = True
                            except (ValueError, TypeError):
                                pass
            if found:
                return round(total_wb / (1024 * 1024), 2)

            # Fallback check pools
            pools = realtime.get("pools", {})
            if isinstance(pools, dict) and pools:
                for pinfo in pools.values():
                    if isinstance(pinfo, dict):
                        wb = pinfo.get("write_bytes") or pinfo.get("bytes_written") or pinfo.get("write_bytes_rate")
                        if wb is not None:
                            try:
                                total_wb += float(wb)
                                found = True
                            except (ValueError, TypeError):
                                pass
            if found:
                return round(total_wb / (1024 * 1024), 2)
        return 0.0


class TrueNASSystemDiskReadIOPSSensor(TrueNASBaseSensor):
    """Aggregated System Disk Read IOPS sensor across all disks/pools."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "system_disk_read_iops", "System Disk Read IOPS")
        self._attr_unique_id = f"{entry.entry_id}_system_disk_read_iops"
        self._attr_native_unit_of_measurement = "ops/s"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:harddisk-search"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            total_ro = 0.0
            found = False
            disks = realtime.get("disks", {})
            if isinstance(disks, dict) and disks:
                for dinfo in disks.values():
                    if isinstance(dinfo, dict):
                        ro = dinfo.get("read_ops") or dinfo.get("read_ops_rate")
                        if ro is not None:
                            try:
                                total_ro += float(ro)
                                found = True
                            except (ValueError, TypeError):
                                pass
            if found:
                return round(total_ro, 1)
        return 0.0


class TrueNASSystemDiskWriteIOPSSensor(TrueNASBaseSensor):
    """Aggregated System Disk Write IOPS sensor across all disks/pools."""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "system_disk_write_iops", "System Disk Write IOPS")
        self._attr_unique_id = f"{entry.entry_id}_system_disk_write_iops"
        self._attr_native_unit_of_measurement = "ops/s"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self) -> str:
        return "mdi:harddisk"

    @property
    def native_value(self) -> Optional[float]:
        realtime = self.coordinator.data.get(DATA_REALTIME, {})
        if isinstance(realtime, dict):
            total_wo = 0.0
            found = False
            disks = realtime.get("disks", {})
            if isinstance(disks, dict) and disks:
                for dinfo in disks.values():
                    if isinstance(dinfo, dict):
                        wo = dinfo.get("write_ops") or dinfo.get("write_ops_rate")
                        if wo is not None:
                            try:
                                total_wo += float(wo)
                                found = True
                            except (ValueError, TypeError):
                                pass
            if found:
                return round(total_wo, 1)
        return 0.0
