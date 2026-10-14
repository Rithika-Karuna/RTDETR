"""
Email Notification Service — sends emergency alert emails
with evidence images via SMTP.
"""
import os
import json
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from typing import Optional

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "notification_config.json")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


class EmailService:
    """Sends emergency alert emails to railway authorities via SMTP."""
    
    def __init__(self):
        self.enabled = True
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587
        self.use_tls = True
        self.sender_email = "rishe8080s@gmail.com"
        self.sender_password = "amig fyic qggo vagg"
        self.sender_name = "Railway Track Alert System"
        self.default_recipients = ["rishe8080s@gmail.com"]
        self.last_error = ""
        self._load_config()
    
    def _load_config(self):
        """Load email configuration."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                email_config = config.get("email", {})
                self.enabled = email_config.get("enabled", True)
                self.smtp_host = email_config.get("smtp_host", "smtp.gmail.com")
                self.smtp_port = email_config.get("smtp_port", 587)
                self.use_tls = email_config.get("smtp_use_tls", True)
                self.sender_email = email_config.get("sender_email") or self.sender_email
                self.sender_password = email_config.get("sender_password") or self.sender_password
                self.sender_name = email_config.get("sender_name", "Railway Track Alert System")
                self.default_recipients = email_config.get("default_recipients") or self.default_recipients
        except Exception as e:
            print(f"[EmailService] Config load error: {e}")

    def _send_smtp_message(self, msg: MIMEMultipart, clean_sender: str, clean_password: str):
        """Attempt SMTP delivery via configured port (STARTTLS) with automatic fallback to SSL port 465."""
        last_exc = None
        ports_to_try = [(self.smtp_port, self.use_tls, False)]
        if self.smtp_port != 465:
            ports_to_try.append((465, False, True))
        elif self.smtp_port == 465:
            ports_to_try = [(465, False, True), (587, True, False)]

        for port, use_tls, use_ssl in ports_to_try:
            try:
                if use_ssl:
                    with smtplib.SMTP_SSL(self.smtp_host, port, timeout=6) as server:
                        server.ehlo()
                        server.login(clean_sender, clean_password)
                        server.send_message(msg)
                        return
                else:
                    with smtplib.SMTP(self.smtp_host, port, timeout=6) as server:
                        server.ehlo()
                        if use_tls:
                            server.starttls()
                            server.ehlo()
                        server.login(clean_sender, clean_password)
                        server.send_message(msg)
                        return
            except Exception as exc:
                last_exc = exc
                continue

        if last_exc:
            raise last_exc
    
    def send_alert(self, to_email: str, payload: dict,
                   evidence_path: Optional[str] = None) -> bool:
        """
        Send an emergency alert email.
        
        Args:
            to_email: Recipient email address
            payload: Alert data dict
            evidence_path: Optional path to evidence image
        
        Returns:
            True if sent successfully, False otherwise
        """
        self.last_error = ""
        if not self.sender_email or not self.sender_password:
            self._load_config()

        if not self.enabled:
            self.last_error = "Email alerts are disabled in configuration."
            print(f"[EmailService] Email not enabled. Would send to: {to_email}")
            return False
        
        if not self.sender_email or not self.sender_password:
            self.last_error = "Sender email or Google App Password not configured."
            print("[EmailService] Sender credentials not configured")
            return False
        
        try:
            msg = MIMEMultipart("related")
            
            # Subject
            risk_level = payload.get("risk_level", "HIGH")
            subject = f"⚠️ {risk_level} RAILWAY TRACK OBSTRUCTION — Immediate Attention Required"
            msg["Subject"] = subject
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = to_email
            msg["X-Priority"] = "1"  # High priority
            
            has_evidence = bool(evidence_path and os.path.exists(evidence_path))
            
            # Build HTML body
            html_body = self._build_html(payload, has_evidence=has_evidence)
            msg_alt = MIMEMultipart("alternative")
            msg_alt.attach(MIMEText(self._build_text(payload), "plain"))
            msg_alt.attach(MIMEText(html_body, "html"))
            msg.attach(msg_alt)

            # Archive local HTML copy of the alert report
            try:
                evt_id = payload.get("event_id") or datetime.utcnow().strftime("%Y%m%d%H%M%S")
                report_file = os.path.join(REPORTS_DIR, f"email_{evt_id}.html")
                with open(report_file, "w", encoding="utf-8") as rf:
                    rf.write(html_body)
            except Exception:
                pass
            
            # Attach evidence image
            if has_evidence:
                with open(evidence_path, "rb") as img_file:
                    img = MIMEImage(img_file.read())
                    img.add_header("Content-ID", "<evidence>")
                    img.add_header("Content-Disposition", "inline",
                                 filename=os.path.basename(evidence_path))
                    msg.attach(img)
            
            # Google App Passwords are often formatted with spaces (e.g. "amig fyic qggo vagg")
            clean_password = self.sender_password.replace(" ", "").strip()
            clean_sender = self.sender_email.strip()

            # Send via SMTP (tries port 587 STARTTLS and port 465 SSL)
            self._send_smtp_message(msg, clean_sender, clean_password)
            
            print(f"[EmailService] Alert sent to {to_email}")
            return True
            
        except (TimeoutError, socket.timeout, OSError) as e:
            self.last_error = (
                f"SMTP connection timed out ({e}). Outbound SMTP ports (587/465) appear blocked by the current Wi-Fi/firewall. "
                f"Switch to a mobile hotspot or unrestricted network for live Gmail delivery."
            )
            print(f"[EmailService] Send failed to {to_email}: {self.last_error}")
            return False
        except Exception as e:
            self.last_error = str(e)
            print(f"[EmailService] Send failed to {to_email}: {e}")
            return False
    
    def _build_html(self, payload: dict, has_evidence: bool = False) -> str:
        """Build HTML email body."""
        risk_color = "#dc2626" if payload.get("risk_level") == "CRITICAL" else "#f59e0b"
        evidence_html = (
            '<div style="margin-top: 16px; text-align: center;">'
            '<p style="color: #9ca3af; font-size: 13px; margin-bottom: 8px;">📸 Captured Track Obstruction Evidence:</p>'
            '<img src="cid:evidence" alt="Track Obstruction Evidence" style="max-width: 100%; border-radius: 8px; border: 2px solid ' + risk_color + ';" />'
            '</div>'
        ) if has_evidence else ""
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #16213e; border-radius: 12px; overflow: hidden; border: 2px solid {risk_color};">
                <div style="background: {risk_color}; padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">
                        ⚠️ {payload.get('risk_level', 'HIGH')} — RAILWAY TRACK OBSTRUCTION
                    </h1>
                </div>
                
                <div style="padding: 24px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px; color: #9ca3af;">Event ID:</td>
                            <td style="padding: 8px; font-weight: bold;">{payload.get('event_id', 'N/A')}</td></tr>
                        <tr><td style="padding: 8px; color: #9ca3af;">Object Detected:</td>
                            <td style="padding: 8px; font-weight: bold;">{payload.get('object_type', 'Unknown')}</td></tr>
                        <tr><td style="padding: 8px; color: #9ca3af;">Object Count:</td>
                            <td style="padding: 8px;">{payload.get('object_count', 1)}</td></tr>
                        <tr><td style="padding: 8px; color: #9ca3af;">Confidence:</td>
                            <td style="padding: 8px;">{int((payload.get('confidence', 0) or 0) * 100)}%</td></tr>
                        <tr><td style="padding: 8px; color: #9ca3af;">Risk Score:</td>
                            <td style="padding: 8px; color: {risk_color}; font-weight: bold;">{payload.get('risk_score', 0)}/100</td></tr>
                        <tr><td style="padding: 8px; color: #9ca3af;">Zone:</td>
                            <td style="padding: 8px;">{payload.get('zone', 'DANGER')}</td></tr>
                        <tr style="background: rgba(255,255,255,0.05);">
                            <td style="padding: 8px; color: #9ca3af;">Location:</td>
                            <td style="padding: 8px;">{payload.get('location_name', 'N/A')}</td></tr>
                        <tr><td style="padding: 8px; color: #9ca3af;">GPS:</td>
                            <td style="padding: 8px;">{payload.get('gps_display', 'N/A')}</td></tr>
                        <tr><td style="padding: 8px; color: #9ca3af;">Nearest Station:</td>
                            <td style="padding: 8px;">{payload.get('nearest_station', 'N/A')}</td></tr>
                        <tr><td style="padding: 8px; color: #9ca3af;">Division / Zone:</td>
                            <td style="padding: 8px;">{payload.get('division', 'N/A')} ({payload.get('railway_zone', 'N/A')})</td></tr>
                        <tr style="background: rgba(59, 130, 246, 0.15); border-left: 3px solid #3b82f6;">
                            <td style="padding: 8px; color: #93c5fd; font-weight: bold;">In-Charge Authority (RAG):</td>
                            <td style="padding: 8px; font-weight: bold; color: #60a5fa;">{payload.get('incharge_name', 'N/A')} — {payload.get('incharge_designation', 'N/A')}<br/><small style="color:#bfdbfe">Email: {payload.get('incharge_email', 'N/A')} | {payload.get('incharge_jurisdiction', '')}</small></td></tr>
                        <tr style="background: rgba(255,255,255,0.05);">
                            <td style="padding: 8px; color: #9ca3af;">Train:</td>
                            <td style="padding: 8px;">{payload.get('train_name', 'N/A')} ({payload.get('train_number', 'N/A')})</td></tr>
                        <tr><td style="padding: 8px; color: #9ca3af;">Train Route:</td>
                            <td style="padding: 8px;">{payload.get('train_source', 'N/A')} → {payload.get('train_destination', 'N/A')}</td></tr>
                        <tr><td style="padding: 8px; color: #9ca3af;">Train Speed:</td>
                            <td style="padding: 8px;">{payload.get('train_speed', 'N/A')} km/h</td></tr>
                        <tr><td style="padding: 8px; color: #9ca3af;">Train Distance:</td>
                            <td style="padding: 8px;">{payload.get('train_distance_km', 'N/A')} km</td></tr>
                        <tr><td style="padding: 8px; color: #9ca3af;">TTI:</td>
                            <td style="padding: 8px; color: {risk_color};">{payload.get('tti_seconds', 'N/A')}s</td></tr>
                        <tr><td style="padding: 8px; color: #9ca3af;">Timestamp:</td>
                            <td style="padding: 8px;">{payload.get('timestamp', 'N/A')}</td></tr>
                    </table>
                    
                    <div style="margin-top: 16px; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 8px;">
                        <strong>Reason:</strong> {payload.get('reason', 'N/A')}
                    </div>
                    {evidence_html}
                    <div style="margin-top: 20px; padding: 16px; background: #7c2d12; border-radius: 8px; text-align: center;">
                        <strong>⚠️ HUMAN VERIFICATION AND ACTION REQUIRED</strong><br/>
                        <small>{payload.get('safety_notice', '')}</small>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _build_text(self, payload: dict) -> str:
        """Build plain text email body."""
        return f"""
