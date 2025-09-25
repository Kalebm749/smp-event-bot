// Event Monitor JavaScript
// Handles event handler status monitoring and health checks

let serverIP = 'Unknown';
let playersOnline = 0;

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
            serverIP = data.server_ip || 'Unknown';
        } else {
            updateHealthCard('minecraft', 'unhealthy', 'Offline', {
                'Last Check': new Date().toLocaleTimeString(),
                'Error': data.error || 'Connection failed'
            });
            serverIP = data.server_ip || 'Unknown';
        }
    } catch (error) {
        updateHealthCard('minecraft', 'unhealthy', 'Error', {
            'Last Check': new Date().toLocaleTimeString(),
            'Error': error.message
        });
    }
    
    updateServerInfo();
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
            playersOnline = data.player_count || 0;
        } else {
            updateHealthCard('rcon', 'unhealthy', 'Failed', {
                'Response Time': responseTime + 'ms',
                'Last Check': new Date().toLocaleTimeString(),
                'Error': data.error || 'Connection failed'
            });
            playersOnline = 0;
        }
    } catch (error) {
        updateHealthCard('rcon', 'unhealthy', 'Error', {
            'Last Check': new Date().toLocaleTimeString(),
            'Error': error.message
        });
        playersOnline = 0;
    }
    
    updateServerInfo();
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

function updateServerInfo() {
    const serverInfoCard = document.getElementById('server-info-card');
    const serverIndicator = document.getElementById('server-indicator');
    
    // Update server IP
    document.getElementById('server-ip').textContent = serverIP;
    
    // Update players online
    document.getElementById('players-online').textContent = playersOnline;
    
    // Update last update time
    document.getElementById('server-last-update').textContent = new Date().toLocaleTimeString();
    
    // Update card status based on health
    const minecraftCard = document.getElementById('minecraft-card');
    const rconCard = document.getElementById('rcon-card');
    
    if (minecraftCard.classList.contains('healthy') && rconCard.classList.contains('healthy')) {
        serverInfoCard.className = 'health-card healthy';
        serverIndicator.className = 'health-status-indicator healthy';
    } else if (minecraftCard.classList.contains('unhealthy') || rconCard.classList.contains('unhealthy')) {
        serverInfoCard.className = 'health-card unhealthy';
        serverIndicator.className = 'health-status-indicator unhealthy';
    } else {
        serverInfoCard.className = 'health-card checking';
        serverIndicator.className = 'health-status-indicator checking';
    }
}

function updateOverallHealth() {
    const minecraftCard = document.getElementById('minecraft-card');
    const rconCard = document.getElementById('rcon-card');
    const overallCard = document.getElementById('overall-status-card');
    const overallIndicator = document.getElementById('overall-indicator');
    
    const minecraftHealthy = minecraftCard.classList.contains('healthy');
    const rconHealthy = rconCard.classList.contains('healthy');
    
    // Update individual status texts
    document.getElementById('minecraft-status-text').textContent = minecraftHealthy ? '✅ Online' : '❌ Offline';
    document.getElementById('rcon-status-text').textContent = rconHealthy ? '✅ Connected' : '❌ Failed';
    
    // Update overall status
    if (minecraftHealthy && rconHealthy) {
        overallCard.className = 'health-card healthy';
        overallIndicator.className = 'health-status-indicator healthy';
        document.getElementById('overall-status-text').textContent = '✅ All Systems Operational';
    } else {
        overallCard.className = 'health-card unhealthy';
        overallIndicator.className = 'health-status-indicator unhealthy';
        const issues = [];
        if (!minecraftHealthy) issues.push('Minecraft');
        if (!rconHealthy) issues.push('RCON');
        document.getElementById('overall-status-text').textContent = '❌ Issues: ' + issues.join(', ');
    }
}

async function refreshServerInfo() {
    await checkMinecraftHealth();
    await checkRconHealth();
}

async function refreshSystemStatus() {
    await checkMinecraftHealth();
    await checkRconHealth();
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
