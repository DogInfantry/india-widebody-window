import type { NextConfig } from "next";

// Static export, deliberately. Every number this app renders is precomputed by
// the Python layer and committed as JSON, so there is nothing for a server to
// do at request time. Exporting buys three things: Vercel can build it from the
// repo root without a Root Directory setting, the output is serveable by any
// static host including the existing GitHub Pages mirror, and the deploy stays
// a pure artifact like everything else in this repo.
const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
  trailingSlash: false,
};

export default nextConfig;
