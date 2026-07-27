"""Tests for TrueNAS Scale binary sensor platform."""

import unittest
from unittest.mock import MagicMock

from custom_components.truenas_scale.binary_sensor import (
    TrueNASAppBinarySensor,
    TrueNASPoolHealthyBinarySensor,
    TrueNASServiceBinarySensor,
    TrueNASSystemAlertsBinarySensor,
    TrueNASVMBinarySensor,
)
from custom_components.truenas_scale.const import (
    DATA_ALERTS,
    DATA_APPS,
    DATA_POOLS,
    DATA_SERVICES,
    DATA_VMS,
)


class TestTrueNASBinarySensors(unittest.TestCase):
    """Test Binary Sensor Entities."""

    def setUp(self):
        self.coordinator = MagicMock()
        self.coordinator.data = {
            DATA_ALERTS: [],
            DATA_POOLS: {"Volume1": {"name": "Volume1", "healthy": True}},
            DATA_SERVICES: {
                "smb": {"service": "smb", "state": "RUNNING"},
                "ssh": {"service": "ssh", "state": "STOPPED"},
                "nfs": {"service": "nfs", "state": "RUNNING"},
                "ftp": {"service": "ftp", "state": "STOPPED"},
                "iscsi": {"service": "iscsitarget", "state": "RUNNING"},
                "other": {"service": "other", "state": "RUNNING"},
            },
            DATA_APPS: {
                "plex": {
                    "name": "plex",
                    "state": "RUNNING",
                    "icon_url": "https://plex.tv/logo.png",
                }
            },
            DATA_VMS: {"ubuntu-server": {"name": "ubuntu-server", "status": {"state": "RUNNING"}}},
        }
        self.entry = MagicMock()
        self.entry.entry_id = "test_entry"
        self.entry.data = {"host": "192.168.1.100"}

    def test_alerts_binary_sensor(self):
        sensor = TrueNASSystemAlertsBinarySensor(self.coordinator, self.entry)
        self.assertFalse(sensor.is_on)

        self.coordinator.data[DATA_ALERTS] = [{"id": "alert1", "level": "WARNING"}]
        self.assertTrue(sensor.is_on)

    def test_pool_healthy_binary_sensor(self):
        sensor = TrueNASPoolHealthyBinarySensor(self.coordinator, self.entry, "Volume1")
        self.assertTrue(sensor.is_on)

    def test_service_binary_sensor_icons(self):
        smb_s = TrueNASServiceBinarySensor(self.coordinator, self.entry, "smb")
        ssh_s = TrueNASServiceBinarySensor(self.coordinator, self.entry, "ssh")
        nfs_s = TrueNASServiceBinarySensor(self.coordinator, self.entry, "nfs")
        ftp_s = TrueNASServiceBinarySensor(self.coordinator, self.entry, "ftp")
        iscsi_s = TrueNASServiceBinarySensor(self.coordinator, self.entry, "iscsi")
        other_s = TrueNASServiceBinarySensor(self.coordinator, self.entry, "other")

        self.assertEqual(smb_s.icon, "mdi:folder-network")
        self.assertEqual(ssh_s.icon, "mdi:console-network")
        self.assertEqual(nfs_s.icon, "mdi:share-network")
        self.assertEqual(ftp_s.icon, "mdi:file-transfer")
        self.assertEqual(iscsi_s.icon, "mdi:harddisk-network")
        self.assertEqual(other_s.icon, "mdi:cog-network")

        self.assertTrue(smb_s.is_on)
        self.assertFalse(ssh_s.is_on)

    def test_app_binary_sensor(self):
        sensor = TrueNASAppBinarySensor(self.coordinator, self.entry, "plex")
        self.assertTrue(sensor.is_on)
        self.assertEqual(sensor.entity_picture, "https://plex.tv/logo.png")

    def test_vm_binary_sensor(self):
        sensor = TrueNASVMBinarySensor(self.coordinator, self.entry, "ubuntu-server", "ubuntu-server")
        self.assertTrue(sensor.is_on)
        self.assertEqual(sensor.icon, "mdi:server")
