/* Scrollytelling controller.
 *
 * Two jobs: render the KPI cards, and swap the sticky chart as each step
 * scrolls into view.
 *
 * Charts are fetched once and cached. Plotly.react is used rather than newPlot
 * so swapping between steps transitions instead of tearing down and rebuilding
 * the whole figure.
 *
 * Everything degrades rather than breaks. If a chart file is missing, that step
 * keeps the previous figure and logs; if the fetches fail entirely (opening the
 * file over file:// blocks them), a note explains how to serve it properly.
 */

(function () {
  "use strict";

  var CHART_BASE = "assets/charts/";
  var chartEl = document.getElementById("chart");
  var fallbackEl = document.getElementById("chart-fallback");
  var cache = {};
  var current = null;

  var MOBILE = window.matchMedia("(max-width: 900px)");

  function get(name) {
    if (cache[name]) return cache[name];
    cache[name] = fetch(CHART_BASE + name + ".json").then(function (r) {
      if (!r.ok) throw new Error(name + ": HTTP " + r.status);
      return r.json();
    });
    return cache[name];
  }


  var MAX_ROWS = 60;

  /* Accessibility, and a second job it happens to do.
   *
   * A Plotly chart is an SVG with no text alternative, so seventeen of them make
   * a page that a screen reader cannot use at all. Each chart therefore gets an
   * aria-label from its own title, and a collapsible table of the numbers behind
   * it.
   *
   * The table is built from `_fullData`, which is Plotly's own decoded copy, not
   * from the JSON on disk. That matters: exported arrays are often binary
   * encoded, so reading the raw file gives an object with no length, while
   * `_fullData` gives a typed array. It also means the table cannot drift from
   * the chart, because it is literally the same numbers the chart drew.
   */
  function fmt(v) {
    if (v === null || v === undefined) return "";
    if (typeof v !== "number") return String(v);
    if (Math.abs(v) >= 1000) return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
    return String(Math.round(v * 100) / 100);
  }

  function rowsFor(trace) {
    var rows = [];
    var i;
    if (trace.type === "sankey" && trace.link && trace.node) {
      var labels = trace.node.label || [];
      for (i = 0; i < trace.link.value.length; i++) {
        rows.push([
          labels[trace.link.source[i]] || trace.link.source[i],
          labels[trace.link.target[i]] || trace.link.target[i],
          fmt(trace.link.value[i])
        ]);
      }
      return { head: ["From", "To", "Passengers"], rows: rows };
    }
    if (trace.x && trace.y && trace.x.length && trace.y.length) {
      var n = Math.min(trace.x.length, trace.y.length);
      var horizontal = trace.orientation === "h";
      for (i = 0; i < n; i++) {
        rows.push([fmt(horizontal ? trace.y[i] : trace.x[i]),
                   fmt(horizontal ? trace.x[i] : trace.y[i])]);
      }
      return { head: [horizontal ? "Category" : "X", "Value"], rows: rows };
    }
    return null;
  }

  function buildTable(host) {
    var body = document.getElementById("chart-data-body");
    var details = document.getElementById("chart-data");
    if (!body || !host._fullData) return;

    body.innerHTML = "";
    var wrote = 0;
    host._fullData.forEach(function (trace) {
      if (trace.visible === false) return;
      var built = rowsFor(trace);
      if (!built || !built.rows.length) return;

      if (trace.name && host._fullData.length > 1) {
        var h = document.createElement("h4");
        h.textContent = trace.name;
        body.appendChild(h);
      }
      var table = document.createElement("table");
      var thead = document.createElement("thead");
      var hr = document.createElement("tr");
      built.head.forEach(function (label) {
        var th = document.createElement("th");
        th.scope = "col";
        th.textContent = label;
        hr.appendChild(th);
      });
      thead.appendChild(hr);
      table.appendChild(thead);

      var tbody = document.createElement("tbody");
      built.rows.slice(0, MAX_ROWS).forEach(function (r) {
        var tr = document.createElement("tr");
        r.forEach(function (cell) {
          var td = document.createElement("td");
          td.textContent = cell;
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      body.appendChild(table);

      if (built.rows.length > MAX_ROWS) {
        var note = document.createElement("p");
        note.className = "truncated";
        note.textContent =
          "Showing the first " + MAX_ROWS + " of " + built.rows.length +
          " rows. The full series is in the repository.";
        body.appendChild(note);
      }
      wrote++;
    });

    if (details) details.hidden = wrote === 0;
  }

  function describe(fig) {
    var title = (fig.layout && fig.layout.title && fig.layout.title.text) || "";
    /* The exported title carries the takeaway on the first line and the caveats
       on the rest, separated by <br>. The whole thing is the description a
       screen reader should hear, so the tags are stripped rather than the text
       truncated. */
    return title.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
  }

  function show(name) {
    if (!name || name === current) return;
    current = name;
    get(name)
      .then(function (fig) {
        if (current !== name) return; // a faster scroll already moved on
        if (fallbackEl) fallbackEl.hidden = true;
        var layout = Object.assign({}, fig.layout, {
          autosize: true,
          margin: MOBILE.matches
            ? { l: 48, r: 16, t: 92, b: 84 }
            : fig.layout.margin
        });
        Plotly.react(chartEl, fig.data, layout, {
          displayModeBar: false,
          responsive: true
        }).then(function () {
          chartEl.setAttribute("aria-label", describe(fig) || "Chart");
          buildTable(chartEl);
        });
      })
      .catch(function (err) {
        console.warn("chart unavailable:", err.message);
        if (fallbackEl && !chartEl.data) fallbackEl.hidden = false;
      });
  }

  function renderKpis() {
    var host = document.getElementById("kpis");
    if (!host) return;
    fetch(CHART_BASE + "kpis.json")
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (cards) {
        host.innerHTML = "";
        cards.forEach(function (c) {
          var box = document.createElement("div");
          box.className = "kpi";

          var num = document.createElement("span");
          num.className = "num";
          num.textContent = c.value;

          var lbl = document.createElement("span");
          lbl.className = "lbl";
          lbl.textContent = c.label;

          box.appendChild(num);
          box.appendChild(lbl);

          if (c.note) {
            var note = document.createElement("span");
            note.className = "note";
            note.textContent = c.note;
            box.appendChild(note);
          }
          host.appendChild(box);
        });
      })
      .catch(function (err) {
        console.warn("kpis unavailable:", err.message);
      });
  }

  function init() {
    renderKpis();

    var steps = Array.prototype.slice.call(document.querySelectorAll(".step"));
    if (!steps.length || !chartEl) return;

    show(steps[0].dataset.chart);

    if (typeof scrollama !== "function") {
      // No scrollama (CDN blocked). Fall back to IntersectionObserver so the
      // page still works rather than showing one frozen chart.
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (e) {
            if (e.isIntersecting) {
              steps.forEach(function (s) { s.classList.remove("is-active"); });
              e.target.classList.add("is-active");
              show(e.target.dataset.chart);
            }
          });
        },
        { rootMargin: "-45% 0px -45% 0px" }
      );
      steps.forEach(function (s) { io.observe(s); });
      return;
    }

    var scroller = scrollama();
    scroller
      .setup({
        step: ".step",
        offset: MOBILE.matches ? 0.75 : 0.55,
        debug: false
      })
      .onStepEnter(function (response) {
        steps.forEach(function (s) { s.classList.remove("is-active"); });
        response.element.classList.add("is-active");
        show(response.element.dataset.chart);
      });

    window.addEventListener("resize", function () {
      scroller.resize();
      if (chartEl.data) Plotly.Plots.resize(chartEl);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
