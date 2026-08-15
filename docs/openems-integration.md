# OpenEMS-Integration

VoltSurfer koppelt sich an [OpenEMS Edge](https://github.com/OpenEMS/openems)
(EPL-2.0) — lokal im **Simulator-Modus** als virtuelle Hardware, später mit
denselben Aufrufen an echte Wechselrichter über die OpenEMS-Gerätetreiber.

```
┌──────────────┐   Preise/Prognosen    ┌─────────────────┐
│ energy-charts │ ───────────────────▶ │   VoltSurfer     │
└──────────────┘                       │  (Planer + App)  │
                                       └────────┬────────┘
                                REST :8084      │  GET  /rest/channel/ess0/Soc
                                (Basic x:admin) │  POST /rest/channel/ess0/SetActivePowerEquals
                                       ┌────────▼────────┐
                                       │  OpenEMS Edge    │  Felix-Console :8080
                                       │  (OSGi, Java 21) │  (admin/admin)
                                       └────────┬────────┘
                              heute: Simulator  │  später: echte Treiber
                        ess0 (20 kWh) · meter0  │  (SMA, Fronius, Deye, …)
```

## Setup (einmalig)

1. **JDK 21** (Temurin): `winget install EclipseAdoptium.Temurin.21.JDK`
2. **Klonen:** `git clone --depth 1 https://github.com/OpenEMS/openems.git external/openems`
3. **Bauen:** `cd external/openems && .\gradlew buildEdge --no-daemon -x test`

## Starten (jedes Mal)

```powershell
powershell scripts/run_openems.ps1                      # 1. Edge starten
.venv\Scripts\python.exe scripts\openems_bootstrap.py   # 2. nur beim ersten Mal nötig
.venv\Scripts\python.exe -m streamlit run app/main.py   # 3. VoltSurfer
```

Dann in der App: Seite **Hardware (OpenEMS)** → „Kopplung aktiv" →
„VoltSurfer steuert OpenEMS".

## Was der Bootstrap anlegt

| Komponente | Factory-PID | Zweck |
|---|---|---|
| `datasource0` | `Simulator.Datasource.CSV.Predefined` | H0-Haushaltslastprofil |
| `meter0` | `Simulator.GridMeter.Acting` | Netzzähler aus dem Profil |
| `ess0` | `Simulator.EssSymmetric.Reacting` | Speicher 20 kWh / 10 kW, SoC 50 % |
| `ctrlDebugLog0` | `Controller.Debug.Log` | Zustands-Log je Cycle |
| `ctrlApiRest0` | `Controller.Api.Rest.ReadWrite` | REST-API auf Port 8084 |
| `scheduler0` | `Scheduler.AllAlphabetically` | Controller-Ausführung |

## Steuerpfad

- VoltSurfer berechnet den Fahrplan (LP/Top-N/Manuell/KI, `voltsurfer/live/strategies.py`)
- `voltsurfer/openems/client.py` sendet den aktuellen 15-min-Sollwert:
  `POST /rest/channel/ess0/SetActivePowerEquals {"value": <Watt>}`
- **Vorzeichen (OpenEMS-Konvention): negativ = laden, positiv = entladen**
- Der Sollwert verfällt nach `apiTimeout` (60 s) — deshalb pusht die
  Hardware-Seite alle 30 s neu (`st.fragment(run_every="30s")`)

## Troubleshooting

| Symptom | Ursache/Lösung |
|---|---|
| Hardware-Seite „offline" | Edge läuft nicht → `scripts/run_openems.ps1`; oder Bootstrap fehlt |
| Bootstrap: „Felix-Console nicht erreichbar" | Edge braucht ~20 s zum Start; Port 8080 belegt? |
| 401 bei REST | Passwort in Einstellungen ≠ Edge-Passwort (Default admin) |
| Sollwert wirkt nicht | `scheduler0` fehlt (Controller laufen nicht) → Bootstrap erneut |
| Firewall-Dialog beim ersten Start | Zulassen — nur lokale Ports 8080/8084/8085 |
| Konfiguration weg nach Neustart | Edge immer aus `data_cache/openems` starten (macht das Skript) |

## Pfad zu echter Hardware (Phase 4)

Gleicher Client, gleiche Kanäle — statt der Simulator-Komponenten werden im
Edge die echten Treiber konfiguriert (z. B. `Battery-Inverter`-, `ESS`- und
`Meter`-Implementierungen für SMA/Fronius/Deye/…). Zusätzlich: OpenEMS Backend
als VPP-Zentrale für viele Haushalte (siehe docs/vpp-konzept.md, Phase 2/3).
