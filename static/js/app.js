/**
 * ═══════════════════════════════════════════════════════════════
 * MediScan AI — Frontend Application Logic
 * Handles symptom search, voice input, prediction, charts,
 * PDF export, theme toggle, and diagnosis history.
 * ═══════════════════════════════════════════════════════════════
 */

// ─── State ──────────────────────────────────────────────────────
const state = {
    symptoms: [],           // Full list from API
    selectedSymptoms: [],   // Currently selected
    sessionId: null,        // Session ID for history
    currentResult: null,    // Last prediction result
    chart: null,            // Chart.js instance
    isRecording: false,     // Voice input active
    recognition: null,      // SpeechRecognition instance
};

// ─── Initialize ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Generate or restore session ID
    state.sessionId = localStorage.getItem('mediscan_session') || generateId();
    localStorage.setItem('mediscan_session', state.sessionId);

    // Load theme
    const savedTheme = localStorage.getItem('mediscan_theme') || 'light';
    setTheme(savedTheme);

    // Check if disclaimer was already accepted
    if (localStorage.getItem('mediscan_disclaimer') === 'accepted') {
        document.getElementById('disclaimer-modal').classList.remove('active');
    }

    // Load symptoms
    loadSymptoms();

    // Set up search input
    const searchInput = document.getElementById('symptom-search');
    searchInput.addEventListener('input', handleSearch);
    searchInput.addEventListener('focus', handleSearch);

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            document.getElementById('symptom-dropdown').classList.remove('active');
        }
    });

    // Initialize speech recognition
    initSpeechRecognition();
});

// ─── Utility ────────────────────────────────────────────────────
function generateId() {
    return 'ms_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
}

// ─── Disclaimer ─────────────────────────────────────────────────
function acceptDisclaimer() {
    localStorage.setItem('mediscan_disclaimer', 'accepted');
    const modal = document.getElementById('disclaimer-modal');
    modal.style.animation = 'fadeIn 0.3s ease-out reverse';
    setTimeout(() => modal.classList.remove('active'), 280);
}

// ─── Theme ──────────────────────────────────────────────────────
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('mediscan_theme', next);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const iconDark = document.getElementById('theme-icon-dark');
    const iconLight = document.getElementById('theme-icon-light');
    const label = document.getElementById('theme-label');

    if (theme === 'dark') {
        iconDark.style.display = 'none';
        iconLight.style.display = 'block';
        label.textContent = 'Light';
    } else {
        iconDark.style.display = 'block';
        iconLight.style.display = 'none';
        label.textContent = 'Dark';
    }

    // Update chart if exists
    if (state.chart) {
        updateChartTheme();
    }
}

// ─── Symptoms Loading ───────────────────────────────────────────
async function loadSymptoms() {
    try {
        const res = await fetch('/api/symptoms');
        const data = await res.json();

        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        state.symptoms = data.symptoms;
    } catch (err) {
        showToast('Failed to load symptoms. Is the server running?', 'error');
        console.error('Load symptoms error:', err);
    }
}

// ─── Search & Dropdown ──────────────────────────────────────────
function handleSearch() {
    const query = document.getElementById('symptom-search').value.trim().toLowerCase();
    const dropdown = document.getElementById('symptom-dropdown');

    if (!query && !document.getElementById('symptom-search').matches(':focus')) {
        dropdown.classList.remove('active');
        return;
    }

    let filtered = state.symptoms;
    if (query) {
        filtered = state.symptoms.filter(s =>
            s.name.toLowerCase().includes(query)
        );
    }

    if (filtered.length === 0) {
        dropdown.innerHTML = '<div class="dropdown-empty">No symptoms matching your search</div>';
        dropdown.classList.add('active');
        return;
    }

    // Limit visible items
    const shown = filtered.slice(0, 50);
    dropdown.innerHTML = shown.map(s => {
        const isSelected = state.selectedSymptoms.includes(s.id);
        let displayName = s.name;

        // Highlight matching text
        if (query) {
            const idx = displayName.toLowerCase().indexOf(query);
            if (idx !== -1) {
                displayName = displayName.substring(0, idx) +
                    '<span class="highlight">' + displayName.substring(idx, idx + query.length) + '</span>' +
                    displayName.substring(idx + query.length);
            }
        }

        return `
            <div class="dropdown-item ${isSelected ? 'selected' : ''}"
                 onclick="toggleSymptom('${s.id}', '${s.name}')">
                <span class="check-icon">${isSelected ? '✓' : ''}</span>
                <span>${displayName}</span>
            </div>
        `;
    }).join('');

    if (filtered.length > 50) {
        dropdown.innerHTML += `<div class="dropdown-empty">Showing 50 of ${filtered.length} results. Type more to narrow down.</div>`;
    }

    dropdown.classList.add('active');
}

