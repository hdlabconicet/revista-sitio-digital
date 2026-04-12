(function () {
  "use strict";

  var REGION_COLORS = {
    "Western Europe": "#3498db", "Latin America": "#2ecc71",
    "North America": "#e74c3c", "Eastern Europe": "#9b59b6",
    "Southern Europe / Classical": "#f39c12", "Other/Unknown": "#95a5a6",
    "Scandinavia": "#00bcd4", "Asia": "#ff9800", "Middle East": "#795548",
  };

  function esc(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  fetch("data/communities_data.json")
    .then(function (r) { return r.json(); })
    .then(function (data) { renderCards(data.communities); })
    .catch(function (err) { console.error("Error al cargar las comunidades:", err); });

  function renderCards(communities) {
    var container = document.getElementById("cards-container");

    communities.forEach(function (comm) {
      var card = document.createElement("div");
      card.className = "comm-card";
      card.addEventListener("click", function () { card.classList.toggle("expanded"); });

      // Subtitle: top 3-4 recognizable names (sorted by name length desc as proxy for notability)
      var topNames = comm.members.slice(0, 4).map(function (m) { return esc(m.name); }).join(", ");

      // Period + median as secondary info
      var periodInfo = comm.top_period;
      if (comm.median_birth_year) periodInfo += ' (mediana ' + comm.median_birth_year + ')';

      card.innerHTML =
        '<div class="comm-header">' +
          '<div class="comm-color" style="background:' + comm.color + '"></div>' +
          '<div class="comm-title">' +
            '<h3>Comunidad ' + comm.id + '</h3>' +
            '<div class="comm-subtitle">' + topNames + (comm.size > 4 ? '...' : '') + '</div>' +
          '</div>' +
          '<div class="comm-size">' + comm.size + ' <span>miembros</span></div>' +
        '</div>' +
        '<div class="comm-bars">' +
          buildRegionBar(comm.regions) +
          '<div class="comm-period-label">' + esc(periodInfo) + '</div>' +
        '</div>' +
        '<div class="comm-details">' +
          '<h4>Colaboradores/as que citan esta comunidad</h4>' +
          buildContributors(comm.top_contributors) +
          '<h4>Todos los miembros (' + comm.size + ')</h4>' +
          buildMemberList(comm.members) +
        '</div>';

      container.appendChild(card);
    });
  }

  function buildRegionBar(regions) {
    var total = 0;
    Object.keys(regions).forEach(function (k) { total += regions[k]; });
    if (!total) return "";

    var html = '<div class="region-bar">';
    Object.keys(regions).forEach(function (r) {
      var pct = regions[r] / total * 100;
      if (pct < 2) return;
      var color = REGION_COLORS[r] || "#95a5a6";
      html += '<div class="region-segment" style="width:' + pct +
        '%;background:' + color + '" data-label="' + r + ': ' + Math.round(pct) + '%"></div>';
    });
    html += '</div>';
    return html;
  }

  function buildContributors(contributors) {
    if (!contributors.length) return '<div style="color:#556677;font-size:12px">Ninguno</div>';
    var html = '';
    contributors.forEach(function (c) {
      html += '<div class="contributor-row"><span>' + esc(c.name) + '</span><span class="count">' + c.count + ' citas</span></div>';
    });
    return html;
  }

  function buildMemberList(members) {
    var html = '<div class="member-list">';
    members.forEach(function (m) {
      html += '<span class="member-chip">' + esc(m.name) + '</span>';
    });
    html += '</div>';
    return html;
  }
})();
