"""Tests for TrueNAS Scale button platform."""

import unittest
from unittest.mock import AsyncMock, MagicMock

from custom_components.truenas_scale.button import (
    TrueNASAppRestartButton,
    TrueNASServiceRestartButton,
    TrueNASVMRestartButton,
    async_setup_entry,
)
from custom_components.truenas_scale.const import (
    DATA_APPS,
    DATA_SERVICES,
    DATA_SYSTEM_INFO,
    DATA_VMS,
    DOMAIN,
)


class TestTrueNASButtons(unittest.IsolatedAsyncioTestCase):
    """Test Button Entities."""

    def setUp(self):
        self.coordinator = MagicMock()
        self.coordinator.client = MagicMock()
        self.coordinator.client.call = AsyncMock()
        self.coordinator.async_request_refresh = AsyncMock()
        self.coordinator.data = {
            DATA_SERVICES: {"smb": {"service": "smb", "state": "RUNNING"}},
            DATA_APPS: {"plex": {"name": "plex", "state": "RUNNING"}},
            DATA_VMS: {"ubuntu-server": {"id": 1, "name": "ubuntu-server", "status": {"state": "RUNNING"}}},
        }
        self.entry = MagicMock()
        self.entry.entry_id = "test_entry"
        self.entry.data = {"host": "192.168.1.100"}

    async def test_service_restart_button(self):
        button = TrueNASServiceRestartButton(self.coordinator, self.entry, "smb")
        self.assertEqual(button.icon, "mdi:restart")

        await button.async_press()
        self.coordinator.client.call.assert_called_with("service.control", ["smb", {"action": "RESTART"}])

    async def test_service_restart_button_exception(self):
        button = TrueNASServiceRestartButton(self.coordinator, self.entry, "smb")
        self.coordinator.client.call.side_effect = Exception("Restart failed")

        # Exception must be swallowed (logged) and the coordinator still refreshed.
        await button.async_press()
        self.assertTrue(self.coordinator.async_request_refresh.called)

    async def test_app_restart_button(self):
        button = TrueNASAppRestartButton(self.coordinator, self.entry, "plex")
        self.assertEqual(button.icon, "mdi:restart")
        await button.async_press()
        self.coordinator.client.call.assert_called_with("app.redeploy", ["plex"])

    async def test_app_restart_button_fallback(self):
        button = TrueNASAppRestartButton(self.coordinator, self.entry, "plex")
        self.coordinator.client.call = AsyncMock(side_effect=[Exception("redeploy not supported"), None, None])
        await button.async_press()
        self.assertEqual(self.coordinator.client.call.call_count, 3)

    async def test_app_restart_button_full_failure(self):
        # Both redeploy and the stop/start fallback fail: the exception must
        # still be swallowed (logged) and the coordinator refreshed.
        button = TrueNASAppRestartButton(self.coordinator, self.entry, "plex")
        self.coordinator.client.call = AsyncMock(side_effect=Exception("unreachable"))
        await button.async_press()
        self.assertTrue(self.coordinator.async_request_refresh.called)

    def test_app_restart_button_entity_picture(self):
        self.coordinator.data[DATA_APPS]["plex"]["icon_url"] = "https://plex.tv/logo.png"
        button = TrueNASAppRestartButton(self.coordinator, self.entry, "plex")
        self.assertEqual(button.entity_picture, "https://plex.tv/logo.png")

    def test_app_restart_button_entity_picture_metadata_fallback(self):
        self.coordinator.data[DATA_APPS]["plex"]["metadata"] = {
            "icon": "https://plex.tv/metadata-logo.png"
        }
        button = TrueNASAppRestartButton(self.coordinator, self.entry, "plex")
        self.assertEqual(button.entity_picture, "https://plex.tv/metadata-logo.png")

    def test_app_restart_button_entity_picture_none(self):
        button = TrueNASAppRestartButton(self.coordinator, self.entry, "plex")
        self.assertIsNone(button.entity_picture)

    async def test_vm_restart_button(self):
        button = TrueNASVMRestartButton(self.coordinator, self.entry, "ubuntu-server", 1, "ubuntu-server")
        self.assertEqual(button.icon, "mdi:restart")
        await button.async_press()
        self.coordinator.client.call.assert_called_with("vm.restart", [1])

    async def test_vm_restart_button_exception(self):
        button = TrueNASVMRestartButton(self.coordinator, self.entry, "ubuntu-server", 1, "ubuntu-server")
        self.coordinator.client.call.side_effect = Exception("VM restart failed")
        await button.async_press()
        self.assertTrue(self.coordinator.async_request_refresh.called)

    def test_device_info(self):
        self.coordinator.data[DATA_SYSTEM_INFO] = {
            "hostname": "truenas-scale",
            "model": "TRUENAS-CUSTOM",
            "version": "26.0.0",
        }
        button = TrueNASServiceRestartButton(self.coordinator, self.entry, "smb")
        info = button.device_info

        self.assertEqual(info["identifiers"], {(DOMAIN, self.entry.entry_id)})
        self.assertEqual(info["name"], "TrueNAS (truenas-scale)")
        self.assertEqual(info["manufacturer"], "iXsystems")
        self.assertEqual(info["model"], "TRUENAS-CUSTOM")
        self.assertEqual(info["sw_version"], "26.0.0")

    def test_device_info_fallback_to_entry_host(self):
        button = TrueNASServiceRestartButton(self.coordinator, self.entry, "smb")
        info = button.device_info

        self.assertEqual(info["name"], "TrueNAS (192.168.1.100)")
        self.assertEqual(info["model"], "TrueNAS Scale")
        self.assertEqual(info["sw_version"], "26.0")


class TestTrueNASButtonSetup(unittest.IsolatedAsyncioTestCase):
    """Test async_setup_entry for the button platform."""

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
        self.assertTrue(any(isinstance(e, TrueNASServiceRestartButton) for e in added))
        self.assertTrue(any(isinstance(e, TrueNASAppRestartButton) for e in added))
        self.assertTrue(any(isinstance(e, TrueNASVMRestartButton) for e in added))

    async def test_async_setup_entry_vm_id_falls_back_to_key(self):
        # A VM without an explicit "id" field should fall back to its dict key.
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
        vm_button = added[0]
        self.assertEqual(vm_button.vm_id, "vm-without-id")
        self.assertEqual(vm_button.vm_name, "vm-without-id")

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
