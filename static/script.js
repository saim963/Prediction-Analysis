(function() {
    'use strict';

    // DOM Elements
    const form = document.getElementById('predictionForm');
    const input = document.getElementById('phraseInput');
    const submitBtn = document.getElementById('submitBtn');
    const results = document.getElementById('results');
    const predictionsGrid = document.getElementById('predictionsGrid');
    const chartCard = document.getElementById('chartCard');
    const analysisCard = document.getElementById('analysisCard');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');

    // Chart instance
    let chart = null;

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const phrase = input.value.trim();
        if (!phrase) return;

        setLoading(true);
        hideError();
        hideResults();

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phrase: phrase })
            });

            const data = await response.json();

            if (data.error) {
                showError(data.error);
                return;
            }

            if (data.response) {
                renderResults(data.response);
            } else {
                showError('Invalid response from server');
            }

        } catch (err) {
            showError('Connection failed. Please try again.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    });

    // Render all results
    function renderResults(data) {
        renderPredictions(data.predictions || []);
        renderChart(data.predictions || []);
        renderAnalysis(data);
        showResults();
    }

    // Render prediction cards
    function renderPredictions(predictions) {
        if (!predictions.length) {
            predictionsGrid.innerHTML = '<p style="color: var(--color-text-muted);">No predictions available</p>';
            return;
        }

        predictionsGrid.innerHTML = predictions.map((pred, index) => {
            const percent = (pred.confidence * 100).toFixed(0);
            return `
                <div class="prediction-card">
                    <div class="prediction-rank">${index + 1}</div>
                    <div class="prediction-content">
                        <div class="prediction-word">${escapeHtml(pred.word)}</div>
                        <div class="prediction-reasoning">${escapeHtml(pred.reasoning)}</div>
                    </div>
                    <div class="prediction-confidence">
                        <span class="confidence-value">${percent}%</span>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${percent}%"></div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Render Chart.js bar chart
    function renderChart(predictions) {
        const ctx = document.getElementById('confidenceChart').getContext('2d');

        // Destroy existing chart
        if (chart) {
            chart.destroy();
        }

        const labels = predictions.map(p => p.word);
        const values = predictions.map(p => (p.confidence * 100).toFixed(1));

        chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Confidence %',
                    data: values,
                    backgroundColor: 'rgba(99, 102, 241, 0.8)',
                    borderColor: 'rgba(99, 102, 241, 1)',
                    borderWidth: 0,
                    borderRadius: 6,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 800,
                    easing: 'easeOutQuart'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleFont: {
                            family: "'Inter', sans-serif",
                            size: 13,
                            weight: '600'
                        },
                        bodyFont: {
                            family: "'Inter', sans-serif",
                            size: 12
                        },
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y + '% confidence';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                family: "'Inter', sans-serif",
                                size: 12,
                                weight: '500'
                            },
                            color: '#64748b'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: '#f1f5f9'
                        },
                        ticks: {
                            font: {
                                family: "'Inter', sans-serif",
                                size: 11
                            },
                            color: '#94a3b8',
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    // Render analysis section
    function renderAnalysis(data) {
        const grammarEl = document.querySelector('#grammarContext .analysis-text');
        const syntacticEl = document.querySelector('#syntacticAnalysis .analysis-text');
        const semanticEl = document.querySelector('#semanticContext .analysis-text');
        const patternsEl = document.querySelector('#commonPatterns .analysis-text');

        grammarEl.textContent = data.grammar_context || 'Not available';
        
        if (data.reasoning) {
            syntacticEl.textContent = data.reasoning.syntactic_analysis || 'Not available';
            semanticEl.textContent = data.reasoning.semantic_context || 'Not available';
            patternsEl.textContent = data.reasoning.common_patterns || 'Not available';
        } else {
            syntacticEl.textContent = 'Not available';
            semanticEl.textContent = 'Not available';
            patternsEl.textContent = 'Not available';
        }
    }

    // UI State functions
    function setLoading(loading) {
        submitBtn.classList.toggle('loading', loading);
        submitBtn.disabled = loading;
    }

    function showResults() {
        results.classList.add('visible');
    }

    function hideResults() {
        results.classList.remove('visible');
    }

    function showError(message) {
        errorText.textContent = message;
        errorMessage.classList.add('visible');
    }

    function hideError() {
        errorMessage.classList.remove('visible');
    }

    // Utility: Escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

})();