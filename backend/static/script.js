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
        await api.upload(platform, file);
        uploadStatus.textContent = 'Upload successful!';
        uploadStatus.style.color = 'var(--success)';
        refreshRules();
    } catch (err) {
        uploadStatus.textContent = `Error: ${err.message}`;
        uploadStatus.style.color = '#ef4444';
    }
});

async function refreshRules() {
    currentRules = await api.getRules();
    renderTable();
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

// Initial Load
refreshRules();
