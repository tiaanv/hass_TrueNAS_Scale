# TrueNAS SCALE Home Assistant Integration

En anpassad Home Assistant-integration (Custom Component) för **TrueNAS SCALE (v25.10+, v26.0+ & v27.0+)** som använder det moderna WebSocket-API:t baserat på **JSON-RPC 2.0**.

---

## 🚀 Funktioner

- **Modert WebSocket API:** Använder TrueNAS SCALE standardiserade JSON-RPC 2.0 protokoll med automatisk återanslutning.
- **Realtidsrapportering:** Live push-uppdateringar och telemetri (`reporting.realtime`) från TrueNAS.
- **Enkel konfiguration (UI):** Full GUI-konfiguration (Config Flow) med värdnamn/IP, port, användarnamn och API-nyckel.

---

## 📊 Mätvärden & Entiteter

### 🌡️ System & Prestanda (`sensor`)
- **CPU Usage:** Realtidsanvändning i `%` (aggregerat över alla CPU-kärnor).
- **CPU Temperature:** Processortemperatur i `°C` (medeltemperatur av alla aktiva CPU-kärnor).
- **CPU Load Average:** 1 min, 5 min och 15 min.
- **RAM-minne:** RAM Usage (`%`), Used RAM (`GB`), Available RAM (`GB`), Total RAM (`GB`).
- **ZFS ARC Cache:** Storlek på ZFS RAM-cache (`GB`).
- **Nätverkstrafik:** Download (Rx) och Upload (Tx) i `MB/s` per nätverkskort (`eno1`, `br0` osv.).
- **System Disk I/O:** Total läs/skriv-hastighet (`MB/s`) samt Read/Write IOPS (`ops/s`) för hela systemet.

### 🗄️ ZFS Pools & Lagring (`sensor`)
- **Usable Capacity:** Total användbar lagringskapacitet (stämmer exakt med TrueNAS Storage GUI).
- **Used Space:** Använt utrymme per ZFS-pool.
- **Free Space:** Ledigt utrymme per ZFS-pool (stöder automatisk enhetsomvandling till `TiB`/`GiB` utan avrundningsfel).
- **Pool Usage:** Användningsgrad i `%`.
- **Pool I/O:** Read Rate (`MB/s`), Write Rate (`MB/s`), Read IOPS och Write IOPS per enskild pool.
- **Datasets:** Använt utrymme per dataset.
- **Disk-temperaturer:** Temperatur i `°C` för varje enskild fysisk disk.

### 🚨 Status & Hälsa (`binary_sensor`)
- **System Alerts:** Indikerar om det finns aktiva systemlarm i TrueNAS.
- **Pool Health:** Indikerar om en ZFS-pool är `Healthy` eller `Degraded`.
- **Systemtjänster:** Status (`Running`/`Stopped`) för SMB, SSH, NFS, iSCSI, FTP m.fl.
- **Appar / Containrar:** Status för installerade TrueNAS-appar.
- **Virtuella Maskiner (VMs):** Status för virtuella maskiner.

### 🎛️ Kontroller (`switch`)
- **Start / Stopp för Tjänster:** Slå på eller av systemtjänster (SMB, SSH, NFS m.fl.).
- **Start / Stopp för Appar:** Starta och stoppa TrueNAS-appar och containers.
- **Start / Stopp för VMs:** Starta och stäng av virtuella maskiner.

### 🔄 Snabbåtgärder (`button`)
- **Starta om Appar:** Starta om/redeploya en app med ett tryck (`App <namn> Restart`).
- **Starta om Tjänster:** Starta om systemtjänster (`Service <namn> Restart`).
- **Starta om VMs:** Starta om virtuella maskiner (`VM <namn> Restart`).

### 📦 Uppdateringar (`update`)
- **App-uppdateringar:** Visar om det finns tillgängliga uppdateringar för TrueNAS-appar med appens logotyp och versioner.

---

## 🛠️ Installation i Home Assistant

### Metod 1: Installation via HACS (Rekommenderas)

1. Öppna **HACS** i din Home Assistant.
2. Klicka på de tre punkterna i övre högra hörnet och välj **Anpassade arkiv (Custom repositories)**.
3. Klistra in sökvägen/URL:en till detta repository (`https://github.com/hurricaneb/hass_TrueNAS_Scale`).
4. Välj **Integration** som kategori och klicka på **Lägg till**.
5. Sök efter **TrueNAS SCALE** i HACS och klicka på **Ladda ner**.
6. Starta om Home Assistant.
7. Gå till **Inställningar** -> **Enheter & Tjänster** -> **Lägg till integration**.
8. Sök efter **TrueNAS SCALE** och fyll i dina anslutningsuppgifter.

---

### Metod 2: Manuell installation

1. Kopiera mappen `custom_components/truenas_scale` till din Home Assistant-konfigurationsmapp:
   ```bash
   /config/custom_components/truenas_scale
   ```
2. Starta om Home Assistant.
3. Gå till **Inställningar** -> **Enheter & Tjänster** -> **Lägg till integration**.
4. Sök efter **TrueNAS SCALE**.
5. Fyll i din TrueNAS IP-adress, användarnamn (t.ex. `root`) och din API-nyckel.

---

## 🔑 Skapa API-nyckel i TrueNAS SCALE

1. Logga in i TrueNAS SCALE webbgränssnitt.
2. Klicka på användarikonen högst upp till höger -> **API Keys**.
3. Klicka på **Add** / **Generate API Key**.
4. Kopiera API-nyckeln och klistra in den i Home Assistant.

---

## 📂 Struktur för Custom Component

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

## 🧪 Automatiserade Tester

Kör testerna i Home Assistant utvecklingsmiljö via `pytest`:
```bash
pytest tests/
```

---

## 📄 Licens

Detta projekt är licensierat under **GNU General Public License v3.0 (GPL-3.0)**. Se filen [LICENSE](LICENSE) för mer information.
