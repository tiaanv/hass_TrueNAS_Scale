"""Tests for TrueNAS Scale binary sensor platform."""

import unittest
from unittest.mock import MagicMock

from custom_components.truenas_scale.binary_sensor import (
    TrueNASAppBinarySensor,
    TrueNASPoolHealthyBinarySensor,
    TrueNASServiceBinarySensor,
    TrueNASSystemAlertsBinarySensor,
    TrueNASVMBinarySensor,
    async_setup_entry,
)
from custom_components.truenas_scale.const import (
    DATA_ALERTS,
    DATA_APPS,
    DATA_POOLS,
    DATA_SERVICES,
    DATA_SYSTEM_INFO,
    DATA_VMS,
    DOMAIN,
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
        # device_class PROBLEM: is_on means a problem is present, so a
        # healthy pool must report is_on == False.
        sensor = TrueNASPoolHealthyBinarySensor(self.coordinator, self.entry, "Volume1")
        self.assertFalse(sensor.is_on)

        self.coordinator.data[DATA_POOLS]["Volume1"]["healthy"] = False
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

        self.coordinator.data[DATA_VMS]["ubuntu-server"]["status"]["state"] = "STOPPED"
        self.assertFalse(sensor.is_on)
        self.assertEqual(sensor.icon, "mdi:server-off")

    def test_alerts_binary_sensor_icon(self):
        sensor = TrueNASSystemAlertsBinarySensor(self.coordinator, self.entry)
        self.assertEqual(sensor.icon, "mdi:alert-circle-outline")

    def test_pool_healthy_binary_sensor_icon(self):
        sensor = TrueNASPoolHealthyBinarySensor(self.coordinator, self.entry, "Volume1")
        self.assertEqual(sensor.icon, "mdi:database-check")

        self.coordinator.data[DATA_POOLS]["Volume1"]["healthy"] = False
        self.assertEqual(sensor.icon, "mdi:database-alert")

    def test_app_binary_sensor_icon(self):
        sensor = TrueNASAppBinarySensor(self.coordinator, self.entry, "plex")
        self.assertEqual(sensor.icon, "mdi:cube-outline")

    def test_app_binary_sensor_entity_picture_metadata_fallback(self):
        self.coordinator.data[DATA_APPS]["plex"].pop("icon_url", None)
        self.coordinator.data[DATA_APPS]["plex"]["metadata"] = {
            "icon": "https://plex.tv/metadata-logo.png"
        }
        sensor = TrueNASAppBinarySensor(self.coordinator, self.entry, "plex")
        self.assertEqual(sensor.entity_picture, "https://plex.tv/metadata-logo.png")

    def test_app_binary_sensor_entity_picture_none(self):
        self.coordinator.data[DATA_APPS]["plex"].pop("icon_url", None)
        sensor = TrueNASAppBinarySensor(self.coordinator, self.entry, "plex")
        self.assertIsNone(sensor.entity_picture)

    def test_device_info(self):
        self.coordinator.data[DATA_SYSTEM_INFO] = {
            "hostname": "truenas-scale",
            "model": "TRUENAS-CUSTOM",
            "version": "26.0.0",
        }
        sensor = TrueNASSystemAlertsBinarySensor(self.coordinator, self.entry)
        info = sensor.device_info

        self.assertEqual(info["identifiers"], {(DOMAIN, self.entry.entry_id)})
        self.assertEqual(info["name"], "TrueNAS (truenas-scale)")
        self.assertEqual(info["manufacturer"], "iXsystems")
        self.assertEqual(info["model"], "TRUENAS-CUSTOM")
        self.assertEqual(info["sw_version"], "26.0.0")

    def test_device_info_fallback_to_entry_host(self):
        # No hostname in system info: falls back to the config entry's host.
        sensor = TrueNASSystemAlertsBinarySensor(self.coordinator, self.entry)
        info = sensor.device_info

        self.assertEqual(info["name"], "TrueNAS (192.168.1.100)")
        self.assertEqual(info["model"], "TrueNAS Scale")
        self.assertEqual(info["sw_version"], "26.0")


class TestTrueNASBinarySensorSetup(unittest.IsolatedAsyncioTestCase):
    """Test async_setup_entry for the binary_sensor platform."""

    async def test_async_setup_entry_creates_all_entities(self):
        coordinator = MagicMock()
        coordinator.data = {
            DATA_ALERTS: [],
            DATA_POOLS: {"Volume1": {"name": "Volume1", "healthy": True}},
            DATA_SERVICES: {"smb": {"service": "smb", "state": "RUNNING"}},
            DATA_APPS: {"plex": {"name": "plex", "state": "RUNNING"}},
            DATA_VMS: {"ubuntu-server": {"name": "ubuntu-server", "status": {"state": "RUNNING"}}},
        }
        entry = MagicMock()
        entry.entry_id = "test_entry"
        entry.data = {"host": "192.168.1.100"}

        hass = MagicMock()
        hass.data = {DOMAIN: {entry.entry_id: {"coordinator": coordinator}}}

        added = []
        await async_setup_entry(hass, entry, added.extend)

        # 1 alerts + 1 pool + 1 service + 1 app + 1 vm = 5 entities
        self.assertEqual(len(added), 5)
        self.assertIsInstance(added[0], TrueNASSystemAlertsBinarySensor)
        self.assertTrue(any(isinstance(e, TrueNASPoolHealthyBinarySensor) for e in added))
        self.assertTrue(any(isinstance(e, TrueNASServiceBinarySensor) for e in added))
        self.assertTrue(any(isinstance(e, TrueNASAppBinarySensor) for e in added))
        self.assertTrue(any(isinstance(e, TrueNASVMBinarySensor) for e in added))

    async def test_async_setup_entry_with_no_optional_data(self):
        coordinator = MagicMock()
        coordinator.data = {DATA_ALERTS: []}
        entry = MagicMock()
        entry.entry_id = "test_entry"
        entry.data = {"host": "192.168.1.100"}

        hass = MagicMock()
        hass.data = {DOMAIN: {entry.entry_id: {"coordinator": coordinator}}}

        added = []
        await async_setup_entry(hass, entry, added.extend)

        # Only the always-present system alerts sensor.
        self.assertEqual(len(added), 1)
        self.assertIsInstance(added[0], TrueNASSystemAlertsBinarySensor)
