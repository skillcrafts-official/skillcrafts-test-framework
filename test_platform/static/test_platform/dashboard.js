// Глобальная переменная для хранения текущего CSV
let currentCSV = '';

function startTests() {
    const button = document.getElementById('test-button');
    const statusDiv = document.getElementById('status-message');
    const tableDiv = document.getElementById('result-table');

    button.disabled = true;
    button.textContent = 'Выполняется...';

    tableDiv.style.display = 'none';
    tableDiv.innerHTML = '';
    document.getElementById('status-filter-container').style.display = 'none';
    document.getElementById('step-status-filter').value = 'all';
    statusDiv.innerHTML = '<div class="text-muted mt-3"><div class="spinner-border spinner-border-sm me-2"></div>Тесты запущены, ожидайте...</div>';

    const formData = new FormData();
    formData.append('run_type', 'full');

    fetch('/run-tests/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const runId = data.run_id;
        pollStatus(runId, button, statusDiv, tableDiv);
    })
    .catch(error => {
        statusDiv.innerHTML = '<div class="text-danger mt-3">Ошибка запуска тестов</div>';
        button.disabled = false;
        button.textContent = 'Запустить тесты';
    });
}

function pollStatus(runId, button, statusDiv, tableDiv) {
    const interval = setInterval(() => {
        fetch(`/check-run-status/${runId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed') {
                    clearInterval(interval);
                    statusDiv.innerHTML = '<div class="text-success mt-3">Тесты завершены</div>';
                    button.disabled = false;
                    button.textContent = 'Запустить тесты';
                    loadCSVTable(runId, tableDiv);
                    loadHistory();
                } else if (data.status === 'failed') {
                    clearInterval(interval);
                    statusDiv.innerHTML = '<div class="text-danger mt-3">Ошибка при выполнении тестов</div>';
                    button.disabled = false;
                    button.textContent = 'Запустить тесты';
                } else {
                    statusDiv.innerHTML = '<div class="text-muted mt-3"><div class="spinner-border spinner-border-sm me-2"></div>Тесты выполняются...</div>';
                }
            })
            .catch(error => {
                clearInterval(interval);
                statusDiv.innerHTML = '<div class="text-danger mt-3">Ошибка опроса статуса</div>';
                button.disabled = false;
                button.textContent = 'Запустить тесты';
            });
    }, 2000);
}

function loadCSVTable(runId, tableDiv) {
    fetch(`/download-csv/${runId}/`)
        .then(response => {
            if (!response.ok) throw new Error('Ошибка загрузки CSV');
            return response.text();
        })
        .then(csvText => {
            currentCSV = csvText;
            const filter = document.getElementById('step-status-filter').value;
            const html = csvToHtmlTable(csvText, filter);
            tableDiv.innerHTML = html;
            tableDiv.style.display = 'block';
            document.getElementById('status-filter-container').style.display = 'flex';
            tableDiv.scrollIntoView({ behavior: 'smooth' });
        })
        .catch(error => {
            tableDiv.innerHTML = '<div class="text-danger">Не удалось загрузить результаты</div>';
            tableDiv.style.display = 'block';
        });
}

function csvToHtmlTable(csv, statusFilter = 'all') {
    const lines = csv.trim().split('\n');
    if (lines.length < 2) return '<p>Нет данных</p>';

    function parseCSVLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            if (char === '"' && !inQuotes) {
                inQuotes = true;
            } else if (char === '"' && inQuotes) {
                if (i + 1 < line.length && line[i + 1] === '"') {
                    current += '"';
                    i++;
                } else {
                    inQuotes = false;
                }
            } else if (char === ',' && !inQuotes) {
                result.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }
        result.push(current.trim());
        return result;
    }

    const headers = parseCSVLine(lines[0]);
    let statusIndex = headers.indexOf('Step Status');
    if (statusIndex === -1) statusIndex = headers.findIndex(h => h.includes('Step Status'));

    let html = '<table class="table table-bordered table-sm">';
    html += '<thead><tr>';
    headers.forEach(h => html += `<th>${h}</th>`);
    html += '</tr></thead><tbody>';

    for (let i = 1; i < lines.length; i++) {
        const cols = parseCSVLine(lines[i]);
        if (cols.length === headers.length) {
            // Фильтрация по статусу шага
            if (statusFilter !== 'all' && statusIndex !== -1) {
                const stepStatus = cols[statusIndex].toLowerCase().trim();
                if (stepStatus !== statusFilter) continue;
            }

            let rowClass = '';
            if (statusIndex !== -1 && cols[statusIndex]) {
                const status = cols[statusIndex].toLowerCase().trim();
                if (status === 'passed') rowClass = 'tr-passed';
                else if (status === 'failed') rowClass = 'tr-failed';
                else if (status === 'error') rowClass = 'tr-error';
                else if (status === 'skipped') rowClass = 'tr-skipped';
            }
            html += `<tr class="${rowClass}">`;
            cols.forEach(col => html += `<td>${col}</td>`);
            html += '</tr>';
        }
    }
    html += '</tbody></table>';
    return html;
}

function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
            return cookie.substring(name.length + 1);
        }
    }
    return '';
}

// ---------- История запусков ----------
let currentStatusFilter = 'all';

function loadHistory(status = null) {
    if (status === null) {
        status = currentStatusFilter;
    } else {
        currentStatusFilter = status;
    }

    fetch(`/get-history/?status=${status}`)
        .then(r => r.json())
        .then(runs => {
            const container = document.getElementById('history-list');
            container.innerHTML = '';
            runs.forEach(run => {
                const statusClass = {
                    'completed': 'list-group-item-success',
                    'failed': 'list-group-item-danger',
                    'running': 'list-group-item-warning',
                    'pending': 'list-group-item-secondary'
                }[run.status] || '';

                const item = document.createElement('a');
                item.className = `list-group-item list-group-item-action ${statusClass}`;
                item.href = '#';
                item.style.cursor = 'pointer';
                item.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <span>
                            <strong>${run.status.toUpperCase()}</strong> — ${run.run_type}
                            (${run.started_at ? new Date(run.started_at).toLocaleString() : 'N/A'})
                        </span>
                        <span>
                            ${run.csv_url ? `<button class="btn btn-sm btn-outline-primary download-btn" data-csv-url="${run.csv_url}">Скачать CSV</button>` : ''}
                        </span>
                    </div>
                `;

                item.addEventListener('click', (e) => {
                    if (e.target.closest('.download-btn')) return;
                    e.preventDefault();
                    const resultTableDiv = document.getElementById('result-table');
                    loadCSVTable(run.id, resultTableDiv);
                });

                const downloadBtn = item.querySelector('.download-btn');
                if (downloadBtn) {
                    downloadBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        window.open(e.target.dataset.csvUrl, '_blank');
                    });
                }

                container.appendChild(item);
            });
        })
        .catch(err => console.error('Ошибка загрузки истории', err));
}

// Обработчик изменения фильтра шагов
document.getElementById('step-status-filter').addEventListener('change', function() {
    if (currentCSV) {
        const tableDiv = document.getElementById('result-table');
        const html = csvToHtmlTable(currentCSV, this.value);
        tableDiv.innerHTML = html;
    }
});

// Обработчик изменения фильтра истории
document.getElementById('history-status-filter').addEventListener('change', function() {
    loadHistory(this.value);
});

document.addEventListener('DOMContentLoaded', () => {
    loadHistory('all');
});