/* StreetWatch Neo — Dashboard JS */

// ── TOAST SYSTEM ──
const toastContainer = (() => {
  let el = document.querySelector('.toast-container');
  if (!el) {
    el = document.createElement('div');
    el.className = 'toast-container';
    document.body.appendChild(el);
  }
  return el;
})();

function showToast(title, msg, type = 'info', duration = 4500) {
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      ${msg ? `<div class="toast-msg">${msg}</div>` : ''}
    </div>
    <span class="toast-close" onclick="removeToast(this.parentElement)">×</span>`;
  toastContainer.appendChild(toast);
  setTimeout(() => removeToast(toast), duration);
}

function removeToast(toast) {
  if (!toast || !toast.parentElement) return;
  toast.classList.add('removing');
  setTimeout(() => toast.remove(), 300);
}

// ── COUNT-UP ANIMATION ──
function animateCount(el, target, duration = 1200, suffix = '') {
  const start = 0;
  const step = target / (duration / 16);
  let current = start;
  const timer = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = Math.round(current).toLocaleString() + suffix;
    if (current >= target) clearInterval(timer);
  }, 16);
}

function initCountUp() {
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseFloat(el.dataset.count);
    const suffix = el.dataset.suffix || '';
    if (!isNaN(target)) animateCount(el, target, 1200, suffix);
  });
}

// ── CHART COLORS ──
const CHART_COLORS = {
  blue:   '#1a56db',
  green:  '#22c55e',
  red:    '#ef4444',
  orange: '#f59e0b',
  purple: '#8b5cf6',
  cyan:   '#06b6d4',
};

const VIOLATION_COLORS = [
  CHART_COLORS.red,
  CHART_COLORS.orange,
  CHART_COLORS.purple,
  CHART_COLORS.cyan,
  CHART_COLORS.blue,
];

// ── CHARTS ──
let trafficChart = null;
let violationChart = null;
let systemChart = null;

function initSystemChart() {
  const ctx = document.getElementById('systemChart');
  if (!ctx) return;
  systemChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Monitoring', 'Cleaning', 'Enforcement', 'Connectivity'],
      datasets: [{
        data: [92, 85, 74, 88],
        backgroundColor: [
          CHART_COLORS.green,
          CHART_COLORS.blue,
          CHART_COLORS.orange,
          CHART_COLORS.cyan,
        ],
        borderColor: '#111827',
        borderWidth: 3,
        hoverOffset: 6,
      }]
    },
    options: {
      responsive: true,
      cutout: '72%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#94a3b8',
            font: { size: 11, family: 'Inter' },
            padding: 12,
            usePointStyle: true,
            pointStyleWidth: 8,
          }
        },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.raw}%`
          }
        }
      }
    }
  });
}

function renderTrafficChart(data) {
  const ctx = document.getElementById('trafficChart');
  if (!ctx) return;
  const labels = data.map(d => `${String(d.hour).padStart(2,'0')}:00`);
  const counts = data.map(d => d.count);
  if (trafficChart) trafficChart.destroy();
  trafficChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Vehicles',
        data: counts,
        borderColor: CHART_COLORS.blue,
        backgroundColor: 'rgba(26,86,219,0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 6,
        pointBackgroundColor: CHART_COLORS.blue,
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { mode: 'index', intersect: false }
      },
      scales: {
        x: {
          grid: { color: 'rgba(30,45,74,0.5)' },
          ticks: { color: '#475569', font: { size: 10 }, maxTicksLimit: 8 }
        },
        y: {
          grid: { color: 'rgba(30,45,74,0.5)' },
          ticks: { color: '#475569', font: { size: 10 }, precision: 0 },
          beginAtZero: true
        }
      }
    }
  });
}

function renderViolationChart(data) {
  const ctx = document.getElementById('violationChart');
  if (!ctx) return;
  const labels = Object.keys(data);
  const values = Object.values(data);
  if (violationChart) violationChart.destroy();
  violationChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: VIOLATION_COLORS,
        borderColor: '#111827',
        borderWidth: 3,
        hoverOffset: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: ctx => ` ${ctx.label}: ${ctx.raw}` }
        }
      }
    }
  });

  const legendEl = document.getElementById('violationLegend');
  if (legendEl) {
    legendEl.innerHTML = labels.map((l, i) => `
      <div class="legend-item">
        <span class="legend-dot" style="background:${VIOLATION_COLORS[i]}"></span>
        <span>${l}</span>
        <span class="legend-count">${values[i]}</span>
      </div>`).join('');
  }
}

// ── ALERTS ──
function renderAlerts(alerts) {
  const el = document.getElementById('alertsList');
  if (!el) return;
  if (!alerts.length) {
    el.innerHTML = '<li class="alert-item"><span style="color:var(--text-muted);font-size:12px;">No recent alerts</span></li>';
    return;
  }
  el.innerHTML = alerts.map(a => {
    const ago = timeAgo(a.timestamp);
    return `<li class="alert-item">
      <span class="alert-dot ${a.severity}"></span>
      <div class="alert-info">
        <div class="alert-type">${a.alert_type}</div>
        <div class="alert-loc">${a.location}</div>
      </div>
      <span class="alert-time">${ago}</span>
    </li>`;
  }).join('');
}

