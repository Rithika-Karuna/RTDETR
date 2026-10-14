"""
Risk Analysis Engine — calculates risk scores using deterministic signals
from object detection, tracking, zone analysis, and train proximity.

Uses configurable weights and thresholds. LLM is NOT used for
physical measurements; only for contextual reasoning and explanations.
"""
import json
import os
from typing import Optional

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "risk_config.json")


class RiskConfig:
    """Loaded risk configuration with all thresholds."""
    
    def __init__(self):
        self.thresholds = {"low": [0, 30], "medium": [31, 60], "high": [61, 80], "critical": [81, 100]}
        self.weights = {
            "object_severity": 0.20,
            "track_occupancy": 0.25,
            "train_proximity": 0.20,
            "train_speed": 0.10,
            "collision_probability": 0.15,
            "persistence": 0.10
        }
        self.object_severity_scores = {
            "elephant": 95, "person": 85, "car": 90, "truck": 95, "bus": 95,
            "motorcycle": 70, "bicycle": 60, "cow": 75, "horse": 80,
            "dog": 50, "cat": 30, "bird": 10, "default": 60
        }
        self.zone_scores = {"DANGER": 100, "WARNING": 50, "MEDIUM": 50, "SAFE": 10}
        self.tti_thresholds = {"critical": 120, "high": 300, "medium": 600, "low": 1200}
        self.train_distance_thresholds = {"critical": 2, "high": 5, "medium": 10, "low": 20}
        self.alert_cooldown_seconds = 300
        self.min_persistence_seconds = 5
        self.min_confidence = 0.5
        self.min_alert_risk_level = "HIGH"
        self._load()
    
    def _load(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    data = json.load(f)
                self.thresholds = data.get("thresholds", self.thresholds)
                self.weights = data.get("weights", self.weights)
                self.object_severity_scores = data.get("object_severity_scores", self.object_severity_scores)
                self.zone_scores = data.get("zone_scores", self.zone_scores)
                self.tti_thresholds = data.get("tti_thresholds_seconds", self.tti_thresholds)
                self.train_distance_thresholds = data.get("train_distance_thresholds_km", self.train_distance_thresholds)
                self.alert_cooldown_seconds = data.get("alert_cooldown_seconds", 300)
                self.min_persistence_seconds = data.get("min_persistence_seconds", 5)
                self.min_confidence = data.get("min_confidence", 0.5)
                self.min_alert_risk_level = data.get("min_alert_risk_level", "HIGH")
                print("[RiskEngine] Config loaded.")
        except Exception as e:
            print(f"[RiskEngine] Config load error: {e}")
    
    def save(self):
        data = {
            "thresholds": self.thresholds,
            "weights": self.weights,
            "object_severity_scores": self.object_severity_scores,
            "zone_scores": self.zone_scores,
            "tti_thresholds_seconds": self.tti_thresholds,
            "train_distance_thresholds_km": self.train_distance_thresholds,
            "alert_cooldown_seconds": self.alert_cooldown_seconds,
            "min_persistence_seconds": self.min_persistence_seconds,
            "min_confidence": self.min_confidence,
            "min_alert_risk_level": self.min_alert_risk_level,
            "max_events_in_history": 10000
        }
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)


