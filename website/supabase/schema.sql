-- =====================================================================
-- VoltSurfer — Datenbank-Schema für das Kontaktformular
--
-- SO WIRD ES EINGERICHTET:
--   1. Auf supabase.com mit dem VoltSurfer-Account anmelden
--   2. Neues Projekt anlegen (Region: eu-central-1 / Frankfurt wegen DSGVO)
--   3. Links im Menü "SQL Editor" öffnen
--   4. Diesen kompletten Text einfügen und "Run" klicken
--   5. Unter "Project Settings > API" die beiden Werte kopieren und in
--      website/.env.local eintragen (siehe .env.example)
--
-- Die Anfragen siehst du danach unter "Table Editor > voltsurfer_leads".
-- =====================================================================

create table if not exists public.voltsurfer_leads (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),

  -- Kontaktdaten
  name text not null check (char_length(name) between 2 and 100),
  email text not null check (
    char_length(email) between 5 and 150
    and email ~* '^[^[:space:]@]+@[^[:space:]@]+\.[a-z]{2,}$'
  ),
  telefon text check (telefon is null or char_length(telefon) <= 40),
  plz text check (plz is null or plz ~ '^[0-9]{5}$'),

  -- Eckdaten für die Vor-Ort-Beratung
  jahresverbrauch_kwh integer check (
    jahresverbrauch_kwh is null or jahresverbrauch_kwh between 500 and 50000
  ),
  waermepumpe boolean,
  eauto boolean,
  pv_vorhanden boolean,
  interesse text check (
    interesse is null or interesse in ('voltsurfer_20', 'voltsurfer_30', 'unklar')
  ),

  nachricht text check (nachricht is null or char_length(nachricht) <= 5000),
  -- Optional: Ergebnis aus dem Kunden-Check, falls ausgefüllt
  rechner_daten jsonb check (
    rechner_daten is null or char_length(rechner_daten::text) <= 20000
  ),

  -- DSGVO: ohne Einwilligung entsteht kein Datensatz
  einwilligung boolean not null default false check (einwilligung = true),

  -- Bearbeitungsstand (nur für dich im Dashboard)
  bearbeitet boolean not null default false,
  notiz text check (notiz is null or char_length(notiz) <= 5000)
);

comment on table public.voltsurfer_leads is
  'Anfragen von der VoltSurfer-Website. Schreiben ist oeffentlich (Formular), Lesen ausschliesslich ueber Dashboard bzw. service_role-Schluessel.';

create index if not exists voltsurfer_leads_created_at_idx
  on public.voltsurfer_leads (created_at desc);
create index if not exists voltsurfer_leads_offen_idx
  on public.voltsurfer_leads (bearbeitet, created_at desc);

-- Zeilenschutz: Besucher dürfen ausschließlich einfügen, nichts lesen.
alter table public.voltsurfer_leads enable row level security;

drop policy if exists "formular darf anfragen anlegen" on public.voltsurfer_leads;
create policy "formular darf anfragen anlegen"
  on public.voltsurfer_leads
  for insert
  to anon, authenticated
  with check (einwilligung = true);
