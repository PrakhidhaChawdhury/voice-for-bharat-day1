from flask import Flask, jsonify, render_template_string
import db

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raksha Telemetry & Analytics</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {
            box-sizing: border-box;
        }

        :root {
            --bg-base: #0b0f19;
            --panel-bg: rgba(17, 24, 39, 0.65);
            --panel-border: rgba(255, 255, 255, 0.07);
            --text-main: #f8fafc;
            --text-muted: #8b9bb4;
            --accent-brand: #818cf8;
            --neon-emerald: #00f2c3;
            --soft-rose: #f43f5e;
        }
        
        body { 
            font-family: 'Inter', sans-serif; 
            background-color: var(--bg-base);
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(244, 63, 94, 0.08) 0px, transparent 50%),
                radial-gradient(rgba(255, 255, 255, 0.025) 1px, transparent 1px);
            background-size: 100% 100%, 100% 100%, 20px 20px;
            color: var(--text-main); 
            margin: 0;
            padding: 24px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .dashboard-container {
            max-width: 1100px;
            width: 100%;
            margin: 0 auto;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--panel-border);
        }

        .header-title {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.4rem;
            font-weight: 700;
        }

        .status-pill {
            background: rgba(0, 242, 195, 0.08);
            color: var(--neon-emerald);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            border: 1px solid rgba(0, 242, 195, 0.2);
            letter-spacing: 0.5px;
        }
        .status-pill::before { 
            content: ""; width: 8px; height: 8px; background: var(--neon-emerald); border-radius: 50%; box-shadow: 0 0 10px var(--neon-emerald);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 24px;
        }

        .panel {
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 20px;
            padding: 24px;
            backdrop-filter: blur(20px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        }

        .stat-card {
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .stat-card h2 { margin: 0 0 6px 0; font-size: 3rem; font-weight: 800; letter-spacing: -1px; }
        .stat-card p { margin: 0; color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 700;}
        
        .main-grid {
            display: grid;
            grid-template-columns: 1.8fr 1.2fr;
            gap: 24px;
        }

        .chart-wrapper {
            position: relative;
            height: 280px;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .legend-container {
            display: flex;
            justify-content: center;
            gap: 24px;
            margin-top: 10px;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.8rem;
            color: var(--text-muted);
            font-weight: 600;
        }
        .legend-dot { width: 10px; height: 10px; border-radius: 50%; }

        /* Diagnostics Sidebar */
        .diag-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid var(--panel-border);
        }
        .diag-item:last-child { border-bottom: none; }
        .diag-label { color: var(--text-muted); font-size: 0.85rem; font-weight: 500; }
        .diag-val { font-family: monospace; font-size: 0.82rem; color: var(--accent-brand); background: rgba(129, 140, 248, 0.1); padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(129, 140, 248, 0.15);}

        /* Color Accents matching Ring Slices */
        #total { color: #f8fafc; }
        #success { color: var(--neon-emerald); text-shadow: 0 0 20px rgba(0, 242, 195, 0.35); }
        #failed { color: var(--soft-rose); text-shadow: 0 0 20px rgba(244, 63, 94, 0.35); }
        #rate { color: var(--accent-brand); text-shadow: 0 0 20px rgba(129, 140, 248, 0.35); }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header">
            <div class="header-title">
                <span style="font-size: 1.6rem;">🛡️</span> Raksha Command Center
            </div>
            <div class="status-pill">SYSTEM ONLINE & SECURE</div>
        </div>
        
        <div class="stats-grid">
            <div class="panel stat-card"><h2 id="total">-</h2><p>Total Sessions</p></div>
            <div class="panel stat-card"><h2 id="success">-</h2><p>Resolved</p></div>
            <div class="panel stat-card"><h2 id="failed">-</h2><p>Dropped / Incomplete</p></div>
            <div class="panel stat-card"><h2 id="rate">-</h2><p>Resolution Rate</p></div>
        </div>

        <div class="main-grid">
            <div class="panel">
                <p style="margin: 0 0 16px 0; color: var(--text-muted); font-weight: 700; letter-spacing: 1px; font-size: 0.75rem;">SESSION OUTCOME DISTRIBUTION</p>
                <div class="chart-wrapper">
                    <canvas id="analyticsChart"></canvas>
                </div>
                <div class="legend-container">
                    <div class="legend-item">
                        <div class="legend-dot" style="background: var(--neon-emerald); box-shadow: 0 0 8px var(--neon-emerald);"></div>
                        Resolved
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot" style="background: var(--soft-rose); box-shadow: 0 0 8px var(--soft-rose);"></div>
                        Incomplete / Dropped
                    </div>
                </div>
            </div>

            <div class="panel">
                <p style="margin: 0 0 12px 0; color: var(--text-muted); font-weight: 700; letter-spacing: 1px; font-size: 0.75rem;">SYSTEM DIAGNOSTICS</p>
                <div class="diag-item"><span class="diag-label">Language Model</span><span class="diag-val">gemini-3.5-flash-lite</span></div>
                <div class="diag-item"><span class="diag-label">TTS Engine</span><span class="diag-val">murf-falcon</span></div>
                <div class="diag-item"><span class="diag-label">STT Engine</span><span class="diag-val">deepgram-nova-3</span></div>
                <div class="diag-item"><span class="diag-label">Turn Detection</span><span class="diag-val">silero-vad</span></div>
                <div class="diag-item"><span class="diag-label">Orchestration</span><span class="diag-val">livekit-rtc</span></div>
                <div class="diag-item"><span class="diag-label">PII Sanitization</span><span class="diag-val" style="color:var(--neon-emerald); background: rgba(0,242,195,0.1); border-color: rgba(0,242,195,0.2);">Active (Regex)</span></div>
            </div>
        </div>
    </div>

    <script>
        // Custom Plugin: Renders the glowing center metric
        const centerTextPlugin = {
            id: 'centerText',
            beforeDraw: function(chart) {
                var width = chart.width, height = chart.height, ctx = chart.ctx;
                ctx.restore();
                
                var data = chart.data.datasets[0].data;
                var total = data[0] + data[1];
                var rate = total > 0 ? Math.round((data[0] / total) * 100) : 0;
                
                ctx.font = "800 3.2rem Inter";
                ctx.textBaseline = "middle";
                ctx.fillStyle = "#f8fafc";
                var text = rate + "%", textX = Math.round((width - ctx.measureText(text).width) / 2), textY = height / 2 - 8;
                ctx.fillText(text, textX, textY);
                
                ctx.font = "700 0.75rem Inter";
                ctx.fillStyle = "#8b9bb4";
                var subText = "SUCCESS RATE";
                var subX = Math.round((width - ctx.measureText(subText).width) / 2);
                ctx.fillText(subText, subX, textY + 32);
                ctx.save();
            }
        };

        // Custom Plugin: Draws an Apple-style subtle background ring track
        const backgroundTrackPlugin = {
            id: 'backgroundTrack',
            beforeDatasetsDraw: function(chart) {
                const {ctx, chartArea: {top, bottom, left, right}} = chart;
                const x = (left + right) / 2;
                const y = (top + bottom) / 2;
                const outerRadius = chart.getDatasetMeta(0).data[0]?.outerRadius || 100;
                const innerRadius = chart.getDatasetMeta(0).data[0]?.innerRadius || 80;
                const radius = (outerRadius + innerRadius) / 2;
                const thickness = outerRadius - innerRadius;

                ctx.save();
                ctx.beginPath();
                ctx.arc(x, y, radius, 0, 2 * Math.PI);
                ctx.lineWidth = thickness;
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
                ctx.stroke();
                ctx.restore();
            }
        };

        let chart;
        async function fetchStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                document.getElementById('total').innerText = data.total;
                document.getElementById('success').innerText = data.success;
                document.getElementById('failed').innerText = data.failed;
                
                const rate = data.total > 0 ? Math.round((data.success / data.total) * 100) : 0;
                document.getElementById('rate').innerText = rate + '%';

                if (!chart) {
                    const ctx = document.getElementById('analyticsChart').getContext('2d');
                    
                    // Smooth Emerald Gradient for Success
                    const successGradient = ctx.createLinearGradient(0, 0, 0, 300);
                    successGradient.addColorStop(0, '#00f2c3');
                    successGradient.addColorStop(1, '#10b981');

                    // Soft Rose Gradient for Incomplete
                    const roseGradient = ctx.createLinearGradient(0, 0, 0, 300);
                    roseGradient.addColorStop(0, '#fb7185');
                    roseGradient.addColorStop(1, '#e11d48');

                    chart = new Chart(ctx, {
                        type: 'doughnut',
                        plugins: [backgroundTrackPlugin, centerTextPlugin],
                        data: {
                            labels: ['Resolved', 'Incomplete'],
                            datasets: [{ 
                                data: [data.success, data.failed], 
                                backgroundColor: [successGradient, roseGradient], 
                                hoverBackgroundColor: ['#00f2c3', '#fb7185'],
                                borderWidth: 0,
                                borderRadius: 12,
                                spacing: 6
                            }]
                        },
                        options: { 
                            responsive: true, 
                            maintainAspectRatio: false,
                            cutout: '82%',
                            plugins: { 
                                legend: { display: false },
                                tooltip: {
                                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                    titleFont: { family: 'Inter', size: 13, weight: '700' },
                                    bodyFont: { family: 'Inter', size: 12 },
                                    padding: 12,
                                    cornerRadius: 10,
                                    borderColor: 'rgba(255, 255, 255, 0.1)',
                                    borderWidth: 1,
                                    displayColors: true
                                }
                            } 
                        }
                    });
                } else {
                    chart.data.datasets[0].data = [data.success, data.failed];
                    chart.update();
                }
            } catch (err) {
                console.error("Error fetching stats:", err);
            }
        }
        
        setInterval(fetchStats, 2000);
        fetchStats();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/stats")
def stats():
    return jsonify(db.get_call_stats())

if __name__ == "__main__":
    db.init_db()
    print("🚀 Dashboard running at http://127.0.0.1:5000")
    app.run(port=5000)