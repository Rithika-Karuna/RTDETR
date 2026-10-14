import './style.css';
import { getRailwayDashboardHTML, getAlertHistoryHTML, getAdminPanelHTML, DashboardController } from './dashboard';

// ============================================================
// Types & Interfaces
// ============================================================
interface Detection {
  class_name: string;
  confidence: number;
  box: { x: number; y: number; width: number; height: number };
  distance_m?: number;
  track_id?: number;
  zone?: string;
  zone_label?: string;
  movement_state?: string;
  duration_on_track?: number;
}

interface ApiResponse {
  image?: string;
  detections: Detection[];
  frame_width?: number;
  frame_height?: number;
  zones?: any;
  pipeline?: boolean;
  tracking?: any;
  risk?: any;
  train?: any;
  all_trains?: any[];
  location?: any;
  alert?: any;
  pipeline_ms?: number;
  frame_id?: number;
}

// ============================================================
// SVG Icons
// ============================================================
const icons = {
  eye: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`,
  settings: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`,
  image: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>`,
  video: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>`,
  camera: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>`,
  upload: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/></svg>`,
  play: `<svg viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>`,
  pause: `<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`,
  square: `<svg viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>`,
  zap: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
  target: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>`,
  cameraSnapshot: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>`,
  download: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`,
  split: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="12" y1="3" x2="12" y2="21"/></svg>`,
  alert: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  search: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
  ruler: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>`,
  box: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>`,
  clock: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
  cpu: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="15" x2="23" y2="15"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="15" x2="4" y2="15"/></svg>`,
  moon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`,
  sun: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`,
};

// Theme Toggle Button HTML Generator
function getThemeToggleBtnHTML(id: string): string {
  return `
    <button class="theme-switch-btn" id="${id}" role="switch" aria-checked="false" title="Switch to Light Mode" aria-label="Toggle Dark and Light Mode">
      <span class="theme-switch-track">
        <span class="theme-switch-icon icon-moon">${icons.moon}</span>
        <span class="theme-switch-icon icon-sun">${icons.sun}</span>
        <span class="theme-switch-thumb"></span>
      </span>
      <span class="theme-switch-label">Dark Mode</span>
    </button>
  `;
}

// ============================================================
// Web Audio Radar Alert Synthesizer
// ============================================================
class RadarAudio {
  private ctx: AudioContext | null = null;
  public enabled = false;

  public ping(frequency = 880) {
    if (!this.enabled) return;
    try {
      if (!this.ctx) {
        const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        this.ctx = new AudioCtx();
      }
      if (this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(frequency, this.ctx.currentTime);
      gain.gain.setValueAtTime(0.12, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.18);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.18);
    } catch {
      // Audio context might be restricted before interaction
    }
  }
}

const radarAudio = new RadarAudio();

// ============================================================
// Application HTML Structure
// ============================================================
const appHtml = `
  <!-- Page Navigation Tabs & Global Theme Switcher -->
  <nav class="page-nav" id="page-nav">
    <div class="page-nav-tabs">
      <button class="page-nav-tab active" data-page="detection">🔍 Detection</button>
      <button class="page-nav-tab" data-page="railway">🛤️ Railway Monitor</button>
      <button class="page-nav-tab" data-page="history">📋 Alert History</button>
      <button class="page-nav-tab" data-page="admin">⚙️ Admin</button>
    </div>
    <div class="page-nav-actions">
      ${getThemeToggleBtnHTML('nav-theme-toggle')}
    </div>
  </nav>

  <!-- Detection Page (existing) -->
  <div class="page-content active" id="page-detection">
  <!-- Header Bar -->
  <header class="app-header">
    <div class="header-brand">
      <div class="brand-icon-wrapper">
        ${icons.eye}
      </div>
      <div class="brand-info">
        <h1 class="app-title">VisionDetect AI <span class="app-version-badge">PRO</span></h1>
        <p class="app-subtitle">High-FPS Neural Object Detection &amp; Spatial Distance Engine</p>
      </div>
    </div>

    <div class="header-actions">
      <!-- Dark / Light Mode Toggle -->
      ${getThemeToggleBtnHTML('header-theme-toggle')}

      <div class="header-badge">
        <span class="dot"></span>
        <span id="backend-status-badge">Engine Active</span>
      </div>
    </div>
  </header>

  <!-- Proximity Warning Banner -->
  <div class="proximity-alert-banner" id="proximity-alert">
    <div class="alert-content">
      ${icons.alert}
      <span id="proximity-text">CRITICAL PROXIMITY: Object detected under 1.5m distance!</span>
    </div>
    <span class="proximity-warning-tag">PROXIMITY WARNING</span>
  </div>

  <!-- Main Layout -->
  <div class="main-layout">
    <!-- Sidebar Control Station -->
    <aside class="sidebar">
      <!-- Model & Performance Settings -->
      <div class="glass-panel">
        <div class="panel-title">${icons.settings} Model &amp; Performance</div>
        
        <div class="control-group">
          <label class="control-label" for="model-select">AI Detection Network</label>
          <select id="model-select">
            <option value="yolo11m" selected>Enhanced RT-DETR</option>
            <option value="yolo11m">YOLO11 Medium — State-of-the-Art Power (51.5 mAP)</option>
            <option value="yolo11s">YOLO11 Small — Ultra High-Speed (47.0 mAP)</option>
          </select>
        </div>

        <div class="control-group">
          <div class="control-label">
            <span>Confidence Threshold</span>
            <span class="label-value" id="conf-val-display">35%</span>
          </div>
          <input type="range" class="slider-input" id="conf-slider" min="10" max="90" value="35" step="5" />
        </div>

        <div class="control-group">
          <label class="control-label" for="resolution-select">Stream Resolution (FPS Booster)</label>
          <select id="resolution-select">
            <option value="480">Fast 480p (Ultra 30+ FPS)</option>
            <option value="640" selected>Balanced 640p (Native Model)</option>
            <option value="native">Native HD (Detailed)</option>
          </select>
        </div>

        <div class="toggle-row">
          <span>Radar Audio Alert</span>
          <label class="toggle-switch">
            <input type="checkbox" id="audio-alert-toggle" />
            <span class="toggle-slider"></span>
          </label>
        </div>

        <div class="toggle-row" style="margin-top:0.75rem; padding-top:0.75rem; border-top:1px solid var(--glass-border);">
          <div style="display:flex; flex-direction:column;">
            <span style="font-weight:600; color:var(--text-primary); font-size:0.85rem;">🛤️ Railway Risk Engine</span>
            <span style="font-size:0.68rem; color:var(--text-secondary);">Track zones, risk scoring &amp; alerts</span>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" id="railway-pipeline-toggle" checked />
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>

      <!-- Detection Source Station -->
      <div class="glass-panel">
        <div class="panel-title">${icons.zap} Input Source</div>
        
        <div class="mode-tabs">
          <button class="mode-tab active" data-mode="video">${icons.video} Video</button>
          <button class="mode-tab" data-mode="image">${icons.image} Image</button>
          <button class="mode-tab" data-mode="webcam">${icons.camera} Live</button>
        </div>

        <!-- Video Mode Controls -->
        <div class="mode-content active" id="mode-video">
          <div class="drop-zone" id="video-drop-zone">
            ${icons.upload}
            <div class="drop-zone-text">
              <strong>Select or Drop Video</strong><br/>MP4, WEBM, MOV, AVI
            </div>
            <input type="file" id="video-upload" accept="video/*" />
          </div>

          <div class="control-group" style="margin-top:0.85rem;">
            <label class="control-label" for="fps-mode-select">Video Playback Engine</label>
            <select id="fps-mode-select">
              <option value="smooth" selected>🚀 Butter-Smooth 60 FPS (Native Video + AI Overlay)</option>
              <option value="synced">⏱️ Frame-by-Frame Synced Detection</option>
              <option value="server-stream">📡 Server Annotated Stream</option>
            </select>
          </div>

          <div class="control-group">
            <label class="control-label" for="video-speed-select">Playback Speed</label>
            <select id="video-speed-select">
              <option value="0.5">0.5x Slow Motion</option>
              <option value="1" selected>1.0x Normal Speed</option>
              <option value="1.5">1.5x Fast Scan</option>
              <option value="2">2.0x Double Speed</option>
            </select>
          </div>

          <div class="btn-group" style="margin-top:0.6rem;">
            <button class="btn btn-primary" id="video-play-btn" disabled>${icons.play} Start Detection</button>
            <button class="btn btn-secondary" id="video-pause-btn" disabled>${icons.pause} Pause</button>
            <button class="btn btn-danger" id="video-stop-btn" disabled>${icons.square} Stop</button>
          </div>
        </div>

        <!-- Image Mode Controls -->
        <div class="mode-content" id="mode-image">
          <div class="drop-zone" id="image-drop-zone">
            ${icons.upload}
            <div class="drop-zone-text">
              <strong>Select or Drop Image</strong><br/>JPG, PNG, WEBP
            </div>
            <input type="file" id="image-upload" accept="image/*" />
          </div>
        </div>

        <!-- Live Camera Mode Controls -->
        <div class="mode-content" id="mode-webcam">
          <div class="btn-group" style="margin-top:0.6rem;">
            <button class="btn btn-primary btn-full" id="start-webcam-btn">${icons.camera} Start Camera</button>
          </div>
          <div class="btn-group" style="margin-top:0.4rem;">
            <button class="btn btn-danger btn-full" id="stop-webcam-btn" disabled>${icons.square} Stop Camera</button>
          </div>
        </div>
      </div>

      <!-- Live Status -->
      <div class="status-bar" id="status-bar">
        <span class="status-dot"></span>
        <span id="status-text">Ready — load video or image</span>
      </div>
    </aside>

    <!-- Main Content & Viewport -->
    <main class="content-area">
      <!-- Telemetry KPI Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">${icons.cpu}</div>
          <div class="stat-info">
            <span class="stat-value fps-high" id="kpi-fps">0</span>
            <span class="stat-label">Processed FPS</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">${icons.target}</div>
          <div class="stat-info">
            <span class="stat-value" id="kpi-objects">0</span>
            <span class="stat-label">Objects in Frame</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">${icons.ruler}</div>
          <div class="stat-info">
            <span class="stat-value" id="kpi-nearest">—</span>
            <span class="stat-label">Nearest Distance</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">${icons.clock}</div>
          <div class="stat-info">
            <span class="stat-value" id="kpi-latency">—</span>
            <span class="stat-label">Latency (ms)</span>
          </div>
        </div>
      </div>

      <!-- Viewport Display -->
      <div class="display-viewport" id="viewport-container">
        <!-- Floating HUD Actions -->
        <div class="viewport-hud">
          <button class="hud-btn" id="hud-split-toggle" title="Toggle Split Screen Comparison">
            ${icons.split} Split View
          </button>
          <button class="hud-btn" id="hud-snapshot-btn" title="Download Current Annotated Snapshot">
            ${icons.cameraSnapshot} Snapshot
          </button>
        </div>

        <div class="placeholder" id="placeholder">
          <div class="placeholder-icon">${icons.target}</div>
          <div class="placeholder-title">No Active Media Feed</div>
          <div class="placeholder-desc">Upload a video or image, or start the webcam to begin real-time high-speed object detection.</div>
        </div>

        <div class="viewport-media-wrapper" id="viewport-media-wrapper">
          <video id="source-video" playsinline muted style="display:none;"></video>
          <video id="webcam-video" autoplay playsinline muted style="display:none;"></video>
          <canvas id="detection-overlay-canvas" class="detection-overlay-canvas" style="display:none;"></canvas>
          <img id="result-image" style="display:none;" alt="Neural Detection Output" />
        </div>
        <canvas id="work-canvas" style="display:none;"></canvas>

        <!-- Interactive Center Play/Pause Overlay -->
        <div class="viewport-play-overlay" id="viewport-play-overlay" style="display:none;">
          <button class="center-play-btn" id="center-play-btn" title="Toggle Play / Pause">
            ${icons.play}
          </button>
        </div>

        <!-- Split Screen View Container -->
        <div class="split-view-container" id="split-view">
          <div class="split-pane">
            <span class="split-pane-label">ORIGINAL INPUT</span>
            <video id="split-source-video" playsinline muted style="max-width:100%; max-height:100%; object-fit:contain;"></video>
            <img id="split-source-img" style="display:none; max-width:100%; max-height:100%; object-fit:contain;" />
          </div>
          <div class="split-pane">
            <span class="split-pane-label">AI DETECTION &amp; DISTANCE</span>
            <img id="split-result-img" style="max-width:100%; max-height:100%; object-fit:contain;" />
          </div>
        </div>
      </div>

      <!-- Video Progress & Seek Bar -->
      <div class="video-toolbar" id="video-toolbar" style="display:none;">
        <button class="btn btn-primary" id="tb-play-btn" style="padding: 6px 14px; font-size: 0.78rem;">
          ${icons.play} <span id="tb-play-text">Start Detection</span>
        </button>
        <button class="btn btn-secondary" id="tb-pause-btn" style="padding: 6px 10px; font-size: 0.78rem;" disabled>
          ${icons.pause} Pause
        </button>
        <div class="video-progress-container">
          <div class="video-progress-bar" id="video-seek-bar">
            <div class="video-progress-fill" id="video-seek-fill"></div>
          </div>
          <span class="video-time-text" id="video-time-display">0:00 / 0:00</span>
        </div>
        <div class="tb-actions">
          <select id="tb-speed-select" class="tb-speed-select" title="Playback Speed">
            <option value="0.5">0.5x</option>
            <option value="1" selected>1.0x</option>
            <option value="1.5">1.5x</option>
            <option value="2">2.0x</option>
          </select>
          <button class="btn btn-secondary" id="video-loop-toggle" style="font-size:0.75rem; padding: 4px 10px;">Loop: ON</button>
        </div>
      </div>

      <!-- Breakdown Chips Bar -->
      <div class="breakdown-bar" id="breakdown-bar" style="display:none;">
        <span class="breakdown-label">Detected Classes:</span>
        <div class="breakdown-chips" id="breakdown-chips"></div>
      </div>

      <!-- Detections List & Filter Station -->
      <div class="detections-panel glass-panel" id="detections-panel" style="display:none;">
        <div class="detections-header">
          <div class="detections-title-wrapper">
            <span class="detections-title">Detected Objects</span>
            <span class="detections-badge" id="detections-count">0</span>
          </div>

          <div style="display:flex; gap:8px;">
            <button class="btn btn-secondary" id="export-json-btn" style="padding:4px 10px; font-size:0.75rem;">
              ${icons.download} Export JSON
            </button>
            <button class="btn btn-secondary" id="copy-summary-btn" style="padding:4px 10px; font-size:0.75rem;">
              Copy List
            </button>
          </div>
        </div>

        <!-- Filter & Search Bar -->
        <div class="filter-bar" style="padding: 0 1.25rem 0.25rem; display:flex; flex-direction:column; gap:8px;">
          <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
            <div class="search-box" style="flex:1; min-width:200px;">
              ${icons.search}
              <input type="text" id="class-search-input" placeholder="Search detected objects (e.g. person, car)..." />
            </div>

            <div class="category-pills" id="category-pills">
              <button class="category-pill active" data-category="all">All Types</button>
              <button class="category-pill" data-category="person">People</button>
              <button class="category-pill" data-category="vehicle">Vehicles</button>
              <button class="category-pill" data-category="animal">Animals</button>
            </div>
          </div>

          <div class="zone-filter-pills" id="zone-filter-pills">
            <span style="font-size:0.75rem; color:var(--text-tertiary); font-weight:600; margin-right:4px;">Zone:</span>
            <button class="zone-filter-pill active" data-zone="all">All Zones</button>
            <button class="zone-filter-pill pill-safe" data-zone="safe">🛡️ Safe Zone</button>
            <button class="zone-filter-pill pill-medium" data-zone="medium">⚠️ Medium Zone</button>
            <button class="zone-filter-pill pill-danger" data-zone="danger">🚨 Danger Zone</button>
          </div>
        </div>

        <!-- Detections Grid -->
        <div class="detections-grid" id="detections-grid">
          <div class="detections-empty">No objects detected.</div>
        </div>
      </div>
    </main>
  </div>
  </div><!-- end page-detection -->

  <!-- Railway Monitor Page -->
  <div class="page-content" id="page-railway"></div>

  <!-- Alert History Page -->
  <div class="page-content" id="page-history"></div>

  <!-- Admin Page -->
  <div class="page-content" id="page-admin"></div>
`;

// Mount safely (handles #app, #root, or dynamically creates #app if missing)
let appRoot = document.querySelector<HTMLDivElement>('#app') || document.querySelector<HTMLDivElement>('#root');
if (!appRoot) {
  appRoot = document.createElement('div');
  appRoot.id = 'app';
  document.body.appendChild(appRoot);
} else {
  appRoot.id = 'app';
}
appRoot.innerHTML = appHtml;

// ============================================================
// State Management
// ============================================================
let currentMode: 'video' | 'image' | 'webcam' = 'video';
type AppTheme = 'dark' | 'light';
let currentTheme: AppTheme = 'dark';
let ws: WebSocket | null = null;
let webcamStream: MediaStream | null = null;
let isWebcamRunning = false;

// Video state
let isVideoProcessing = false;
let isVideoPaused = false;
let videoFile: File | null = null;
let videoLoop = true;
let isWsInFlight = false;
let videoAnimFrameId: number | null = null;

// Telemetry & metrics
let fpsFrameCount = 0;
let lastFpsTimestamp = performance.now();
let lastFrameSentTime = 0;
let currentDetections: Detection[] = [];
let isSplitView = false;
let activeCategoryFilter = 'all';
let activeZoneFilter = 'all';
let searchQuery = '';

// Smooth overlay state & geometry
let latestFrameWidth = 640;
let latestFrameHeight = 480;
let latestZones: any = null;
let latestTracking: any = null;
let latestRisk: any = null;

// ============================================================
// DOM References
// ============================================================
const modelSelect = document.getElementById('model-select') as HTMLSelectElement;
const confSlider = document.getElementById('conf-slider') as HTMLInputElement;
const confValDisplay = document.getElementById('conf-val-display') as HTMLSpanElement;
const resolutionSelect = document.getElementById('resolution-select') as HTMLSelectElement;
const audioAlertToggle = document.getElementById('audio-alert-toggle') as HTMLInputElement;
const proximityAlert = document.getElementById('proximity-alert') as HTMLDivElement;
const proximityText = document.getElementById('proximity-text') as HTMLSpanElement;

// Mode tabs
const modeTabs = document.querySelectorAll<HTMLButtonElement>('.mode-tab');
const modeContents = document.querySelectorAll<HTMLDivElement>('.mode-content');

// Video elements
const videoUpload = document.getElementById('video-upload') as HTMLInputElement;
const videoDropZone = document.getElementById('video-drop-zone') as HTMLDivElement;
const fpsModeSelect = document.getElementById('fps-mode-select') as HTMLSelectElement;
const videoSpeedSelect = document.getElementById('video-speed-select') as HTMLSelectElement;
const videoPlayBtn = document.getElementById('video-play-btn') as HTMLButtonElement;
const videoPauseBtn = document.getElementById('video-pause-btn') as HTMLButtonElement;
const videoStopBtn = document.getElementById('video-stop-btn') as HTMLButtonElement;
const videoToolbar = document.getElementById('video-toolbar') as HTMLDivElement;
const videoSeekBar = document.getElementById('video-seek-bar') as HTMLDivElement;
const videoSeekFill = document.getElementById('video-seek-fill') as HTMLDivElement;
const videoTimeDisplay = document.getElementById('video-time-display') as HTMLSpanElement;
const videoLoopToggle = document.getElementById('video-loop-toggle') as HTMLButtonElement;
const tbPlayBtn = document.getElementById('tb-play-btn') as HTMLButtonElement;
const tbPlayText = document.getElementById('tb-play-text') as HTMLSpanElement;
const tbPauseBtn = document.getElementById('tb-pause-btn') as HTMLButtonElement;
const tbSpeedSelect = document.getElementById('tb-speed-select') as HTMLSelectElement;
const viewportContainer = document.getElementById('viewport-container') as HTMLDivElement;
const viewportPlayOverlay = document.getElementById('viewport-play-overlay') as HTMLDivElement;
const centerPlayBtn = document.getElementById('center-play-btn') as HTMLButtonElement;

// Image & Camera elements
const imageUpload = document.getElementById('image-upload') as HTMLInputElement;
const imageDropZone = document.getElementById('image-drop-zone') as HTMLDivElement;
const startWebcamBtn = document.getElementById('start-webcam-btn') as HTMLButtonElement;
const stopWebcamBtn = document.getElementById('stop-webcam-btn') as HTMLButtonElement;

// Viewport elements
const placeholder = document.getElementById('placeholder') as HTMLDivElement;
const resultImage = document.getElementById('result-image') as HTMLImageElement;
const sourceVideo = document.getElementById('source-video') as HTMLVideoElement;
const webcamVideo = document.getElementById('webcam-video') as HTMLVideoElement;
const detectionOverlayCanvas = document.getElementById('detection-overlay-canvas') as HTMLCanvasElement;
const workCanvas = document.getElementById('work-canvas') as HTMLCanvasElement;
const splitView = document.getElementById('split-view') as HTMLDivElement;
const splitSourceVideo = document.getElementById('split-source-video') as HTMLVideoElement;
const splitSourceImg = document.getElementById('split-source-img') as HTMLImageElement;
const splitResultImg = document.getElementById('split-result-img') as HTMLImageElement;
const hudSplitToggle = document.getElementById('hud-split-toggle') as HTMLButtonElement;
const hudSnapshotBtn = document.getElementById('hud-snapshot-btn') as HTMLButtonElement;

// KPI cards
const kpiFps = document.getElementById('kpi-fps') as HTMLSpanElement;
const kpiObjects = document.getElementById('kpi-objects') as HTMLSpanElement;
const kpiNearest = document.getElementById('kpi-nearest') as HTMLSpanElement;
const kpiLatency = document.getElementById('kpi-latency') as HTMLSpanElement;

// Status & outputs
const statusBar = document.getElementById('status-bar') as HTMLDivElement;
const statusText = document.getElementById('status-text') as HTMLSpanElement;
const breakdownBar = document.getElementById('breakdown-bar') as HTMLDivElement;
const breakdownChips = document.getElementById('breakdown-chips') as HTMLDivElement;
const detectionsPanel = document.getElementById('detections-panel') as HTMLDivElement;
const detectionsCount = document.getElementById('detections-count') as HTMLSpanElement;
const detectionsGrid = document.getElementById('detections-grid') as HTMLDivElement;
const classSearchInput = document.getElementById('class-search-input') as HTMLInputElement;
const categoryPills = document.querySelectorAll<HTMLButtonElement>('.category-pill');
const zoneFilterPills = document.querySelectorAll<HTMLButtonElement>('.zone-filter-pill');
const exportJsonBtn = document.getElementById('export-json-btn') as HTMLButtonElement;
const copySummaryBtn = document.getElementById('copy-summary-btn') as HTMLButtonElement;

// ============================================================
// Dark & Light Mode Theme Management
// ============================================================
function initTheme() {
  const saved = localStorage.getItem('vision_theme') as AppTheme | null;
  if (saved === 'light' || saved === 'dark') {
    currentTheme = saved;
  } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
    currentTheme = 'light';
  } else {
    currentTheme = 'dark';
  }
  applyTheme(currentTheme);

  document.querySelectorAll<HTMLButtonElement>('.theme-switch-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const nextTheme: AppTheme = currentTheme === 'dark' ? 'light' : 'dark';
      applyTheme(nextTheme);
    });
  });
}

function applyTheme(theme: AppTheme) {
  currentTheme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('vision_theme', theme);

  const isLight = theme === 'light';
  document.querySelectorAll<HTMLButtonElement>('.theme-switch-btn').forEach(btn => {
    btn.setAttribute('aria-checked', String(isLight));
    btn.title = isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode';
    const label = btn.querySelector('.theme-switch-label');
    if (label) {
      label.textContent = isLight ? 'Light Mode' : 'Dark Mode';
    }
  });
}

initTheme();

// ============================================================
// Audio Radar & Proximity Handlers
// ============================================================
audioAlertToggle.addEventListener('change', () => {
  radarAudio.enabled = audioAlertToggle.checked;
  if (audioAlertToggle.checked) {
    radarAudio.ping(950);
  }
});

function checkProximityAlert(detections: Detection[]) {
  let closestDist = Infinity;
  let closestName = '';

  for (const d of detections) {
    if (d.distance_m !== undefined && d.distance_m < closestDist) {
      closestDist = d.distance_m;
      closestName = d.class_name;
    }
  }

  if (closestDist < Infinity) {
    kpiNearest.textContent = `${closestDist.toFixed(1)}m (${closestName})`;
  } else {
    kpiNearest.textContent = '—';
  }

  // Critical proximity threshold < 1.5m
  if (closestDist < 1.5) {
    proximityAlert.classList.add('active');
    proximityText.textContent = `CRITICAL PROXIMITY: ${closestName.toUpperCase()} detected at ${closestDist.toFixed(1)}m distance!`;
    radarAudio.ping(1100);
  } else {
    proximityAlert.classList.remove('active');
  }
}

// ============================================================
// Helpers & Visual Status
// ============================================================
function setStatus(text: string, type: '' | 'active' | 'error' | 'processing' = '') {
  statusText.textContent = text;
  statusBar.className = 'status-bar' + (type ? ` ${type}` : '');
}

function updateConfidenceDisplay() {
  confValDisplay.textContent = `${confSlider.value}%`;
}

confSlider.addEventListener('input', updateConfidenceDisplay);

function formatTime(seconds: number): string {
  if (isNaN(seconds)) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s < 10 ? '0' : ''}${s}`;
}

