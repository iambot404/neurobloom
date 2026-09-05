// Student Dashboard JavaScript
// Extracted from student-dashboard.html for maintainability

let isLoadingDashboard = false;
let autoRefreshInterval = null;
const AUTO_REFRESH_INTERVAL = 15000; // Refresh every 15 seconds

document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    setupTabNavigation();
    setupEventListeners();
    startAutoRefresh();
});

document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        stopAutoRefresh();
    } else {
        startAutoRefresh();
        loadDashboardData();
    }
});

function startAutoRefresh() {
    if (autoRefreshInterval) return;
    autoRefreshInterval = setInterval(() => {
        loadDashboardData();
    }, AUTO_REFRESH_INTERVAL);
    console.log('Dashboard auto-refresh started (every 15 seconds)');
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
        console.log('Dashboard auto-refresh stopped');
    }
}

function loadDashboardData() {
    if (isLoadingDashboard) return;
    isLoadingDashboard = true;
    showLoadingState(true);

    fetch('/api/student/dashboard')
        .then(r => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
        })
        .then(data => {
            if (data.status === 'ok') {
                updateQuickStats(data);
                // Get selected disorder filter from the hidden select elements (check all three)
                const overviewFilter = document.getElementById('overviewFilter')?.value || '';
                const disorderFilter = document.getElementById('disorderFilter')?.value || '';
                const recommendationFilter = document.getElementById('recommendationDisorderFilter')?.value || '';
                const currentFilter = overviewFilter || disorderFilter || recommendationFilter || '';
                
                // Filter recent and history by disorder - convert both to lowercase for comparison
                // For recent: if filtering, show the most recent items of that type from history
                let filteredRecent;
                if (currentFilter) {
                    const filteredByType = (data.history || []).filter(h => 
                        (h.disorder_type || '').toLowerCase().trim() === currentFilter.toLowerCase().trim()
                    );
                    filteredRecent = filteredByType.slice(0, 5); // Take most recent 5 of this type
                } else {
                    filteredRecent = data.recent || [];
                }
                
                const filteredHistory = currentFilter ? (data.history || []).filter(h => 
                    (h.disorder_type || '').toLowerCase().trim() === currentFilter.toLowerCase().trim()
                ) : (data.history || []);
                
                updateRecentAssessments(filteredRecent);
                updateAssessmentHistory(filteredHistory);
                updateProgressMetrics(data.progress);
                // Filter recommendations by selected disorder
                const filteredRecommendations = currentFilter ? (data.recommendations || []).filter(r => 
                    (r.disorder || '').toLowerCase().trim() === currentFilter.toLowerCase().trim()
                ) : (data.recommendations || []);
                updateRecommendations(filteredRecommendations);
                if (filteredRecent && filteredRecent.length > 0) {
                    renderPerformanceChartEnhanced(filteredHistory);
                }
            } else {
                console.error('API returned error:', data);
                showErrorMessage(data.error || 'Failed to load dashboard data');
            }
        })
        .catch(err => {
            console.error('Error loading dashboard:', err);
            showErrorMessage('Unable to load dashboard. Please refresh the page. (' + err.message + ')');
        })
        .finally(() => {
            isLoadingDashboard = false;
            showLoadingState(false);
            updateLastUpdateTime();
        });
}

function showLoadingState(show) {
    const statsContainer = document.querySelector('.quick-stats');
    if (statsContainer) {
        statsContainer.style.opacity = show ? '0.6' : '1';
        statsContainer.style.pointerEvents = show ? 'none' : 'auto';
    }
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        if (show) {
            refreshBtn.style.animation = 'spin 1s linear infinite';
            refreshBtn.style.cursor = 'not-allowed';
        } else {
            refreshBtn.style.animation = 'none';
            refreshBtn.style.cursor = 'pointer';
        }
    }
}

function updateQuickStats(data) {
    document.getElementById('totalAssessments').textContent = data.stats.total_assessments;
    document.getElementById('avgScore').textContent = (data.stats.average_score || 0).toFixed(1) + '%';
    document.getElementById('overallRisk').textContent = data.stats.overall_risk || '-';
    document.getElementById('latestTest').textContent = data.stats.latest_disorder || '-';
}

