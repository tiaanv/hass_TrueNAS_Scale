"""Tests for TrueNAS Scale sensor platform."""

import asyncio
import unittest
from unittest.mock import MagicMock

from custom_components.truenas_scale.const import (
    DATA_DATASETS,
    DATA_DISKS,
    DATA_DISK_TEMPS,
    DATA_INTERFACES,
    DATA_POOLS,
    DATA_REALTIME,
    DATA_SERVICES,
    DATA_SYSTEM_INFO,
    DATA_VMS,
    DOMAIN,
)
from custom_components.truenas_scale.sensor import (
    TrueNASCPULoad15mSensor,
    TrueNASCPULoad1mSensor,
    TrueNASCPULoad5mSensor,
    TrueNASCPUTemperatureSensor,
    TrueNASCPUUsageSensor,
    TrueNASDatasetUsedSensor,
    TrueNASDiskTemperatureSensor,
    TrueNASMemoryAvailableSensor,
    TrueNASMemoryTotalSensor,
    TrueNASMemoryUsageSensor,
    TrueNASMemoryUsedSensor,
    TrueNASNetworkRxSensor,
    TrueNASNetworkTxSensor,
    TrueNASPoolFreeSensor,
    TrueNASPoolReadIOPSSensor,
    TrueNASPoolReadRateSensor,
    TrueNASPoolUsableCapacitySensor,
    TrueNASPoolUsageSensor,
    TrueNASPoolUsedSpaceSensor,
    TrueNASPoolWriteIOPSSensor,
    TrueNASPoolWriteRateSensor,
    TrueNASSystemDiskReadIOPSSensor,
    TrueNASSystemDiskReadRateSensor,
    TrueNASSystemDiskWriteIOPSSensor,
    TrueNASSystemDiskWriteRateSensor,
    TrueNASUptimeSensor,
    TrueNASZFSARCSizeSensor,
    async_setup_entry,
)


