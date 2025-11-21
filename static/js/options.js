// Options/Settings Page JavaScript

// Load settings on page load
document.addEventListener('DOMContentLoaded', function() {
    loadSettings();
});

async function loadSettings() {
    try {
        const response = await fetch('/api/settings/get');
        const settings = await response.json();
        
        if (settings.error) {
            showStatus('connection-status', 'error', 'Failed to load settings: ' + settings.error);
            return;
        }
        
        // Populate form fields
        document.getElementById('rcon-host').value = settings.rcon_host || '';
        document.getElementById('rcon-port').value = settings.rcon_port || '25575';
        document.getElementById('discord-token').value = settings.discord_token || '';
        document.getElementById('event-channel-id').value = settings.event_channel_id || '';
        
    } catch (error) {
        showStatus('connection-status', 'error', 'Error loading settings: ' + error.message);
    }
}

async function testConnection() {
    const host = document.getElementById('rcon-host').value;
    const port = document.getElementById('rcon-port').value;
    
    if (!host) {
        showStatus('connection-status', 'error', 'Please enter a server host/IP address');
        return;
    }
    
    const testBtn = document.getElementById('test-btn');
    testBtn.disabled = true;
    testBtn.textContent = 'Testing...';
    
    showStatus('connection-status', 'info', 'Testing connection...');
    
    try {
        const response = await fetch('/api/settings/test-connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                rcon_host: host,
                rcon_port: port
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('connection-status', 'success', 
                '✅ Connection successful! Server responded: ' + data.result);
        } else {
            showStatus('connection-status', 'error', 
                '❌ Connection failed: ' + data.error);
        }
        
    } catch (error) {
        showStatus('connection-status', 'error', 
            '❌ Connection test failed: ' + error.message);
    } finally {
        testBtn.disabled = false;
        testBtn.textContent = 'Test Connection';
    }
}

async function saveSettings() {
    const settings = {
        rcon_host: document.getElementById('rcon-host').value,
        rcon_port: document.getElementById('rcon-port').value,
        discord_token: document.getElementById('discord-token').value,
        event_channel_id: document.getElementById('event-channel-id').value
    };
    
    const saveBtn = document.getElementById('save-btn');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    
    showStatus('connection-status', 'info', 'Saving settings...');
    
    try {
        const response = await fetch('/api/settings/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('connection-status', 'success', 
                '✅ Settings saved successfully! ' + data.message);
            showStatus('discord-status', 'success', 
                '✅ Discord settings saved!');
        } else {
            showStatus('connection-status', 'error', 
                '❌ Failed to save settings: ' + data.error);
        }
        
    } catch (error) {
        showStatus('connection-status', 'error', 
            '❌ Error saving settings: ' + error.message);
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save Settings';
    }
}

function showStatus(elementId, type, message) {
    const element = document.getElementById(elementId);
    
    let className = 'alert alert-info';
    if (type === 'success') {
        className = 'alert alert-success';
    } else if (type === 'error') {
        className = 'alert alert-danger';
    }
    
    element.innerHTML = `<div class="${className}">${message}</div>`;
    
    // Auto-clear after 10 seconds for non-error messages
    if (type !== 'error') {
        setTimeout(() => {
            element.innerHTML = '';
        }, 10000);
    }
}