function updateRecentAssessments(recent) {
    const container = document.getElementById('recentAssessments');
    if (!recent || recent.length === 0) {
        container.innerHTML = '<p class="empty-state">No assessments yet.</p>';
        return;
    }
    container.innerHTML = recent.map(a => `
        <div class="recent-item ${a.status === 'in_progress' ? 'in-progress' : ''}" onclick="viewAssessmentDetails(${a.id})">
            <div class="recent-header">
                <span class="disorder-badge">${a.disorder_type || 'Unknown'}</span>
                <span class="status-badge status-${a.status || 'unknown'}">${(a.status === 'in_progress' ? 'In Progress' : 'Completed').toUpperCase()}</span>
                <span class="date">${a.date ? new Date(a.date).toLocaleDateString() : 'N/A'}</span>
            </div>
            <div class="recent-score">
                ${a.score !== null && a.score !== undefined ? 
                    `<span class="score-value">${a.score}%</span>
                     <span class="risk-badge ${(a.risk_level || 'medium').toLowerCase()}">${a.risk_level || 'Medium'}</span>` :
                    `<span class="score-value">-</span>
                     <span class="risk-badge pending">Pending</span>`
                }
            </div>
        </div>
    `).join('');
}

function updateAssessmentHistory(history) {
    const container = document.getElementById('assessmentHistory');
    if (!history || history.length === 0) {
        container.innerHTML = '<p class="empty-state">No assessments found.</p>';
        return;
    }
    container.innerHTML = history.map(h => `
        <div class="history-item ${h.status === 'in_progress' ? 'in-progress' : ''}" onclick="viewAssessmentDetails(${h.id})">
            <div class="history-left">
                <div class="disorder-type">${h.disorder_type || 'Unknown'}</div>
                <div class="date-time">
                    ${h.date ? new Date(h.date).toLocaleString() : 'N/A'}
                    <span class="status-badge-small status-${h.status || 'unknown'}">${(h.status === 'in_progress' ? 'In Progress' : 'Completed').toUpperCase()}</span>
                </div>
            </div>
            <div class="history-right">
                ${h.score !== null && h.score !== undefined ? 
                    `<div class="score">${h.score}%</div>
                     <div class="risk ${(h.risk_level || 'medium').toLowerCase()}">${h.risk_level || 'Medium'}</div>` :
                    `<div class="score">-</div>
                     <div class="risk pending">Pending</div>`
                }
            </div>
        </div>
    `).join('');
}

function updateProgressMetrics(progress) {
    const disorders = ['dyslexia', 'dyscalculia', 'dysgraphia'];
    disorders.forEach(disorder => {
        const p = progress[disorder] || {};
        document.getElementById(`${disorder}Attempts`).textContent = p.attempts || 0;
        document.getElementById(`${disorder}Avg`).textContent = p.average_score ? (p.average_score).toFixed(1) + '%' : '-';
        document.getElementById(`${disorder}Risk`).textContent = p.risk_level || '-';
        if (p.history && p.history.length > 0) {
            renderMiniChartEnhanced(disorder, p.history);
        }
    });
}

function updateRecommendations(recommendations) {
    const container = document.getElementById('recommendationsDisplay');
    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p class="empty-state">No recommendations available.</p>';
        return;
    }
    container.innerHTML = recommendations.map(r => `
        <div class="recommendation-card ${r.risk_class || 'medium'}">
            <div class="rec-header">
                <div class="rec-number">${r.index || '·'}</div>
                <span class="risk-indicator">${r.indicator || '📌'}</span>
            </div>
            <h4>${r.title || 'Recommendation'}</h4>
            <p>${r.description || 'No description available'}</p>
            <div class="rec-meta">
                <span class="disorder">${r.disorder || '-'}</span>
                <span class="date">${r.date ? new Date(r.date).toLocaleDateString() : '-'}</span>
            </div>
        </div>
    `).join('');
}

function setupTabNavigation() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabName + '-tab').classList.add('active');
            this.classList.add('active');
        });
    });
}

