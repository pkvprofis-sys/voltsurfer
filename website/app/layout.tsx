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
    "Mittags kostet Strom an der Börse 5 Cent, abends 14 — manchmal sogar weniger als nichts. VoltSurfer kauft in den günstigsten Stunden ein und versorgt damit dein Haus, wenn es teuer wird.",
  metadataBase: new URL("https://voltsurfer.de"),
  openGraph: {
    title: "VoltSurfer — Stromspeicher, der mitverdient",
    description:
      "Die günstigste Stunde wandert: im Sommer mittags, im Winter nachts. Dein Speicher entscheidet jeden Tag neu — bis zu 1.348 € im Jahr.",
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
