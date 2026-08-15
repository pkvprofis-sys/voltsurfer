# ⚡ VoltSurfer

**Graustrom-Arbitrage-EMS für Privathaushalte.** Der Speicher (20/30 kWh, 11 kW)
lädt in den günstigsten Börsen-Viertelstunden — bei Negativpreisen gibt es Geld
fürs Laden —, versorgt Haushalt + Wärmepumpe und verkauft den Rest zu
Spitzenpreisen (Speicherprivileg: Rückspeisung ohne Doppel-Abgaben). Der
**Playground** rechnet mit echten Day-Ahead-Preisen seit 2023 und echtem Wetter
vor, was die Anlage verdient hätte — dieselbe Engine steuert den Live-Betrieb
und (via OpenEMS) später die echte Hardware.

## Schnellstart

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install highspy   # optional, schneller LP-Solver
.\.venv\Scripts\python.exe -m streamlit run app/main.py
```

## Die App (6 Screens)

| Screen | Inhalt |
|--------|--------|
| **Kunden-Check** (Start) | Fragebogen (Personen, PV, Wärmepumpe, E-Auto mit km+Akku, smarte Geräte) → Tagesbedarf + Speicher-Empfehlung → **12-Monats-Rückblick als Zeitraffer** (x5–x50) mit Endergebnis-Karte inkl. E-Auto-KI-Ladebonus |
| **Playground (Experten)** | 3 Eingaben → „Dein Ertrag: X €/Jahr" mit Zerlegung (Handel/Verbrauch/PV/§ 14a), Jahresvergleich 2023–2026, Tages-Replay mit echten Preisen, Speicherprivileg-Vergleichsschalter |
| **Live-Betrieb** | Live-Spotpreis, animierter Energiefluss (Netz/Speicher/Haus/Geräte), Preisphasen-Chart heute+morgen, Smart-Device-Kacheln, Lastvorschau inkl. Wärmepumpe |
| **Zeitplan & Strategie** | 4 Strategien: **Auto** (LP-Optimierung), **Top-N** (günstigste Stunden laden), **Manuell** (tägliche Fenster), **KI-Adaptiv** (lernt den Verbrauch, reserviert Tagesbedarf, verkauft den Rest — Puffer bleibt immer) |
| **Batterie** | SoC/SoH-Gauges, Zyklenzähler vs. 6.000 (LFP), Zellspannungs-Spreizung, Balancing, Historie |
| **Hardware (OpenEMS)** | Live-Kopplung an OpenEMS Edge: Ist-Werte lesen, Fahrplan-Sollwerte senden |
| **Einstellungen** | Haushalt (Personen/WP/Standort), Speicher, § 14a-Modul, Speicherprivileg, Tarif-Experten, Geräte, Reset |

**Erlösmodell (Speicherprivileg, § 21 EnFG/§ 118 EnWG):** Ladestrom kostet nur
Spot+Aufschlag; Abgaben fallen erst bei Letztverbrauch an; Verkauf erlöst den
Spotpreis. Der konservative Vergleich (volle Abgaben) ist zuschaltbar, solange
die BNetzA-Abgrenzungsfestlegung aussteht. § 14a: Modul 1 (Pauschale), Modul 2
(−60 % NE auf Speicherstrom) oder Modul 3 (zeitvariable Netzentgelte, das EMS
lädt automatisch in NT-Fenstern).

Ohne echte Hardware werden Speicherzustand und Geräte simuliert
(`data_cache/plant_state.json`); Preise und Solarprognose sind echt. Die
Planer-Logik ist identisch mit dem späteren Gateway-EMS.

## OpenEMS-Kopplung (Screen „Hardware")

VoltSurfer steuert ein lokales [OpenEMS Edge](https://github.com/OpenEMS/openems)
im Simulator-Modus über dessen REST-API — derselbe Steuerpfad wie später bei
echten Wechselrichtern:

```powershell
# einmalig: JDK 21 + Clone + Build
winget install EclipseAdoptium.Temurin.21.JDK
git clone --depth 1 https://github.com/OpenEMS/openems.git external/openems
cd external/openems; .\gradlew buildEdge --no-daemon -x test; cd ../..

# starten
powershell scripts/run_openems.ps1                      # Edge (Java) im Hintergrund
.venv\Scripts\python.exe scripts\openems_bootstrap.py   # einmalig: Simulator-Anlage anlegen
```

Danach in der App: **Hardware (OpenEMS)** → Kopplung aktivieren → „VoltSurfer
steuert OpenEMS". Details: [docs/openems-integration.md](docs/openems-integration.md).

Beim ersten Start werden ~24 Monate Preis- und Solardaten von der
[Energy-Charts-API](https://api.energy-charts.info) geladen (Fraunhofer ISE,
Daten SMARD/Bundesnetzagentur, CC BY 4.0) und lokal in `data_cache/` abgelegt.
Die erste Simulation je Konfiguration dauert ~30–60 s, danach kommt alles aus dem Cache.
`scripts/precompute.py` rechnet die Standardkonfigurationen vor.

## Was die Simulation macht

- **Daten:** Day-Ahead DE-LU auf 15-min-Raster (stündlich bis 09/2025, danach
  15-min-MTU), nationale PV-Erzeugung als wetterechtes PV-Profil, synthetisches
  H0-artiges Haushaltslastprofil.
- **Optimierung:** tagesweise lineare Programmierung (PuLP/HiGHS, Formulierung
  nach [EMHASS](https://github.com/davidusb-geek/emhass)-Vorbild) mit 48-h-Fenster;
  Preisvoraussicht entspricht der Realität (Day-Ahead steht am Vortag fest).
- **Szenarien:** A statischer Tarif ohne Speicher · B statisch + Speicher
  (klassisch) · C dynamisch ohne Speicher · D dynamisch + VoltSurfer-EMS —
  wahlweise nur Eigenverbrauch oder VPP-Modus mit Rückspeisung (Direktvermarktung).
- **KPIs:** Ersparnis €/Jahr, Amortisation, Vollzyklen, Negativpreis-Laden,
  Ø Lade-/Entladepreis, Monatskosten.

## Projektstruktur

| Pfad | Inhalt |
|------|--------|
| `voltsurfer/config.py` | Batterie-/Tarif-/Simulationsparameter (Presets 20/30 kWh) |
| `voltsurfer/data/prices.py` | Energy-Charts-Client (Historik) mit Parquet-Cache und Rate-Limit-Backoff |
| `voltsurfer/live/` | Live-Preise & Solarprognose, 4 Betriebsstrategien, simulierte Anlage, Geräteplanung |
| `voltsurfer/profiles/` | Haushaltslast- und PV-Profil |
| `voltsurfer/sim/` | LP-Optimierer (PuLP/HiGHS), Engine, Greedy-Vergleich, KPI-Auswertung |
| `app/main.py` + `app/pages/` | Multi-Page-Streamlit-App (`app/theme.py`: Branding, `app/flow.py`: Energiefluss) |
| `docs/vpp-konzept.md` | Regulatorik & Roadmap: Direktvermarktung, § 14a EnWG, Regelleistung, OpenEMS-Pfad |
| `voltsurfer/tests/` | pytest: Physik-Invarianten, Arbitrage, DST-Tage, Strategien, Geräte, Anlagenzustand |

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest voltsurfer/tests -q
```
