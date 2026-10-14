"""
Agent Pipeline Orchestrator — connects all agents in the correct order.

Pipeline flow:
  Camera Frame
    → Detection Agent (YOLO/RT-DETR + tracking IDs)
    → Tracking Agent (zone classification, movement, persistence)
    → Risk Analysis Agent (risk scoring)
    → Alert Validation Agent (final gate)
    → Location Intelligence Agent
    → Authority Agent (RAG retrieval)
    → Notification Agent (Email + WhatsApp)
"""
import time
import numpy as np
from typing import Optional

from model_service import detection_service
from tracking_service import tracking_service
from zone_service import zone_service
from train_service import train_service
from risk_engine import risk_engine
from event_manager import event_manager

from agents.detection_agent import DetectionAgent
from agents.tracking_agent import TrackingAgent
from agents.risk_agent import RiskAgent
from agents.location_agent import LocationAgent
from agents.alert_validation_agent import AlertValidationAgent
from agents.authority_agent import AuthorityAgent
from agents.notification_agent import NotificationAgent

from rag.authority_retriever import authority_retriever
from notifications.email_service import email_service
from notifications.whatsapp_service import whatsapp_service


class AgentPipeline:
    """
    Orchestrates the full agent pipeline from detection to notification.
    Each frame is processed through the chain of agents.
    """

    def __init__(self):
        # Initialize all agents
        self.detection_agent = DetectionAgent(detection_service)
        self.tracking_agent = TrackingAgent(tracking_service, zone_service)
        self.risk_agent = RiskAgent(risk_engine, train_service)
        self.location_agent = LocationAgent(train_service)
        self.alert_validation_agent = AlertValidationAgent(risk_engine, event_manager)
        self.authority_agent = AuthorityAgent(authority_retriever)
        self.notification_agent = NotificationAgent(email_service, whatsapp_service)

        # Pipeline state (last results for dashboard)
        self.last_detection = None
        self.last_tracking = None
        self.last_risk = None
        self.last_validation = None
        self.last_location = None
        self.last_authority = None
        self.last_notification = None
        self._frame_count = 0
        self._pipeline_enabled = True

        print("[AgentPipeline] All agents initialized.")

    def process_frame(self, frame: np.ndarray, model_type: str = "yolo",
                      conf_threshold: float = 0.25) -> dict:
        """
        Process a single frame through the full agent pipeline.

        Returns a combined result with detection, tracking, risk,
        and alert information for the frontend dashboard.
        """
        self._frame_count += 1
        t0 = time.time()

        # === Stage 1: Detection Agent ===
        detection_result = self.detection_agent.process(frame, model_type, conf_threshold)
        self.last_detection = detection_result
        annotated_frame = detection_result["annotated_frame"]

        # Enrich detections with zone information
        h_frame, w_frame = frame.shape[:2]
        for d in detection_result.get("detections", []):
            if "zone" not in d:
                bx = d.get("box", {})
                z_info = zone_service.classify_bbox(
                    int(bx.get("x", 0)), int(bx.get("y", 0)),
                    int(bx.get("width", 0)), int(bx.get("height", 0)),
                    frame_w=w_frame, frame_h=h_frame
                )
                d["zone"] = z_info["zone"]
                d["zone_label"] = z_info["zone_label"]

        # === Stage 2: Tracking Agent ===
        tracking_result = self.tracking_agent.process(detection_result)
        self.last_tracking = tracking_result

        # === Stage 3: Draw zone overlays ===
        annotated_frame = zone_service.draw_zones(annotated_frame)

        # Draw zone labels on tracked objects
        self._draw_tracking_overlays(annotated_frame, tracking_result)

        # === Stage 4: Risk Analysis Agent ===
        risk_result = self.risk_agent.process(tracking_result)
        self.last_risk = risk_result

        # === Stage 5: Location Intelligence ===
        location_info = self.location_agent.process(risk_result)
        self.last_location = location_info

        # === Stage 6: Alert Validation Agent ===
        validation_result = self.alert_validation_agent.process(
            risk_result=risk_result,
            tracking_result=tracking_result,
            location_info=location_info,
            frame=frame
        )
        self.last_validation = validation_result

        # === Stage 7: Authority Retrieval Agent (RAG) ===
        # Identifies designated in-charge authority for this location from Knowledge Base
        event = validation_result.get("event")
        authority_result = self.authority_agent.process(location_info, event)
        self.last_authority = authority_result

        # === Stage 8: Notification Agent (Dispatches asynchronously so video stream never stalls) ===
        if validation_result.get("approved"):
            import threading
            self.last_notification = {
                "agent": "notification",
                "dispatched": True,
                "status": "DISPATCHING",
                "event_id": (validation_result.get("event") or {}).get("event_id", ""),
            }
            def _dispatch_async(val_res, auth_res, loc_info, r_res):
                try:
                    self.last_notification = self.notification_agent.process(
                        validation_result=val_res,
                        authority_result=auth_res,
                        location_info=loc_info,
                        risk_result=r_res
                    )
                except Exception as exc:
                    print(f"[AgentPipeline] Async notification error: {exc}")

            threading.Thread(
                target=_dispatch_async,
                args=(validation_result, authority_result, location_info, risk_result),
                daemon=True
            ).start()

        # Draw risk overlay on frame
        self._draw_risk_overlay(annotated_frame, risk_result)

        pipeline_ms = round((time.time() - t0) * 1000, 1)

        # === Build combined response ===
        return {
            "annotated_frame": annotated_frame,
            "detections": detection_result.get("detections", []),
            "detection_count": detection_result.get("detection_count", 0),
            "tracking": {
                "tracked_objects": tracking_result.get("tracked_objects", []),
                "total_tracked": tracking_result.get("total_tracked", 0),
                "danger_count": tracking_result.get("danger_count", 0),
                "warning_count": tracking_result.get("warning_count", 0),
                "medium_count": tracking_result.get("medium_count", tracking_result.get("warning_count", 0)),
                "safe_count": tracking_result.get("safe_count", 0),
                "has_track_obstruction": tracking_result.get("has_track_obstruction", False),
            },
            "risk": {
                "risk_score": risk_result.get("risk_score", 0),
                "risk_level": risk_result.get("risk_level", "LOW"),
                "reason": risk_result.get("reason", ""),
                "recommended_action": risk_result.get("recommended_action", "NO_ACTION"),
                "breakdown": risk_result.get("breakdown", {}),
                "danger_objects_count": risk_result.get("danger_objects_count", 0),
                "warning_objects_count": risk_result.get("warning_objects_count", 0),
                "primary_object": risk_result.get("primary_object"),
                "all_object_types": risk_result.get("all_object_types", []),
            },
            "train": risk_result.get("train_info"),
            "all_trains": risk_result.get("all_trains", []),
            "location": {
                "latitude": location_info.get("latitude"),
                "longitude": location_info.get("longitude"),
                "name": location_info.get("location_name", ""),
                "nearest_station": location_info.get("nearest_station", ""),
                "railway_zone": location_info.get("railway_zone", ""),
                "division": location_info.get("division", ""),
                "district": location_info.get("district", ""),
            },
            "authority": {
                "rag_available": authority_result.get("rag_available", False),
                "primary_authority": authority_result.get("primary_authority"),
                "primary_email": authority_result.get("primary_email"),
                "primary_incharge": authority_result.get("primary_incharge"),
                "primary_role": authority_result.get("primary_role"),
                "authorities": authority_result.get("authorities", []),
                "authority_count": authority_result.get("authority_count", 0),
                "message": authority_result.get("message", "")
            },
            "alert": {
                "approved": validation_result.get("approved", False),
                "event_id": validation_result.get("event", {}).get("event_id") if validation_result.get("event") else None,
                "active_events": validation_result.get("active_events", []),
                "validation_checks": validation_result.get("validation_checks", {}),
            },
            "notification": self.last_notification,
            "pipeline_ms": pipeline_ms,
            "frame_id": self._frame_count,
        }

    def _draw_tracking_overlays(self, frame: np.ndarray, tracking_result: dict):
        """Draw zone labels and track IDs on tracked objects."""
        import cv2

        h_img, w_img = frame.shape[:2]
        scale = max(1.0, min(w_img, h_img) / 480.0)
        font_scale = max(0.45, 0.45 * scale)
        font_thick = max(1, int(1.2 * scale))

        for obj in tracking_result.get("tracked_objects", []):
            bbox = obj.get("bbox", {})
            x = int(bbox.get("x", 0))
            y = int(bbox.get("y", 0))
            w = int(bbox.get("width", 0))
            h = int(bbox.get("height", 0))
            zone = obj.get("zone", "SAFE")
            tid = obj.get("track_id", "?")
            dur = obj.get("duration_on_track", 0)

            # Zone-based color and prominent zone classification markings
            if zone == "DANGER":
                color = (0, 0, 255)  # Red BGR
                zone_label = f"DANGER ZONE ({dur:.0f}s)" if dur > 0 else "DANGER ZONE • TRACK"
                # Draw thick emergency box for track obstructions
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, max(3, int(3.5 * scale)))
            elif zone in ("WARNING", "MEDIUM"):
                color = (0, 165, 255)  # Amber/Orange BGR
                zone_label = "MEDIUM ZONE"
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, max(2, int(2.5 * scale)))
            else:
                color = (70, 220, 80)  # Green BGR
                zone_label = "SAFE ZONE"
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, max(2, int(2 * scale)))

            # Draw zone badge below bounding box
            badge_y = y + h + int(18 * scale)
            (lw, lh), _ = cv2.getTextSize(zone_label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thick)
            cv2.rectangle(frame, (x, badge_y - lh - 4), (x + lw + 8, badge_y + 4), color, cv2.FILLED)
            text_color = (255, 255, 255) if zone == "DANGER" else (0, 0, 0)
            cv2.putText(frame, zone_label, (x + 4, badge_y - 2),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, font_thick, cv2.LINE_AA)

            # Movement indicator
            movement = obj.get("movement", "stationary")
            if movement != "stationary":
                cv2.putText(frame, movement, (x, badge_y + int(16 * scale)),
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.85, (220, 220, 220), 1, cv2.LINE_AA)

    def _draw_risk_overlay(self, frame: np.ndarray, risk_result: dict):
        """Draw risk level indicator on the frame."""
        import cv2

        risk_level = risk_result.get("risk_level", "LOW")
        risk_score = risk_result.get("risk_score", 0)

        if risk_level == "LOW":
            return  # Don't clutter the frame for low risk

        # Color based on risk
        colors = {
            "MEDIUM": (0, 200, 255),
            "HIGH": (0, 100, 255),
            "CRITICAL": (0, 0, 255),
        }
        color = colors.get(risk_level, (200, 200, 200))

        h, w = frame.shape[:2]

        # Risk badge in top-right
        badge_text = f"RISK: {risk_level} ({risk_score:.0f})"
        font = cv2.FONT_HERSHEY_SIMPLEX
        (tw, th), _ = cv2.getTextSize(badge_text, font, 0.6, 2)

        bx = w - tw - 20
        by = 10
        cv2.rectangle(frame, (bx - 5, by), (w - 5, by + th + 10), (0, 0, 0), -1)
        cv2.rectangle(frame, (bx - 5, by), (w - 5, by + th + 10), color, 2)
        cv2.putText(frame, badge_text, (bx, by + th + 3),
                    font, 0.6, color, 2, cv2.LINE_AA)

        # Pulsing border for CRITICAL
        if risk_level == "CRITICAL":
            cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 0, 255), 4)

    def get_dashboard_state(self) -> dict:
        """Get the current state of all agents for the dashboard."""
        return {
            "detection": {
                "count": self.last_detection.get("detection_count", 0) if self.last_detection else 0,
            },
            "tracking": self.last_tracking if self.last_tracking else {},
            "risk": self.last_risk if self.last_risk else {},
            "location": self.last_location if self.last_location else {},
            "authority": self.last_authority if self.last_authority else {},
            "alert": self.last_validation if self.last_validation else {},
            "notification": self.last_notification if self.last_notification else {},
            "pipeline_enabled": self._pipeline_enabled,
            "frame_count": self._frame_count,
        }

    def reset(self):
        """Reset all agent states and session cooldowns for a fresh stream."""
        tracking_service.reset()
        if hasattr(self.detection_agent, 'reset_tracker'):
            self.detection_agent.reset_tracker()
        if hasattr(event_manager, 'reset_session'):
            event_manager.reset_session()
        self.last_detection = None
        self.last_tracking = None
        self.last_risk = None
        self.last_validation = None
        self.last_location = None
        self.last_authority = None
        self.last_notification = None
        self._frame_count = 0


# Singleton
agent_pipeline = AgentPipeline()
