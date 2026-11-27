import type { Metadata } from "next";
import { Gabarito, Onest } from "next/font/google";
import "./globals.css";

const gabarito = Gabarito({ subsets: ["latin"], variable: "--font-gabarito" });
const onest = Onest({ subsets: ["latin"], variable: "--font-onest" });

export const metadata: Metadata = {
  title: "VoltSurfer — Stromspeicher, der günstig einkauft",
  description:
    "Dein Speicher lädt, wenn Strom an der Börse fast nichts kostet, und versorgt Haus, Wärmepumpe und E-Auto, wenn er teuer ist. Kein Abo, auch ohne Solaranlage.",
};

/* Gestaltungsvertrag, bleibt im ausgelieferten HTML lesbar. */
const VERTRAG = `<!--
THESIS: Ein heller, freundlicher Energieanbieter-Auftritt (Octopus / 1Komma5° / Tibber), der nicht Gefühle verkauft, sondern echte Börsenpreise zeigt. Verweigert: dunkle Neon-Energie-Optik, 3D-Haus, Icon-Kachel-Raster.
OWN-WORLD: Weiß mit weichen Flächen in Minze, Himmel und Sonne. Grün = günstig und heute real, Koralle = teuer, Sonnengelb = erst mit dem Verbund. Gabarito für Überschriften, Onest für Text, Zahlen tabellarisch. Schwebende App-Karten mit weichem Schatten, Pillen-Knöpfe.
STORY: Strom kostet nicht immer gleich viel; VoltSurfer kennt die Preise für morgen und lädt im Tal; was das bringt (heute und mit Verbund getrennt); zwei Größen mit Preis; Fragen; Beratung anfragen.
FIRST VIEWPORT: Links große Headline, Satz zur Preisspanne, grüner Beratungsknopf, Ersparnis-Satz in Textgröße. Rechts schwebende Karte "Dein Plan für morgen" mit 24 Stundenbalken aus echten Sommerpreisen, Lade- und Versorgungsfenster.
FORM: Branchenstandard (canon), bewusst gewählt nach drei Runden; Seed 0cd9fcf0.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
-->`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="de" data-scroll-behavior="smooth" className={`${gabarito.variable} ${onest.variable}`}>
      <body>
        <div hidden dangerouslySetInnerHTML={{ __html: VERTRAG }} />
        {children}
      </body>
    </html>
  );
}
