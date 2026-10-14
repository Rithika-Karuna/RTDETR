"""
WhatsApp Notification Service — sends emergency alert messages
via WhatsApp Business API (Twilio or direct API).
"""
import os
import json
from datetime import datetime
from typing import Optional

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "notification_config.json")


class WhatsAppService:
    """Sends emergency alert messages via WhatsApp Business API."""
    
    def __init__(self):
        self.enabled = False
        self.provider = "twilio"
        self.account_sid = ""
        self.auth_token = ""
        self.from_number = ""
        self.default_recipients = []
        self._load_config()
    
    def _load_config(self):
        """Load WhatsApp configuration."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                wa_config = config.get("whatsapp", {})
                self.enabled = wa_config.get("enabled", False)
                self.provider = wa_config.get("provider", "twilio")
                self.account_sid = wa_config.get("account_sid", "")
                self.auth_token = wa_config.get("auth_token", "")
                self.from_number = wa_config.get("from_number", "")
                self.default_recipients = wa_config.get("default_recipients", [])
        except Exception as e:
            print(f"[WhatsAppService] Config load error: {e}")
    
    def send_alert(self, to_number: str, payload: dict,
                   evidence_path: Optional[str] = None) -> bool:
        """
        Send an emergency WhatsApp message.
        
        Args:
            to_number: Recipient WhatsApp number
            payload: Alert data dict
            evidence_path: Optional path to evidence image
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            print(f"[WhatsAppService] WhatsApp not enabled. Would send to: {to_number}")
            return False
        
        message = self._build_message(payload)
        
        if self.provider == "twilio":
            return self._send_via_twilio(to_number, message, evidence_path)
        else:
            print(f"[WhatsAppService] Unknown provider: {self.provider}")
            return False
    
    def _send_via_twilio(self, to_number: str, message: str,
                          evidence_path: Optional[str] = None) -> bool:
        """Send via Twilio WhatsApp API."""
        try:
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            
            kwargs = {
                "from_": f"whatsapp:{self.from_number}",
                "body": message,
                "to": f"whatsapp:{to_number}"
            }
            
            # Attach media if available (requires publicly accessible URL)
            # For local files, you'd need to host them first
            
            msg = client.messages.create(**kwargs)
            print(f"[WhatsAppService] Sent to {to_number}: SID={msg.sid}")
            return True
            
        except ImportError:
            print("[WhatsAppService] Twilio library not installed. Install with: pip install twilio")
            return False
        except Exception as e:
            print(f"[WhatsAppService] Send failed to {to_number}: {e}")
            return False
    
    def _build_message(self, payload: dict) -> str:
        """Build WhatsApp alert message."""
        risk_level = payload.get("risk_level", "HIGH")
        
        msg = f"""🚨 *{risk_level} ALERT*

*Railway track obstruction detected.*

📍 *Location:* {payload.get('location_name', 'N/A')}
🚧 *Object:* {payload.get('object_type', 'Unknown')}
🔢 *Count:* {payload.get('object_count', 1)}
📊 *Confidence:* {int((payload.get('confidence', 0) or 0) * 100)}%
⚠️ *Status:* Blocking track
🚂 *Train:* {payload.get('train_name', 'N/A')} ({payload.get('train_number', 'N/A')})
🛤️ *Route:* {payload.get('train_source', 'N/A')} → {payload.get('train_destination', 'N/A')}
⏱️ *Train Distance:* {payload.get('train_distance_km', 'N/A')} km
🎯 *Risk:* {risk_level}
📈 *Risk Score:* {payload.get('risk_score', 0)}/100
📌 *GPS:* {payload.get('gps_display', 'N/A')}
🏪 *Nearest Station:* {payload.get('nearest_station', 'N/A')}

⚠️ *Immediate verification/action required.*
_This is an automated early-warning alert. Human verification is required._

🆔 Event: {payload.get('event_id', 'N/A')}
⏰ Time: {payload.get('timestamp', 'N/A')}"""
        
        return msg
    
    def update_config(self, config: dict):
        """Update WhatsApp configuration."""
        self.enabled = config.get("enabled", self.enabled)
        self.provider = config.get("provider", self.provider)
        self.account_sid = config.get("account_sid", self.account_sid)
        self.auth_token = config.get("auth_token", self.auth_token)
        self.from_number = config.get("from_number", self.from_number)
        self.default_recipients = config.get("default_recipients", self.default_recipients)


# Singleton
whatsapp_service = WhatsAppService()