// ============================================================
// Detection Rendering & Categorization
// ============================================================
const categoryMap: Record<string, string[]> = {
  person: ['person'],
  vehicle: ['car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'bicycle'],
  animal: ['bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe'],
};

function matchesFilter(d: Detection): boolean {
  if (activeZoneFilter !== 'all') {
    const z = (d.zone || 'SAFE').toUpperCase();
    if (activeZoneFilter === 'safe' && z !== 'SAFE') return false;
    if (activeZoneFilter === 'medium' && z !== 'MEDIUM' && z !== 'WARNING') return false;
    if (activeZoneFilter === 'danger' && z !== 'DANGER') return false;
  }
  if (activeCategoryFilter !== 'all') {
    const list = categoryMap[activeCategoryFilter] || [];
    if (!list.includes(d.class_name.toLowerCase())) {
      return false;
    }
  }
  if (searchQuery) {
    if (!d.class_name.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
  }
  return true;
}

function renderDetectionCards(detections: Detection[]) {
  detectionsPanel.style.display = 'flex';
  detectionsCount.textContent = String(detections.length);

  // Breakdown Chips
  renderBreakdownChips(detections);

  // Proximity check
  checkProximityAlert(detections);

  // Filter detections
  const filtered = detections.filter(matchesFilter);

  if (filtered.length === 0) {
    detectionsGrid.innerHTML = `<div class="detections-empty">No matching objects found. ${detections.length > 0 ? `(${detections.length} total filtered out)` : ''}</div>`;
    return;
  }

  detectionsGrid.innerHTML = filtered.map(d => {
    const confPct = Math.round(d.confidence * 100);
    const confLevel = confPct >= 75 ? 'high' : confPct >= 45 ? 'medium' : 'low';
    const isClose = d.distance_m !== undefined && d.distance_m < 1.5;
    const zone = (d.zone || 'SAFE').toUpperCase();
    const isDanger = zone === 'DANGER';
    const isMedium = zone === 'MEDIUM' || zone === 'WARNING';
    const zoneClass = isDanger ? 'zone-danger' : isMedium ? 'zone-medium' : 'zone-safe';
    const zoneLabel = isDanger ? 'DANGER ZONE' : isMedium ? 'MEDIUM ZONE' : 'SAFE ZONE';
    const zoneIcon = isDanger ? '🚨' : isMedium ? '⚠️' : '🛡️';

    return `
      <div class="detection-card ${zoneClass}-card ${isClose ? 'close-proximity' : ''}">
        <div class="detection-card-header">
          <div class="class-and-zone">
            <span class="detection-class">${d.class_name}</span>
            <span class="zone-badge ${zoneClass}">${zoneIcon} ${zoneLabel}</span>
          </div>
          <span class="detection-conf ${confLevel}">${confPct}%</span>
        </div>
        <div class="detection-details">
          <span class="detail-item ${isClose ? 'proximity-danger' : ''}">
            ${icons.ruler} ${d.distance_m !== undefined ? `${d.distance_m}m` : 'N/A'}
          </span>
          <span class="detail-item">
            ${icons.box} ${d.box.width}×${d.box.height}
          </span>
        </div>
      </div>
    `;
  }).join('');
}

function renderBreakdownChips(detections: Detection[]) {
  if (detections.length === 0) {
    breakdownBar.style.display = 'none';
    return;
  }

  breakdownBar.style.display = 'flex';

  // Zone summary counts
  const safeCount = detections.filter(d => (d.zone || 'SAFE').toUpperCase() === 'SAFE').length;
  const mediumCount = detections.filter(d => ['MEDIUM', 'WARNING'].includes((d.zone || '').toUpperCase())).length;
  const dangerCount = detections.filter(d => (d.zone || '').toUpperCase() === 'DANGER').length;

  const zoneChipsHtml = `
    <div class="breakdown-chip chip-safe" title="Objects in Safe Zone">
      <span>🛡️ Safe</span>
      <span class="chip-count">${safeCount}</span>
    </div>
    <div class="breakdown-chip chip-medium" title="Objects in Medium Buffer Zone">
      <span>⚠️ Medium</span>
      <span class="chip-count">${mediumCount}</span>
    </div>
    <div class="breakdown-chip chip-danger" title="Objects in Danger Track Zone">
      <span>🚨 Danger</span>
      <span class="chip-count">${dangerCount}</span>
    </div>
  `;

  const counts: Record<string, number> = {};
  for (const d of detections) {
    counts[d.class_name] = (counts[d.class_name] || 0) + 1;
  }

  const classChipsHtml = Object.entries(counts).map(([name, count]) => `
    <div class="breakdown-chip">
      <span>${name}</span>
      <span class="chip-count">${count}</span>
    </div>
  `).join('');

  breakdownChips.innerHTML = zoneChipsHtml + classChipsHtml;
}

// Category filter pills
categoryPills.forEach(pill => {
  pill.addEventListener('click', () => {
    categoryPills.forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    activeCategoryFilter = pill.dataset.category || 'all';
    renderDetectionCards(currentDetections);
  });
});

// Zone filter pills
zoneFilterPills.forEach(pill => {
  pill.addEventListener('click', () => {
    zoneFilterPills.forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    activeZoneFilter = (pill.dataset.zone || 'all') as typeof activeZoneFilter;
    renderDetectionCards(currentDetections);
  });
});

classSearchInput.addEventListener('input', () => {
  searchQuery = classSearchInput.value.trim();
  renderDetectionCards(currentDetections);
});

// ============================================================
// FPS & Performance Telemetry
// ============================================================
function updateFpsCounter() {
  fpsFrameCount++;
  const now = performance.now();
  const elapsed = now - lastFpsTimestamp;

  if (elapsed >= 500) {
    const calculatedFps = Math.round((fpsFrameCount / elapsed) * 1000);
    kpiFps.textContent = String(calculatedFps);
    kpiFps.className = `stat-value ${calculatedFps >= 20 ? 'fps-high' : calculatedFps >= 12 ? 'fps-mid' : 'fps-low'}`;
    fpsFrameCount = 0;
    lastFpsTimestamp = now;
  }
}

// ============================================================
// Frame Resolution Optimization
// ============================================================
function getTargetDimensions(originalWidth: number, originalHeight: number): { width: number; height: number } {
  const mode = resolutionSelect.value;
  if (mode === 'native' || originalWidth === 0) {
    return { width: originalWidth, height: originalHeight };
  }
  const targetWidth = mode === '480' ? 480 : 640;
  if (originalWidth <= targetWidth) {
    return { width: originalWidth, height: originalHeight };
  }
  const aspectRatio = originalHeight / originalWidth;
  return {
    width: targetWidth,
    height: Math.round(targetWidth * aspectRatio),
  };
}

// ============================================================
// WebSocket Pipeline
// ============================================================
let wsWatchdogTimer: ReturnType<typeof setTimeout> | null = null;

function getWebSocketUrl(): string {
  const loc = window.location;
  const protocol = loc.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = loc.hostname || 'localhost';
  return `${protocol}//${host}:8000/ws/detect/stream`;
}

function ensureWebSocket(): Promise<WebSocket> {
  return new Promise((resolve, reject) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      resolve(ws);
      return;
    }
    if (ws && ws.readyState === WebSocket.CONNECTING) {
      const poll = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          clearInterval(poll);
          resolve(ws);
        } else if (!ws || ws.readyState === WebSocket.CLOSED) {
          clearInterval(poll);
          reject(new Error('WebSocket connection failed'));
        }
      }, 50);
      return;
    }

    try {
      ws = new WebSocket(getWebSocketUrl());
    } catch (e) {
      reject(e);
      return;
    }

    ws.onopen = () => {
      setStatus('Neural Engine Connected', 'active');
      resolve(ws!);
    };

    ws.onmessage = (event) => {
      isWsInFlight = false;
      if (wsWatchdogTimer) {
        clearTimeout(wsWatchdogTimer);
        wsWatchdogTimer = null;
      }

      const latency = Math.round(performance.now() - lastFrameSentTime);
      kpiLatency.textContent = `${latency}`;

      try {
        const data: ApiResponse = JSON.parse(event.data);
        if (data && data.detections !== undefined) {
          handleFrameDetectionResult(data);
        }
      } catch (e) {
        console.error('Failed to parse detection frame:', e);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      setStatus('WebSocket Engine Error', 'error');
      isWsInFlight = false;
      if (wsWatchdogTimer) {
        clearTimeout(wsWatchdogTimer);
        wsWatchdogTimer = null;
      }
      reject(err);
    };

    ws.onclose = () => {
      isWsInFlight = false;
      if (wsWatchdogTimer) {
        clearTimeout(wsWatchdogTimer);
        wsWatchdogTimer = null;
      }
      ws = null;
    };
  });
}

