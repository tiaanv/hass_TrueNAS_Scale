"""Tests for TrueNAS Scale integration setup and coordinator."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.truenas_scale import (
    TrueNASCoordinator,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.truenas_scale.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    DATA_APPS,
    DATA_POOLS,
    DATA_SERVICES,
    DATA_SYSTEM_INFO,
    DATA_VMS,
    DOMAIN,
)


class TestTrueNASInit(unittest.IsolatedAsyncioTestCase):
    """Test coordinator and init handlers."""

    async def test_coordinator_update_data(self):
        hass = MagicMock()
        client = MagicMock()
        client.async_get_system_info = AsyncMock(return_value={"hostname": "truenas-scale"})
        client.async_get_pools = AsyncMock(return_value=[{"name": "Volume1"}])
        client.async_get_datasets = AsyncMock(return_value=[])
        client.async_get_disks = AsyncMock(return_value=[])
        client.async_get_disk_temperatures = AsyncMock(return_value={})
        client.async_get_services = AsyncMock(return_value=[{"service": "smb", "state": "RUNNING"}])
        client.async_get_apps = AsyncMock(return_value=[{"name": "plex", "state": "RUNNING"}])
        client.async_get_alerts = AsyncMock(return_value=[])
        client.async_get_realtime_cache = AsyncMock(return_value={})
        client.async_get_interfaces = AsyncMock(return_value=[])
        client.async_get_vms = AsyncMock(return_value=[{"id": 1, "name": "ubuntu-server"}])

        coordinator = TrueNASCoordinator(hass, client)
        data = await coordinator._async_update_data()

        self.assertIn(DATA_SYSTEM_INFO, data)
        self.assertEqual(data[DATA_SYSTEM_INFO]["hostname"], "truenas-scale")
        self.assertIn("Volume1", data[DATA_POOLS])
        self.assertIn("smb", data[DATA_SERVICES])
        self.assertIn("plex", data[DATA_APPS])
        self.assertIn("ubuntu-server", data[DATA_VMS])

    async def test_coordinator_update_data_warnings(self):
        hass = MagicMock()
        client = MagicMock()
        client.async_get_system_info = AsyncMock(return_value={"hostname": "truenas-scale"})
        client.async_get_pools = AsyncMock(return_value=[{"name": "Volume1"}])
        client.async_get_datasets = AsyncMock(return_value=[])
        client.async_get_disks = AsyncMock(return_value=[])
        client.async_get_disk_temperatures = AsyncMock(return_value={})
        client.async_get_services = AsyncMock(side_effect=Exception("Services unavailable"))
        client.async_get_apps = AsyncMock(side_effect=Exception("Apps unavailable"))
        client.async_get_alerts = AsyncMock(side_effect=Exception("Alerts unavailable"))
        client.async_get_realtime_cache = AsyncMock(return_value={})
        client.async_get_interfaces = AsyncMock(return_value=[])
        client.async_get_vms = AsyncMock(side_effect=Exception("VMs unavailable"))

        coordinator = TrueNASCoordinator(hass, client)
        data = await coordinator._async_update_data()
        self.assertIn(DATA_SYSTEM_INFO, data)

    async def test_coordinator_update_data_failure(self):
        hass = MagicMock()
        client = MagicMock()
        client.async_get_system_info = AsyncMock(side_effect=Exception("Connection reset"))
        client.async_get_pools = AsyncMock(side_effect=Exception("Connection reset"))
        client.async_get_datasets = AsyncMock(return_value=[])
        client.async_get_disks = AsyncMock(return_value=[])
        client.async_get_disk_temperatures = AsyncMock(return_value={})
        client.async_get_services = AsyncMock(return_value=[])
        client.async_get_apps = AsyncMock(return_value=[])
        client.async_get_alerts = AsyncMock(return_value=[])
        client.async_get_realtime_cache = AsyncMock(return_value={})
        client.async_get_interfaces = AsyncMock(return_value=[])
        client.async_get_vms = AsyncMock(return_value=[])

        coordinator = TrueNASCoordinator(hass, client)
        with self.assertRaises(UpdateFailed):
            await coordinator._async_update_data()

    async def test_async_setup_and_unload_entry(self):
        hass = MagicMock()
        hass.data = {}
        hass.config_entries = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        entry = MagicMock()
        entry.entry_id = "test_entry_id"
        entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_API_KEY: "key",
            CONF_USERNAME: "root",
            CONF_PORT: 443,
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
        }

        with patch("custom_components.truenas_scale.TrueNASScaleClient") as mock_client_cls:
            client_mock = AsyncMock()
            mock_client_cls.return_value = client_mock

            setup_ok = await async_setup_entry(hass, entry)
            self.assertTrue(setup_ok)
            self.assertIn(DOMAIN, hass.data)

            unload_ok = await async_unload_entry(hass, entry)
            self.assertTrue(unload_ok)

    async def test_async_setup_entry_not_ready(self):
        hass = MagicMock()
        hass.data = {}
        entry = MagicMock()
        entry.entry_id = "test_entry_id"
        entry.data = {
            CONF_HOST: "192.168.1.100",
            CONF_API_KEY: "key",
            CONF_USERNAME: "root",
            CONF_PORT: 443,
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
        }

        with patch("custom_components.truenas_scale.TrueNASScaleClient") as mock_client_cls:
            client_mock = AsyncMock()
            client_mock.connect.side_effect = Exception("Unreachable")
            mock_client_cls.return_value = client_mock

            with self.assertRaises(ConfigEntryNotReady):
                await async_setup_entry(hass, entry)
