HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>K4-L3B Day 13 Monitoring & LLMOps Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --success: #4ade80;
      --warning: #facc15;
      --danger: #f87171;
    }
    body {
      margin: 0;
      padding: 24px;
      background-color: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }
    .header h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 700;
      color: var(--text);
    }
    .meta-badges {
      display: flex;
      gap: 12px;
    }
    .badge {
      background: var(--card-bg);
      border: 1px solid var(--border);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 13px;
      color: var(--text-muted);
    }
    .badge b { color: var(--primary); }
    .grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
    }
    @media (max-width: 1200px) {
      .grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 768px) {
      .grid { grid-template-columns: 1fr; }
    }
    .panel {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 18px;
      display: flex;
      flex-direction: column;
    }
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 12px;
    }
    .panel-title {
      font-size: 15px;
      font-weight: 600;
      color: var(--text);
    }
    .panel-unit {
      font-size: 12px;
      color: var(--text-muted);
    }
    .stats-row {
      display: flex;
      gap: 16px;
      margin-bottom: 14px;
      flex-wrap: wrap;
    }
    .stat-item {
      display: flex;
      flex-direction: column;
    }
    .stat-val {
      font-size: 20px;
      font-weight: 700;
      color: var(--primary);
    }
    .stat-label {
      font-size: 11px;
      color: var(--text-muted);
      text-transform: uppercase;
    }
    .chart-container {
      position: relative;
      height: 180px;
      width: 100%;
    }
    .threshold-badge {
      font-size: 11px;
      padding: 2px 6px;
      border-radius: 4px;
      background: rgba(56, 189, 248, 0.1);
      color: var(--primary);
      margin-top: 8px;
      display: inline-block;
    }
  </style>
