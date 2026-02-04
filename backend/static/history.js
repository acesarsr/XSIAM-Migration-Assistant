// History view JavaScript

const api = {
    getHistory: async () => {
        const res = await fetch('/api/history');
        return res.json();
    },
    getDetails: async (migrationId) => {
        const res = await fetch(`/api/history/${migrationId}`);
        return res.json();
    },
    deleteMigration: async (migrationId) => {
        const res = await fetch(`/api/history/${migrationId}`, { method: 'DELETE' });
        return res.json();
    },
    getStats: async () => {
        const res = await fetch('/api/history/stats');
        return res.json();
    }
};

async function loadStats() {
    try {
        const stats = await api.getStats();
        document.getElementById('totalMigrations').textContent = stats.total_migrations;
        document.getElementById('totalRules').textContent = stats.total_rules;
        document.getElementById('totalSuccessful').textContent = stats.total_successful;
        document.getElementById('avgSuccessRate').textContent = stats.avg_success_rate + '%';
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

async function loadHistory() {
    try {
        const history = await api.getHistory();
        renderHistoryTable(history);
    } catch (err) {
        console.error('Failed to load history:', err);
        document.getElementById('historyTableBody').innerHTML = `
            <tr><td colspan="8" style="text-align: center; color: var(--text-secondary)">
                Failed to load history
            </td></tr>
        `;
    }
}

function renderHistoryTable(history) {
    const tbody = document.getElementById('historyTableBody');

    if (history.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-secondary)">
                No migration history yet. Start by uploading rules!
            </td></tr>
        `;
        return;
    }

    tbody.innerHTML = history.map(migration => {
        const date = new Date(migration.timestamp).toLocaleString();
        const successRate = migration.total_rules > 0
            ? ((migration.successful_conversions / migration.total_rules) * 100).toFixed(1)
            : 0;

        return `
            <tr>
                <td>${date}</td>
                <td><span class="badge badge-${migration.source_platform}">${migration.source_platform}</span></td>
                <td>${migration.file_name || 'N/A'}</td>
                <td>${migration.total_rules}</td>
                <td style="color: var(--success)">${migration.successful_conversions}</td>
                <td style="color: var(--danger)">${migration.failed_conversions}</td>
                <td>
                    <div style="background: var(--bg-secondary); border-radius: 1rem; padding: 0.25rem; position: relative; overflow: hidden;">
                        <div style="background: var(--success); height: 1.5rem; border-radius: 1rem; width: ${successRate}%; transition: width 0.3s;"></div>
                        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 0.75rem; font-weight: bold;">
                            ${successRate}%
                        </div>
                    </div>
                </td>
                <td>
                    <button onclick="viewDetails(${migration.id})" style="background: var(--accent); border: none; color: white; padding: 0.25rem 0.75rem; border-radius: 0.25rem; cursor: pointer; margin-right: 0.5rem;">View</button>
                    <button onclick="deleteMigration(${migration.id})" style="background: var(--danger); border: none; color: white; padding: 0.25rem 0.75rem; border-radius: 0.25rem; cursor: pointer;">Delete</button>
                </td>
            </tr>
        `;
    }).join('');
}

async function viewDetails(migrationId) {
    try {
        const migration = await api.getDetails(migrationId);

        const modal = document.getElementById('detailsModal');
        const detailsDiv = document.getElementById('migrationDetails');

        const date = new Date(migration.timestamp).toLocaleString();

        let html = `
            <div style="background: var(--bg-secondary); padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1.5rem;">
                <h3>Migration Information</h3>
                <p><strong>Date:</strong> ${date}</p>
                <p><strong>Platform:</strong> ${migration.source_platform}</p>
                <p><strong>File:</strong> ${migration.file_name || 'N/A'}</p>
                <p><strong>Total Rules:</strong> ${migration.total_rules}</p>
                <p><strong>Successful:</strong> ${migration.successful_conversions}</p>
                <p><strong>Failed:</strong> ${migration.failed_conversions}</p>
            </div>
            
            <h3>Rules</h3>
            <table style="width: 100%; margin-top: 1rem;">
                <thead>
                    <tr>
                        <th>Rule Name</th>
                        <th>Status</th>
                        <th>Coverage Score</th>
                        <th>Best Match</th>
                    </tr>
                </thead>
                <tbody>
        `;

        for (const rule of migration.rules || []) {
            const coveragePercent = (rule.coverage_score * 100).toFixed(0);
            html += `
                <tr>
                    <td>${rule.rule_name}</td>
                    <td><span class="badge badge-${rule.status}">${rule.status}</span></td>
                    <td>${coveragePercent}%</td>
                    <td>${rule.best_match || 'No match'}</td>
                </tr>
            `;
        }

        html += `
                </tbody>
            </table>
        `;

        detailsDiv.innerHTML = html;
        modal.style.display = 'flex';
    } catch (err) {
        alert('Failed to load migration details: ' + err.message);
    }
}

async function deleteMigration(migrationId) {
    if (!confirm('Are you sure you want to delete this migration? This cannot be undone.')) {
        return;
    }

    try {
        await api.deleteMigration(migrationId);
        await loadHistory();
        await loadStats();
    } catch (err) {
        alert('Failed to delete migration: ' + err.message);
    }
}

function closeDetailsModal() {
    document.getElementById('detailsModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function (event) {
    const modal = document.getElementById('detailsModal');
    if (event.target === modal) {
        closeDetailsModal();
    }
};

// Initial load
loadStats();
loadHistory();
