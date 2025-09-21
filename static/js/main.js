// --- Calendar ---
async function refreshCalendar() {
    const res = await fetch("/api/calendar");
    const data = await res.json();
    const tbody = document.querySelector("#calendar-table tbody");
    tbody.innerHTML = "";
    data.forEach(event => {
        const tr = document.createElement("tr");
        tr.className = event.status;
        tr.innerHTML = `
            <td>${event.name}</td>
            <td>${new Date(event.start).toLocaleString()}</td>
            <td>${new Date(event.end).toLocaleString()}</td>
            <td>${event.status}</td>
        `;
        tbody.appendChild(tr);
    });
}

// --- Event JSON Files ---
async function refreshEventFiles() {
    const res = await fetch("/api/event_files");
    const files = await res.json();
    const tbody = document.querySelector("#event-json-table tbody");
    tbody.innerHTML = "";
    files.forEach(file => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td class="json-file" onclick="loadEventJson('${file}')">${file}</td>`;
        tbody.appendChild(tr);
    });
    // Clear event JSON content area when refreshing list
    document.getElementById("event-json-content").textContent = "";
}

async function loadEventJson(filename) {
    const res = await fetch(`/api/event_json_content/${filename}`);
    const content = await res.text();
    const pre = document.getElementById("event-json-content");
    pre.textContent = content;

    // Ensure JSON table row stays expanded
    const jsonTable = document.getElementById("event-json-table");
    jsonTable.style.display = "table";
}

// --- Logs ---
async function refreshLogs() {
    const res = await fetch("/api/logs");
    const files = await res.json();
    const tbody = document.querySelector("#logs-table tbody");
    tbody.innerHTML = "";
    files.forEach(file => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td class="log-file" onclick="loadLog('${file}')">${file}</td>`;
        tbody.appendChild(tr);
    });
    // Clear log content area when refreshing list
    document.getElementById("log-content").textContent = "";
}

async function loadLog(filename) {
    const res = await fetch(`/api/log_content/${filename}`);
    const content = await res.text();
    document.getElementById("log-content").textContent = content;

    // Ensure log table row stays expanded
    const logsTable = document.getElementById("logs-table");
    logsTable.style.display = "table";
}

// --- Initial load ---
document.addEventListener("DOMContentLoaded", () => {
    refreshCalendar();
    refreshEventFiles();
    refreshLogs();
});
