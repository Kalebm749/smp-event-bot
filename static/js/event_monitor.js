// Event Monitor JavaScript
// Handles event handler status monitoring and health checks

async function refreshStatus() {
    try {
        const res = await fetch("/api/event_handler_status");
        const data = await res.json();
        const statusCard = document.getElementById("handler-status-card");
        const statusDiv = document.getElementById("status");
        const statusDescription = document.getElementById("status-description");
        const statusIcon = document.getElementById("handler-icon");
        
        // Update status text and styling
        statusDiv.textContent = data.status;
        
        if (data.status === "Running") {
            statusCard.className = "event-handler-status-card running";
            statusDiv.className = "handler-status-label running";
            statusDescription.textContent = "Actively processing events and monitoring schedules";
            statusIcon.textContent = "⚙️";
        } else {
            statusCard.className = "event-handler-status-card stopped";
            statusDiv.className = "handler-status-label stopped";
            statusDescription.textContent = "Event handler is not running. Events will not be processed.";
            statusIcon.textContent = "⏸️";
        }
    } catch (err) {
        console.error("Error fetching status:", err);
        const statusCard = document.getElementById("handler-status-card");
        const statusDiv = document.getElementById("status");
        const statusDescription = document.getElementById("status-description");
        
        statusCard.className = "event-handler-status-card stopped";
        statusDiv.textContent = "Error";
        statusDiv.className = "handler-status-label stopped";
        statusDescription.textContent = "Unable to determine status";
    }
}

async function startEventHandler() {
    await fetch("/api/event_handler/start", { method: "POST" });
    refreshStatus();
}

async function stopEventHandler() {
    await fetch("/api/event_handler/stop", { method: "POST" });
    refreshStatus();
}

async function checkMinecraftHealth() {
    updateHealthCard('minecraft', 'checking', 'Checking...', {});
    
    try {
        const res = await fetch("/api/health/minecraft");
        const data = await res.json();
        
        if (data.healthy) {
            updateHealthCard('minecraft', 'healthy', 'Online', {
                'Last Check': new Date().toLocaleTimeString()
            });
        } else {
            updateHealthCard('minecraft', 'unhealthy', 'Offline', {
                'Last Check': new Date().toLocaleTimeString(),
                'Error': data.error || 'Connection failed'
            });
        }
    } catch (error) {
        updateHealthCard('minecraft', 'unhealthy', 'Error', {
            'Last Check': new Date().toLocaleTimeString(),
            'Error': error.message
        });
    }
    
    updateOverallHealth();
}

async function checkRconHealth() {
    updateHealthCard('rcon', 'checking', 'Checking...', {});
    
    try {
        const startTime = Date.now();
        const res = await fetch("/api/health/rcon");
        const responseTime = Date.now() - startTime;
        const data = await res.json();
        
        if (data.healthy) {
            updateHealthCard('rcon', 'healthy', 'Connected', {
                'Response Time': responseTime + 'ms',
                'Last Check': new Date().toLocaleTimeString()
            });
        } else {
            updateHealthCard('rcon', 'unhealthy', 'Failed', {
                'Response Time': responseTime + 'ms',
                'Last Check': new Date().toLocaleTimeString(),
                'Error': data.error || 'Connection failed'
            });
        }
    } catch (error) {
        updateHealthCard('rcon', 'unhealthy', 'Error', {
            'Last Check': new Date().toLocaleTimeString(),
            'Error': error.message
        });
    }
    
    updateOverallHealth();
}

function updateHealthCard(type, status, statusText, details) {
    const card = document.getElementById(`${type}-card`);
    const indicator = document.getElementById(`${type}-indicator`);
    const statusElement = document.getElementById(`${type}-status`);
    
    // Update card status
    card.className = `health-card ${status}`;
    indicator.className = `health-status-indicator ${status}`;
    statusElement.textContent = statusText;
    
    // Update details
    Object.entries(details).forEach(([label, value]) => {
        const element = document.getElementById(`${type}-${label.toLowerCase().replace(/\s+/g, '-')}`);
        if (element) {
            element.textContent = value;
        }
    });
}

function updateOverallHealth() {
    const minecraftCard = document.getElementById('minecraft-card');
    const rconCard = document.getElementById('rcon-card');
    const overallHealth = document.getElementById('overall-health');
    const overallStatus = document.getElementById('overall-status');
    
    const minecraftHealthy = minecraftCard.classList.contains('healthy');
    const rconHealthy = rconCard.classList.contains('healthy');
    
    if (minecraftHealthy && rconHealthy) {
        overallHealth.className = 'overall-health healthy';
        overallStatus.textContent = 'All Systems Operational';
    } else {
        overallHealth.className = 'overall-health unhealthy';
        const issues = [];
        if (!minecraftHealthy) issues.push('Minecraft Server');
        if (!rconHealthy) issues.push('RCON');
        overallStatus.textContent = `Issues Detected: ${issues.join(', ')}`;
    }
}

// Initialize event listeners and auto-refresh
document.addEventListener("DOMContentLoaded", () => {
    // Set up button event listeners
    document.getElementById("start-btn").addEventListener("click", startEventHandler);
    document.getElementById("stop-btn").addEventListener("click", stopEventHandler);

    // Initial load
    refreshStatus();
    checkMinecraftHealth();
    checkRconHealth();

    // Auto-refresh status every 30 seconds
    setInterval(refreshStatus, 30000);
    
    // Auto-refresh health checks every 60 seconds
    setInterval(() => {
        checkMinecraftHealth();
        checkRconHealth();
    }, 60000);
});