function handleFrameDetectionResult(data: ApiResponse) {
  currentDetections = data.detections || [];
  kpiObjects.textContent = String(currentDetections.length);

  latestFrameWidth = data.frame_width || 640;
  latestFrameHeight = data.frame_height || 480;
  if (data.zones !== undefined) latestZones = data.zones;
  latestTracking = data.tracking || null;
  latestRisk = data.risk || null;

  // Nearest distance telemetry from all detected/tracked objects
  const allObjects = [
    ...(data.detections || []),
    ...((data.tracking && data.tracking.tracked_objects) ? data.tracking.tracked_objects : [])
  ];
  const validDistances = allObjects
    .map((d: any) => d.distance_m)
    .filter((d: any) => typeof d === 'number' && d > 0);
  if (validDistances.length > 0) {
    const minD = Math.min(...validDistances);
    kpiNearest.textContent = `${minD.toFixed(1)}m`;
    kpiNearest.className = `stat-value ${minD < 1.5 ? 'fps-low' : minD < 3.0 ? 'fps-mid' : 'fps-high'}`;

    if (minD < 1.5) {
      proximityAlert.classList.add('visible');
      proximityText.textContent = `CRITICAL PROXIMITY: Object detected under ${minD.toFixed(1)}m distance!`;
      radarAudio.ping(1100);
    } else {
      proximityAlert.classList.remove('visible');
    }
  } else {
    kpiNearest.textContent = '—';
    proximityAlert.classList.remove('visible');
  }

  placeholder.style.display = 'none';

  // If in server-stream mode, or if not processing video (e.g. single image mode), display resultImage
  if (data.image && (fpsModeSelect.value === 'server-stream' || !isVideoProcessing)) {
    resultImage.style.display = 'block';
    resultImage.src = data.image;
    if (isSplitView) {
      splitResultImg.src = data.image;
    }
  }

  updateFpsCounter();
  renderDetectionCards(currentDetections);
  renderDetectionOverlay();
}

