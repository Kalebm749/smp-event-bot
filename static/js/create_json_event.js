// Create JSON Event Form JavaScript
// Handles dynamic form building for event JSON creation

let already_agg = false;

function toggleAggregateFields() {
    const isAgg = document.querySelector('input[name="is_aggregate"]:checked').value === "true";
    document.getElementById("aggregate-setup-extra").style.display = isAgg ? "block" : "none";

    if (isAgg) {
        forceAggregate();
    } else {
        const container = document.getElementById("setup-commands-container");

        // Remove the aggregate dummy row
        const aggLine = container.querySelector('.inline-form[data-agg="true"]');
        if (aggLine) container.removeChild(aggLine);

        // Remove all extra setup commands
        container.querySelectorAll('.inline-form[data-extra-agg="true"]').forEach(el => el.remove());

        already_agg = false;
    }

    syncAggregateName();
}

function forceAggregate() {
    const container = document.getElementById("setup-commands-container");
    if (already_agg) return;
    already_agg = true;

    const div = document.createElement("div");
    div.className = "inline-form";
    div.dataset.agg = "true";

    div.innerHTML = `
        <div class="field">
            <label>Command</label>
            <input type="text" value="scoreboard objectives add" readonly>
        </div>
        <div class="field">
            <label>Aggregate Name</label>
            <input type="text" name="aggregate_obj_name" readonly>
        </div>
        <div class="field">
            <label>Type</label>
            <input type="text" value="dummy" readonly>
        </div>
    `;

    container.appendChild(div);

    // Immediately sync with the main input
    syncAggregateName();
}

function addSetupCommand() {
    const isAgg = document.querySelector('input[name="is_aggregate"]:checked').value === "true";
    if (!isAgg) return;

    const container = document.getElementById("setup-commands-container");
    const div = document.createElement("div");
    div.className = "inline-form";
    div.dataset.extraAgg = "true";

    div.innerHTML = `
        <div class="field">
            <label>Command</label>
            <input type="text" value="scoreboard objectives add" readonly>
        </div>
        <div class="field">
            <label>Custom Name</label>
            <input type="text" name="setup_obj_name[]" pattern="[a-zA-Z]+" required>
        </div>
        <div class="field">
            <label>Namespace</label>
            <input type="text" value="minecraft" readonly>
        </div>
        <div class="field">
            <label>Action</label>
            <select name="setup_action[]">
                <option value="custom">custom</option>
                <option value="mined">mined</option>
                <option value="broken">broken</option>
                <option value="crafted">crafted</option>
                <option value="used">used</option>
                <option value="picked_up">picked_up</option>
                <option value="dropped">dropped</option>
                <option value="killed">killed</option>
                <option value="killed_by">killed_by</option>
            </select>
        </div>
        <div class="field">
            <label>Namespace</label>
            <input type="text" value="minecraft" readonly>
        </div>
        <div class="field">
            <label>Item/Entity</label>
            <input type="text" name="setup_item[]" pattern="[a-z_]+" required>
        </div>
        <button type="button" onclick="removeSetupCommand(this)">Remove</button>
    `;

    const aggLine = container.querySelector('.inline-form[data-agg="true"]');
    if (aggLine) {
        container.insertBefore(div, aggLine);
    } else {
        container.appendChild(div);
    }
}

function removeSetupCommand(button) {
    const row = button.parentElement;
    row.remove();
}

// Sync function: keeps aggregate/custom names aligned with the overall input
function syncAggregateName() {
    const overallInput = document.querySelector('input[name="aggregate_objective"]');
    if (!overallInput) return;

    const isAgg = document.querySelector('input[name="is_aggregate"]:checked').value === "true";
    const newName = overallInput.value;

    if (isAgg) {
        const aggInput = document.querySelector('input[name="aggregate_obj_name"]');
        if (aggInput) aggInput.value = newName;
    } else {
        const firstCustom = document.querySelector('input[name="setup_obj_name[]"]');
        if (firstCustom) firstCustom.value = newName;
    }
}

// Initialize default setup command on page load
function initializeDefaultSetupCommand() {
    const container = document.getElementById("setup-commands-container");
    const div = document.createElement("div");
    div.className = "inline-form";
    div.innerHTML = `
        <div class="field">
            <label>Command</label>
            <input type="text" value="scoreboard objectives add" readonly>
        </div>
        <div class="field">
            <label>Custom Name</label>
            <input type="text" name="setup_obj_name[]" pattern="[a-zA-Z]+" required>
        </div>
        <div class="field">
            <label>Namespace</label>
            <input type="text" value="minecraft" readonly>
        </div>
        <div class="field">
            <label>Action</label>
            <select name="setup_action[]">
                <option value="custom">custom</option>
                <option value="mined">mined</option>
                <option value="broken">broken</option>
                <option value="crafted">crafted</option>
                <option value="used">used</option>
                <option value="picked_up">picked_up</option>
                <option value="dropped">dropped</option>
                <option value="killed">killed</option>
                <option value="killed_by">killed_by</option>
            </select>
        </div>
        <div class="field">
            <label>Namespace</label>
            <input type="text" value="minecraft" readonly>
        </div>
        <div class="field">
            <label>Item/Entity/Block</label>
            <input type="text" name="setup_item[]" pattern="[a-z_]+" required>
        </div>
    `;
    container.appendChild(div);
}

// Setup live syncing for aggregate name
function setupLiveSync() {
    const overallInput = document.querySelector('input[name="aggregate_objective"]');
    if (overallInput) {
        overallInput.addEventListener("input", syncAggregateName);
    }
}

// Initialize on page load
window.addEventListener("DOMContentLoaded", () => {
    initializeDefaultSetupCommand();
    setupLiveSync();
});