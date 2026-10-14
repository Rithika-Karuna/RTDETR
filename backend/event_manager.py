"""
Event Manager — handles event lifecycle, duplicate prevention,
cooldown management, and evidence capture.

Event states: DETECTED → MONITORING → HIGH_RISK → ALERT_SENT → ACKNOWLEDGED → RESOLVED
"""
import os
import time
import cv2
import numpy as np
from datetime import datetime
from typing import Optional

from database import insert_event, update_event, get_active_events, get_event, insert_risk_history

EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "data", "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)


class EventManager:
    """
    Manages the lifecycle of railway track alert events.
    Prevents duplicate alerts and maintains event state.
    """
    
    def __init__(self):
        self.active_events: dict[str, dict] = {}  # event_id -> event data (in-memory cache)
        self.alert_cooldowns: dict[str, float] = {}  # event_key -> last alert timestamp
        self.default_cooldown = 300  # 5 minutes
        self._event_counter = 0
        self._load_active_events()
    
    def _load_active_events(self):
        """Load active events from database on startup."""
        try:
            events = get_active_events()
            for evt in events:
                self.active_events[evt["event_id"]] = evt
            print(f"[EventManager] Loaded {len(self.active_events)} active events from DB")
        except Exception as e:
            print(f"[EventManager] Failed to load active events: {e}")
    
    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        self._event_counter += 1
        return f"EVT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{self._event_counter:04d}"
    
    def _make_event_key(self, object_types: list, zone: str) -> str:
        """
        Create a deduplication key from object types and zone.
        Same object types in the same zone = same event (prevents duplicates).
        """
        types_key = "-".join(sorted(set(t.lower() for t in object_types)))
        return f"{types_key}_{zone}"
    
    def process_risk_assessment(self, risk_result: dict, tracked_objects: list,
                                 train_info: Optional[dict] = None,
                                 location_info: Optional[dict] = None,
                                 frame: Optional[np.ndarray] = None) -> Optional[dict]:
        """
        Process a risk assessment result and manage event lifecycle.
        
        Returns event dict if an alert should be sent, None otherwise.
        """
        risk_level = risk_result["risk_level"]
        risk_score = risk_result["risk_score"]
        
        # Get object types in danger
        danger_objects = [o for o in tracked_objects if o["zone"] in ("DANGER", "WARNING")]
        if not danger_objects:
            # Check if active events should be resolved
            self._check_resolve_events(tracked_objects)
            return None
        
        object_types = list(set(o["object"] for o in danger_objects))
        primary_zone = "DANGER" if any(o["zone"] == "DANGER" for o in danger_objects) else "WARNING"
        event_key = self._make_event_key(object_types, primary_zone)
        
        # Check if there's already an active event for this situation
        existing_event = self._find_matching_event(event_key)
        
        if existing_event:
            # Update existing event
            return self._update_existing_event(
                existing_event, risk_result, danger_objects, train_info, location_info, frame
            )
        else:
            # Create new event
            return self._create_new_event(
                event_key, risk_result, danger_objects, train_info, location_info, frame
            )
    
    def _find_matching_event(self, event_key: str) -> Optional[dict]:
        """Find an active event matching this situation."""
        for eid, evt in self.active_events.items():
            if evt.get("_event_key") == event_key and evt["status"] not in ("RESOLVED",):
                return evt
        return None
    
    def _create_new_event(self, event_key: str, risk_result: dict,
                          danger_objects: list, train_info: Optional[dict],
                          location_info: Optional[dict],
                          frame: Optional[np.ndarray]) -> Optional[dict]:
        """Create a new event from a risk assessment."""
        event_id = self._generate_event_id()
        now = datetime.utcnow().isoformat()
        
        object_types = list(set(o["object"] for o in danger_objects))
        track_ids = [o["track_id"] for o in danger_objects]
        
        # Determine initial status based on risk level
        status = "DETECTED"
        if risk_result["risk_level"] in ("HIGH", "CRITICAL"):
            persistence = risk_result.get("max_persistence_seconds", 0)
            if persistence >= 5:  # Min persistence threshold
                status = "HIGH_RISK"
            else:
                status = "MONITORING"
        elif risk_result["risk_level"] == "MEDIUM":
            status = "MONITORING"
        
        # Capture evidence
        evidence_path = None
        if frame is not None and risk_result["risk_level"] in ("HIGH", "CRITICAL"):
            evidence_path = self._capture_evidence(event_id, frame, danger_objects, risk_result)
        
        event = {
            "event_id": event_id,
            "_event_key": event_key,
            "status": status,
            "risk_level": risk_result["risk_level"],
            "risk_score": risk_result["risk_score"],
            "object_type": ", ".join(object_types),
            "object_count": len(danger_objects),
            "confidence": max(o.get("confidence", 0) for o in danger_objects),
            "zone": danger_objects[0]["zone"] if danger_objects else "SAFE",
            "track_ids": track_ids,
            "reason": risk_result["reason"],
            "evidence_path": evidence_path,
            "first_detected_at": now,
            "metadata": {
                "risk_breakdown": risk_result.get("breakdown", {}),
                "recommended_action": risk_result.get("recommended_action", "")
            }
        }
        
        # Add location info
        if location_info:
            event["gps_latitude"] = location_info.get("latitude")
            event["gps_longitude"] = location_info.get("longitude")
            event["location_name"] = location_info.get("name", "")
            event["nearest_station"] = location_info.get("nearest_station", "")
            event["railway_zone"] = location_info.get("railway_zone", "")
            event["division"] = location_info.get("division", "")
        
        # Add train info
        if train_info:
            event["train_number"] = train_info.get("train_number", "")
            event["train_name"] = train_info.get("train_name", "")
            event["train_source"] = train_info.get("source_station", "")
            event["train_destination"] = train_info.get("destination_station", "")
            event["train_speed"] = train_info.get("speed_kmph")
            event["train_distance_km"] = train_info.get("distance_km")
            event["tti_seconds"] = train_info.get("tti_seconds")
        
        # Store in database and cache
        insert_event(event)
        self.active_events[event_id] = event
        
        # Record risk history
        insert_risk_history(event_id, risk_result["risk_score"], risk_result["risk_level"],
                           risk_result.get("breakdown"))
        
        # Determine if alert should be sent
        if self._should_send_alert(event) and not self._is_in_cooldown(event_key):
            event["status"] = "ALERT_SENT"
            event["alert_sent_at"] = now
            update_event(event_id, {"status": "ALERT_SENT", "alert_sent_at": now})
            self.alert_cooldowns[event_key] = time.time()
            return event
        
        return None
    
    def _update_existing_event(self, event: dict, risk_result: dict,
                                danger_objects: list, train_info: Optional[dict],
                                location_info: Optional[dict],
                                frame: Optional[np.ndarray]) -> Optional[dict]:
        """Update an existing event with new risk data."""
        event_id = event["event_id"]
        event_key = event.get("_event_key", "")
        
        # Update risk info
        updates = {
            "risk_level": risk_result["risk_level"],
            "risk_score": risk_result["risk_score"],
            "object_count": len(danger_objects),
            "reason": risk_result["reason"]
        }
        
        # Escalate status if risk increased
        old_level = event.get("risk_level", "LOW")
        new_level = risk_result["risk_level"]
        
        level_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        
        if level_order.get(new_level, 0) > level_order.get(old_level, 0):
            if new_level in ("HIGH", "CRITICAL"):
                updates["status"] = "HIGH_RISK"
                # Capture new evidence at higher risk
                if frame is not None:
                    evidence_path = self._capture_evidence(event_id, frame, danger_objects, risk_result)
                    if evidence_path:
                        updates["evidence_path"] = evidence_path
        
        # Update train info
        if train_info:
            updates["train_distance_km"] = train_info.get("distance_km")
            updates["train_speed"] = train_info.get("speed_kmph")
            updates["tti_seconds"] = train_info.get("tti_seconds")
        
        update_event(event_id, updates)
        event.update(updates)
        
        # Record risk history
        insert_risk_history(event_id, risk_result["risk_score"], risk_result["risk_level"],
                           risk_result.get("breakdown"))
        
        # Check if we should send a new alert (respecting cooldown)
        if self._should_send_alert(event) and not self._is_in_cooldown(event_key):
            if frame is not None and not event.get("evidence_path"):
                evidence_path = self._capture_evidence(event_id, frame, danger_objects, risk_result)
                if evidence_path:
                    event["evidence_path"] = evidence_path
                    update_event(event_id, {"evidence_path": evidence_path})
            event["status"] = "ALERT_SENT"
            event["alert_sent_at"] = datetime.utcnow().isoformat()
            update_event(event_id, {"status": "ALERT_SENT", "alert_sent_at": event["alert_sent_at"]})
            self.alert_cooldowns[event_key] = time.time()
            return event
        
        return None
    
    def _should_send_alert(self, event: dict) -> bool:
        """Check if this event warrants sending an alert."""
        risk_level = event.get("risk_level", "LOW")
        status = event.get("status", "DETECTED")
        
        # Only HIGH and CRITICAL trigger alerts
        if risk_level not in ("HIGH", "CRITICAL"):
            return False
        
        # Don't re-alert if acknowledged or resolved
        if status in ("ACKNOWLEDGED", "RESOLVED"):
            return False
        
        return True
    
    def _is_in_cooldown(self, event_key: str) -> bool:
        """Check if an event key is in alert cooldown period."""
        last_alert = self.alert_cooldowns.get(event_key)
        if last_alert is None:
            return False
        return (time.time() - last_alert) < self.default_cooldown
    
    def reset_session(self):
        """Reset cooldowns and in-memory session events for a new stream/video."""
        self.alert_cooldowns.clear()
        self.active_events.clear()
    
    def _check_resolve_events(self, tracked_objects: list):
        """Check if any active events should be resolved (objects left the track)."""
        now = datetime.utcnow().isoformat()
        
        danger_track_ids = set()
        for obj in tracked_objects:
            if obj["zone"] in ("DANGER", "WARNING"):
                danger_track_ids.add(obj["track_id"])
        
        to_resolve = []
        for eid, event in self.active_events.items():
            if event["status"] in ("RESOLVED", "ACKNOWLEDGED"):
                continue
            
            # Check if any of the event's tracked objects are still in danger
            event_track_ids = set(event.get("track_ids", []))
            if not event_track_ids.intersection(danger_track_ids):
                to_resolve.append(eid)
        
        for eid in to_resolve:
            update_event(eid, {"status": "RESOLVED", "resolved_at": now})
            self.active_events[eid]["status"] = "RESOLVED"
            self.active_events[eid]["resolved_at"] = now
    
    def _capture_evidence(self, event_id: str, frame: np.ndarray,
                          danger_objects: list, risk_result: dict) -> Optional[str]:
        """Capture and annotate an evidence frame."""
        try:
            evidence = frame.copy()
            
            for obj in danger_objects:
                bbox = obj.get("bbox", {})
                x, y, w, h = bbox.get("x", 0), bbox.get("y", 0), bbox.get("width", 0), bbox.get("height", 0)
                
                # Color based on zone
                color = (0, 0, 255) if obj["zone"] == "DANGER" else (0, 165, 255)
                cv2.rectangle(evidence, (x, y), (x + w, y + h), color, 3)
                
                # Label
                label = f"{obj['object'].upper()} #{obj['track_id']}"
                conf_label = f"Conf: {int(obj.get('confidence', 0) * 100)}%"
                risk_label = f"Risk: {risk_result['risk_level']}"
                
                cv2.putText(evidence, label, (x, y - 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)
                cv2.putText(evidence, conf_label, (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            
            # Add risk overlay at top
            cv2.rectangle(evidence, (0, 0), (evidence.shape[1], 40), (0, 0, 0), -1)
            risk_color = (0, 0, 255) if risk_result["risk_level"] == "CRITICAL" else (0, 165, 255)
            cv2.putText(evidence, f"RISK: {risk_result['risk_level']} ({risk_result['risk_score']}/100)",
                       (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, risk_color, 2, cv2.LINE_AA)
            
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            cv2.putText(evidence, timestamp, (evidence.shape[1] - 250, 28),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
            
            # Save
            filename = f"{event_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(EVIDENCE_DIR, filename)
            cv2.imwrite(filepath, evidence, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            return filepath
        except Exception as e:
            print(f"[EventManager] Evidence capture error: {e}")
            return None
    
    def resolve_event(self, event_id: str):
        """Manually resolve an event."""
        now = datetime.utcnow().isoformat()
        update_event(event_id, {"status": "RESOLVED", "resolved_at": now})
        if event_id in self.active_events:
            self.active_events[event_id]["status"] = "RESOLVED"
            self.active_events[event_id]["resolved_at"] = now
    
    def acknowledge_event(self, event_id: str):
        """Acknowledge an event (stops re-alerting)."""
        update_event(event_id, {"status": "ACKNOWLEDGED"})
        if event_id in self.active_events:
            self.active_events[event_id]["status"] = "ACKNOWLEDGED"
    
    def get_active_event_summary(self) -> list:
        """Get summary of all active events."""
        return [
            {
                "event_id": evt["event_id"],
                "status": evt["status"],
                "risk_level": evt.get("risk_level", "LOW"),
                "risk_score": evt.get("risk_score", 0),
                "object_type": evt.get("object_type", ""),
                "object_count": evt.get("object_count", 0),
                "zone": evt.get("zone", "SAFE"),
                "first_detected_at": evt.get("first_detected_at", ""),
                "reason": evt.get("reason", "")
            }
            for evt in self.active_events.values()
            if evt["status"] not in ("RESOLVED",)
        ]
    
    def set_cooldown(self, seconds: int):
        """Update the alert cooldown period."""
        self.default_cooldown = seconds


# Singleton
event_manager = EventManager()
