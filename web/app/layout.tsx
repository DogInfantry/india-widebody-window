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
      <body>
        <SiteNav />
        {children}
      </body>
    </html>
  );
}
