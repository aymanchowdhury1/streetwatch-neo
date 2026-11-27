/* StreetWatch Neo — Video Analysis JS */
'use strict';

// ── STATE ──
let currentSessionId = null;
let eventSource = null;
let webcamStream = null;
let webcamInterval = null;
let detectionResults = [];

// ── DOM REFS ──
const $ = id => document.getElementById(id);
const csrfHeaders = () => ({ 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || '' });

// ── TAB SWITCHING ──
function switchTab(tabName) {
  document.querySelectorAll('.video-tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.video-tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
  const panel = $('panel-' + tabName);
  if (panel) panel.classList.add('active');
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.video-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  setupDropZone();
  setupUploadForm();
  setupWebcam();
  setupExportCsv();
});

// ── DRAG-DROP UPLOAD ZONE ──
function setupDropZone() {
  const zone = $('upload-zone');
  const fileInput = $('video-file-input');
  const fileInfo = $('selected-file-info');
  const fileName = $('selected-file-name');
  const fileSize = $('selected-file-size');

  if (!zone) return;

  zone.addEventListener('dragover', e => {
    e.preventDefault();
    zone.classList.add('drag-over');
  });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length) handleFileSelect(files[0]);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) handleFileSelect(fileInput.files[0]);
  });

  function handleFileSelect(file) {
    fileName.textContent = file.name;
    fileSize.textContent = formatBytes(file.size);
    fileInfo.classList.add('show');
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;
  }
}

function formatBytes(bytes) {
  if (bytes < 1024)     return bytes + ' B';
  if (bytes < 1048576)  return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

// ── UPLOAD + ANALYSIS ──
function setupUploadForm() {
  const form = $('upload-form');
  if (!form) return;

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const fileInput = $('video-file-input');
    if (!fileInput.files.length) {
      showToast('No File', 'Please select a video file first.', 'warning');
      return;
    }

    const formData = new FormData();
    formData.append('video', fileInput.files[0]);

    setAnalyzeBtn(true);
    showProgress(true);
    setProgressText('Uploading video...');
    setProgressBar(0, true);
    clearFeed();
    clearResultTable();
    detectionResults = [];

    try {
      const resp = await fetch('/video/upload', { method: 'POST', headers: csrfHeaders(), body: formData });
      const data = await resp.json();
      if (!resp.ok || data.error) {
        throw new Error(data.error || 'Upload failed');
      }
      currentSessionId = data.session_id;
      setProgressText('Analyzing video... AI is processing frames');
      startSSE(currentSessionId);
    } catch (err) {
      showProgress(false);
      setAnalyzeBtn(false);
      showToast('Upload Failed', err.message, 'error');
    }
  });
}

function setAnalyzeBtn(disabled) {
  const btn = $('analyze-btn');
  if (!btn) return;
  btn.disabled = disabled;
  btn.innerHTML = disabled
    ? '<span class="progress-spinner"></span> Analyzing...'
    : '<i class="fas fa-brain"></i> Start Analysis';
}

function showProgress(show) {
  const sec = $('progress-section');
  if (sec) sec.classList.toggle('show', show);
}

function setProgressText(text) {
  const el = $('progress-text');
  if (el) el.textContent = text;
}

function setProgressBar(pct, indeterminate = false) {
  const bar = $('progress-bar-fill');
  if (!bar) return;
  if (indeterminate) {
    bar.classList.add('indeterminate');
    bar.style.width = '';
  } else {
    bar.classList.remove('indeterminate');
    bar.style.width = Math.min(100, pct) + '%';
  }
}

// ── SSE ──
function startSSE(sessionId) {
  if (eventSource) eventSource.close();

  eventSource = new EventSource(`/video/stream/${sessionId}`);

  eventSource.onmessage = e => {
    let msg;
    try { msg = JSON.parse(e.data); } catch { return; }

    if (msg.type === 'detection' && msg.data) {
      addDetectionCard(msg.data);
      addTableRow(msg.data);
      detectionResults.push(msg.data);
      updateSessionStats(msg.frame_count, msg.detections_so_far);
      setProgressText(`Analyzing frame ${msg.frame_count}... ${msg.detections_so_far} detections found`);
    }

    if (msg.type === 'progress') {
      updateSessionStats(msg.frame_count, msg.detections_so_far);
      setProgressText(`Processing frame ${msg.frame_count}... ${msg.detections_so_far} detections so far`);
    }

    if (msg.type === 'done') {
      eventSource.close();
      eventSource = null;
      setProgressBar(100, false);
      setProgressText(`Analysis complete — ${msg.frame_count} frames processed, ${msg.detections_so_far || detectionResults.length} detections`);
      setAnalyzeBtn(false);
      showToast('Analysis Complete', `${detectionResults.length} vehicles detected.`, 'success');
    }

    if (msg.type === 'error') {
      eventSource.close();
      eventSource = null;
      showProgress(false);
      setAnalyzeBtn(false);
      showToast('Error', msg.message, 'error');
    }
  };

  eventSource.onerror = () => {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  };
}

