"""Tests for TrueNAS Scale API Client."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.truenas_scale.api import (
    TrueNASAPIError,
    TrueNASAuthError,
    TrueNASConnectionError,
    TrueNASScaleClient,
)


class TestTrueNASAPI(unittest.IsolatedAsyncioTestCase):
    """Test API client."""

    async def test_client_init(self):
        client = TrueNASScaleClient(
            host="192.168.1.100",
            api_key="test_api_key",
            username="root",
            port=443,
            use_ssl=True,
            verify_ssl=False,
        )
        self.assertEqual(client.host, "192.168.1.100")
        self.assertEqual(client.api_key, "test_api_key")
        self.assertEqual(client.port, 443)
        self.assertFalse(client.is_connected)

    async def test_client_connect_ssl_context(self):
        session = MagicMock()
        ws_mock = AsyncMock()
        session.ws_connect = AsyncMock(return_value=ws_mock)

        client = TrueNASScaleClient("192.168.1.100", "key", use_ssl=True, verify_ssl=False, session=session)

        # Mock authentication call
        with patch.object(client, "call", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = True
            await client.connect()
            self.assertTrue(client.is_connected)

    async def test_client_close(self):
        ws_mock = AsyncMock()
        ws_mock.closed = False
        client = TrueNASScaleClient("192.168.1.100", "key")
        client._ws = ws_mock
        client._connected = True

        await client.close()
        self.assertFalse(client.is_connected)
        self.assertIsNone(client._ws)

    async def test_client_handle_message_string_id(self):
        client = TrueNASScaleClient("192.168.1.100", "test_key")
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        client._pending_requests[1] = future

        # String ID "1" matching int 1
        data = {"jsonrpc": "2.0", "id": "1", "result": {"success": True}}
        client._handle_message(data)
        self.assertTrue(future.done())
        res = await future
        self.assertEqual(res, {"success": True})

    async def test_client_handle_message_error(self):
        client = TrueNASScaleClient("192.168.1.100", "test_key")
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        client._pending_requests[2] = future

        data = {"jsonrpc": "2.0", "id": 2, "error": {"code": -32601, "message": "Method not found"}}
        client._handle_message(data)
        self.assertTrue(future.done())
        with self.assertRaises(TrueNASAPIError):
            await future

    async def test_client_handle_realtime_event(self):
        client = TrueNASScaleClient("192.168.1.100", "test_key")
        callback = MagicMock()
        client.register_callback(callback)

        event_data = {
            "method": "reporting.realtime",
            "params": {
                "fields": {
                    "cpu": {"usage": 45.0, "temp": 50.0},
                }
            },
        }
        client._handle_message(event_data)
        realtime_cache = await client.async_get_realtime_cache()
        self.assertIn("cpu", realtime_cache)
        self.assertEqual(realtime_cache["cpu"]["usage"], 45.0)
        self.assertTrue(callback.called)

    async def test_client_api_methods(self):
        client = TrueNASScaleClient("192.168.1.100", "test_key")
        client.call = AsyncMock(return_value=[])

        await client.async_get_system_info()
        client.call.assert_called_with("system.info")

        await client.async_get_pools()
        client.call.assert_called_with("pool.query")

        await client.async_get_disks()
        client.call.assert_called_with("disk.query")

        await client.async_get_disk_temperatures()
        client.call.assert_called_with("disk.temperatures")

        await client.async_get_services()
        client.call.assert_called_with("service.query")

        await client.async_get_apps()
        client.call.assert_called_with("app.query")

        await client.async_get_alerts()
        client.call.assert_called_with("alert.list")

        await client.async_get_vms()
        client.call.assert_called_with("vm.query")
