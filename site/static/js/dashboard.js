/**
 * Research Dashboard — D3.js Knowledge Graph Visualization
 *
 * Renders an interactive force-directed graph of extracted research data.
 * Nodes = claims, concepts, statistics, etc. Edges = shared topic tags.
 * Source nodes act as anchors. Bubble size reflects cross-source frequency.
 */

/* global d3 */

var dashboardData = null;

function initDashboard(dataUrl) {
  fetch(dataUrl)
    .then(function (r) { return r.json(); })
    .then(function (data) {
      dashboardData = data;
      renderStats(data);
      renderFilters(data);
      renderLegend(data);
      renderGraph(data);
      // Default: show findings (canonical cross-source claims)
      selectFilter("finding");
    })
    .catch(function (err) {
      console.error("Failed to load dashboard data:", err);
      document.getElementById("graph-container").innerHTML =
        '<p style="padding:2rem;opacity:0.5;">Could not load dashboard data.</p>';
    });
}

// ── Stats bar ──

function renderStats(data) {
  var s = data.stats;
  animateCounter("stat-findings", s.findings || 0);
  animateCounter("stat-claims", s.claims);
  animateCounter("stat-statistics", s.statistics);
  animateCounter("stat-concepts", s.concepts);
  animateCounter("stat-frameworks", s.frameworks);
  animateCounter("stat-sources", s.sources);

  var topicEl = document.getElementById("dashboard-topic");
  if (topicEl && data.topic) {
    topicEl.textContent =
      "Topic: " + data.topic + " \u00B7 " + data.sources.length + " sources \u00B7 " + data.stats.edges + " connections";
  }
}

