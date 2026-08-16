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
