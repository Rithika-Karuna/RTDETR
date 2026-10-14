import base64
import cv2
import numpy as np

def base64_to_image(base64_str: str) -> np.ndarray:
    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]
    img_data = base64.b64decode(base64_str)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def image_to_base64(img: np.ndarray, quality: int = 80) -> str:
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, buffer = cv2.imencode('.jpg', img, encode_param)
    base64_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_str}"

def calculate_distance_heuristic(class_name: str, box_width: float, box_height: float, img_width: int, img_height: int) -> float:
    """
    Rough heuristic to estimate distance.
    Distance = (Known Object Height * Focal Length) / Pixel Height
    We'll assume some average heights (in meters) for common COCO classes.
    """
    avg_heights = {
        'person': 1.7,
        'car': 1.5,
        'bus': 3.0,
        'truck': 3.0,
        'motorcycle': 1.2,
        'bicycle': 1.0,
        'stop sign': 0.75,
        'dog': 0.6,
        'cat': 0.4,
        'chair': 1.0,
        'bottle': 0.25,
        'cup': 0.1,
    }
    
    # Fallback default height
    real_height = avg_heights.get(class_name.lower(), 0.5) 
    
    # Assume a standard focal length (in pixels). 
    # For a typical webcam with a ~60 degree FOV, focal_length ~ (image_width / 2) / tan(FOV/2)
    focal_length = img_width / 1.15
    
    if box_height <= 0:
        return 0.0
        
    distance = (real_height * focal_length) / box_height
    return round(distance, 2)
