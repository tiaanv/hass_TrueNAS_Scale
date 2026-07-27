"""Fixtures for TrueNAS Scale integration tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.truenas_scale.const import DOMAIN


@pytest.fixture
def mock_system_info():
    return {
        "hostname": "truenas-scale",
        "model": "TRUENAS-CUSTOM",
        "version": "26.0.0",
        "cores": 8,
        "physmem": 68719476736,
        "loadavg": [0.45, 0.32, 0.28],
    }


@pytest.fixture
def mock_pools():
    return [
        {
            "name": "Volume1",
            "status": "ONLINE",
            "healthy": True,
            "size": 109951162777600,
            "allocated": 94250000000000,
            "free": 15701162777600,
        }
    ]


@pytest.fixture
def mock_datasets():
    return [
        {
            "id": "Volume1",
            "name": "Volume1",
            "used": {"parsed": 75594115000000},
            "available": {"parsed": 13281900000000},
        },
        {
            "id": "Volume1/data",
            "name": "Volume1/data",
            "used": {"parsed": 5000000000000},
            "available": {"parsed": 13281900000000},
        },
    ]


@pytest.fixture
def mock_disks():
    return [
        {"name": "sda", "size": 10002048860160, "temp": 35},
        {"name": "sdb", "size": 10002048860160, "temp": 36},
    ]


@pytest.fixture
def mock_services():
    return [
        {"service": "smb", "state": "RUNNING", "enable": True},
        {"service": "ssh", "state": "STOPPED", "enable": False},
    ]


@pytest.fixture
def mock_apps():
    return [
        {
            "name": "plex",
            "state": "RUNNING",
            "version": "1.32.0",
            "human_version": "1.32.0",
            "upgrade_available": True,
            "available_version": "1.33.0",
            "icon_url": "https://plex.tv/logo.png",
        }
    ]


@pytest.fixture
def mock_vms():
    return [
        {
            "id": 1,
            "name": "ubuntu-server",
            "status": {"state": "RUNNING"},
            "vcpus": 4,
            "memory": 8192,
        }
    ]


@pytest.fixture
def mock_realtime():
    return {
        "cpu": {
            "cpu0": {"usage": 15.0, "temp": 42.0},
            "cpu1": {"usage": 25.0, "temp": 44.0},
        },
        "memory": {
            "physical_memory_total": 68719476736,
            "physical_memory_available": 34359738368,
            "arc_size": 17179869184,
        },
        "disks": {
            "sda": {"read_bytes": 1048576, "write_bytes": 2097152, "read_ops": 10.0, "write_ops": 20.0},
        },
        "interfaces": {
            "eno1": {"received_bytes_rate": 5242880, "sent_bytes_rate": 10485760},
        },
    }
