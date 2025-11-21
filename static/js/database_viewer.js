// Database Viewer JavaScript
// Handles database table viewing, queries, and admin functions

let currentTable = '';
let currentTab = 'events';

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadDatabaseInfo();
    loadTable('events');
    setupExampleQueries();

    // Add event listener for event selection (for admin tab)
    setTimeout(() => {
        const eventSelect = document.getElementById('event-to-delete');
        if (eventSelect) {
            eventSelect.addEventListener('change', function() {
                const deleteBtn = document.getElementById('delete-event-btn');
                
                if (this.value) {
                    deleteBtn.disabled = false;
                    deleteBtn.style.backgroundColor = '#f44336';
                    deleteBtn.style.cursor = 'pointer';
                    
                    // Show event details
                    const eventText = this.selectedOptions[0].textContent;
                    document.getElementById('event-info').innerHTML = `<strong>${eventText}</strong>`;
                    document.getElementById('event-details').style.display = 'block';
                    document.getElementById('delete-status').textContent = '';
                } else {
                    deleteBtn.disabled = true;
                    deleteBtn.style.backgroundColor = '#666';
                    deleteBtn.style.cursor = 'not-allowed';
                    document.getElementById('event-details').style.display = 'none';
                }
            });
        }
    }, 1000);

    // Add event listener for JSON file selection
    setTimeout(() => {
        const jsonSelect = document.getElementById('json-to-delete');
        if (jsonSelect) {
            jsonSelect.addEventListener('change', function() {
                const deleteBtn = document.getElementById('delete-json-btn');
                
                if (this.value) {
                    deleteBtn.disabled = false;
                    deleteBtn.style.backgroundColor = '#f44336';
                    deleteBtn.style.cursor = 'pointer';
                    
                    // Show JSON file details
                    const fileText = this.selectedOptions[0].textContent;
                    document.getElementById('json-info').innerHTML = `<strong>${fileText}</strong>`;
                    document.getElementById('json-details').style.display = 'block';
                    document.getElementById('delete-json-status').textContent = '';
                } else {
                    deleteBtn.disabled = true;
                    deleteBtn.style.backgroundColor = '#666';
                    deleteBtn.style.cursor = 'not-allowed';
                    document.getElementById('json-details').style.display = 'none';
                }
            });
        }
    }, 1000);
});

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.classList.add('active');
    currentTab = tabName;

    // Load data for tab if not already loaded
    if (tabName === 'events' && !document.getElementById('events-table').innerHTML.includes('table')) {
        loadTable('events');
    } else if (tabName === 'notifications' && !document.getElementById('notifications-table').innerHTML.includes('table')) {
        loadTable('event_notifications');
    } else if (tabName === 'logs' && !document.getElementById('logs-table').innerHTML.includes('table')) {
        loadTable('logs');
    } else if (tabName === 'winners' && !document.getElementById('winners-table').innerHTML.includes('table')) {
        loadTable('event_winners');
    }
}

function loadDatabaseInfo() {
    fetch('/api/database/info')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('db-info').innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
                return;
            }

            let html = '<div class="db-info-panel">';
            
            // Tables section
            html += '<div class="db-info-section">';
            html += '<h3>Tables</h3>';
            if (data.tables) {
                html += '<ul style="list-style: disc; margin-left: 20px;">';
                data.tables.forEach(table => {
                    const count = data.row_counts ? data.row_counts[table] || 0 : 0;
                    html += `<li>${table}: <span class="badge">${count} rows</span></li>`;
                });
                html += '</ul>';
            }
            html += '</div>';
            
            // Stats section
            html += '<div class="db-info-section">';
            html += '<h3>Database Stats</h3>';
            html += `<p><strong>Size:</strong> ${data.size_mb || 'Unknown'} MB</p>`;
            html += `<p><strong>File Size:</strong> ${data.size_bytes || 'Unknown'} bytes</p>`;
            html += '</div>';
            
            html += '</div>';

            document.getElementById('db-info').innerHTML = html;
        })
        .catch(error => {
            document.getElementById('db-info').innerHTML = `<div class="alert alert-danger">Failed to load database info: ${error}</div>`;
        });
}

