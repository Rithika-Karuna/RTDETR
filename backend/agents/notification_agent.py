"""
Agent 7 — Notification Agent
Sends emergency notifications via Email and WhatsApp.
Only dispatches when authorized by the Alert Validation Agent.
"""
import json
import os
from datetime import datetime
from typing import Optional

from database import insert_alert_log


class NotificationAgent:
    """
    Dispatches emergency notifications to authorized railway personnel.
    Supports Email and WhatsApp channels.
    Every alert clearly indicates that human verification/action is required.
    """
    
    def __init__(self, email_service=None, whatsapp_service=None):
        self.email_service = email_service
        self.whatsapp_service = whatsapp_service
        self._notification_log = []
    
    def process(self, validation_result: dict, authority_result: dict,
                location_info: dict, risk_result: dict) -> dict:
        """
        Send notifications if the alert is authorized.
        
        Args:
            validation_result: Output from AlertValidationAgent (must have approved=True)
            authority_result: Output from AuthorityAgent
            location_info: Output from LocationAgent
            risk_result: Output from RiskAgent
        
        Returns:
            Notification dispatch results.
        """
        timestamp = datetime.utcnow().isoformat()
        
        if not validation_result.get("approved"):
            return {
                "agent": "notification",
                "timestamp": timestamp,
                "dispatched": False,
                "reason": "Alert not authorized by validation agent",
                "notifications_sent": []
            }
        
        event = validation_result.get("event", {})
        authorities = authority_result.get("authorities", [])
        notifications_sent = []
        
        # Build notification payload with RAG-retrieved authority details
        payload = self._build_payload(event, location_info, risk_result, authority_result)
        
        # Collect email recipients from primary authority + configured default recipients
        # Exclude simulated internal '.railnet.gov.in' roster emails to prevent SMTP bounce-backs
        target_emails = set()
        for auth in authorities:
            em = (auth.get("email") or "").strip()
            if em and not em.lower().endswith(".railnet.gov.in"):
                target_emails.add(em)
        if self.email_service and getattr(self.email_service, "default_recipients", None):
            for dem in self.email_service.default_recipients:
                if dem and dem.strip():
                    target_emails.add(dem.strip())

        # Collect WhatsApp recipients from authorities + configured default recipients
        target_numbers = set()
        for auth in authorities:
            wa = auth.get("whatsapp") or auth.get("phone")
            if wa:
                target_numbers.add(wa.strip())
        if self.whatsapp_service and getattr(self.whatsapp_service, "default_recipients", None):
            for dwa in self.whatsapp_service.default_recipients:
                if dwa:
                    target_numbers.add(dwa.strip())

        # Send Email notifications
        if self.email_service and target_emails:
            for email in target_emails:
                try:
                    success = self.email_service.send_alert(
                        to_email=email,
                        payload=payload,
                        evidence_path=event.get("evidence_path")
                    )
                    status = "SENT" if success else "FAILED"
                    insert_alert_log(event.get("event_id", ""), "email", email, status)
                    notifications_sent.append({
                        "channel": "email",
                        "recipient": email,
                        "status": status
                    })
                except Exception as e:
                    insert_alert_log(event.get("event_id", ""), "email", email, "FAILED")
                    notifications_sent.append({
                        "channel": "email",
                        "recipient": email,
                        "status": "FAILED",
                        "error": str(e)
                    })
        
        # Send WhatsApp notifications
        if self.whatsapp_service and target_numbers:
            for whatsapp in target_numbers:
                try:
                    success = self.whatsapp_service.send_alert(
                        to_number=whatsapp,
                        payload=payload,
                        evidence_path=event.get("evidence_path")
                    )
                    status = "SENT" if success else "FAILED"
                    insert_alert_log(event.get("event_id", ""), "whatsapp", whatsapp, status)
                    notifications_sent.append({
                        "channel": "whatsapp",
                        "recipient": whatsapp,
                        "status": status
                    })
                except Exception as e:
                    insert_alert_log(event.get("event_id", ""), "whatsapp", whatsapp, "FAILED")
                    notifications_sent.append({
                        "channel": "whatsapp",
                        "recipient": whatsapp,
                        "status": "FAILED",
                        "error": str(e)
                    })
        
        # If no notification services configured, log it
        if not self.email_service and not self.whatsapp_service:
            notifications_sent.append({
                "channel": "system_log",
                "status": "LOGGED",
                "message": "No notification services configured. Alert logged to system."
            })
        
        # If no authorities found in RAG
        if not authorities:
            notifications_sent.append({
                "channel": "system_log",
                "status": "NO_RECIPIENTS",
                "message": "No authority contacts found in knowledge base."
            })
        
        self._notification_log.append({
            "timestamp": timestamp,
            "event_id": event.get("event_id", ""),
            "notifications": notifications_sent
        })
        
        return {
            "agent": "notification",
            "timestamp": timestamp,
            "dispatched": len([n for n in notifications_sent if n.get("status") == "SENT"]) > 0,
            "event_id": event.get("event_id", ""),
            "notifications_sent": notifications_sent,
            "total_sent": len([n for n in notifications_sent if n.get("status") == "SENT"]),
            "total_failed": len([n for n in notifications_sent if n.get("status") == "FAILED"]),
            "payload_summary": {
                "risk_level": payload.get("risk_level"),
                "object_type": payload.get("object_type"),
                "location": payload.get("location_name")
            }
        }
    
    def _build_payload(self, event: dict, location_info: dict, risk_result: dict, authority_result: dict = None) -> dict:
        """Build the notification payload with all relevant information including RAG in-charge details."""
        primary_auth = (authority_result or {}).get("primary_authority") or {}
        
        return {
            "alert_level": event.get("risk_level", "HIGH"),
            "risk_level": event.get("risk_level", "HIGH"),
            "risk_score": event.get("risk_score", 0),
            "event_id": event.get("event_id", ""),
            "event_type": "RAILWAY TRACK OBSTRUCTION",
            "object_type": event.get("object_type", "Unknown"),
            "object_count": event.get("object_count", 1),
            "confidence": event.get("confidence", 0),
            "zone": event.get("zone", "DANGER"),
            "reason": event.get("reason", ""),
            "gps_latitude": event.get("gps_latitude") or location_info.get("latitude"),
            "gps_longitude": event.get("gps_longitude") or location_info.get("longitude"),
            "gps_display": f"{event.get('gps_latitude', 0):.6f}, {event.get('gps_longitude', 0):.6f}",
            "location_name": event.get("location_name") or location_info.get("location_name", ""),
            "nearest_station": event.get("nearest_station") or location_info.get("nearest_station", ""),
            "railway_zone": event.get("railway_zone") or location_info.get("railway_zone", ""),
            "division": event.get("division") or location_info.get("division", ""),
            "incharge_name": primary_auth.get("name", "Designated Emergency Controller"),
            "incharge_designation": primary_auth.get("designation", "Divisional Safety Officer"),
            "incharge_email": primary_auth.get("email", ""),
            "incharge_phone": primary_auth.get("phone", ""),
            "incharge_station": primary_auth.get("station", ""),
            "incharge_jurisdiction": primary_auth.get("jurisdiction", ""),
            "rag_authority_count": (authority_result or {}).get("authority_count", 0),
            "rag_retrieval_status": "MATCHED" if primary_auth else "NO_MATCH",
            "train_number": event.get("train_number", ""),
            "train_name": event.get("train_name", ""),
            "train_source": event.get("train_source", ""),
            "train_destination": event.get("train_destination", ""),
            "train_speed": event.get("train_speed"),
            "train_distance_km": event.get("train_distance_km"),
            "tti_seconds": event.get("tti_seconds"),
            "evidence_path": event.get("evidence_path"),
            "timestamp": datetime.utcnow().isoformat(),
            "safety_notice": "⚠️ This is an automated early-warning alert from the Railway Track Vulnerability Detection System. HUMAN VERIFICATION AND ACTION IS REQUIRED. This system does not control railway signals, brakes, or switches."
        }
    
    def get_recent_notifications(self, limit: int = 50) -> list:
        """Get recent notification history."""
        return self._notification_log[-limit:]
