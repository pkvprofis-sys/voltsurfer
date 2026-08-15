"use client";

import { useRef, useState } from "react";

type Status = "idle" | "sending" | "ok" | "error";

export function ContactForm() {
  const [status, setStatus] = useState<Status>("idle");
  const [fehler, setFehler] = useState<string | null>(null);
  const formRef = useRef<HTMLFormElement>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("sending");
    setFehler(null);

    const daten = Object.fromEntries(new FormData(e.currentTarget).entries());
    try {
      const res = await fetch("/api/anfrage", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(daten),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.fehler ?? "Anfrage konnte nicht gesendet werden.");
      }
      setStatus("ok");
      formRef.current?.reset();
    } catch (err) {
      setStatus("error");
      setFehler(err instanceof Error ? err.message : "Unbekannter Fehler.");
    }
  }

  if (status === "ok") {
    return (
      <div
        className="rounded-3xl border-2 border-volt bg-volt-wash p-8 text-center"
        role="status"
        aria-live="polite"
      >
        <p className="text-2xl font-extrabold text-ink">Danke — wir melden uns!</p>
        <p className="mt-2 text-ink-soft">
          Wir schauen uns deine Angaben an und melden uns für einen Beratungstermin bei dir.
        </p>
        <button
          type="button"
          onClick={() => setStatus("idle")}
          className="mt-6 rounded-full border border-line bg-paper px-5 py-2.5 text-sm font-semibold text-ink-soft transition-colors hover:text-ink"
        >
          Weitere Anfrage senden
        </button>
      </div>
    );
  }

  const feld =
    "w-full rounded-xl border border-line bg-paper px-4 py-3 text-ink placeholder:text-ink-soft/50 transition-colors focus:border-volt";
  const label = "mb-1.5 block text-sm font-semibold text-ink";

  return (
    <form
      ref={formRef}
      onSubmit={onSubmit}
      className="rounded-3xl border border-line bg-mist p-6 sm:p-8"
      noValidate={false}
    >
      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <label className={label} htmlFor="name">
            Name <span className="text-volt">*</span>
          </label>
          <input
            id="name"
            name="name"
            required
            minLength={2}
            maxLength={100}
            autoComplete="name"
            className={feld}
            placeholder="Max Mustermann"
          />
        </div>

        <div>
          <label className={label} htmlFor="email">
            E-Mail <span className="text-volt">*</span>
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            autoComplete="email"
            spellCheck={false}
            className={feld}
            placeholder="max@beispiel.de"
          />
        </div>

        <div>
          <label className={label} htmlFor="telefon">
            Telefon
          </label>
          <input
            id="telefon"
            name="telefon"
            type="tel"
            autoComplete="tel"
            className={feld}
            placeholder="0170 1234567"
          />
        </div>

        <div>
          <label className={label} htmlFor="plz">
            Postleitzahl
          </label>
          <input
            id="plz"
            name="plz"
            inputMode="numeric"
            pattern="[0-9]{5}"
            maxLength={5}
            autoComplete="postal-code"
            className={feld}
            placeholder="12345"
          />
        </div>

        <div>
          <label className={label} htmlFor="jahresverbrauch_kwh">
            Stromverbrauch pro Jahr (kWh)
          </label>
          <input
            id="jahresverbrauch_kwh"
            name="jahresverbrauch_kwh"
            type="number"
            min={500}
            max={50000}
            step={100}
            className={feld}
            placeholder="4000"
          />
        </div>

        <div>
          <label className={label} htmlFor="interesse">
            Interesse
          </label>
          <select id="interesse" name="interesse" className={feld} defaultValue="unklar">
            <option value="unklar">Noch unklar — bitte beraten</option>
            <option value="voltsurfer_20">VoltSurfer 20 (20 kWh)</option>
            <option value="voltsurfer_30">VoltSurfer 30 (30 kWh)</option>
          </select>
        </div>
      </div>

      <fieldset className="mt-5">
        <legend className={label}>Vorhanden im Haushalt</legend>
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          {[
            { name: "waermepumpe", text: "Wärmepumpe" },
            { name: "eauto", text: "E-Auto" },
            { name: "pv_vorhanden", text: "PV-Anlage" },
          ].map((o) => (
            <label key={o.name} className="flex items-center gap-2 text-sm text-ink">
              <input
                type="checkbox"
                name={o.name}
                value="true"
                className="size-4 rounded border-line accent-volt"
              />
              {o.text}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="mt-5">
        <label className={label} htmlFor="nachricht">
          Deine Nachricht
        </label>
        <textarea
          id="nachricht"
          name="nachricht"
          rows={4}
          maxLength={5000}
          className={feld}
          placeholder="Was möchtest du wissen?"
        />
      </div>

      <label className="mt-5 flex items-start gap-3 text-sm text-ink-soft">
        <input
          type="checkbox"
          name="einwilligung"
          value="true"
          required
          className="mt-0.5 size-4 shrink-0 rounded border-line accent-volt"
        />
        <span>
          Ich bin damit einverstanden, dass meine Angaben zur Bearbeitung meiner Anfrage
          gespeichert und verarbeitet werden. <span className="text-volt">*</span>{" "}
          <a href="/datenschutz" className="underline underline-offset-2 hover:text-ink">
            Datenschutzerklärung
          </a>
        </span>
      </label>

      {status === "error" && fehler && (
        <p
          className="mt-4 rounded-xl border border-coral/40 bg-coral/10 px-4 py-3 text-sm font-semibold text-coral"
          role="alert"
        >
          {fehler}
        </p>
      )}

      <button
        type="submit"
        disabled={status === "sending"}
        className="mt-6 w-full touch-manipulation rounded-full bg-volt px-8 py-4 text-lg font-bold text-white transition-colors hover:bg-volt/90 disabled:opacity-60 sm:w-auto"
      >
        {status === "sending" ? "Wird gesendet …" : "Beratungstermin anfragen"}
      </button>
    </form>
  );
}
