"""
Web dashboard for the Aster Perpetuals Trading Bot.

Provides a modern, auto-refreshing single-page dashboard that shows:
  - Bot status & uptime
  - Current balance & PnL
  - Open positions per symbol
  - Latest indicator values & signals
  - Trade history
  - OpenClaw monitor status
  - Live log stream

Runs on a background thread so it doesn't block the main trading loop.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from flask import Flask, jsonify, Response

from aster_perpetuals_bot.shared_state import bot_state

logger = logging.getLogger("aster_bot.dashboard")

app = Flask(__name__)

# Suppress Flask's default request logging in production
flask_log = logging.getLogger("werkzeug")
flask_log.setLevel(logging.WARNING)


# ======================================================================
# API Endpoints
# ======================================================================

@app.route("/api/state")
def api_state() -> tuple[Response, int]:
    """Return full bot state as JSON (polled by the frontend)."""
    return jsonify(bot_state.snapshot()), 200


@app.route("/api/health")
def api_health() -> tuple[Response, int]:
    """Simple health-check endpoint."""
    return jsonify({"status": "ok"}), 200


# ======================================================================
# Dashboard HTML (single-page, self-contained)
# ======================================================================

@app.route("/")
def index() -> str:
    """Serve the dashboard HTML."""
    return DASHBOARD_HTML


# ======================================================================
# Launcher
# ======================================================================

def start_dashboard(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Start the Flask dashboard in a daemon thread."""
    thread = threading.Thread(
        target=lambda: app.run(host=host, port=port, debug=False, use_reloader=False),
        daemon=True,
        name="dashboard",
    )
    thread.start()
    logger.info("Dashboard started at http://%s:%d", host, port)


# ======================================================================
# Embedded HTML/CSS/JS
# ======================================================================

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aster Perpetuals Bot — Dashboard</title>
<style>
/* ---- Reset & Base ---- */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg:       #0f1117;
  --surface:  #1a1d27;
  --surface2: #242836;
  --border:   #2e3348;
  --text:     #e4e6f0;
  --text2:    #8b8fa3;
  --green:    #00d68f;
  --red:      #ff4d6a;
  --blue:     #3b82f6;
  --yellow:   #f5a623;
  --purple:   #a78bfa;
  --cyan:     #22d3ee;
  --radius:   12px;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  min-height: 100vh;
}
a { color: var(--blue); text-decoration: none; }

/* ---- Layout ---- */
.header {
  background: linear-gradient(135deg, #1a1d27 0%, #242836 100%);
  border-bottom: 1px solid var(--border);
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}
.header h1 {
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--cyan), var(--blue));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.header-right { display: flex; align-items: center; gap: 16px; font-size: 0.85rem; }
.status-dot {
  width: 10px; height: 10px; border-radius: 50%; display: inline-block;
  margin-right: 6px; animation: pulse 2s ease-in-out infinite;
}
.status-dot.green { background: var(--green); box-shadow: 0 0 8px var(--green); }
.status-dot.red   { background: var(--red);   box-shadow: 0 0 8px var(--red); }
.status-dot.yellow{ background: var(--yellow); box-shadow: 0 0 8px var(--yellow); }
.status-dot.gray  { background: #555; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }

.container { max-width: 1400px; margin: 0 auto; padding: 20px; }

/* ---- Cards ---- */
.grid { display: grid; gap: 16px; margin-bottom: 16px; }
.grid-4 { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
.grid-2 { grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); }
.grid-1 { grid-template-columns: 1fr; }

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  transition: border-color 0.2s;
}
.card:hover { border-color: var(--blue); }
.card-title {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text2);
  margin-bottom: 8px;
}
.card-value {
  font-size: 1.8rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.card-sub { font-size: 0.82rem; color: var(--text2); margin-top: 4px; }
.positive { color: var(--green); }
.negative { color: var(--red); }
.neutral  { color: var(--text2); }

/* ---- Section headers ---- */
.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 24px 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
  color: var(--text2);
}

/* ---- Tables ---- */
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
thead th {
  text-align: left;
  padding: 10px 12px;
  color: var(--text2);
  font-weight: 500;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
tbody td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
tbody tr:hover { background: var(--surface2); }
.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}
.badge-long  { background: rgba(0,214,143,0.15); color: var(--green); }
.badge-short { background: rgba(255,77,106,0.15); color: var(--red); }
.badge-none  { background: rgba(139,143,163,0.15); color: var(--text2); }

