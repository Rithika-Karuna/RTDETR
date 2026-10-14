"""
Agent 1 — Detection Agent
Wraps the existing YOLO/RT-DETR detection service.
Produces structured JSON output for the tracking agent.
"""
from datetime import datetime
from typing import Optional
import numpy as np


class DetectionAgent:
    """
    Processes camera frames through YOLO/RT-DETR and produces
    structured detection output for downstream agents.
    """
    
    def __init__(self, detection_service):
        self.detection_service = detection_service
        self._frame_count = 0
    
    def process(self, frame: np.ndarray, model_type: str = "yolo",
                conf_threshold: float = 0.25) -> dict:
        """
        Run detection on a frame and produce structured output.
        
        Returns:
            {
                "agent": "detection",
                "timestamp": "...",
                "frame_id": int,
                "detections": [
                    {"class_name": str, "confidence": float, "box": {...}, "track_id": int|None}
                ],
                "annotated_frame": np.ndarray,
                "raw_frame": np.ndarray,
                "model_type": str
            }
        """
        self._frame_count += 1
        timestamp = datetime.utcnow().isoformat()
        
        # Use tracking mode to get track IDs from ultralytics
        annotated_frame, detections, detections_with_ids = self._detect_with_tracking(
            frame, model_type, conf_threshold
        )
        
        return {
            "agent": "detection",
            "timestamp": timestamp,
            "frame_id": self._frame_count,
            "detections": detections_with_ids,
            "detection_count": len(detections_with_ids),
            "annotated_frame": annotated_frame,
            "raw_frame": frame,
            "model_type": model_type
        }
    
    def _detect_with_tracking(self, frame: np.ndarray, model_type: str,
                               conf_threshold: float) -> tuple:
        """
        Run detection with built-in ultralytics tracking for ID assignment.
        Falls back to regular detection if tracking is unavailable.
        """
        import cv2
        
        # Select YOLO11 model
        model, resolved_type = self.detection_service.get_model(model_type)
        if model is None:
            return frame.copy(), [], []
        model_type = resolved_type

        # Run tracking with ByteTrack (natively supported by YOLO11)
        try:
            results = model.track(frame, conf=conf_threshold, persist=True, tracker="bytetrack.yaml", verbose=False)
        except Exception:
            try:
                results = model.track(frame, conf=conf_threshold, persist=True, verbose=False)
            except Exception:
                results = model(frame, conf=conf_threshold, verbose=False)
        
        detections = []
        detections_with_ids = []
        annotated_frame = frame.copy()
        
        box_color = (70, 230, 110) if model_type == "yolo" else (240, 160, 20)
        text_color = (0, 0, 0)
        
        # Dynamic scale for crisp, bold boxes and labels on all resolutions
        h, w = frame.shape[:2]
        scale = max(1.0, min(w, h) / 480.0)
        box_thick = max(2, int(2.5 * scale))
        font_scale = max(0.5, 0.5 * scale)
        font_thick = max(1, int(1.5 * scale))

        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                width = x2 - x1
                height = y2 - y1
                conf = round(float(box.conf[0]), 2)
                cls_id = int(box.cls[0])
                class_name = model.names[cls_id]
                
                # Get track ID if available
                track_id = None
                if hasattr(box, 'id') and box.id is not None:
                    track_id = int(box.id[0])
                
                det = {
                    "class_name": class_name,
                    "confidence": conf,
                    "box": {"x": x1, "y": y1, "width": width, "height": height}
                }
                det_with_id = {**det, "track_id": track_id}
                
                detections.append(det)
                detections_with_ids.append(det_with_id)
                
                # Draw bounding box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, box_thick)
                
                # Label with track ID
                if track_id is not None:
                    label = f"{class_name.upper()} #{track_id} {int(conf * 100)}%"
                else:
                    label = f"{class_name.upper()} {int(conf * 100)}%"
                
                font = cv2.FONT_HERSHEY_DUPLEX
                (label_w, label_h), baseline = cv2.getTextSize(label, font, font_scale, font_thick)
                pad_x = int(5 * scale)
                pad_y = int(4 * scale)
                
                label_y1 = max(y1 - label_h - pad_y * 2, 0)
                label_y2 = y1
                cv2.rectangle(annotated_frame, (x1, label_y1),
                            (x1 + label_w + pad_x * 2, label_y2), box_color, cv2.FILLED)
                cv2.putText(annotated_frame, label, (x1 + pad_x, label_y2 - pad_y),
                          font, font_scale, text_color, font_thick, cv2.LINE_AA)
        
        return annotated_frame, detections, detections_with_ids

    def reset_tracker(self):
        """Reset internal tracker state."""
        self._frame_count = 0
        if hasattr(self.detection_service, 'reset_tracker'):
            self.detection_service.reset_tracker()
