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
}

async function loadEventJson(filename) {
    const res = await fetch(`/api/event_json_content/${filename}`);
    const content = await res.text();
    document.getElementById("event-json-content").textContent = content;
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
}

async function loadLog(filename) {
    const res = await fetch(`/api/log_content/${filename}`);
    const content = await res.text();
    document.getElementById("log-content").textContent = content;
}

// --- Initial load ---
document.addEventListener("DOMContentLoaded", () => {
    refreshCalendar();
    refreshEventFiles();
    refreshLogs();
});

