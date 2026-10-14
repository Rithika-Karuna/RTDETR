import os
import cv2
import numpy as np
from ultralytics import YOLO
from zone_service import zone_service


class DetectionService:
    """
    State-of-the-Art Object Detection Service powered by Ultralytics YOLO11.
    Integrates spatial railway zone classification (SAFE ZONE, MEDIUM ZONE, DANGER ZONE).
    """
    def __init__(self, yolo11m_path="yolo11m.pt", yolo11s_path="yolo11s.pt"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        m_path = os.path.join(base_dir, yolo11m_path) if not os.path.isabs(yolo11m_path) else yolo11m_path
        s_path = os.path.join(base_dir, yolo11s_path) if not os.path.isabs(yolo11s_path) else yolo11s_path

        # If file exists in base_dir use full path, otherwise fall back to filename for auto-download
        m_target = m_path if os.path.exists(m_path) else yolo11m_path
        s_target = s_path if os.path.exists(s_path) else yolo11s_path

        print(f"Loading YOLO11 Medium (Flagship High Accuracy): {m_target}...")
        try:
            self.yolo11m = YOLO(m_target)
            print("YOLO11 Medium loaded successfully.")
        except Exception as e:
            print("Failed to load YOLO11 Medium:", e)
            self.yolo11m = None

        print(f"Loading YOLO11 Small (High-Speed Variant): {s_target}...")
        try:
            self.yolo11s = YOLO(s_target)
            print("YOLO11 Small loaded successfully.")
        except Exception as e:
            print("Failed to load YOLO11 Small:", e)
            self.yolo11s = None

    def get_model(self, model_type: str = "yolo11m"):
        """Select appropriate YOLO11 model variant."""
        model_type = str(model_type).lower().strip()
        if model_type in ("yolo11s", "s", "fast", "speed") and self.yolo11s is not None:
            return self.yolo11s, "yolo11s"
        if self.yolo11m is not None:
            return self.yolo11m, "yolo11m"
        if self.yolo11s is not None:
            return self.yolo11s, "yolo11s"
        return None, "none"

    def reset_tracker(self):
        """Reset internal tracker states across models to prevent jumping tracks."""
        for m in (self.yolo11m, self.yolo11s):
            if m is not None and hasattr(m, 'predictor') and m.predictor is not None:
                if hasattr(m.predictor, 'trackers') and m.predictor.trackers:
                    for tracker in m.predictor.trackers:
                        if hasattr(tracker, 'reset'):
                            tracker.reset()

    def process_frame(self, frame: np.ndarray, model_type: str = "yolo11m", conf_threshold: float = 0.35, draw_zones: bool = True):
        """
        Runs inference on a single frame using the powerful YOLO11 model.
        Classifies all detected objects into SAFE ZONE, MEDIUM ZONE, or DANGER ZONE,
        and annotates the frame with zone ROI overlays and zone-marked bounding boxes.
        Returns the annotated frame and structured list of detections.
        """
        model, resolved_type = self.get_model(model_type)
        if model is None:
            print("No YOLO11 model available for inference.")
            return frame.copy(), []

        # Run inference with confidence threshold
        results = model(frame, conf=conf_threshold, verbose=False)

        detections = []
        annotated_frame = frame.copy()
        h, w = frame.shape[:2]

        # Draw zone classification ROI polygons (Safe, Medium, Danger) first if enabled
        if draw_zones and zone_service.zone_enabled:
            annotated_frame = zone_service.draw_zones(annotated_frame)

        # Dynamic scale for crisp, bold boxes and labels on all resolutions
        scale = max(1.0, min(w, h) / 480.0)
        box_thick = max(2, int(2.5 * scale))
        font_scale = max(0.48, 0.48 * scale)
        font_thick = max(1, int(1.4 * scale))
        pad_x = int(6 * scale)
        pad_y = int(4 * scale)

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                # Bounding box coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                width = x2 - x1
                height = y2 - y1

                # Confidence and class
                conf = round(float(box.conf[0]), 2)
                cls_id = int(box.cls[0])
                class_name = model.names[cls_id]

                # Classify into zone: SAFE, MEDIUM, or DANGER
                zone_info = zone_service.classify_bbox(x1, y1, width, height, frame_w=w, frame_h=h)
                zone = zone_info.get("zone", "SAFE")
                zone_label = zone_info.get("zone_label", "SAFE ZONE")

                detections.append({
                    "class_name": class_name,
                    "confidence": conf,
                    "box": {
                        "x": x1,
                        "y": y1,
                        "width": width,
                        "height": height
                    },
                    "zone": zone,
                    "zone_label": zone_label,
                    "distance_to_track_center": zone_info.get("distance_to_track_center", 0),
                    "danger_overlap_ratio": zone_info.get("danger_overlap_ratio", 0)
                })

                # Determine color scheme by zone classification
                if zone == "DANGER":
                    box_color = (0, 0, 255)       # Red BGR
                    text_color = (255, 255, 255)
                    zone_badge = "DANGER ZONE"
                elif zone in ("MEDIUM", "WARNING"):
                    box_color = (0, 165, 255)     # Amber/Orange BGR
                    text_color = (0, 0, 0)
                    zone_badge = "MEDIUM ZONE"
                else:
                    box_color = (70, 235, 120)    # Cyber Emerald Green BGR
                    text_color = (0, 0, 0)
                    zone_badge = "SAFE ZONE"

                # Draw bold bounding box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, box_thick)

                # Corner brackets for surveillance UI aesthetics
                c_len = max(8, min(int(18 * scale), width // 3, height // 3))
                c_thick = max(box_thick + 1, int(3.2 * scale))
                # Top-left
                cv2.line(annotated_frame, (x1, y1 + c_len), (x1, y1), box_color, c_thick)
                cv2.line(annotated_frame, (x1, y1), (x1 + c_len, y1), box_color, c_thick)
                # Top-right
                cv2.line(annotated_frame, (x2 - c_len, y1), (x2, y1), box_color, c_thick)
                cv2.line(annotated_frame, (x2, y1), (x2, y1 + c_len), box_color, c_thick)
                # Bottom-left
                cv2.line(annotated_frame, (x1, y2 - c_len), (x1, y2), box_color, c_thick)
                cv2.line(annotated_frame, (x1, y2), (x1 + c_len, y2), box_color, c_thick)
                # Bottom-right
                cv2.line(annotated_frame, (x2 - c_len, y2), (x2, y2), box_color, c_thick)
                cv2.line(annotated_frame, (x2, y2), (x2, y2 - c_len), box_color, c_thick)

                # Draw filled label background pill showing Class, Confidence, and Zone Marking
                label = f"{class_name.upper()} {int(conf * 100)}% | {zone_badge}"
                font = cv2.FONT_HERSHEY_DUPLEX
                (label_w, label_h), _ = cv2.getTextSize(label, font, font_scale, font_thick)

                label_y1 = max(y1 - label_h - pad_y * 2, 0)
                label_y2 = y1
                cv2.rectangle(annotated_frame, (x1, label_y1), (x1 + label_w + pad_x * 2, label_y2), box_color, cv2.FILLED)
                cv2.putText(annotated_frame, label, (x1 + pad_x, label_y2 - pad_y), font, font_scale, text_color, font_thick, cv2.LINE_AA)

        return annotated_frame, detections

# Singleton instance
detection_service = DetectionService()
