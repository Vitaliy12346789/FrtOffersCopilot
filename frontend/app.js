// API base URL - empty for same origin
const API_BASE = '';

// DOM Elements
const loadPortSelect = document.getElementById('loadPort');
const dischargePortSelect = document.getElementById('dischargePort');
const cargoSelect = document.getElementById('cargo');
const chartererSelect = document.getElementById('charterer');
const quantityInput = document.getElementById('quantity');
const toleranceInput = document.getElementById('tolerance');
const freightRateInput = document.getElementById('freightRate');
const demurrageRateInput = document.getElementById('demurrageRate');
const laycanStartInput = document.getElementById('laycanStart');
const laycanEndInput = document.getElementById('laycanEnd');
const orSubCheckbox = document.getElementById('orSub');
const offerForm = document.getElementById('offerForm');
const offerOutput = document.getElementById('offerOutput');
const copyBtn = document.getElementById('copyBtn');
const copySuccess = document.getElementById('copySuccess');
const summary = document.getElementById('summary');
const summaryContent = document.getElementById('summaryContent');
const loadingOverlay = document.getElementById('loadingOverlay');
const generateBtn = document.getElementById('generateBtn');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadDropdownData();
    setDefaultDates();
    setupEventListeners();
});

// Load dropdown data from API
async function loadDropdownData() {
    try {
        const [loadPorts, dischargePorts, cargoes, charterers] = await Promise.all([
            fetch(`${API_BASE}/api/ports/load`).then(r => r.json()),
            fetch(`${API_BASE}/api/ports/discharge`).then(r => r.json()),
            fetch(`${API_BASE}/api/cargoes`).then(r => r.json()),
            fetch(`${API_BASE}/api/charterers`).then(r => r.json())
        ]);

        // Populate load ports
        loadPorts.forEach(port => {
            const option = document.createElement('option');
            option.value = port.name;
            option.textContent = `${port.name} (${port.region})`;
            option.dataset.region = port.region;
            loadPortSelect.appendChild(option);
        });

        // Populate discharge ports
        dischargePorts.forEach(port => {
            const option = document.createElement('option');
            option.value = port.name;
            option.textContent = `${port.name}, ${port.country}`;
            dischargePortSelect.appendChild(option);
        });

        // Populate cargoes
        cargoes.forEach(cargo => {
            const option = document.createElement('option');
            option.value = cargo.name;
            option.textContent = `${cargo.name} (STW ${cargo.stw_range})`;
            cargoSelect.appendChild(option);
        });

        // Populate charterers
        charterers.forEach(charterer => {
            const option = document.createElement('option');
            option.value = charterer.charterer_id;
            option.textContent = charterer.charterer_name;
            option.dataset.orSubDefault = charterer.or_sub_default;
            chartererSelect.appendChild(option);
        });

    } catch (error) {
        console.error('Error loading dropdown data:', error);
        alert('Failed to load form data. Please refresh the page.');
    }
}

// Set default dates (5 days from now)
function setDefaultDates() {
    const today = new Date();
    const start = new Date(today);
    start.setDate(today.getDate() + 5);
    const end = new Date(start);
    end.setDate(start.getDate() + 5);

    laycanStartInput.value = formatDate(start);
    laycanEndInput.value = formatDate(end);
}

function formatDate(date) {
    return date.toISOString().split('T')[0];
}

// Setup event listeners
function setupEventListeners() {
    // Form submit
    offerForm.addEventListener('submit', handleSubmit);

    // Copy button
    copyBtn.addEventListener('click', handleCopy);

    // Enable editing of output
    offerOutput.removeAttribute('readonly');

    // Charterer change - update OR SUB default
    chartererSelect.addEventListener('change', (e) => {
        const selected = e.target.options[e.target.selectedIndex];
        if (selected.dataset.orSubDefault === 'true') {
            orSubCheckbox.checked = true;
        }
    });

    // Laycan validation
    laycanEndInput.addEventListener('change', () => {
        if (laycanEndInput.value < laycanStartInput.value) {
            laycanEndInput.value = laycanStartInput.value;
        }
    });

    laycanStartInput.addEventListener('change', () => {
        if (laycanEndInput.value < laycanStartInput.value) {
            laycanEndInput.value = laycanStartInput.value;
        }
    });
}

// Handle form submit
async function handleSubmit(e) {
    e.preventDefault();

    // Validate
    if (!loadPortSelect.value || !dischargePortSelect.value || !cargoSelect.value) {
        alert('Please select load port, discharge port, and cargo');
        return;
    }

    // Show loading
    loadingOverlay.classList.remove('hidden');
    generateBtn.disabled = true;

    try {
        const requestData = {
            load_port: loadPortSelect.value,
            discharge_port: dischargePortSelect.value,
            cargo: cargoSelect.value,
            quantity: parseInt(quantityInput.value),
            freight_rate: parseFloat(freightRateInput.value),
            demurrage_rate: parseFloat(demurrageRateInput.value),
            laycan_start: laycanStartInput.value,
            laycan_end: laycanEndInput.value,
            charterer_id: chartererSelect.value || null,
            or_sub: orSubCheckbox.checked,
            quantity_tolerance: parseFloat(toleranceInput.value)
        };

        const response = await fetch(`${API_BASE}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate offer');
        }

        const result = await response.json();

        // Update output
        offerOutput.value = result.firm_offer_text;
        copyBtn.disabled = false;

        // Update summary
        showSummary(result.summary);

    } catch (error) {
        console.error('Error generating offer:', error);
        alert(`Error: ${error.message}`);
    } finally {
        loadingOverlay.classList.add('hidden');
        generateBtn.disabled = false;
    }
}

// Show summary
function showSummary(summaryData) {
    summaryContent.innerHTML = `
        <p><strong>Route:</strong> ${summaryData.route}</p>
        <p><strong>Cargo:</strong> ${summaryData.cargo_description}</p>
        <p><strong>Total Freight:</strong> USD ${summaryData.total_freight.toLocaleString()}</p>
        <p><strong>Port Type:</strong> ${summaryData.port_type}</p>
        <p><strong>Clauses:</strong> ${summaryData.clauses_count} clauses included</p>
    `;
    summary.classList.remove('hidden');
}

// Handle copy
async function handleCopy() {
    try {
        await navigator.clipboard.writeText(offerOutput.value);

        // Show success message
        copySuccess.classList.remove('hidden');
        copySuccess.classList.add('copy-success');

        // Hide after animation
        setTimeout(() => {
            copySuccess.classList.add('hidden');
            copySuccess.classList.remove('copy-success');
        }, 2000);

    } catch (error) {
        // Fallback for older browsers
        offerOutput.select();
        document.execCommand('copy');

        copySuccess.classList.remove('hidden');
        setTimeout(() => {
            copySuccess.classList.add('hidden');
        }, 2000);
    }
}
