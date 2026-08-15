# VoltSurfer-Website

Verkaufs-Landingpage mit eingebettetem Ersparnis-Rechner.
Next.js (App Router) + Tailwind, fertig für Vercel.

## Lokal starten

```bash
cd website
npm install
cp .env.example .env.local   # PowerShell: Copy-Item .env.example .env.local
npm run dev
```

Läuft dann auf http://localhost:3000. Ohne ausgefüllte `.env.local` funktioniert
alles außer Kontaktformular und Live-Demo — an deren Stelle erscheinen Hinweise.

---

## Einrichtung mit eigenen Accounts

Du brauchst drei kostenlose Konten. **Wichtig:** Du kannst überall einen eigenen,
von deinen anderen Projekten getrennten Account verwenden — nichts davon hängt an
bestehenden Zugängen.

### 1. Supabase — Speicher für Kontaktanfragen

1. Auf [supabase.com](https://supabase.com) mit dem **VoltSurfer-Account** anmelden
   (eigene E-Mail-Adresse verwenden, wenn die Projekte getrennt bleiben sollen)
2. **New Project** → Name `voltsurfer`, Region **Frankfurt (eu-central-1)** wählen
   (Server in der EU, DSGVO-freundlich)
3. Links **SQL Editor** öffnen, den Inhalt von [`supabase/schema.sql`](supabase/schema.sql)
   einfügen und **Run** klicken → legt die Tabelle `voltsurfer_leads` an
4. Unter **Project Settings → API** zwei Werte kopieren:
   - *Project URL* → `NEXT_PUBLIC_SUPABASE_URL`
   - *publishable key* (beginnt mit `sb_publishable_`) → `SUPABASE_PUBLISHABLE_KEY`
5. Beide in `.env.local` eintragen

**Anfragen ansehen:** Supabase → **Table Editor** → `voltsurfer_leads`.
Die Spalten `bearbeitet` und `notiz` sind für deine eigene Nachverfolgung gedacht.

> Sicherheit: Besucher dürfen ausschließlich *einfügen*, nicht lesen. Selbst wenn
> jemand den öffentlichen Schlüssel aus dem Seitenquelltext ausliest, kommt er nicht
> an die Anfragen anderer. Das erzwingt die Row-Level-Security-Regel im Schema.

### 2. GitHub — Code-Ablage (nötig für die Demo)

Das Projekt ist bisher nur lokal. Für die Live-Demo brauchst du ein Repository:

```bash
cd C:\Users\Stani911\Desktop\VoltSurfer
git init
git add .
git commit -m "VoltSurfer: EMS, Simulation und Website"
```

Dann auf [github.com](https://github.com) mit dem **gewünschten Account** ein neues,
**privates** Repository anlegen (z. B. `voltsurfer`) und verbinden:

```bash
git remote add origin https://github.com/DEIN-ACCOUNT/voltsurfer.git
git branch -M main
git push -u origin main
```

Beim ersten Push fragt Git nach Zugangsdaten — melde dich mit dem Account an, dem
das Repository gehören soll. Falls Windows noch Zugangsdaten eines anderen Accounts
gespeichert hat: *Systemsteuerung → Anmeldeinformationsverwaltung → Windows-Anmelde-
informationen* → Eintrag `git:https://github.com` entfernen, dann erneut pushen.

> `.gitignore` schließt bereits aus: `data_cache/` (Zustandsdaten), `.venv/`,
> `external/` (OpenEMS-Klon) und `.streamlit/secrets.toml`. Prüfe vor dem ersten
> Push mit `git status`, dass nichts Vertrauliches dabei ist.

### 3. Streamlit Community Cloud — der Ersparnis-Rechner

1. Auf [share.streamlit.io](https://share.streamlit.io) mit **demselben GitHub-Account**
   anmelden
2. **New app** → das Repository wählen
3. Einstellungen:
   - **Main file path:** `app/demo.py`
   - **Advanced settings → Secrets:** leer lassen
   - **Advanced settings → Python version:** 3.11 oder neuer
4. Damit nur die schlanken Abhängigkeiten installiert werden, im Repo-Stammverzeichnis
   `requirements-demo.txt` nach `requirements.txt` kopieren **oder** in den App-
   Einstellungen den Pfad auf `requirements-demo.txt` setzen
5. Deployen. Die entstehende Adresse (z. B. `https://voltsurfer.streamlit.app`)
   als `NEXT_PUBLIC_DEMO_URL` in `.env.local` bzw. bei Vercel eintragen

Die Umgebungsvariable `VOLTSURFER_DEMO` setzt `app/demo.py` selbst — jeder Besucher
bekommt eine eigene, nicht gespeicherte Anlage.

> Erster Aufruf dauert etwas: Die App lädt Börsenpreise und Wetterdaten und rechnet
> den Backtest. Danach greift der Cache.

### 4. Vercel — die Website

1. Auf [vercel.com](https://vercel.com) mit dem GitHub-Account anmelden
2. **Add New → Project** → Repository auswählen
3. **Root Directory** auf `website` setzen (wichtig — das Repo enthält auch die Python-App)
4. Unter **Environment Variables** dieselben drei Werte wie in `.env.local` eintragen
5. **Deploy**

Eigene Domain: Vercel → Projekt → **Settings → Domains** → Domain eintragen und die
angezeigten DNS-Einträge bei deinem Domain-Anbieter setzen.

---

## Vor dem Livegang erledigen

- [ ] `app/impressum/page.tsx` — alle `[Platzhalter]` durch echte Firmendaten ersetzen
      (Pflicht nach § 5 DDG, fehlerhafte Angaben sind abmahnfähig)
- [ ] `app/datenschutz/page.tsx` — Firmendaten ergänzen und Text juristisch prüfen lassen
- [ ] Auftragsverarbeitungsverträge mit Supabase und Vercel abschließen (in den
      jeweiligen Dashboards verfügbar)
- [ ] Preise und Ersparnis-Angaben gegenprüfen — sie sind Richtwerte

## Aufbau

| Pfad | Inhalt |
|---|---|
| `app/page.tsx` | Landingpage (Hero, Funktionsweise, Demo, Produkte, Kontakt) |
| `app/api/anfrage/route.ts` | Nimmt das Formular entgegen, validiert, schreibt nach Supabase |
| `components/ContactForm.tsx` | Kontaktformular |
| `components/PriceWave.tsx` | Animierte Preiskurve im Hero |
| `components/Logo.tsx` | Wortmarke |
| `supabase/schema.sql` | Datenbank-Schema zum Einspielen |
| `app/globals.css` | Farbwelt (identisch zur Streamlit-App) |
