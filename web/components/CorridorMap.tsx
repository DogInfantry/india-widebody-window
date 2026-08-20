import { GREY, INK, LIGHT, RED } from "@/lib/chart-theme";
import { corridors, geo } from "@/lib/data";
import land from "@/public/geo/land.json";

// The case, on real geography.
//
// `PastTheGulf` states the thesis as a schematic: India, a hub, a destination.
// This is the evidence for the same thesis, drawn where the places actually are,
// with every corridor the analysis covers rather than the one it argues about.
//
// **No map library, and the reason is not minimalism for its own sake.**
// MapLibre needs a tile source, which means an API key or a hosted style, on a
// project whose whole discipline is that it builds offline from committed data.
// It is roughly 800KB and renders to a WebGL canvas that neither prints nor
// takes the palette. ECharts would draw this well and is about 1MB for a third
// charting library in one repository. What this actually needs is a projection,
// which is two lines of arithmetic, and coordinates, which have been sitting in
// `data/processed/airports.parquet` since the first commit: 5,275 airports with
// latitude and longitude, from OurAirports.
//
// The land outline is Natural Earth 110m, public domain, simplified to 50KB by
// `scripts/make_basemap.py` and committed. Same arrangement as the social card:
// generated once, never built in CI.
//
// **On the one-red-element rule.** The rule protects one MESSAGE per chart, not
// one path. The message here is "fly west", so Europe and North America are the
// red, solid for the first move and dashed for the second, and every other
// corridor recedes to grey. The Gulf is deliberately the heaviest line on the
// map and deliberately not red: it is the volume, and the argument is that
// volume is not where the aircraft should go.

// Equidistant cylindrical, standard parallel at 25 degrees, which is roughly the
// latitude of Delhi and Dubai. Scaling longitude by cos(lat0) stops the map
// stretching sideways the way a plain equirectangular does at this width.
const LAT0 = (25 * Math.PI) / 180;
const KX = Math.cos(LAT0);

const LON_MIN = -95;
const LON_MAX = 165;
const LAT_MIN = -45;
const LAT_MAX = 70;

const W = (LON_MAX - LON_MIN) * KX;
const H = LAT_MAX - LAT_MIN;

const x = (lon: number) => (lon - LON_MIN) * KX;
const y = (lat: number) => LAT_MAX - lat;

const rad = (d: number) => (d * Math.PI) / 180;
const deg = (r: number) => (r * 180) / Math.PI;

/** Great-circle path between two points, sampled and projected.
 *
 *  Straight lines on a cylindrical projection are not the route an aeroplane
 *  flies, and on the Delhi to New York corridor the difference is most of the
 *  Arctic. Interpolating along the sphere and projecting each sample is the
 *  honest version and costs about ten lines. */
function arc(lat1: number, lon1: number, lat2: number, lon2: number, steps = 64): string {
  const [p1, t1, p2, t2] = [rad(lat1), rad(lon1), rad(lat2), rad(lon2)];
  const d = Math.acos(
    Math.min(1, Math.sin(p1) * Math.sin(p2) + Math.cos(p1) * Math.cos(p2) * Math.cos(t2 - t1)),
  );
  if (!d) return "";

  const points: string[] = [];
  for (let i = 0; i <= steps; i++) {
    const f = i / steps;
    const a = Math.sin((1 - f) * d) / Math.sin(d);
    const b = Math.sin(f * d) / Math.sin(d);
    const xc = a * Math.cos(p1) * Math.cos(t1) + b * Math.cos(p2) * Math.cos(t2);
    const yc = a * Math.cos(p1) * Math.sin(t1) + b * Math.cos(p2) * Math.sin(t2);
    const zc = a * Math.sin(p1) + b * Math.sin(p2);
    const lat = deg(Math.atan2(zc, Math.hypot(xc, yc)));
    const lon = deg(Math.atan2(yc, xc));
    points.push(`${x(lon).toFixed(2)},${y(lat).toFixed(2)}`);
  }
  return `M ${points.join(" L ")}`;
}

const RECOMMENDED = new Set(["Europe", "North America"]);

const drawn = corridors
  .filter((c) => c.hub_lat != null && c.hub_lon != null)
  .sort((a, b) => b.pax_total - a.pax_total);

const maxPax = Math.max(...drawn.map((c) => c.pax_total));
// Square root, because a line's visual weight is read from its area, not its
// height. Linear width would make the Gulf nine times anything else.
const weight = (pax: number) => 0.5 + 2.6 * Math.sqrt(pax / maxPax);

