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
<title>Aster 永續合約機器人 — 控制台</title>
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
  <h1>Aster 永續合約交易機器人</h1>
  <div class="header-right">
    <span id="tradingMode" class="badge badge-none">--</span>
    <span><span class="status-dot gray" id="statusDot"></span><span id="statusText">連線中…</span></span>
    <span style="color:var(--text2)">循環 #<span id="cycleNum">0</span></span>
  </div>
</header>

<div class="container">

  <!-- KPI 卡片 -->
  <div class="grid grid-4">
    <div class="card">
      <div class="card-title">帳戶餘額 (USDT)</div>
      <div class="card-value" id="balance">--</div>
      <div class="card-sub">初始餘額：<span id="initBalance">--</span></div>
    </div>
    <div class="card">
      <div class="card-title">累計盈虧</div>
      <div class="card-value" id="totalPnl">--</div>
      <div class="card-sub" id="totalPnlPct">--</div>
    </div>
    <div class="card">
      <div class="card-title">勝率</div>
      <div class="card-value" id="winRate">--</div>
      <div class="card-sub" id="winLoss">贏：0 / 輸：0</div>
    </div>
    <div class="card">
      <div class="card-title">風控監督狀態</div>
      <div class="card-value" id="clawStatus">--</div>
      <div class="card-sub">連續虧損：<span id="consecLoss">0</span> / 5 &nbsp; 交易/時：<span id="tradesHr">0</span> / 40</div>
    </div>
  </div>

  <!-- 持倉 + 策略 -->
  <div class="grid grid-2">

    <!-- 當前持倉 -->
    <div class="card">
      <div class="card-title">當前持倉</div>
      <div id="positionsContainer">
        <div class="empty">目前無持倉</div>
      </div>
    </div>

    <!-- 策略說明 -->
    <div class="card">
      <div class="card-title">使用策略</div>
      <div class="strategy-box">
        <strong>布林帶反彈 + 限價單 + 手續費優化</strong><br>
        <code>做多</code>：價格 &lt; 布林下軌 + 成交量 &gt; 均量 30% + RSI &lt; 50 + ATR 夠高<br>
        <code>做空</code>：價格 &gt; 布林上軌 + 成交量 &gt; 均量 30% + RSI &gt; 50 + ATR 夠高<br>
        <code>過濾</code>：預期獲利 &lt; 0.3% + 手續費 → 跳過（避免淨虧）<br>
        <code>平倉</code>：追蹤止損 / 價格回到中軌 / 最長持倉 1 小時<br><br>
        訂單類型：<code>限價單 ±0.1%</code> &nbsp; 手續費：<code>0.04%/側</code><br>
        時間框架：<code>5 分鐘</code> &nbsp; 輪詢：<code>每 30 秒</code> &nbsp; 槓桿：<code>3x 逐倉</code><br>
        最小止盈：<code>0.3%</code> &nbsp; 追蹤止損：<code>初始 0.5% / 跟隨 0.3%</code><br>
        風控：<code>淨勝率 &gt;55%</code> / <code>日手續費 &lt;2%</code> / <code>總虧 &lt;2%</code>
      </div>
    </div>
  </div>

  <!-- 即時指標 -->
  <div class="section-title">即時技術指標</div>
  <div class="grid grid-2" id="indicatorsGrid">
    <div class="card empty">等待數據中…</div>
  </div>

  <!-- 交易歷史 -->
  <div class="section-title">交易歷史紀錄</div>
  <div class="card" style="overflow-x:auto">
    <table>
      <thead>
        <tr>
          <th>時間</th>
          <th>交易對</th>
          <th>方向</th>
          <th>入場價</th>
          <th>出場價</th>
          <th>數量</th>
          <th>盈虧 (USDT)</th>
          <th>盈虧 %</th>
        </tr>
      </thead>
      <tbody id="tradesBody">
        <tr><td colspan="8" class="empty">尚無交易紀錄</td></tr>
      </tbody>
    </table>
  </div>

  <!-- 即時日誌 -->
  <div class="section-title">即時運行日誌</div>
  <div class="log-box" id="logBox">等待日誌中…</div>

  <div style="text-align:center;padding:24px;color:var(--text2);font-size:0.75rem;">
    每 5 秒自動更新 &nbsp;|&nbsp; 上次更新：<span id="lastUpdate">--</span>
  </div>

