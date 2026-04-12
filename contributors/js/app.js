(function () {
  "use strict";

  function esc(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  var data = null;
  var cellSize = 28;
  var labelWidth = 120;
  var hoveredCell = null;

  fetch("data/affinities_data.json")
    .then(function (r) { return r.json(); })
    .then(function (d) {
      data = d;
      renderMatrix();
    });

  var REGION_COLORS = {
    "Western Europe": "#3498db",
    "Latin America": "#2ecc71",
    "North America": "#e74c3c",
    "Eastern Europe": "#9b59b6",
    "Southern Europe / Classical": "#f39c12",
    "Other/Unknown": "#95a5a6",
    "Scandinavia": "#00bcd4",
    "Asia": "#ff9800",
    "Middle East": "#795548",
  };

  function renderMatrix() {
    var canvas = document.getElementById("matrix-canvas");
    var n = data.contributors.length;
    var totalSize = labelWidth + n * cellSize;
    var dpr = window.devicePixelRatio || 1;

    canvas.width = totalSize * dpr;
    canvas.height = totalSize * dpr;
    canvas.style.width = totalSize + "px";
    canvas.style.height = totalSize + "px";

    var ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);

    // Background
    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, totalSize, totalSize);

    // Column labels (rotated)
    ctx.save();
    ctx.font = "10px sans-serif";
    ctx.fillStyle = "#8899aa";
    ctx.textAlign = "left";
    for (var j = 0; j < n; j++) {
      ctx.save();
      ctx.translate(labelWidth + j * cellSize + cellSize / 2, labelWidth - 4);
      ctx.rotate(-Math.PI / 3);
      var colName = data.contributors[j].name;
      if (colName.length > 16) colName = colName.substring(0, 14) + "..";
      ctx.fillText(colName, 0, 0);
      ctx.restore();
    }

    // Row labels
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (var i = 0; i < n; i++) {
      var rowName = data.contributors[i].name;
      if (rowName.length > 16) rowName = rowName.substring(0, 14) + "..";
      ctx.fillStyle = "#8899aa";
      ctx.fillText(rowName, labelWidth - 6, labelWidth + i * cellSize + cellSize / 2);
    }

    // Matrix cells
    for (var i = 0; i < n; i++) {
      for (var j = 0; j < n; j++) {
        var cell = data.matrix[i][j];
        var x = labelWidth + j * cellSize;
        var y = labelWidth + i * cellSize;

        if (i === j) {
          // Diagonal — show unique count
          ctx.fillStyle = "#0f3460";
          ctx.fillRect(x + 1, y + 1, cellSize - 2, cellSize - 2);
          ctx.fillStyle = "#667788";
          ctx.font = "9px sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(data.contributors[i].unique_figures, x + cellSize / 2, y + cellSize / 2);
        } else {
          // Off-diagonal — Jaccard similarity as color intensity
          var intensity = Math.min(cell.jaccard * 5, 1); // Scale up for visibility
          var r = Math.round(52 + intensity * (52));
          var g = Math.round(152 + intensity * (103));
          var b = Math.round(219);
          ctx.fillStyle = intensity > 0.01 ?
            "rgba(" + r + "," + g + "," + b + "," + (0.15 + intensity * 0.85) + ")" :
            "#111122";
          ctx.fillRect(x + 1, y + 1, cellSize - 2, cellSize - 2);

          // Show shared count in cells with significant overlap
          if (cell.shared > 5) {
            ctx.fillStyle = "#eee";
            ctx.font = "9px sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(cell.shared, x + cellSize / 2, y + cellSize / 2);
          }
        }
      }
    }

    ctx.restore();

    // Click handler
    canvas.addEventListener("click", function (e) {
      var rect = canvas.getBoundingClientRect();
      var mx = e.clientX - rect.left;
      var my = e.clientY - rect.top;

      var col = Math.floor((mx - labelWidth) / cellSize);
      var row = Math.floor((my - labelWidth) / cellSize);

      if (col < 0 || row < 0 || col >= n || row >= n) return;

      document.getElementById("detail-section").classList.remove("hidden");

      if (row === col) {
        showSingleDetail(row);
      } else {
        showPairDetail(Math.min(row, col), Math.max(row, col));
      }
    });

    // Hover tooltip via title
    canvas.addEventListener("mousemove", function (e) {
      var rect = canvas.getBoundingClientRect();
      var mx = e.clientX - rect.left;
      var my = e.clientY - rect.top;
      var col = Math.floor((mx - labelWidth) / cellSize);
      var row = Math.floor((my - labelWidth) / cellSize);

      if (col >= 0 && row >= 0 && col < n && row < n) {
        if (row === col) {
          canvas.title = data.contributors[row].name + ": " + data.contributors[row].unique_figures + " figuras únicas";
        } else {
          var cell = data.matrix[row][col];
          canvas.title = data.contributors[row].name + " + " + data.contributors[col].name + ": " + cell.shared + " figuras compartidas (Jaccard: " + cell.jaccard + ")";
        }
      } else {
        canvas.title = "";
      }
    });
  }

  function showPairDetail(i, j) {
    document.getElementById("pair-detail").classList.remove("hidden");
    document.getElementById("single-detail").classList.add("hidden");

    var a1 = data.contributors[i];
    var a2 = data.contributors[j];
    var cell = data.matrix[i][j];

    document.getElementById("pair-title").textContent = a1.name + " + " + a2.name;
    document.getElementById("pair-stats").textContent =
      cell.shared + " figuras compartidas (Jaccard: " + cell.jaccard + ")";

    var container = document.getElementById("pair-shared");
    container.innerHTML = "";

    var key = i + "-" + j;
    var shared = data.shared_details[key] || [];
    if (!shared.length) {
      container.innerHTML = "<div style='color:#556677'>Sin figuras compartidas</div>";
      return;
    }

    shared.forEach(function (fig) {
      var div = document.createElement("div");
      div.className = "shared-figure";
      div.innerHTML = '<span>' + esc(fig.name) + '</span><span class="count">' + fig.count + '</span>';
      container.appendChild(div);
    });
  }

  function showSingleDetail(i) {
    document.getElementById("single-detail").classList.remove("hidden");
    document.getElementById("pair-detail").classList.add("hidden");

    var c = data.contributors[i];
    document.getElementById("single-name").textContent = c.name;
    document.getElementById("single-meta").innerHTML =
      c.total_citations + " citas · " +
      c.unique_figures + " figuras · " +
      c.num_texts + " textos · " +
      "Números: " + c.issues.map(function (x) { return x.replace("issue_", "#"); }).join(", ");

    // Region bar
    var regions = c.region_breakdown;
    var total = 0;
    Object.keys(regions).forEach(function (k) { total += regions[k]; });

    var barHtml = '<div class="region-bar">';
    Object.keys(regions).forEach(function (r) {
      var pct = regions[r] / total * 100;
      if (pct < 1) return;
      barHtml += '<div class="region-segment" style="width:' + pct + '%;background:' +
        (REGION_COLORS[r] || "#95a5a6") + '" title="' + r + ': ' + Math.round(pct) + '%"></div>';
    });
    barHtml += '</div>';

    // Top cited
    var citedHtml = '<h4 style="font-size:12px;color:#8899aa;margin:12px 0 6px;">Más citados</h4>';
    c.top_cited.forEach(function (f) {
      citedHtml += '<div class="shared-figure"><span>' + esc(f.name) + '</span><span class="count">' + f.count + '</span></div>';
    });

    document.getElementById("single-top-cited").innerHTML = barHtml + citedHtml;
  }
})();
