"""
Agent 5 — Alert Validation Agent (Alert Decision Agent)
Final gate before sending notifications.
Verifies all conditions are met before authorizing an alert.
"""
from datetime import datetime


class AlertValidationAgent:
    """
    Validates whether an alert should actually be sent.
    Checks all required conditions before authorizing notification dispatch.
    
    The system should NOT send an alert merely because an object is detected.
    """
    
    def __init__(self, risk_engine, event_manager):
        self.risk_engine = risk_engine
        self.event_manager = event_manager
    
    def process(self, risk_result: dict, tracking_result: dict,
                location_info: dict = None, frame=None) -> dict:
        """
        Validate whether an alert is warranted.
        
        Checks:
        1. Is the object actually in the railway danger zone?
        2. Is the object large/dangerous enough to threaten the train?
        3. Is a train approaching?
        4. Is the train sufficiently close?
        5. Is the obstruction persistent?
        6. Is the estimated risk HIGH or CRITICAL?
        7. Has the same event already been alerted?
        
        Returns:
            Validation result with approved/rejected status and event data.
        """
        timestamp = datetime.utcnow().isoformat()
        
        risk_level = risk_result.get("risk_level", "LOW")
        risk_score = risk_result.get("risk_score", 0)
        tracked_objects = risk_result.get("tracked_objects", [])
        train_info = risk_result.get("train_info")
        
        # === Validation Checks ===
        
        checks = {}
        
        # Check 1: Object in danger zone?
        danger_objects = [o for o in tracked_objects if o["zone"] == "DANGER"]
        warning_objects = [o for o in tracked_objects if o["zone"] == "WARNING"]
        checks["object_in_danger_zone"] = len(danger_objects) > 0
        checks["object_in_warning_zone"] = len(warning_objects) > 0
        checks["any_zone_threat"] = len(danger_objects) > 0 or len(warning_objects) > 0
        
        # Check 2: Object large/dangerous enough?
        min_conf = self.risk_engine.config.min_confidence
        high_conf_objects = [o for o in danger_objects + warning_objects 
                           if o.get("confidence", 0) >= min_conf]
        checks["sufficient_confidence"] = len(high_conf_objects) > 0
        
        # Check 3: Train approaching?
        train_approaching = False
        if train_info and train_info.get("is_approaching"):
            train_approaching = True
        checks["train_approaching"] = train_approaching
        
        # Check 4: Train sufficiently close?
        train_close = False
        if train_info and train_info.get("distance_km") is not None:
            dist = train_info["distance_km"]
            # Use the 'low' threshold as the maximum relevant distance
            max_dist = self.risk_engine.config.train_distance_thresholds.get("low", 20)
            train_close = dist <= max_dist
        checks["train_sufficiently_close"] = train_close
        
        # Check 5: Obstruction persistent?
        min_persistence = self.risk_engine.config.min_persistence_seconds
        max_persistence = max((o.get("duration_on_track", 0) for o in danger_objects), default=0)
        checks["obstruction_persistent"] = max_persistence >= min_persistence
        
        # Check 6: Risk HIGH or CRITICAL?
        min_level = self.risk_engine.config.min_alert_risk_level
        level_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        checks["risk_meets_threshold"] = (
            level_order.get(risk_level, 0) >= level_order.get(min_level, 2)
        )
        
        # === Decision Logic ===
        # Core conditions for alert authorization:
        # Must have object in danger zone OR (warning zone + approaching train)
        # Must meet risk threshold
        # Must have sufficient persistence
        
        core_condition = (
            checks["any_zone_threat"] and
            checks["sufficient_confidence"] and
            checks["risk_meets_threshold"]
        )
        
        # For HIGH/CRITICAL with danger zone objects — alert even without confirmed train
        # For WARNING zone objects — need confirmed approaching train
        if checks["object_in_danger_zone"]:
            spatial_condition = checks["obstruction_persistent"]
        else:
            # Warning zone only — need train confirmation
            spatial_condition = (
                checks["train_approaching"] and
                checks["train_sufficiently_close"] and
                checks["obstruction_persistent"]
            )
        
        approved = core_condition and spatial_condition
        
        # === Process through Event Manager ===
        event = None
        if approved or checks["any_zone_threat"]:
            # Even if not approved for alert, track the event
            event = self.event_manager.process_risk_assessment(
                risk_result=risk_result,
                tracked_objects=tracked_objects,
                train_info=train_info,
                location_info=location_info,
                frame=frame
            )
        else:
            # Check if existing events should be resolved
            self.event_manager._check_resolve_events(tracked_objects)
        
        # Event manager returns an event dict only when an alert should be sent
        alert_authorized = event is not None
        
        return {
            "agent": "alert_validation",
            "timestamp": timestamp,
            "approved": alert_authorized,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "validation_checks": checks,
            "all_checks_passed": all(checks.values()),
            "event": event,
            "event_type": "TRACK_OBSTRUCTION" if alert_authorized else None,
            "reason": risk_result.get("reason", ""),
            "active_events": self.event_manager.get_active_event_summary()
        }
