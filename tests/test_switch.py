"""Tests for TrueNAS Scale switch platform."""

import unittest
from unittest.mock import AsyncMock, MagicMock

from custom_components.truenas_scale.const import DATA_APPS, DATA_SERVICES, DATA_VMS
from custom_components.truenas_scale.switch import (
    TrueNASAppSwitch,
    TrueNASServiceSwitch,
    TrueNASVMSwitch,
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
