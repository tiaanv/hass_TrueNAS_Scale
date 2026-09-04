"""Tests for TrueNAS Scale config flow."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import data_entry_flow

from custom_components.truenas_scale.config_flow import TrueNASScaleConfigFlow
from custom_components.truenas_scale.const import DOMAIN


class TestTrueNASConfigFlow(unittest.IsolatedAsyncioTestCase):
    """Test Config Flow."""

    def setUp(self):
        self.clientsession_patcher = patch(
            "custom_components.truenas_scale.config_flow.async_get_clientsession",
            return_value=MagicMock(),
        )
        self.clientsession_patcher.start()
        self.addCleanup(self.clientsession_patcher.stop)

    def _make_flow(self):
        flow = TrueNASScaleConfigFlow()
        flow.hass = MagicMock()
        flow.hass.config_entries.async_entry_for_domain_unique_id = MagicMock(return_value=None)
        flow.context = {}
        flow._async_current_entries = MagicMock(return_value=[])
        return flow

    async def test_form_user_success(self):
        flow = self._make_flow()

        with patch(
            "custom_components.truenas_scale.config_flow.TrueNASScaleClient.connect",
            new_callable=AsyncMock,
        ) as mock_connect, patch(
            "custom_components.truenas_scale.config_flow.TrueNASScaleClient.async_get_system_info",
            new_callable=AsyncMock,
        ) as mock_system_info, patch(
            "custom_components.truenas_scale.config_flow.TrueNASScaleClient.close",
            new_callable=AsyncMock,
        ):
            mock_connect.return_value = True
            mock_system_info.return_value = {}
            result = await flow.async_step_user(
                {
                    "host": "192.168.1.100",
                    "api_key": "valid_key",
                    "username": "root",
                    "port": 443,
                    "ssl": True,
                    "verify_ssl": False,
                }
            )

            self.assertEqual(result["type"], data_entry_flow.FlowResultType.CREATE_ENTRY)
            self.assertEqual(result["title"], "TrueNAS SCALE (192.168.1.100)")
            self.assertEqual(result["data"]["host"], "192.168.1.100")

    async def test_form_user_invalid_auth(self):
        flow = self._make_flow()

        from custom_components.truenas_scale.api import TrueNASAuthError

        with patch(
            "custom_components.truenas_scale.config_flow.TrueNASScaleClient.connect",
            side_effect=TrueNASAuthError("Invalid API key"),
        ), patch(
            "custom_components.truenas_scale.config_flow.TrueNASScaleClient.close",
            new_callable=AsyncMock,
        ):
            result = await flow.async_step_user(
                {
                    "host": "192.168.1.100",
                    "api_key": "invalid_key",
                    "username": "root",
                    "port": 443,
                    "ssl": True,
                    "verify_ssl": False,
                }
            )

            self.assertEqual(result["type"], data_entry_flow.FlowResultType.FORM)
            self.assertEqual(result["errors"]["base"], "invalid_auth")

    async def test_form_user_unknown_error(self):
        flow = self._make_flow()

        with patch(
            "custom_components.truenas_scale.config_flow.TrueNASScaleClient.connect",
            new_callable=AsyncMock,
        ), patch(
            "custom_components.truenas_scale.config_flow.TrueNASScaleClient.async_get_system_info",
            side_effect=ValueError("Unexpected response shape"),
        ), patch(
            "custom_components.truenas_scale.config_flow.TrueNASScaleClient.close",
            new_callable=AsyncMock,
        ):
            result = await flow.async_step_user(
                {
                    "host": "192.168.1.100",
                    "api_key": "key",
                    "username": "root",
                    "port": 443,
                    "ssl": True,
                    "verify_ssl": False,
                }
            )

            self.assertEqual(result["type"], data_entry_flow.FlowResultType.FORM)
            self.assertEqual(result["errors"]["base"], "unknown")

    async def test_form_user_cannot_connect(self):
        flow = self._make_flow()

        from custom_components.truenas_scale.api import TrueNASConnectionError

        with patch(
            "custom_components.truenas_scale.config_flow.TrueNASScaleClient.connect",
            side_effect=TrueNASConnectionError("Could not connect"),
        ), patch(
            "custom_components.truenas_scale.config_flow.TrueNASScaleClient.close",
            new_callable=AsyncMock,
        ):
            result = await flow.async_step_user(
                {
                    "host": "192.168.1.100",
                    "api_key": "key",
                    "username": "root",
                    "port": 443,
                    "ssl": True,
                    "verify_ssl": False,
                }
            )

            self.assertEqual(result["type"], data_entry_flow.FlowResultType.FORM)
            self.assertEqual(result["errors"]["base"], "cannot_connect")
