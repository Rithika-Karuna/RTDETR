"""
Railway Track Zone Service — ROI polygon management and zone classification.
Determines whether objects are in SAFE, MEDIUM, or DANGER zones.
"""
import json
import os
import cv2
import numpy as np
from typing import Optional

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "zone_config.json")


class ZoneService:
    """Manages railway track ROI polygons and classifies object positions into SAFE, MEDIUM, or DANGER zones."""
    
    def __init__(self):
        self.danger_polygon: list = []
        self.warning_polygon: list = []  # Medium zone
        self.safe_polygon: list = []     # Safe zone boundary
        self.track_center_line: list = []
        self.frame_width: int = 640
        self.frame_height: int = 480
        self.zone_enabled: bool = True
        self.danger_color = (0, 0, 255)       # Red in BGR
        self.warning_color = (0, 165, 255)    # Orange/Amber in BGR (Medium zone)
        self.safe_color = (70, 220, 80)       # Green in BGR (Safe zone)
        self.danger_opacity = 0.28
        self.warning_opacity = 0.20
        self.safe_opacity = 0.12
        self._load_config()
    
    def _load_config(self):
        """Load zone configuration from file."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    config = json.load(f)
                
                self.danger_polygon = config.get("danger_zone", {}).get("polygon", [])
                self.warning_polygon = (config.get("warning_zone", {}).get("polygon", []) or
                                       config.get("medium_zone", {}).get("polygon", []))
                self.safe_polygon = config.get("safe_zone", {}).get("polygon", [])
                self.track_center_line = config.get("track_center_line", [])
                self.frame_width = config.get("frame_width", 640)
                self.frame_height = config.get("frame_height", 480)
                self.zone_enabled = config.get("zone_enabled", True)
                
                dc = config.get("danger_zone", {}).get("color", [0, 0, 255])
                self.danger_color = tuple(dc)
                wc = (config.get("warning_zone", {}).get("color", [0, 165, 255]) or
                      config.get("medium_zone", {}).get("color", [0, 165, 255]))
                self.warning_color = tuple(wc)
                sc = config.get("safe_zone", {}).get("color", [0, 220, 80])
                self.safe_color = tuple(sc)
                
                self.danger_opacity = config.get("danger_zone", {}).get("opacity", 0.28)
                self.warning_opacity = config.get("warning_zone", {}).get("opacity", 0.20)
                self.safe_opacity = config.get("safe_zone", {}).get("opacity", 0.12)
                
                # Default safe polygon around warning zone if empty
                if not self.safe_polygon and self.warning_polygon and len(self.warning_polygon) >= 3:
                    self._generate_default_safe_polygon()
                
                print(f"[ZoneService] Loaded zones: safe={len(self.safe_polygon)} pts, medium={len(self.warning_polygon)} pts, danger={len(self.danger_polygon)} pts")
        except Exception as e:
            print(f"[ZoneService] Error loading config: {e}")
            if not self.safe_polygon and self.warning_polygon:
                self._generate_default_safe_polygon()

    def _generate_default_safe_polygon(self):
        """Generate safe zone perimeter enclosing track and buffer."""
        fw = self.frame_width or 640
        fh = self.frame_height or 480
        self.safe_polygon = [
            [int(fw * 0.10), int(fh * 0.45)],
            [int(fw * 0.90), int(fh * 0.45)],
            [int(fw * 0.98), int(fh * 0.96)],
            [int(fw * 0.02), int(fh * 0.96)]
        ]

    def save_config(self):
        """Save current zone configuration to file."""
        config = {
            "safe_zone": {
                "polygon": self.safe_polygon,
                "color": list(self.safe_color),
                "opacity": self.safe_opacity,
                "label": "SAFE ZONE"
            },
            "danger_zone": {
                "polygon": self.danger_polygon,
                "color": list(self.danger_color),
                "opacity": self.danger_opacity,
                "label": "DANGER ZONE"
            },
            "warning_zone": {
                "polygon": self.warning_polygon,
                "color": list(self.warning_color),
                "opacity": self.warning_opacity,
                "label": "MEDIUM ZONE"
            },
            "medium_zone": {
                "polygon": self.warning_polygon,
                "color": list(self.warning_color),
                "opacity": self.warning_opacity,
                "label": "MEDIUM ZONE"
            },
            "track_center_line": self.track_center_line,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "zone_enabled": self.zone_enabled
        }
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
    
    def update_zones(self, danger_polygon: list = None, warning_polygon: list = None,
                     safe_polygon: list = None, track_center_line: list = None,
                     frame_width: int = None, frame_height: int = None, zone_enabled: bool = None):
        """Update zone configuration."""
        if danger_polygon is not None:
            self.danger_polygon = danger_polygon
        if warning_polygon is not None:
            self.warning_polygon = warning_polygon
        if safe_polygon is not None:
            self.safe_polygon = safe_polygon
        if track_center_line is not None:
            self.track_center_line = track_center_line
        if frame_width is not None:
            self.frame_width = frame_width
        if frame_height is not None:
            self.frame_height = frame_height
        if zone_enabled is not None:
            self.zone_enabled = zone_enabled
        self.save_config()
    
    def classify_point(self, cx: float, cy: float, frame_w: int = None, frame_h: int = None) -> str:
        """
        Classify a point (object center) into a zone.
        Returns: "DANGER", "MEDIUM", or "SAFE"
        """
        if not self.zone_enabled:
            return "SAFE"

        # Apply scaling if frame resolution differs from config
        scale_x = (frame_w / self.frame_width) if (frame_w and self.frame_width) else 1.0
        scale_y = (frame_h / self.frame_height) if (frame_h and self.frame_height) else 1.0
        norm_cx = cx / scale_x
        norm_cy = cy / scale_y
        
        # Check danger zone first (innermost - track)
        if self.danger_polygon and len(self.danger_polygon) >= 3:
            poly = np.array(self.danger_polygon, dtype=np.float32)
            result = cv2.pointPolygonTest(poly, (float(norm_cx), float(norm_cy)), False)
            if result >= 0:
                return "DANGER"
        
        # Check warning / medium zone (middle buffer)
        if self.warning_polygon and len(self.warning_polygon) >= 3:
            poly = np.array(self.warning_polygon, dtype=np.float32)
            result = cv2.pointPolygonTest(poly, (float(norm_cx), float(norm_cy)), False)
            if result >= 0:
                return "MEDIUM"
        
        return "SAFE"
    
    def classify_bbox(self, x: int, y: int, w: int, h: int, frame_w: int = None, frame_h: int = None) -> dict:
        """
        Classify a bounding box. Checks center and all corners.
        Returns zone info: "SAFE", "MEDIUM", or "DANGER", with labels and overlap details.
        """
        cx, cy = x + w / 2, y + h / 2
        center_zone = self.classify_point(cx, cy, frame_w, frame_h)
        
        # Check corners for partial overlap
        corners = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
        corner_zones = [self.classify_point(px, py, frame_w, frame_h) for px, py in corners]
        
        any_danger = "DANGER" in corner_zones or center_zone == "DANGER"
        any_medium = any(z in ("MEDIUM", "WARNING") for z in corner_zones) or center_zone in ("MEDIUM", "WARNING")
        
        if any_danger:
            zone = "DANGER"
            zone_label = "DANGER ZONE"
            zone_color = (0, 0, 255)
        elif any_medium:
            zone = "MEDIUM"
            zone_label = "MEDIUM ZONE"
            zone_color = (0, 165, 255)
        else:
            zone = "SAFE"
            zone_label = "SAFE ZONE"
            zone_color = (70, 220, 80)

        # Calculate distance to track center
        distance_to_center = self._distance_to_track_center(cx, cy, frame_w, frame_h)
        overlap_ratio = self._estimate_zone_overlap(x, y, w, h, frame_w, frame_h)
        
        return {
            "zone": zone,
            "zone_label": zone_label,
            "zone_color": zone_color,
            "center_zone": center_zone,
            "any_corner_in_danger": any_danger,
            "any_corner_in_warning": any_medium,
            "distance_to_track_center": round(distance_to_center, 1),
            "danger_overlap_ratio": round(overlap_ratio, 2)
        }
    
    def _distance_to_track_center(self, cx: float, cy: float, frame_w: int = None, frame_h: int = None) -> float:
        """Calculate pixel distance from point to track center line."""
        scale_x = (frame_w / self.frame_width) if (frame_w and self.frame_width) else 1.0
        scale_y = (frame_h / self.frame_height) if (frame_h and self.frame_height) else 1.0
        norm_cx = cx / scale_x
        norm_cy = cy / scale_y

        if len(self.track_center_line) < 2:
            if self.danger_polygon:
                poly = np.array(self.danger_polygon)
                track_cx = poly[:, 0].mean()
                track_cy = poly[:, 1].mean()
                return float(np.sqrt((norm_cx - track_cx)**2 + (norm_cy - track_cy)**2))
            return 999.0
        
        min_dist = float('inf')
        for i in range(len(self.track_center_line) - 1):
            p1 = np.array(self.track_center_line[i], dtype=float)
            p2 = np.array(self.track_center_line[i + 1], dtype=float)
            pt = np.array([norm_cx, norm_cy], dtype=float)
            
            line_vec = p2 - p1
            line_len = np.linalg.norm(line_vec)
            if line_len < 1e-6:
                continue
            
            t = max(0, min(1, np.dot(pt - p1, line_vec) / (line_len**2)))
            projection = p1 + t * line_vec
            dist = np.linalg.norm(pt - projection)
            min_dist = min(min_dist, dist)
        
        return min_dist
    
    def _estimate_zone_overlap(self, x: int, y: int, w: int, h: int, frame_w: int = None, frame_h: int = None) -> float:
        """Estimate what fraction of the bounding box overlaps with the danger zone."""
        if not self.danger_polygon or len(self.danger_polygon) < 3:
            return 0.0
        
        sample_count = 0
        inside_count = 0
        step = max(1, min(w, h) // 5)
        
        for px in range(x, x + w, step):
            for py in range(y, y + h, step):
                sample_count += 1
                if self.classify_point(px, py, frame_w, frame_h) == "DANGER":
                    inside_count += 1
        
        return inside_count / max(sample_count, 1)
    
    def draw_zones(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw zone overlays on a frame:
        - SAFE ZONE: Green tinted overlay and boundary
        - MEDIUM ZONE: Orange tinted overlay and buffer boundary
        - DANGER ZONE: Red tinted overlay and track boundary
        - Track center line
        """
        if not self.zone_enabled:
            return frame
        
        h_frame, w_frame = frame.shape[:2]
        scale_x = w_frame / self.frame_width if self.frame_width else 1.0
        scale_y = h_frame / self.frame_height if self.frame_height else 1.0
        ui_scale = max(1.0, min(w_frame, h_frame) / 480.0)

        overlay = frame.copy()
        
        def scale_pts(polygon):
            return np.array([[int(p[0] * scale_x), int(p[1] * scale_y)] for p in polygon], dtype=np.int32)
        
        # 1. Draw Safe Zone overlay (outermost)
        if self.safe_polygon and len(self.safe_polygon) >= 3:
            pts_safe = scale_pts(self.safe_polygon)
            cv2.fillPoly(overlay, [pts_safe], self.safe_color)
            cv2.polylines(overlay, [pts_safe], True, self.safe_color, max(2, int(2 * ui_scale)))

        # 2. Draw Medium Zone (warning buffer)
        if self.warning_polygon and len(self.warning_polygon) >= 3:
            pts_med = scale_pts(self.warning_polygon)
            cv2.fillPoly(overlay, [pts_med], self.warning_color)
            cv2.polylines(overlay, [pts_med], True, self.warning_color, max(2, int(2.5 * ui_scale)))
        
        # 3. Draw Danger Zone (innermost on track)
        if self.danger_polygon and len(self.danger_polygon) >= 3:
            pts_dan = scale_pts(self.danger_polygon)
            cv2.fillPoly(overlay, [pts_dan], self.danger_color)
            cv2.polylines(overlay, [pts_dan], True, self.danger_color, max(2, int(3 * ui_scale)))
        
        # Blend overlays with smooth transparency
        result = cv2.addWeighted(overlay, 0.22, frame, 0.78, 0)
        
        # Draw crisp zone label badges with dark pill backgrounds for readability
        def draw_zone_tag(text: str, pt, bg_color, text_color=(0, 0, 0)):
            font = cv2.FONT_HERSHEY_DUPLEX
            font_scale = 0.5 * ui_scale
            font_thick = max(1, int(1.2 * ui_scale))
            (tw, th), _ = cv2.getTextSize(text, font, font_scale, font_thick)
            px, py = pt[0] - tw // 2, pt[1]
            pad = int(4 * ui_scale)
            cv2.rectangle(result, (px - pad, py - th - pad), (px + tw + pad, py + pad), bg_color, cv2.FILLED)
            cv2.putText(result, text, (px, py), font, font_scale, text_color, font_thick, cv2.LINE_AA)

        # Safe Zone label
        if self.safe_polygon and len(self.safe_polygon) >= 3:
            pts = scale_pts(self.safe_polygon)
            top_pt = pts[0]
            draw_zone_tag("SAFE ZONE", (top_pt[0] + 60, top_pt[1] + 24), self.safe_color, (0, 0, 0))

        # Medium Zone label
        if self.warning_polygon and len(self.warning_polygon) >= 3:
            pts = scale_pts(self.warning_polygon)
            center = pts.mean(axis=0).astype(int)
            draw_zone_tag("MEDIUM ZONE", (center[0], center[1] - int(28 * ui_scale)), self.warning_color, (0, 0, 0))

        # Danger Zone label
        if self.danger_polygon and len(self.danger_polygon) >= 3:
            pts = scale_pts(self.danger_polygon)
            center = pts.mean(axis=0).astype(int)
            draw_zone_tag("DANGER ZONE", (center[0], center[1]), self.danger_color, (255, 255, 255))
        
        # Draw track center line
        if len(self.track_center_line) >= 2:
            for i in range(len(self.track_center_line) - 1):
                p1 = (int(self.track_center_line[i][0] * scale_x), int(self.track_center_line[i][1] * scale_y))
                p2 = (int(self.track_center_line[i + 1][0] * scale_x), int(self.track_center_line[i + 1][1] * scale_y))
                cv2.line(result, p1, p2, (255, 255, 255), max(1, int(1.5 * ui_scale)), cv2.LINE_AA)
        
        return result
    
    def get_config(self) -> dict:
        """Return current zone configuration with full metadata."""
        return {
            "safe_zone": {
                "polygon": self.safe_polygon,
                "color": list(self.safe_color),
                "opacity": self.safe_opacity,
                "label": "SAFE ZONE"
            },
            "warning_zone": {
                "polygon": self.warning_polygon,
                "color": list(self.warning_color),
                "opacity": self.warning_opacity,
                "label": "MEDIUM ZONE"
            },
            "medium_zone": {
                "polygon": self.warning_polygon,
                "color": list(self.warning_color),
                "opacity": self.warning_opacity,
                "label": "MEDIUM ZONE"
            },
            "danger_zone": {
                "polygon": self.danger_polygon,
                "color": list(self.danger_color),
                "opacity": self.danger_opacity,
                "label": "DANGER ZONE"
            },
            "track_center_line": self.track_center_line,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "zone_enabled": self.zone_enabled
        }


# Singleton
zone_service = ZoneService()
