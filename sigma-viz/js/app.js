/**
 * Revista SITIO — Sigma.js Citation Network Explorer
 *
 * Loads pre-built sigma_graph.json and renders with Sigma.js v2.
 * Features: color toggle, issue filter, search, detail panel, hover highlight.
 */

(function () {
  "use strict";

  function esc(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  var renderer = null;
  var graph = null;
  var graphData = null;
  var colorMode = "community";
  var hoveredNode = null;
  var selectedNode = null;
  var hoveredNeighbors = null;
  var activeIssues = new Set();
  var minDegree = 1;
  var nodeLabels = [];

  fetch("data/sigma_graph.json")
    .then(function (res) { return res.json(); })
    .then(function (data) {
      graphData = data;
      initGraph(data);
      initUI(data);
      updateStats();
    })
    .catch(function (err) {
      console.error("Failed to load graph data:", err);
      document.getElementById("sigma-container").textContent =
        "Error al cargar los datos del grafo. Asegurate de que sigma_graph.json existe en data/.";
    });

  function initGraph(data) {
    graph = new graphology.Graph();

    data.nodes.forEach(function (n) {
      graph.addNode(n.key, Object.assign({}, n.attributes, {
        color: n.attributes["color_" + colorMode],
      }));
    });

    data.edges.forEach(function (e) {
      if (graph.hasNode(e.source) && graph.hasNode(e.target)) {
        if (!graph.hasEdge(e.source, e.target)) {
          graph.addEdge(e.source, e.target, e.attributes || {});
        }
      }
    });

    renderer = new Sigma(graph, document.getElementById("sigma-container"), {
      minCameraRatio: 0.1,
      maxCameraRatio: 10,
      renderLabels: true,
      labelRenderedSizeThreshold: 8,
      labelFont: "sans-serif",
      labelSize: 12,
      labelColor: { color: "#ccc" },
      defaultEdgeColor: "#334455",
      defaultEdgeType: "arrow",
      edgeReducer: edgeReducer,
      nodeReducer: nodeReducer,
    });

    renderer.on("enterNode", function (e) {
      hoveredNode = e.node;
      hoveredNeighbors = new Set(graph.neighbors(e.node));
      renderer.refresh();
    });

    renderer.on("leaveNode", function () {
      hoveredNode = null;
      hoveredNeighbors = null;
      renderer.refresh();
    });

    renderer.on("clickNode", function (e) {
      selectedNode = e.node;
      showDetailPanel(e.node);
      renderer.refresh();
    });

    renderer.on("clickStage", function () {
      selectedNode = null;
      hideDetailPanel();
      renderer.refresh();
    });

    nodeLabels = [];
    graph.forEachNode(function (key, attrs) {
      nodeLabels.push({ key: key, label: attrs.label || key });
    });
    nodeLabels.sort(function (a, b) { return a.label.localeCompare(b.label); });
  }

  function nodeReducer(node, data) {
    var res = Object.assign({}, data);

    if (isNodeHidden(node)) {
      res.hidden = true;
      return res;
    }

    if (hoveredNode && hoveredNode !== node && hoveredNeighbors && !hoveredNeighbors.has(node)) {
      res.color = "#222233";
      res.label = "";
    }

    if (selectedNode === node) {
      res.highlighted = true;
      res.zIndex = 1;
    }

    return res;
  }

  function edgeReducer(edge, data) {
    var res = Object.assign({}, data);
    var source = graph.source(edge);
    var target = graph.target(edge);

    if (isNodeHidden(source) || isNodeHidden(target)) {
      res.hidden = true;
      return res;
    }

    if (hoveredNode) {
      if (source !== hoveredNode && target !== hoveredNode) {
        res.hidden = true;
      } else {
        res.color = "#5577aa";
        res.size = 2;
      }
    }

    return res;
  }

  function isNodeHidden(node) {
    var attrs = graph.getNodeAttributes(node);
    if (activeIssues.size > 0) {
      var nodeIssues = attrs.issues || [];
      var visible = false;
      for (var i = 0; i < nodeIssues.length; i++) {
        if (activeIssues.has(nodeIssues[i])) { visible = true; break; }
      }
      if (!visible) return true;
    }
    var totalDeg = (attrs.in_degree || 0) + (attrs.out_degree || 0);
    if (attrs.node_type !== "author" && totalDeg < minDegree) return true;
    return false;
  }

  function setColorMode(mode) {
    colorMode = mode;
    graph.forEachNode(function (key, attrs) {
      graph.setNodeAttribute(key, "color", attrs["color_" + mode]);
    });
    document.querySelectorAll(".color-btn").forEach(function (btn) {
      btn.classList.toggle("active", btn.dataset.mode === mode);
    });
  }

  function updateIssueFilter() {
    activeIssues.clear();
    var checkboxes = document.querySelectorAll(".issue-cb");
    var allChecked = true;
    checkboxes.forEach(function (cb) {
      if (cb.checked) {
        activeIssues.add(cb.value);
      } else {
        allChecked = false;
      }
    });
    if (allChecked) activeIssues.clear();
    renderer.refresh();
    updateStats();
  }

  function updateDegreeFilter(val) {
    minDegree = parseInt(val, 10);
    document.getElementById("degree-value").textContent = val;
    renderer.refresh();
    updateStats();
  }

  function handleSearch(query) {
    var suggestions = document.getElementById("search-suggestions");
    if (!query || query.length < 2) {
      suggestions.style.display = "none";
      return;
    }
    var q = query.toLowerCase();
    var matches = nodeLabels.filter(function (n) {
      return n.label.toLowerCase().indexOf(q) !== -1;
    }).slice(0, 10);

    if (matches.length === 0) {
      suggestions.style.display = "none";
      return;
    }

    suggestions.innerHTML = "";
    matches.forEach(function (m) {
      var div = document.createElement("div");
      div.className = "suggestion";
      div.textContent = m.label;
      div.addEventListener("click", function () {
        selectSearchResult(m.key);
        suggestions.style.display = "none";
        document.getElementById("search-input").value = m.label;
      });
      suggestions.appendChild(div);
    });
    suggestions.style.display = "block";
  }

  function selectSearchResult(nodeKey) {
    selectedNode = nodeKey;
    showDetailPanel(nodeKey);

    var attrs = graph.getNodeAttributes(nodeKey);
    var camera = renderer.getCamera();
    camera.animate({ x: attrs.x, y: attrs.y, ratio: 0.3 }, { duration: 500 });
    renderer.refresh();
  }

  function showDetailPanel(nodeKey) {
    var attrs = graph.getNodeAttributes(nodeKey);
    var panel = document.getElementById("detail-panel");

    document.getElementById("detail-name").textContent = attrs.label || nodeKey;

    var dates = "";
    if (attrs.birth_year) dates = "Nacido: " + attrs.birth_year;
    document.getElementById("detail-dates").innerHTML =
      dates ? "<strong>Fechas:</strong> " + dates : "";

    document.getElementById("detail-country").innerHTML =
      "<strong>País:</strong> " + esc(attrs.country || "Desconocido");

    document.getElementById("detail-period").innerHTML =
      "<strong>Período:</strong> " + esc(attrs.period || "Desconocido");

    document.getElementById("detail-community").innerHTML =
      "<strong>Comunidad:</strong> " + (attrs.community !== undefined ? attrs.community : "—");

    document.getElementById("detail-type").innerHTML =
      "<strong>Rol:</strong> " + (attrs.node_type === "author" ? "Colaborador/a de SITIO" : "Figura citada");

    document.getElementById("detail-degree").innerHTML =
      "<strong>Citado por:</strong> " + (attrs.in_degree || 0) +
      " &nbsp; <strong>Cita:</strong> " + (attrs.out_degree || 0);

    var issueText = (attrs.issues || []).join(", ") || "—";
    document.getElementById("detail-issues").innerHTML =
      "<strong>Presente en:</strong> " + issueText;

    var wdEl = document.getElementById("detail-wikidata");
    if (attrs.wikidata) {
      wdEl.innerHTML = '<a href="' + attrs.wikidata + '" target="_blank" rel="noopener">Wikidata &rarr;</a>';
    } else {
      wdEl.innerHTML = "";
    }

    var neighbors = graph.neighbors(nodeKey);
    var list = document.getElementById("neighbor-list");
    list.innerHTML = "";
    neighbors.sort(function (a, b) {
      var la = graph.getNodeAttribute(a, "label") || a;
      var lb = graph.getNodeAttribute(b, "label") || b;
      return la.localeCompare(lb);
    });
    neighbors.forEach(function (nkey) {
      var li = document.createElement("li");
      li.textContent = graph.getNodeAttribute(nkey, "label") || nkey;
      li.addEventListener("click", function () {
        selectSearchResult(nkey);
      });
      list.appendChild(li);
    });

    panel.classList.remove("hidden");
  }

  function hideDetailPanel() {
    document.getElementById("detail-panel").classList.add("hidden");
  }

  function updateStats() {
    if (!graph) return;
    var visible = 0;
    graph.forEachNode(function (key) {
      if (!isNodeHidden(key)) visible++;
    });
    document.getElementById("visible-count").textContent =
      visible + " / " + graph.order + " nodos visibles";
  }

  function initUI(data) {
    document.querySelectorAll(".color-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        setColorMode(btn.dataset.mode);
      });
    });

    document.querySelectorAll(".issue-cb").forEach(function (cb) {
      cb.addEventListener("change", updateIssueFilter);
    });

    var slider = document.getElementById("degree-slider");
    slider.addEventListener("input", function () {
      updateDegreeFilter(slider.value);
    });

    var searchInput = document.getElementById("search-input");
    searchInput.addEventListener("input", function () {
      handleSearch(searchInput.value);
    });
    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        searchInput.value = "";
        document.getElementById("search-suggestions").style.display = "none";
      }
    });

    document.addEventListener("click", function (e) {
      if (!document.getElementById("search-container").contains(e.target)) {
        document.getElementById("search-suggestions").style.display = "none";
      }
    });

    document.getElementById("close-panel").addEventListener("click", function () {
      selectedNode = null;
      hideDetailPanel();
      renderer.refresh();
    });

    activeIssues.clear();
  }
})();