function stopSession() {
  if (!currentSessionId) return;
  fetch(`/video/stop/${currentSessionId}`, { method: 'POST', headers: csrfHeaders() });
  if (eventSource) { eventSource.close(); eventSource = null; }
  setAnalyzeBtn(false);
  showProgress(false);
  showToast('Stopped', 'Processing stopped.', 'info');
}

// ── WEBCAM ──
function setupWebcam() {
  const startBtn = $('webcam-start-btn');
  const stopBtn  = $('webcam-stop-btn');
  if (!startBtn) return;

  startBtn.addEventListener('click', startWebcam);
  stopBtn.addEventListener('click',  stopWebcam);
}

async function startWebcam() {
  const videoEl = $('webcam-video');
  const overlay = $('webcam-overlay');
  const activeInd = $('webcam-active-ind');
  const startBtn = $('webcam-start-btn');
  const stopBtn  = $('webcam-stop-btn');

  try {
    webcamStream = await navigator.mediaDevices.getUserMedia({ video: true });
    videoEl.srcObject = webcamStream;
    videoEl.play();
    if (overlay)   overlay.style.display = 'none';
    if (activeInd) activeInd.style.display = 'flex';
    startBtn.style.display = 'none';
    stopBtn.style.display  = 'flex';

    clearFeed();
    clearResultTable();
    detectionResults = [];

    const resp = await fetch('/video/webcam/start');
    const data = await resp.json();
    if (data.error) throw new Error(data.error);
    currentSessionId = data.session_id;
    startSSE(currentSessionId);

    webcamInterval = setInterval(() => captureWebcamFrame(videoEl), 3000);
    showToast('Webcam Started', 'Capturing and analyzing frames every 3 seconds.', 'success');
  } catch (err) {
    showToast('Camera Error', err.message || 'Could not access webcam.', 'error');
  }
}

function stopWebcam() {
  if (webcamStream) {
    webcamStream.getTracks().forEach(t => t.stop());
    webcamStream = null;
  }
  if (webcamInterval) { clearInterval(webcamInterval); webcamInterval = null; }
  if (eventSource)    { eventSource.close(); eventSource = null; }
  if (currentSessionId) {
    fetch(`/video/stop/${currentSessionId}`, { method: 'POST', headers: csrfHeaders() });
  }

  const videoEl   = $('webcam-video');
  const overlay   = $('webcam-overlay');
  const activeInd = $('webcam-active-ind');
  const startBtn  = $('webcam-start-btn');
  const stopBtn   = $('webcam-stop-btn');

  if (videoEl)   { videoEl.srcObject = null; }
  if (overlay)   overlay.style.display = 'flex';
  if (activeInd) activeInd.style.display = 'none';
  if (startBtn)  startBtn.style.display = 'flex';
  if (stopBtn)   stopBtn.style.display  = 'none';
  showToast('Webcam Stopped', 'Camera feed ended.', 'info');
}

async function captureWebcamFrame(videoEl) {
  if (!videoEl.srcObject) return;
  const canvas = document.createElement('canvas');
  canvas.width  = videoEl.videoWidth  || 640;
  canvas.height = videoEl.videoHeight || 480;
  canvas.getContext('2d').drawImage(videoEl, 0, 0);

  canvas.toBlob(async blob => {
    if (!blob) return;
    const fd = new FormData();
    fd.append('video', new File([blob], 'webcam_frame.mp4', { type: 'video/mp4' }));
    try {
      await fetch('/video/upload', { method: 'POST', headers: csrfHeaders(), body: fd });
    } catch {}
  }, 'image/jpeg', 0.85);
}

