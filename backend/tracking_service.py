"""
Multi-Object Tracking Service using ByteTrack via Ultralytics.
Maintains object identity across frames, calculates movement, velocity,
zone occupancy duration, and direction of travel.
"""
import time
import math
from collections import defaultdict
from typing import Optional


class TrackedObject:
    """Represents a single tracked object with full history."""
    
    def __init__(self, track_id: int, class_name: str, confidence: float,
                 bbox: dict, zone: str = "SAFE", timestamp: float = None):
        self.track_id = track_id
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox  # {x, y, width, height}
        self.zone = zone
        
        now = timestamp or time.time()
        self.first_seen = now
        self.last_seen = now
        self.positions = [(self._center(bbox), now)]  # [(cx, cy), timestamp]
        self.zone_history = [(zone, now)]
        self.danger_zone_entry_time: Optional[float] = now if zone == "DANGER" else None
        self.warning_zone_entry_time: Optional[float] = now if zone == "WARNING" else None
        
        # Movement state
        self.velocity = (0.0, 0.0)  # pixels per second
        self.speed = 0.0  # pixels per second magnitude
        self.direction = "stationary"  # stationary, moving_left, moving_right, moving_up, moving_down, crossing
        self.is_stationary = True
        self.movement_label = "stationary"
    
    @staticmethod
    def _center(bbox: dict) -> tuple:
        return (bbox["x"] + bbox["width"] / 2, bbox["y"] + bbox["height"] / 2)
    
    def update(self, confidence: float, bbox: dict, zone: str, timestamp: float = None):
        """Update tracked object with new frame data."""
        now = timestamp or time.time()
        self.confidence = confidence
        self.bbox = bbox
        self.last_seen = now
        
        cx, cy = self._center(bbox)
        self.positions.append(((cx, cy), now))
        
        # Keep last 60 positions for smooth velocity calculation
        if len(self.positions) > 60:
            self.positions = self.positions[-60:]
        
        # Update zone tracking
        if zone != self.zone:
            self.zone_history.append((zone, now))
            if zone == "DANGER" and self.danger_zone_entry_time is None:
                self.danger_zone_entry_time = now
            elif zone != "DANGER":
                self.danger_zone_entry_time = None
            
            if zone == "WARNING" and self.warning_zone_entry_time is None:
                self.warning_zone_entry_time = now
            elif zone != "WARNING" and zone != "DANGER":
                self.warning_zone_entry_time = None
        
        self.zone = zone
        self._calculate_movement()
    
    def _calculate_movement(self):
        """Calculate velocity, speed, and direction from position history."""
        if len(self.positions) < 2:
            self.velocity = (0.0, 0.0)
            self.speed = 0.0
            self.direction = "stationary"
            self.is_stationary = True
            self.movement_label = "stationary"
            return
        
        # Use last N positions for smoothed velocity
        n = min(10, len(self.positions))
        recent = self.positions[-n:]
        
        (x1, y1), t1 = recent[0]
        (x2, y2), t2 = recent[-1]
        dt = t2 - t1
        
        if dt < 0.01:
            return
        
        vx = (x2 - x1) / dt
        vy = (y2 - y1) / dt
        self.velocity = (vx, vy)
        self.speed = math.sqrt(vx**2 + vy**2)
        
        # Stationary threshold: less than 3 pixels/second
        if self.speed < 3.0:
            self.is_stationary = True
            self.direction = "stationary"
            self.movement_label = "stationary"
        else:
            self.is_stationary = False
            # Determine primary direction
            if abs(vx) > abs(vy):
                self.direction = "moving_right" if vx > 0 else "moving_left"
                self.movement_label = "crossing" if abs(vx) > 5 else "drifting"
            else:
                self.direction = "moving_down" if vy > 0 else "moving_up"
                self.movement_label = "approaching" if vy > 0 else "receding"
    
    @property
    def duration_on_track(self) -> float:
        """Seconds the object has been in danger zone."""
        if self.danger_zone_entry_time is None:
            return 0.0
        return time.time() - self.danger_zone_entry_time
    
    @property
    def duration_in_warning(self) -> float:
        """Seconds the object has been in warning zone."""
        if self.warning_zone_entry_time is None:
            return 0.0
        return time.time() - self.warning_zone_entry_time
    
    @property
    def total_tracked_duration(self) -> float:
        """Total seconds this object has been tracked."""
        return time.time() - self.first_seen
    
    @property
    def is_moving_toward_track(self) -> bool:
        """Whether the object appears to be moving toward the danger zone."""
        if self.zone == "DANGER":
            return False  # Already on track
        # If in warning or medium zone and moving down (toward typical track position), it's approaching
        return self.zone in ("WARNING", "MEDIUM") and self.direction == "moving_down"
    
    def to_dict(self) -> dict:
        """Serialize to structured JSON for agent communication."""
        return {
            "track_id": self.track_id,
            "object": self.class_name,
            "class_name": self.class_name,
            "confidence": round(self.confidence, 2),
            "bbox": self.bbox,
            "box": self.bbox,
            "zone": self.zone,
            "duration_on_track": round(self.duration_on_track, 1),
            "duration_in_warning": round(self.duration_in_warning, 1),
            "total_tracked_seconds": round(self.total_tracked_duration, 1),
            "movement": self.movement_label,
            "direction": self.direction,
            "speed_px_s": round(self.speed, 1),
            "is_stationary": self.is_stationary,
            "is_moving_toward_track": self.is_moving_toward_track,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen
        }


