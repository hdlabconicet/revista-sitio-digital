(function () {
  "use strict";

  function esc(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  var allFigures = [];
  var figureMap = {};
  var issueYears = {};

  fetch("data/figures_data.json")
    .then(function (r) { return r.json(); })
    .then(function (data) {
      allFigures = data.figures;
      issueYears = data.issue_years;
      allFigures.forEach(function (f) { figureMap[f.key] = f; });
      showSuggestedFigures();
      initSearch();
    });

  function showSuggestedFigures() {
    var container = document.getElementById("suggested-figures");
    // Show top 20 + some interesting picks
    var suggested = allFigures.slice(0, 25);
    suggested.forEach(function (fig) {
      var chip = document.createElement("span");
      chip.className = "suggested-chip";
      chip.textContent = fig.name;
      chip.addEventListener("click", function () { selectFigure(fig.key); });
      container.appendChild(chip);
    });
  }

  function initSearch() {
    var input = document.getElementById("search-input");
    var suggestions = document.getElementById("search-suggestions");

    input.addEventListener("input", function () {
      var q = input.value.toLowerCase();
      if (q.length < 2) { suggestions.style.display = "none"; return; }

      var matches = allFigures.filter(function (f) {
        return f.name.toLowerCase().indexOf(q) !== -1;
      }).slice(0, 12);

      if (!matches.length) { suggestions.style.display = "none"; return; }

      suggestions.innerHTML = "";
      matches.forEach(function (f) {
        var div = document.createElement("div");
        div.className = "suggestion";
        div.innerHTML = '<span>' + esc(f.name) + '</span><span class="cite-count">' + f.total_citations + ' citas</span>';
        div.addEventListener("click", function () {
          selectFigure(f.key);
          input.value = f.name;
          suggestions.style.display = "none";
        });
        suggestions.appendChild(div);
      });
      suggestions.style.display = "block";
    });

    input.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { input.value = ""; suggestions.style.display = "none"; }
    });

    document.addEventListener("click", function (e) {
      if (!document.getElementById("search-container").contains(e.target)) {
        suggestions.style.display = "none";
      }
    });
  }

  function selectFigure(key) {
    var fig = figureMap[key];
    if (!fig) return;

    document.getElementById("no-selection").classList.add("hidden");
    document.getElementById("biography").classList.remove("hidden");

    // Header
    document.getElementById("bio-name").textContent = fig.name;
    var meta = [];
    if (fig.birth_year) meta.push(fig.birth_year + (fig.death_year ? "\u2013" + fig.death_year : ""));
    if (fig.country && fig.country !== "Unknown") meta.push(fig.country);
    if (fig.period && fig.period !== "Unknown") meta.push(fig.period);
    if (fig.wikidata) meta.push('<a href="' + fig.wikidata + '" target="_blank">Wikidata</a>');
    document.getElementById("bio-meta").innerHTML = meta.join(" \u00b7 ");

    // Issue bars
    renderIssueBars(fig);

    // Cited by
    renderPersonList("cited-by-list", fig.cited_by, "#e74c3c");

    // Co-cited
    renderPersonList("co-cited-list", fig.co_cited, "#3498db");
  }

  function renderIssueBars(fig) {
    var container = document.getElementById("issue-bars");
    container.innerHTML = "";

    var issues = ["issue_1", "issue_2", "issue_3", "issue_4-5", "issue_6"];
    var maxCitations = 0;
    issues.forEach(function (iid) {
      var d = fig.issues[iid];
      if (d && d.citations > maxCitations) maxCitations = d.citations;
    });

    issues.forEach(function (iid) {
      var d = fig.issues[iid];
      var year = issueYears[iid] || "";
      var row = document.createElement("div");
      row.className = "issue-bar-row";

      var label = document.createElement("span");
      label.className = "issue-bar-label";
      label.textContent = iid.replace("issue_", "#") + " (" + year + ")";

      var track = document.createElement("div");
      track.className = "issue-bar-track";

      if (d && d.citations > 0) {
        var pct = (d.citations / Math.max(maxCitations, 1)) * 100;
        var fill = document.createElement("div");
        fill.className = "issue-bar-fill";
        fill.style.width = Math.max(pct, 10) + "%";
        fill.style.backgroundColor = fig.color;
        fill.textContent = d.citations;
        track.appendChild(fill);

        // Show who cites them in this issue
        if (d.cited_by && d.cited_by.length) {
          var citers = document.createElement("span");
          citers.className = "issue-bar-citers";
          citers.textContent = "by " + d.cited_by.map(function (c) { return c.name.split(" ").pop(); }).join(", ");
          row.appendChild(label);
          row.appendChild(track);
          row.appendChild(citers);
          container.appendChild(row);
          return;
        }
      } else if (d && d.role === "author") {
        var fill2 = document.createElement("div");
        fill2.className = "issue-bar-fill";
        fill2.style.width = "100%";
        fill2.style.backgroundColor = "#f39c12";
        fill2.style.opacity = "0.5";
        fill2.textContent = "autor/a";
        track.appendChild(fill2);
      }

      row.appendChild(label);
      row.appendChild(track);
      container.appendChild(row);
    });
  }

  function renderPersonList(containerId, persons, barColor) {
    var container = document.getElementById(containerId);
    container.innerHTML = "";
    if (!persons || !persons.length) {
      container.innerHTML = '<div style="color:#556677;font-size:12px;">Ninguna</div>';
      return;
    }

    var maxCount = persons[0].count;

    persons.forEach(function (p) {
      var row = document.createElement("div");
      row.className = "person-row";
      row.addEventListener("click", function () {
        if (figureMap[p.id]) {
          selectFigure(p.id);
          document.getElementById("search-input").value = p.name;
        }
      });

      var name = document.createElement("span");
      name.className = "person-name";
      name.textContent = p.name;

      var barWrapper = document.createElement("div");
      barWrapper.className = "person-bar";
      var barFill = document.createElement("div");
      barFill.className = "person-bar-fill";
      barFill.style.width = (p.count / maxCount * 100) + "%";
      barFill.style.backgroundColor = barColor;
      barWrapper.appendChild(barFill);

      var count = document.createElement("span");
      count.className = "person-count";
      count.textContent = p.count;

      row.appendChild(name);
      row.appendChild(barWrapper);
      row.appendChild(count);
      container.appendChild(row);
    });
  }
})();
