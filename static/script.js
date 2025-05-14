let tokens = [];
let predictions = [];
let grammarContext = '';
let reasoning = {};
let lastRequestTime = 0;
const COOLDOWN = 3000; // 3 seconds
let heatmapChart = null;
let canvas = null;
let isProcessing = false;

function windowResized() {
    if (canvas) {
        resizeCanvas(windowWidth * 0.8, 600);
    }
}

function setup() {
    console.log('Setup called');
    const container = document.getElementById('canvasContainer');
    if (!container) {
        console.error('Canvas container not found');
        return;
    }
    canvas = createCanvas(windowWidth * 0.8, 600);
    canvas.parent('canvasContainer');
    textSize(16);
}

function draw() {
    if (!canvas) return;
    
    background(255);
    if (tokens.length > 0) {
        for (let i = 0; i < tokens.length; i++) {
            textAlign(CENTER);
            fill(0);
            text(tokens[i], 100 + i * 100, 200);
        }
        for (let p = 0; p < predictions.length; p++) {
            const pred = predictions[p];
            if (!pred || !pred.attention) continue;
            
            const predX = 100 + tokens.length * 100;
            const predY = 300 + p * 60;
            textAlign(CENTER);
            fill(0);
            text(pred.word, predX, predY);
            textAlign(LEFT);
            fill(100);
            text(`${(pred.confidence * 100).toFixed(1)}%`, predX + 50, predY);
            
            for (let i = 0; i < tokens.length; i++) {
                const weight = pred.attention[i] || 0;
                strokeWeight(Math.max(weight * 5, 0.5));
                stroke(0, 0, 255, weight * 255);
                line(predX, predY + 10, 100 + i * 100, 200);
            }
        }
    }
}

function updateHeatmap() {
    const ctx = document.getElementById('heatmapChart').getContext('2d');
    if (heatmapChart) heatmapChart.destroy();
    const labels = predictions.map(p => p.word);
    const data = predictions.map(p => p.confidence * 100);
    heatmapChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Prediction Confidence',
                data: data,
                backgroundColor: data.map(value => `rgba(76, 175, 80, ${value / 100})`),
                borderColor: 'rgba(76, 175, 80, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: { display: true, text: 'Confidence (%)' }
                }
            }
        }
    });
}

function updateContextClues() {
    const contextDiv = document.getElementById('contextClues');
    if (predictions.length > 0) {
        let contextText = '<strong>Context Analysis:</strong><br>';
        
        // Add grammar context
        contextText += `<div class="analysis-section">
            <h4>Grammar Context</h4>
            <p>${grammarContext}</p>
        </div>`;

        // Add reasoning if available
        if (reasoning) {
            contextText += `<div class="analysis-section">
                <h4>Detailed Analysis</h4>
                <p><strong>Syntactic Analysis:</strong> ${reasoning.syntactic_analysis || 'Not available'}</p>
                <p><strong>Semantic Context:</strong> ${reasoning.semantic_context || 'Not available'}</p>
                <p><strong>Common Patterns:</strong> ${reasoning.common_patterns || 'Not available'}</p>
            </div>`;
        }

        // Add prediction-specific reasoning
        contextText += '<div class="analysis-section"><h4>Prediction Reasoning</h4>';
        predictions.forEach((pred, index) => {
            if (pred.reasoning) {
                contextText += `<p><strong>${pred.word}:</strong> ${pred.reasoning}</p>`;
            }
        });
        contextText += '</div>';

        // Add attention analysis
        const topPred = predictions[0];
        if (topPred && topPred.attention) {
            const maxAttentionIndex = topPred.attention.indexOf(Math.max(...topPred.attention));
            contextText += `<div class="analysis-section">
                <h4>Attention Analysis</h4>
                <p>Most attention on word "${tokens[maxAttentionIndex]}"</p>
            </div>`;
        }

        contextDiv.innerHTML = contextText;
    } else {
        contextDiv.innerHTML = '';
    }
}

function useExample(phrase) {
    document.getElementById('phraseInput').value = phrase;
    predictAndVisualize();
}

async function predictAndVisualize() {
    if (isProcessing) {
        return;
    }

    console.log('Predict called');
    const predictBtn = document.getElementById('predictBtn');
    const predictionDiv = document.getElementById('prediction');
    const now = Date.now();

    if (now - lastRequestTime < COOLDOWN) {
        const waitTime = Math.ceil((COOLDOWN - (now - lastRequestTime)) / 1000);
        predictionDiv.innerText = `Please wait ${waitTime} seconds before trying again`;
        return;
    }

    isProcessing = true;
    predictBtn.disabled = true;
    predictionDiv.innerText = 'Predicting...';
    const input = document.getElementById('phraseInput').value;

    if (!input.trim()) {
        predictionDiv.innerText = 'Please enter a phrase';
        predictBtn.disabled = false;
        isProcessing = false;
        return;
    }

    tokens = input.split(' ').filter(Boolean);
    console.log('Tokens:', tokens);
    predictionDiv.innerHTML = '';

    try {
        lastRequestTime = Date.now();
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ phrase: input })
        });

        // First check if the response is ok
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Server error:', errorText);
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }

        // Then try to parse as JSON
        const data = await response.json();
        console.log('Received data:', data);
        
        if (!data.response) {
            throw new Error('No response data received from server');
        }

        let resultJson;
        try {
            resultJson = JSON.parse(data.response);
        } catch (e) {
            console.error('JSON parse failed:', e);
            console.error('Raw response:', data.response);
            throw new Error('Invalid response format from API');
        }

        predictions = resultJson.predictions || [];
        grammarContext = resultJson.grammar_context || 'No grammar context provided.';
        reasoning = resultJson.reasoning || {};
        
        console.log('Predictions:', predictions);
        console.log('Grammar Context:', grammarContext);
        console.log('Reasoning:', reasoning);

        if (predictions.length === 0) {
            throw new Error('No predictions received from API');
        }

        predictionDiv.innerHTML = '';
        predictions.forEach(pred => {
            const predItem = document.createElement('div');
            predItem.className = 'prediction-item';
            predItem.innerHTML = `
                <div>${pred.word}</div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${pred.confidence * 100}%"></div>
                </div>
                <div>${(pred.confidence * 100).toFixed(1)}%</div>
            `;
            predictionDiv.appendChild(predItem);
        });

        updateHeatmap();
        updateContextClues();

    } catch (error) {
        console.error('API call failed:', error);
        predictionDiv.innerHTML = `<div class="error-message">Error: ${error.message}</div>`;
        predictions = [];
        grammarContext = '';
        reasoning = {};
        updateHeatmap();
        updateContextClues();
    } finally {
        predictBtn.disabled = false;
        isProcessing = false;
    }
} 