// Dashboard JavaScript
// Handles dashboard-specific functionality including event handler status and system health

let eventHandlerStatus = 'unknown';

// Check event handler status
async function checkEventHandlerStatus() {
    try {
        const res = await fetch("/api/event_handler_status");
        const data = await res.json();
        eventHandlerStatus = data.status;
        updateEventHandlerWarning(data.status);
    } catch (err) {
        console.error("Error fetching event handler status:", err);
        updateEventHandlerWarning('Error');
    }
}

function updateEventHandlerWarning(status) {
    const warning = document.getElementById('handler-warning');
    const statusText = document.getElementById('handler-status-text');
    const startBtn = document.getElementById('start-handler-btn');

    if (status === 'Running') {
        warning.className = 'event-handler-warning running';
        statusText.textContent = 'Event handler is running and processing events automatically.';
        startBtn.style.display = 'none';
        warning.querySelector('.warning-icon').textContent = '✅';
    } else if (status === 'Not Running') {
        warning.className = 'event-handler-warning';
        statusText.textContent = 'Event handler is not running. Events will not be processed automatically.';
        startBtn.style.display = 'block';
        warning.querySelector('.warning-icon').textContent = '⚠️';
    } else {
        warning.className = 'event-handler-warning';
        statusText.textContent = 'Unable to determine event handler status.';
        startBtn.style.display = 'block';
        warning.querySelector('.warning-icon').textContent = '❓';
    }
}

async function startEventHandler() {
    try {
        const res = await fetch("/api/event_handler/start", { method: "POST" });
        const data = await res.json();
        
        if (data.success) {
            setTimeout(checkEventHandlerStatus, 2000); // Check status after 2 seconds
        } else {
            alert('Failed to start event handler');
        }
    } catch (err) {
        console.error("Error starting event handler:", err);
        alert('Error starting event handler');
    }
}

// System status checks
async function checkSystemStatus() {
    // Minecraft status
    try {
        const res = await fetch("/api/health/minecraft");
        const data = await res.json();
        updateStatusCard('minecraft', data.healthy ? 'healthy' : 'unhealthy', 
            data.healthy ? 'Online' : 'Offline');
    } catch (err) {
        updateStatusCard('minecraft', 'unhealthy', 'Error');
    }

    // RCON status
    try {
        const res = await fetch("/api/health/rcon");
        const data = await res.json();
        updateStatusCard('rcon', data.healthy ? 'healthy' : 'unhealthy', 
            data.healthy ? 'Connected' : 'Failed');
    } catch (err) {
        updateStatusCard('rcon', 'unhealthy', 'Error');
    }
}

function updateStatusCard(type, status, value) {
    const card = document.getElementById(`${type}-status-card`);
    const statusElement = document.getElementById(`${type}-status`);
    
    card.className = `status-card ${status}`;
    statusElement.textContent = value;
}

// Enhanced calendar refresh for dashboard (shows only recent 8 events)
async function refreshCalendar() {
    try {
        const res = await fetch("/api/calendar");
        const data = await res.json();
        const tbody = document.querySelector("#calendar-table tbody");
        tbody.innerHTML = "";
        
        // Show only the most recent 8 events
        const recentEvents = data.slice(0, 8);
        
        recentEvents.forEach(event => {
            const tr = document.createElement("tr");
            tr.className = event.status;
            
            const startDate = new Date(event.start.replace('Z', '+00:00')).toLocaleString();
            
            tr.innerHTML = `
                <td>${event.name}</td>
                <td>${startDate}</td>
                <td>${event.status}</td>
            `;
            tbody.appendChild(tr);
        });

    } catch (error) {
        console.error("Error refreshing calendar:", error);
        const tbody = document.querySelector("#calendar-table tbody");
        tbody.innerHTML = '<tr><td colspan="3">Error loading calendar data</td></tr>';
    }
}

// Enhanced event files refresh for dashboard
async function refreshEventFiles() {
    try {
        const res = await fetch("/api/event_files");
        const files = await res.json();
        const tbody = document.querySelector("#event-json-table tbody");
        tbody.innerHTML = "";
        
        files.forEach(file => {
            const tr = document.createElement("tr");
            const displayName = file.replace('.json', '').replace(/([A-Z])/g, ' $1').trim();
            tr.innerHTML = `<td class="json-file" onclick="loadEventJson('${file}')">${displayName}</td>`;
            tbody.appendChild(tr);
        });
        
        document.getElementById("event-json-content").style.display = "none";
    } catch (error) {
        console.error("Error refreshing event files:", error);
    }
}

async function loadEventJson(filename) {
    try {
        const res = await fetch(`/api/event_json_content/${filename}`);
        const content = await res.text();
        const pre = document.getElementById("event-json-content");
        if (pre) {
            pre.textContent = content;
            pre.style.display = "block";
        }
    } catch (error) {
        console.error("Error loading event JSON:", error);
    }
}

// Initialize dashboard
document.addEventListener("DOMContentLoaded", () => {
    checkEventHandlerStatus();
    checkSystemStatus();
    refreshCalendar();
    refreshEventFiles();
    
    // Auto-refresh every 30 seconds
    setInterval(() => {
        checkEventHandlerStatus();
        checkSystemStatus();
        refreshCalendar();
    }, 30000);
});