function timeAgo(ts) {
  const now = new Date();
  const past = new Date(ts.replace(' ', 'T') + 'Z');
  const diff = Math.floor((now - past) / 1000);
  if (diff < 60)    return `${diff}s ago`;
  if (diff < 3600)  return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}

// ── STATS UPDATE ──
function updateStats(data) {
  const map = {
    'stat-violations-today': data.violations_today,
    'stat-challans-today':   data.challans_today,
  };
  Object.entries(map).forEach(([id, val]) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  });
}

// ── FETCH AND REFRESH ──
function fetchDashboardData() {
  fetch('/api/violations/chart')
    .then(r => r.json())
    .then(renderViolationChart)
    .catch(() => {});

  fetch('/api/traffic/hourly')
    .then(r => r.json())
    .then(renderTrafficChart)
    .catch(() => {});

  fetch('/api/alerts/recent')
    .then(r => r.json())
    .then(renderAlerts)
    .catch(() => {});

  fetch('/api/stats')
    .then(r => r.json())
    .then(updateStats)
    .catch(() => {});
}

// ── LEAFLET MAP ──
function initMap() {
  const mapEl = document.getElementById('main-map');
  if (!mapEl || typeof L === 'undefined') return;

  const map = L.map('main-map', { zoomControl: true, scrollWheelZoom: true })
    .setView([26.3411, 88.5541], 13);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map);

  const markers = [
    { lat: 26.3411, lng: 88.5541, type: 'monitoring', label: 'CAM-01 — Station Road',    color: '#22c55e' },
    { lat: 26.3455, lng: 88.5580, type: 'monitoring', label: 'CAM-02 — Thana Road',      color: '#22c55e' },
    { lat: 26.3380, lng: 88.5510, type: 'violation',  label: 'Violation — College Road', color: '#ef4444' },
    { lat: 26.3490, lng: 88.5600, type: 'cleaning',   label: 'Robot — Sadar Road',       color: '#06b6d4' },
    { lat: 26.3340, lng: 88.5460, type: 'block',      label: 'Road Block — Boda Road',   color: '#f59e0b' },
    { lat: 26.3520, lng: 88.5560, type: 'monitoring', label: 'CAM-04 — Hospital Road',   color: '#22c55e' },
    { lat: 26.3430, lng: 88.5480, type: 'violation',  label: 'Violation — DC Office',    color: '#ef4444' },
  ];

  markers.forEach(m => {
    const icon = L.divIcon({
      html: `<div style="width:14px;height:14px;background:${m.color};border-radius:50%;border:2px solid #fff;box-shadow:0 0 8px ${m.color}"></div>`,
      className: '',
      iconSize: [14, 14],
      iconAnchor: [7, 7],
    });
    L.marker([m.lat, m.lng], { icon })
      .addTo(map)
      .bindPopup(`<div style="color:#111;font-family:Inter,sans-serif;font-size:12px"><b>${m.label}</b></div>`);
  });
}

// ── SIMULATE DETECTION (Monitoring page) ──
function simulateDetection() {
  const btn = document.getElementById('simulate-btn');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Simulating...';
  }

  fetch('/api/simulate-detection')
    .then(r => r.json())
    .then(data => {
      const tbody = document.getElementById('live-feed-body');
      if (tbody) {
        const tr = document.createElement('tr');
        tr.className = 'flash-row';
        const speedClass = data.speed_kmh > 90 ? 'speed-red' : data.speed_kmh > 60 ? 'speed-orange' : 'speed-green';
        const vBadge = data.violation_type
          ? `<span class="badge badge-overspeeding">${data.violation_type}</span>`
          : `<span class="badge badge-none">None</span>`;
        tr.innerHTML = `
          <td>${data.plate_number}</td>
          <td class="${speedClass}">${data.speed_kmh} km/h</td>
          <td>${data.location}</td>
          <td>${data.camera_id}</td>
          <td>${vBadge}</td>
          <td>${new Date().toLocaleTimeString()}</td>`;
        tbody.insertBefore(tr, tbody.firstChild);
        if (tbody.children.length > 20) tbody.removeChild(tbody.lastChild);
      }
      showToast('Detection Simulated', `${data.plate_number} detected at ${data.location}`, data.violation_type ? 'warning' : 'success');
    })
    .catch(() => showToast('Error', 'Failed to simulate detection', 'error'))
    .finally(() => {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-bolt"></i> Simulate Detection';
      }
    });
}

// ── INIT ──
document.addEventListener('DOMContentLoaded', () => {
  initCountUp();
  initSystemChart();
  initMap();
  fetchDashboardData();
  setInterval(fetchDashboardData, 30000);
});
