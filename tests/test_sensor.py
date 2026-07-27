"""Tests for TrueNAS Scale sensor platform."""

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
)


class TestTrueNASSensors(unittest.TestCase):
    """Test Sensor Entities."""

    def setUp(self):
        self.coordinator = MagicMock()
        self.coordinator.data = {
            DATA_SYSTEM_INFO: {
                "hostname": "truenas-scale",
                "uptime": "10 days, 2 hours",
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
        sensor = TrueNASUptimeSensor(self.coordinator, self.entry)
        self.assertEqual(sensor.native_value, "10 days, 2 hours")

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
