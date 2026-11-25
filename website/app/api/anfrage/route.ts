import { NextResponse } from "next/server";

/**
 * Nimmt Kontaktanfragen entgegen und legt sie in Supabase ab.
 * Läuft serverseitig, damit Validierung nicht umgangen werden kann.
 */

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_PUBLISHABLE_KEY;
const TABELLE = "voltsurfer_leads";

function alsBool(v: unknown): boolean {
  return v === "true" || v === true || v === "on";
}

function text(v: unknown, max: number): string | null {
  if (typeof v !== "string") return null;
  const s = v.trim();
  return s.length === 0 || s.length > max ? null : s;
}

export async function POST(request: Request) {
  if (!SUPABASE_URL || !SUPABASE_KEY) {
    console.error("Supabase-Zugangsdaten fehlen (.env.local prüfen).");
    return NextResponse.json(
      { fehler: "Das Formular ist gerade nicht erreichbar. Bitte versuch es später noch einmal." },
      { status: 503 },
    );
  }

  // Die Seite schickt FormData (system.js des Taste-Baukastens), ältere Clients JSON.
  let body: Record<string, unknown>;
  try {
    const typ = request.headers.get("content-type") ?? "";
    body = typ.includes("application/json")
      ? await request.json()
      : Object.fromEntries((await request.formData()).entries());
  } catch {
    return NextResponse.json({ fehler: "Ungültige Anfrage." }, { status: 400 });
  }

  const name = text(body.name, 100);
  const email = text(body.email, 150);

  if (!name || name.length < 2) {
    return NextResponse.json({ fehler: "Bitte gib deinen Namen an." }, { status: 400 });
  }
  if (!email || !/^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/.test(email)) {
    return NextResponse.json({ fehler: "Bitte gib eine gültige E-Mail-Adresse an." }, { status: 400 });
  }
  if (!alsBool(body.einwilligung)) {
    return NextResponse.json(
      { fehler: "Ohne deine Einwilligung dürfen wir die Anfrage nicht speichern." },
      { status: 400 },
    );
  }

  const plz = text(body.plz, 5);
  const verbrauch = Number(body.jahresverbrauch_kwh);
  const interesse = text(body.interesse, 20);

  const datensatz = {
    name,
    email,
    telefon: text(body.telefon, 40),
    plz: plz && /^\d{5}$/.test(plz) ? plz : null,
    jahresverbrauch_kwh:
      Number.isFinite(verbrauch) && verbrauch >= 500 && verbrauch <= 50000 ? Math.round(verbrauch) : null,
    waermepumpe: alsBool(body.waermepumpe),
    eauto: alsBool(body.eauto),
    pv_vorhanden: alsBool(body.pv_vorhanden),
    interesse:
      interesse && ["voltsurfer_20", "voltsurfer_30", "unklar"].includes(interesse) ? interesse : "unklar",
    nachricht: text(body.nachricht, 5000),
    einwilligung: true,
  };

  try {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/${TABELLE}`, {
      method: "POST",
      headers: {
        apikey: SUPABASE_KEY,
        Authorization: `Bearer ${SUPABASE_KEY}`,
        "Content-Type": "application/json",
        Prefer: "return=minimal",
      },
      body: JSON.stringify(datensatz),
    });

    if (!res.ok) {
      console.error("Supabase-Fehler:", res.status, await res.text());
      return NextResponse.json(
        { fehler: "Speichern hat nicht geklappt. Bitte versuch es später noch einmal." },
        { status: 502 },
      );
    }
  } catch (err) {
    console.error("Netzwerkfehler zu Supabase:", err);
    return NextResponse.json(
      { fehler: "Keine Verbindung zum Server. Bitte versuch es später noch einmal." },
      { status: 502 },
    );
  }

  return NextResponse.json({ ok: true }, { status: 201 });
}