// ============================================================
// Real-Time Canvas Overlay Renderer (Butter-Smooth 60 FPS)
// ============================================================
function renderDetectionOverlay() {
  if (!detectionOverlayCanvas || !sourceVideo) return;
  const ctx = detectionOverlayCanvas.getContext('2d');
  if (!ctx) return;

  const activeVideo = currentMode === 'webcam' ? webcamVideo : sourceVideo;
  const vWidth = activeVideo.videoWidth || activeVideo.clientWidth || 640;
  const vHeight = activeVideo.videoHeight || activeVideo.clientHeight || 480;

  if (vWidth === 0 || vHeight === 0) return;

  if (detectionOverlayCanvas.width !== vWidth || detectionOverlayCanvas.height !== vHeight) {
    detectionOverlayCanvas.width = vWidth;
    detectionOverlayCanvas.height = vHeight;
  }

  // Ensure canvas CSS size strictly matches the video client rectangle
  if (activeVideo.clientWidth > 0 && activeVideo.clientHeight > 0) {
    const cssW = `${activeVideo.clientWidth}px`;
    const cssH = `${activeVideo.clientHeight}px`;
    if (detectionOverlayCanvas.style.width !== cssW) detectionOverlayCanvas.style.width = cssW;
    if (detectionOverlayCanvas.style.height !== cssH) detectionOverlayCanvas.style.height = cssH;
  }

  ctx.clearRect(0, 0, vWidth, vHeight);

  const frameW = latestFrameWidth > 0 ? latestFrameWidth : vWidth;
  const frameH = latestFrameHeight > 0 ? latestFrameHeight : vHeight;
  const scaleX = vWidth / frameW;
  const scaleY = vHeight / frameH;

  // 1. Draw Railway Track Zones if enabled
  if (isPipelineMode && latestZones) {
    drawTrackZonesOnCanvas(ctx, latestZones, vWidth, vHeight);
  }

  // 2. Combine detections so nothing is missed!
  const objectsToDraw: any[] = [];
  if (latestTracking && latestTracking.tracked_objects && latestTracking.tracked_objects.length > 0) {
    objectsToDraw.push(...latestTracking.tracked_objects);
  } else if (currentDetections && currentDetections.length > 0) {
    objectsToDraw.push(...currentDetections);
  }

  for (const obj of objectsToDraw) {
    drawObjectOnCanvas(ctx, obj, scaleX, scaleY);
  }

  // 3. Draw Top-Right AI HUD Badge
  drawHudOnCanvas(ctx, vWidth, vHeight);

  // 4. If Danger Zone Obstruction, draw pulsing emergency border
  if (latestTracking && latestTracking.has_track_obstruction) {
    drawEmergencyBorder(ctx, vWidth, vHeight);
  }
}