class RiskEngine:
    """
    Deterministic risk scoring engine.
    
    Risk Score = weighted sum of:
      - Object severity (type-based danger rating)
      - Track occupancy (zone intersection)
      - Train proximity (distance-based)
      - Train speed factor
      - Collision probability (TTI-based)
      - Persistence (duration on track)
    """
    
    def __init__(self):
        self.config = RiskConfig()
    
    def calculate_risk(self, tracked_objects: list, train_info: Optional[dict] = None) -> dict:
        """
        Calculate overall risk from tracked objects and train information.
        
        Args:
            tracked_objects: List of tracked object dicts from TrackingService
            train_info: Dict from TrainService.get_nearest_train()
        
        Returns:
            Risk assessment dict with score, level, breakdown, and reason
        """
        if not tracked_objects:
            return self._empty_result()
        
        # Filter to dangerous objects (in danger/warning/medium zone with sufficient confidence)
        danger_objects = [o for o in tracked_objects if o["zone"] in ("DANGER", "WARNING", "MEDIUM")]
        
        if not danger_objects:
            return self._empty_result()
        
        # Calculate individual component scores (0-100 each)
        severity_score = self._calc_object_severity(danger_objects)
        occupancy_score = self._calc_track_occupancy(danger_objects)
        proximity_score = self._calc_train_proximity(train_info)
        speed_score = self._calc_train_speed(train_info)
        collision_score = self._calc_collision_probability(train_info, danger_objects)
        persistence_score = self._calc_persistence(danger_objects)
        
        # Weighted aggregate
        w = self.config.weights
        raw_score = (
            severity_score * w["object_severity"] +
            occupancy_score * w["track_occupancy"] +
            proximity_score * w["train_proximity"] +
            speed_score * w["train_speed"] +
            collision_score * w["collision_probability"] +
            persistence_score * w["persistence"]
        )
        
        # Normalize to 0-100
        risk_score = min(100, max(0, raw_score))
        risk_level = self._score_to_level(risk_score)
        
        # Generate reason
        reason = self._generate_reason(danger_objects, train_info, risk_level, risk_score)
        
        # Determine recommended action
        action = self._recommend_action(risk_level)
        
        return {
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level,
            "reason": reason,
            "recommended_action": action,
            "breakdown": {
                "object_severity": round(severity_score, 1),
                "track_occupancy": round(occupancy_score, 1),
                "train_proximity": round(proximity_score, 1),
                "train_speed": round(speed_score, 1),
                "collision_probability": round(collision_score, 1),
                "persistence": round(persistence_score, 1)
            },
            "danger_objects_count": len([o for o in danger_objects if o["zone"] == "DANGER"]),
            "warning_objects_count": len([o for o in danger_objects if o["zone"] in ("WARNING", "MEDIUM")]),
            "primary_object": danger_objects[0]["object"] if danger_objects else None,
            "all_object_types": list(set(o["object"] for o in danger_objects)),
            "max_persistence_seconds": max((o["duration_on_track"] for o in danger_objects), default=0)
        }
    
    def _calc_object_severity(self, objects: list) -> float:
        """Score based on object type danger level. Multiple objects increase score."""
        if not objects:
            return 0.0
        
        scores = []
        for obj in objects:
            cls = obj["object"].lower()
            base = self.config.object_severity_scores.get(
                cls, self.config.object_severity_scores.get("default", 60)
            )
            # Weight by confidence
            score = base * min(obj.get("confidence", 0.5), 1.0)
            scores.append(score)
        
        # Max severity + bonus for multiple objects
        max_score = max(scores)
        multi_bonus = min(20, (len(scores) - 1) * 5)  # +5 per additional object, cap at 20
        return min(100, max_score + multi_bonus)
    
    def _calc_track_occupancy(self, objects: list) -> float:
        """Score based on zone occupation. DANGER zone = 100, WARNING = 50."""
        if not objects:
            return 0.0
        
        max_zone_score = 0
        for obj in objects:
            zone = obj["zone"]
            zone_score = self.config.zone_scores.get(zone, 0)
            
            # Stationary objects in danger zone are worse
            if zone == "DANGER" and obj.get("is_stationary", False):
                zone_score = 100
            elif zone == "DANGER":
                zone_score = 85  # Moving through danger zone
            
            max_zone_score = max(max_zone_score, zone_score)
        
        return max_zone_score
    
    def _calc_train_proximity(self, train_info: Optional[dict]) -> float:
        """Score based on how close the nearest train is."""
        if not train_info or train_info.get("distance_km") is None:
            return 30.0  # Moderate default when train info is unavailable
        
        if not train_info.get("is_approaching", False):
            return 10.0  # Train not approaching
        
        dist = train_info["distance_km"]
        thresholds = self.config.train_distance_thresholds
        
        if dist <= thresholds["critical"]:
            return 100.0
        elif dist <= thresholds["high"]:
            return 80.0
        elif dist <= thresholds["medium"]:
            return 60.0
        elif dist <= thresholds["low"]:
            return 40.0
        else:
            return 15.0
    
    def _calc_train_speed(self, train_info: Optional[dict]) -> float:
        """Score based on train speed. Faster = more dangerous."""
        if not train_info or train_info.get("speed_kmph") is None:
            return 30.0
        
        speed = train_info["speed_kmph"]
        if speed >= 100:
            return 100.0
        elif speed >= 80:
            return 85.0
        elif speed >= 60:
            return 70.0
        elif speed >= 40:
            return 50.0
        elif speed >= 20:
            return 30.0
        else:
            return 15.0
    
    def _calc_collision_probability(self, train_info: Optional[dict], objects: list) -> float:
        """Score based on Time-to-Impact estimation."""
        if not train_info or train_info.get("tti_seconds") is None:
            return 20.0
        
        if not train_info.get("is_approaching", False):
            return 5.0
        
        tti = train_info["tti_seconds"]
        thresholds = self.config.tti_thresholds
        
        # Check if any objects are stationary (higher collision probability)
        any_stationary = any(o.get("is_stationary", False) for o in objects)
        bonus = 10 if any_stationary else 0
        
        if tti <= thresholds["critical"]:
            return min(100, 100 + bonus)
        elif tti <= thresholds["high"]:
            return min(100, 80 + bonus)
        elif tti <= thresholds["medium"]:
            return min(100, 55 + bonus)
        elif tti <= thresholds["low"]:
            return min(100, 30 + bonus)
        else:
            return 10.0
    
    def _calc_persistence(self, objects: list) -> float:
        """Score based on how long objects have been on the track."""
        if not objects:
            return 0.0
        
        max_duration = max(o.get("duration_on_track", 0) for o in objects)
        
        if max_duration >= 60:
            return 100.0
        elif max_duration >= 30:
            return 80.0
        elif max_duration >= 15:
            return 60.0
        elif max_duration >= 5:
            return 40.0
        elif max_duration >= 2:
            return 20.0
        else:
            return 5.0
    
    def _score_to_level(self, score: float) -> str:
        """Convert numeric score to risk level string."""
        for level in ["critical", "high", "medium", "low"]:
            bounds = self.config.thresholds[level]
            if bounds[0] <= score <= bounds[1]:
                return level.upper()
        
        if score > 80:
            return "CRITICAL"
        return "LOW"
    
    def _generate_reason(self, objects: list, train_info: Optional[dict],
                         risk_level: str, score: float) -> str:
        """Generate a human-readable reason for the risk assessment."""
        obj_types = list(set(o["object"] for o in objects))
        obj_count = len(objects)
        danger_count = len([o for o in objects if o["zone"] == "DANGER"])
        
        obj_desc = ", ".join(obj_types)
        if obj_count > 1:
            obj_desc = f"{obj_count} objects ({obj_desc})"
        else:
            obj_desc = obj_types[0] if obj_types else "Unknown object"
        
        zone_desc = "blocking railway track" if danger_count > 0 else "near railway track"
        
        train_desc = ""
        if train_info and train_info.get("is_approaching"):
            dist = train_info.get("distance_km")
            if dist is not None:
                train_desc = f" while train {train_info.get('train_name', '')} is approaching ({dist:.1f} km away)"
        
        stationary = any(o.get("is_stationary") for o in objects)
        movement_desc = " (stationary)" if stationary else ""
        
        return f"{obj_desc}{movement_desc} {zone_desc}{train_desc}"
    
    def _recommend_action(self, risk_level: str) -> str:
        """Determine recommended action based on risk level."""
        actions = {
            "CRITICAL": "IMMEDIATE_ALERT",
            "HIGH": "EMERGENCY_ALERT",
            "MEDIUM": "CONTINUE_MONITORING",
            "LOW": "NO_ACTION"
        }
        return actions.get(risk_level, "NO_ACTION")
    
    def _empty_result(self) -> dict:
        return {
            "risk_score": 0,
            "risk_level": "LOW",
            "reason": "No objects detected in track zone",
            "recommended_action": "NO_ACTION",
            "breakdown": {
                "object_severity": 0, "track_occupancy": 0,
                "train_proximity": 0, "train_speed": 0,
                "collision_probability": 0, "persistence": 0
            },
            "danger_objects_count": 0,
            "warning_objects_count": 0,
            "primary_object": None,
            "all_object_types": [],
            "max_persistence_seconds": 0
        }
    
    def update_config(self, updates: dict):
        """Update risk configuration."""
        if "thresholds" in updates:
            self.config.thresholds = updates["thresholds"]
        if "weights" in updates:
            self.config.weights = updates["weights"]
        if "object_severity_scores" in updates:
            self.config.object_severity_scores = updates["object_severity_scores"]
        if "tti_thresholds_seconds" in updates:
            self.config.tti_thresholds = updates["tti_thresholds_seconds"]
        if "train_distance_thresholds_km" in updates:
            self.config.train_distance_thresholds = updates["train_distance_thresholds_km"]
        if "alert_cooldown_seconds" in updates:
            self.config.alert_cooldown_seconds = updates["alert_cooldown_seconds"]
        if "min_persistence_seconds" in updates:
            self.config.min_persistence_seconds = updates["min_persistence_seconds"]
        if "min_confidence" in updates:
            self.config.min_confidence = updates["min_confidence"]
        if "min_alert_risk_level" in updates:
            self.config.min_alert_risk_level = updates["min_alert_risk_level"]
        self.config.save()


# Singleton
risk_engine = RiskEngine()