</head>
<body>

  <div class="header">
    <div>
      <h1>K4-L3B Day 13 Monitoring & LLMOps</h1>
      <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">System Health & LLM Observability Dashboard</div>
    </div>
    <div class="meta-badges">
      <div class="badge">Time Range: <b>Last 60m</b></div>
      <div class="badge">Auto-Refresh: <b>30s</b></div>
      <div class="badge" id="lastUpdatedBadge">Updated: <b>Loading...</b></div>
    </div>
  </div>

  <div class="grid">
    <!-- Panel 1: Latency & TTFT -->
    <div class="panel" id="panel-latency">
      <div class="panel-header">
        <div class="panel-title">1. Latency percentiles and TTFT</div>
        <div class="panel-unit">Unit: ms</div>
      </div>
      <div class="stats-row">
        <div class="stat-item"><span class="stat-val" id="val-p50">-</span><span class="stat-label">P50</span></div>
        <div class="stat-item"><span class="stat-val" id="val-p95">-</span><span class="stat-label">P95</span></div>
        <div class="stat-item"><span class="stat-val" id="val-p99">-</span><span class="stat-label">P99</span></div>
        <div class="stat-item"><span class="stat-val" id="val-ttft">-</span><span class="stat-label">TTFT P95</span></div>
      </div>
      <div class="chart-container"><canvas id="chartLatency"></canvas></div>
      <div class="threshold-badge">Threshold: P95 &le; 3000 ms</div>
    </div>

    <!-- Panel 2: Traffic -->
    <div class="panel" id="panel-traffic">
      <div class="panel-header">
        <div class="panel-title">2. Request traffic</div>
        <div class="panel-unit">Unit: req / min</div>
      </div>
      <div class="stats-row">
        <div class="stat-item"><span class="stat-val" id="val-requests">-</span><span class="stat-label">Total Requests</span></div>
        <div class="stat-item"><span class="stat-val" id="val-rate">-</span><span class="stat-label">Rate / Min</span></div>
      </div>
      <div class="chart-container"><canvas id="chartTraffic"></canvas></div>
      <div class="threshold-badge">Threshold: Rate &ge; 1 req/min</div>
    </div>

    <!-- Panel 3: Errors & Retrieval -->
    <div class="panel" id="panel-errors">
      <div class="panel-header">
        <div class="panel-title">3. Error rate and retrieval success</div>
        <div class="panel-unit">Unit: percent (%)</div>
      </div>
      <div class="stats-row">
        <div class="stat-item"><span class="stat-val" id="val-error-rate">-</span><span class="stat-label">Error Rate</span></div>
        <div class="stat-item"><span class="stat-val" id="val-retrieval-success">-</span><span class="stat-label">Retrieval Success</span></div>
      </div>
      <div class="chart-container"><canvas id="chartErrors"></canvas></div>
      <div class="threshold-badge">Threshold: Error Rate &le; 2.0% | Retrieval &ge; 90.0%</div>
    </div>

    <!-- Panel 4: Cost -->
    <div class="panel" id="panel-cost">
      <div class="panel-header">
        <div class="panel-title">4. Cost over time</div>
        <div class="panel-unit">Unit: USD ($)</div>
      </div>
      <div class="stats-row">
        <div class="stat-item"><span class="stat-val" id="val-cost-total">-</span><span class="stat-label">Total Cost</span></div>
      </div>
      <div class="chart-container"><canvas id="chartCost"></canvas></div>
      <div class="threshold-badge">Threshold: Total &le; $2.50</div>
    </div>

    <!-- Panel 5: Tokens -->
    <div class="panel" id="panel-tokens">
      <div class="panel-header">
        <div class="panel-title">5. Input and output tokens</div>
        <div class="panel-unit">Unit: tokens</div>
      </div>
      <div class="stats-row">
        <div class="stat-item"><span class="stat-val" id="val-tokens-in">-</span><span class="stat-label">Tokens In</span></div>
        <div class="stat-item"><span class="stat-val" id="val-tokens-out">-</span><span class="stat-label">Tokens Out</span></div>
        <div class="stat-item"><span class="stat-val" id="val-tokens-total">-</span><span class="stat-label">Total Tokens</span></div>
      </div>
      <div class="chart-container"><canvas id="chartTokens"></canvas></div>
      <div class="threshold-badge">Threshold: Total &le; 50,000 tokens</div>
    </div>

    <!-- Panel 6: Quality -->
    <div class="panel" id="panel-quality">
      <div class="panel-header">
        <div class="panel-title">6. Quality proxy</div>
        <div class="panel-unit">Unit: score (0 - 1.0)</div>
      </div>
      <div class="stats-row">
        <div class="stat-item"><span class="stat-val" id="val-quality-mean">-</span><span class="stat-label">Mean Quality</span></div>
      </div>
      <div class="chart-container"><canvas id="chartQuality"></canvas></div>
      <div class="threshold-badge">Threshold: Mean &ge; 0.75</div>
    </div>
  </div>

  <script>
    let charts = {};

    async function fetchDashboardData() {
      try {
        const res = await fetch('/dashboard/data');
        const data = await res.json();
        updateUI(data);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      }
    }

    function updateUI(data) {
      const s = data.summary;
      document.getElementById('lastUpdatedBadge').innerHTML = 'Updated: <b>' + new Date().toLocaleTimeString() + '</b>';

      // 1. Latency
      document.getElementById('val-p50').textContent = s.p50 + 'ms';
      document.getElementById('val-p95').textContent = s.p95 + 'ms';
      document.getElementById('val-p99').textContent = s.p99 + 'ms';
      document.getElementById('val-ttft').textContent = s.ttft_p95 + 'ms';

      // 2. Traffic
      document.getElementById('val-requests').textContent = s.total_requests;
      document.getElementById('val-rate').textContent = s.traffic_rate_pm;

      // 3. Errors
      document.getElementById('val-error-rate').textContent = s.error_rate_pct + '%';
      document.getElementById('val-retrieval-success').textContent = s.retrieval_success_rate + '%';

      // 4. Cost
      document.getElementById('val-cost-total').textContent = '$' + s.cost_total.toFixed(4);

      // 5. Tokens
      document.getElementById('val-tokens-in').textContent = s.tokens_in_total.toLocaleString();
      document.getElementById('val-tokens-out').textContent = s.tokens_out_total.toLocaleString();
      document.getElementById('val-tokens-total').textContent = (s.tokens_in_total + s.tokens_out_total).toLocaleString();

      // 6. Quality
      document.getElementById('val-quality-mean').textContent = s.quality_mean.toFixed(2);

      renderCharts(data);
    }

    function renderCharts(data) {
      const ts = data.time_series.slice(-25);
      const labels = ts.map(x => x.ts || 'req');

      // 1. Latency Chart
      renderChart('chartLatency', 'line', labels, [
        { label: 'Latency (ms)', data: ts.map(x => x.latency_ms), borderColor: '#38bdf8', backgroundColor: 'rgba(56, 189, 248, 0.1)', fill: true },
        { label: 'TTFT (ms)', data: ts.map(x => x.ttft_ms), borderColor: '#facc15', borderDash: [4, 4] },
        { label: 'Threshold (3000ms)', data: labels.map(() => 3000), borderColor: '#f87171', borderDash: [6, 4], pointRadius: 0 }
      ]);

      // 2. Traffic Chart
      const trafficLabels = Object.keys(data.traffic_buckets).slice(-15);
      const trafficCounts = trafficLabels.map(k => data.traffic_buckets[k]);
      renderChart('chartTraffic', 'bar', trafficLabels.length ? trafficLabels : labels, [
        { label: 'Requests', data: trafficLabels.length ? trafficCounts : ts.map(() => 1), backgroundColor: '#38bdf8' }
      ]);

      // 3. Errors Chart
      renderChart('chartErrors', 'bar', ['Error Rate %', 'Retrieval Success %'], [
        { label: 'Rate (%)', data: [data.summary.error_rate_pct, data.summary.retrieval_success_rate], backgroundColor: ['#f87171', '#4ade80'] }
      ]);

      // 4. Cost Chart
      renderChart('chartCost', 'line', labels, [
        { label: 'Cost USD ($)', data: ts.map(x => x.cost_usd), borderColor: '#4ade80', backgroundColor: 'rgba(74, 222, 128, 0.1)', fill: true },
        { label: 'Threshold ($2.50)', data: labels.map(() => 2.50), borderColor: '#f87171', borderDash: [6, 4], pointRadius: 0 }
      ]);

      // 5. Tokens Chart
      renderChart('chartTokens', 'bar', labels, [
        { label: 'Tokens In', data: ts.map(x => x.tokens_in), backgroundColor: '#38bdf8' },
        { label: 'Tokens Out', data: ts.map(x => x.tokens_out), backgroundColor: '#a855f7' }
      ], { scales: { x: { stacked: true }, y: { stacked: true } } });

      // 6. Quality Chart
      renderChart('chartQuality', 'line', labels, [
        { label: 'Quality Score', data: ts.map(x => x.quality_score), borderColor: '#facc15', backgroundColor: 'rgba(250, 204, 21, 0.1)', fill: true },
        { label: 'Threshold (0.75)', data: labels.map(() => 0.75), borderColor: '#f87171', borderDash: [6, 4], pointRadius: 0 }
      ], { scales: { y: { min: 0, max: 1.0 } } });
    }

    function renderChart(canvasId, type, labels, datasets, extraOptions = {}) {
      if (charts[canvasId]) {
        charts[canvasId].destroy();
      }
      const ctx = document.getElementById(canvasId).getContext('2d');
      charts[canvasId] = new Chart(ctx, {
        type: type,
        data: { labels: labels, datasets: datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: '#94a3b8', font: { size: 10 } } }
          },
          scales: {
            x: { ticks: { color: '#64748b', font: { size: 9 } }, grid: { color: '#334155' } },
            y: { ticks: { color: '#64748b', font: { size: 9 } }, grid: { color: '#334155' } },
            ...(extraOptions.scales || {})
          }
        }
      });
    }

    fetchDashboardData();
    setInterval(fetchDashboardData, 30000);
  </script>
</body>
</html>
"""