function loadTable(tableName) {
    currentTable = tableName;
    const targetDiv = tableName === 'event_notifications' ? 'notifications-table' : `${tableName.replace('event_', '')}-table`;

    // Get limit for logs
    let limit = 50;
    if (tableName === 'logs') {
        limit = document.getElementById('logs-limit')?.value || 50;
    }

    document.getElementById(targetDiv).innerHTML = '<div class="loading">Loading data...</div>';

    // Use enhanced endpoint for notifications and winners
    const endpoint = (tableName === 'event_notifications' || tableName === 'event_winners') 
        ? `/api/database/enhanced-table/${tableName}?limit=${limit}`
        : `/api/database/table/${tableName}?limit=${limit}`;

    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById(targetDiv).innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
                return;
            }

            if (!data.rows || data.rows.length === 0) {
                document.getElementById(targetDiv).innerHTML = '<div class="alert alert-info">No data found in this table.</div>';
                return;
            }

            // Build table HTML
            let html = '<div class="table-responsive"><table>';
            
            // Add headers
            html += '<thead><tr>';
            data.columns.forEach(col => {
                html += `<th>${col}</th>`;
            });
            html += '</tr></thead>';
            
            // Add rows
            html += '<tbody>';
            data.rows.forEach(row => {
                html += '<tr>';
                data.columns.forEach(col => {
                    let value = row[col];

                    // Format timestamps
                    if (col.includes('time') || col === 'timestamp' || col === 'sent_at' || col === 'rewarded_at') {
                        if (value) {
                            const date = new Date(value);
                            value = `<small>${date.toLocaleString()}</small>`;
                        }
                    }

                    // Truncate long text
                    if (typeof value === 'string' && value.length > 100) {
                        value = value.substring(0, 100) + '...';
                    }

                    // Handle null/undefined
                    if (value === null || value === undefined) {
                        value = '<span style="color: #666;">null</span>';
                    }

                    html += `<td>${value}</td>`;
                });
                html += '</tr>';
            });
            html += '</tbody></table></div>';

            // Add pagination info
            html += `<div class="pagination-info">Showing ${data.rows.length} of ${data.total} total rows</div>`;

            document.getElementById(targetDiv).innerHTML = html;
        })
        .catch(error => {
            document.getElementById(targetDiv).innerHTML = `<div class="alert alert-danger">Failed to load table: ${error}</div>`;
        });
}

function executeQuery() {
    const query = document.getElementById('query-input').value.trim();
    if (!query) {
        alert('Please enter a SQL query');
        return;
    }

    document.getElementById('query-results').innerHTML = '<div class="loading">Executing query...</div>';

    fetch('/api/database/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('query-results').innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
            return;
        }

        if (!data.results || data.results.length === 0) {
            document.getElementById('query-results').innerHTML = '<div class="alert alert-info">Query executed successfully, but returned no results.</div>';
            return;
        }

        // Build results table
        let html = `<div class="alert alert-success">Query executed successfully. Found ${data.count} results.</div>`;
        html += '<div class="table-responsive"><table>';
        
        // Get column headers from first row
        const firstRow = data.results[0];
        html += '<thead><tr>';
        
        if (Array.isArray(firstRow)) {
            for (let i = 0; i < firstRow.length; i++) {
                html += `<th>Column ${i + 1}</th>`;
            }
        } else {
            Object.keys(firstRow).forEach(key => {
                html += `<th>${key}</th>`;
            });
        }
        html += '</tr></thead>';
        
        // Add rows
        html += '<tbody>';
        data.results.forEach(row => {
            html += '<tr>';
            if (Array.isArray(row)) {
                row.forEach(cell => {
                    let value = cell;
                    if (value === null || value === undefined) {
                        value = '<span style="color: #666;">null</span>';
                    }
                    html += `<td>${value}</td>`;
                });
            } else {
                Object.values(row).forEach(cell => {
                    let value = cell;
                    if (value === null || value === undefined) {
                        value = '<span style="color: #666;">null</span>';
                    }
                    html += `<td>${value}</td>`;
                });
            }
            html += '</tr>';
        });
        html += '</tbody></table></div>';

        document.getElementById('query-results').innerHTML = html;
    })
    .catch(error => {
        document.getElementById('query-results').innerHTML = `<div class="alert alert-danger">Failed to execute query: ${error}</div>`;
    });
}

function clearQuery() {
    document.getElementById('query-input').value = '';
    document.getElementById('query-results').innerHTML = '';
}

function setupExampleQueries() {
    const exampleQueries = [
        "SELECT * FROM events ORDER BY start_time DESC LIMIT 10",
        "SELECT name, start_time, event_over FROM events WHERE event_over = 1",
        "SELECT COUNT(*) as total_events FROM events",
        "SELECT log_level, COUNT(*) as count FROM logs GROUP BY log_level",
        "SELECT e.name, w.player_name, w.final_score FROM events e JOIN event_winners w ON e.id = w.event_id",
        "SELECT notification_type, COUNT(*) as sent_count FROM event_notifications GROUP BY notification_type"
    ];

    const container = document.getElementById('example-buttons');
    exampleQueries.forEach((query, index) => {
        const button = document.createElement('button');
        button.className = 'example-button';
        button.textContent = query.split(' ').slice(0, 4).join(' ') + '...';
        button.onclick = () => {
            document.getElementById('query-input').value = query;
        };
        container.appendChild(button);
    });
}