function animateCounter(elId, target) {
  var el = document.getElementById(elId);
  if (!el) return;
  var duration = 600;
  var start = performance.now();
  function tick(now) {
    var t = Math.min((now - start) / duration, 1);
    var ease = 1 - Math.pow(1 - t, 3);
    el.textContent = Math.round(ease * target);
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// ── Top items summary ──

function renderTopItems(type) {
  var container = document.getElementById("top-items-summary");
  container.innerHTML = "";

  if (!dashboardData) return;

  // For findings, show canonical claims (aligned across sources)
  if (type === "finding" && dashboardData.canonical_claims && dashboardData.canonical_claims.length > 0) {
    container.style.display = "block";

    var heading = document.createElement("h3");
    heading.className = "top-items-heading";
    heading.textContent = "Key claims across " + dashboardData.stats.sources + " sources (" + dashboardData.canonical_claims.length + " consensus themes)";
    container.appendChild(heading);

    // Show top canonical claims sorted by source_count
    var sorted = dashboardData.canonical_claims.slice().sort(function (a, b) {
      return b.source_count - a.source_count;
    });
    var top = sorted.slice(0, 7);

    var list = document.createElement("ol");
    list.className = "top-items-list";
    top.forEach(function (cc) {
      var li = document.createElement("li");

      var text = document.createElement("span");
      text.className = "top-item-text";
      text.textContent = cc.statement;
      li.appendChild(text);

      var meta = document.createElement("span");
      meta.className = "top-item-meta";
      meta.textContent = " \u2014 " + cc.source_count + " sources";
      if (cc.extensions && cc.extensions.length > 0) {
        meta.textContent += " + " + cc.extensions.length + " extensions";
      }
      li.appendChild(meta);

      list.appendChild(li);
    });
    container.appendChild(list);

    // Show contradictions if any
    if (dashboardData.contradictions && dashboardData.contradictions.length > 0) {
      var contraHeading = document.createElement("h3");
      contraHeading.className = "top-items-heading";
      contraHeading.style.marginTop = "1rem";
      contraHeading.textContent = "Key contradictions (" + dashboardData.contradictions.length + ")";
      container.appendChild(contraHeading);

      var contraList = document.createElement("ul");
      contraList.className = "top-items-list";
      contraList.style.listStyle = "none";
      contraList.style.paddingLeft = "0";
      dashboardData.contradictions.forEach(function (ct) {
        var li = document.createElement("li");
        li.style.marginBottom = "0.5rem";

        var tension = document.createElement("span");
        tension.className = "top-item-text";
        tension.textContent = ct.tension;
        li.appendChild(tension);

        var sides = document.createElement("div");
        sides.className = "top-item-meta";
        sides.style.marginTop = "0.15rem";
        var sideA = ct.side_a || {};
        var sideB = ct.side_b || {};
        sides.textContent = "A: \"" + (sideA.statement || "") + "\" vs B: \"" + (sideB.statement || "") + "\"";
        li.appendChild(sides);

        contraList.appendChild(li);
      });
      container.appendChild(contraList);
    }

    return;
  }

  // For other types, show top items by cross_source_freq
  var items = dashboardData.nodes
    .filter(function (n) { return n.type === type; })
    .sort(function (a, b) { return b.cross_source_freq - a.cross_source_freq; })
    .slice(0, 5);

  if (items.length === 0) {
    container.style.display = "none";
    return;
  }

  container.style.display = "block";

  var heading = document.createElement("h3");
  heading.className = "top-items-heading";
  heading.textContent = "Top " + items.length + " " + type + "s (by cross-source frequency)";
  container.appendChild(heading);

  var list = document.createElement("ol");
  list.className = "top-items-list";
  items.forEach(function (item) {
    var li = document.createElement("li");
    var source = dashboardData.sources.find(function (s) { return s.id === item.source; });
    var sourceLabel = source ? source.short_author : item.source;

    var text = document.createElement("span");
    text.className = "top-item-text";
    text.textContent = item.detail || item.label;
    li.appendChild(text);

    var meta = document.createElement("span");
    meta.className = "top-item-meta";
    meta.textContent = " \u2014 " + sourceLabel;
    if (item.metadata && item.metadata.strength) {
      meta.textContent += " (" + item.metadata.strength + ")";
    }
    if (item.cross_source_freq > 1) {
      meta.textContent += " \u00B7 " + item.cross_source_freq + " sources";
    }
    li.appendChild(meta);

    list.appendChild(li);
  });
  container.appendChild(list);
}

function hideTopItems() {
  var container = document.getElementById("top-items-summary");
  container.innerHTML = "";
  container.style.display = "none";
}

// ── Filter controls ──

var activeFilters = new Set();
var allFilterTypes = ["finding", "claim", "statistic", "concept", "recommendation", "reference", "framework", "source"];
var filterButtons = {};

function renderFilters(data) {
  var container = document.getElementById("filter-controls");

  // "All" button
  var allBtn = document.createElement("button");
  allBtn.className = "filter-btn filter-btn-all";
  allBtn.textContent = "All";
  allBtn.addEventListener("click", function () {
    selectAll();
  });
  container.appendChild(allBtn);
  filterButtons["all"] = allBtn;

  // Type buttons (no "source" — hidden by default, only visible in "All" mode)
  var visibleTypes = ["finding", "claim", "statistic", "concept", "recommendation", "reference", "framework"];
  visibleTypes.forEach(function (type) {
    var btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.dataset.type = type;
    var dot = document.createElement("span");
    dot.className = "dot";
    dot.style.backgroundColor = data.type_colors[type] || "#888";
    btn.appendChild(dot);
    btn.appendChild(document.createTextNode(type));
    btn.addEventListener("click", function (event) {
      handleFilterClick(type, event);
    });
    container.appendChild(btn);
    filterButtons[type] = btn;
  });
}

function handleFilterClick(type, event) {
  // Ctrl/Meta/Alt + click = toggle (multi-select)
  if (event.ctrlKey || event.metaKey || event.altKey) {
    toggleFilterMulti(type);
  } else {
    // Plain click = radio behavior (select only this type)
    selectFilter(type);
  }
}

function selectFilter(type) {
  // Select only this type (radio behavior)
  activeFilters.clear();
  activeFilters.add(type);

  // Update button states
  Object.keys(filterButtons).forEach(function (key) {
    if (key === "all") {
      filterButtons[key].classList.remove("active");
    } else {
      filterButtons[key].classList.toggle("active", key === type);
      filterButtons[key].classList.toggle("inactive", key !== type);
    }
  });

  renderTopItems(type);
  applyFilters();
}

function toggleFilterMulti(type) {
  // If coming from "all" mode or single mode, start fresh multi-select
  if (activeFilters.has(type)) {
    activeFilters.delete(type);
    // If nothing left, select all
    if (activeFilters.size === 0 || (activeFilters.size === 1 && activeFilters.has("source"))) {
      selectAll();
      return;
    }
  } else {
    // Remove "source" if it was part of "all" selection
    activeFilters.add(type);
  }

  // Ensure source is excluded unless explicitly in "all" mode
  activeFilters.delete("source");

  // Update button states
  filterButtons["all"].classList.remove("active");
  allFilterTypes.forEach(function (t) {
    if (filterButtons[t]) {
      filterButtons[t].classList.toggle("active", activeFilters.has(t));
      filterButtons[t].classList.toggle("inactive", !activeFilters.has(t));
    }
  });

  // Show top items for the single selected type, or hide if multiple
  if (activeFilters.size === 1) {
    renderTopItems(activeFilters.values().next().value);
  } else {
    hideTopItems();
  }

  applyFilters();
}

function selectAll() {
  activeFilters.clear();
  allFilterTypes.forEach(function (t) { activeFilters.add(t); });

  // Update button states
  filterButtons["all"].classList.add("active");
  allFilterTypes.forEach(function (t) {
    if (filterButtons[t]) {
      filterButtons[t].classList.remove("active");
      filterButtons[t].classList.remove("inactive");
    }
  });

  hideTopItems();
  applyFilters();
}

function applyFilters() {
  d3.selectAll(".node-group").each(function (d) {
    var visible = activeFilters.has(d.type);
    d3.select(this).style("display", visible ? null : "none");
    d.hidden = !visible;
  });
  d3.selectAll(".edge-line").each(function (d) {
    var srcVisible = !d.source.hidden;
    var tgtVisible = !d.target.hidden;
    d3.select(this).style("display", srcVisible && tgtVisible ? null : "none");
  });
}

// ── Legend ──

function renderLegend(data) {
  var legend = document.getElementById("legend");
  var items = [
    { label: "Finding", color: data.type_colors.finding },
    { label: "Claim", color: data.type_colors.claim },
    { label: "Statistic", color: data.type_colors.statistic },
    { label: "Concept", color: data.type_colors.concept },
    { label: "Recommendation", color: data.type_colors.recommendation },
    { label: "Reference", color: data.type_colors.reference },
    { label: "Framework", color: data.type_colors.framework },
    { label: "Source", color: data.type_colors.source },
  ];
  items.forEach(function (item) {
    var el = document.createElement("span");
    el.className = "legend-item";
    el.innerHTML =
      '<span class="legend-dot" style="background:' + item.color + '"></span>' + item.label;
    legend.appendChild(el);
  });

  var sizeNote = document.createElement("span");
  sizeNote.className = "legend-item";
  sizeNote.style.opacity = "0.5";
  sizeNote.textContent = "\u00B7 Node size = cross-source frequency \u00B7 Ctrl/Cmd+click to multi-select filters";
  legend.appendChild(sizeNote);
}

// ── Knowledge Graph ──

var simulation;

function renderGraph(data) {
  var container = document.getElementById("graph-container");
  var svg = d3.select("#graph-svg");
  var tooltip = document.getElementById("graph-tooltip");
  var isDark = document.documentElement.classList.contains("dark");

  var width = container.clientWidth;
  var height = Math.max(500, Math.min(700, window.innerHeight * 0.6));
  svg.attr("viewBox", [0, 0, width, height]).attr("width", width).attr("height", height);

  var nodes = data.nodes.map(function (n) { return Object.assign({}, n); });
  var nodeById = new Map(nodes.map(function (n) { return [n.id, n]; }));

  var edges = data.edges
    .filter(function (e) { return nodeById.has(e.source) && nodeById.has(e.target); })
    .map(function (e) { return Object.assign({}, e); });

  var maxFreq = d3.max(nodes, function (d) { return d.cross_source_freq; }) || 1;
  var radiusScale = function (d) {
    if (d.type === "source") return 16;
    if (d.type === "finding") return 8 + (d.cross_source_freq / maxFreq) * 10;
    return 3 + (d.cross_source_freq / maxFreq) * 7;
  };

  simulation = d3
    .forceSimulation(nodes)
    .force(
      "link",
      d3
        .forceLink(edges)
        .id(function (d) { return d.id; })
        .distance(function (d) { return d.weight > 1 ? 60 : 100; })
        .strength(function (d) { return d.shared_tags && d.shared_tags.length > 0 ? 0.3 : 0.05; })
    )
    .force("charge", d3.forceManyBody().strength(-30))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force(
      "collision",
      d3.forceCollide().radius(function (d) { return radiusScale(d) + 2; })
    )
    .force("x", d3.forceX(width / 2).strength(0.03))
    .force("y", d3.forceY(height / 2).strength(0.03));

  var g = svg.append("g");

  var zoom = d3
    .zoom()
    .scaleExtent([0.3, 5])
    .on("zoom", function (event) {
      g.attr("transform", event.transform);
    });
  svg.call(zoom);

  var edgeGroup = g.append("g").attr("class", "edges");
  var edgeLines = edgeGroup
    .selectAll("line")
    .data(edges)
    .join("line")
    .attr("class", "edge-line")
    .attr("stroke", function (d) {
      return d.shared_tags && d.shared_tags.length > 0
        ? isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)"
        : isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.03)";
    })
    .attr("stroke-width", function (d) { return d.weight > 1 ? 1.5 : 0.5; });

  var nodeGroup = g.append("g").attr("class", "nodes");
  var nodeGroups = nodeGroup
    .selectAll("g")
    .data(nodes)
    .join("g")
    .attr("class", "node-group")
    .style("cursor", "pointer")
    .call(
      d3
        .drag()
        .on("start", dragStarted)
        .on("drag", dragged)
        .on("end", dragEnded)
    );

  nodeGroups
    .append("circle")
    .attr("r", function (d) { return radiusScale(d); })
    .attr("fill", function (d) { return data.type_colors[d.type] || "#888"; })
    .attr("fill-opacity", function (d) { return d.type === "source" || d.type === "finding" ? 0.9 : 0.7; })
    .attr("stroke", function (d) {
      if (d.type === "source") return isDark ? "#fff" : "#000";
      if (d.type === "finding") return isDark ? "#fbbf24" : "#d97706";
      return "none";
    })
    .attr("stroke-width", function (d) { return d.type === "source" ? 1.5 : d.type === "finding" ? 2 : 0; });

  nodeGroups
    .filter(function (d) { return d.type === "source"; })
    .append("text")
    .text(function (d) { return d.label; })
    .attr("dy", function (d) { return radiusScale(d) + 14; })
    .attr("text-anchor", "middle")
    .attr("font-size", "11px")
    .attr("font-weight", "600")
    .attr("fill", isDark ? "#ccc" : "#333")
    .attr("pointer-events", "none");

  // Labels for finding nodes (truncated)
  nodeGroups
    .filter(function (d) { return d.type === "finding"; })
    .append("text")
    .text(function (d) {
      var t = d.label;
      return t.length > 50 ? t.substring(0, 47) + "..." : t;
    })
    .attr("dy", function (d) { return radiusScale(d) + 12; })
    .attr("text-anchor", "middle")
    .attr("font-size", "9px")
    .attr("font-weight", "500")
    .attr("fill", isDark ? "#fbbf24" : "#92400e")
    .attr("pointer-events", "none");

  nodeGroups
    .on("mouseover", function (event, d) {
      tooltip.style.display = "block";
      tooltip.textContent = d.label;

      edgeLines
        .attr("stroke-opacity", function (e) {
          return e.source.id === d.id || e.target.id === d.id ? 1 : 0.1;
        })
        .attr("stroke-width", function (e) {
          return e.source.id === d.id || e.target.id === d.id ? 2 : 0.5;
        })
        .attr("stroke", function (e) {
          return e.source.id === d.id || e.target.id === d.id
            ? data.type_colors[d.type] || "#888"
            : isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.03)";
        });

      nodeGroups.select("circle").attr("fill-opacity", function (n) {
        if (n.id === d.id) return 1;
        var connected = edges.some(function (e) {
          return (e.source.id === d.id && e.target.id === n.id) ||
                 (e.target.id === d.id && e.source.id === n.id);
        });
        return connected ? 0.8 : 0.15;
      });
    })
    .on("mousemove", function (event) {
      var rect = container.getBoundingClientRect();
      tooltip.style.left = event.clientX - rect.left + 12 + "px";
      tooltip.style.top = event.clientY - rect.top - 8 + "px";
    })
    .on("mouseout", function () {
      tooltip.style.display = "none";
      edgeLines
        .attr("stroke-opacity", 1)
        .attr("stroke-width", function (d) { return d.weight > 1 ? 1.5 : 0.5; })
        .attr("stroke", function (d) {
          return d.shared_tags && d.shared_tags.length > 0
            ? isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)"
            : isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.03)";
        });
      nodeGroups.select("circle").attr("fill-opacity", function (d) {
        return d.type === "source" ? 0.9 : 0.7;
      });
    })
    .on("click", function (event, d) {
      event.stopPropagation();
      showDetail(d, data);
    });

  svg.on("click", function () {
    hideDetail();
  });

  simulation.on("tick", function () {
    edgeLines
      .attr("x1", function (d) { return d.source.x; })
      .attr("y1", function (d) { return d.source.y; })
      .attr("x2", function (d) { return d.target.x; })
      .attr("y2", function (d) { return d.target.y; });

    nodeGroups.attr("transform", function (d) { return "translate(" + d.x + "," + d.y + ")"; });
  });

  function dragStarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }
  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }
  function dragEnded(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  var resizeTimeout;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function () {
      var newWidth = container.clientWidth;
      svg.attr("viewBox", [0, 0, newWidth, height]).attr("width", newWidth);
      simulation.force("center", d3.forceCenter(newWidth / 2, height / 2));
      simulation.force("x", d3.forceX(newWidth / 2).strength(0.03));
      simulation.alpha(0.3).restart();
    }, 200);
  });
}