export function CorridorMap() {
  const o = geo.origin;

  return (
    <figure className="mt-8">
      {/* gotcha 61: a chart that cannot fit scrolls in its own box rather than
          pushing the whole page sideways on a narrow screen. */}
      <div className="overflow-x-auto">
        <svg
          viewBox={`-6 -6 ${W + 12} ${H + 30}`}
          className="w-full min-w-[640px]"
          role="img"
          aria-labelledby="cmap-title cmap-desc"
        >
          <title id="cmap-title">
            India&rsquo;s international corridors, and the two the wide-bodies should fly
          </title>
          <desc id="cmap-desc">
            Great-circle routes from Delhi to the reference hub of each corridor. Line weight is
            corridor passengers. Europe and North America, the recommended sequence, are in red.
            The Gulf is the heaviest line on the map and is not recommended.
          </desc>

          <g>
            {(land.rings as number[][][]).map((ring, i) => (
              <path
                key={i}
                d={`M ${ring.map(([lon, lat]) => `${x(lon).toFixed(1)},${y(lat).toFixed(1)}`).join(" L ")} Z`}
                fill={LIGHT}
                stroke="none"
              />
            ))}
          </g>

          {/* Corridors, heaviest first so the thin recommended arcs sit on top. */}
          <g fill="none" strokeLinecap="round">
            {drawn.map((c) => {
              const rec = RECOMMENDED.has(c.region);
              return (
                <path
                  key={c.region}
                  d={arc(o.lat, o.lon, c.hub_lat!, c.hub_lon!)}
                  stroke={rec ? RED : GREY}
                  strokeWidth={weight(c.pax_total)}
                  strokeDasharray={c.region === "North America" ? "5 4" : undefined}
                  opacity={rec ? 1 : 0.55}
                />
              );
            })}
          </g>

          <g>
            {drawn.map((c) => {
              const rec = RECOMMENDED.has(c.region);
              const gulf = c.region === "Gulf";
              return (
                <g key={c.region}>
                  <circle
                    cx={x(c.hub_lon!)}
                    cy={y(c.hub_lat!)}
                    r={gulf ? 3.4 : 2.4}
                    fill={gulf ? "#FFFFFF" : rec ? RED : GREY}
                    stroke={gulf ? GREY : "none"}
                    strokeWidth={gulf ? 1.6 : 0}
                  />
                  <text
                    x={x(c.hub_lon!)}
                    y={y(c.hub_lat!) - 5}
                    textAnchor="middle"
                    style={{
                      fontSize: 5,
                      fontWeight: rec || gulf ? 700 : 500,
                      fill: rec ? RED : gulf ? INK : GREY,
                    }}
                  >
                    {c.hub_name}
                  </text>
                </g>
              );
            })}

            <circle cx={x(o.lon)} cy={y(o.lat)} r={3.6} fill={INK} />
            <text
              x={x(o.lon)}
              y={y(o.lat) + 9}
              textAnchor="middle"
              style={{ fontSize: 5.6, fontWeight: 700, fill: INK }}
            >
              {o.name}
            </text>
          </g>

          {/* Legend, on the map rather than beside it, because a legend a reader
              has to look away to decode is a second exhibit. */}
          <g transform={`translate(2, ${H + 12})`} style={{ fontSize: 5 }}>
            <line x1={0} y1={-2} x2={14} y2={-2} stroke={RED} strokeWidth={2.4} />
            <text x={17} y={0} style={{ fill: INK, fontWeight: 600 }}>
              Deploy here: Europe first, North America second (dashed)
            </text>
            <line x1={0} y1={8} x2={14} y2={8} stroke={GREY} strokeWidth={3.4} opacity={0.55} />
            <text x={17} y={10} style={{ fill: GREY }}>
              Everywhere else. Line weight is corridor passengers, so the Gulf is the heaviest
            </text>
          </g>
        </svg>
      </div>
      <figcaption className="mt-3 text-caption leading-relaxed text-grey">
        Great circles from Delhi to each corridor&rsquo;s reference hub. Airport coordinates from
        OurAirports (CC0) via the committed extract; land outline Natural Earth 110m, public
        domain. Corridor passengers and yield headroom computed in{" "}
        <code className="text-caption">benchmarking.corridor_scale()</code> and{" "}
        <code className="text-caption">options.corridor_economics()</code>.
      </figcaption>
    </figure>
  );
}
