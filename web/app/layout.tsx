import type { Metadata } from "next";
import { IBM_Plex_Sans, IBM_Plex_Serif } from "next/font/google";
import { SiteNav } from "@/components/SiteNav";
import "./globals.css";

// next/font self-hosts these, so the app drops the two Google Fonts round trips
// the static mirror still pays for, and there is no layout shift on first paint.
const plexSans = IBM_Plex_Sans({
  variable: "--font-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const plexSerif = IBM_Plex_Serif({
  variable: "--font-plex-serif",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  display: "swap",
});

const SITE = "https://india-widebody-window.vercel.app";

// Structured data, byte-identical to the block in `docs/index.html`. Report plus
// Dataset, naming the five sources, the licence and the author. It carries no
// figures on purpose: `CORPUS_FILES` globs this file, the narrative guard strips
// tags and reads the JSON body as prose, and metadata is the wrong place to
// publish a number that would then have to be swept like any other.
const JSON_LD = {
 "@context": "https://schema.org",
 "@graph": [
  {
   "@id": "https://india-widebody-window.vercel.app/#report",
   "@type": "Report",
   "about": [
    {
     "@type": "Thing",
     "name": "Commercial aviation market entry"
    },
    {
     "@type": "Thing",
     "name": "Wide-body aircraft deployment"
    },
    {
     "@type": "Thing",
     "name": "India Gulf air corridor"
    },
    {
     "@type": "Organization",
     "name": "IndiGo"
    },
    {
     "@type": "Organization",
     "name": "Air India"
    },
    {
     "@type": "Place",
     "name": "India"
    }
   ],
   "abstract": "Compete with the Gulf hubs, do not fly more aircraft to them. Europe first, North America second, Gulf capacity roughly flat. A commercial aviation market entry case in which every figure is computed from committed open data, conflicts between agencies are reported rather than resolved away, and every change of mind is published.",
   "author": {
    "@type": "Person",
    "name": "Anklesh Rawat",
    "url": "https://github.com/DogInfantry"
   },
   "creator": {
    "@type": "Person",
    "name": "Anklesh Rawat",
    "url": "https://github.com/DogInfantry"
   },
   "datePublished": "2026-08-15",
   "headline": "Where should Indian carriers deploy their next 100 long-haul aircraft, and can the India-Gulf corridor absorb them?",
   "inLanguage": "en",
   "isAccessibleForFree": true,
   "isBasedOn": {
    "@id": "https://india-widebody-window.vercel.app/#dataset"
   },
   "license": "https://opensource.org/licenses/MIT",
   "name": "India's Wide-Body Window",
   "url": "https://india-widebody-window.vercel.app"
  },
  {
   "@id": "https://india-widebody-window.vercel.app/#dataset",
   "@type": "Dataset",
   "codeRepository": "https://github.com/DogInfantry/india-widebody-window",
   "creator": {
    "@type": "Person",
    "name": "Anklesh Rawat",
    "url": "https://github.com/DogInfantry"
   },
   "description": "Indian international and domestic air traffic, carrier operating statistics, corridor economics, wide-body order book and market sizing, computed from DGCA, Eurostat, IATA, World Bank and OurAirports and committed as parquet. Modelled values are labelled as modelled and hand-entered values carry a verification status.",
   "distribution": [
    {
     "@type": "DataDownload",
     "contentUrl": "https://github.com/DogInfantry/india-widebody-window/tree/main/data/processed",
     "encodingFormat": "application/vnd.apache.parquet",
     "name": "Processed parquet corpus"
    }
   ],
   "isAccessibleForFree": true,
   "isBasedOn": [
    {
     "@type": "Dataset",
     "description": "Indian domestic and international traffic, the spine of the analysis.",
     "license": "https://opendatacommons.org/licenses/odbl/",
     "name": "DGCA traffic statistics",
     "url": "https://github.com/Vonter/india-aviation-traffic"
    },
    {
     "@type": "Dataset",
     "description": "The European end of India to Europe routes, used to check DGCA from the opposite direction.",
     "license": "https://ec.europa.eu/info/legal-notice_en",
     "name": "Eurostat avia_par",
     "url": "https://ec.europa.eu/eurostat/web/transport/data/database"
    },
    {
     "@type": "Dataset",
     "description": "India's departing international origin to destination split, by region and by country.",
     "license": "https://www.iata.org/en/about/terms-conditions/",
     "name": "IATA, Aviation in India",
     "url": "https://www.iata.org/"
    },
    {
     "@type": "Dataset",
     "description": "Income, population and air travel propensity across twelve peer countries.",
     "license": "https://creativecommons.org/licenses/by/4.0/",
     "name": "World Bank Open Data",
     "url": "https://data.worldbank.org/"
    },
    {
     "@type": "Dataset",
     "description": "Airport reference data and coordinates.",
     "license": "https://creativecommons.org/publicdomain/zero/1.0/",
     "name": "OurAirports",
     "url": "https://ourairports.com/data/"
    }
   ],
   "keywords": [
    "commercial aviation",
    "India",
    "DGCA",
    "airline economics",
    "market sizing",
    "wide-body aircraft",
    "India Gulf corridor",
    "yield headroom",
    "available seat kilometres",
    "open data"
   ],
   "license": "https://opensource.org/licenses/MIT",
   "name": "India's Wide-Body Window computed corpus",
   "spatialCoverage": {
    "@type": "Place",
    "name": "India and its international corridors"
   },
   "temporalCoverage": "2015/2026",
   "url": "https://github.com/DogInfantry/india-widebody-window",
   "variableMeasured": [
    "International sector passengers",
    "Available seat kilometres",
    "Average stage length",
    "Load factor",
    "Yield headroom by corridor",
    "Seat entitlement utilisation",
    "Unit cost per available seat kilometre"
   ]
  },
  {
   "@id": "https://india-widebody-window.vercel.app/#website",
   "@type": "WebSite",
   "inLanguage": "en",
   "license": "https://opensource.org/licenses/MIT",
   "name": "India's Wide-Body Window",
   "publisher": {
    "@type": "Person",
    "name": "Anklesh Rawat",
    "url": "https://github.com/DogInfantry"
   },
   "url": "https://india-widebody-window.vercel.app"
  }
 ]
};

export const metadata: Metadata = {
  metadataBase: new URL(SITE),
  title: {
    default: "India's Wide-Body Window",
    template: "%s | India's Wide-Body Window",
  },
  description:
    "Where should Indian carriers deploy their next 100 long-haul aircraft, and can the India-Gulf corridor absorb them?",
  openGraph: {
    type: "website",
    url: SITE,
    title: "India's Wide-Body Window",
    description:
      "Compete with the Gulf hubs, do not fly more aircraft to them. Europe first, North America second.",
    images: [{ url: "/social-card.png", alt: "India's Wide-Body Window" }],
  },
  twitter: { card: "summary_large_image", images: ["/social-card.png"] },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    // The font variables go on <html>, not <body>. Tailwind v4 declares
    // --font-sans and --font-serif inside @theme, which lands on :root, and a
    // var() reference inside a custom property is resolved at the element that
    // DECLARES it. With the next/font classes on <body>, :root could not see
    // --font-plex-sans, the declaration became invalid, and every heading
    // silently fell back to -apple-system.
    <html lang="en" className={`${plexSans.variable} ${plexSerif.variable}`}>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(JSON_LD) }}
        />
      </head>
      <body>
        <SiteNav />
        {children}
      </body>
    </html>
  );
}