class TestTrueNASSensors(unittest.TestCase):
    """Test Sensor Entities."""

    def setUp(self):
        self.coordinator = MagicMock()
        self.coordinator.data = {
            DATA_SYSTEM_INFO: {
                "hostname": "truenas-scale",
                "uptime": "10 days, 2 hours",
                "uptime_seconds": 871200.0,
                "cores": 8,
                "physmem": 68719476736,
                "loadavg": [0.45, 0.32, 0.28],
            },
            DATA_POOLS: {
                "Volume1": {
                    "name": "Volume1",
                    "status": "ONLINE",
                    "healthy": True,
                    "size": 109951162777600,
                    "allocated": 94250000000000,
                    "free": 15701162777600,
                }
            },
            DATA_DATASETS: {
                "Volume1": {
                    "id": "Volume1",
                    "name": "Volume1",
                    "used": {"parsed": 75594115000000},
                    "available": {"parsed": 13281900000000},
                }
            },
            DATA_DISKS: {"sda": {"name": "sda", "temp": 35}},
            DATA_DISK_TEMPS: {"sda": 35},
            DATA_REALTIME: {
                "cpu": {
                    "cpu0": {"usage": 15.0, "temp": 42.0},
                    "cpu1": {"usage": 25.0, "temp": 44.0},
                },
                "memory": {
                    "physical_memory_total": 68719476736,
                    "physical_memory_available": 34359738368,
                    "arc_size": 17179869184,
                },
                "disks": {
                    "sda": {"read_bytes": 1048576, "write_bytes": 2097152, "read_ops": 15.0, "write_ops": 25.0},
                },
                "pools": {
                    "Volume1": {"read_bytes": 1048576, "write_bytes": 2097152, "read_ops": 10.0, "write_ops": 20.0},
                },
                "interfaces": {
                    "eno1": {"received_bytes_rate": 5242880, "sent_bytes_rate": 10485760},
                },
            },
            DATA_INTERFACES: {"eno1": {"id": "eno1"}},
        }

        self.entry = MagicMock()
        self.entry.entry_id = "test_entry_id"
        self.entry.data = {"host": "192.168.1.100"}

    def test_uptime_sensor(self):
        # DURATION device class requires a numeric value in seconds, not the
        # human-readable "uptime" string TrueNAS also returns.
        sensor = TrueNASUptimeSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 871200.0)

    def test_cpu_usage_sensor(self):
        sensor = TrueNASCPUUsageSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 20.0)

    def test_cpu_usage_sensor_fallback(self):
        self.coordinator.data[DATA_REALTIME] = {}
        sensor = TrueNASCPUUsageSensor(self.coordinator, self.entry)
        # loadavg[0]=0.45 / 8 cores * 100 = 5.625 -> 5.6
        self.assertEqual(sensor.native_value, 5.6)

    def test_cpu_temperature_sensor(self):
        sensor = TrueNASCPUTemperatureSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 43.0)

    def test_cpu_load_avg_sensors(self):
        s1 = TrueNASCPULoad1mSensor(self.coordinator, self.entry)
        s5 = TrueNASCPULoad5mSensor(self.coordinator, self.entry)
        s15 = TrueNASCPULoad15mSensor(self.coordinator, self.entry)

        self.assertEqual(s1.native_value, 0.45)
        self.assertEqual(s5.native_value, 0.32)
        self.assertEqual(s15.native_value, 0.28)

    def test_memory_usage_sensor(self):
        sensor = TrueNASMemoryUsageSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 50.0)

    def test_memory_used_available_sensors(self):
        u_sensor = TrueNASMemoryUsedSensor(self.coordinator, self.entry)
        a_sensor = TrueNASMemoryAvailableSensor(self.coordinator, self.entry)

        # 34359738368 bytes / (1024^3) = 32.0 GB
        self.assertEqual(u_sensor.native_value, 32.0)
        self.assertEqual(a_sensor.native_value, 32.0)

    def test_memory_total_sensor(self):
        sensor = TrueNASMemoryTotalSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 64.0)

    def test_zfs_arc_size_sensor(self):
        sensor = TrueNASZFSARCSizeSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 16.0)

    def test_pool_usable_capacity_sensor(self):
        sensor = TrueNASPoolUsableCapacitySensor(self.coordinator, self.entry, "Volume1")
        self.assertEqual(sensor.native_value, 88876015000000)

    def test_pool_free_sensor(self):
        sensor = TrueNASPoolFreeSensor(self.coordinator, self.entry, "Volume1")
        self.assertEqual(sensor.native_value, 13281900000000)
        self.assertIn("available_bytes", sensor.extra_state_attributes)

    def test_pool_used_sensor(self):
        sensor = TrueNASPoolUsedSpaceSensor(self.coordinator, self.entry, "Volume1")
        self.assertEqual(sensor.native_value, 75594115000000)

    def test_pool_usage_sensor(self):
        sensor = TrueNASPoolUsageSensor(self.coordinator, self.entry, "Volume1")
        # 75594115000000 / 88876015000000 * 100 = 85.05 -> 85.1
        self.assertEqual(sensor.native_value, 85.1)

    def test_pool_io_sensors(self):
        pr_sensor = TrueNASPoolReadRateSensor(self.coordinator, self.entry, "Volume1")
        pw_sensor = TrueNASPoolWriteRateSensor(self.coordinator, self.entry, "Volume1")
        pri_sensor = TrueNASPoolReadIOPSSensor(self.coordinator, self.entry, "Volume1")
        pwi_sensor = TrueNASPoolWriteIOPSSensor(self.coordinator, self.entry, "Volume1")

        # 1048576 / (1024^2) = 1.0 MB/s
        self.assertEqual(pr_sensor.native_value, 1.0)
        # 2097152 / (1024^2) = 2.0 MB/s
        self.assertEqual(pw_sensor.native_value, 2.0)
        self.assertEqual(pri_sensor.native_value, 10.0)
        self.assertEqual(pwi_sensor.native_value, 20.0)

    def test_system_disk_io_sensors(self):
        sr_sensor = TrueNASSystemDiskReadRateSensor(self.coordinator, self.entry)
        sw_sensor = TrueNASSystemDiskWriteRateSensor(self.coordinator, self.entry)
        sri_sensor = TrueNASSystemDiskReadIOPSSensor(self.coordinator, self.entry)
        swi_sensor = TrueNASSystemDiskWriteIOPSSensor(self.coordinator, self.entry)

        self.assertEqual(sr_sensor.native_value, 1.0)
        self.assertEqual(sw_sensor.native_value, 2.0)
        self.assertEqual(sri_sensor.native_value, 15.0)
        self.assertEqual(swi_sensor.native_value, 25.0)

    def test_network_rx_tx_sensors(self):
        rx_sensor = TrueNASNetworkRxSensor(self.coordinator, self.entry, "eno1")
        tx_sensor = TrueNASNetworkTxSensor(self.coordinator, self.entry, "eno1")

        self.assertEqual(rx_sensor.native_value, 5.0)
        self.assertEqual(tx_sensor.native_value, 10.0)

    def test_disk_temperature_sensor(self):
        sensor = TrueNASDiskTemperatureSensor(self.coordinator, self.entry, "sda")
        self.assertEqual(sensor.native_value, 35.0)

    def test_dataset_used_sensor(self):
        sensor = TrueNASDatasetUsedSensor(self.coordinator, self.entry, "Volume1")
        self.assertEqual(sensor.native_value, 75594115000000)

    def test_dataset_used_sensor_missing_and_invalid(self):
        sensor = TrueNASDatasetUsedSensor(self.coordinator, self.entry, "missing")
        self.assertIsNone(sensor.native_value)

        self.coordinator.data[DATA_DATASETS]["Volume1"]["used"] = "not-a-number"
        sensor = TrueNASDatasetUsedSensor(self.coordinator, self.entry, "Volume1")
        self.assertIsNone(sensor.native_value)

    def test_async_setup_entry_creates_all_sensors(self):
        hass = MagicMock()
        entry = self.entry
        entry.entry_id = "test_entry_id"
        hass.data = {DOMAIN: {entry.entry_id: {"coordinator": self.coordinator}}}

        added = []
        asyncio.run(async_setup_entry(hass, entry, added.extend))

        # 15 system sensors + 8/pool + 1/dataset + 1/disk + 2/interface
        self.assertEqual(len(added), 15 + 8 + 1 + 1 + 2)

    def test_device_info(self):
        sensor = TrueNASUptimeSensor(self.coordinator, self.entry)
        info = sensor.device_info

        self.assertEqual(info["identifiers"], {(DOMAIN, self.entry.entry_id)})
        self.assertEqual(info["name"], "TrueNAS (truenas-scale)")
        self.assertEqual(info["manufacturer"], "iXsystems")
        self.assertEqual(info["model"], "TrueNAS Scale")
        self.assertEqual(info["sw_version"], "26.0")

    def test_device_info_falls_back_to_host_and_defaults(self):
        self.coordinator.data[DATA_SYSTEM_INFO] = {}
        sensor = TrueNASUptimeSensor(self.coordinator, self.entry)
        info = sensor.device_info

        self.assertEqual(info["name"], "TrueNAS (192.168.1.100)")
        self.assertEqual(info["model"], "TrueNAS Scale")
        self.assertEqual(info["sw_version"], "26.0")

    def test_icons(self):
        checks = [
            (TrueNASUptimeSensor(self.coordinator, self.entry), "mdi:clock-outline"),
            (TrueNASCPUUsageSensor(self.coordinator, self.entry), "mdi:cpu-64-bit"),
            (TrueNASCPUTemperatureSensor(self.coordinator, self.entry), "mdi:thermometer"),
            (TrueNASCPULoad1mSensor(self.coordinator, self.entry), "mdi:cpu-64-bit"),
            (TrueNASCPULoad5mSensor(self.coordinator, self.entry), "mdi:cpu-64-bit"),
            (TrueNASCPULoad15mSensor(self.coordinator, self.entry), "mdi:cpu-64-bit"),
            (TrueNASMemoryUsageSensor(self.coordinator, self.entry), "mdi:memory"),
            (TrueNASMemoryUsedSensor(self.coordinator, self.entry), "mdi:memory"),
            (TrueNASMemoryAvailableSensor(self.coordinator, self.entry), "mdi:memory"),
            (TrueNASMemoryTotalSensor(self.coordinator, self.entry), "mdi:memory"),
            (TrueNASZFSARCSizeSensor(self.coordinator, self.entry), "mdi:database-clock"),
            (TrueNASPoolUsageSensor(self.coordinator, self.entry, "Volume1"), "mdi:database"),
            (TrueNASPoolFreeSensor(self.coordinator, self.entry, "Volume1"), "mdi:database-search"),
            (TrueNASPoolUsedSpaceSensor(self.coordinator, self.entry, "Volume1"), "mdi:database-arrow-right"),
            (TrueNASPoolUsableCapacitySensor(self.coordinator, self.entry, "Volume1"), "mdi:database"),
            (TrueNASPoolReadRateSensor(self.coordinator, self.entry, "Volume1"), "mdi:database-arrow-down"),
            (TrueNASPoolWriteRateSensor(self.coordinator, self.entry, "Volume1"), "mdi:database-arrow-up"),
            (TrueNASPoolReadIOPSSensor(self.coordinator, self.entry, "Volume1"), "mdi:database-search"),
            (TrueNASPoolWriteIOPSSensor(self.coordinator, self.entry, "Volume1"), "mdi:database-edit"),
            (TrueNASDatasetUsedSensor(self.coordinator, self.entry, "Volume1"), "mdi:folder-database"),
            (TrueNASDiskTemperatureSensor(self.coordinator, self.entry, "sda"), "mdi:harddisk"),
            (TrueNASNetworkRxSensor(self.coordinator, self.entry, "eno1"), "mdi:download-network"),
            (TrueNASNetworkTxSensor(self.coordinator, self.entry, "eno1"), "mdi:upload-network"),
            (TrueNASSystemDiskReadRateSensor(self.coordinator, self.entry), "mdi:harddisk-remove"),
            (TrueNASSystemDiskWriteRateSensor(self.coordinator, self.entry), "mdi:harddisk-plus"),
            (TrueNASSystemDiskReadIOPSSensor(self.coordinator, self.entry), "mdi:harddisk-search"),
            (TrueNASSystemDiskWriteIOPSSensor(self.coordinator, self.entry), "mdi:harddisk"),
        ]
        for sensor, expected_icon in checks:
            self.assertEqual(sensor.icon, expected_icon, msg=type(sensor).__name__)

    def test_uptime_sensor_string_fallback_and_invalid(self):
        self.coordinator.data[DATA_SYSTEM_INFO] = {"uptime_seconds": "not-a-number", "uptime": "3600"}
        sensor = TrueNASUptimeSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 3600.0)

        self.coordinator.data[DATA_SYSTEM_INFO] = {"uptime": "10 days, 2 hours"}
        sensor = TrueNASUptimeSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

        self.coordinator.data[DATA_SYSTEM_INFO] = {}
        sensor = TrueNASUptimeSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

    def test_cpu_load_avg_sensors_missing_and_invalid(self):
        self.coordinator.data[DATA_SYSTEM_INFO]["loadavg"] = None
        s1 = TrueNASCPULoad1mSensor(self.coordinator, self.entry)
        s5 = TrueNASCPULoad5mSensor(self.coordinator, self.entry)
        s15 = TrueNASCPULoad15mSensor(self.coordinator, self.entry)
        self.assertIsNone(s1.native_value)
        self.assertIsNone(s5.native_value)
        self.assertIsNone(s15.native_value)

        self.coordinator.data[DATA_SYSTEM_INFO]["loadavg"] = ["bad", "bad", "bad"]
        s1 = TrueNASCPULoad1mSensor(self.coordinator, self.entry)
        s5 = TrueNASCPULoad5mSensor(self.coordinator, self.entry)
        s15 = TrueNASCPULoad15mSensor(self.coordinator, self.entry)
        self.assertIsNone(s1.native_value)
        self.assertIsNone(s5.native_value)
        self.assertIsNone(s15.native_value)

    def test_memory_usage_sensor_total_avail_fallback(self):
        self.coordinator.data[DATA_REALTIME]["memory"] = {
            "physical_memory_total": 100.0,
            "physical_memory_available": 25.0,
        }
        sensor = TrueNASMemoryUsageSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 75.0)

    def test_memory_usage_sensor_invalid_and_missing(self):
        self.coordinator.data[DATA_REALTIME]["memory"] = {"usage_percent": "bad"}
        sensor = TrueNASMemoryUsageSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

        self.coordinator.data[DATA_REALTIME] = {}
        sensor = TrueNASMemoryUsageSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

        self.coordinator.data[DATA_REALTIME] = "not-a-dict"
        sensor = TrueNASMemoryUsageSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

    def test_memory_usage_sensor_total_avail_invalid(self):
        self.coordinator.data[DATA_REALTIME]["memory"] = {
            "physical_memory_total": "bad",
            "physical_memory_available": "bad",
        }
        sensor = TrueNASMemoryUsageSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

    def test_memory_used_available_total_invalid_and_missing(self):
        self.coordinator.data[DATA_REALTIME]["memory"] = {}
        u_sensor = TrueNASMemoryUsedSensor(self.coordinator, self.entry)
        a_sensor = TrueNASMemoryAvailableSensor(self.coordinator, self.entry)
        self.assertIsNone(u_sensor.native_value)
        self.assertIsNone(a_sensor.native_value)

        self.coordinator.data[DATA_REALTIME]["memory"] = {
            "physical_memory_total": "bad",
            "physical_memory_available": "bad",
        }
        u_sensor = TrueNASMemoryUsedSensor(self.coordinator, self.entry)
        a_sensor = TrueNASMemoryAvailableSensor(self.coordinator, self.entry)
        self.assertIsNone(u_sensor.native_value)
        self.assertIsNone(a_sensor.native_value)

    def test_memory_total_sensor_physmem_fallback_and_invalid(self):
        self.coordinator.data[DATA_REALTIME] = {}
        sensor = TrueNASMemoryTotalSensor(self.coordinator, self.entry)
        # physmem 68719476736 bytes / (1024^3) = 64.0 GB
        self.assertEqual(sensor.native_value, 64.0)

        self.coordinator.data[DATA_SYSTEM_INFO]["physmem"] = "bad"
        sensor = TrueNASMemoryTotalSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

        del self.coordinator.data[DATA_SYSTEM_INFO]["physmem"]
        sensor = TrueNASMemoryTotalSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

    def test_memory_total_sensor_realtime_invalid_falls_back_to_physmem(self):
        self.coordinator.data[DATA_REALTIME]["memory"] = {"physical_memory_total": "bad"}
        sensor = TrueNASMemoryTotalSensor(self.coordinator, self.entry)
        # physmem 68719476736 bytes / (1024^3) = 64.0 GB
        self.assertEqual(sensor.native_value, 64.0)

    def test_zfs_arc_size_sensor_zfs_fallback_and_invalid(self):
        self.coordinator.data[DATA_REALTIME]["memory"] = {}
        self.coordinator.data[DATA_REALTIME]["zfs"] = {"arc_size": 8589934592}
        sensor = TrueNASZFSARCSizeSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 8.0)

        self.coordinator.data[DATA_REALTIME]["memory"] = {"arc_size": "bad"}
        self.coordinator.data[DATA_REALTIME]["zfs"] = {"arc_size": "bad"}
        sensor = TrueNASZFSARCSizeSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

        self.coordinator.data[DATA_REALTIME] = {}
        sensor = TrueNASZFSARCSizeSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

    def test_get_pool_dataset_bytes_via_pool_embedded_dataset(self):
        # No matching entry under DATA_DATASETS: fall back to a dataset-like
        # object embedded directly on the pool (root_dataset/properties).
        self.coordinator.data[DATA_DATASETS] = {}
        self.coordinator.data[DATA_POOLS]["Volume1"]["root_dataset"] = {
            "used": 500,
            "available": 100,
        }
        sensor = TrueNASPoolUsedSpaceSensor(self.coordinator, self.entry, "Volume1")
        self.assertEqual(sensor.native_value, 500)
        free_sensor = TrueNASPoolFreeSensor(self.coordinator, self.entry, "Volume1")
        self.assertEqual(free_sensor.native_value, 100)

    def test_get_pool_dataset_bytes_matches_by_mountpoint(self):
        self.coordinator.data[DATA_DATASETS] = {
            "other-id": {
                "id": "other-id",
                "mountpoint": "/Volume1",
                "used": {"rawvalue": 300},
                "available": {"rawvalue": 200},
            }
        }
        sensor = TrueNASPoolUsedSpaceSensor(self.coordinator, self.entry, "Volume1")
        self.assertEqual(sensor.native_value, 300)

    def test_pool_usage_sensor_fallback_to_raw_pool_capacity(self):
        self.coordinator.data[DATA_DATASETS] = {}
        self.coordinator.data[DATA_POOLS]["Volume1"] = {
            "name": "Volume1",
            "size": 1000,
            "allocated": 250,
        }
        sensor = TrueNASPoolUsageSensor(self.coordinator, self.entry, "Volume1")
        self.assertEqual(sensor.native_value, 25.0)
        self.assertEqual(sensor.extra_state_attributes, {})

    def test_pool_usage_sensor_extra_state_attributes(self):
        sensor = TrueNASPoolUsageSensor(self.coordinator, self.entry, "Volume1")
        attrs = sensor.extra_state_attributes
        self.assertIn("available_bytes", attrs)
        self.assertIn("used_bytes", attrs)
        self.assertIn("total_usable_gb", attrs)

    def test_pool_usage_sensor_no_data(self):
        self.coordinator.data[DATA_DATASETS] = {}
        self.coordinator.data[DATA_POOLS] = {"Volume1": {"name": "Volume1"}}
        sensor = TrueNASPoolUsageSensor(self.coordinator, self.entry, "Volume1")
        self.assertIsNone(sensor.native_value)

    def test_pool_free_sensor_fallback_to_raw_pool_free(self):
        self.coordinator.data[DATA_DATASETS] = {}
        self.coordinator.data[DATA_POOLS]["Volume1"] = {"name": "Volume1", "free": 999}
        sensor = TrueNASPoolFreeSensor(self.coordinator, self.entry, "Volume1")
        self.assertEqual(sensor.native_value, 999)
        self.assertEqual(sensor.extra_state_attributes, {})

    def test_pool_free_sensor_no_data(self):
        self.coordinator.data[DATA_DATASETS] = {}
        self.coordinator.data[DATA_POOLS] = {"Volume1": {"name": "Volume1"}}
        sensor = TrueNASPoolFreeSensor(self.coordinator, self.entry, "Volume1")
        self.assertIsNone(sensor.native_value)

    def test_pool_used_space_sensor_fallback_to_allocated(self):
        self.coordinator.data[DATA_DATASETS] = {}
        self.coordinator.data[DATA_POOLS]["Volume1"] = {"name": "Volume1", "allocated": 777}
        sensor = TrueNASPoolUsedSpaceSensor(self.coordinator, self.entry, "Volume1")
        self.assertEqual(sensor.native_value, 777)
        self.assertEqual(sensor.extra_state_attributes, {})

    def test_pool_used_space_sensor_extra_state_attributes(self):
        sensor = TrueNASPoolUsedSpaceSensor(self.coordinator, self.entry, "Volume1")
        attrs = sensor.extra_state_attributes
        self.assertIn("used_bytes", attrs)
        self.assertIn("available_bytes", attrs)

    def test_pool_used_space_sensor_no_data(self):
        self.coordinator.data[DATA_DATASETS] = {}
        self.coordinator.data[DATA_POOLS] = {"Volume1": {"name": "Volume1"}}
        sensor = TrueNASPoolUsedSpaceSensor(self.coordinator, self.entry, "Volume1")
        self.assertIsNone(sensor.native_value)

    def test_pool_usable_capacity_sensor_fallback_to_size_and_attrs(self):
        sensor = TrueNASPoolUsableCapacitySensor(self.coordinator, self.entry, "Volume1")
        attrs = sensor.extra_state_attributes
        self.assertEqual(attrs["total_usable_bytes"], 88876015000000)

        self.coordinator.data[DATA_DATASETS] = {}
        self.coordinator.data[DATA_POOLS]["Volume1"] = {"name": "Volume1", "size": 4242}
        sensor = TrueNASPoolUsableCapacitySensor(self.coordinator, self.entry, "Volume1")
        self.assertEqual(sensor.native_value, 4242)
        self.assertEqual(sensor.extra_state_attributes, {})

    def test_pool_usable_capacity_sensor_no_data(self):
        self.coordinator.data[DATA_DATASETS] = {}
        self.coordinator.data[DATA_POOLS] = {"Volume1": {"name": "Volume1"}}
        sensor = TrueNASPoolUsableCapacitySensor(self.coordinator, self.entry, "Volume1")
        self.assertIsNone(sensor.native_value)

    def test_pool_sensors_fallback_when_dataset_values_invalid(self):
        # "parsed" present but non-numeric: the dataset-level conversion
        # raises, so each sensor must fall back to the raw ZFS pool fields
        # (size=109951162777600, allocated=94250000000000, free=15701162777600).
        self.coordinator.data[DATA_DATASETS]["Volume1"]["used"] = {"parsed": "bad"}
        self.coordinator.data[DATA_DATASETS]["Volume1"]["available"] = {"parsed": "bad"}

        usage_sensor = TrueNASPoolUsageSensor(self.coordinator, self.entry, "Volume1")
        free_sensor = TrueNASPoolFreeSensor(self.coordinator, self.entry, "Volume1")
        used_sensor = TrueNASPoolUsedSpaceSensor(self.coordinator, self.entry, "Volume1")
        capacity_sensor = TrueNASPoolUsableCapacitySensor(self.coordinator, self.entry, "Volume1")

        self.assertAlmostEqual(usage_sensor.native_value, 85.7, delta=0.1)
        self.assertEqual(free_sensor.native_value, 15701162777600)
        self.assertEqual(used_sensor.native_value, 94250000000000)
        self.assertEqual(capacity_sensor.native_value, 109951162777600)

        # extra_state_attributes must not crash on the same non-numeric
        # "parsed" values - it has no raw-pool fallback, so it should just
        # omit the attributes it couldn't compute rather than raising.
        self.assertEqual(usage_sensor.extra_state_attributes, {})
        self.assertEqual(free_sensor.extra_state_attributes, {})
        self.assertEqual(used_sensor.extra_state_attributes, {})
        self.assertEqual(capacity_sensor.extra_state_attributes, {})

    def test_pool_sensors_return_none_when_all_data_invalid(self):
        self.coordinator.data[DATA_DATASETS] = {}
        self.coordinator.data[DATA_POOLS]["Volume1"] = {
            "name": "Volume1",
            "size": "bad",
            "allocated": "bad",
            "free": "bad",
        }

        usage_sensor = TrueNASPoolUsageSensor(self.coordinator, self.entry, "Volume1")
        free_sensor = TrueNASPoolFreeSensor(self.coordinator, self.entry, "Volume1")
        used_sensor = TrueNASPoolUsedSpaceSensor(self.coordinator, self.entry, "Volume1")
        capacity_sensor = TrueNASPoolUsableCapacitySensor(self.coordinator, self.entry, "Volume1")

        self.assertIsNone(usage_sensor.native_value)
        self.assertIsNone(free_sensor.native_value)
        self.assertIsNone(used_sensor.native_value)
        self.assertIsNone(capacity_sensor.native_value)

    def test_disk_temperature_sensor_disks_fallback_and_alt_key(self):
        self.coordinator.data[DATA_DISK_TEMPS] = {}
        self.coordinator.data[DATA_DISKS]["sda"] = {"name": "sda", "temperature": 40}
        sensor = TrueNASDiskTemperatureSensor(self.coordinator, self.entry, "sda")
        self.assertEqual(sensor.native_value, 40.0)

    def test_disk_temperature_sensor_no_data(self):
        self.coordinator.data[DATA_DISK_TEMPS] = {}
        self.coordinator.data[DATA_DISKS] = {}
        sensor = TrueNASDiskTemperatureSensor(self.coordinator, self.entry, "sda")
        self.assertIsNone(sensor.native_value)

    def test_disk_temperature_sensor_invalid_values(self):
        self.coordinator.data[DATA_DISK_TEMPS]["sda"] = "bad"
        self.coordinator.data[DATA_DISKS]["sda"]["temp"] = "also-bad"
        sensor = TrueNASDiskTemperatureSensor(self.coordinator, self.entry, "sda")
        self.assertIsNone(sensor.native_value)

    def test_cpu_usage_sensor_aggregate_and_toplevel_branches(self):
        self.coordinator.data[DATA_REALTIME]["cpu"] = {"cpu": {"usage": 55.0}}
        sensor = TrueNASCPUUsageSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 55.0)

        self.coordinator.data[DATA_REALTIME]["cpu"] = {"usage": 33.0}
        sensor = TrueNASCPUUsageSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 33.0)

        self.coordinator.data[DATA_REALTIME]["cpu"] = 42.0
        sensor = TrueNASCPUUsageSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 42.0)

    def test_cpu_usage_sensor_no_data(self):
        self.coordinator.data[DATA_REALTIME] = {}
        self.coordinator.data[DATA_SYSTEM_INFO]["loadavg"] = None
        sensor = TrueNASCPUUsageSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

        self.coordinator.data[DATA_SYSTEM_INFO]["loadavg"] = ["bad"]
        sensor = TrueNASCPUUsageSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

    def test_cpu_usage_sensor_aggregate_invalid_falls_back_to_per_core(self):
        self.coordinator.data[DATA_REALTIME]["cpu"] = {
            "cpu": {"usage": "bad"},
            "cpu0": {"usage": 10.0},
        }
        sensor = TrueNASCPUUsageSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 10.0)

    def test_cpu_usage_sensor_per_core_invalid_and_direct_numeric(self):
        self.coordinator.data[DATA_REALTIME]["cpu"] = {
            "cpu0": {"usage": "bad"},
            "cpu2": 33.0,
        }
        sensor = TrueNASCPUUsageSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 33.0)

    def test_cpu_usage_sensor_toplevel_invalid_falls_back_to_loadavg(self):
        self.coordinator.data[DATA_REALTIME]["cpu"] = {"usage": "bad"}
        sensor = TrueNASCPUUsageSensor(self.coordinator, self.entry)
        # loadavg[0]=0.45 / 8 cores * 100 = 5.625 -> 5.6
        self.assertEqual(sensor.native_value, 5.6)

    def test_cpu_temperature_sensor_aggregate_and_toplevel_branches(self):
        self.coordinator.data[DATA_REALTIME]["cpu"] = {"cpu": {"temp": 60.0}}
        sensor = TrueNASCPUTemperatureSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 60.0)

        self.coordinator.data[DATA_REALTIME]["cpu"] = {"temperature": 50.0}
        sensor = TrueNASCPUTemperatureSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 50.0)

        self.coordinator.data[DATA_REALTIME]["cpu"] = 47.0
        sensor = TrueNASCPUTemperatureSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 47.0)

    def test_cpu_temperature_sensor_no_data(self):
        self.coordinator.data[DATA_REALTIME] = {}
        sensor = TrueNASCPUTemperatureSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

        self.coordinator.data[DATA_REALTIME]["cpu"] = {"cpu0": {"temp": "bad"}}
        sensor = TrueNASCPUTemperatureSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

    def test_cpu_temperature_sensor_aggregate_invalid_falls_back_to_per_core(self):
        self.coordinator.data[DATA_REALTIME]["cpu"] = {
            "cpu": {"temp": "bad"},
            "cpu0": {"temp": 50.0},
        }
        sensor = TrueNASCPUTemperatureSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 50.0)

    def test_cpu_temperature_sensor_direct_numeric_core(self):
        self.coordinator.data[DATA_REALTIME]["cpu"] = {"cpu1": 45.0}
        sensor = TrueNASCPUTemperatureSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, 45.0)

    def test_cpu_temperature_sensor_toplevel_invalid_returns_none(self):
        self.coordinator.data[DATA_REALTIME]["cpu"] = {"temperature": "bad"}
        sensor = TrueNASCPUTemperatureSensor(self.coordinator, self.entry)
        self.assertIsNone(sensor.native_value)

    def test_network_rx_tx_sensors_no_data_and_invalid(self):
        rx_sensor = TrueNASNetworkRxSensor(self.coordinator, self.entry, "missing-iface")
        tx_sensor = TrueNASNetworkTxSensor(self.coordinator, self.entry, "missing-iface")
        self.assertEqual(rx_sensor.native_value, 0.0)
        self.assertEqual(tx_sensor.native_value, 0.0)

        self.coordinator.data[DATA_REALTIME]["interfaces"]["eno1"]["received_bytes_rate"] = "bad"
        self.coordinator.data[DATA_REALTIME]["interfaces"]["eno1"]["sent_bytes_rate"] = "bad"
        rx_sensor = TrueNASNetworkRxSensor(self.coordinator, self.entry, "eno1")
        tx_sensor = TrueNASNetworkTxSensor(self.coordinator, self.entry, "eno1")
        self.assertEqual(rx_sensor.native_value, 0.0)
        self.assertEqual(tx_sensor.native_value, 0.0)

    def test_pool_io_sensors_no_data_and_invalid(self):
        pr_sensor = TrueNASPoolReadRateSensor(self.coordinator, self.entry, "missing-pool")
        pw_sensor = TrueNASPoolWriteRateSensor(self.coordinator, self.entry, "missing-pool")
        pri_sensor = TrueNASPoolReadIOPSSensor(self.coordinator, self.entry, "missing-pool")
        pwi_sensor = TrueNASPoolWriteIOPSSensor(self.coordinator, self.entry, "missing-pool")
        self.assertEqual(pr_sensor.native_value, 0.0)
        self.assertEqual(pw_sensor.native_value, 0.0)
        self.assertEqual(pri_sensor.native_value, 0.0)
        self.assertEqual(pwi_sensor.native_value, 0.0)

        self.coordinator.data[DATA_REALTIME]["pools"]["Volume1"] = {
            "read_bytes": "bad",
            "write_bytes": "bad",
            "read_ops": "bad",
            "write_ops": "bad",
        }
        pr_sensor = TrueNASPoolReadRateSensor(self.coordinator, self.entry, "Volume1")
        pw_sensor = TrueNASPoolWriteRateSensor(self.coordinator, self.entry, "Volume1")
        pri_sensor = TrueNASPoolReadIOPSSensor(self.coordinator, self.entry, "Volume1")
        pwi_sensor = TrueNASPoolWriteIOPSSensor(self.coordinator, self.entry, "Volume1")
        self.assertEqual(pr_sensor.native_value, 0.0)
        self.assertEqual(pw_sensor.native_value, 0.0)
        self.assertEqual(pri_sensor.native_value, 0.0)
        self.assertEqual(pwi_sensor.native_value, 0.0)

    def test_system_disk_io_sensors_pools_fallback(self):
        self.coordinator.data[DATA_REALTIME]["disks"] = {}
        sr_sensor = TrueNASSystemDiskReadRateSensor(self.coordinator, self.entry)
        sw_sensor = TrueNASSystemDiskWriteRateSensor(self.coordinator, self.entry)
        # Read/write IOPS sensors only aggregate the "disks" source, not pools.
        self.assertEqual(sr_sensor.native_value, 1.0)
        self.assertEqual(sw_sensor.native_value, 2.0)

    def test_system_disk_io_sensors_no_data_and_invalid(self):
        self.coordinator.data[DATA_REALTIME] = {}
        sr_sensor = TrueNASSystemDiskReadRateSensor(self.coordinator, self.entry)
        sw_sensor = TrueNASSystemDiskWriteRateSensor(self.coordinator, self.entry)
        sri_sensor = TrueNASSystemDiskReadIOPSSensor(self.coordinator, self.entry)
        swi_sensor = TrueNASSystemDiskWriteIOPSSensor(self.coordinator, self.entry)
        self.assertEqual(sr_sensor.native_value, 0.0)
        self.assertEqual(sw_sensor.native_value, 0.0)
        self.assertEqual(sri_sensor.native_value, 0.0)
        self.assertEqual(swi_sensor.native_value, 0.0)

        self.coordinator.data[DATA_REALTIME] = {
            "disks": {"sda": {"read_bytes": "bad", "write_bytes": "bad", "read_ops": "bad", "write_ops": "bad"}},
            "pools": {"Volume1": {"read_bytes": "bad", "write_bytes": "bad"}},
        }
        sr_sensor = TrueNASSystemDiskReadRateSensor(self.coordinator, self.entry)
        sw_sensor = TrueNASSystemDiskWriteRateSensor(self.coordinator, self.entry)
        sri_sensor = TrueNASSystemDiskReadIOPSSensor(self.coordinator, self.entry)
        swi_sensor = TrueNASSystemDiskWriteIOPSSensor(self.coordinator, self.entry)
        self.assertEqual(sr_sensor.native_value, 0.0)
        self.assertEqual(sw_sensor.native_value, 0.0)
        self.assertEqual(sri_sensor.native_value, 0.0)
        self.assertEqual(swi_sensor.native_value, 0.0)