⚠️ {payload.get('risk_level', 'HIGH')} — RAILWAY TRACK OBSTRUCTION

Event ID: {payload.get('event_id', 'N/A')}
Object: {payload.get('object_type', 'Unknown')} (x{payload.get('object_count', 1)})
Confidence: {int((payload.get('confidence', 0) or 0) * 100)}%
Risk Score: {payload.get('risk_score', 0)}/100
Zone: {payload.get('zone', 'DANGER')}

Location: {payload.get('location_name', 'N/A')}
GPS: {payload.get('gps_display', 'N/A')}
Nearest Station: {payload.get('nearest_station', 'N/A')}
Railway Zone / Division: {payload.get('railway_zone', 'N/A')} / {payload.get('division', 'N/A')}

Authority In-Charge (RAG): {payload.get('incharge_name', 'N/A')} ({payload.get('incharge_designation', 'N/A')})
In-Charge Contact Email: {payload.get('incharge_email', 'N/A')}
In-Charge Jurisdiction: {payload.get('incharge_jurisdiction', 'N/A')}

Train: {payload.get('train_name', 'N/A')} ({payload.get('train_number', 'N/A')})
Route: {payload.get('train_source', 'N/A')} → {payload.get('train_destination', 'N/A')}
Speed: {payload.get('train_speed', 'N/A')} km/h
Distance: {payload.get('train_distance_km', 'N/A')} km
TTI: {payload.get('tti_seconds', 'N/A')}s

