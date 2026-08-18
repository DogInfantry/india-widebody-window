"""Chart builders in the Bain visual identity.

House rules, enforced here rather than left to each caller:

- One red element per chart. Everything else is grey. Colour marks the point
  being made, it is not decoration.
- Titles state the takeaway, never the topic. "IndiGo leads domestic but cedes
  the Gulf connect premium", not "Market share by carrier".
- Every figure carries its source line. A chart without provenance does not ship.
- Modelled numbers are labelled modelled on the chart face, not in a footnote
  somebody has to go looking for.

Attribution. `mekko()` is adapted from Vizro's `marimekko.py`
(https://github.com/mckinsey/vizro, Apache-2.0), whose chart taxonomy derives from
the FT Visual Vocabulary (MIT, (c) 2016 FT Interactive News). See NOTICE. The
variable-width stacked bar approach, normalised widths with cumulative x
positions, originates there. Changes made here are listed in that function.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

ROOT = Path(__file__).resolve().parent.parent
CHART_DIR = ROOT / "docs" / "assets" / "charts"

# Bain palette. RED is the signal colour and is spent on one element per chart.
RED = "#CC0000"
ACCENT = "#EE3224"
INK = "#1A1A1A"
GREY = "#999999"
LIGHT = "#E6E6E6"
PAPER = "#FFFFFF"

# Ordered greys for series that must be distinguishable without competing with
# the red. Deliberately short: a chart needing more than four muted series is a
# chart that needs splitting.
MUTED = ["#4D4D4D", "#808080", "#B3B3B3", "#D9D9D9"]

# Charts use the sans, never the display serif. Axis ticks, data labels and
# legends live at 11 to 13px where a serif loses legibility, and Plex Sans has
# true tabular figures so numeric labels align down a column.
FONT = "IBM Plex Sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
# The display face, used only for chart titles, which are set at 19px and are
# the one place a figure carries a headline rather than a label.
FONT_DISPLAY = "IBM Plex Serif, Georgia, 'Times New Roman', serif"

_TEMPLATE_NAME = "bain"


def _register_template() -> None:
    pio.templates[_TEMPLATE_NAME] = go.layout.Template(
        layout=go.Layout(
            font=dict(family=FONT, size=13, color=INK),
            paper_bgcolor=PAPER,
            plot_bgcolor=PAPER,
            colorway=[RED] + MUTED,
            margin=dict(l=72, r=32, t=96, b=72),
            title=dict(
                font=dict(family=FONT_DISPLAY, size=19, color=INK),
                x=0,
                xanchor="left",
                y=0.96,
                yanchor="top",
            ),
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showline=True,
                linecolor=LIGHT,
                ticks="outside",
                tickcolor=LIGHT,
                tickfont=dict(size=12, color=GREY),
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=LIGHT,
                gridwidth=1,
                zeroline=False,
                showline=False,
                tickfont=dict(size=12, color=GREY),
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.22,
                xanchor="left",
                x=0,
                font=dict(size=12, color=GREY),
                title_text="",
            ),
            hoverlabel=dict(font=dict(family=FONT, size=12), bordercolor=LIGHT),
        )
    )


_register_template()


def finish(
    fig: go.Figure,
    *,
    title: str,
    subtitle: str | None = None,
    source: str,
    modeled: bool = False,
) -> go.Figure:
    """Apply the house template, takeaway title, source line and modelled badge.

    `title` must be the takeaway. Writing a topic here ("Market share by
    carrier") means the chart has not been thought through yet.

    `modeled=True` stamps a visible badge on the chart face. Not optional
    politeness: a modelled margin that reads as a measured one is the single most
    damaging thing a chart in this project could do.
    """
    heading = title
    if subtitle:
        heading = f"{title}<br><span style='font-size:13px;color:{GREY}'>{subtitle}</span>"
    fig.update_layout(template=_TEMPLATE_NAME, title_text=heading)

    fig.add_annotation(
        text=f"<span style='color:{GREY}'>Source: {source}</span>",
        xref="paper",
        yref="paper",
        x=0,
        y=-0.30,
        xanchor="left",
        yanchor="top",
        showarrow=False,
        font=dict(size=11),
    )

    if modeled:
        fig.add_annotation(
            text="<b>MODELLED</b>",
            xref="paper",
            yref="paper",
            x=1,
            y=1.06,
            xanchor="right",
            yanchor="bottom",
            showarrow=False,
            font=dict(size=11, color=PAPER),
            bgcolor=ACCENT,
            borderpad=4,
        )
    return fig


def _highlight_colors(labels, highlight) -> list[str]:
    """Red for the one label being argued about, grey for the rest."""
    wanted = {highlight} if isinstance(highlight, str) else set(highlight or ())
    return [RED if str(label) in wanted else GREY for label in labels]


# --------------------------------------------------------------------------
# builders
# --------------------------------------------------------------------------


def bar(
    df: pd.DataFrame,
    *,
    category: str,
    value: str,
    highlight: str | list[str] | None = None,
    orientation: str = "v",
    value_fmt: str = ",.0f",
    sort: bool = True,
) -> go.Figure:
    """Ranked bar with a single highlighted member.

    `sort=False` keeps the caller's order. Added for the cargo chart, where the
    point is that freight per passenger does NOT track sector length: ordering
    those bars by value would hide the very absence the chart exists to show.
    Ranking stays the default because for most exhibits it is the right answer.
    """
    d = df.sort_values(value, ascending=(orientation == "h")) if sort else df
    colors = _highlight_colors(d[category], highlight)
    labels = d[value].map(lambda v: format(v, value_fmt))
    if orientation == "h":
        trace = go.Bar(
            x=d[value],
            y=d[category],
            orientation="h",
            marker_color=colors,
            text=labels,
            textposition="outside",
        )
    else:
        trace = go.Bar(
            x=d[category],
            y=d[value],
            marker_color=colors,
            text=labels,
            textposition="outside",
        )
    fig = go.Figure(trace)
    fig.update_layout(showlegend=False)
    return fig


def slope(
    df: pd.DataFrame,
    *,
    label: str,
    start_col: str,
    end_col: str,
    start_name: str,
    end_name: str,
    highlight: str | list[str] | None = None,
) -> go.Figure:
    """Two-period slope chart. Shows direction of change, not level."""
    fig = go.Figure()
    for _, row in df.iterrows():
        is_hot = _highlight_colors([row[label]], highlight)[0] == RED
        fig.add_trace(
            go.Scatter(
                x=[start_name, end_name],
                y=[row[start_col], row[end_col]],
                mode="lines+markers+text",
                line=dict(color=RED if is_hot else LIGHT, width=3 if is_hot else 1.5),
                marker=dict(size=8, color=RED if is_hot else GREY),
                text=[f"{row[label]}  ", f"  {row[label]}"],
                textposition=["middle left", "middle right"],
                textfont=dict(size=12, color=INK if is_hot else GREY),
                hovertemplate=f"<b>{row[label]}</b><br>%{{x}}: %{{y:,.0f}}<extra></extra>",
                showlegend=False,
            )
        )
    fig.update_xaxes(showline=False, ticks="")
    return fig


def waterfall(
    df: pd.DataFrame, *, x: str, y: str, measure: str, value_fmt: str = ",.0f"
) -> go.Figure:
    """Bridge from one total to another.

    Native `go.Waterfall`, no custom geometry. Found while reading Vizro's
    waterfall example: this is a built-in Plotly trace type, so hand-building it
    would have been pure waste.
    """
    fig = go.Figure(
        go.Waterfall(
            x=df[x],
            y=df[y],
            measure=df[measure],
            connector=dict(line=dict(color=LIGHT, width=1)),
            increasing=dict(marker=dict(color=GREY)),
            decreasing=dict(marker=dict(color=GREY)),
            totals=dict(marker=dict(color=RED)),
            text=df[y].map(lambda v: format(v, value_fmt)),
            textposition="outside",
        )
    )
    fig.update_layout(showlegend=False)
    return fig


def sankey(
    links: pd.DataFrame,
    *,
    source: str,
    target: str,
    value: str,
    highlight_nodes: list[str] | None = None,
) -> go.Figure:
    """Flow diagram, built for one job: showing where India's traffic actually goes.

    `links` is an edge list. Node order follows first appearance so the columns
    read left to right in the order the story is told.
    """
    nodes: list[str] = []
    for col in (source, target):
        for name in links[col]:
            if name not in nodes:
                nodes.append(name)
    index = {name: i for i, name in enumerate(nodes)}
    hot = set(highlight_nodes or ())

    return go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                label=nodes,
                pad=18,
                thickness=16,
                color=[RED if n in hot else GREY for n in nodes],
                line=dict(color=PAPER, width=0),
            ),
            link=dict(
                source=links[source].map(index),
                target=links[target].map(index),
                value=links[value],
                color=[
                    "rgba(204,0,0,0.28)" if s in hot or t in hot else "rgba(153,153,153,0.22)"
                    for s, t in zip(links[source], links[target])
                ],
            ),
        )
    )


def triangulation(
    estimates: dict[str, float], *, band: tuple[float, float], value_fmt: str = ",.1f"
) -> go.Figure:
    """Three independent estimates converging on a reconciled band.

    The band is drawn, not the average. Averaging three methods hides the very
    disagreement that makes the exercise worth doing.
    """
    names = list(estimates)
    values = [estimates[n] for n in names]
    lo, hi = band

    fig = go.Figure()
    fig.add_shape(
        type="rect",
        x0=-0.5,
        x1=len(names) - 0.5,
        y0=lo,
        y1=hi,
        fillcolor="rgba(204,0,0,0.10)",
        line=dict(width=0),
        layer="below",
    )
    fig.add_trace(
        go.Bar(
            x=names,
            y=values,
            marker_color=GREY,
            width=0.45,
            text=[format(v, value_fmt) for v in values],
            textposition="outside",
        )
    )
    for y in (lo, hi):
        fig.add_shape(
            type="line",
            x0=-0.5,
            x1=len(names) - 0.5,
            y0=y,
            y1=y,
            line=dict(color=RED, width=2, dash="dot"),
        )
    fig.add_annotation(
        x=len(names) - 0.5,
        y=hi,
        text=f"<b>reconciled band {format(lo, value_fmt)} to {format(hi, value_fmt)}</b>",
        xanchor="right",
        yanchor="bottom",
        showarrow=False,
        font=dict(size=12, color=RED),
    )
    fig.update_layout(showlegend=False)
    return fig


def profit_pool_curve(
    df: pd.DataFrame, *, segment: str, revenue: str, margin: str, highlight: str | None = None
) -> go.Figure:
    """Profit pool: cumulative revenue on x, operating margin on y.

    Segment width is revenue, height is margin, so each rectangle's area is that
    segment's profit. Gadiesh and Gilbert, HBR 1998.
    """
    d = df.sort_values(margin, ascending=False).reset_index(drop=True)
    widths = d[revenue].to_numpy(dtype=float)
    left = widths.cumsum() - widths
    centers = left + widths / 2
    colors = _highlight_colors(d[segment], highlight)

    fig = go.Figure(
        go.Bar(
            x=centers,
            y=d[margin],
            width=widths,
            marker_color=colors,
            marker_line=dict(color=PAPER, width=1.5),
            customdata=d[[segment, revenue]].to_numpy(),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>revenue %{customdata[1]:,.0f}"
                "<br>margin %{y:.1f}%<extra></extra>"
            ),
            text=d[segment],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color=PAPER, size=11),
        )
    )
    fig.update_layout(showlegend=False, bargap=0)
    fig.update_xaxes(title_text="Cumulative revenue", showticklabels=False)
    fig.update_yaxes(title_text="Operating margin (%)")
    return fig


def mekko(
    df: pd.DataFrame,
    *,
    category: str,
    subcategory: str,
    values: str,
    highlight: str | list[str] | None = None,
    total_fmt: str = ",.1f",
) -> go.Figure:
    """Marimekko. Column width is market size, segment height is share, so each
    cell's area encodes an absolute quantity.

    Adapted from Vizro's `marimekko.py` (Apache-2.0, see NOTICE). Four changes
    from the original, three of them fixing real fragility:

    1. The original assigns a full-length `pct` Series onto a filtered frame and
       relies on pandas index alignment. Replaced with an explicit pivot.
    2. The original assumes exactly one row per (category, subcategory) pair and
       silently takes element zero. This pre-aggregates, so passing raw rows
       works instead of quietly producing a wrong chart.
    3. The original hardcodes the total annotation at y=112 against a fixed
       [0, 115] axis. Here it is derived from the axis so it cannot drift.
    4. Colour follows the house rule: one red subcategory, the rest muted.
    """
    if df.empty:
        raise ValueError("mekko received an empty frame")

    grid = (
        df.groupby([category, subcategory], as_index=False)[values]
        .sum()
        .pivot(index=subcategory, columns=category, values=values)
        .fillna(0.0)
    )

    totals = grid.sum(axis=0)
    order = totals.sort_values(ascending=False).index
    grid, totals = grid[order], totals[order]

    widths = (totals / totals.sum()).to_numpy(dtype=float)
    left = widths.cumsum() - widths
    centers = left + widths / 2
    share = (grid / totals) * 100.0

    subcats = list(grid.index)
    colors = _highlight_colors(subcats, highlight)
    muted = iter(MUTED * (len(subcats) // len(MUTED) + 1))
    palette = {
        name: (RED if color == RED else next(muted)) for name, color in zip(subcats, colors)
    }

    top = 100.0
    headroom = top * 0.12
    fig = go.Figure()
    for name in subcats:
        y = share.loc[name].to_numpy(dtype=float)
        fig.add_trace(
            go.Bar(
                x=centers,
                y=y,
                width=widths,
                name=str(name),
                marker_color=palette[name],
                marker_line=dict(color=PAPER, width=1.5),
                customdata=[[c, totals[c]] for c in grid.columns],
                text=[f"{v:.0f}%" if v > 8 else "" for v in y],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(color=PAPER, size=11),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    + str(name)
                    + ": %{y:.1f}%<br>total %{customdata[1]:,.0f}<extra></extra>"
                ),
            )
        )

    for center, col in zip(centers, grid.columns):
        fig.add_annotation(
            x=center,
            y=top + headroom * 0.35,
            text=f"<b>{col}</b><br>{format(totals[col], total_fmt)}",
            showarrow=False,
            font=dict(size=11, color=INK),
            xanchor="center",
            yanchor="bottom",
        )

    fig.update_layout(barmode="stack", bargap=0)
    fig.update_xaxes(range=[0, 1], showticklabels=False, showline=False, ticks="")
    fig.update_yaxes(range=[0, top + headroom], showticklabels=False, showgrid=False)
    return fig


def kpi(value: str, label: str, *, note: str | None = None) -> dict:
    """A hero metric, as data rather than a figure.

    Deliberately not a Plotly chart. Three numbers in boxes is HTML and CSS; a
    chart engine for that would be 300 KB spent drawing a rectangle.
    """
    return {"value": value, "label": label, "note": note}


# --------------------------------------------------------------------------
# export
# --------------------------------------------------------------------------


def export(fig: go.Figure, name: str) -> Path:
    """Write a figure to docs/assets/charts/<name>.json for the page to load."""
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / f"{name}.json"
    path.write_text(fig.to_json(), encoding="utf-8")
    return path


def export_kpis(cards: list[dict], name: str = "kpis") -> Path:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / f"{name}.json"
    path.write_text(json.dumps(cards, indent=2), encoding="utf-8")
    return path