function setupEventListeners() {
    document.getElementById('takeAssessmentBtn').addEventListener('click', () => {
        window.location.href = '/assessments';
    });
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadDashboardData();
        });
    }
    
    // Handle filter button clicks for all tabs
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const filterContainer = this.closest('.history-filters, .filter-select-container, .overview-filters, .progress-filters');
            if (!filterContainer) return;
            
            // Remove active class from all buttons in this container
            filterContainer.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('filter-btn-active'));
            
            // Add active class to clicked button
            this.classList.add('filter-btn-active');
            
            // Update the hidden select element in this container
            const filterValue = this.dataset.filter === 'all' ? '' : this.dataset.filter;
            const selectEl = filterContainer.querySelector('.filter-select');
            if (selectEl) {
                selectEl.value = filterValue;
            }
            
            // Sync all other filter selects
            const allSelects = document.querySelectorAll('.filter-select');
            allSelects.forEach(select => {
                select.value = filterValue;
            });
            
            // Update all filter buttons to reflect the new selection
            document.querySelectorAll('.filter-btn').forEach(b => {
                const btnFilter = b.dataset.filter === 'all' ? '' : b.dataset.filter;
                if (btnFilter === filterValue) {
                    b.classList.add('filter-btn-active');
                } else {
                    b.classList.remove('filter-btn-active');
                }
            });
            
            // Trigger data load with the new filter
            loadDashboardData();
        });
    });
    
    // Keep the old select change handlers for backwards compatibility
    const overviewFilter = document.getElementById('overviewFilter');
    const disorderFilter = document.getElementById('disorderFilter');
    const recommendationFilter = document.getElementById('recommendationDisorderFilter');
    
    const syncFilters = (value) => {
        if (overviewFilter) overviewFilter.value = value;
        if (disorderFilter) disorderFilter.value = value;
        if (recommendationFilter) recommendationFilter.value = value;
    };
    
    if (overviewFilter) {
        overviewFilter.addEventListener('change', function() {
            syncFilters(this.value);
            loadDashboardData();
        });
    }
    
    if (disorderFilter) {
        disorderFilter.addEventListener('change', function() {
            syncFilters(this.value);
            loadDashboardData();
        });
    }
    
    if (recommendationFilter) {
        recommendationFilter.addEventListener('change', function() {
            syncFilters(this.value);
            loadDashboardData();
        });
    }
}

function updateLastUpdateTime() {
    const timeEl = document.getElementById('lastUpdateTime');
    if (timeEl) {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        timeEl.textContent = timeString;
    }
}

function viewAssessmentDetails(assessmentId) {
    fetch(`/api/student/assessment/${assessmentId}`)
        .then(r => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
        })
        .then(data => {
            if (data.status === 'ok') {
                showAssessmentModal(data.assessment);
            } else {
                showErrorMessage('Failed to load assessment details');
            }
        })
        .catch(err => {
            console.error('Error loading assessment:', err);
            showErrorMessage('Error loading assessment details. Please try again.');
        });
}

function showAssessmentModal(assessment) {
    const modal = document.getElementById('assessmentModal');
    const content = document.getElementById('assessmentModalContent');
    const recommendationsHtml = assessment.recommendations && assessment.recommendations.length > 0
        ? assessment.recommendations.map((r, i) => `
            <div class="rec-item">
                <span class="rec-index">${i + 1}</span>
                <p>${r.recommendation_text || r}</p>
            </div>
        `).join('')
        : '<p class="empty-state">No recommendations available for this assessment.</p>';
    content.innerHTML = `
        <h2>${assessment.disorder_type} Assessment</h2>
        <div class="modal-body">
            <div class="assessment-meta">
                <div class="meta-item">
                    <label>Date:</label>
                    <span>${new Date(assessment.date).toLocaleString()}</span>
                </div>
                <div class="meta-item">
                    <label>Score:</label>
                    <span>${assessment.score}%</span>
                </div>
                <div class="meta-item">
                    <label>Risk Level:</label>
                    <span class="risk-badge ${assessment.risk_level.toLowerCase()}">${assessment.risk_level}</span>
                </div>
            </div>
            <div class="recommendations-section">
                <h3>Recommendations</h3>
                <div class="recs-list">
                    ${recommendationsHtml}
                </div>
            </div>
        </div>
    `;
    modal.style.display = 'block';
    document.querySelector('#assessmentModal .modal-close').onclick = () => modal.style.display = 'none';
}

function showErrorMessage(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #ef4444; color: white; padding: 12px 20px; border-radius: 6px; z-index: 10000;';
    document.body.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
}

function renderPerformanceChart(history) {
    // Delegate to enhanced version
    renderPerformanceChartEnhanced(history);
}function renderMiniChart(disorder, history) {
    // Delegate to enhanced version
    renderMiniChartEnhanced(disorder, history);
}
