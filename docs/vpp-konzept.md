# VoltSurfer — VPP-Konzept: Regulatorik, Markt und Roadmap

Stand: Juli 2026. Arbeitsdokument für die Produktentwicklung — keine Rechtsberatung;
vor Markteintritt anwaltlich und mit BNetzA-Festlegungen abgleichen.

## 1. Produktidee in einem Satz

VoltSurfer verkauft Privathaushalten Batteriespeicher (20/30 kWh) mit eigenem EMS,
das den Speicher am dynamischen Tarif optimiert — und bündelt alle Speicher zu einem
virtuellen Kraftwerk (VPP), das Flexibilität am Strommarkt vermarktet und die Erlöse
mit den Kunden teilt.

## 2. Die vier Erlöshebel (Wertschöpfungs-Stack)

| # | Hebel | Mechanik | Größenordnung* |
|---|-------|----------|----------------|
| 1 | **Arbitrage am dynamischen Tarif** | Laden in Billig-Viertelstunden, Haushalt versorgen in Teuerstunden | siehe Simulation (Dashboard) |
| 2 | **PV-Eigenverbrauchsoptimierung** | Überschuss speichern statt für ~7,9 ct einspeisen, abends statt für ~35 ct beziehen | klassischer Speichernutzen |
| 3 | **§ 14a EnWG Netzentgelt-Reduktion** | Modul 1: pauschal ~110–190 €/a; Modul 3: zeitvariable Netzentgelte (Spread ~Faktor 3) — das EMS legt Ladefenster in Niedertarifzeiten | 100–300 €/a |
| 4 | **VPP-Erlöse** | Direktvermarktung der Rückspeisung zu Spotpreisen, perspektivisch Regelleistung (FCR/aFRR) über Pooling | Zusatzerlös, siehe VPP-Modus der Simulation |

*Hebel 1+2 quantifiziert unsere Simulation mit echten Day-Ahead-Preisen; Hebel 3
lässt sich als nächstes Feature einbauen (zeitvariable Netzentgelte als Preiskomponente).

## 3. Regulatorischer Rahmen (Stand Juli 2026)

### 3.1 Solarspitzengesetz / § 19 EEG — der Game-Changer für Speicher

Seit 25.02.2025 dürfen Batteriespeicher **flexibel** betrieben werden: Netzstrom
einspeichern und später rückspeisen ist grundsätzlich erlaubt, ohne die EEG-Förderung
der PV-Anlage zu verlieren (vorher: Ausschließlichkeitsprinzip).

- **Pauschaloption für Heimspeicher (bis 30 kWp):** kein aufwendiges Messkonzept
  nötig; die geförderte Strommenge wird pauschal mit **500 kWh je kWp PV** angesetzt.
  Rückspeisung darüber hinaus gilt als Graustrom (Vergütung über Direktvermarktung,
  nicht EEG).
- **Offen:** die genaue Abgrenzungs-Festlegung der BNetzA (angekündigt bis Juni 2026)
  — muss vor Produktlaunch geprüft werden.
- Konsequenz für VoltSurfer: unser „VPP-Modus" (Rückspeisung zum Spotpreis) ist seit
  2025 **rechtlich möglich**; praktisch braucht es iMSys, Direktvermarktungszugang
  und saubere Abgrenzung. Genau diese Lücke füllt unser Produkt.