function drawTrackZonesOnCanvas(ctx: CanvasRenderingContext2D, zones: any, width: number, height: number) {
  const fw = zones.frame_width || 640;
  const fh = zones.frame_height || 480;
  const zScaleX = width / fw;
  const zScaleY = height / fh;
  const scaleFactor = Math.max(1, width / 750);

  // 1. Safe Zone
  const safeZone = zones.safe_zone;
  const safePts = safeZone?.polygon || (Array.isArray(safeZone) ? safeZone : null);
  if (safePts && safePts.length > 2) {
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(safePts[0][0] * zScaleX, safePts[0][1] * zScaleY);
    for (let i = 1; i < safePts.length; i++) {
      ctx.lineTo(safePts[i][0] * zScaleX, safePts[i][1] * zScaleY);
    }
    ctx.closePath();
    ctx.fillStyle = 'rgba(16, 185, 129, 0.08)';
    ctx.fill();
    ctx.setLineDash([6 * scaleFactor, 4 * scaleFactor]);
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.75)';
    ctx.lineWidth = 2 * scaleFactor;
    ctx.stroke();

    const topPt = safePts[0];
    const fontSize = Math.max(11, Math.round(12 * scaleFactor));
    ctx.font = `bold ${fontSize}px "Inter", Arial, sans-serif`;
    ctx.fillStyle = '#10b981';
    ctx.fillText('🛡️ SAFE ZONE', topPt[0] * zScaleX + 8, topPt[1] * zScaleY + fontSize + 4);
    ctx.restore();
  }

  // 2. Medium Zone (Warning / Buffer)
  const warnZone = zones.medium_zone || zones.warning_zone;
  const warnPts = warnZone?.polygon || (Array.isArray(warnZone) ? warnZone : null);
  if (warnPts && warnPts.length > 2) {
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(warnPts[0][0] * zScaleX, warnPts[0][1] * zScaleY);
    for (let i = 1; i < warnPts.length; i++) {
      ctx.lineTo(warnPts[i][0] * zScaleX, warnPts[i][1] * zScaleY);
    }
    ctx.closePath();
    ctx.fillStyle = 'rgba(245, 158, 11, 0.15)';
    ctx.fill();
    ctx.setLineDash([8 * scaleFactor, 6 * scaleFactor]);
    ctx.strokeStyle = 'rgba(245, 158, 11, 0.9)';
    ctx.lineWidth = 2.5 * scaleFactor;
    ctx.stroke();

    const topPt = warnPts[0];
    const fontSize = Math.max(12, Math.round(13 * scaleFactor));
    ctx.font = `bold ${fontSize}px "Inter", Arial, sans-serif`;
    ctx.fillStyle = '#f59e0b';
    ctx.fillText('⚠️ MEDIUM ZONE', topPt[0] * zScaleX + 8, topPt[1] * zScaleY + fontSize + 4);
    ctx.restore();
  }

  // 3. Danger Zone (Active Track)
  const dangerZone = zones.danger_zone;
  const dangerPts = dangerZone?.polygon || (Array.isArray(dangerZone) ? dangerZone : null);
  if (dangerPts && dangerPts.length > 2) {
    const pts = dangerPts;
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(pts[0][0] * zScaleX, pts[0][1] * zScaleY);
    for (let i = 1; i < pts.length; i++) {
      ctx.lineTo(pts[i][0] * zScaleX, pts[i][1] * zScaleY);
    }
    ctx.closePath();
    ctx.fillStyle = 'rgba(239, 68, 68, 0.25)';
    ctx.fill();
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 3.5 * scaleFactor;
    ctx.shadowColor = 'rgba(239, 68, 68, 0.7)';
    ctx.shadowBlur = 10 * scaleFactor;
    ctx.stroke();

    const topPt = pts[0];
    const fontSize = Math.max(13, Math.round(14 * scaleFactor));
    ctx.font = `bold ${fontSize}px "Inter", Arial, sans-serif`;
    ctx.fillStyle = '#ef4444';
    ctx.fillText('🚨 DANGER ZONE (TRACK)', topPt[0] * zScaleX + 8, topPt[1] * zScaleY + fontSize + 4);
    ctx.restore();
  }

  // 4. Track center line
  if (zones.track_center_line && zones.track_center_line.length >= 2) {
    ctx.save();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
    ctx.lineWidth = 1.5 * scaleFactor;
    ctx.setLineDash([5 * scaleFactor, 5 * scaleFactor]);
    ctx.beginPath();
    ctx.moveTo(zones.track_center_line[0][0] * zScaleX, zones.track_center_line[0][1] * zScaleY);
    for (let i = 1; i < zones.track_center_line.length; i++) {
      ctx.lineTo(zones.track_center_line[i][0] * zScaleX, zones.track_center_line[i][1] * zScaleY);
    }
    ctx.stroke();
    ctx.restore();
  }
}

function drawObjectOnCanvas(ctx: CanvasRenderingContext2D, obj: any, scaleX: number, scaleY: number) {
  const box = obj.box || obj.bbox;
  if (!box) return;

  const rawX = box.x !== undefined ? box.x : box[0];
  const rawY = box.y !== undefined ? box.y : box[1];
  const rawW = box.width !== undefined ? box.width : (box[2] - box[0]);
  const rawH = box.height !== undefined ? box.height : (box[3] - box[1]);

  const bx = rawX * scaleX;
  const by = rawY * scaleY;
  const bw = rawW * scaleX;
  const bh = rawH * scaleY;

  const zone = (obj.zone || 'SAFE').toUpperCase();
  const isDanger = zone === 'DANGER';
  const isMedium = zone === 'MEDIUM' || zone === 'WARNING';

  const color = isDanger ? '#ef4444' : isMedium ? '#f59e0b' : '#10b981';
  const zoneBadgeText = isDanger ? '🚨 DANGER ZONE' : isMedium ? '⚠️ MEDIUM ZONE' : '🛡️ SAFE ZONE';

  // Responsive scale factor based on canvas width so boxes and text are bold and visible
  const scaleFactor = Math.max(1, ctx.canvas.width / 750);

  ctx.save();

  // Bounding box: 3px - 5px thick
  ctx.strokeStyle = color;
  ctx.lineWidth = Math.round((isDanger ? 4 : 3) * scaleFactor);
  ctx.strokeRect(bx, by, bw, bh);

  // Corner brackets for high-tech look
  const cLen = Math.min(22 * scaleFactor, bw / 3, bh / 3);
  ctx.lineWidth = Math.round((isDanger ? 6 : 4.5) * scaleFactor);

  // Top-left
  ctx.beginPath();
  ctx.moveTo(bx, by + cLen);
  ctx.lineTo(bx, by);
  ctx.lineTo(bx + cLen, by);
  ctx.stroke();
  // Top-right
  ctx.beginPath();
  ctx.moveTo(bx + bw - cLen, by);
  ctx.lineTo(bx + bw, by);
  ctx.lineTo(bx + bw, by + cLen);
  ctx.stroke();
  // Bottom-left
  ctx.beginPath();
  ctx.moveTo(bx, by + bh - cLen);
  ctx.lineTo(bx, by + bh);
  ctx.lineTo(bx + cLen, by + bh);
  ctx.stroke();
  // Bottom-right
  ctx.beginPath();
  ctx.moveTo(bx + bw - cLen, by + bh);
  ctx.lineTo(bx + bw, by + bh);
  ctx.lineTo(bx + bw, by + bh - cLen);
  ctx.stroke();

  // Label text with prominent zone classification markings
  const rawClass = obj.class_name || obj.object || obj.label || 'OBJECT';
  const className = String(rawClass).toUpperCase();
  const rawConf = obj.confidence !== undefined ? obj.confidence : obj.conf;
  const confText = rawConf ? `${Math.round(rawConf * 100)}%` : '';
  const distText = obj.distance_m ? `${Number(obj.distance_m).toFixed(1)}m` : '';
  const trackIdText = obj.track_id !== undefined ? `#${obj.track_id}` : '';

  const labelParts = [className];
  if (trackIdText) labelParts.push(trackIdText);
  if (confText) labelParts.push(confText);
  labelParts.push(zoneBadgeText);
  if (distText) labelParts.push(`📍${distText}`);
  if (isDanger) labelParts.push('ON TRACK');

  const labelText = labelParts.join(' • ');

  const fontSize = Math.max(12, Math.round(13 * scaleFactor));
  ctx.font = `bold ${fontSize}px "JetBrains Mono", Arial, sans-serif`;
  const textMetrics = ctx.measureText(labelText);
  const pillPaddingX = 8 * scaleFactor;
  const pillPaddingY = 5 * scaleFactor;
  const pillW = textMetrics.width + pillPaddingX * 2;
  const pillH = fontSize + pillPaddingY * 2;
  const pillX = Math.max(0, bx);
  const pillY = Math.max(0, by - pillH);

  // Solid high-contrast pill background
  ctx.fillStyle = color;
  ctx.fillRect(pillX, pillY, pillW, pillH);

  // Black bold text on bright colored background for maximum contrast and readability
  ctx.fillStyle = '#000000';
  ctx.textBaseline = 'middle';
  ctx.fillText(labelText, pillX + pillPaddingX, pillY + pillH / 2);

  ctx.restore();
}