class TrackingService:
    """
    Multi-object tracking service.
    Wraps ByteTrack via ultralytics model.track() and maintains
    a rich state for each tracked object (zone, velocity, persistence).
    """
    
    def __init__(self):
        self.tracked_objects: dict[int, TrackedObject] = {}
        self.lost_timeout = 3.0  # seconds before removing lost tracks
        self._frame_count = 0
        self._next_synthetic_id = 1

    def update(self, detections_with_ids: list, zone_classifier=None, timestamp: float = None) -> list:
        """
        Update tracking state with new detections that already have track IDs
        or assign synthetic track IDs for RT-DETR / untracked detections.
        
        Args:
            detections_with_ids: List of dicts with keys:
                {class_name, confidence, box: {x,y,width,height}, track_id}
            zone_classifier: Optional callable(cx, cy) -> "SAFE"|"WARNING"|"DANGER"
            timestamp: Optional override timestamp
        
        Returns:
            List of TrackedObject.to_dict() for all active tracks
        """
        now = timestamp or time.time()
        self._frame_count += 1
        seen_ids = set()

        # Phase 1: Process detections that already have a valid track_id
        unassigned_dets = []
        for det in detections_with_ids:
            tid = det.get("track_id")
            if tid is not None:
                try:
                    tid = int(tid)
                    det["track_id"] = tid
                    seen_ids.add(tid)
                    self._next_synthetic_id = max(self._next_synthetic_id, tid + 1)
                    bbox = det["box"]
                    cls = det["class_name"]
                    conf = det["confidence"]
                    cx = bbox["x"] + bbox["width"] / 2
                    cy = bbox["y"] + bbox["height"] / 2
                    zone = zone_classifier(cx, cy) if zone_classifier else "SAFE"
                    if tid in self.tracked_objects:
                        self.tracked_objects[tid].update(conf, bbox, zone, now)
                    else:
                        self.tracked_objects[tid] = TrackedObject(
                            track_id=tid, class_name=cls, confidence=conf,
                            bbox=bbox, zone=zone, timestamp=now
                        )
                except (ValueError, TypeError):
                    unassigned_dets.append(det)
            else:
                unassigned_dets.append(det)

        # Phase 2: For detections without track_id (e.g. RT-DETR), match with active tracks or allocate new ID
        for det in unassigned_dets:
            bbox = det["box"]
            cls = det["class_name"]
            conf = det["confidence"]
            cx = bbox["x"] + bbox["width"] / 2
            cy = bbox["y"] + bbox["height"] / 2
            zone = zone_classifier(cx, cy) if zone_classifier else "SAFE"

            # Try to match with an existing un-updated track of the same class
            matched_tid = None
            min_dist = float('inf')
            max_match_radius = max(80.0, float(bbox.get("width", 50)), float(bbox.get("height", 50)))

            for tid, obj in self.tracked_objects.items():
                if tid in seen_ids or obj.class_name != cls:
                    continue
                last_cx, last_cy = obj.positions[-1][0]
                dist = math.hypot(cx - last_cx, cy - last_cy)
                if dist < max_match_radius and dist < min_dist:
                    min_dist = dist
                    matched_tid = tid

            if matched_tid is not None:
                tid = matched_tid
                self.tracked_objects[tid].update(conf, bbox, zone, now)
            else:
                tid = self._next_synthetic_id
                self._next_synthetic_id += 1
                self.tracked_objects[tid] = TrackedObject(
                    track_id=tid, class_name=cls, confidence=conf,
                    bbox=bbox, zone=zone, timestamp=now
                )

            det["track_id"] = tid
            seen_ids.add(tid)

        # Remove stale tracks
        stale = [
            tid for tid, obj in self.tracked_objects.items()
            if tid not in seen_ids and (now - obj.last_seen) > self.lost_timeout
        ]
        for tid in stale:
            del self.tracked_objects[tid]

        # Return all active tracks
        return [obj.to_dict() for obj in self.tracked_objects.values()]
    
    def get_danger_zone_objects(self) -> list:
        """Get all tracked objects currently in the DANGER zone."""
        return [
            obj.to_dict() for obj in self.tracked_objects.values()
            if obj.zone == "DANGER"
        ]
    
    def get_warning_zone_objects(self) -> list:
        """Get all tracked objects currently in the WARNING zone."""
        return [
            obj.to_dict() for obj in self.tracked_objects.values()
            if obj.zone == "WARNING"
        ]
    
    def get_objects_by_class(self, class_name: str) -> list:
        """Get all tracked objects of a specific class."""
        return [
            obj.to_dict() for obj in self.tracked_objects.values()
            if obj.class_name.lower() == class_name.lower()
        ]
    
    def get_summary(self) -> dict:
        """Get a summary of current tracking state."""
        zones = defaultdict(int)
        classes = defaultdict(int)
        for obj in self.tracked_objects.values():
            zones[obj.zone] += 1
            classes[obj.class_name] += 1
        
        return {
            "total_tracked": len(self.tracked_objects),
            "zone_counts": dict(zones),
            "class_counts": dict(classes),
            "danger_objects": self.get_danger_zone_objects(),
            "warning_objects": self.get_warning_zone_objects(),
            "frame_count": self._frame_count
        }
    
    def reset(self):
        """Reset all tracking state."""
        self.tracked_objects.clear()
        self._frame_count = 0


# Singleton instance
tracking_service = TrackingService()
