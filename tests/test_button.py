"""Tests for TrueNAS Scale button platform."""

import unittest
from unittest.mock import AsyncMock, MagicMock

from custom_components.truenas_scale.button import (
    TrueNASAppRestartButton,
    TrueNASServiceRestartButton,
    TrueNASVMRestartButton,
)
from custom_components.truenas_scale.const import DATA_APPS, DATA_SERVICES, DATA_VMS


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

    async def test_app_restart_button(self):
        button = TrueNASAppRestartButton(self.coordinator, self.entry, "plex")
        await button.async_press()
        self.coordinator.client.call.assert_called_with("app.redeploy", ["plex"])

    async def test_app_restart_button_fallback(self):
        button = TrueNASAppRestartButton(self.coordinator, self.entry, "plex")
        self.coordinator.client.call = AsyncMock(side_effect=[Exception("redeploy not supported"), None, None])
        await button.async_press()
        self.assertEqual(self.coordinator.client.call.call_count, 3)

    async def test_vm_restart_button(self):
        button = TrueNASVMRestartButton(self.coordinator, self.entry, "ubuntu-server", 1, "ubuntu-server")
        await button.async_press()
        self.coordinator.client.call.assert_called_with("vm.restart", [1])