function drawHudOnCanvas(ctx: CanvasRenderingContext2D, width: number, _height: number) {
  ctx.save();
  const hudW = 210;
  const hudH = isPipelineMode ? 62 : 36;
  const hudX = width - hudW - 12;
  const hudY = 12;

  ctx.fillStyle = 'rgba(10, 15, 25, 0.85)';
  ctx.beginPath();
  ctx.roundRect(hudX, hudY, hudW, hudH, 6);
  ctx.fill();
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
  ctx.lineWidth = 1;
  ctx.stroke();

  ctx.font = 'bold 11px "JetBrains Mono", monospace';
  ctx.fillStyle = '#10b981';
  ctx.fillText('● 60 FPS SMOOTH', hudX + 10, hudY + 18);

  ctx.fillStyle = '#94a3b8';
  ctx.fillText(modelSelect.value.toUpperCase(), hudX + 130, hudY + 18);

  if (isPipelineMode && latestRisk) {
    const riskLevel = latestRisk.risk_level || 'LOW';
    const riskScore = latestRisk.risk_score || 0;
    const rColor = riskLevel === 'CRITICAL' ? '#ef4444' : riskLevel === 'HIGH' ? '#f59e0b' : '#10b981';

    ctx.fillStyle = rColor;
    ctx.fillText(`RISK: ${riskLevel} (${riskScore}/100)`, hudX + 10, hudY + 38);

    const dangerCount = latestTracking?.danger_count || 0;
    ctx.fillStyle = dangerCount > 0 ? '#ef4444' : '#94a3b8';
    ctx.fillText(dangerCount > 0 ? `🚨 ${dangerCount} IN DANGER ZONE` : '✓ Track Clear', hudX + 10, hudY + 53);
  }

  ctx.restore();
}

function drawEmergencyBorder(ctx: CanvasRenderingContext2D, width: number, height: number) {
  ctx.save();
  ctx.strokeStyle = 'rgba(239, 68, 68, 0.75)';
  ctx.lineWidth = 6;
  ctx.shadowColor = '#ef4444';
  ctx.shadowBlur = 18;
  ctx.strokeRect(3, 3, width - 6, height - 6);
  ctx.restore();
}

// ============================================================
// HIGH-FPS REAL-TIME VIDEO ENGINE (30+ FPS)
// ============================================================
function updateVideoControlsState(state: 'ready' | 'playing' | 'paused' | 'stopped') {
  const isServerStream = fpsModeSelect.value === 'server-stream';

  if (state === 'ready') {
    videoPlayBtn.disabled = false;
    videoPlayBtn.innerHTML = `${icons.play} Start Detection`;
    videoPauseBtn.disabled = true;
    videoStopBtn.disabled = true;

    tbPlayBtn.disabled = false;
    tbPlayText.textContent = 'Start Detection';
    tbPauseBtn.disabled = true;

    viewportPlayOverlay.style.display = 'flex';
    centerPlayBtn.innerHTML = icons.play;
    placeholder.style.display = 'none';

    sourceVideo.style.display = 'block';
    detectionOverlayCanvas.style.display = 'block';
    resultImage.style.display = 'none';
  } else if (state === 'playing') {
    videoPlayBtn.disabled = true;
    videoPauseBtn.disabled = false;
    videoStopBtn.disabled = false;

    tbPlayBtn.disabled = true;
    tbPlayText.textContent = 'Detecting…';
    tbPauseBtn.disabled = false;

    viewportPlayOverlay.style.display = 'none';
    placeholder.style.display = 'none';

    if (isServerStream) {
      sourceVideo.style.display = 'none';
      detectionOverlayCanvas.style.display = 'none';
      resultImage.style.display = 'block';
    } else {
      sourceVideo.style.display = 'block';
      detectionOverlayCanvas.style.display = 'block';
      resultImage.style.display = 'none';
    }
  } else if (state === 'paused') {
    videoPlayBtn.disabled = false;
    videoPlayBtn.innerHTML = `${icons.play} Resume`;
    videoPauseBtn.disabled = true;
    videoStopBtn.disabled = false;

    tbPlayBtn.disabled = false;
    tbPlayText.textContent = 'Resume';
    tbPauseBtn.disabled = true;

    viewportPlayOverlay.style.display = 'flex';
    centerPlayBtn.innerHTML = icons.play;

    if (!isServerStream) {
      sourceVideo.style.display = 'block';
      detectionOverlayCanvas.style.display = 'block';
      resultImage.style.display = 'none';
      renderDetectionOverlay();
    }
  } else if (state === 'stopped') {
    videoPlayBtn.disabled = !videoFile;
    videoPlayBtn.innerHTML = `${icons.play} Start Detection`;
    videoPauseBtn.disabled = true;
    videoStopBtn.disabled = true;

    tbPlayBtn.disabled = !videoFile;
    tbPlayText.textContent = 'Start Detection';
    tbPauseBtn.disabled = true;

    viewportPlayOverlay.style.display = videoFile ? 'flex' : 'none';
    centerPlayBtn.innerHTML = icons.play;

    if (videoFile) {
      sourceVideo.style.display = 'block';
      detectionOverlayCanvas.style.display = 'block';
      resultImage.style.display = 'none';
    }
  }
}

videoUpload.addEventListener('change', () => {
  const file = videoUpload.files?.[0];
  if (!file) return;
  videoFile = file;

  // Reset tracker state so old tracks don't jump on the new video
  fetch('http://localhost:8000/api/tracker/reset', { method: 'POST' }).catch(() => {});
  latestTracking = null;
  currentDetections = [];
  if (detectionOverlayCanvas) {
    const ctx = detectionOverlayCanvas.getContext('2d');
    if (ctx) ctx.clearRect(0, 0, detectionOverlayCanvas.width, detectionOverlayCanvas.height);
  }

  // Immediately display video in viewport and hide placeholder
  placeholder.style.display = 'none';
  resultImage.style.display = 'none';
  sourceVideo.style.display = 'block';
  detectionOverlayCanvas.style.display = 'block';

  const url = URL.createObjectURL(file);
  sourceVideo.src = url;
  splitSourceVideo.src = url;
  sourceVideo.load();

  sourceVideo.onloadedmetadata = () => {
    updateVideoControlsState('ready');
    videoToolbar.style.display = 'flex';
    videoTimeDisplay.textContent = `0:00 / ${formatTime(sourceVideo.duration)}`;
    setStatus(`Video Ready: ${file.name} (${sourceVideo.videoWidth}x${sourceVideo.videoHeight}) — Launching Neural Detection…`, 'active');

    // Auto-start video detection & playback!
    startVideoProcessing();
  };

  sourceVideo.onerror = () => {
    console.error('Error decoding video file:', file.name);
    setStatus(`Cannot decode video "${file.name}". Please ensure it is an MP4 (H.264), WebM, or supported format.`, 'error');
    placeholder.style.display = 'flex';
    sourceVideo.style.display = 'none';
    resultImage.style.display = 'none';
    viewportPlayOverlay.style.display = 'none';
  };

  videoUpload.value = '';
});

// Timeline seeking
function seekVideo(pct: number) {
  if (!sourceVideo.duration) return;
  const targetTime = pct * sourceVideo.duration;
  sourceVideo.currentTime = targetTime;
  splitSourceVideo.currentTime = targetTime;
  videoSeekFill.style.width = `${pct * 100}%`;
  videoTimeDisplay.textContent = `${formatTime(targetTime)} / ${formatTime(sourceVideo.duration)}`;
}

videoSeekBar.addEventListener('click', (e) => {
  if (!sourceVideo.duration) return;
  const rect = videoSeekBar.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const pct = Math.max(0, Math.min(1, clickX / rect.width));
  seekVideo(pct);
});

sourceVideo.addEventListener('seeked', () => {
  if (isVideoPaused || !isVideoProcessing) {
    // Single-frame on-demand detection when seeking while paused
    triggerSingleFrameDetection();
  }
});

async function triggerSingleFrameDetection() {
  if (!videoFile || sourceVideo.readyState < 2) return;
  try {
    await ensureWebSocket();
    captureAndSendVideoFrame();
  } catch (err) {
    console.error('Frame detection error:', err);
  }
}

sourceVideo.addEventListener('timeupdate', () => {
  if (!sourceVideo.duration) return;
  const pct = (sourceVideo.currentTime / sourceVideo.duration) * 100;
  videoSeekFill.style.width = `${pct}%`;
  videoTimeDisplay.textContent = `${formatTime(sourceVideo.currentTime)} / ${formatTime(sourceVideo.duration)}`;

  if (isSplitView) {
    splitSourceVideo.currentTime = sourceVideo.currentTime;
  }
});

sourceVideo.addEventListener('ended', () => {
  if (videoLoop && isVideoProcessing) {
    sourceVideo.currentTime = 0;
    sourceVideo.play();
  } else {
    pauseVideoProcessing();
    videoSeekFill.style.width = '100%';
    setStatus('Video playback complete — click Play or seek to restart', 'active');
  }
});

videoLoopToggle.addEventListener('click', () => {
  videoLoop = !videoLoop;
  videoLoopToggle.textContent = `Loop: ${videoLoop ? 'ON' : 'OFF'}`;
  videoLoopToggle.className = `btn ${videoLoop ? 'btn-secondary' : 'btn-ghost'}`;
});