Reason: {payload.get('reason', 'N/A')}

Timestamp: {payload.get('timestamp', 'N/A')}

{payload.get('safety_notice', '')}
        """
    
    def send_test_alert(self, to_email: str) -> dict:
        """Send a test email to verify SMTP configuration and recipient delivery."""
        test_payload = {
            "event_id": "TEST-ALERT-" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "risk_level": "CRITICAL",
            "risk_score": 98,
            "object_type": "Elephant (Test Alert)",
            "object_count": 1,
            "confidence": 0.96,
            "zone": "DANGER",
            "location_name": "Coimbatore Railway Section",
            "gps_display": "11.016800, 76.955800",
            "nearest_station": "Coimbatore Junction",
            "railway_zone": "Southern Railway",
            "division": "Salem Division",
            "incharge_name": "Er. Rishe S",
            "incharge_designation": "Chief Divisional Safety Officer & Emergency Controller",
            "incharge_email": to_email,
            "incharge_jurisdiction": "Coimbatore Junction - Podanur - Irugur Track Section",
            "train_name": "Shatabdi Express",
            "train_number": "12243",
            "train_source": "Chennai Central",
            "train_destination": "Coimbatore Junction",
            "train_speed": 82.5,
            "train_distance_km": 3.8,
            "tti_seconds": 165,
            "reason": "TEST ALERT: Large obstacle detected directly in Danger Zone (Track Bed) with incoming train approaching",
            "safety_notice": "⚠️ Automated Railway Track Alert Verification. This test confirms email delivery to the designated responder.",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        success = self.send_alert(to_email, test_payload)
        return {
            "success": success,
            "recipient": to_email,
            "message": (
                f"Test alert email successfully dispatched to {to_email}"
                if success
                else (self.last_error or "Failed to send email. Check SMTP credentials or app password.")
            )
        }

    def update_config(self, config: dict):
        """Update email configuration."""
        self.enabled = config.get("enabled", self.enabled)
        self.smtp_host = config.get("smtp_host", self.smtp_host)
        self.smtp_port = config.get("smtp_port", self.smtp_port)
        self.use_tls = config.get("smtp_use_tls", self.use_tls)
        self.sender_email = config.get("sender_email", self.sender_email)
        self.sender_password = config.get("sender_password", self.sender_password)
        self.sender_name = config.get("sender_name", self.sender_name)
        self.default_recipients = config.get("default_recipients", self.default_recipients)


# Singleton
email_service = EmailService()

