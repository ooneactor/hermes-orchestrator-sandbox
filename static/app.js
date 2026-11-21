"use strict";

const rows = document.getElementById("nodes");
const message = document.getElementById("message");
const refresh = document.getElementById("refresh");
const statuses = new Set(["healthy", "warning", "critical"]);

function addCell(row, value, className) {
    const cell = document.createElement("td");
    cell.textContent = String(value);
    if (className) cell.classList.add(className);
    row.appendChild(cell);
}

function renderNodes(nodes) {
    const fragment = document.createDocumentFragment();
    for (const node of nodes) {
        const row = document.createElement("tr");
        const status = statuses.has(node.status) ? node.status : "unknown";
        addCell(row, node.name);
        addCell(row, status.toUpperCase(), status);
        addCell(row, `${node.cpu_percent}%`);
        addCell(row, `${node.memory_percent}%`);
        fragment.appendChild(row);
    }
    rows.replaceChildren(fragment);
}

async function refreshNodes() {
    refresh.disabled = true;
    message.textContent = "Loading...";
    try {
        const response = await fetch("/api/nodes", {cache: "no-store"});
        if (!response.ok) throw new Error("API request failed");
        const data = await response.json();
        if (!Array.isArray(data.nodes)) throw new Error("Invalid response");
        renderNodes(data.nodes);
        message.textContent = "Node data loaded.";
    } catch {
        rows.replaceChildren();
        message.textContent = "Unable to load node data.";
    } finally {
        refresh.disabled = false;
    }
}

refresh.addEventListener("click", refreshNodes);
refreshNodes();