videoSpeedSelect.addEventListener('change', () => {
  const speed = parseFloat(videoSpeedSelect.value) || 1;
  tbSpeedSelect.value = String(speed);
  sourceVideo.playbackRate = speed;
  splitSourceVideo.playbackRate = speed;
});

tbSpeedSelect.addEventListener('change', () => {
  const speed = parseFloat(tbSpeedSelect.value) || 1;
  videoSpeedSelect.value = String(speed);
  sourceVideo.playbackRate = speed;
  splitSourceVideo.playbackRate = speed;
});

videoPlayBtn.addEventListener('click', resumeOrStartDetection);
tbPlayBtn.addEventListener('click', resumeOrStartDetection);
centerPlayBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  resumeOrStartDetection();
});

videoPauseBtn.addEventListener('click', pauseVideoProcessing);
tbPauseBtn.addEventListener('click', pauseVideoProcessing);
videoStopBtn.addEventListener('click', stopVideoProcessing);

// Viewport click toggles play/pause
viewportContainer.addEventListener('click', (e) => {
  const target = e.target as HTMLElement;
  if (target.closest('.viewport-hud') || target.closest('.video-toolbar')) return;
  if (currentMode !== 'video' || !videoFile) return;

  if (isVideoProcessing && !isVideoPaused) {
    pauseVideoProcessing();
  } else {
    resumeOrStartDetection();
  }
});

async function resumeOrStartDetection() {
  if (!videoFile) return;

  if (isVideoPaused) {
    isVideoPaused = false;
    updateVideoControlsState('playing');
    try {
      await sourceVideo.play();
      if (isSplitView) splitSourceVideo.play();
    } catch (e) {
      console.warn('Playback error:', e);
    }
    setStatus('Resuming video detection…', 'active');
    startVideoFrameLoop();
    return;
  }

  await startVideoProcessing();
}

function pauseVideoProcessing() {
  isVideoPaused = true;
  updateVideoControlsState('paused');
  sourceVideo.pause();
  if (isSplitView) splitSourceVideo.pause();
  if (videoAnimFrameId) {
    cancelAnimationFrame(videoAnimFrameId);
    videoAnimFrameId = null;
  }
  renderDetectionOverlay();
  setStatus('Paused — click Play or click video to resume', 'active');
}

async function startVideoProcessing() {
  try {
    setStatus('Connecting to Neural Engine…', 'processing');
    await ensureWebSocket();

    isVideoProcessing = true;
    isVideoPaused = false;

    updateVideoControlsState('playing');

    sourceVideo.playbackRate = parseFloat(videoSpeedSelect.value) || 1;
    splitSourceVideo.playbackRate = sourceVideo.playbackRate;

    try {
      await sourceVideo.play();
      if (isSplitView) splitSourceVideo.play();
    } catch (playErr) {
      console.warn('Autoplay prevented, awaiting user gesture:', playErr);
      updateVideoControlsState('paused');
      return;
    }

    setStatus('Real-Time High-FPS Detection Active', 'active');
    startVideoFrameLoop();
  } catch (err) {
    console.error(err);
    setStatus('Could not connect to detection engine', 'error');
    stopVideoProcessing();
  }
}

function startVideoFrameLoop() {
  if (!isVideoProcessing || isVideoPaused) return;

  const mode = fpsModeSelect.value;
  const isServerStream = mode === 'server-stream';

  if (!isServerStream) {
    // === 60 FPS NATIVE HARDWARE ACCELERATED VIDEO + CANVAS OVERLAY ===
    sourceVideo.style.display = 'block';
    detectionOverlayCanvas.style.display = 'block';
    resultImage.style.display = 'none';

    const loop = () => {
      if (!isVideoProcessing || isVideoPaused) return;
      if (sourceVideo.paused || sourceVideo.ended) return;

      // 1. Draw smooth overlay on canvas on EVERY animation frame (60 FPS)
      renderDetectionOverlay();

      // 2. Sample frame to backend asynchronously without stalling playback
      const now = performance.now();
      const minInterval = mode === 'synced' ? 100 : (1000 / 25); // ~25 inferences/sec
      if (!isWsInFlight && (now - lastFrameSentTime) >= minInterval) {
        captureAndSendVideoFrame(false);
      }

      videoAnimFrameId = requestAnimationFrame(loop);
    };

    videoAnimFrameId = requestAnimationFrame(loop);
  } else {
    // === SERVER STREAM MODE (legacy) ===
    sourceVideo.style.display = 'none';
    detectionOverlayCanvas.style.display = 'none';
    resultImage.style.display = 'block';

    const loop = () => {
      if (!isVideoProcessing || isVideoPaused) return;
      if (sourceVideo.paused || sourceVideo.ended) return;

      if (!isWsInFlight) {
        captureAndSendVideoFrame(false);
      }
      videoAnimFrameId = requestAnimationFrame(loop);
    };

    videoAnimFrameId = requestAnimationFrame(loop);
  }
}

function captureAndSendVideoFrame(skipImage: boolean = false) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  const activeVideo = currentMode === 'webcam' ? webcamVideo : sourceVideo;
  if (activeVideo.videoWidth === 0 || activeVideo.readyState < 2) return;

  const ctx = workCanvas.getContext('2d');
  if (!ctx) return;

  const { width: targetW, height: targetH } = getTargetDimensions(activeVideo.videoWidth, activeVideo.videoHeight);

  if (workCanvas.width !== targetW || workCanvas.height !== targetH) {
    workCanvas.width = targetW;
    workCanvas.height = targetH;
  }

  try {
    ctx.drawImage(activeVideo, 0, 0, targetW, targetH);
  } catch {
    return;
  }

  const base64 = workCanvas.toDataURL('image/jpeg', 0.85);
  if (!base64 || base64.length < 50) return;

  const confThresh = (parseFloat(confSlider.value) || 35) / 100;

  isWsInFlight = true;
  lastFrameSentTime = performance.now();

  // Watchdog timeout to prevent pipeline freezing
  if (wsWatchdogTimer) clearTimeout(wsWatchdogTimer);
  wsWatchdogTimer = setTimeout(() => {
    if (isWsInFlight) {
      isWsInFlight = false;
    }
  }, 400);

  try {
    ws.send(JSON.stringify({
      model: modelSelect.value,
      conf: confThresh,
      quality: 80,
      image: base64,
      pipeline: isPipelineMode,
      skip_image: skipImage,
    }));
  } catch (err) {
    isWsInFlight = false;
    console.error('Failed to send frame to WebSocket:', err);
  }
}

function stopVideoProcessing() {
  isVideoProcessing = false;
  isVideoPaused = false;
  isWsInFlight = false;

  if (wsWatchdogTimer) {
    clearTimeout(wsWatchdogTimer);
    wsWatchdogTimer = null;
  }

  if (videoAnimFrameId) {
    cancelAnimationFrame(videoAnimFrameId);
    videoAnimFrameId = null;
  }

  sourceVideo.pause();
  sourceVideo.currentTime = 0;
  splitSourceVideo.pause();
  splitSourceVideo.currentTime = 0;
  videoSeekFill.style.width = '0%';

  if (detectionOverlayCanvas) {
    const ctx = detectionOverlayCanvas.getContext('2d');
    if (ctx) ctx.clearRect(0, 0, detectionOverlayCanvas.width, detectionOverlayCanvas.height);
  }

  updateVideoControlsState('stopped');
  setStatus('Video Detection Stopped', '');
}

// ============================================================
// IMAGE UPLOAD DETECTION (REST API)
// ============================================================
imageUpload.addEventListener('change', async () => {
  const file = imageUpload.files?.[0];
  if (!file) return;

  setStatus('Analyzing image with neural model…', 'processing');
  placeholder.style.display = 'none';

  const formData = new FormData();
  formData.append('file', file);
  formData.append('model', modelSelect.value);
  formData.append('conf', String((parseFloat(confSlider.value) || 35) / 100));

  const startTime = performance.now();

  try {
    const res = await fetch('http://localhost:8000/api/detect/image', {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data: ApiResponse = await res.json();

    const latency = Math.round(performance.now() - startTime);
    kpiLatency.textContent = `${latency}`;
    kpiFps.textContent = '—';

    handleFrameDetectionResult(data);
    if (data.pipeline) {
      dashboardCtrl.updateFromPipelineData(data);
    }
    const alertNote = data.alert?.approved ? ' — 🚨 Alert Email Dispatched to rishe8080s@gmail.com!' : '';
    setStatus(`Analysis complete — Detected ${data.detections.length} objects${alertNote}`, 'active');
  } catch (err) {
    console.error(err);
    setStatus('Error processing image. Check backend status.', 'error');
  }

  imageUpload.value = '';
});

// ============================================================
// WEBCAM LIVE STREAMING
// ============================================================
startWebcamBtn.addEventListener('click', startWebcam);
stopWebcamBtn.addEventListener('click', stopWebcam);

async function startWebcam() {
  try {
    setStatus('Requesting Camera Access…', 'processing');
    webcamStream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } },
    });
    webcamVideo.srcObject = webcamStream;
    await webcamVideo.play();

    await ensureWebSocket();

    isWebcamRunning = true;
    startWebcamBtn.disabled = true;
    stopWebcamBtn.disabled = false;

    placeholder.style.display = 'none';
    resultImage.style.display = 'none';
    webcamVideo.style.display = 'block';
    detectionOverlayCanvas.style.display = 'block';

    setStatus('Live Camera Neural Detection Active', 'active');
    streamWebcamLoop();
  } catch (err) {
    console.error(err);
    setStatus('Failed to start camera feed', 'error');
  }
}

