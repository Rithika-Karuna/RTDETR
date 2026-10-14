/**
 * Railway Track Monitoring Dashboard Module
 * Provides the Railway Monitor, Alert History, and Admin Panel views.
 * Integrates with the backend agent pipeline via WebSocket and REST APIs.
 */

// ============================================================
// Dashboard HTML Templates
// ============================================================

export function getRailwayDashboardHTML(): string {
  return `
    <div class="railway-dashboard" id="railway-dashboard">
      <!-- Top Risk Banner -->
      <div class="risk-banner" id="risk-banner">
        <div class="risk-banner-content">
          <div class="risk-indicator" id="risk-indicator">
            <span class="risk-level-badge" id="risk-level-badge">LOW</span>
            <span class="risk-score-display" id="risk-score-display">0<small>/100</small></span>
          </div>
          <div class="risk-details" id="risk-details">
            <span class="risk-reason" id="risk-reason">No objects detected in track zone</span>
            <span class="risk-action" id="risk-action">System monitoring</span>
          </div>
          <div class="risk-meta">
            <span id="pipeline-fps-display">0 FPS</span>
            <span id="pipeline-latency-display">0ms</span>
          </div>
        </div>
      </div>

      <div class="dashboard-grid">
        <!-- Left: Live Feed -->
        <div class="dash-panel dash-feed-panel">
          <div class="dash-panel-header">
            <span class="dash-panel-title">📹 Live Camera — Railway Track Monitor</span>
            <div class="dash-panel-actions">
              <label class="toggle-switch-sm">
                <input type="checkbox" id="zone-overlay-toggle" checked />
                <span class="toggle-slider-sm"></span>
              </label>
              <span style="font-size:0.7rem;color:var(--text-secondary)">Zones</span>
            </div>
          </div>
          <div class="dash-feed-viewport" id="dash-feed-viewport">
            <div class="dash-placeholder" id="dash-placeholder">
              <div class="dash-placeholder-icon">🛤️</div>
              <div style="font-size:1.1rem; font-weight:600; margin-bottom:6px;">Railway Monitoring Feed Inactive</div>
              <div style="color:var(--text-secondary); font-size:0.85rem; max-width:400px; margin-bottom:14px; text-align:center;">
                Load a track video or start the live camera to begin automated vulnerability detection, obstacle risk calculation, and emergency alerting.
              </div>
              <button class="btn btn-primary" id="btn-quick-upload-video" style="padding:8px 18px; font-size:0.85rem; cursor:pointer;">
                📂 Select Track Video / Start Feed
              </button>
            </div>
            <img id="dash-result-image" style="display:none;" alt="Railway Monitor Feed" />
          </div>
        </div>

        <!-- Right: Info Panels -->
        <div class="dash-info-column">
          <!-- Train Info Panel -->
          <div class="dash-panel">
            <div class="dash-panel-header">
              <span class="dash-panel-title">🚂 Train Information</span>
            </div>
            <div class="dash-panel-body" id="train-info-panel">
              <div class="dash-info-row">
                <span class="dash-label">Train:</span>
                <span class="dash-value" id="train-name-display">—</span>
              </div>
              <div class="dash-info-row">
                <span class="dash-label">Number:</span>
                <span class="dash-value" id="train-number-display">—</span>
              </div>
              <div class="dash-info-row">
                <span class="dash-label">Route:</span>
                <span class="dash-value" id="train-route-display">—</span>
              </div>
              <div class="dash-info-row">
                <span class="dash-label">Speed:</span>
                <span class="dash-value" id="train-speed-display">—</span>
              </div>
              <div class="dash-info-row">
                <span class="dash-label">Distance:</span>
                <span class="dash-value dash-highlight" id="train-distance-display">—</span>
              </div>
              <div class="dash-info-row">
                <span class="dash-label">TTI:</span>
                <span class="dash-value dash-highlight" id="train-tti-display">—</span>
              </div>
              <div class="dash-info-row">
                <span class="dash-label">Direction:</span>
                <span class="dash-value" id="train-direction-display">—</span>
              </div>
            </div>
          </div>

          <!-- Risk Breakdown Panel -->
          <div class="dash-panel">
            <div class="dash-panel-header">
              <span class="dash-panel-title">📊 Risk Breakdown</span>
            </div>
            <div class="dash-panel-body" id="risk-breakdown-panel">
              <div class="risk-bar-group">
                <div class="risk-bar-row">
                  <span>Object Severity</span>
                  <div class="risk-bar"><div class="risk-bar-fill" id="bar-severity" style="width:0%"></div></div>
                  <span class="risk-bar-val" id="val-severity">0</span>
                </div>
                <div class="risk-bar-row">
                  <span>Track Occupancy</span>
                  <div class="risk-bar"><div class="risk-bar-fill" id="bar-occupancy" style="width:0%"></div></div>
                  <span class="risk-bar-val" id="val-occupancy">0</span>
                </div>
                <div class="risk-bar-row">
                  <span>Train Proximity</span>
                  <div class="risk-bar"><div class="risk-bar-fill" id="bar-proximity" style="width:0%"></div></div>
                  <span class="risk-bar-val" id="val-proximity">0</span>
                </div>
                <div class="risk-bar-row">
                  <span>Train Speed</span>
                  <div class="risk-bar"><div class="risk-bar-fill" id="bar-speed" style="width:0%"></div></div>
                  <span class="risk-bar-val" id="val-speed">0</span>
                </div>
                <div class="risk-bar-row">
                  <span>Collision Prob.</span>
                  <div class="risk-bar"><div class="risk-bar-fill" id="bar-collision" style="width:0%"></div></div>
                  <span class="risk-bar-val" id="val-collision">0</span>
                </div>
                <div class="risk-bar-row">
                  <span>Persistence</span>
                  <div class="risk-bar"><div class="risk-bar-fill" id="bar-persistence" style="width:0%"></div></div>
                  <span class="risk-bar-val" id="val-persistence">0</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Location Panel -->
          <div class="dash-panel">
            <div class="dash-panel-header">
              <span class="dash-panel-title">📍 Location Intelligence</span>
            </div>
            <div class="dash-panel-body">
              <div class="dash-info-row">
                <span class="dash-label">Location:</span>
                <span class="dash-value" id="loc-name-display">—</span>
              </div>
              <div class="dash-info-row">
                <span class="dash-label">GPS:</span>
                <span class="dash-value" id="loc-gps-display">—</span>
              </div>
              <div class="dash-info-row">
                <span class="dash-label">Station:</span>
                <span class="dash-value" id="loc-station-display">—</span>
              </div>
              <div class="dash-info-row">
                <span class="dash-label">Division:</span>
                <span class="dash-value" id="loc-division-display">—</span>
              </div>
              <div class="dash-info-row">
                <span class="dash-label">Zone:</span>
                <span class="dash-value" id="loc-zone-display">—</span>
              </div>
            </div>
          </div>

          <!-- In-Charge Authority Panel (RAG) -->
          <div class="dash-panel">
            <div class="dash-panel-header">
              <span class="dash-panel-title">🛡️ Designated In-Charge (RAG)</span>
              <span class="dash-badge" id="auth-rag-badge" style="background:#10b981;color:#fff;font-size:0.65rem">RAG LINKED</span>
            </div>
            <div class="dash-panel-body" id="authority-info-panel">
              <div class="dash-info-row">
                <span class="dash-label">Officer In-Charge:</span>
                <span class="dash-value dash-highlight" id="auth-name-display">Er. Rishe S</span>
              </div>
              <div class="dash-info-row">
                <span class="dash-label">Designation:</span>
                <span class="dash-value" id="auth-role-display">Chief Divisional Safety Officer</span>
              </div>
              <div class="dash-info-row">
                <span class="dash-label">Alert Mail:</span>
                <span class="dash-value" id="auth-email-display" style="font-family:'JetBrains Mono',monospace;color:#60a5fa;font-weight:600">rishe8080s@gmail.com</span>
              </div>
              <div class="dash-info-row">
                <span class="dash-label">Jurisdiction:</span>
                <span class="dash-value" id="auth-jurisdiction-display" style="font-size:0.75rem;color:var(--text-secondary)">Coimbatore Section</span>
              </div>
            </div>
          </div>

          <!-- Alert Status Panel -->
          <div class="dash-panel">
            <div class="dash-panel-header">
              <span class="dash-panel-title">🚨 Alert Status</span>
            </div>
            <div class="dash-panel-body" id="alert-status-panel">
              <div class="dash-info-row">
                <span class="dash-label">Status:</span>
                <span class="dash-value" id="alert-status-display">No active alerts</span>
              </div>
              <div class="dash-info-row">
                <span class="dash-label">Active Events:</span>
                <span class="dash-value" id="alert-active-count">0</span>
              </div>
              <div id="active-events-list" class="active-events-list"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tracked Objects Table -->
      <div class="dash-panel" style="margin-top: 1rem;">
        <div class="dash-panel-header">
          <span class="dash-panel-title">🎯 Tracked Objects</span>
          <span class="dash-badge" id="tracked-count-badge">0</span>
        </div>
        <div class="tracked-objects-table-wrap">
          <table class="tracked-objects-table" id="tracked-objects-table">
            <thead>
              <tr>
                <th>ID</th><th>Object</th><th>Confidence</th><th>Zone</th>
                <th>Movement</th><th>On Track</th><th>Speed</th><th>Status</th>
              </tr>
            </thead>
            <tbody id="tracked-objects-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}


export function getAlertHistoryHTML(): string {
  return `
    <div class="alert-history-page" id="alert-history-page">
      <div class="dash-panel">
        <div class="dash-panel-header">
          <span class="dash-panel-title">📋 Alert History</span>
          <div class="history-filters">
            <select id="history-risk-filter">
              <option value="">All Risk Levels</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
            <select id="history-status-filter">
              <option value="">All Statuses</option>
              <option value="DETECTED">DETECTED</option>
              <option value="MONITORING">MONITORING</option>
              <option value="HIGH_RISK">HIGH_RISK</option>
              <option value="ALERT_SENT">ALERT_SENT</option>
              <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
              <option value="RESOLVED">RESOLVED</option>
            </select>
            <button class="btn btn-secondary btn-sm" id="history-refresh-btn">Refresh</button>
          </div>
        </div>
        <div class="history-table-wrap">
          <table class="tracked-objects-table" id="history-table">
            <thead>
              <tr>
                <th>Event ID</th><th>Date/Time</th><th>Object</th><th>Risk</th>
                <th>Score</th><th>Zone</th><th>Train</th><th>Station</th>
                <th>Status</th><th>Actions</th>
              </tr>
            </thead>
            <tbody id="history-tbody"></tbody>
          </table>
        </div>
        <div class="history-pagination" id="history-pagination"></div>
      </div>
    </div>
  `;
}


export function getAdminPanelHTML(): string {
  return `
    <div class="admin-page" id="admin-page">
      <div class="admin-grid">
        <!-- Notification & Email Alert System -->
        <div class="dash-panel">
          <div class="dash-panel-header">
            <span class="dash-panel-title">📧 Email & Alert Notification Hub</span>
          </div>
          <div class="dash-panel-body">
            <div class="admin-help-box">
              Alerts are automatically triggered when an obstacle enters or remains in the <strong>Danger Zone</strong>. Configure recipient emails and SMTP to receive instant alerts with GPS, station, and event diagnostics.
            </div>

            <h4 style="color:var(--text-primary);margin:0 0 0.5rem">Emergency Alert Recipient</h4>
            <div class="control-group">
              <label class="control-label">Alert Target Email(s) (comma-separated)</label>
              <input type="text" id="admin-alert-recipients" class="admin-input" placeholder="rishe8080s@gmail.com" value="rishe8080s@gmail.com" />
              <div style="font-size:0.7rem;color:var(--text-tertiary);margin-top:0.25rem">Receives immediate danger notifications and location briefings.</div>
            </div>

            <div class="admin-section-divider"></div>
            <h4 style="color:var(--text-primary);margin:0 0 0.5rem">Outgoing Mail Server (SMTP)</h4>
            
            <div class="toggle-row" style="margin-bottom:0.75rem">
              <span>Enable Email Alerts</span>
              <label class="toggle-switch">
                <input type="checkbox" id="admin-email-enabled" checked />
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="admin-grid-2col">
              <div class="control-group">
                <label class="control-label">SMTP Host</label>
                <input type="text" id="admin-smtp-host" class="admin-input" value="smtp.gmail.com" />
              </div>
              <div class="control-group">
                <label class="control-label">Sender Email</label>
                <input type="email" id="admin-sender-email" class="admin-input" placeholder="rishe8080s@gmail.com" value="rishe8080s@gmail.com" />
              </div>
            </div>

            <div class="control-group">
              <label class="control-label">Google App Password (16 chars)</label>
              <input type="password" id="admin-sender-password" class="admin-input" placeholder="•••••••••••••••• (Configured)" />
              <div style="font-size:0.7rem;color:var(--text-tertiary);margin-top:0.25rem">Active Gmail App Password configured for <code>rishe8080s@gmail.com</code>.</div>
            </div>

            <div class="admin-button-row">
              <button class="btn btn-primary" id="admin-save-notif-btn">Save Notification Config</button>
              <button class="btn btn-secondary" id="admin-test-email-btn" title="Send a test alert email right now">📨 Send Test Alert to Mail</button>
            </div>
            <div class="admin-status" id="admin-notif-status"></div>

            <div class="admin-section-divider"></div>
            <h4 style="color:var(--text-primary);margin:0 0 0.5rem">WhatsApp Alert Dispatch (Optional)</h4>
            <div class="toggle-row" style="margin-bottom:0.5rem">
              <span>Enable WhatsApp Alerts</span>
              <label class="toggle-switch">
                <input type="checkbox" id="admin-wa-enabled" />
                <span class="toggle-slider"></span>
              </label>
            </div>
            <div class="control-group">
              <label class="control-label">Account SID</label>
              <input type="text" id="admin-wa-sid" class="admin-input" placeholder="Twilio SID" />
            </div>
            <div class="control-group">
              <label class="control-label">Auth Token</label>
              <input type="password" id="admin-wa-token" class="admin-input" placeholder="Twilio Token" />
            </div>
            <div class="control-group">
              <label class="control-label">From Phone Number</label>
              <input type="text" id="admin-wa-from" class="admin-input" placeholder="+14155238886" />
            </div>
          </div>
        </div>

        <!-- Monitoring Location -->
        <div class="dash-panel">
          <div class="dash-panel-header">
            <span class="dash-panel-title">📍 Monitoring Station & GPS Location</span>
          </div>
          <div class="dash-panel-body">
            <div class="admin-help-box">
              These coordinates and station tags are embedded inside every alert email sent to <code>rishe8080s@gmail.com</code> so authorities know exactly which track section is obstructed.
            </div>
            <div class="admin-grid-2col">
              <div class="control-group">
                <label class="control-label">Latitude</label>
                <input type="number" id="admin-mon-lat" class="admin-input" step="0.0001" value="11.0168" />
              </div>
              <div class="control-group">
                <label class="control-label">Longitude</label>
                <input type="number" id="admin-mon-lon" class="admin-input" step="0.0001" value="76.9558" />
              </div>
            </div>
            <div class="control-group">
              <label class="control-label">Location Name / Section</label>
              <input type="text" id="admin-mon-name" class="admin-input" value="Coimbatore Railway Track Section" />
            </div>
            <div class="control-group">
              <label class="control-label">Nearest Station</label>
              <input type="text" id="admin-mon-station" class="admin-input" value="Coimbatore Junction" />
            </div>
            <div class="admin-grid-2col">
              <div class="control-group">
                <label class="control-label">Railway Zone</label>
                <input type="text" id="admin-mon-rzone" class="admin-input" value="Southern Railway" />
              </div>
              <div class="control-group">
                <label class="control-label">Division</label>
                <input type="text" id="admin-mon-division" class="admin-input" value="Salem Division" />
              </div>
            </div>
            <button class="btn btn-primary" id="admin-save-location-btn" style="margin-top:0.6rem">Save Location Details</button>
            <div class="admin-status" id="admin-location-status"></div>
          </div>
        </div>

        <!-- Train Fleet Simulation / Monitoring -->
        <div class="dash-panel">
          <div class="dash-panel-header">
            <span class="dash-panel-title">🚂 Approaching Train Tracker</span>
          </div>
          <div class="dash-panel-body">
            <div class="admin-help-box">
              Active trains approaching the monitored location. When an object is in the danger zone, Time-To-Impact (TTI) and train details are included in the dispatched email.
            </div>
            <div class="admin-grid-2col">
              <div class="control-group">
                <label class="control-label">Train Number</label>
                <input type="text" id="admin-train-number" class="admin-input" placeholder="e.g. 12675" />
              </div>
              <div class="control-group">
                <label class="control-label">Train Name</label>
                <input type="text" id="admin-train-name" class="admin-input" placeholder="Kovai Express" />
              </div>
            </div>
            <div class="admin-grid-2col">
              <div class="control-group">
                <label class="control-label">Source Station</label>
                <input type="text" id="admin-train-source" class="admin-input" placeholder="Chennai Central" />
              </div>
              <div class="control-group">
                <label class="control-label">Destination</label>
                <input type="text" id="admin-train-dest" class="admin-input" placeholder="Coimbatore Jn" />
              </div>
            </div>
            <div class="admin-grid-2col">
              <div class="control-group">
                <label class="control-label">Speed (km/h)</label>
                <input type="number" id="admin-train-speed" class="admin-input" value="85" />
              </div>
              <div class="control-group">
                <label class="control-label">Train Lat / Lon</label>
                <div style="display:flex;gap:0.3rem">
                  <input type="number" id="admin-train-lat" class="admin-input" step="0.001" placeholder="Lat" value="11.050" />
                  <input type="number" id="admin-train-lon" class="admin-input" step="0.001" placeholder="Lon" value="76.990" />
                </div>
              </div>
            </div>
            <button class="btn btn-primary" id="admin-add-train-btn" style="margin-top:0.6rem">Add / Update Train</button>
            <div class="admin-status" id="admin-train-status"></div>
            <div class="admin-section-divider"></div>
            <h5 style="color:var(--text-secondary);margin:0 0 0.4rem;font-size:0.75rem">Active Monitored Trains:</h5>
            <div id="admin-train-list"></div>
          </div>
        </div>

        <!-- Risk Policy & Alert Sensitivity -->
        <div class="dash-panel">
          <div class="dash-panel-header">
            <span class="dash-panel-title">⚙️ Risk Sensitivity & Cooldown</span>
          </div>
          <div class="dash-panel-body">
            <div class="admin-help-box">
              Controls when danger alerts are triggered. Lower persistence will trigger alerts faster. Cooldown avoids inbox flooding.
            </div>
            <div class="control-group">
              <label class="control-label">Alert Cooldown (seconds between repeated emails)</label>
              <input type="number" id="admin-cooldown" class="admin-input" value="300" />
            </div>
            <div class="control-group">
              <label class="control-label">Min Danger Persistence (seconds required in zone)</label>
              <input type="number" id="admin-persistence" class="admin-input" value="3" />
            </div>
            <div class="control-group">
              <label class="control-label">Min AI Detection Confidence (0.0 to 1.0)</label>
              <input type="number" id="admin-min-conf" class="admin-input" value="0.45" step="0.05" min="0" max="1" />
            </div>
            <div class="control-group">
              <label class="control-label">Advanced Risk Thresholds (JSON)</label>
              <textarea id="admin-risk-thresholds" class="admin-textarea" rows="2" style="font-size:0.7rem"></textarea>
            </div>
            <div class="control-group">
              <label class="control-label">Advanced Risk Weights (JSON)</label>
              <textarea id="admin-risk-weights" class="admin-textarea" rows="2" style="font-size:0.7rem"></textarea>
            </div>
            <button class="btn btn-primary" id="admin-save-risk-btn">Save Risk Settings</button>
            <div class="admin-status" id="admin-risk-status"></div>
          </div>
        </div>

        <!-- Track Zone Boundaries -->
        <div class="dash-panel">
          <div class="dash-panel-header">
            <span class="dash-panel-title">🛤️ Track Zone Coordinates</span>
          </div>
          <div class="dash-panel-body">
            <div class="admin-help-box">
              Coordinates defining <strong>Danger Zone</strong> (Immediate Track Bed), <strong>Medium Zone</strong> (Track Clearance Buffer), and <strong>Safe Zone</strong>.
            </div>
            <div class="toggle-row" style="margin-bottom:0.6rem">
              <span>Zone Checking Active</span>
              <label class="toggle-switch">
                <input type="checkbox" id="admin-zones-enabled" checked />
                <span class="toggle-slider"></span>
              </label>
            </div>
            <div class="control-group">
              <label class="control-label">Danger Zone Polygon (Track Bed)</label>
              <textarea id="admin-danger-polygon" class="admin-textarea" rows="2"></textarea>
            </div>
            <div class="control-group">
              <label class="control-label">Medium Zone (Warning Buffer) Polygon</label>
              <textarea id="admin-warning-polygon" class="admin-textarea" rows="2"></textarea>
            </div>
            <div class="control-group">
              <label class="control-label">Safe Zone Polygon (Outer Boundary)</label>
              <textarea id="admin-safe-polygon" class="admin-textarea" rows="2"></textarea>
            </div>
            <div class="control-group">
              <label class="control-label">Track Center Line Coordinates</label>
              <textarea id="admin-track-center" class="admin-textarea" rows="2"></textarea>
            </div>
            <div class="admin-button-row">
              <button class="btn btn-primary" id="admin-save-zones-btn">Save Zone Config</button>
              <button class="btn btn-secondary btn-sm" id="admin-reset-zones-btn">Reset Default Coordinates</button>
            </div>
            <div class="admin-status" id="admin-zone-status"></div>
          </div>
        </div>

        <!-- Knowledge Base -->
        <div class="dash-panel">
          <div class="dash-panel-header">
            <span class="dash-panel-title">📚 Knowledge Base (RAG Authorities)</span>
          </div>
          <div class="dash-panel-body">
            <div class="admin-help-box">
              The RAG system indexes official railway safety manuals, station rosters, and contact directories. When track obstruction occurs, RAG dynamically retrieves the in-charge authority and emergency email for the active station section.
            </div>
            <div class="drop-zone" id="kb-drop-zone">
              <div class="drop-zone-text">
                <strong>Upload Authority Manuals & Contacts</strong><br/>CSV, JSON, PDF, TXT, MD
              </div>
              <input type="file" id="kb-file-upload" accept=".pdf,.docx,.doc,.csv,.json,.txt,.md" />
            </div>
            <div class="admin-status" id="kb-upload-status"></div>
            <div class="dash-info-row" style="margin-top:0.5rem">
              <span class="dash-label">Indexed Chunks:</span>
              <span class="dash-value" id="kb-total-chunks">0</span>
            </div>
            <div class="dash-info-row">
              <span class="dash-label">Knowledge Sources:</span>
              <span class="dash-value" id="kb-total-sources">0</span>
            </div>
            <div id="kb-sources-list" style="margin-top:0.4rem;font-size:0.72rem;color:var(--text-tertiary)"></div>
            <button class="btn btn-secondary btn-sm" id="kb-reindex-btn" style="margin-top:0.6rem">🔄 Re-index All Documents</button>

            <div class="admin-section-divider"></div>
            <h4 style="color:var(--text-primary);margin:0 0 0.5rem">🔍 Live RAG Authority Lookup</h4>
            <div class="control-group">
              <label class="control-label">Station / Location Name</label>
              <div style="display:flex;gap:0.4rem">
                <input type="text" id="admin-rag-test-station" class="admin-input" placeholder="e.g. Coimbatore Junction" value="Coimbatore Junction" />
                <button class="btn btn-primary btn-sm" id="admin-rag-test-btn" style="white-space:nowrap">Query RAG In-Charge</button>
              </div>
            </div>
            <div id="admin-rag-result-box" style="margin-top:0.6rem;padding:0.6rem;background:rgba(255,255,255,0.03);border:1px solid var(--glass-border);border-radius:6px;font-size:0.75rem;display:none;"></div>
          </div>
        </div>

      </div>
    </div>
  `;
}


// ============================================================
// Dashboard Controller
// ============================================================

const API_BASE = `http://${window.location.hostname || 'localhost'}:8000`;

export class DashboardController {
  private historyPage = 0;
  private historyLimit = 20;

  /** Update the railway dashboard panels from pipeline data */
  updateFromPipelineData(data: any) {
    if (!data.pipeline) return;

    // Risk banner
    this.updateRiskBanner(data.risk);
    // Train info
    this.updateTrainPanel(data.train);
    // Risk breakdown
    this.updateRiskBreakdown(data.risk?.breakdown);
    // Location
    this.updateLocationPanel(data.location);
    // In-Charge Authority (RAG)
    this.updateAuthorityPanel(data.authority);
    // Alert status
    this.updateAlertPanel(data.alert);
    // Tracked objects table
    this.updateTrackedObjectsTable(data.tracking?.tracked_objects || []);
    // Feed image
    if (data.image) {
      const img = document.getElementById('dash-result-image') as HTMLImageElement;
      const ph = document.getElementById('dash-placeholder') as HTMLDivElement;
      if (img && ph) {
        img.src = data.image;
        img.style.display = 'block';
        ph.style.display = 'none';
      }
    }
    // Pipeline performance
    const fpsEl = document.getElementById('pipeline-fps-display');
    const latEl = document.getElementById('pipeline-latency-display');
    if (fpsEl) fpsEl.textContent = `${data.pipeline_ms || 0}ms pipeline`;
    if (latEl) latEl.textContent = `Frame #${data.frame_id || 0}`;
  }

  updateRiskBanner(risk: any) {
    if (!risk) return;
    const badge = document.getElementById('risk-level-badge');
    const score = document.getElementById('risk-score-display');
    const reason = document.getElementById('risk-reason');
    const action = document.getElementById('risk-action');
    const banner = document.getElementById('risk-banner');

    if (badge) {
      badge.textContent = risk.risk_level || 'LOW';
      badge.className = `risk-level-badge risk-${(risk.risk_level || 'low').toLowerCase()}`;
    }
    if (score) score.innerHTML = `${Math.round(risk.risk_score || 0)}<small>/100</small>`;
    if (reason) reason.textContent = risk.reason || 'No threats detected';
    if (action) action.textContent = risk.recommended_action || 'NO_ACTION';
    if (banner) {
      banner.className = `risk-banner risk-banner-${(risk.risk_level || 'low').toLowerCase()}`;
    }
  }

  updateTrainPanel(train: any) {
    const set = (id: string, val: string) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };
    if (!train) {
      set('train-name-display', '—');
      set('train-number-display', '—');
      set('train-route-display', '—');
      set('train-speed-display', '—');
      set('train-distance-display', '—');
      set('train-tti-display', '—');
      set('train-direction-display', '—');
      return;
    }
    set('train-name-display', train.train_name || '—');
    set('train-number-display', train.train_number || '—');
    set('train-route-display', `${train.source_station || '?'} → ${train.destination_station || '?'}`);
    set('train-speed-display', train.speed_kmph != null ? `${train.speed_kmph} km/h` : '—');
    set('train-distance-display', train.distance_km != null ? `${train.distance_km.toFixed(1)} km` : '—');
    set('train-tti-display', train.tti_display || '—');
    set('train-direction-display', train.is_approaching ? '⬇️ Approaching' : '➡️ ' + (train.direction || 'Unknown'));
  }

  updateRiskBreakdown(breakdown: any) {
    if (!breakdown) return;
    const items: [string, string, string][] = [
      ['bar-severity', 'val-severity', 'object_severity'],
      ['bar-occupancy', 'val-occupancy', 'track_occupancy'],
      ['bar-proximity', 'val-proximity', 'train_proximity'],
      ['bar-speed', 'val-speed', 'train_speed'],
      ['bar-collision', 'val-collision', 'collision_probability'],
      ['bar-persistence', 'val-persistence', 'persistence'],
    ];
    for (const [barId, valId, key] of items) {
      const val = breakdown[key] || 0;
      const bar = document.getElementById(barId) as HTMLDivElement;
      const valEl = document.getElementById(valId);
      if (bar) bar.style.width = `${Math.min(100, val)}%`;
      if (valEl) valEl.textContent = Math.round(val).toString();
    }
  }

  updateLocationPanel(loc: any) {
    if (!loc) return;
    const set = (id: string, val: string) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };
    set('loc-name-display', loc.name || '—');
    set('loc-gps-display', loc.latitude && loc.longitude ? `${loc.latitude.toFixed(4)}, ${loc.longitude.toFixed(4)}` : '—');
    set('loc-station-display', loc.nearest_station || '—');
    set('loc-division-display', loc.division || '—');
    set('loc-zone-display', loc.railway_zone || '—');
  }

  updateAuthorityPanel(auth: any) {
    if (!auth) return;
    const primary = auth.primary_authority || (Array.isArray(auth) ? auth[0] : null) || (auth.authorities ? auth.authorities[0] : null) || auth;
    const set = (id: string, val: string) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };
    if (!primary || !primary.name) {
      set('auth-name-display', 'Retrieving from RAG...');
      set('auth-role-display', '—');
      set('auth-email-display', '—');
      set('auth-jurisdiction-display', '—');
      return;
    }
    set('auth-name-display', primary.name || '—');
    set('auth-role-display', primary.designation || '—');
    set('auth-email-display', primary.email || '—');
    set('auth-jurisdiction-display', primary.jurisdiction || primary.section || primary.station || '—');
    const badge = document.getElementById('auth-rag-badge');
    if (badge) {
      badge.textContent = primary.is_primary_incharge ? '✓ RAG IN-CHARGE' : 'RAG LINKED';
      badge.style.background = '#10b981';
    }
  }

  async loadInitialRailwayState() {
    try {
      const res = await fetch(`${API_BASE}/api/dashboard`);
      if (res.ok) {
        const data = await res.json();
        if (data.monitoring_location) this.updateLocationPanel(data.monitoring_location);
        if (data.trains && data.trains[0]) this.updateTrainPanel(data.trains[0]);
        if (data.authority) this.updateAuthorityPanel(data.authority);
      }
    } catch (e) {
      console.warn('Initial railway state fetch fallback:', e);
    }
  }

  updateAlertPanel(alert: any) {
    if (!alert) return;
    const statusEl = document.getElementById('alert-status-display');
    const countEl = document.getElementById('alert-active-count');
    const listEl = document.getElementById('active-events-list');

    const activeEvents = alert.active_events || [];
    const hasAlertSent = alert.approved || activeEvents.some((e: any) => e.status === 'ALERT_SENT');
    if (statusEl) {
      statusEl.textContent = hasAlertSent ? '🚨 ALERT EMAIL DISPATCHED' : activeEvents.length > 0 ? '⚠️ Monitoring' : '✅ No active alerts';
    }
    if (countEl) countEl.textContent = String(activeEvents.length);
    if (listEl) {
      if (activeEvents.length === 0) {
        listEl.innerHTML = '<div style="color:var(--text-tertiary);font-size:0.75rem;padding:0.25rem 0">No active events</div>';
      } else {
        listEl.innerHTML = activeEvents.map((e: any) => `
          <div class="active-event-item risk-${(e.risk_level||'low').toLowerCase()}">
            <span class="event-id">${e.event_id}</span>
            <span class="risk-level-badge risk-${(e.risk_level||'low').toLowerCase()}" style="font-size:0.65rem">${e.risk_level}</span>
            <span>${e.object_type || 'Unknown'}</span>
            <span class="event-status">${e.status}</span>
          </div>
        `).join('');
      }
    }
  }

  updateTrackedObjectsTable(objects: any[]) {
    const tbody = document.getElementById('tracked-objects-tbody');
    const badge = document.getElementById('tracked-count-badge');
    if (badge) badge.textContent = String(objects.length);
    if (!tbody) return;

    if (objects.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-tertiary)">No objects tracked</td></tr>';
      return;
    }

    tbody.innerHTML = objects.map((o: any) => {
      const z = (o.zone || 'SAFE').toUpperCase();
      const isDanger = z === 'DANGER';
      const isMedium = z === 'MEDIUM' || z === 'WARNING';
      const zoneClass = isDanger ? 'zone-danger' : isMedium ? 'zone-medium' : 'zone-safe';
      const zoneDisplay = isDanger ? '🚨 DANGER' : isMedium ? '⚠️ MEDIUM' : '🛡️ SAFE';
      return `
        <tr class="${zoneClass}">
          <td>#${o.track_id}</td>
          <td>${o.object || o.class_name}</td>
          <td>${Math.round((o.confidence || 0) * 100)}%</td>
          <td><span class="zone-badge ${zoneClass}">${zoneDisplay}</span></td>
          <td>${o.movement || 'stationary'}</td>
          <td>${(o.duration_on_track || 0).toFixed(1)}s</td>
          <td>${(o.speed_px_s || 0).toFixed(0)} px/s</td>
          <td>${o.is_stationary ? '⏸️ Stationary' : '▶️ Moving'}</td>
        </tr>
      `;
    }).join('');
  }

  // === Alert History ===
  async loadAlertHistory() {
    const riskFilter = (document.getElementById('history-risk-filter') as HTMLSelectElement)?.value || '';
    const statusFilter = (document.getElementById('history-status-filter') as HTMLSelectElement)?.value || '';
    const params = new URLSearchParams();
    params.set('limit', String(this.historyLimit));
    params.set('offset', String(this.historyPage * this.historyLimit));
    if (riskFilter) params.set('risk_level', riskFilter);
    if (statusFilter) params.set('status', statusFilter);

    try {
      const res = await fetch(`${API_BASE}/api/events?${params}`);
      const data = await res.json();
      this.renderAlertHistory(data.events || [], data.total || 0);
    } catch (e) {
      console.error('Failed to load alert history:', e);
    }
  }

  renderAlertHistory(events: any[], total: number) {
    const tbody = document.getElementById('history-tbody');
    if (!tbody) return;

    if (events.length === 0) {
      tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;color:var(--text-tertiary)">No events found</td></tr>';
    } else {
      tbody.innerHTML = events.map((e: any) => `
        <tr class="risk-${(e.risk_level||'low').toLowerCase()}">
          <td style="font-family:'JetBrains Mono',monospace;font-size:0.7rem">${e.event_id || '—'}</td>
          <td>${e.first_detected_at ? new Date(e.first_detected_at).toLocaleString() : '—'}</td>
          <td>${e.object_type || '—'} (×${e.object_count || 1})</td>
          <td><span class="risk-level-badge risk-${(e.risk_level||'low').toLowerCase()}" style="font-size:0.65rem">${e.risk_level || '—'}</span></td>
          <td>${e.risk_score || 0}</td>
          <td>${e.zone || '—'}</td>
          <td>${e.train_name || '—'}</td>
          <td>${e.nearest_station || '—'}</td>
          <td><span class="event-status-badge">${e.status || '—'}</span></td>
          <td>
            ${e.status !== 'RESOLVED' ? `<button class="btn btn-sm btn-danger resolve-btn" data-eid="${e.event_id}">Resolve</button>` : ''}
          </td>
        </tr>
      `).join('');

      // Add resolve button handlers
      tbody.querySelectorAll('.resolve-btn').forEach((btn) => {
        btn.addEventListener('click', async () => {
          const eid = (btn as HTMLElement).dataset.eid;
          if (eid) {
            await fetch(`${API_BASE}/api/events/${eid}/resolve`, { method: 'POST' });
            this.loadAlertHistory();
          }
        });
      });
    }

    // Pagination
    const pag = document.getElementById('history-pagination');
    if (pag) {
      const totalPages = Math.ceil(total / this.historyLimit);
      pag.innerHTML = `
        <span style="color:var(--text-secondary);font-size:0.8rem">
          Page ${this.historyPage + 1} of ${totalPages || 1} (${total} events)
        </span>
        <div>
          <button class="btn btn-sm btn-secondary" ${this.historyPage === 0 ? 'disabled' : ''} id="hist-prev">Prev</button>
          <button class="btn btn-sm btn-secondary" ${this.historyPage >= totalPages - 1 ? 'disabled' : ''} id="hist-next">Next</button>
        </div>
      `;
      document.getElementById('hist-prev')?.addEventListener('click', () => {
        if (this.historyPage > 0) { this.historyPage--; this.loadAlertHistory(); }
      });
      document.getElementById('hist-next')?.addEventListener('click', () => {
        if (this.historyPage < totalPages - 1) { this.historyPage++; this.loadAlertHistory(); }
      });
    }
  }

  // === Admin Panel ===
  async loadAdminData() {
    // Load zones defensively
    try {
      const zRes = await fetch(`${API_BASE}/api/zones`);
      if (zRes.ok) {
        const zones = await zRes.json();
        const sp = document.getElementById('admin-safe-polygon') as HTMLTextAreaElement;
        const dp = document.getElementById('admin-danger-polygon') as HTMLTextAreaElement;
        const wp = document.getElementById('admin-warning-polygon') as HTMLTextAreaElement;
        const tc = document.getElementById('admin-track-center') as HTMLTextAreaElement;
        const ze = document.getElementById('admin-zones-enabled') as HTMLInputElement;
        if (sp) sp.value = JSON.stringify(zones.safe_zone?.polygon || zones.safe_zone || [[80,220],[560,220],[640,580],[0,580]]);
        if (dp) dp.value = JSON.stringify(zones.danger_zone?.polygon || zones.danger_zone || [[200,350],[440,350],[520,480],[120,480]]);
        if (wp) wp.value = JSON.stringify(zones.warning_zone?.polygon || zones.warning_zone || [[150,300],[490,300],[580,520],[70,520]]);
        if (tc) tc.value = JSON.stringify(zones.track_center_line || [[320,350],[320,480]]);
        if (ze) ze.checked = zones.zone_enabled !== false;
      }
    } catch (e) {
      console.warn('Zones load fallback:', e);
    }

    // Load risk config defensively
    try {
      const rRes = await fetch(`${API_BASE}/api/risk/config`);
      if (rRes.ok) {
        const risk = await rRes.json();
        const rt = document.getElementById('admin-risk-thresholds') as HTMLTextAreaElement;
        const rw = document.getElementById('admin-risk-weights') as HTMLTextAreaElement;
        if (rt) rt.value = JSON.stringify(risk.thresholds || { low: [0, 30], medium: [31, 60], high: [61, 80], critical: [81, 100] }, null, 2);
        if (rw) rw.value = JSON.stringify(risk.weights || { object_severity: 0.20, track_occupancy: 0.25, train_proximity: 0.20, train_speed: 0.10, collision_probability: 0.15, persistence: 0.10 }, null, 2);
        const cd = document.getElementById('admin-cooldown') as HTMLInputElement;
        const ps = document.getElementById('admin-persistence') as HTMLInputElement;
        const mc = document.getElementById('admin-min-conf') as HTMLInputElement;
        if (cd) cd.value = String(risk.alert_cooldown_seconds || 300);
        if (ps) ps.value = String(risk.min_persistence_seconds || 3);
        if (mc) mc.value = String(risk.min_confidence || 0.45);
      }
    } catch (e) {
      console.warn('Risk config load fallback:', e);
    }

    // Load knowledge base stats defensively
    try {
      const kRes = await fetch(`${API_BASE}/api/knowledge/stats`);
      if (kRes.ok) {
        const kStats = await kRes.json();
        const ktc = document.getElementById('kb-total-chunks');
        const kts = document.getElementById('kb-total-sources');
        const ksl = document.getElementById('kb-sources-list');
        if (ktc) ktc.textContent = String(kStats.total_chunks || 0);
        if (kts) kts.textContent = String(kStats.total_sources || 0);
        if (ksl) ksl.textContent = (kStats.sources || []).join(', ') || 'Standard Railway Operating Guidelines Loaded';
      }
    } catch (e) {
      console.warn('Knowledge stats load fallback:', e);
    }

    // Load notification config defensively
    try {
      const nRes = await fetch(`${API_BASE}/api/notifications/config`);
      if (nRes.ok) {
        const notif = await nRes.json();
        const ar = document.getElementById('admin-alert-recipients') as HTMLInputElement;
        const ee = document.getElementById('admin-email-enabled') as HTMLInputElement;
        const sh = document.getElementById('admin-smtp-host') as HTMLInputElement;
        const se = document.getElementById('admin-sender-email') as HTMLInputElement;
        const we = document.getElementById('admin-wa-enabled') as HTMLInputElement;
        const ws = document.getElementById('admin-wa-sid') as HTMLInputElement;
        const wf = document.getElementById('admin-wa-from') as HTMLInputElement;

        const defaultRecipients = notif.email?.default_recipients || [];
        if (ar) {
          ar.value = defaultRecipients.length > 0 ? defaultRecipients.join(', ') : 'rishe8080s@gmail.com';
        }
        if (ee) ee.checked = notif.email?.enabled !== false;
        if (sh) sh.value = notif.email?.smtp_host || 'smtp.gmail.com';
        if (se) se.value = notif.email?.sender_email || 'rishe8080s@gmail.com';
        const spw = document.getElementById('admin-sender-password') as HTMLInputElement;
        if (spw && notif.email?.sender_password) {
          spw.placeholder = '•••••••••••••••• (Configured)';
        }
        if (we) we.checked = notif.whatsapp?.enabled || false;
        if (ws) ws.value = notif.whatsapp?.account_sid || '';
        if (wf) wf.value = notif.whatsapp?.from_number || '';
      }
    } catch (e) {
      console.warn('Notification config load fallback:', e);
    }

    // Load monitoring location & trains defensively
    try {
      const tRes = await fetch(`${API_BASE}/api/trains`);
      if (tRes.ok) {
        const trains = await tRes.json();
        const ml = trains.monitoring_location || {};
        const la = document.getElementById('admin-mon-lat') as HTMLInputElement;
        const lo = document.getElementById('admin-mon-lon') as HTMLInputElement;
        const nm = document.getElementById('admin-mon-name') as HTMLInputElement;
        const st = document.getElementById('admin-mon-station') as HTMLInputElement;
        const rz = document.getElementById('admin-mon-rzone') as HTMLInputElement;
        const dv = document.getElementById('admin-mon-division') as HTMLInputElement;
        if (la) la.value = String(ml.latitude || 11.0168);
        if (lo) lo.value = String(ml.longitude || 76.9558);
        if (nm) nm.value = ml.name || 'Coimbatore Railway Section';
        if (st) st.value = ml.nearest_station || 'Coimbatore Junction';
        if (rz) rz.value = ml.railway_zone || 'Southern Railway';
        if (dv) dv.value = ml.division || 'Salem Division';

        this.renderTrainList(trains.trains || []);
      }
    } catch (e) {
      console.warn('Trains load fallback:', e);
    }
  }

  renderTrainList(trains: any[]) {
    const el = document.getElementById('admin-train-list');
    if (!el) return;
    if (trains.length === 0) {
      el.innerHTML = '<div style="color:var(--text-tertiary);font-size:0.75rem">No active trains in proximity</div>';
      return;
    }
    el.innerHTML = trains.map((t: any) => `
      <div class="admin-train-item">
        <span><strong>${t.train_name}</strong> (${t.train_number})</span>
        <span style="font-size:0.7rem;color:var(--text-secondary)">${t.distance_km != null ? t.distance_km.toFixed(1) : '?'} km away · ${t.speed_kmph || 80} km/h</span>
        <button class="btn btn-sm btn-danger del-train-btn" data-tn="${t.train_number}">Remove</button>
      </div>
    `).join('');

    el.querySelectorAll('.del-train-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const tn = (btn as HTMLElement).dataset.tn;
        if (tn) {
          await fetch(`${API_BASE}/api/trains/${tn}`, { method: 'DELETE' });
          this.loadAdminData();
        }
      });
    });
  }

  /** Initialize all admin panel event handlers with validation & feedback */
  initAdminHandlers() {
    // Save zones
    document.getElementById('admin-save-zones-btn')?.addEventListener('click', async () => {
      try {
        const body: any = {};
        const sp = (document.getElementById('admin-safe-polygon') as HTMLTextAreaElement)?.value;
        const dp = (document.getElementById('admin-danger-polygon') as HTMLTextAreaElement)?.value;
        const wp = (document.getElementById('admin-warning-polygon') as HTMLTextAreaElement)?.value;
        const tc = (document.getElementById('admin-track-center') as HTMLTextAreaElement)?.value;
        if (sp) body.safe_polygon = JSON.parse(sp);
        if (dp) body.danger_polygon = JSON.parse(dp);
        if (wp) body.warning_polygon = JSON.parse(wp);
        if (tc) body.track_center_line = JSON.parse(tc);
        body.zone_enabled = (document.getElementById('admin-zones-enabled') as HTMLInputElement)?.checked;
        const res = await fetch(`${API_BASE}/api/zones`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        if (res.ok) {
          this.showStatus('admin-zone-status', '✓ Zone configuration successfully saved!', 'success');
        } else {
          this.showStatus('admin-zone-status', `Server error: ${res.statusText}`, 'error');
        }
      } catch (e) {
        this.showStatus('admin-zone-status', `Invalid JSON syntax: ${e}`, 'error');
      }
    });

    // Reset default zones
    document.getElementById('admin-reset-zones-btn')?.addEventListener('click', () => {
      const sp = document.getElementById('admin-safe-polygon') as HTMLTextAreaElement;
      const dp = document.getElementById('admin-danger-polygon') as HTMLTextAreaElement;
      const wp = document.getElementById('admin-warning-polygon') as HTMLTextAreaElement;
      const tc = document.getElementById('admin-track-center') as HTMLTextAreaElement;
      if (sp) sp.value = JSON.stringify([[80,220],[560,220],[640,580],[0,580]]);
      if (dp) dp.value = JSON.stringify([[200,350],[440,350],[520,480],[120,480]]);
      if (wp) wp.value = JSON.stringify([[150,300],[490,300],[580,520],[70,520]]);
      if (tc) tc.value = JSON.stringify([[320,350],[320,480]]);
      this.showStatus('admin-zone-status', 'Default track coordinates restored. Click "Save Zone Config" to apply.', 'success');
    });

    // Save risk
    document.getElementById('admin-save-risk-btn')?.addEventListener('click', async () => {
      try {
        const body: any = {};
        const rt = (document.getElementById('admin-risk-thresholds') as HTMLTextAreaElement)?.value;
        const rw = (document.getElementById('admin-risk-weights') as HTMLTextAreaElement)?.value;
        if (rt && rt.trim()) body.thresholds = JSON.parse(rt);
        if (rw && rw.trim()) body.weights = JSON.parse(rw);
        body.alert_cooldown_seconds = parseInt((document.getElementById('admin-cooldown') as HTMLInputElement)?.value || '300');
        body.min_persistence_seconds = parseInt((document.getElementById('admin-persistence') as HTMLInputElement)?.value || '3');
        body.min_confidence = parseFloat((document.getElementById('admin-min-conf') as HTMLInputElement)?.value || '0.45');
        const res = await fetch(`${API_BASE}/api/risk/config`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        if (res.ok) {
          this.showStatus('admin-risk-status', '✓ Risk settings successfully applied!', 'success');
        } else {
          this.showStatus('admin-risk-status', `Server error: ${res.statusText}`, 'error');
        }
      } catch (e) {
        this.showStatus('admin-risk-status', `Error parsing thresholds/weights JSON: ${e}`, 'error');
      }
    });

    // Upload knowledge base file
    document.getElementById('kb-file-upload')?.addEventListener('change', async (e) => {
      const input = e.target as HTMLInputElement;
      const file = input.files?.[0];
      if (!file) return;
      const fd = new FormData();
      fd.append('file', file);
      try {
        const res = await fetch(`${API_BASE}/api/knowledge/upload`, { method: 'POST', body: fd });
        const data = await res.json();
        this.showStatus('kb-upload-status', `✓ Uploaded ${file.name}: ${data.chunks_processed || 0} chunks indexed`, 'success');
        this.loadAdminData();
      } catch (err) {
        this.showStatus('kb-upload-status', `Upload failed: ${err}`, 'error');
      }
      input.value = '';
    });

    // Reindex
    document.getElementById('kb-reindex-btn')?.addEventListener('click', async () => {
      try {
        const res = await fetch(`${API_BASE}/api/knowledge/reindex`, { method: 'POST' });
        const data = await res.json();
        this.showStatus('kb-upload-status', `✓ Re-indexed: ${data.chunks_processed || 0} chunks`, 'success');
        this.loadAdminData();
      } catch (err) {
        this.showStatus('kb-upload-status', `Reindex failed: ${err}`, 'error');
      }
    });

    // Test RAG In-Charge Authority Match
    document.getElementById('admin-rag-test-btn')?.addEventListener('click', async () => {
      const station = (document.getElementById('admin-rag-test-station') as HTMLInputElement)?.value || 'Coimbatore Junction';
      const resultBox = document.getElementById('admin-rag-result-box');
      if (resultBox) {
        resultBox.style.display = 'block';
        resultBox.innerHTML = '<span style="color:#60a5fa">🔍 Querying RAG Knowledge Store for in-charge authority...</span>';
      }
      try {
        const res = await fetch(`${API_BASE}/api/knowledge/authorities?station=${encodeURIComponent(station)}`);
        const data = await res.json();
        const primary = data.primary_incharge;
        if (resultBox) {
          if (primary) {
            resultBox.innerHTML = `
              <div style="color:#10b981;font-weight:600;margin-bottom:6px">✓ RAG Matched In-Charge for "${station}":</div>
              <div style="margin-bottom:2px"><strong>Officer:</strong> ${primary.name || '—'}</div>
              <div style="margin-bottom:2px"><strong>Designation:</strong> ${primary.designation || '—'}</div>
              <div style="margin-bottom:2px"><strong>Alert Mail:</strong> <code style="color:#60a5fa;font-weight:bold">${primary.email || '—'}</code></div>
              <div style="margin-bottom:2px"><strong>Phone:</strong> ${primary.phone || '—'}</div>
              <div style="margin-bottom:2px"><strong>Jurisdiction:</strong> ${primary.jurisdiction || primary.section || primary.station || '—'}</div>
              <div style="font-size:0.7rem;color:var(--text-tertiary);margin-top:6px;border-top:1px solid rgba(255,255,255,0.08);padding-top:4px">
                Total Matches: ${data.count} · Affinity Score: ${primary.location_match_score || 0} · Vector Score: ${primary.vector_score || 0}
              </div>
            `;
          } else {
            resultBox.innerHTML = `<div style="color:#ef4444">No matching authority in knowledge base for "${station}".</div>`;
          }
        }
      } catch (err) {
        if (resultBox) resultBox.innerHTML = `<div style="color:#ef4444">RAG query failed: ${err}</div>`;
      }
    });

    // Save notifications
    document.getElementById('admin-save-notif-btn')?.addEventListener('click', async () => {
      try {
        const rawRecipients = (document.getElementById('admin-alert-recipients') as HTMLInputElement)?.value || 'rishe8080s@gmail.com';
        const recipientsList = rawRecipients.split(',').map(s => s.trim()).filter(Boolean);

        const senderPassword = (document.getElementById('admin-sender-password') as HTMLInputElement)?.value;
        const waToken = (document.getElementById('admin-wa-token') as HTMLInputElement)?.value;

        const body: any = {
          email: {
            enabled: (document.getElementById('admin-email-enabled') as HTMLInputElement)?.checked,
            smtp_host: (document.getElementById('admin-smtp-host') as HTMLInputElement)?.value || 'smtp.gmail.com',
            sender_email: (document.getElementById('admin-sender-email') as HTMLInputElement)?.value || '',
            default_recipients: recipientsList,
          },
          whatsapp: {
            enabled: (document.getElementById('admin-wa-enabled') as HTMLInputElement)?.checked,
            account_sid: (document.getElementById('admin-wa-sid') as HTMLInputElement)?.value || '',
            from_number: (document.getElementById('admin-wa-from') as HTMLInputElement)?.value || '',
          }
        };

        if (senderPassword) body.email.sender_password = senderPassword;
        if (waToken) body.whatsapp.auth_token = waToken;

        const res = await fetch(`${API_BASE}/api/notifications/config`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        if (res.ok) {
          this.showStatus('admin-notif-status', `✓ Notification settings saved! Alerts set to: ${recipientsList.join(', ')}`, 'success');
        } else {
          this.showStatus('admin-notif-status', `Save failed: ${res.statusText}`, 'error');
        }
      } catch (e) {
        this.showStatus('admin-notif-status', `Error: ${e}`, 'error');
      }
    });

    // Test Email Dispatch Button
    document.getElementById('admin-test-email-btn')?.addEventListener('click', async () => {
      const statusEl = document.getElementById('admin-notif-status');
      if (statusEl) {
        statusEl.textContent = '📨 Sending test alert email...';
        statusEl.className = 'admin-status';
      }
      try {
        const rawRecipients = (document.getElementById('admin-alert-recipients') as HTMLInputElement)?.value || 'rishe8080s@gmail.com';
        const recipient = rawRecipients.split(',')[0].trim() || 'rishe8080s@gmail.com';

        const res = await fetch(`${API_BASE}/api/notifications/test-email`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: recipient })
        });
        const data = await res.json();
        if (data.success) {
          this.showStatus('admin-notif-status', `✓ Test alert delivered successfully to ${recipient}!`, 'success');
        } else {
          this.showStatus('admin-notif-status', `❌ Delivery error: ${data.message || 'Check Sender Email and App Password in SMTP settings'}`, 'error');
        }
      } catch (e) {
        this.showStatus('admin-notif-status', `Network error while sending test email: ${e}`, 'error');
      }
    });

    // Save monitoring location
    document.getElementById('admin-save-location-btn')?.addEventListener('click', async () => {
      try {
        const body = {
          latitude: parseFloat((document.getElementById('admin-mon-lat') as HTMLInputElement)?.value || '11.0168'),
          longitude: parseFloat((document.getElementById('admin-mon-lon') as HTMLInputElement)?.value || '76.9558'),
          name: (document.getElementById('admin-mon-name') as HTMLInputElement)?.value || 'Coimbatore Railway Section',
          nearest_station: (document.getElementById('admin-mon-station') as HTMLInputElement)?.value || 'Coimbatore Junction',
          railway_zone: (document.getElementById('admin-mon-rzone') as HTMLInputElement)?.value || 'Southern Railway',
          division: (document.getElementById('admin-mon-division') as HTMLInputElement)?.value || 'Salem Division',
        };
        const res = await fetch(`${API_BASE}/api/monitoring-location`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        if (res.ok) {
          this.showStatus('admin-location-status', '✓ Location & GPS details saved!', 'success');
        } else {
          this.showStatus('admin-location-status', `Save failed: ${res.statusText}`, 'error');
        }
      } catch (e) {
        this.showStatus('admin-location-status', `Error: ${e}`, 'error');
      }
    });

    // Add / Update train
    document.getElementById('admin-add-train-btn')?.addEventListener('click', async () => {
      try {
        const tNum = (document.getElementById('admin-train-number') as HTMLInputElement)?.value;
        const tName = (document.getElementById('admin-train-name') as HTMLInputElement)?.value;
        if (!tNum || !tName) {
          this.showStatus('admin-train-status', 'Please enter Train Number and Train Name', 'error');
          return;
        }

        const body = {
          train_number: tNum,
          train_name: tName,
          source_station: (document.getElementById('admin-train-source') as HTMLInputElement)?.value || 'Chennai Central',
          destination_station: (document.getElementById('admin-train-dest') as HTMLInputElement)?.value || 'Coimbatore Junction',
          speed_kmph: parseFloat((document.getElementById('admin-train-speed') as HTMLInputElement)?.value || '85'),
          current_location: {
            latitude: parseFloat((document.getElementById('admin-train-lat') as HTMLInputElement)?.value || '11.050'),
            longitude: parseFloat((document.getElementById('admin-train-lon') as HTMLInputElement)?.value || '76.990'),
          },
          direction: 'towards_monitoring',
          status: 'running',
        };
        const res = await fetch(`${API_BASE}/api/trains`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        if (res.ok) {
          this.showStatus('admin-train-status', `✓ Train ${tName} (${tNum}) added!`, 'success');
          this.loadAdminData();
        } else {
          this.showStatus('admin-train-status', `Failed to add train: ${res.statusText}`, 'error');
        }
      } catch (e) {
        this.showStatus('admin-train-status', `Error: ${e}`, 'error');
      }
    });

    // History filters
    document.getElementById('history-risk-filter')?.addEventListener('change', () => { this.historyPage = 0; this.loadAlertHistory(); });
    document.getElementById('history-status-filter')?.addEventListener('change', () => { this.historyPage = 0; this.loadAlertHistory(); });
    document.getElementById('history-refresh-btn')?.addEventListener('click', () => this.loadAlertHistory());
  }

  showStatus(id: string, msg: string, type: 'success' | 'error') {
    const el = document.getElementById(id);
    if (el) {
      el.textContent = msg;
      el.className = `admin-status ${type}`;
      setTimeout(() => { el.textContent = ''; el.className = 'admin-status'; }, 4000);
    }
  }
}
