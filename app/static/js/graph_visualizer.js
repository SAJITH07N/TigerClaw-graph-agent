/**
 * Cytoscape.js Interactive Graph Visualizer for Agent Tiger.
 * Features: Force-directed topology, dynamic node/edge badges, entity inspector, and neighbor highlighting.
 */

let cy = null;

function initCytoscapeGraph(containerId = "cy") {
  const container = document.getElementById(containerId);
  if (!container) return;

  cy = cytoscape({
    container: container,
    boxSelectionEnabled: false,
    autounselectify: false,
    style: [
      {
        // Neo-Bauhaus: flat primary fills, no gradients, geometry encodes entity type.
        selector: 'node',
        style: {
          'background-color': '#3A3A42',
          'label': 'data(label)',
          'color': '#F5F5F2',
          'font-size': '9px',
          'font-weight': 500,
          'font-family': 'JetBrains Mono, monospace',
          'text-valign': 'bottom',
          'text-margin-y': 6,
          'text-wrap': 'ellipsis',
          'text-max-width': '90px',
          'width': 26,
          'height': 26,
          'border-width': 0,
          'transition-property': 'background-color, border-width, width, height, opacity',
          'transition-duration': '0.18s'
        }
      },
      {
        selector: 'node[type = "Transaction"]',
        style: { 'background-color': '#E63A27', 'shape': 'diamond', 'width': 36, 'height': 36 }
      },
      {
        selector: 'node[type = "Account"]',
        style: { 'background-color': '#2358E6', 'shape': 'rectangle', 'width': 28, 'height': 28 }
      },
      {
        selector: 'node[type = "Card"]',
        style: { 'background-color': '#8B5CF6', 'shape': 'ellipse', 'width': 26, 'height': 26 }
      },
      {
        selector: 'node[type = "Device"]',
        style: { 'background-color': '#F5C518', 'shape': 'hexagon', 'width': 30, 'height': 30 }
      },
      {
        selector: 'node[type = "Address"]',
        style: { 'background-color': '#18B26A', 'shape': 'triangle', 'width': 28, 'height': 28 }
      },
      {
        selector: 'node[type = "Identity"]',
        style: { 'background-color': '#F5F5F2', 'shape': 'ellipse', 'width': 24, 'height': 24 }
      },
      {
        selector: 'edge',
        style: {
          'width': 1,
          'line-color': '#3A3A42',
          'target-arrow-color': '#3A3A42',
          'target-arrow-shape': 'triangle',
          'arrow-scale': 0.7,
          'curve-style': 'straight',
          'font-size': '8px',
          'font-family': 'JetBrains Mono, monospace',
          'color': '#8A8A93',
          'label': 'data(label)',
          'text-rotation': 'autorotate',
          'text-margin-y': -7,
          'text-background-color': '#0A0A0B',
          'text-background-opacity': 0.85,
          'text-background-padding': 2
        }
      },
      {
        selector: ':selected',
        style: { 'border-width': 3, 'border-color': '#F5C518' }
      },
      {
        selector: '.highlighted',
        style: { 'border-width': 2, 'border-color': '#F5F5F2', 'opacity': 1.0 }
      },
      {
        selector: 'edge.highlighted',
        style: { 'line-color': '#F5C518', 'target-arrow-color': '#F5C518', 'width': 2, 'border-width': 0 }
      },
      {
        selector: '.faded',
        style: { 'opacity': 0.15 }
      }
    ],
    elements: [],
    layout: {
      name: 'cose',
      animate: true,
      animationDuration: 500,
      padding: 30
    }
  });

  // Node Selection / Inspection Interaction
  cy.on('tap', 'node', function(evt) {
    const node = evt.target;
    showNodeInspector(node);
    highlightNeighborhood(node);
  });

  // Canvas Tap to Reset Highlights
  cy.on('tap', function(evt) {
    if (evt.target === cy) {
      resetHighlights();
      hideNodeInspector();
    }
  });
}

function highlightNeighborhood(node) {
  if (!cy) return;
  cy.elements().removeClass('highlighted faded');
  const neighborhood = node.neighborhood().add(node);
  cy.elements().not(neighborhood).addClass('faded');
  neighborhood.addClass('highlighted');
}

function resetHighlights() {
  if (!cy) return;
  cy.elements().removeClass('highlighted faded');
}

