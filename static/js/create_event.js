// Create Event Form JavaScript
// Handles event scheduling form with timezone support and validation

// Auto-detect user's timezone and pre-select it
function initializeTimezone() {
    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const timezoneSelect = document.getElementById('timezone');
    const supportedTimezones = Array.from(timezoneSelect.options).map(opt => opt.value);
    
    if (supportedTimezones.includes(userTimezone)) {
        timezoneSelect.value = userTimezone;
    } else {
        // Default to US/Eastern if user's timezone isn't supported
        timezoneSelect.value = "US/Eastern";
    }
}

// Set minimum datetime to now
function setMinimumDateTime() {
    const now = new Date();
    const nowString = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    document.getElementById('start_datetime').min = nowString;
    document.getElementById('end_datetime').min = nowString;
}

// Auto-populate event name when type is selected
function setupEventTypeListener() {
    document.getElementById('event_json').addEventListener('change', function() {
        const selected = this.value.replace('.json', '');
        const spaced = selected.replace(/([A-Z])/g, ' $1').trim();
        document.getElementById('name').value = spaced;
        updatePreview();
    });
}

// Quick time setters
function setQuickTime(field, preset) {
    const input = document.getElementById(field + '_datetime');
    const now = new Date();
    let targetDate;

    switch(preset) {
        case 'now':
            targetDate = new Date(now.getTime() + 5 * 60000); // +5 minutes
            break;
        case '1hour':
            targetDate = new Date(now.getTime() + 60 * 60000);
            break;
        case 'tomorrow':
            targetDate = new Date(now);
            targetDate.setDate(targetDate.getDate() + 1);
            targetDate.setHours(9, 0, 0, 0);
            break;
        case 'weekend':
            targetDate = new Date(now);
            const daysUntilSaturday = (6 - targetDate.getDay()) % 7 || 7;
            targetDate.setDate(targetDate.getDate() + daysUntilSaturday);
            targetDate.setHours(10, 0, 0, 0);
            break;
    }

    const localString = new Date(targetDate.getTime() - targetDate.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    input.value = localString;
    
    if (field === 'start') {
        updateEndTimeMin();
    }
    updatePreview();
}

// Duration setters
function setDuration(hours) {
    const startInput = document.getElementById('start_datetime');
    const endInput = document.getElementById('end_datetime');
    
    if (!startInput.value) {
        showError('Please set a start time first');
        return;
    }

    const startDate = new Date(startInput.value);
    const endDate = new Date(startDate.getTime() + hours * 60 * 60000);
    const localString = new Date(endDate.getTime() - endDate.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    endInput.value = localString;
    updatePreview();
}

// Update end time minimum when start time changes
function updateEndTimeMin() {
    const startInput = document.getElementById('start_datetime');
    const endInput = document.getElementById('end_datetime');
    
    if (startInput.value) {
        endInput.min = startInput.value;
        
        // If end time is before start time, auto-adjust
        if (endInput.value && endInput.value <= startInput.value) {
            setDuration(1); // Default to 1 hour
        }
    }
}

// Update preview
function updatePreview() {
    const eventJson = document.getElementById('event_json').value;
    const name = document.getElementById('name').value;
    const startDatetime = document.getElementById('start_datetime').value;
    const endDatetime = document.getElementById('end_datetime').value;
    const timezone = document.getElementById('timezone').value;

    // Show preview if we have basic info
    if (eventJson && name && startDatetime && endDatetime && timezone) {
        document.getElementById('event-preview').style.display = 'block';
        
        // Format dates
        const startDate = new Date(startDatetime);
        const endDate = new Date(endDatetime);
        const duration = Math.round((endDate - startDate) / (1000 * 60 * 60 * 10)) / 10; // Hours with 1 decimal
        
        document.getElementById('preview-name').textContent = name;
        document.getElementById('preview-type').textContent = eventJson.replace('.json', '');
        document.getElementById('preview-start').textContent = startDate.toLocaleString();
        document.getElementById('preview-end').textContent = endDate.toLocaleString();
        document.getElementById('preview-duration').textContent = duration + ' hours';
        document.getElementById('preview-timezone').textContent = timezone || 'Not selected';

        // Update datetime previews
        document.getElementById('start-preview').textContent = 'Local: ' + startDate.toLocaleString();
        document.getElementById('end-preview').textContent = 'Local: ' + endDate.toLocaleString();

        // Enable submit button
        document.getElementById('submit-btn').disabled = false;
    } else {
        document.getElementById('event-preview').style.display = 'none';
        document.getElementById('submit-btn').disabled = true;
    }
}

// Show error message
function showError(message) {
    const container = document.getElementById('error-container');
    container.innerHTML = `<div class="error-message">${message}</div>`;
    setTimeout(() => {
        container.innerHTML = '';
    }, 5000);
}

// Form validation and submission
function setupFormSubmission() {
    document.getElementById('create-event-form').addEventListener('submit', function(e) {
        const startDatetime = document.getElementById('start_datetime').value;
        const endDatetime = document.getElementById('end_datetime').value;
        
        if (!startDatetime || !endDatetime) {
            e.preventDefault();
            showError('Please fill in both start and end times');
            return;
        }

        if (new Date(endDatetime) <= new Date(startDatetime)) {
            e.preventDefault();
            showError('End time must be after start time');
            return;
        }

        // Get timezone from the select dropdown
        const timezone = document.getElementById('timezone').value;
        
        if (!timezone) {
            e.preventDefault();
            showError('Please select a timezone');
            return;
        }
        
        // Create hidden timezone input for backend
        const timezoneInput = document.createElement('input');
        timezoneInput.type = 'hidden';
        timezoneInput.name = 'timezone';
        timezoneInput.value = timezone;
        this.appendChild(timezoneInput);

        // Convert datetime-local to the exact format the backend expects
        const startDate = new Date(startDatetime);
        const endDate = new Date(endDatetime);
        
        // Backend expects: "YYYY-MM-DD HH:MM AM/PM" format
        const startFormatted = startDate.getFullYear() + '-' + 
                             String(startDate.getMonth() + 1).padStart(2, '0') + '-' + 
                             String(startDate.getDate()).padStart(2, '0') + ' ' + 
                             startDate.toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit', hour12: true});
                             
        const endFormatted = endDate.getFullYear() + '-' + 
                           String(endDate.getMonth() + 1).padStart(2, '0') + '-' + 
                           String(endDate.getDate()).padStart(2, '0') + ' ' + 
                           endDate.toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit', hour12: true});

        // Create hidden inputs with the exact names the backend expects
        const startInput = document.createElement('input');
        startInput.type = 'hidden';
        startInput.name = 'start';
        startInput.value = startFormatted;
        this.appendChild(startInput);

        const endInput = document.createElement('input');
        endInput.type = 'hidden';
        endInput.name = 'end';
        endInput.value = endFormatted;
        this.appendChild(endInput);

        console.log('Sending to backend:', {
            timezone: timezone,
            start: startFormatted,
            end: endFormatted
        });
    });
}

// Event listeners for real-time updates
function setupEventListeners() {
    document.getElementById('start_datetime').addEventListener('change', updateEndTimeMin);
    document.getElementById('start_datetime').addEventListener('change', updatePreview);
    document.getElementById('end_datetime').addEventListener('change', updatePreview);
    document.getElementById('name').addEventListener('input', updatePreview);
    document.getElementById('description').addEventListener('input', updatePreview);
    document.getElementById('timezone').addEventListener('change', updatePreview);
}

// Initialize with current time + 1 hour
function initializeDefaultTimes() {
    setQuickTime('start', '1hour');
    setDuration(2); // Default 2 hour event
}

// Initialize everything on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeTimezone();
    setMinimumDateTime();
    setupEventTypeListener();
    setupFormSubmission();
    setupEventListeners();
    initializeDefaultTimes();
});