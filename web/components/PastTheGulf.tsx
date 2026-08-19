import { GREY, INK, LIGHT, RED } from "@/lib/chart-theme";
import { economics, corridors } from "@/lib/data";

// The governing thought, drawn.
//
// "Compete with the Gulf hubs. Do not fly more aircraft to them" has been the
// answer since the 2026-08-18 pivot and it has never been a picture on any
// surface. It was a sentence, and then several paragraphs explaining the
// sentence, which is the reason the answer page read as a wall of text.
//
// The whole argument is one geometry: the passenger who starts in India and
// ends in Europe currently goes through a Gulf hub, and the recommendation is
// an aircraft that flies over the top of it. Two paths, one detour, one direct.
// Drawing that costs nothing and does more than the paragraphs did.
//
// **Inline SVG rather than a chart library.** There is no data series here, only
// a diagram, so Recharts has nothing to offer it. Inline keeps it themeable by
// the same tokens the charts use, printable in the PDF path, and free of any
// dependency. The house rule holds: exactly ONE red element, and it is the
// recommendation.
//
// Every number is read from the export. Nothing on this diagram is typed.

const vas = economics.value_at_stake;
const gulf = corridors.find((c) => c.region === "Gulf")!;
const europe = corridors.find((c) => c.region === "Europe")!;

const LABEL = { fontSize: 13, fontWeight: 600, fill: INK };
const SMALL = { fontSize: 11.5, fill: GREY };

export function PastTheGulf() {
  const pax = vas.connecting_pax_m.toFixed(1);
  const lo = Math.round(vas.revenue_floor_inr_cr).toLocaleString();
  const hi = Math.round(vas.revenue_ceiling_inr_cr).toLocaleString();

  return (
    <figure className="mt-10">
      {/* overflow-x-auto per gotcha 61: a diagram that cannot fit scrolls in its
          own box rather than pushing the page sideways on a 375px screen. */}
      <div className="overflow-x-auto">
        <svg
          viewBox="0 0 720 250"
          className="w-full min-w-[560px]"
          role="img"
          aria-labelledby="ptg-title ptg-desc"
        >
          <title id="ptg-title">
            The connecting passenger, and the aircraft that flies past the hub
          </title>
          <desc id="ptg-desc">
            {pax} million passengers a year travel from India to Europe and North America by
            connecting through a Gulf hub. The recommendation is direct service that makes
            that connection unnecessary.
          </desc>

          {/* THE DETOUR. Grey, because it is what happens today, not what is
              being recommended. Two legs through the hub, drawn as a dip so the
              extra distance is visible rather than asserted. */}
          <path
            d="M 96 118 C 190 118, 250 168, 352 168"
            fill="none"
            stroke={GREY}
            strokeWidth={2}
          />
          <path
            d="M 388 168 C 490 168, 550 118, 636 118"
            fill="none"
            stroke={GREY}
            strokeWidth={2}
            strokeDasharray="5 4"
          />

          {/* THE RECOMMENDATION. The one red element: an arc over the top that
              never touches the hub. This is the entire case in one stroke. */}
          <path
            d="M 96 104 C 250 34, 500 34, 636 104"
            fill="none"
            stroke={RED}
            strokeWidth={2.5}
            markerEnd="url(#ptg-arrow)"
          />
          <defs>
            <marker
              id="ptg-arrow"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill={RED} />
            </marker>
          </defs>

          <text x={366} y={62} textAnchor="middle" style={{ ...LABEL, fill: RED }}>
            Fly past it
          </text>
          <text x={366} y={80} textAnchor="middle" style={SMALL}>
            Europe first, North America second
          </text>

          {/* Nodes. The hub is hollow because the recommendation is to stop
              routing value through it, not to stop flying there. */}
          <circle cx={84} cy={112} r={9} fill={INK} />
          <circle cx={370} cy={168} r={11} fill="#FFFFFF" stroke={GREY} strokeWidth={2} />
          <circle cx={648} cy={112} r={9} fill={INK} />

          <text x={84} y={140} textAnchor="middle" style={LABEL}>
            India
          </text>
          <text x={370} y={196} textAnchor="middle" style={{ ...LABEL, fill: GREY }}>
            Gulf hub
          </text>
          <text x={648} y={140} textAnchor="middle" style={LABEL}>
            Europe, North America
          </text>

          <text x={370} y={214} textAnchor="middle" style={SMALL}>
            {pax}M passengers a year connect here
          </text>
          <text x={370} y={231} textAnchor="middle" style={SMALL}>
            worth INR {lo} to {hi} crore
          </text>

          {/* The two corridor headroom figures, placed under the endpoint each
              describes, so the comparison needs no legend and no sentence. */}
          <text x={84} y={162} textAnchor="middle" style={SMALL}>
            Gulf sectors {gulf.yield_headroom_pct!.toFixed(1)}% headroom
          </text>
          <text x={648} y={162} textAnchor="middle" style={SMALL}>
            Europe +{europe.yield_headroom_pct!.toFixed(1)}%
          </text>

          <line x1={40} y1={236} x2={0} y2={236} stroke={LIGHT} />
        </svg>
      </div>
      <figcaption className="mt-3 text-[12.5px] leading-relaxed text-grey">
        The corridor is the prize and the hub is not the destination. Connecting passengers
        and the contested revenue band are computed in{" "}
        <code className="text-[12px]">options.value_at_stake()</code>; corridor headroom in{" "}
        <code className="text-[12px]">options.corridor_economics()</code>.
      </figcaption>
    </figure>
  );
}
