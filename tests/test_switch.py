"""Tests for TrueNAS Scale switch platform."""

import unittest
from unittest.mock import AsyncMock, MagicMock

from custom_components.truenas_scale.const import (
    DATA_APPS,
    DATA_SERVICES,
    DATA_SYSTEM_INFO,
    DATA_VMS,
    DOMAIN,
)
from custom_components.truenas_scale.switch import (
    TrueNASAppSwitch,
    TrueNASServiceSwitch,
    TrueNASVMSwitch,
    async_setup_entry,
)


class TestTrueNASSwitches(unittest.IsolatedAsyncioTestCase):
    """Test Switch Entities."""

    def setUp(self):
        self.coordinator = MagicMock()
        self.coordinator.client = MagicMock()
        self.coordinator.client.call = AsyncMock()
        self.coordinator.async_request_refresh = AsyncMock()
        self.coordinator.data = {
            DATA_SERVICES: {
                "smb": {"service": "smb", "state": "RUNNING"},
                "ssh": {"service": "ssh", "state": "STOPPED"},
                "nfs": {"service": "nfs", "state": "RUNNING"},
                "ftp": {"service": "ftp", "state": "STOPPED"},
                "iscsi": {"service": "iscsitarget", "state": "RUNNING"},
            },
            DATA_APPS: {
                "plex": {
                    "name": "plex",
                    "state": "RUNNING",
                    "icon_url": "https://plex.tv/logo.png",
                }
            },
            DATA_VMS: {"ubuntu-server": {"id": 1, "name": "ubuntu-server", "status": {"state": "RUNNING"}}},
        }
        self.entry = MagicMock()
        self.entry.entry_id = "test_entry"
        self.entry.data = {"host": "192.168.1.100"}

    async def test_service_switch(self):
        switch = TrueNASServiceSwitch(self.coordinator, self.entry, "smb")
        self.assertTrue(switch.is_on)
        self.assertEqual(switch.icon, "mdi:folder-network")

        await switch.async_turn_off()
        self.coordinator.client.call.assert_called_with("service.control", ["smb", {"action": "STOP"}])

        await switch.async_turn_on()
        self.coordinator.client.call.assert_called_with("service.control", ["smb", {"action": "START"}])

    async def test_service_switch_exception(self):
        switch = TrueNASServiceSwitch(self.coordinator, self.entry, "smb")
        self.coordinator.client.call.side_effect = Exception("Service error")
        await switch.async_turn_on()
        # Should catch exception gracefully and refresh
        self.assertTrue(self.coordinator.async_request_refresh.called)

    async def test_service_switch_turn_off_exception(self):
        switch = TrueNASServiceSwitch(self.coordinator, self.entry, "smb")
        self.coordinator.client.call.side_effect = Exception("Service error")
        await switch.async_turn_off()
        self.assertTrue(self.coordinator.async_request_refresh.called)

    def test_service_switch_icons(self):
        ssh_s = TrueNASServiceSwitch(self.coordinator, self.entry, "ssh")
        nfs_s = TrueNASServiceSwitch(self.coordinator, self.entry, "nfs")
        ftp_s = TrueNASServiceSwitch(self.coordinator, self.entry, "ftp")
        iscsi_s = TrueNASServiceSwitch(self.coordinator, self.entry, "iscsi")
        other_s = TrueNASServiceSwitch(self.coordinator, self.entry, "other")

        self.assertEqual(ssh_s.icon, "mdi:console-network")
        self.assertEqual(nfs_s.icon, "mdi:share-network")
        self.assertEqual(ftp_s.icon, "mdi:file-transfer")
        self.assertEqual(iscsi_s.icon, "mdi:harddisk-network")
        self.assertEqual(other_s.icon, "mdi:cog-network")

    async def test_app_switch(self):
        switch = TrueNASAppSwitch(self.coordinator, self.entry, "plex")
        self.assertTrue(switch.is_on)
        self.assertEqual(switch.icon, "mdi:cube-outline")
        self.assertEqual(switch.entity_picture, "https://plex.tv/logo.png")

        await switch.async_turn_off()
        self.coordinator.client.call.assert_called_with("app.stop", ["plex"])

        await switch.async_turn_on()
        self.coordinator.client.call.assert_called_with("app.start", ["plex"])

    async def test_app_switch_exception(self):
        switch = TrueNASAppSwitch(self.coordinator, self.entry, "plex")
        self.coordinator.client.call.side_effect = Exception("App error")
        await switch.async_turn_on()
        self.assertTrue(self.coordinator.async_request_refresh.called)

    async def test_app_switch_turn_off_exception(self):
        switch = TrueNASAppSwitch(self.coordinator, self.entry, "plex")
        self.coordinator.client.call.side_effect = Exception("App error")
        await switch.async_turn_off()
        self.assertTrue(self.coordinator.async_request_refresh.called)

    def test_app_switch_entity_picture_metadata_fallback(self):
        self.coordinator.data[DATA_APPS]["plex"].pop("icon_url", None)
        self.coordinator.data[DATA_APPS]["plex"]["metadata"] = {
            "icon": "https://plex.tv/metadata-logo.png"
        }
        switch = TrueNASAppSwitch(self.coordinator, self.entry, "plex")
        self.assertEqual(switch.entity_picture, "https://plex.tv/metadata-logo.png")

    def test_app_switch_entity_picture_none(self):
        self.coordinator.data[DATA_APPS]["plex"].pop("icon_url", None)
        switch = TrueNASAppSwitch(self.coordinator, self.entry, "plex")
        self.assertIsNone(switch.entity_picture)

    async def test_vm_switch(self):
        switch = TrueNASVMSwitch(self.coordinator, self.entry, "ubuntu-server", 1, "ubuntu-server")
        self.assertTrue(switch.is_on)
        self.assertEqual(switch.icon, "mdi:server-network")

        await switch.async_turn_off()
        self.coordinator.client.call.assert_called_with("vm.stop", [1])

        await switch.async_turn_on()
        self.coordinator.client.call.assert_called_with("vm.start", [1])

    async def test_vm_switch_exception(self):
        switch = TrueNASVMSwitch(self.coordinator, self.entry, "ubuntu-server", 1, "ubuntu-server")
        self.coordinator.client.call.side_effect = Exception("VM error")
        await switch.async_turn_on()
        self.assertTrue(self.coordinator.async_request_refresh.called)

    async def test_vm_switch_turn_off_exception(self):
        switch = TrueNASVMSwitch(self.coordinator, self.entry, "ubuntu-server", 1, "ubuntu-server")
        self.coordinator.client.call.side_effect = Exception("VM error")
        await switch.async_turn_off()
        self.assertTrue(self.coordinator.async_request_refresh.called)

    def test_device_info(self):
        self.coordinator.data[DATA_SYSTEM_INFO] = {
            "hostname": "truenas-scale",
            "model": "TRUENAS-CUSTOM",
            "version": "26.0.0",
        }
        switch = TrueNASServiceSwitch(self.coordinator, self.entry, "smb")
        info = switch.device_info

        self.assertEqual(info["identifiers"], {(DOMAIN, self.entry.entry_id)})
        self.assertEqual(info["name"], "TrueNAS (truenas-scale)")
        self.assertEqual(info["manufacturer"], "iXsystems")
        self.assertEqual(info["model"], "TRUENAS-CUSTOM")
        self.assertEqual(info["sw_version"], "26.0.0")

    def test_device_info_fallback_to_entry_host(self):
        switch = TrueNASServiceSwitch(self.coordinator, self.entry, "smb")
        info = switch.device_info

        self.assertEqual(info["name"], "TrueNAS (192.168.1.100)")
        self.assertEqual(info["model"], "TrueNAS Scale")
        self.assertEqual(info["sw_version"], "26.0")