function streamWebcamLoop() {
  if (!isWebcamRunning || !ws || ws.readyState !== WebSocket.OPEN) return;

  renderDetectionOverlay();

  const now = performance.now();
  if (webcamVideo.videoWidth > 0 && !isWsInFlight && (now - lastFrameSentTime) >= 40) {
    captureAndSendVideoFrame(false);
  }

  if (isWebcamRunning) {
    requestAnimationFrame(streamWebcamLoop);
  }
}

function stopWebcam() {
  isWebcamRunning = false;
  isWsInFlight = false;

  if (webcamStream) {
    webcamStream.getTracks().forEach(t => t.stop());
    webcamStream = null;
  }

  webcamVideo.style.display = 'none';
  if (detectionOverlayCanvas) {
    const ctx = detectionOverlayCanvas.getContext('2d');
    if (ctx) ctx.clearRect(0, 0, detectionOverlayCanvas.width, detectionOverlayCanvas.height);
  }

  startWebcamBtn.disabled = false;
  stopWebcamBtn.disabled = true;
  setStatus('Camera Stopped', '');
}

// ============================================================
// Drag & Drop Setup
// ============================================================
function setupDrop(zone: HTMLDivElement, input: HTMLInputElement) {
  zone.addEventListener('dragover', (e) => {
    e.preventDefault();
    zone.classList.add('drag-over');
  });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    if (e.dataTransfer?.files.length) {
      input.files = e.dataTransfer.files;
      input.dispatchEvent(new Event('change'));
    }
  });
}
setupDrop(videoDropZone, videoUpload);
setupDrop(imageDropZone, imageUpload);

// ============================================================
// Mode Switcher Tabs
// ============================================================
modeTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    const mode = tab.dataset.mode as typeof currentMode;
    if (mode === currentMode) return;

    if (currentMode === 'video') stopVideoProcessing();
    if (currentMode === 'webcam') stopWebcam();

    currentMode = mode;
    modeTabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    modeContents.forEach(c => c.classList.remove('active'));
    document.getElementById(`mode-${mode}`)?.classList.add('active');

    placeholder.style.display = 'flex';
    resultImage.style.display = 'none';
    sourceVideo.style.display = 'none';
    webcamVideo.style.display = 'none';
    if (detectionOverlayCanvas) {
      detectionOverlayCanvas.style.display = 'none';
      const ctx = detectionOverlayCanvas.getContext('2d');
      if (ctx) ctx.clearRect(0, 0, detectionOverlayCanvas.width, detectionOverlayCanvas.height);
    }

    splitView.classList.remove('active');
    isSplitView = false;
    kpiObjects.textContent = '0';
    kpiFps.textContent = '0';
    kpiNearest.textContent = '—';
    proximityAlert.classList.remove('active');
    breakdownBar.style.display = 'none';

    setStatus(`Switched to ${mode.toUpperCase()} mode`);
  });
});

// Engine Switcher Event Listener
fpsModeSelect.addEventListener('change', () => {
  if (isVideoProcessing && !isVideoPaused) {
    updateVideoControlsState('playing');
    if (videoAnimFrameId) {
      cancelAnimationFrame(videoAnimFrameId);
      videoAnimFrameId = null;
    }
    startVideoFrameLoop();
  }
  setStatus(`Video engine set to: ${fpsModeSelect.options[fpsModeSelect.selectedIndex].text}`, 'active');
});

// ============================================================
// HUD Tools: Split View & Snapshot Download
// ============================================================
hudSplitToggle.addEventListener('click', () => {
  isSplitView = !isSplitView;
  hudSplitToggle.classList.toggle('active', isSplitView);
  splitView.classList.toggle('active', isSplitView);
  resultImage.style.display = isSplitView ? 'none' : 'block';

  if (isSplitView) {
    splitSourceVideo.style.display = currentMode === 'video' ? 'block' : 'none';
    splitSourceImg.style.display = currentMode === 'image' ? 'block' : 'none';
    if (resultImage.src) {
      splitResultImg.src = resultImage.src;
    }
  }
});

hudSnapshotBtn.addEventListener('click', () => {
  const activeVideo = currentMode === 'webcam' ? webcamVideo : sourceVideo;
  if (isVideoProcessing || isWebcamRunning || (activeVideo.readyState >= 2 && activeVideo.style.display !== 'none')) {
    const snapCanvas = document.createElement('canvas');
    snapCanvas.width = activeVideo.videoWidth || 1280;
    snapCanvas.height = activeVideo.videoHeight || 720;
    const snapCtx = snapCanvas.getContext('2d');
    if (snapCtx) {
      snapCtx.drawImage(activeVideo, 0, 0, snapCanvas.width, snapCanvas.height);
      if (detectionOverlayCanvas && detectionOverlayCanvas.style.display !== 'none') {
        snapCtx.drawImage(detectionOverlayCanvas, 0, 0, snapCanvas.width, snapCanvas.height);
      }
      const a = document.createElement('a');
      a.href = snapCanvas.toDataURL('image/png');
      a.download = `VisionDetect_Snapshot_${Date.now()}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setStatus('High-Res Detection Snapshot downloaded!', 'active');
      return;
    }
  }

  if (!resultImage.src) {
    alert('No detection frame active to capture!');
    return;
  }
  const a = document.createElement('a');
  a.href = resultImage.src;
  a.download = `VisionDetect_${Date.now()}.jpg`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setStatus('Snapshot downloaded!', 'active');
});

// ============================================================
// Data Export (JSON & Clipboard)
// ============================================================
exportJsonBtn.addEventListener('click', () => {
  const payload = {
    timestamp: new Date().toISOString(),
    model: modelSelect.value,
    confidenceThreshold: confSlider.value,
    detections: currentDetections,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `VisionDetect_Report_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
  setStatus('Report exported as JSON', 'active');
});

copySummaryBtn.addEventListener('click', () => {
  if (currentDetections.length === 0) {
    alert('No detections to copy!');
    return;
  }
  const summary = currentDetections.map((d, i) => `${i + 1}. ${d.class_name.toUpperCase()} (${(d.confidence * 100).toFixed(0)}%) - Dist: ${d.distance_m ?? 'N/A'}m`).join('\n');
  navigator.clipboard.writeText(`VisionDetect AI Report:\n${summary}`);
  setStatus('Detection summary copied to clipboard!', 'active');
});

// ============================================================
// Railway Pipeline Mode & Page Navigation
// ============================================================
let isPipelineMode = true; // Enabled by default for track vulnerability detection
let currentPage = 'detection';
const dashboardCtrl = new DashboardController();

// Initialize dashboard pages
function initDashboardPages() {
  const railwayPage = document.getElementById('page-railway');
  const historyPage = document.getElementById('page-history');
  const adminPage = document.getElementById('page-admin');
  if (railwayPage) railwayPage.innerHTML = getRailwayDashboardHTML();
  if (historyPage) historyPage.innerHTML = getAlertHistoryHTML();
  if (adminPage) adminPage.innerHTML = getAdminPanelHTML();

  // Wire quick upload button inside the Railway Monitor feed placeholder
  const quickUploadBtn = document.getElementById('btn-quick-upload-video');
  if (quickUploadBtn) {
    quickUploadBtn.addEventListener('click', () => {
      const detectionTab = document.querySelector<HTMLButtonElement>('.page-nav-tab[data-page="detection"]');
      if (detectionTab) detectionTab.click();
      setTimeout(() => {
        videoUpload.click();
      }, 100);
    });
  }
}
initDashboardPages();

// Sidebar Railway Pipeline Toggle
const railwayPipelineToggle = document.getElementById('railway-pipeline-toggle') as HTMLInputElement | null;
if (railwayPipelineToggle) {
  railwayPipelineToggle.checked = isPipelineMode;
  railwayPipelineToggle.addEventListener('change', () => {
    isPipelineMode = railwayPipelineToggle.checked;
    setStatus(isPipelineMode ? 'Railway Risk Engine Enabled' : 'Standard Detection Mode', 'active');
  });
}

// Page navigation
document.querySelectorAll<HTMLButtonElement>('.page-nav-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const page = tab.dataset.page || 'detection';
    if (page === currentPage) return;

    currentPage = page;

    if (page === 'railway') {
      isPipelineMode = true;
      if (railwayPipelineToggle) railwayPipelineToggle.checked = true;
    }

    // Update tab active state
    document.querySelectorAll('.page-nav-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    // Show/hide pages
    document.querySelectorAll('.page-content').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${page}`)?.classList.add('active');

    // Load page-specific data
    if (page === 'railway') {
      dashboardCtrl.loadInitialRailwayState();
    } else if (page === 'history') {
      dashboardCtrl.loadAlertHistory();
    } else if (page === 'admin') {
      dashboardCtrl.loadAdminData();
      dashboardCtrl.initAdminHandlers();
    }
  });
});

// Load initial state for railway monitor on page startup
dashboardCtrl.loadInitialRailwayState();

// Hook into existing WebSocket message handler to update dashboard
function patchWebSocketForDashboard() {
  const checkAndPatch = () => {
    if (ws && ws.onmessage) {
      const prevHandler = ws.onmessage;
      ws.onmessage = (event: MessageEvent) => {
        // Call original handler first
        if (ws) prevHandler.call(ws, event);

        // Update dashboard if pipeline data is returned
        try {
          const data = JSON.parse(event.data);
          if (data.pipeline) {
            dashboardCtrl.updateFromPipelineData(data);
          }
        } catch { /* ignore parse errors */ }
      };
    }
  };
  setInterval(checkAndPatch, 1000);
  checkAndPatch();
}
patchWebSocketForDashboard();