// ─── Symptom Selection ──────────────────────────────────────────
function toggleSymptom(id, name) {
    const idx = state.selectedSymptoms.indexOf(id);

    if (idx === -1) {
        state.selectedSymptoms.push(id);
    } else {
        state.selectedSymptoms.splice(idx, 1);
    }

    renderSelectedSymptoms();
    handleSearch(); // Refresh dropdown
    updateActionButtons();
}

function removeSymptom(id) {
    const idx = state.selectedSymptoms.indexOf(id);
    if (idx !== -1) {
        state.selectedSymptoms.splice(idx, 1);
        renderSelectedSymptoms();
        handleSearch();
        updateActionButtons();
    }
}

function clearSymptoms() {
    state.selectedSymptoms = [];
    renderSelectedSymptoms();
    handleSearch();
    updateActionButtons();
    document.getElementById('symptom-search').value = '';
}

function renderSelectedSymptoms() {
    const container = document.getElementById('selected-symptoms');
    const noMsg = document.getElementById('no-symptoms-msg');

    if (state.selectedSymptoms.length === 0) {
        container.innerHTML = '<p id="no-symptoms-msg" class="empty-msg">No symptoms selected yet. Start typing above to search.</p>';
        return;
    }

    container.innerHTML = state.selectedSymptoms.map(id => {
        const symptom = state.symptoms.find(s => s.id === id);
        const name = symptom ? symptom.name : id.replace(/_/g, ' ');
        return `
            <span class="symptom-pill">
                ${name}
                <button class="remove-pill" onclick="removeSymptom('${id}')" title="Remove">×</button>
            </span>
        `;
    }).join('');
}

function updateActionButtons() {
    const clearBtn = document.getElementById('clear-symptoms-btn');
    const diagnoseBtn = document.getElementById('diagnose-btn');
    const hasSymptoms = state.selectedSymptoms.length > 0;

    clearBtn.disabled = !hasSymptoms;
    diagnoseBtn.disabled = !hasSymptoms;
}

// ─── Voice Input ────────────────────────────────────────────────
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        document.getElementById('voice-btn').style.display = 'none';
        return;
    }

    state.recognition = new SpeechRecognition();
    state.recognition.continuous = false;
    state.recognition.interimResults = false;
    state.recognition.lang = 'en-US';

    state.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript.toLowerCase().trim();
        processVoiceInput(transcript);
        stopVoiceInput();
    };

    state.recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'not-allowed') {
            showToast('Microphone access denied. Please allow microphone access.', 'error');
        } else {
            showToast('Voice input error. Please try again.', 'error');
        }
        stopVoiceInput();
    };

    state.recognition.onend = () => {
        stopVoiceInput();
    };
}

function startVoiceInput() {
    if (!state.recognition) {
        showToast('Voice input is not supported in your browser. Try Chrome.', 'warning');
        return;
    }

    if (state.isRecording) {
        stopVoiceInput();
        return;
    }

    state.isRecording = true;
    const btn = document.getElementById('voice-btn');
    btn.classList.add('recording');
    document.getElementById('mic-icon').style.display = 'none';
    document.getElementById('mic-icon-active').style.display = 'block';

    showToast('Listening... Speak your symptoms', 'info');

    try {
        state.recognition.start();
    } catch (e) {
        stopVoiceInput();
    }
}

function stopVoiceInput() {
    state.isRecording = false;
    const btn = document.getElementById('voice-btn');
    btn.classList.remove('recording');
    document.getElementById('mic-icon').style.display = 'block';
    document.getElementById('mic-icon-active').style.display = 'none';

    try {
        state.recognition.stop();
    } catch (e) { /* ignore */ }
}