class TestTrueNASSwitchSetup(unittest.IsolatedAsyncioTestCase):
    """Test async_setup_entry for the switch platform."""

    async def test_async_setup_entry_creates_all_entities(self):
        coordinator = MagicMock()
        coordinator.data = {
            DATA_SERVICES: {"smb": {"service": "smb", "state": "RUNNING"}},
            DATA_APPS: {"plex": {"name": "plex", "state": "RUNNING"}},
            DATA_VMS: {"ubuntu-server": {"id": 1, "name": "ubuntu-server", "status": {"state": "RUNNING"}}},
        }
        entry = MagicMock()
        entry.entry_id = "test_entry"
        entry.data = {"host": "192.168.1.100"}

        hass = MagicMock()
        hass.data = {DOMAIN: {entry.entry_id: {"coordinator": coordinator}}}

        added = []
        await async_setup_entry(hass, entry, added.extend)

        # 1 service + 1 app + 1 vm = 3 entities
        self.assertEqual(len(added), 3)
        self.assertTrue(any(isinstance(e, TrueNASServiceSwitch) for e in added))
        self.assertTrue(any(isinstance(e, TrueNASAppSwitch) for e in added))
        self.assertTrue(any(isinstance(e, TrueNASVMSwitch) for e in added))

    async def test_async_setup_entry_vm_id_falls_back_to_key(self):
        coordinator = MagicMock()
        coordinator.data = {
            DATA_SERVICES: {},
            DATA_APPS: {},
            DATA_VMS: {"vm-without-id": {"status": {"state": "RUNNING"}}},
        }
        entry = MagicMock()
        entry.entry_id = "test_entry"
        entry.data = {"host": "192.168.1.100"}

        hass = MagicMock()
        hass.data = {DOMAIN: {entry.entry_id: {"coordinator": coordinator}}}

        added = []
        await async_setup_entry(hass, entry, added.extend)

        self.assertEqual(len(added), 1)
        vm_switch = added[0]
        self.assertEqual(vm_switch.vm_id, "vm-without-id")
        self.assertEqual(vm_switch.vm_name, "vm-without-id")

    async def test_async_setup_entry_with_no_data(self):
        coordinator = MagicMock()
        coordinator.data = {}
        entry = MagicMock()
        entry.entry_id = "test_entry"
        entry.data = {"host": "192.168.1.100"}

        hass = MagicMock()
        hass.data = {DOMAIN: {entry.entry_id: {"coordinator": coordinator}}}

        added = []
        await async_setup_entry(hass, entry, added.extend)

        self.assertEqual(added, [])