</div>

<script>
const API = '/api/state';
const REFRESH_MS = 5000;

// ---- 工具函數 ----
const $ = id => document.getElementById(id);
const fmt = (n, d=2) => Number(n).toFixed(d);
const fmtK = n => {
  if (Math.abs(n) >= 1e6) return (n/1e6).toFixed(2) + 'M';
  if (Math.abs(n) >= 1e3) return (n/1e3).toFixed(1) + 'K';
  return fmt(n);
};
const pnlClass = v => v > 0 ? 'positive' : v < 0 ? 'negative' : 'neutral';

const sideLabel = s => {
  if (s === 'long') return '做多';
  if (s === 'short') return '做空';
  if (s === 'close_long') return '平多';
  if (s === 'close_short') return '平空';
  if (s === 'none') return '無';
  return s;
};
const sideBadge = s => `<span class="badge badge-${s === 'long' ? 'long' : s === 'short' ? 'short' : 'none'}">${sideLabel(s)}</span>`;

const timeStr = iso => {
  if (!iso) return '--';
  const d = new Date(iso);
  return d.toLocaleString('zh-TW', {hour12:false, month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', second:'2-digit'});
};

const statusMap = {
  'running': '運行中',
  'paused': '已暫停',
  'stopped': '已停止',
  'starting': '啟動中',
};

// ---- 主要更新 ----
async function refresh() {
  $('refreshBar').classList.add('active');
  try {
    const res = await fetch(API);
    if (!res.ok) throw new Error(res.status);
    const d = await res.json();
    render(d);
  } catch(e) {
    $('statusText').textContent = '連線中斷';
    $('statusDot').className = 'status-dot red';
    console.error('更新失敗:', e);
  }
  setTimeout(() => $('refreshBar').classList.remove('active'), 800);
}

function render(d) {
  // -- 狀態 --
  const st = d.bot.status;
  $('statusText').textContent = statusMap[st] || st;
  $('statusDot').className = 'status-dot ' + (
    st === 'running' ? 'green' : st === 'paused' ? 'yellow' : st === 'stopped' ? 'red' : 'gray'
  );
  const modeLabel = d.bot.trading_mode === 'live' ? '實盤交易' : '模擬交易';
  $('tradingMode').textContent = modeLabel;
  $('tradingMode').className = 'badge ' + (d.bot.trading_mode === 'live' ? 'badge-short' : 'badge-long');
  $('cycleNum').textContent = d.bot.cycle;

  // -- 餘額 --
  $('balance').textContent = fmtK(d.balance.current);
  $('initBalance').textContent = fmt(d.balance.initial);

  // -- 盈虧 --
  const pnl = d.balance.pnl;
  $('totalPnl').textContent = (pnl >= 0 ? '+' : '') + fmt(pnl, 4);
  $('totalPnl').className = 'card-value ' + pnlClass(pnl);
  $('totalPnlPct').textContent = (d.balance.pnl_pct >= 0 ? '+' : '') + fmt(d.balance.pnl_pct) + '% (佔初始餘額)';
  $('totalPnlPct').className = 'card-sub ' + pnlClass(pnl);

  // -- 勝率 --
  const netWr = d.openclaw.net_win_rate || d.openclaw.win_rate;
  $('winRate').textContent = d.openclaw.total_trades > 0 ? fmt(netWr,1) + '%' : '--';
  $('winRate').className = 'card-value ' + (netWr >= 55 ? 'positive' : netWr > 0 ? 'negative' : 'neutral');
  const feeStr = d.openclaw.total_fees ? `  手續費：${fmt(d.openclaw.total_fees,2)}` : '';
  $('winLoss').textContent = `贏：${d.openclaw.wins} / 輸：${d.openclaw.losses}（共 ${d.openclaw.total_trades} 筆）${feeStr}`;

  // -- 風控監督 --
  const paused = d.openclaw.is_paused;
  $('clawStatus').textContent = paused ? '已暫停' : '正常運行';
  $('clawStatus').className = 'card-value ' + (paused ? 'negative' : 'positive');
  $('consecLoss').textContent = d.openclaw.consecutive_losses;
  if ($('tradesHr')) $('tradesHr').textContent = d.openclaw.trades_this_hour || 0;

  // -- 持倉 --
  const posKeys = Object.keys(d.positions);
  if (posKeys.length === 0 || posKeys.every(k => !d.positions[k])) {
    $('positionsContainer').innerHTML = '<div class="empty">目前無持倉</div>';
  } else {
    let html = '<table><thead><tr><th>交易對</th><th>方向</th><th>入場價</th><th>數量</th><th>止損</th><th>止盈</th><th>未實現盈虧</th></tr></thead><tbody>';
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

  // -- 指標 --
  const indKeys = Object.keys(d.indicators);
  if (indKeys.length === 0) {
    $('indicatorsGrid').innerHTML = '<div class="card empty">等待數據中…</div>';
  } else {
    let html = '';
    for (const k of indKeys) {
      const ind = d.indicators[k];
      const rsiColor = ind.rsi > 70 ? 'var(--red)' : ind.rsi < 30 ? 'var(--green)' : 'var(--blue)';
      const bbUpper = ind.ema_short;  // repurposed
      const bbLower = ind.ema_long;   // repurposed
      const price = ind.last_price;
      const zone = price < bbLower ? '支撐帶（做多區）' : price > bbUpper ? '壓力帶（做空區）' : '通道內';
      const zoneColor = price < bbLower ? 'positive' : price > bbUpper ? 'negative' : 'neutral';
      html += `<div class="card">
        <div class="card-title">${ind.symbol} — <span class="${zoneColor}">${zone}</span></div>
        <div style="font-size:1.3rem;font-weight:700;margin-bottom:12px">${fmtK(ind.last_price)} <span style="font-size:0.8rem;color:var(--text2)">USDT</span></div>
        <div class="ind-row">
          <span class="ind-label">布林上軌</span>
          <span class="ind-val" style="color:var(--red)">${fmtK(bbUpper)}</span>
        </div>
        <div class="ind-row">
          <span class="ind-label">布林下軌</span>
          <span class="ind-val" style="color:var(--green)">${fmtK(bbLower)}</span>
        </div>
        <div class="ind-row">
          <span class="ind-label">RSI(14)</span>
          <div class="ind-bar-bg"><div class="ind-bar" style="width:${Math.min(ind.rsi,100)}%;background:${rsiColor}"></div></div>
          <span class="ind-val" style="color:${rsiColor}">${fmt(ind.rsi,1)}</span>
        </div>
        <div style="margin-top:10px;font-size:0.82rem;color:var(--text2)">
          最新訊號：${sideBadge(ind.last_signal)}
          <span style="margin-left:6px">${ind.signal_reason || ''}</span>
        </div>
      </div>`;
    }
    $('indicatorsGrid').innerHTML = html;
  }

  // -- 交易紀錄 --
  if (d.trades.length === 0) {
    $('tradesBody').innerHTML = '<tr><td colspan="8" class="empty">尚無交易紀錄</td></tr>';
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

  // -- 日誌 --
  if (d.recent_logs && d.recent_logs.length > 0) {
    $('logBox').innerHTML = d.recent_logs.map(l =>
      l.replace(/</g,'&lt;').replace(/>/g,'&gt;')
    ).join('<br>');
    const box = $('logBox');
    box.scrollTop = box.scrollHeight;
  }

  // -- 時間戳 --
  $('lastUpdate').textContent = new Date().toLocaleTimeString('zh-TW', {hour12:false});
}

// ---- 啟動 ----
refresh();
setInterval(refresh, REFRESH_MS);
</script>
</body>
</html>
"""