// ── Detail panel ──

function showDetail(d, data) {
  var panel = document.getElementById("detail-panel");
  var typeEl = document.getElementById("detail-type");
  var labelEl = document.getElementById("detail-label");
  var textEl = document.getElementById("detail-text");
  var metaEl = document.getElementById("detail-meta");

  typeEl.textContent = d.type;
  typeEl.style.backgroundColor = data.type_colors[d.type] || "#888";
  labelEl.textContent = d.label;
  textEl.textContent = d.detail || "";

  metaEl.innerHTML = "";
  var source = data.sources.find(function (s) { return s.id === d.source; });
  if (source) {
    addMeta(metaEl, "Source", source.short_author + " (" + source.date + ")");
  }

  if (d.metadata) {
    var m = d.metadata;
    if (m.claim_type) addMeta(metaEl, "Type", m.claim_type);
    if (m.strength) addMeta(metaEl, "Strength", m.strength);
    if (m.value !== undefined && m.value !== null) addMeta(metaEl, "Value", m.value + " " + (m.unit || ""));
    if (m.year) addMeta(metaEl, "Year", m.year);
    if (m.original_source) addMeta(metaEl, "Original source", m.original_source);
    if (m.target_audience) addMeta(metaEl, "Audience", m.target_audience);
    if (m.framework_type) addMeta(metaEl, "Framework type", m.framework_type);
    if (m.author) addMeta(metaEl, "Author", m.author);
    if (m.for_claim) addMeta(metaEl, "For claim", m.for_claim);
    if (m.ref_type) addMeta(metaEl, "Reference type", m.ref_type);
    if (m.related_terms && m.related_terms.length)
      addMeta(metaEl, "Related", m.related_terms.join(", "));
    if (m.components && m.components.length)
      addMeta(metaEl, "Components", m.components.join("; "));
  }

  if (d.tags && d.tags.length) {
    addMeta(metaEl, "Tags", d.tags.join(", "));
  }

  addMeta(metaEl, "Cross-source freq", d.cross_source_freq + " source(s)");

  panel.classList.add("visible");
}

function hideDetail() {
  document.getElementById("detail-panel").classList.remove("visible");
}

function addMeta(container, label, value) {
  var dt = document.createElement("dt");
  dt.textContent = label + ":";
  var dd = document.createElement("dd");
  dd.textContent = value;
  container.appendChild(dt);
  container.appendChild(dd);
}

document.addEventListener("DOMContentLoaded", function () {
  var closeBtn = document.getElementById("detail-close");
  if (closeBtn) {
    closeBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      hideDetail();
    });
  }
});
