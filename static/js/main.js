// --- Calendar (now from database) ---
async function refreshCalendar() {
    try {
        const res = await fetch("/api/calendar");
        const data = await res.json();
        const tbody = document.querySelector("#calendar-table tbody");
        tbody.innerHTML = "";
        
        data.forEach(event => {
            const tr = document.createElement("tr");
            tr.className = event.status;
            
            // Format dates for display
            const startDate = new Date(event.start.replace('Z', '+00:00')).toLocaleString();
            const endDate = new Date(event.end.replace('Z', '+00:00')).toLocaleString();
            
            tr.innerHTML = `
                <td>${event.name}</td>
                <td>${startDate}</td>
                <td>${endDate}</td>
                <td>${event.status}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error("Error refreshing calendar:", error);
        const tbody = document.querySelector("#calendar-table tbody");
        tbody.innerHTML = '<tr><td colspan="4">Error loading calendar data</td></tr>';
    }
}

// --- Event JSON Files (unchanged) ---
async function refreshEventFiles() {
    try {
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
        const contentElement = document.getElementById("event-json-content");
        if (contentElement) {
            contentElement.textContent = "";
        }
    } catch (error) {
        console.error("Error refreshing event files:", error);
        const tbody = document.querySelector("#event-json-table tbody");
        tbody.innerHTML = '<tr><td>Error loading event files</td></tr>';
    }
}

async function loadEventJson(filename) {
    try {
        const res = await fetch(`/api/event_json_content/${filename}`);
        const content = await res.text();
        const pre = document.getElementById("event-json-content");
        if (pre) {
            pre.textContent = content;
        }

        // Ensure JSON table row stays expanded
        const jsonTable = document.getElementById("event-json-table");
        if (jsonTable) {
            jsonTable.style.display = "table";
        }
    } catch (error) {
        console.error("Error loading event JSON:", error);
        const pre = document.getElementById("event-json-content");
        if (pre) {
            pre.textContent = "Error loading event JSON file";
        }
    }
}

// --- Logs (now from database) ---
async function refreshLogs() {
    try {
        const res = await fetch("/api/logs");
        const logs = await res.json();
        const tbody = document.querySelector("#logs-table tbody");
        tbody.innerHTML = "";
        
        // Create a virtual "file" for database logs
        const tr = document.createElement("tr");
        tr.innerHTML = `<td class="log-file" onclick="loadDatabaseLogs()">Database Logs (Recent)</td>`;
        tbody.appendChild(tr);
        
        // Clear log content area when refreshing
        const contentElement = document.getElementById("log-content");
        if (contentElement) {
            contentElement.textContent = "";
        }
    } catch (error) {
        console.error("Error refreshing logs:", error);
        const tbody = document.querySelector("#logs-table tbody");
        tbody.innerHTML = '<tr><td>Error loading logs</td></tr>';
    }
}

async function loadDatabaseLogs() {
    try {
        const res = await fetch("/api/logs");
        const logs = await res.json();
        
        // Format logs as text
        let logText = "";
        logs.forEach(log => {
            const timestamp = new Date(log.timestamp.replace('Z', '+00:00')).toLocaleString();
            logText += `${timestamp}: [${log.log_level}] ${log.message}\n`;
        });
        
        const contentElement = document.getElementById("log-content");
        if (contentElement) {
            contentElement.textContent = logText || "No logs found";
        }

        // Ensure log table stays expanded
        const logsTable = document.getElementById("logs-table");
        if (logsTable) {
            logsTable.style.display = "table";
        }
    } catch (error) {
        console.error("Error loading database logs:", error);
        const contentElement = document.getElementById("log-content");
        if (contentElement) {
            contentElement.textContent = "Error loading logs from database";
        }
    }
}

// --- Legacy log file loading (for backward compatibility) ---
async function loadLog(filename) {
    try {
        const res = await fetch(`/api/log_content/${filename}`);
        const content = await res.text();
        const contentElement = document.getElementById("log-content");
        if (contentElement) {
            contentElement.textContent = content;
        }

        // Ensure log table row stays expanded
        const logsTable = document.getElementById("logs-table");
        if (logsTable) {
            logsTable.style.display = "table";
        }
    } catch (error) {
        console.error("Error loading log file:", error);
        const contentElement = document.getElementById("log-content");
        if (contentElement) {
            contentElement.textContent = "Error loading log file";
        }
    }
}

// --- Initial load ---
document.addEventListener("DOMContentLoaded", () => {
    // Load all data on page load
    refreshCalendar();
    refreshEventFiles();
    refreshLogs();
    
    // Auto-refresh calendar every 30 seconds to show status updates
    setInterval(refreshCalendar, 30000);
});