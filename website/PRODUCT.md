# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Eigenheimbesitzer in ganz Deutschland, mit oder ohne Photovoltaik. Typischer Anlass: hohe Stromrechnung, Wärmepumpe oder E-Auto in Planung oder schon da, Interesse an dynamischen Stromtarifen. Sie wollen verstehen, ob sich ein Heimspeicher für sie rechnet, und dann ein Beratungsgespräch anfragen. Kein Fachpublikum: Börsenpreise, Netzentgelte und § 14a müssen ohne Vorwissen verständlich sein.

## Product Purpose

VoltSurfer verkauft einen Batteriespeicher (20 oder 30 kWh, 11 kW) mit eigener Steuerung. Der Speicher lädt in den günstigsten Viertelstunden des Tages zu Börsenpreisen und versorgt Haus, Wärmepumpe und E-Auto, wenn der Strom teuer ist. Später schalten sich die Speicher zu einem Verbund (virtuelles Kraftwerk) zusammen und verkaufen zusätzlich Strom an der Börse. Erfolg der Website: qualifizierte Beratungsanfragen über das Kontaktformular.

## Positioning

Die Steuerung entscheidet nicht nach Uhrzeit, sondern jeden Tag neu nach den Day-Ahead-Börsenpreisen für morgen und der Wettervorhersage. Die günstigste Stunde wandert (Sommer: mittags, Winter: nachts), nur der Abend ist ganzjährig teuer: "Die Delle wandert. Der Abendberg bleibt." Funktioniert ohne PV, weil der Speicher vom Preisunterschied zwischen den Stunden lebt. Offene OpenEMS-Software, kein Abo, keine Herstellerbindung.

## Operating Context

Besucher kommen auf die Seite, lesen die Preisgeschichte, schauen sich die zwei Produktgrößen an und fragen eine kostenlose Beratung vor Ort an (Zählerschrank-Check, echte Verbrauchswerte). Ein dynamischer Stromtarif und ein Smart Meter sind Voraussetzung; VoltSurfer übernimmt Tarifwechsel, Smart-Meter-Antrag und Netzbetreiber-Anmeldung. Optional: eingebetteter Ersparnisrechner (Streamlit-Demo über `NEXT_PUBLIC_DEMO_URL`).

## Capabilities and Constraints

- Next.js 16, Deploy auf Vercel, Root Directory `website`. Die Startseite, Impressum und Datenschutz sind statische HTML-Seiten in `public/` (Rewrites in `next.config.ts`); Next.js stellt nur die Anfrage-API. Schriften liegen selbst gehostet in `public/fonts`.
- Kontaktformular → `POST /api/anfrage` → Supabase-Tabelle `voltsurfer_leads` (RLS insert-only, Schema in `supabase/schema.sql`). ENV: `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`.
- Produkte: VoltSurfer 20 (20 kWh, 8.000 €) und VoltSurfer 30 (30 kWh, 11.000 €), je 11 kW laden/entladen, LFP-Zellen mit 6.000 Zyklen, § 14a-fähig. Preise sind Richtwerte inkl. Standardinstallation; Zählerschrank-Erneuerung kommt ggf. hinzu; verbindliches Angebot vor Bestellung.
- Der Verbund existiert noch nicht. Er braucht rund 20–30 Haushalte. Kein Startdatum versprechen.
- Regulatorisch offen: Abgrenzungsfestlegung der BNetzA zum Speicherprivileg (§ 21 EnFG, § 118 EnWG). Muss im Kleingedruckten stehen.
- Impressum und Datenschutz sind noch Platzhalter und müssen vom Betreiber gefüllt werden.

## Brand Commitments

- Name: VoltSurfer. Absender ist eine Firma ("wir"), Ansprache "du".
- Ehrlichkeitsregel: Was heute ab Installation real ist, wird klar getrennt von dem, was erst mit dem Verbund kommt. Beide Rechnungen werden immer getrennt gezeigt.
- Die große Zahl ("bis zu 1.348 € im Jahr") darf bleiben, aber nur zusammen mit dem Hinweis, dass rund 820 € davon ab Tag eins entstehen und der Rest aus der Vermarktung über den Verbund kommt.
- Deutsche Anführungszeichen in TSX als `&bdquo;`/`&ldquo;` setzen, nicht als Zeichen im String.
- Gestaltung (Stand 25.11.2026): Der helle Branchenstandard wurde verworfen. Verbindlich ist das Vorbild des Kunden: fast schwarzer Grund mit Grünstich (#0c0e0a), Limette als einziger Akzent (#c6ef62), eine kursive Serifenzeile (Instrument Serif) in der Überschrift, rechts im ersten Bildschirm ein Knoten mit Leitungen und laufenden Lichtpunkten, Lichtstrahlen mit Staub als Effekt. Gebaut mit dem Taste-Skill (design-taste-frontend) als statische Seite `public/index.html`, Baukasten in `public/assets`. Das 3D-Rendering der Anlage wird nicht verwendet.

## Evidence on Hand

- Echte Day-Ahead-Börsenpreise DE-LU (energy-charts.info / SMARD), Auswertung 15.08.2025–15.08.2026: Tiefstpreis an 64 % der Tage mittags (Sommerhalbjahr 98 %), Ø Mittag 5,5 ct / Nacht 9,4 ct / Abend 14,1 ct, Ø Tagesspanne 15,6 ct, 6,0 % negative Viertelstunden an 27 % der Tage, Trend 3,4 % (2023) → 7,3 % (2026). Stundenprofile Sommer/Winter/Jahr liegen vor (früher `lib/preise.ts`).
- Simulation (12 Monate, VoltSurfer 30, 3 Personen, Wärmepumpe, § 14a Modul 1, gegen 35 ct Festpreis): 820 €/Jahr ohne Verkauf, 1.348 € mit Verbund; Amortisation 13 bzw. 8 Jahre.
- Eigenes 3D-Rendering der Anlage (aufgeschnittenes Haus, Speicher, Wärmepumpe, Wallbox, Carport mit E-Auto, Netzanschluss) als `public/anlage/haus.png` plus Leitungsmaske `public/anlage/leitungen.png`. Rechte beim Betreiber. Nachtszene in Blautönen.
- Keine Kundenstimmen, keine Referenzanlagen, keine Fotos von echten Installationen, keine Presse. Nichts davon erfinden.

## Product Principles

1. Rechnen statt versprechen: Jede Zahl stammt aus echten Börsendaten oder der Simulation und nennt ihre Quelle.
2. Heute und Verbund immer getrennt zeigen.
3. Verständlich ohne Vorwissen: erst das Phänomen (Preise schwanken), dann die Maschine, dann das Angebot.
4. Kein Abo, keine Bindung: der Speicher gehört dem Kunden.

## Accessibility & Inclusion

Zielgruppe schließt ältere Hausbesitzer ein: gut lesbare Textgrößen, ausreichender Kontrast, Bewegung respektiert `prefers-reduced-motion`, Formular vollständig per Tastatur bedienbar.