/* ---- Strategy panel ---- */
.strategy-box {
  background: var(--surface2);
  border-radius: 8px;
  padding: 16px;
  font-size: 0.85rem;
  line-height: 1.8;
}
.strategy-box code {
  background: rgba(59,130,246,0.12);
  color: var(--cyan);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.82rem;
}

/* ---- Indicator bars ---- */
.ind-row { display: flex; align-items: center; gap: 12px; margin: 8px 0; }
.ind-label { width: 90px; font-size: 0.82rem; color: var(--text2); }
.ind-bar-bg {
  flex: 1; height: 8px; background: var(--surface2);
  border-radius: 4px; overflow: hidden; position: relative;
}
.ind-bar {
  height: 100%; border-radius: 4px;
  transition: width 0.5s ease;
}
.ind-val { width: 70px; text-align: right; font-size: 0.85rem; font-weight: 600; font-variant-numeric: tabular-nums; }

/* ---- Log panel ---- */
.log-box {
  background: #0d0f14;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  max-height: 260px;
  overflow-y: auto;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.75rem;
  line-height: 1.6;
  color: var(--text2);
}
.log-box::-webkit-scrollbar { width: 6px; }
.log-box::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ---- Responsive ---- */
@media (max-width: 768px) {
  .grid-2 { grid-template-columns: 1fr; }
  .header { flex-direction: column; gap: 8px; }
  .card-value { font-size: 1.4rem; }
  .container { padding: 12px; }
}

/* ---- Refresh indicator ---- */
.refresh-bar {
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--blue), transparent);
  position: fixed; top: 0; left: 0; width: 100%; z-index: 200;
  opacity: 0; transition: opacity 0.2s;
}
.refresh-bar.active { opacity: 1; animation: slide 0.8s linear; }
@keyframes slide { from{transform:translateX(-100%)} to{transform:translateX(100%)} }

/* ---- Empty state ---- */
.empty { text-align: center; padding: 40px; color: var(--text2); font-size: 0.9rem; }
</style>
</head>
<body>

<div class="refresh-bar" id="refreshBar"></div>

<header class="header">
  <h1>Aster Perpetuals Bot</h1>
  <div class="header-right">
    <span id="tradingMode" class="badge badge-none">--</span>
    <span><span class="status-dot gray" id="statusDot"></span><span id="statusText">Connecting…</span></span>
    <span style="color:var(--text2)">Cycle #<span id="cycleNum">0</span></span>
  </div>
</header>

<div class="container">

  <!-- KPI Cards -->
  <div class="grid grid-4">
    <div class="card">
      <div class="card-title">Balance (USDT)</div>
      <div class="card-value" id="balance">--</div>
      <div class="card-sub">Initial: <span id="initBalance">--</span></div>
    </div>
    <div class="card">
      <div class="card-title">Total PnL</div>
      <div class="card-value" id="totalPnl">--</div>
      <div class="card-sub" id="totalPnlPct">--</div>
    </div>
    <div class="card">
      <div class="card-title">Win Rate</div>
      <div class="card-value" id="winRate">--</div>
      <div class="card-sub" id="winLoss">W: 0 / L: 0</div>
    </div>
    <div class="card">
      <div class="card-title">OpenClaw Status</div>
      <div class="card-value" id="clawStatus">--</div>
      <div class="card-sub">Consec. losses: <span id="consecLoss">0</span> / 3</div>
    </div>
  </div>

  <!-- Positions + Strategy -->
  <div class="grid grid-2">

    <!-- Positions -->
    <div class="card">
      <div class="card-title">Open Positions</div>
      <div id="positionsContainer">
        <div class="empty">No open positions</div>
      </div>
    </div>

    <!-- Strategy Info -->
    <div class="card">
      <div class="card-title">Strategy</div>
      <div class="strategy-box">
        <strong>EMA Crossover + RSI Filter</strong><br>
        <code>LONG</code> : EMA(9) crosses above EMA(21) &amp; RSI(14) &lt; 60<br>
        <code>SHORT</code> : EMA(9) crosses below EMA(21) &amp; RSI(14) &gt; 40<br>
        <code>EXIT</code> : Reverse crossover or SL/TP hit<br><br>
        Timeframe: <code>15m</code> &nbsp; Leverage: <code>5x Isolated</code><br>
        Risk/trade: <code>1%</code> &nbsp; SL: <code>±1.5%</code> &nbsp; TP: <code>±3%</code>
      </div>
    </div>
  </div>

  <!-- Indicators per symbol -->
  <div class="section-title">Indicators (Live)</div>
  <div class="grid grid-2" id="indicatorsGrid">
    <div class="card empty">Waiting for data…</div>
  </div>

  <!-- Trade History -->
  <div class="section-title">Trade History</div>
  <div class="card" style="overflow-x:auto">
    <table>
      <thead>
        <tr>
          <th>Time</th>
          <th>Symbol</th>
          <th>Side</th>
          <th>Entry</th>
          <th>Exit</th>
          <th>Qty</th>
          <th>PnL (USDT)</th>
          <th>PnL %</th>
        </tr>
      </thead>
      <tbody id="tradesBody">
        <tr><td colspan="8" class="empty">No trades yet</td></tr>
      </tbody>
    </table>
  </div>

  <!-- Logs -->
  <div class="section-title">Live Logs</div>
  <div class="log-box" id="logBox">Waiting for logs…</div>

  <div style="text-align:center;padding:24px;color:var(--text2);font-size:0.75rem;">
    Auto-refresh every 5s &nbsp;|&nbsp; Last update: <span id="lastUpdate">--</span>
  </div>

