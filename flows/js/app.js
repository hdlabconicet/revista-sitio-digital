(function () {
  "use strict";

  function esc(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  fetch("data/flows_data.json")
    .then(function (r) { return r.json(); })
    .then(function (data) { render(data); });

  function render(data) {
    var container = document.getElementById("flows-container");
    var colors = data.region_colors;

    // Legend
    var legend = document.createElement("div");
    legend.className = "legend";
    Object.keys(data.region_totals).forEach(function (region) {
      var item = document.createElement("span");
      item.className = "legend-item";
      item.innerHTML = '<span class="legend-dot" style="background:' + (colors[region] || "#95a5a6") + '"></span>' + region;
      legend.appendChild(item);
    });
    container.appendChild(legend);

    // One bar per contributor
    data.contributors.forEach(function (c) {
      var row = document.createElement("div");
      row.className = "flow-row";

      var label = document.createElement("div");
      label.className = "flow-label";
      label.textContent = c.name;

      var bar = document.createElement("div");
      bar.className = "flow-bar";

      // Sort regions by count descending for this contributor
      var regions = Object.keys(c.flows).sort(function (a, b) { return c.flows[b] - c.flows[a]; });
      regions.forEach(function (region) {
        var count = c.flows[region];
        var pct = (count / c.total) * 100;
        if (pct < 1) return;
        var seg = document.createElement("div");
        seg.className = "flow-segment";
        seg.style.width = pct + "%";
        seg.style.backgroundColor = colors[region] || "#95a5a6";
        seg.setAttribute("data-label", esc(region) + ": " + count + " (" + Math.round(pct) + "%)");
        bar.appendChild(seg);
      });

      var total = document.createElement("div");
      total.className = "flow-total";
      total.textContent = c.total;

      row.appendChild(label);
      row.appendChild(bar);
      row.appendChild(total);
      container.appendChild(row);
    });
  }
})();