function processVoiceInput(transcript) {
    showToast(`Heard: "${transcript}"`, 'success');

    // Split by common separators
    const words = transcript.split(/[,;and]+/).map(w => w.trim()).filter(Boolean);
    let matchCount = 0;

    words.forEach(word => {
        // Find best matching symptom
        const matches = state.symptoms.filter(s =>
            s.name.toLowerCase().includes(word) ||
            word.includes(s.name.toLowerCase())
        );

        matches.forEach(match => {
            if (!state.selectedSymptoms.includes(match.id)) {
                state.selectedSymptoms.push(match.id);
                matchCount++;
            }
        });
    });

    if (matchCount > 0) {
        renderSelectedSymptoms();
        updateActionButtons();
        showToast(`Added ${matchCount} symptom(s)`, 'success');
    } else {
        // Try fuzzy match
        const searchInput = document.getElementById('symptom-search');
        searchInput.value = transcript;
        handleSearch();
        showToast('No exact match found. Check the suggestions below.', 'info');
    }
}

// ─── Diagnosis ──────────────────────────────────────────────────
async function diagnose() {
    if (state.selectedSymptoms.length === 0) {
        showToast('Please select at least one symptom.', 'warning');
        return;
    }

    const btn = document.getElementById('diagnose-btn');
    const btnText = document.getElementById('diagnose-btn-text');
    const spinner = document.getElementById('diagnose-spinner');

    btn.disabled = true;
    btnText.textContent = 'Analyzing...';
    spinner.style.display = 'block';

    try {
        const res = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symptoms: state.selectedSymptoms,
                session_id: state.sessionId
            })
        });

        const data = await res.json();

        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        state.currentResult = data;
        displayResults(data);

    } catch (err) {
        showToast('Failed to get diagnosis. Please try again.', 'error');
        console.error('Diagnose error:', err);
    } finally {
        btn.disabled = false;
        btnText.textContent = 'Analyze Symptoms';
        spinner.style.display = 'none';
    }
}

// ─── Display Results ────────────────────────────────────────────
function displayResults(data) {
    const resultsSection = document.getElementById('results-section');

    // Disease name
    document.getElementById('disease-name').textContent = data.predicted_disease;

    // Confidence ring
    animateConfidence(data.confidence);

    if (data.low_confidence) {
        document.getElementById('disease-name').textContent = "Uncertain Diagnosis";
        document.getElementById('disease-description').textContent = data.message;
        document.getElementById('disease-description').style.color = "var(--warning)";
        document.getElementById('disease-description').style.fontWeight = "bold";
        
        // Hide info lists
        ['causes-list', 'symptoms-list', 'risk-factors-list', 'prevention-list', 'remedies-list', 'advice-list', 'doctor-list', 'clinical-treatments-list', 'shap-list'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = '<li>Insufficient data</li>';
        });
        
        const shapContainer = document.getElementById('shap-explanation-container');
        if (shapContainer) shapContainer.style.display = 'none';
        
    } else {
        document.getElementById('disease-name').textContent = data.predicted_disease;
        document.getElementById('disease-description').textContent = data.knowledge.description;
        document.getElementById('disease-description').style.color = "var(--text-secondary)";
        document.getElementById('disease-description').style.fontWeight = "normal";

        // Selected symptoms pills
        const pillsContainer = document.getElementById('result-symptoms-pills');
        pillsContainer.innerHTML = data.selected_symptoms.map(s =>
            `<span class="result-pill">${s}</span>`
        ).join('');
        
        // SHAP Explanations
        const shapContainer = document.getElementById('shap-explanation-container');
        const shapList = document.getElementById('shap-list');
        if (data.shap_explanations && data.shap_explanations.length > 0) {
            shapContainer.style.display = 'block';
            shapList.innerHTML = data.shap_explanations.map(s => 
                `<li><strong>${s.symptom}</strong> (Contribution: ${s.contribution}%)</li>`
            ).join('');
        } else {
            shapContainer.style.display = 'none';
        }

        // Info lists
        populateList('causes-list', data.knowledge.causes);
        populateList('symptoms-list', data.knowledge.common_symptoms);
        populateList('risk-factors-list', data.knowledge.risk_factors);
        populateList('prevention-list', data.knowledge.prevention);
        populateList('remedies-list', data.knowledge.home_remedies);
        populateList('advice-list', data.knowledge.general_advice);
        populateList('doctor-list', data.knowledge.when_to_see_doctor);
        populateList('clinical-treatments-list', data.knowledge.clinical_treatments);
    }

    // Chart
    renderChart(data.top_predictions);

    // Show results
    resultsSection.style.display = 'block';

    // Scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);

    // Refresh history
    loadHistory();
}

