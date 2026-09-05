// Enhanced Chart Functions with Better Visualization
// Add to static/student-dashboard.js

// Store chart instances for management
if (!window.miniChartInstances) {
    window.miniChartInstances = {};
}

function renderMiniChartEnhanced(disorder, history) {
    if (!window.miniChartInstances) {
        window.miniChartInstances = {};
    }
    
    const ctx = document.getElementById(disorder + 'Chart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (window.miniChartInstances[disorder]) {
        window.miniChartInstances[disorder].destroy();
    }
    
    // Prepare data
    const labels = history.map((_, i) => `Attempt ${i + 1}`);
    const scores = history.map(h => h.score || 0);
    
    // Calculate trend line
    const trendData = calculateTrendLine(scores);
    
    console.log(`Chart for ${disorder}:`, {
        scores,
        trendData,
        historyLength: history.length
    });
    
    // Create enhanced chart with gradient and disorder-specific colors
    const disorderColors = {
        dyslexia: { primary: '#FF6B6B', light: 'rgba(255, 107, 107, 0.3)', trend: '#FFA07A' },
        dyscalculia: { primary: '#4ECDC4', light: 'rgba(78, 205, 196, 0.3)', trend: '#45B7AA' },
        dysgraphia: { primary: '#95E1D3', light: 'rgba(149, 225, 211, 0.3)', trend: '#7FDBCA' }
    };
    
    const colors = disorderColors[disorder] || { primary: '#4facfe', light: 'rgba(79, 172, 254, 0.3)', trend: 'rgba(255, 152, 0, 0.6)' };
    
    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, colors.light);
    gradient.addColorStop(1, 'rgba(79, 172, 254, 0.05)');
    
    window.miniChartInstances[disorder] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Assessment Score',
                    data: scores,
                    borderColor: colors.primary,
                    backgroundColor: gradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointBackgroundColor: colors.primary,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointHoverBackgroundColor: colors.trend,
                    segment: {
                        borderDash: ctx => ctx.p0DataIndex === ctx.p1DataIndex - 1 ? [0] : [5, 5]
                    }
                },
                {
                    label: 'Trend',
                    data: trendData,
                    borderColor: colors.trend,
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0,
                    borderDash: [5, 5],
                    pointHoverRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#1a1a2e',
                        font: {
                            size: 12,
                            weight: '600'
                        },
                        padding: 12,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        boxWidth: 8
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(26, 26, 46, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#e0e7ff',
                    borderColor: colors.primary,
                    borderWidth: 2,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y.toFixed(1) + '%';
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(200, 200, 200, 0.15)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#666',
                        font: {
                            size: 11
                        },
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        color: '#666',
                        font: {
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

function calculateTrendLine(scores) {
    if (scores.length < 2) return scores;
    
    // Simple linear regression
    const n = scores.length;
    const sumX = (n * (n - 1)) / 2;
    const sumY = scores.reduce((a, b) => a + b, 0);
    const sumXY = scores.reduce((sum, y, i) => sum + i * y, 0);
    const sumX2 = scores.reduce((sum, _, i) => sum + i * i, 0);
    
    const denominator = n * sumX2 - sumX * sumX;
    if (denominator === 0) return scores;
    
    const slope = (n * sumXY - sumX * sumY) / denominator;
    const intercept = (sumY - slope * sumX) / n;
    
    const trendData = scores.map((_, i) => {
        const value = slope * i + intercept;
        return Math.round(value * 10) / 10; // Round to 1 decimal place
    });
    
    return trendData;
}

// Enhanced performance chart
function renderPerformanceChartEnhanced(history) {
    if (window.performanceChartInstance) {
        window.performanceChartInstance.destroy();
    }
    
    const ctx = document.getElementById('performanceChart');
    if (!ctx) return;
    
    const labels = history.map(h => new Date(h.date).toLocaleDateString());
    const scores = history.map(h => h.score || 0);
    
    // Create gradient
    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(79, 172, 254, 0.5)');
    gradient.addColorStop(1, 'rgba(79, 172, 254, 0.05)');
    
    window.performanceChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Assessment Performance',
                data: scores,
                borderColor: '#4facfe',
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 7,
                pointHoverRadius: 9,
                pointBackgroundColor: '#4facfe',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#cbd5e1',
                        font: { size: 13, weight: '600' },
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 24, 35, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: 'rgba(79, 172, 254, 0.3)',
                    borderWidth: 1,
                    padding: 12
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(79, 172, 254, 0.1)' },
                    ticks: {
                        color: '#94a3b8',
                        font: { size: 12 },
                        callback: function(value) { return value + '%'; }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8', font: { size: 12 } }
                }
            }
        }
    });
}