Quellen: [BSW-FAQ Solarspitzengesetz](https://www.solarwirtschaft.de/unsere-themen/photovoltaik/standpunkte/faq-solarspitzengesetz/),
[Interconnector-Überblick](https://www.interconnector.de/energieblog/direktvermarktung/solarspitzengesetz-2025-was-sich-jetzt-fuer-pv-und-speicher-aendert/),
[SMA-Zusammenfassung](https://www.sma.de/solarspitzengesetz2025)

### 3.2 § 14a EnWG — Netzdienlichkeit & reduzierte Netzentgelte

Speicher > 4,2 kW Anschlussleistung sind steuerbare Verbrauchseinrichtungen (SteuVE):
Pflicht zur netzorientierten Steuerung (Dimmen auf 4,2 kW Bezug im Engpassfall),
im Gegenzug reduzierte Netzentgelte in drei Modulen:

- **Modul 1:** pauschale Reduktion (~110–190 €/a je nach Netzgebiet)
- **Modul 2:** prozentuale Arbeitspreis-Reduktion (~60 %) auf separat gemessene SteuVE
- **Modul 3:** **zeitvariable Netzentgelte** (HT/ST/NT, seit 04/2025 wählbar, ab 2026
  flächendeckend) — für ein preisgesteuertes EMS der spannendste Hebel, da sich
  Ladefenster gezielt in NT-Zeiten legen lassen

VoltSurfer-EMS muss die Steuerbarkeit (Steuerbox/EEBUS) technisch umsetzen — das ist
zugleich die Eintrittskarte für die volle Einspeiseleistung nach § 9 EEG.

Quellen: [BNetzA § 14a](https://www.bundesnetzagentur.de/enwg14a),
[Modul-Vergleich 2026](https://elektronik-zeit.de/14a-enwg/berater/),
[Stromfee-Leitfaden](https://www.stromfee.me/post/14a-enwg-2026-wie-steuerbare-verbraucher-reduziertes-netzentgelt-nutzen)

### 3.3 Abgaben auf Rückspeisung (EnFG, Stromsteuer)

- **§ 21 EnFG:** Befreiung von Umlagen für Strom, der zur Zwischenspeicherung
  entnommen und wieder eingespeist wird (kein doppeltes Zahlen von Umlagen).
- **Stromsteuer:** Speicher können als „Teil des Versorgungsnetzes" behandelt werden;
  für eingespeicherten und rückgespeisten Strom fällt im Ergebnis keine doppelte
  Stromsteuer an. Details (Erlaubnisschein, Anmeldung Hauptzollamt) klären.
- **Netzentgelte auf den Ladestrom** bleiben der größte Kostenblock der Arbitrage —
  § 118 Abs. 6 EnWG (Befreiung) gilt klassisch für reine Netzspeicher; für
  Multi-Use-Heimspeicher ist die anteilige Behandlung Gegenstand laufender
  BNetzA-Festlegungen. Konservativ kalkulieren wir volle Netzentgelte (so auch
  in der Simulation).

### 3.4 Messwesen — iMSys, Steuerbox, 15-min-Bilanzierung

- **iMSys-Pflicht** seit 2025 u. a. bei Jahresverbrauch > 6.000 kWh, PV ≥ 7 kWp und
  SteuVE nach § 14a — unsere Zielkunden haben also ohnehin Anspruch/Pflicht.
  Kosten gedeckelt (~25–50 €/a, MsbG-Novelle 02/2025).
- **Dynamische Tarife** setzen iMSys voraus (15-min-Bilanzierung); alle Lieferanten
  müssen seit 2025 dynamische Tarife anbieten.
- **Steuerbox + EEBUS** verbinden Netzbetreiber und Anlage (Dimmen nach § 14a,
  Steuerung nach § 9 EEG). Das VoltSurfer-Gateway sollte EEBUS nativ sprechen.

Quellen: [sonnen Smart-Meter-Pflicht](https://www.sonnen.de/blog/smart-meter-pflicht),
[EMA § 9 EEG / Steuerbox](https://ema-energiewelt.de/wissen/pv-anlage-steuerbarkeit-paragraph-9-eeg-2026)

### 3.5 Direktvermarktung & Marktrollen

Für den Verkauf von Speicherstrom an der Börse braucht es die Kette:
**Bilanzkreisverantwortlicher (BKV) → Direktvermarkter/Aggregator → Händler an
EPEX Spot**.

**Gewählter Weg (Stand Juli 2026): White-Label-Direktvermarktung über EnBW.**
EnBW übernimmt Bilanzkreis, Börsenzugang und Abwicklung; VoltSurfer liefert
Steuerung + Fahrpläne über die eigene EMS-Cloud. **Startschwelle: ab ~100 kWh
Handelsvolumen pro Tag, also ~20–30 Kunden** (je Kunde ~4–6 kWh Verkauf/Tag laut
Simulation) — ab da ist das VPP operativ real, nicht nur konzeptionell.
Die Tagesabrechnung in der App kennzeichnet entsprechend: ✅ heute
(Eigenverbrauch + § 14a) vs. 🔓 Vermarktung (Verkaufserlöse, ab Startschwelle).

Späterer Ausbau: eigener Bilanzkreis und Marktteilnehmer-Zulassung — hohe
Fixkosten, erst ab einigen tausend Speichern sinnvoll.

Aggregator-Modelle für Anlagen ab ~7 kWp werden durch den iMSys-Rollout praktikabel;
ab 06/2026 kommt **Energy Sharing** als zusätzlicher Vermarktungsweg hinzu.

### 3.6 Regelleistung (FCR/aFRR)

- Präqualifikation beim ÜNB, Mindestgebot 1 MW → nur als **Pool** erreichbar
  (bei 20/30-kWh-Systemen mit 10/15 kW: ~70–100 Speicher je MW).
- Machbarkeit ist bewiesen: TransnetBW hat sonnens Heimspeicher-VPP für
  **Primärregelleistung (FCR)** präqualifiziert (12/2024); sonnen erbringt FCR aus
  Heimspeichern produktiv. 1Komma5° steuert inzwischen ~1 GW Flexibilität.
- Für die Roadmap: Phase 3 — erst dynamischer Tarif (Phase 1), dann
  Direktvermarktung (Phase 2), dann Regelleistung (höchste Anforderungen an
  Verfügbarkeit, Messung, IT-Sicherheit/ISMS, BSI-Zertifizierung des Gateways).

Quellen: [pv magazine: TransnetBW/sonnen](https://www.pv-magazine.de/2024/12/12/transnet-bw-praequalifiziert-virtuelles-kraftwerk-aus-heimspeicher-von-sonnen-fuer-primarregelleistung/),
[pv magazine: 1Komma5° 1 GW](https://www.pv-magazine.de/2026/05/20/1komma5-steuert-ein-gigawatt-flexibilitaet-aus-privaten-photovoltaik-speicheranlagen/),
[heise: VPP bei Tibber & sonnen](https://www.heise.de/hintergrund/Virtuelle-Kraftwerke-Wie-sie-bei-Tibber-und-Sonnen-funktionieren-10242041.html)

## 4. Wettbewerb — und die Lücke für VoltSurfer

| Anbieter | Modell | Schwäche aus Kundensicht |
|----------|--------|--------------------------|
| sonnen | Speicher + sonnenVPP (FCR), eigener Tarif | geschlossenes Ökosystem, Speicher-Premium-Preis |
| 1Komma5° | Heartbeat-EMS, dyn. Tarif, 1 GW VPP | nur im Komplettpaket (PV+WP+Speicher) attraktiv |
| Tibber | dynamischer Tarif + Steuerung von Fremdgeräten | kein eigener Speicher, Steuerungstiefe begrenzt |
| Viessmann/Kiwigrid | Flexvermarktung für WP + Speicher (seit 07/2026) | an Viessmann-Hardware gebunden |

**Lücke:** ein hardware-offenes, transparentes Speicher+EMS-Angebot mit klarer
Erlösbeteiligung („dein Speicher verdient mit") und nachvollziehbarer Simulation
VOR dem Kauf — genau das zeigt unser Dashboard dem Kunden.

## 5. Technische Roadmap

**Phase 1 (dieses Repo):** Simulation + Dashboard als Vertriebs- und
Auslegungswerkzeug. LP-Optimierung (PuLP/HiGHS, EMHASS-Formulierung) gegen echte
Day-Ahead-Preise; Szenarien A–D; 20/30-kWh-Presets.

**Phase 2 (Pilot, 10–50 Haushalte):**
- Gateway im Haus auf **OpenEMS-Edge**-Basis (EPL-2.0, produktiv bei FENECON):
  fertige Treiber für gängige Hybrid-Wechselrichter (SMA, Fronius, Deye, Sungrow, …),
  Zähler, EEBUS/§ 14a.
- **OpenEMS-Backend** als VoltSurfer-Cloud: Monitoring, Fahrplan-Verteilung; unsere
  Phase-1-Strategie wird zum Fahrplan-Service (täglich nach Day-Ahead-Auktion um
  ~13 Uhr Fahrpläne je Haushalt rechnen — exakt der Simulations-Code).
- Dynamischer Tarif über Partner-Lieferanten, Rückspeisung über
  Partner-Direktvermarkter (Pauschalabgrenzung 500 kWh/kWp).
- Alternativ-Referenz für schlanke MQTT-Ansteuerung: batcontrol (Fronius/Tibber).

**Phase 3 (Skalierung):** eigener Bilanzkreis oder Tiefen-Integration beim
Aggregator, aFRR/FCR-Präqualifikation des Pools, Energy-Sharing-Produkte,
§ 14a Modul 3-Optimierung im EMS.

## 6. Risiken & offene Punkte

1. **BNetzA-Festlegung zur Speicher-Abgrenzung** (fällig ~06/2026): Pauschalwerte
   könnten sich ändern → Business Case VPP-Modus neu rechnen.
2. **Netzentgelt-Reform** (AgNes/Betreibermodelle in Diskussion): Arbitrage-Marge
   hängt an der Behandlung des Ladestroms.
3. **Spread-Kompression:** je mehr Großspeicher zubauen, desto kleiner die
   Day-Ahead-Spreads — Sensitivität im Dashboard prüfen (Verschleißkosten-Regler).
4. **iMSys-Rollout-Tempo** beim Messstellenbetreiber des Kunden (BNetzA führt
   bereits Aufsichtsverfahren gegen säumige MSB).
5. **Haftung/Gewährleistung** bei Fremd-Wechselrichtern (Garantiebedingungen
   einzelner Hersteller bei Netzladung prüfen).
