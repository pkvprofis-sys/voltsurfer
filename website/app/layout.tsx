import type { Metadata } from "next";
import { Bricolage_Grotesque, IBM_Plex_Mono, Instrument_Sans } from "next/font/google";
import "./globals.css";

const display = Bricolage_Grotesque({
  subsets: ["latin"],
  variable: "--font-bricolage",
  weight: ["500", "700", "800"],
});
const body = Instrument_Sans({
  subsets: ["latin"],
  variable: "--font-instrument",
  weight: ["400", "500", "600", "700"],
});
const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-plex",
  weight: ["500", "600"],
});

export const metadata: Metadata = {
  title: "VoltSurfer — Stromspeicher, der mitverdient",
  description:
    "Batteriespeicher mit intelligentem Energiemanagement: lädt, wenn Strom billig ist, versorgt dein Haus, wenn er teuer ist. Bis zu 1.348 € Ersparnis im Jahr.",
  metadataBase: new URL("https://voltsurfer.de"),
  openGraph: {
    title: "VoltSurfer — Stromspeicher, der mitverdient",
    description:
      "Bis zu 1.348 € im Jahr sparen — mit Speicher, dynamischem Tarif und § 14a-Netzentgelt.",
    locale: "de_DE",
    type: "website",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="de" className={`${display.variable} ${body.variable} ${mono.variable}`}>
      <body className="antialiased">{children}</body>
    </html>
  );
}