</div>

<script>
const API = '/api/state';
const REFRESH_MS = 5000;

// ---- Helpers ----
const $ = id => document.getElementById(id);
const fmt = (n, d=2) => Number(n).toFixed(d);
const fmtK = n => {
  if (Math.abs(n) >= 1e6) return (n/1e6).toFixed(2) + 'M';
  if (Math.abs(n) >= 1e3) return (n/1e3).toFixed(1) + 'K';
  return fmt(n);
};
const pnlClass = v => v > 0 ? 'positive' : v < 0 ? 'negative' : 'neutral';
const sideBadge = s => `<span class="badge badge-${s === 'long' ? 'long' : s === 'short' ? 'short' : 'none'}">${s}</span>`;
const timeStr = iso => {
  if (!iso) return '--';
  const d = new Date(iso);
  return d.toLocaleString('zh-TW', {hour12:false, month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', second:'2-digit'});
};

// ---- Main fetch & render ----
async function refresh() {
  $('refreshBar').classList.add('active');
  try {
    const res = await fetch(API);
    if (!res.ok) throw new Error(res.status);
    const d = await res.json();
    render(d);
  } catch(e) {
    $('statusText').textContent = 'Disconnected';
    $('statusDot').className = 'status-dot red';
    console.error('Fetch error:', e);
  }
  setTimeout(() => $('refreshBar').classList.remove('active'), 800);
}

function render(d) {
  // -- Status --
  const st = d.bot.status;
  $('statusText').textContent = st.charAt(0).toUpperCase() + st.slice(1);
  $('statusDot').className = 'status-dot ' + (
    st === 'running' ? 'green' : st === 'paused' ? 'yellow' : st === 'stopped' ? 'red' : 'gray'
  );
  $('tradingMode').textContent = d.bot.trading_mode.toUpperCase();
  $('tradingMode').className = 'badge ' + (d.bot.trading_mode === 'live' ? 'badge-short' : 'badge-long');
  $('cycleNum').textContent = d.bot.cycle;

  // -- Balance --
  $('balance').textContent = fmtK(d.balance.current);
  $('initBalance').textContent = fmt(d.balance.initial);

  // -- PnL --
  const pnl = d.balance.pnl;
  $('totalPnl').textContent = (pnl >= 0 ? '+' : '') + fmt(pnl, 4);
  $('totalPnl').className = 'card-value ' + pnlClass(pnl);
  $('totalPnlPct').textContent = (d.balance.pnl_pct >= 0 ? '+' : '') + fmt(d.balance.pnl_pct) + '% of initial';
  $('totalPnlPct').className = 'card-sub ' + pnlClass(pnl);

  // -- Win rate --
  $('winRate').textContent = d.openclaw.total_trades > 0 ? fmt(d.openclaw.win_rate,1) + '%' : '--';
  $('winLoss').textContent = `W: ${d.openclaw.wins} / L: ${d.openclaw.losses} (${d.openclaw.total_trades} total)`;

  // -- OpenClaw --
  const paused = d.openclaw.is_paused;
  $('clawStatus').textContent = paused ? 'PAUSED' : 'Active';
  $('clawStatus').className = 'card-value ' + (paused ? 'negative' : 'positive');
  $('consecLoss').textContent = d.openclaw.consecutive_losses;

  // -- Positions --
  const posKeys = Object.keys(d.positions);
  if (posKeys.length === 0 || posKeys.every(k => !d.positions[k])) {
    $('positionsContainer').innerHTML = '<div class="empty">No open positions</div>';
  } else {
    let html = '<table><thead><tr><th>Symbol</th><th>Side</th><th>Entry</th><th>Qty</th><th>SL</th><th>TP</th><th>uPnL</th></tr></thead><tbody>';
    for (const k of posKeys) {
      const p = d.positions[k];
      if (!p) continue;
      const upnl = p.unrealised_pnl;
      html += `<tr>
        <td><strong>${p.symbol}</strong></td>
        <td>${sideBadge(p.side)}</td>
        <td>${fmt(p.entry_price)}</td>
        <td>${p.quantity}</td>
        <td>${fmt(p.sl_price)}</td>
        <td>${fmt(p.tp_price)}</td>
        <td class="${pnlClass(upnl)}">${(upnl>=0?'+':'')+fmt(upnl,4)}</td>
      </tr>`;
    }
    html += '</tbody></table>';
    $('positionsContainer').innerHTML = html;
  }

  // -- Indicators --
  const indKeys = Object.keys(d.indicators);
  if (indKeys.length === 0) {
    $('indicatorsGrid').innerHTML = '<div class="card empty">Waiting for data…</div>';
  } else {
    let html = '';
    for (const k of indKeys) {
      const ind = d.indicators[k];
      const rsiColor = ind.rsi > 70 ? 'var(--red)' : ind.rsi < 30 ? 'var(--green)' : 'var(--blue)';
      const emaDiff = ind.ema_short - ind.ema_long;
      const trend = emaDiff > 0 ? 'Bullish' : emaDiff < 0 ? 'Bearish' : 'Neutral';
      const trendColor = emaDiff > 0 ? 'positive' : emaDiff < 0 ? 'negative' : 'neutral';
      html += `<div class="card">
        <div class="card-title">${ind.symbol} — <span class="${trendColor}">${trend}</span></div>
        <div style="font-size:1.3rem;font-weight:700;margin-bottom:12px">${fmtK(ind.last_price)} <span style="font-size:0.8rem;color:var(--text2)">USDT</span></div>
        <div class="ind-row">
          <span class="ind-label">EMA(9)</span>
          <span class="ind-val">${fmtK(ind.ema_short)}</span>
        </div>
        <div class="ind-row">
          <span class="ind-label">EMA(21)</span>
          <span class="ind-val">${fmtK(ind.ema_long)}</span>
        </div>
        <div class="ind-row">
          <span class="ind-label">RSI(14)</span>
          <div class="ind-bar-bg"><div class="ind-bar" style="width:${Math.min(ind.rsi,100)}%;background:${rsiColor}"></div></div>
          <span class="ind-val" style="color:${rsiColor}">${fmt(ind.rsi,1)}</span>
        </div>
        <div style="margin-top:10px;font-size:0.82rem;color:var(--text2)">
          Signal: ${sideBadge(ind.last_signal)}
          <span style="margin-left:6px">${ind.signal_reason || ''}</span>
        </div>
      </div>`;
    }
    $('indicatorsGrid').innerHTML = html;
  }

  // -- Trades --
  if (d.trades.length === 0) {
    $('tradesBody').innerHTML = '<tr><td colspan="8" class="empty">No trades yet</td></tr>';
  } else {
    let html = '';
    for (const t of d.trades) {
      const pnl = t.pnl;
      html += `<tr>
        <td>${timeStr(t.closed_at)}</td>
        <td>${t.symbol}</td>
        <td>${sideBadge(t.side)}</td>
        <td>${fmt(t.entry_price)}</td>
        <td>${fmt(t.exit_price)}</td>
        <td>${t.quantity}</td>
        <td class="${pnlClass(pnl)}">${(pnl>=0?'+':'')+fmt(pnl,4)}</td>
        <td class="${pnlClass(pnl)}">${(t.pnl_pct>=0?'+':'')+fmt(t.pnl_pct)}%</td>
      </tr>`;
    }
    $('tradesBody').innerHTML = html;
  }

  // -- Logs --
  if (d.recent_logs && d.recent_logs.length > 0) {
    $('logBox').innerHTML = d.recent_logs.map(l =>
      l.replace(/</g,'&lt;').replace(/>/g,'&gt;')
    ).join('<br>');
    const box = $('logBox');
    box.scrollTop = box.scrollHeight;
  }

  // -- Timestamp --
  $('lastUpdate').textContent = new Date().toLocaleTimeString('zh-TW', {hour12:false});
}

// ---- Kick off ----
refresh();
setInterval(refresh, REFRESH_MS);
</script>
</body>
</html>
"""
