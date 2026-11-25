import type { NextConfig } from "next";

/*
 * Die Verkaufsseite ist eine statische HTML-Seite nach dem Taste-Skill
 * (public/index.html mit dem Baukasten in public/assets). Next.js liefert sie
 * aus und stellt daneben nur die Anfrage-API (/api/anfrage) bereit.
 */
const nextConfig: NextConfig = {
  async rewrites() {
    return {
      beforeFiles: [
        { source: "/", destination: "/index.html" },
        { source: "/impressum", destination: "/impressum.html" },
        { source: "/datenschutz", destination: "/datenschutz.html" },
      ],
      afterFiles: [],
      fallback: [],
    };
  },
};

export default nextConfig;