function animateConfidence(confidence) {
    const circle = document.getElementById('confidence-circle');
    const valueEl = document.getElementById('confidence-value');
    const circumference = 2 * Math.PI * 42; // r=42
    const offset = circumference - (confidence / 100) * circumference;

    // Reset
    circle.style.strokeDashoffset = circumference;

    // Animate after a short delay
    setTimeout(() => {
        circle.style.strokeDashoffset = offset;
    }, 100);

    // Animate number
    let current = 0;
    const step = confidence / 40;
    const timer = setInterval(() => {
        current += step;
        if (current >= confidence) {
            current = confidence;
            clearInterval(timer);
        }
        valueEl.textContent = Math.round(current) + '%';
    }, 25);
}

function populateList(elementId, items) {
    const list = document.getElementById(elementId);
    if (!items || items.length === 0) {
        list.innerHTML = '<li>No information available</li>';
        return;
    }
    list.innerHTML = items.map(item => `<li>${item}</li>`).join('');
}

// ─── Chart ──────────────────────────────────────────────────────
function renderChart(predictions) {
    const ctx = document.getElementById('probability-chart').getContext('2d');

    // Destroy previous chart
    if (state.chart) {
        state.chart.destroy();
    }

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#94a3b8' : '#475569';
    const gridColor = isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(15, 23, 42, 0.06)';

    const colors = ['#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b'];
    const bgColors = colors.map(c => c + '33');

    state.chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: predictions.map(p => p.disease),
            datasets: [{
                label: 'Probability (%)',
                data: predictions.map(p => p.probability),
                backgroundColor: bgColors.slice(0, predictions.length),
                borderColor: colors.slice(0, predictions.length),
                borderWidth: 2,
                borderRadius: 6,
                barThickness: 28,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: isDark ? '#1e293b' : '#ffffff',
                    titleColor: isDark ? '#f1f5f9' : '#0f172a',
                    bodyColor: isDark ? '#94a3b8' : '#475569',
                    borderColor: isDark ? '#334155' : '#e2e8f0',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => ` ${ctx.parsed.x.toFixed(1)}%`
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: gridColor },
                    ticks: { color: textColor, font: { family: "'Inter', sans-serif", size: 12 }, callback: v => v + '%' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: textColor, font: { family: "'Inter', sans-serif", size: 12, weight: 600 } }
                }
            }
        }
    });
}

function updateChartTheme() {
    if (state.currentResult) {
        renderChart(state.currentResult.top_predictions);
    }
}

// ─── New Diagnosis ──────────────────────────────────────────────
function newDiagnosis() {
    clearSymptoms();
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('symptom-search').value = '';
    state.currentResult = null;

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ─── History ────────────────────────────────────────────────────
function toggleHistory() {
    const sidebar = document.getElementById('history-sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');

    if (sidebar.classList.contains('active')) {
        loadHistory();
    }
}

async function loadHistory() {
    try {
        const res = await fetch(`/api/history?session_id=${state.sessionId}`);
        const data = await res.json();

        const list = document.getElementById('history-list');

        if (!data.history || data.history.length === 0) {
            list.innerHTML = '<p class="empty-msg">No diagnosis history yet.</p>';
            return;
        }

        list.innerHTML = data.history.map(item => {
            const symptoms = item.symptoms.map(s => s.replace(/_/g, ' ')).slice(0, 4);
            const time = new Date(item.timestamp).toLocaleString();

            return `
                <div class="history-item">
                    <div class="history-disease">${item.predicted_disease}</div>
                    <div class="history-confidence">Confidence: ${item.confidence}%</div>
                    <div class="history-symptoms-preview">
                        ${symptoms.map(s => `<span class="mini-pill">${s}</span>`).join('')}
                        ${item.symptoms.length > 4 ? `<span class="mini-pill">+${item.symptoms.length - 4} more</span>` : ''}
                    </div>
                    <div class="history-time">${time}</div>
                </div>
            `;
        }).join('');
    } catch (err) {
        console.error('Load history error:', err);
    }
}

async function clearHistory() {
    try {
        await fetch('/api/history', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: state.sessionId })
        });

        document.getElementById('history-list').innerHTML = '<p class="empty-msg">No diagnosis history yet.</p>';
        showToast('History cleared', 'success');
    } catch (err) {
        showToast('Failed to clear history', 'error');
    }
}