function showNodeInspector(node) {
  const data = node.data();
  const attrs = data.attributes || {};
  let inspector = document.getElementById("node-inspector-overlay");

  if (!inspector) {
    const container = document.getElementById("cy");
    if (!container) return;
    inspector = document.createElement("div");
    inspector.id = "node-inspector-overlay";
    inspector.className = "absolute bottom-3 left-3 right-3 bau-panel edge-yellow p-3 text-xs z-10 flex items-start justify-between shadow-2xl animate-in";
    container.parentElement.style.position = "relative";
    container.parentElement.appendChild(inspector);
  }

  const type = data.type || "Entity";
  const id = data.id || data.label || "N/A";

  // Format attributes with Neo-Bauhaus styling
  let attrsHtml = "";
  if (type === "Device") {
    const isEmulator = data.is_emulator !== undefined ? data.is_emulator : attrs.is_emulator;
    const devType = data.device_type || attrs.device_type;
    const ip = data.ip_address || attrs.ip_address;
    attrsHtml = `
      <div class="flex items-center gap-3 text-mute mt-1">
        <span>Emulator: <strong class="${isEmulator ? 'text-bau-red' : 'text-bau-green'}">${isEmulator ? 'YES (High Risk)' : 'NO'}</strong></span>
        ${devType ? `<span>Type: <strong class="text-chalk">${devType}</strong></span>` : ''}
        ${ip ? `<span>IP: <code class="text-bau-yellow font-mono text-[10px]">${ip}</code></span>` : ''}
      </div>`;
  } else if (type === "Transaction") {
    const amt = data.amount !== undefined ? data.amount : (attrs.amount !== undefined ? attrs.amount : 0);
    const risk = data.risk_score !== undefined ? data.risk_score : attrs.risk_score;
    attrsHtml = `
      <div class="flex items-center gap-3 text-mute mt-1">
        <span>Amount: <strong class="text-bau-green font-mono">$${parseFloat(amt || 0).toLocaleString(undefined, {minimumFractionDigits: 2})}</strong></span>
        ${risk !== undefined ? `<span>Risk Score: <strong class="text-bau-red">${risk}</strong></span>` : ''}
      </div>`;
  } else if (type === "Account") {
    const status = data.status || attrs.status || 'ACTIVE';
    const risk = data.risk_score !== undefined ? data.risk_score : attrs.risk_score;
    attrsHtml = `
      <div class="flex items-center gap-3 text-mute mt-1">
        <span>Status: <strong class="text-bau-blue">${status}</strong></span>
        ${risk !== undefined ? `<span>Network Risk: <strong class="text-bau-yellow">${risk}</strong></span>` : ''}
      </div>`;
  } else if (type === "Card") {
    const issuer = data.issuer || attrs.issuer || 'Visa/Mastercard';
    const cardType = data.card_type || attrs.card_type;
    attrsHtml = `
      <div class="flex items-center gap-3 text-mute mt-1">
        <span>Issuer: <strong class="text-chalk">${issuer}</strong></span>
        ${cardType ? `<span>Category: <strong class="text-chalk">${cardType}</strong></span>` : ''}
      </div>`;
  } else if (type === "Address") {
    const zip = data.zip || attrs.addr1 || attrs.zip || '';
    const country = data.country || attrs.country || 'US';
    attrsHtml = `
      <div class="flex items-center gap-3 text-mute mt-1">
        <span>ZIP / Country: <strong class="text-chalk">${zip} ${country}</strong></span>
      </div>`;
  }

  inspector.innerHTML = `
    <div class="space-y-0.5 min-w-0 pr-3">
      <div class="flex items-center gap-2">
        <span class="px-1.5 py-0.5 rounded-sm text-[10px] font-bold font-mono uppercase bau-inset text-chalk border border-line-strong">${type}</span>
        <span class="font-mono text-xs font-bold text-chalk">${id}</span>
      </div>
      ${attrsHtml}
    </div>
    <button onclick="hideNodeInspector()" class="text-mute hover:text-chalk p-1" aria-label="Close inspector">
      <i class="fa-solid fa-xmark"></i>
    </button>
  `;
  inspector.style.display = "flex";
}

function hideNodeInspector() {
  const inspector = document.getElementById("node-inspector-overlay");
  if (inspector) inspector.style.display = "none";
}

function renderSubgraphData(elements) {
  if (!cy) initCytoscapeGraph();
  if (!cy) return;

  hideNodeInspector();
  cy.elements().remove();
  cy.add(elements);

  cy.layout({
    name: 'cose',
    animate: true,
    animationDuration: 400,
    randomize: false,
    fit: true,
    padding: 35,
    nodeRepulsion: 5000,
    idealEdgeLength: 65,
  }).run();
}

function fitGraphView() {
  if (cy) {
    cy.fit(null, 35);
  }
}