// Admin functions
function unlockAdmin() {
    const password = document.getElementById('admin-password').value;
    
    fetch('/api/database/admin-unlock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('admin-password-section').style.display = 'none';
            document.getElementById('admin-functions').style.display = 'block';
            refreshEventsList();
            refreshJsonFilesList();
        } else {
            alert('Invalid password');
            document.getElementById('admin-password').value = '';
        }
    })
    .catch(error => {
        alert('Error validating password');
    });
}

function clearLogs() {
    if (!confirm('Are you sure you want to delete ALL log entries? This cannot be undone.')) {
        return;
    }

    document.getElementById('logs-status').textContent = 'Clearing logs...';
    
    fetch('/api/database/admin-clear-logs', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('logs-status').textContent = `✅ Cleared ${data.deleted_count} log entries`;
                // Refresh logs tab if it's currently loaded
                if (currentTable === 'logs') {
                    loadTable('logs');
                }
            } else {
                document.getElementById('logs-status').textContent = `❌ Error: ${data.error}`;
            }
        })
        .catch(error => {
            document.getElementById('logs-status').textContent = `❌ Error: ${error}`;
        });
}

function refreshEventsList() {
    const select = document.getElementById('event-to-delete');
    select.innerHTML = '<option value="">Loading events...</option>';
    
    fetch('/api/database/admin-events-list')
        .then(response => response.json())
        .then(data => {
            select.innerHTML = '<option value="">Select an event to delete...</option>';
            
            data.events.forEach(event => {
                const option = document.createElement('option');
                option.value = event.id;
                option.textContent = `${event.name} (${event.unique_event_name}) - ${event.start_time}`;
                select.appendChild(option);
            });
        })
        .catch(error => {
            select.innerHTML = '<option value="">Error loading events</option>';
        });
}

function deleteEvent() {
    const eventId = document.getElementById('event-to-delete').value;
    if (!eventId) return;

    const eventName = document.getElementById('event-to-delete').selectedOptions[0].textContent;
    
    if (!confirm(`Are you ABSOLUTELY sure you want to permanently delete this event and ALL related data?\n\n${eventName}\n\nThis will delete:\n- Event record\n- All notifications\n- All winners\n- Cannot be undone!`)) {
        return;
    }

    document.getElementById('delete-status').textContent = 'Deleting...';
    document.getElementById('delete-event-btn').disabled = true;
    
    fetch('/api/database/admin-delete-event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('delete-status').textContent = `✅ Event deleted successfully`;
            refreshEventsList();
            document.getElementById('event-details').style.display = 'none';
            
            // Refresh any loaded tables
            if (['events', 'event_notifications', 'event_winners'].includes(currentTable)) {
                loadTable(currentTable);
            }
        } else {
            document.getElementById('delete-status').textContent = `❌ Error: ${data.error}`;
            document.getElementById('delete-event-btn').disabled = false;
        }
    })
    .catch(error => {
        document.getElementById('delete-status').textContent = `❌ Error: ${error}`;
        document.getElementById('delete-event-btn').disabled = false;
    });
}

function refreshJsonFilesList() {
    const select = document.getElementById('json-to-delete');
    select.innerHTML = '<option value="">Loading JSON files...</option>';
    
    fetch('/api/database/admin-json-files')
        .then(response => response.json())
        .then(data => {
            select.innerHTML = '<option value="">Select a JSON template to delete...</option>';
            
            data.files.forEach(file => {
                const option = document.createElement('option');
                option.value = file.filename;
                option.textContent = `${file.filename} - ${file.event_name} (${file.size_bytes} bytes, modified: ${file.modified})`;
                select.appendChild(option);
            });
        })
        .catch(error => {
            select.innerHTML = '<option value="">Error loading JSON files</option>';
        });
}

function deleteJsonFile() {
    const filename = document.getElementById('json-to-delete').value;
    if (!filename) return;

    const fileText = document.getElementById('json-to-delete').selectedOptions[0].textContent;
    
    if (!confirm(`Are you ABSOLUTELY sure you want to permanently delete this JSON template?\n\n${fileText}\n\nThis will:\n- Delete the template file\n- Prevent creating new events of this type\n- NOT affect existing scheduled events\n- Cannot be undone!`)) {
        return;
    }

    document.getElementById('delete-json-status').textContent = 'Deleting...';
    document.getElementById('delete-json-btn').disabled = true;
    
    fetch('/api/database/admin-delete-json', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: filename })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('delete-json-status').textContent = `✅ JSON template deleted successfully`;
            refreshJsonFilesList();
            document.getElementById('json-details').style.display = 'none';
        } else {
            document.getElementById('delete-json-status').textContent = `❌ Error: ${data.error}`;
            document.getElementById('delete-json-btn').disabled = false;
        }
    })
    .catch(error => {
        document.getElementById('delete-json-status').textContent = `❌ Error: ${error}`;
        document.getElementById('delete-json-btn').disabled = false;
    });
}