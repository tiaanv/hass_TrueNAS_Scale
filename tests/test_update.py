"""Tests for TrueNAS Scale update platform."""

import unittest
from unittest.mock import AsyncMock, MagicMock

from custom_components.truenas_scale.const import DATA_APPS
from custom_components.truenas_scale.update import TrueNASAppUpdateEntity


class TestTrueNASUpdateEntities(unittest.IsolatedAsyncioTestCase):
    """Test Update Entities."""

    def setUp(self):
        self.coordinator = MagicMock()
        self.coordinator.client = MagicMock()
        self.coordinator.client.async_upgrade_app = AsyncMock()
        self.coordinator.async_request_refresh = AsyncMock()
        self.coordinator.data = {
            DATA_APPS: {
                "plex": {
                    "name": "plex",
                    "version": "1.32.0",
                    "human_version": "1.32.0",
                    "upgrade_available": True,
                    "available_version": "1.33.0",
                    "icon_url": "https://plex.tv/logo.png",
                }
            }
        }
        self.entry = MagicMock()
        self.entry.entry_id = "test_entry"
        self.entry.data = {"host": "192.168.1.100"}

    def test_app_update_entity(self):
        update_entity = TrueNASAppUpdateEntity(self.coordinator, self.entry, "plex")

        self.assertEqual(update_entity.installed_version, "1.32.0")
        self.assertEqual(update_entity.latest_version, "1.33.0")
        self.assertEqual(update_entity.entity_picture, "https://plex.tv/logo.png")

    async def test_app_update_install(self):
        update_entity = TrueNASAppUpdateEntity(self.coordinator, self.entry, "plex")
        await update_entity.async_install(version="1.33.0", backup=False)

        self.coordinator.client.async_upgrade_app.assert_called_with("plex")
        self.assertTrue(self.coordinator.async_request_refresh.called)