// ── DETECTION CARD ──
function addDetectionCard(result) {
  const feed = $('detection-feed');
  if (!feed) return;

  const empty = feed.querySelector('.feed-empty');
  if (empty) empty.remove();

  const speedClass = result.speed > 90 ? 'high' : result.speed > 60 ? 'mid' : 'low';
  const hasViol    = !!result.violation;

  const card = document.createElement('div');
  card.className = `detection-card ${hasViol ? 'violation' : 'clean'}`;
  card.innerHTML = `
    <div class="det-plate">${result.plate}</div>
    <div class="det-meta">
      <span class="speed-badge ${speedClass}">
        <i class="fas fa-tachometer-alt" style="margin-right:3px;"></i>${result.speed} km/h
      </span>
      ${hasViol
        ? `<span class="viol-badge yes"><i class="fas fa-exclamation-triangle" style="margin-right:3px;"></i>${result.violation}</span>`
        : `<span class="viol-badge none">Clean</span>`}
      <span class="conf-tag">${result.class_name} · ${Math.round(result.confidence * 100)}%</span>
    </div>
    <div class="det-location"><i class="fas fa-map-marker-alt" style="margin-right:4px;color:var(--accent-cyan);"></i>${result.location}</div>
    <div class="det-time">${result.timestamp}</div>`;

  feed.insertBefore(card, feed.firstChild);

  if (feed.children.length > 50) feed.removeChild(feed.lastChild);
}

// ── RESULTS TABLE ──
function addTableRow(result) {
  const tbody = $('results-tbody');
  if (!tbody) return;

  const empty = tbody.querySelector('.empty-row');
  if (empty) empty.remove();

  const speedClass = result.speed > 90 ? 'speed-red' : result.speed > 60 ? 'speed-orange' : 'speed-green';
  const tr = document.createElement('tr');
  tr.className = 'flash-row';
  tr.innerHTML = `
    <td style="font-family:'Rajdhani',sans-serif;font-size:14px;font-weight:700;color:var(--accent-cyan);letter-spacing:1px;">${result.plate}</td>
    <td class="${speedClass}">${result.speed} km/h</td>
    <td>${result.violation
      ? `<span class="badge badge-overspeeding">${result.violation}</span>`
      : `<span class="badge badge-none">—</span>`}</td>
    <td style="font-size:12px;color:var(--text-muted);">${result.camera_id}</td>
    <td style="font-size:12px;color:var(--text-secondary);">${result.timestamp}</td>
    <td>
      ${result.violation
        ? `<span class="badge" style="background:rgba(245,158,11,0.15);color:var(--accent-orange);">Pending</span>`
        : `<span class="badge badge-none">N/A</span>`}
    </td>`;
  tbody.insertBefore(tr, tbody.firstChild);
}

function clearFeed() {
  const feed = $('detection-feed');
  if (!feed) return;
  feed.innerHTML = `
    <div class="feed-empty">
      <i class="fas fa-camera"></i>
      <p>No detections yet.<br/>Upload a video or start webcam.</p>
    </div>`;
}

function clearResultTable() {
  const tbody = $('results-tbody');
  if (!tbody) return;
  tbody.innerHTML = `
    <tr class="empty-row">
      <td colspan="6" style="text-align:center;color:var(--text-muted);padding:24px;font-size:13px;">
        <i class="fas fa-info-circle" style="margin-right:6px;"></i>Results will appear here after analysis
      </td>
    </tr>`;
}

// ── SESSION STATS ──
function updateSessionStats(frameCount, detectCount) {
  const fc = $('stat-frames');
  const dc = $('stat-detects');
  if (fc) fc.textContent = frameCount;
  if (dc) dc.textContent = detectCount;
}

// ── EXPORT CSV ──
function setupExportCsv() {
  const btn = $('export-csv-btn');
  if (!btn) return;
  btn.addEventListener('click', exportCsv);
}

function exportCsv() {
  if (!detectionResults.length) {
    showToast('No Data', 'Run an analysis first to export results.', 'warning');
    return;
  }
  const headers = ['Plate', 'Speed (km/h)', 'Violation', 'Class', 'Location', 'Camera', 'Timestamp'];
  const rows = detectionResults.map(r => [
    r.plate, r.speed, r.violation || '', r.class_name, r.location, r.camera_id, r.timestamp
  ]);
  const csv = [headers, ...rows].map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `streetwatch_results_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Exported', `${detectionResults.length} records saved to CSV.`, 'success');
}