// ─── PDF Export ─────────────────────────────────────────────────
function downloadPDF() {
    if (!state.currentResult) {
        showToast('No diagnosis to export.', 'warning');
        return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const r = state.currentResult;
    let y = 20;

    // Colors
    const accent = [6, 182, 212];
    const dark = [15, 23, 42];
    const gray = [100, 116, 139];
    const warning = [245, 158, 11];

    // Header bar
    doc.setFillColor(...accent);
    doc.rect(0, 0, 210, 35, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(20);
    doc.setFont('helvetica', 'bold');
    doc.text('MediScan AI', 15, 16);
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text('Medical Disease Diagnosis Report', 15, 25);
    doc.text(`Generated: ${new Date().toLocaleString()}`, 15, 31);

    y = 45;

    // Predicted Disease
    doc.setTextColor(...dark);
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('PREDICTED CONDITION', 15, y);
    y += 8;
    doc.setFontSize(18);
    doc.setTextColor(...accent);
    doc.text(r.predicted_disease, 15, y);
    y += 8;
    doc.setFontSize(11);
    doc.setTextColor(...gray);
    doc.text(`Confidence: ${r.confidence}%`, 15, y);
    y += 12;

    // Symptoms
    doc.setTextColor(...dark);
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('ANALYZED SYMPTOMS', 15, y);
    y += 7;
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...gray);
    const symptomsText = r.selected_symptoms.join(', ');
    const symptomsLines = doc.splitTextToSize(symptomsText, 180);
    doc.text(symptomsLines, 15, y);
    y += symptomsLines.length * 5 + 8;

    // Top Predictions
    if (r.top_predictions && r.top_predictions.length > 1) {
        doc.setTextColor(...dark);
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text('TOP PREDICTIONS', 15, y);
        y += 7;
        doc.setFontSize(9);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(...gray);
        r.top_predictions.forEach(p => {
            doc.text(`• ${p.disease}: ${p.probability}%`, 18, y);
            y += 5;
        });
        y += 5;
    }

    // Helper to add sections
    function addSection(title, items) {
        if (!items || items.length === 0) return;
        if (y > 260) { doc.addPage(); y = 20; }

        doc.setTextColor(...dark);
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text(title, 15, y);
        y += 7;
        doc.setFontSize(9);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(...gray);

        items.forEach(item => {
            if (y > 275) { doc.addPage(); y = 20; }
            const lines = doc.splitTextToSize(`• ${item}`, 178);
            doc.text(lines, 18, y);
            y += lines.length * 4.5 + 1;
        });
        y += 5;
    }

    addSection('ABOUT THIS CONDITION', [r.knowledge.description]);
    addSection('POSSIBLE CAUSES', r.knowledge.causes);
    addSection('COMMON SYMPTOMS', r.knowledge.common_symptoms);
    addSection('RISK FACTORS', r.knowledge.risk_factors);
    addSection('PREVENTION TIPS', r.knowledge.prevention);
    addSection('HOME REMEDIES', r.knowledge.home_remedies);
    addSection('GENERAL ADVICE', r.knowledge.general_advice);
    addSection('WHEN TO SEE A DOCTOR', r.knowledge.when_to_see_doctor);

    // Disclaimer
    if (y > 250) { doc.addPage(); y = 20; }
    y += 5;
    doc.setFillColor(255, 248, 230);
    doc.rect(12, y - 4, 186, 25, 'F');
    doc.setDrawColor(...warning);
    doc.rect(12, y - 4, 186, 25, 'S');
    doc.setTextColor(...warning);
    doc.setFontSize(9);
    doc.setFont('helvetica', 'bold');
    doc.text('MEDICAL DISCLAIMER', 15, y + 2);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...gray);
    doc.setFontSize(7.5);
    const disclaimerText = 'This report is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of a qualified healthcare provider with any questions regarding a medical condition. Do not use this report for emergency medical situations.';
    const discLines = doc.splitTextToSize(disclaimerText, 178);
    doc.text(discLines, 15, y + 8);

    // Save
    const filename = `MediScan_Report_${r.predicted_disease.replace(/\s+/g, '_')}_${Date.now()}.pdf`;
    doc.save(filename);
    showToast('PDF report downloaded!', 'success');
}

// ─── Toast Notifications ────────────────────────────────────────
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');

    const icons = {
        success: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        error: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        warning: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        info: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span>${message}`;
    container.appendChild(toast);

    // Auto-remove
    setTimeout(() => {
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
