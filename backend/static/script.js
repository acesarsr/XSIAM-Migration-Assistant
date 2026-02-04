const api = {
    upload: async (platform, file) => {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch(`/api/upload/${platform}`, {
            method: 'POST',
            body: formData
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },
    getRules: async () => {
        const res = await fetch('/api/rules');
        return res.json();
    },
    getCoverage: async (ruleId) => {
        const res = await fetch(`/api/coverage/${ruleId}`);
        return res.json();
    },
    exportContentPack: async () => {
        const res = await fetch('/api/export/content-pack', { method: 'POST' });
        if (!res.ok) throw new Error('Export failed');
        return res.blob();
    },
    // XSIAM API functions
    saveXSIAMConfig: async (config) => {
        const res = await fetch('/api/config/xsiam', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        return res.json();
    },
    testXSIAMConnection: async () => {
        const res = await fetch('/api/config/xsiam/test', { method: 'POST' });
        return res.json();
    },
    uploadToXSIAM: async (ruleId) => {
        const res = await fetch(`/api/upload-to-xsiam/${ruleId}`, { method: 'POST' });
        return res.json();
    }
};

// State
let currentRules = [];

// DOM Elements
const fileInput = document.getElementById('fileInput');
const platformSelect = document.getElementById('platformSelect');
const uploadStatus = document.getElementById('uploadStatus');
const tableBody = document.getElementById('rulesTableBody');
const editModal = document.getElementById('editModal');

// Event Listeners
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const platform = platformSelect.value;
    uploadStatus.textContent = 'Uploading and analyzing...';
    uploadStatus.style.color = 'var(--text-secondary)';

    try {
        const result = await api.upload(platform, file);
        uploadStatus.textContent = `Upload successful! Processed ${result.count} rules.`;
        uploadStatus.style.color = 'var(--success)';
        document.getElementById('exportBtn').style.display = 'inline-block';
        document.getElementById('reportBtn').style.display = 'inline-block';
        refreshRules();
    } catch (err) {
        uploadStatus.textContent = `Error: ${err.message}`;
        uploadStatus.style.color = '#ef4444';
    }
});

async function refreshRules() {
    try {
        currentRules = await api.getRules();
        renderTable();

        // Show export and report buttons if we have rules
        if (currentRules.length > 0) {
            document.getElementById('exportBtn').style.display = 'inline-block';
            document.getElementById('reportBtn').style.display = 'inline-block';
        }
    } catch (err) {
        console.error('Failed to fetch rules:', err);
    }
}

function renderTable() {
    tableBody.innerHTML = currentRules.map((rule, idx) => `
        <tr>
            <td><span class="badge badge-${rule.source_platform}">${rule.source_platform}</span></td>
            <td>${rule.name}</td>
            <td style="font-family: monospace; font-size: 0.875rem;">
                ${rule.original_query.substring(0, 50)}${rule.original_query.length > 50 ? '...' : ''}
            </td>
            <td><span class="badge badge-${rule.status.toLowerCase()}">${rule.status}</span></td>
            <td>
                <button onclick="openModal(${idx})" style="background: none; border: 1px solid var(--border); color: var(--text-primary); padding: 0.25rem 0.75rem; border-radius: 0.25rem; cursor: pointer; margin-right: 0.5rem;">Edit</button>
                <button onclick="checkCoverage(${idx})" style="background: var(--accent); border: none; color: white; padding: 0.25rem 0.75rem; border-radius: 0.25rem; cursor: pointer;">Coverage</button>
            </td>
        </tr>
    `).join('');
}

// Modal Logic
let editingIndex = -1;

window.openModal = (idx) => {
    editingIndex = idx;
    const rule = currentRules[idx];
    document.getElementById('modalTitle').textContent = rule.name;
    document.getElementById('sourceQuery').value = rule.original_query;
    document.getElementById('xqlQuery').value = rule.converted_query || '';
    editModal.classList.add('active');
};

window.closeModal = () => {
    editModal.classList.remove('active');
};

window.saveRule = async () => {
    const newXql = document.getElementById('xqlQuery').value;
    const rule = currentRules[editingIndex];

    // Update local state
    rule.converted_query = newXql;
    rule.status = "reviewed"; // Mark as reviewed after manual edit

    try {
        // Persist to backend
        const res = await fetch(`/api/rules/${rule.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(rule)
        });

        if (!res.ok) throw new Error("Failed to save");

        closeModal();
        renderTable();
    } catch (err) {
        alert("Error saving rule: " + err.message);
    }
};

window.checkCoverage = async (idx) => {
    const rule = currentRules[idx];
    try {
        const coverage = await api.getCoverage(rule.id);

        let html = `<h3 style="margin-bottom: 1rem;">Coverage Analysis: ${rule.name}</h3>`;

        if (coverage.covered) {
            html += `<p style="color: var(--success); margin-bottom: 1rem;">✓ Potentially covered by XSIAM analytics (${Math.round(coverage.confidence * 100)}% confidence)</p>`;
            html += `<h4>Top Matches:</h4><ul style="list-style: none; padding: 0;">`;

            coverage.all_matches.forEach(match => {
                html += `
                    <li style="background: var(--bg-primary); padding: 1rem; margin: 0.5rem 0; border-radius: 0.5rem; border-left: 3px solid var(--accent);">
                        <strong>${match.name}</strong> <span class="badge badge-${match.severity?.toLowerCase() || 'medium'}">${match.severity}</span><br>
                        <small style="color: var(--text-secondary);">Match: ${match.score * 100}%</small><br>
                        <small style="color: var(--text-secondary);">Tags: ${match.tags || 'N/A'}</small>
                    </li>
                `;
            });
            html += `</ul>`;
        } else {
            html += `<p style="color: var(--warning);">⚠ No matching XSIAM analytics found. You may need to create a custom detection rule.</p>`;
        }

        document.getElementById('modalTitle').innerHTML = 'Coverage Analysis';
        document.querySelector('.editor-split').innerHTML = html;
        document.querySelector('.modal-content button.upload-btn').style.display = 'none';
        editModal.classList.add('active');
    } catch (err) {
        alert('Error checking coverage: ' + err.message);
    }
};

window.exportContentPack = async () => {
    try {
        const blob = await api.exportContentPack();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'MigratedRules_ContentPack.zip';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (err) {
        alert('Error exporting content pack: ' + err.message);
    }
};

window.toggleReportMenu = () => {
    const menu = document.getElementById('reportMenu');
    menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
};

window.downloadReport = async (format) => {
    document.getElementById('reportMenu').style.display = 'none';

    try {
        const res = await fetch(`/api/reports/coverage/${format}`);
        if (!res.ok) throw new Error('Report generation failed');

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Coverage_Report.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (err) {
        alert('Error generating report: ' + err.message);
    }
};

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.dropdown')) {
        document.getElementById('reportMenu').style.display = 'none';
    }
});

// Initial Load
refreshRules();
// Settings Modal JS
window.openSettingsModal = () => {
    document.getElementById("settingsModal").style.display = "flex";
};

window.closeSettingsModal = () => {
    document.getElementById("settingsModal").style.display = "none";
};

window.saveXSIAMConfig = async () => {
    const fqdn = document.getElementById("xsiamFQDN").value.trim();
    const apiKey = document.getElementById("xsiamAPIKey").value.trim();
    const apiKeyID = document.getElementById("xsiamAPIKeyID").value.trim();
    
    if (!fqdn || !apiKey || !apiKeyID) {
        alert("Please fill in all fields");
        return;
    }
    
    try {
        await api.saveXSIAMConfig({ fqdn, api_key: apiKey, api_key_id: apiKeyID });
        document.getElementById("settingsStatus").innerHTML = "<span style=\"color: var(--success)\">✅ Configuration saved successfully!</span>";
    } catch (err) {
        document.getElementById("settingsStatus").innerHTML = "<span style=\"color: var(--danger)\">❌ Failed to save configuration</span>";
    }
};

window.testXSIAMConnection = async () => {
    document.getElementById("settingsStatus").textContent = "Testing connection...";
    
    try {
        const result = await api.testXSIAMConnection();
        document.getElementById("settingsStatus").innerHTML = "<span style=\"color: var(--success)\">✅ " + result.message + "</span>";
    } catch (err) {
        document.getElementById("settingsStatus").innerHTML = "<span style=\"color: var(--danger)\">❌ Connection failed. Check your credentials.</span>";
    }
};
