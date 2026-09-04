# TrueNAS SCALE Home Assistant Integration

A custom Home Assistant integration for **TrueNAS SCALE (v25.10+, v26.0+ & v27.0+)** using the modern WebSocket API based on **JSON-RPC 2.0**.

---

## 🚀 Features

- **Modern WebSocket API:** Uses TrueNAS SCALE's standardized JSON-RPC 2.0 protocol with automatic reconnection.
- **Real-time reporting:** Live push updates and telemetry (`reporting.realtime`) from TrueNAS.
- **Easy configuration (UI):** Full GUI configuration (Config Flow) with hostname/IP, port, username and API key.

---

## 📊 Metrics & Entities

### 🌡️ System & Performance (`sensor`)
- **CPU Usage:** Real-time usage in `%` (aggregated across all CPU cores).
- **CPU Temperature:** Processor temperature in `°C` (average across all active CPU cores).
- **CPU Load Average:** 1 min, 5 min and 15 min.
- **Memory:** RAM Usage (`%`), Used RAM (`GB`), Available RAM (`GB`), Total RAM (`GB`).
- **ZFS ARC Cache:** Size of the ZFS RAM cache (`GB`).
- **Network Traffic:** Download (Rx) and Upload (Tx) in `MB/s` per network interface (`eno1`, `br0`, etc.).
- **System Disk I/O:** Total read/write speed (`MB/s`) and Read/Write IOPS (`ops/s`) for the whole system.

### 🗄️ ZFS Pools & Storage (`sensor`)
- **Usable Capacity:** Total usable storage capacity (matches the TrueNAS Storage GUI exactly).
- **Used Space:** Used space per ZFS pool.
- **Free Space:** Free space per ZFS pool (supports automatic unit conversion to `TiB`/`GiB` without rounding errors).
- **Pool Usage:** Usage percentage in `%`.
- **Pool I/O:** Read Rate (`MB/s`), Write Rate (`MB/s`), Read IOPS and Write IOPS per individual pool.
- **Datasets:** Used space per dataset.
- **Disk Temperatures:** Temperature in `°C` for each individual physical disk.

### 🚨 Status & Health (`binary_sensor`)
- **System Alerts:** Indicates whether there are active system alerts in TrueNAS.
- **Pool Health:** Indicates whether a ZFS pool is `Healthy` or `Degraded`.
- **System Services:** Status (`Running`/`Stopped`) for SMB, SSH, NFS, iSCSI, FTP and more.
- **Apps / Containers:** Status of installed TrueNAS apps.
- **Virtual Machines (VMs):** Status of virtual machines.

### 🎛️ Controls (`switch`)
- **Start / Stop Services:** Turn system services on or off (SMB, SSH, NFS, etc.).
- **Start / Stop Apps:** Start and stop TrueNAS apps and containers.
- **Start / Stop VMs:** Start and shut down virtual machines.

### 🔄 Quick Actions (`button`)
- **Restart Apps:** Restart/redeploy an app with one tap (`App <name> Restart`).
- **Restart Services:** Restart system services (`Service <name> Restart`).
- **Restart VMs:** Restart virtual machines (`VM <name> Restart`).

### 📦 Updates (`update`)
- **App Updates:** Shows whether updates are available for TrueNAS apps, with the app's logo and version numbers.

---

## 🛠️ Installation in Home Assistant

### Method 1: Install via HACS (Recommended)

1. Open **HACS** in your Home Assistant instance.
2. Click the three dots in the top-right corner and select **Custom repositories**.
3. Paste the URL of this repository (`https://github.com/hurricaneb/hass_TrueNAS_Scale`).
4. Select **Integration** as the category and click **Add**.
5. Search for **TrueNAS SCALE** in HACS and click **Download**.
6. Restart Home Assistant.
7. Go to **Settings** -> **Devices & Services** -> **Add Integration**.
8. Search for **TrueNAS SCALE** and enter your connection details.

---

### Method 2: Manual installation

1. Copy the `custom_components/truenas_scale` folder to your Home Assistant config directory:
   ```bash
   /config/custom_components/truenas_scale
   ```
2. Restart Home Assistant.
3. Go to **Settings** -> **Devices & Services** -> **Add Integration**.
4. Search for **TrueNAS SCALE**.
5. Enter your TrueNAS IP address, username (e.g. `root`) and your API key.

---

## 🔑 Creating an API key in TrueNAS SCALE

1. Log in to the TrueNAS SCALE web interface.
2. Click the user icon in the top-right corner -> **API Keys**.
3. Click **Add** / **Generate API Key**.
4. Copy the API key and paste it into Home Assistant.

---

## 📂 Custom Component Structure

```
truenas_scale/
├── custom_components/
│   └── truenas_scale/
│       ├── __init__.py
│       ├── api.py
│       ├── binary_sensor.py
│       ├── button.py
│       ├── config_flow.py
│       ├── const.py
│       ├── manifest.json
│       ├── sensor.py
│       ├── strings.json
│       ├── switch.py
│       ├── icon.png
│       ├── logo.png
│       ├── brand/
│       │   ├── icon.png
│       │   ├── icon@2x.png
│       │   ├── logo.png
│       │   └── logo@2x.png
│       └── translations/
│           ├── en.json
│           └── sv.json
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_binary_sensor.py
│   ├── test_button.py
│   ├── test_init.py
│   ├── test_sensor.py
│   ├── test_switch.py
│   └── test_update.py
├── .gitignore
├── hacs.json
├── LICENSE
└── README.md
```

---

## 🧪 Automated Tests

Run the tests in a Home Assistant development environment via `pytest`:
```bash
pytest tests/
```

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**. See the [LICENSE](LICENSE) file for more information.
