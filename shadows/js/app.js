(function () {
  "use strict";

  function esc(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  var data = null;
  var currentSort = "shadow";

  fetch("data/shadows_data.json")
    .then(function (r) { return r.json(); })
    .then(function (d) {
      data = d;
      renderTable();
      initUI();
    });

  function renderTable() {
    var container = document.getElementById("table-container");
    container.innerHTML = "";

    var figures;
    if (currentSort === "shadow") figures = data.by_shadow;
    else if (currentSort === "betweenness") figures = data.by_betweenness;
    else figures = data.by_citation;

    // Compute max values for scaling bars
    var maxBetw = 0, maxCite = 0, maxShadow = 0;
    figures.forEach(function (f) {
      if (f.betweenness > maxBetw) maxBetw = f.betweenness;
      if (f.in_degree > maxCite) maxCite = f.in_degree;
      if (f.shadow_score > maxShadow) maxShadow = f.shadow_score;
    });

    figures.forEach(function (f, i) {
      var row = document.createElement("div");
      row.className = "figure-row";

      // Highlight figures with high shadow score (top quartile)
      if (f.shadow_score > maxShadow * 0.5 && currentSort === "shadow") {
        row.classList.add("highlight");
      }

      var betwPct = maxBetw > 0 ? (f.betweenness / maxBetw * 100) : 0;
      var citePct = maxCite > 0 ? (f.in_degree / maxCite * 100) : 0;
      var shadowPct = maxShadow > 0 ? (f.shadow_score / maxShadow * 100) : 0;

      row.innerHTML =
        '<span class="figure-rank">' + (i + 1) + '</span>' +
        '<span class="figure-name">' + esc(f.name) +
          '<span class="figure-meta">' + esc(f.country) + ' · ' + esc(f.period) + '</span>' +
        '</span>' +
        '<div class="metric-bars">' +
          '<div class="metric-col">' +
            '<span class="metric-label">Citas</span>' +
            '<div class="metric-bar-track"><div class="metric-bar-fill" style="width:' + citePct + '%;background:#3498db"></div></div>' +
            '<span class="metric-value">' + f.in_degree + '</span>' +
          '</div>' +
          '<div class="metric-col">' +
            '<span class="metric-label">Intermediación</span>' +
            '<div class="metric-bar-track"><div class="metric-bar-fill" style="width:' + betwPct + '%;background:#f39c12"></div></div>' +
            '<span class="metric-value">' + f.betweenness.toFixed(4) + '</span>' +
          '</div>' +
          '<div class="metric-col">' +
            '<span class="metric-label">Resistencia</span>' +
            '<div class="metric-bar-track"><div class="metric-bar-fill" style="width:' + shadowPct + '%;background:#e74c3c"></div></div>' +
            '<span class="metric-value">' + f.shadow_score.toFixed(5) + '</span>' +
          '</div>' +
        '</div>';

      container.appendChild(row);
    });
  }

  function initUI() {
    document.querySelectorAll(".sort-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        currentSort = btn.dataset.sort;
        document.querySelectorAll(".sort-btn").forEach(function (b) {
          b.classList.toggle("active", b.dataset.sort === currentSort);
        });
        renderTable();
      });
    });
  }
})();
