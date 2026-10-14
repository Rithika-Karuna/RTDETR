"""
Agent 2 — Tracking Agent
Wraps the TrackingService with zone-aware object tracking.
Produces structured JSON output for the risk agent.
"""
from datetime import datetime
from typing import Optional


class TrackingAgent:
    """
    Tracks detected objects across frames, assigns zones,
    calculates movement/velocity/persistence.
    """
    
    def __init__(self, tracking_service, zone_service):
        self.tracking_service = tracking_service
        self.zone_service = zone_service
    
    def process(self, detection_result: dict) -> dict:
        """
        Process detection agent output and produce tracking result.
        
        Args:
            detection_result: Output from DetectionAgent.process()
        
        Returns:
            Structured tracking data with zone classification for each object
        """
        detections = detection_result.get("detections", [])
        timestamp = detection_result.get("timestamp", datetime.utcnow().isoformat())
        
        # Zone classifier function
        def zone_classifier(cx, cy):
            return self.zone_service.classify_point(cx, cy)
        
        # Update tracking service
        tracked_objects = self.tracking_service.update(
            detections,
            zone_classifier=zone_classifier
        )
        
        # Categorize by zone
        danger_objects = [o for o in tracked_objects if o["zone"] == "DANGER"]
        warning_objects = [o for o in tracked_objects if o["zone"] in ("WARNING", "MEDIUM")]
        safe_objects = [o for o in tracked_objects if o["zone"] == "SAFE"]
        
        return {
            "agent": "tracking",
            "timestamp": timestamp,
            "frame_id": detection_result.get("frame_id", 0),
            "tracked_objects": tracked_objects,
            "total_tracked": len(tracked_objects),
            "danger_objects": danger_objects,
            "warning_objects": warning_objects,
            "medium_objects": warning_objects,
            "safe_objects": safe_objects,
            "danger_count": len(danger_objects),
            "warning_count": len(warning_objects),
            "medium_count": len(warning_objects),
            "safe_count": len(safe_objects),
            "has_track_obstruction": len(danger_objects) > 0,
            "has_warning": len(warning_objects) > 0,
            "has_medium": len(warning_objects) > 0,
            "summary": self.tracking_service.get_summary()
        }
