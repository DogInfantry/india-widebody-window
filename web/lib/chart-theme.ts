// The house rules as values, in one place. They were copied into three chart
// files, which is three places for them to drift from `src/charts.py`, where a
// test enforces them.
//
// The rules themselves, carried over from the Python side:
//   ONE red element per chart. Red IS the argument; everything else recedes.
//   Minimal gridlines, no tick marks, no gradients, no shadows.
//   Sans labels at every size, tabular figures wherever numbers are compared.
//   No animation on load.

export const RED = "#CC0000";
export const GREY = "#999999";
export const LIGHT = "#E6E6E6";
export const INK = "#1A1A1A";
export const WASH = "#FAFAFA";

export const AXIS = {
  stroke: LIGHT,
  tick: { fill: GREY, fontSize: 12 },
  tickLine: false,
} as const;

export const TOOLTIP = {
  contentStyle: {
    border: `1px solid ${LIGHT}`,
    borderRadius: 0,
    fontSize: 13,
    boxShadow: "none",
  },
  labelStyle: { color: INK, fontWeight: 600 },
  cursor: { fill: WASH },
} as const;

/** Fill for BAR marks. `#E6E6E6` only works where there is area to see it.
 *  A scatter point is about eight pixels across and light grey on white is
 *  invisible: that is how the option 2x2 shipped reading as an empty grid. */
export const barFill = (isRed: boolean) => (isRed ? RED : LIGHT);

/** Fill for POINT and LINE marks, which have no area. Grey, never light. */
export const markFill = (isRed: boolean) => (isRed ? RED : GREY);

export const pct = (n: number, d = 1) => `${n.toFixed(d)}%`;
export const signed = (n: number, d = 1) => `${n > 0 ? "+" : ""}${n.toFixed(d)}%`;
export const n0 = (n: number) => Math.round(n).toLocaleString();
