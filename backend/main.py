import asyncio
import os
import json
import shutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import numpy as np
import cv2

from utils import base64_to_image, image_to_base64, calculate_distance_heuristic
from model_service import detection_service
from agent_pipeline import agent_pipeline
from zone_service import zone_service
from train_service import train_service
from risk_engine import risk_engine
from event_manager import event_manager
from database import get_events, get_event, get_event_count, get_alert_logs
from rag.authority_retriever import authority_retriever

# Ensure data directories exist
os.makedirs(os.path.join(os.path.dirname(__file__), "data", "knowledge_base"), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "data", "evidence"), exist_ok=True)

app = FastAPI(title="Railway Track Vulnerability Detection & Alert System")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve evidence images as static files
EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "data", "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)
app.mount("/evidence", StaticFiles(directory=EVIDENCE_DIR), name="evidence")


def enrich_detections_with_distance(detections, img_width, img_height):
    enriched = []
    for d in detections:
        dist = calculate_distance_heuristic(
            class_name=d["class_name"],
            box_width=d["box"]["width"],
            box_height=d["box"]["height"],
            img_width=img_width,
            img_height=img_height
        )
        d["distance_m"] = dist
        enriched.append(d)
    return enriched


# ============================================================
# EXISTING ENDPOINTS (preserved)
# ============================================================
# ENDPOINTS
# ============================================================

@app.post("/api/tracker/reset")
async def reset_tracker():
    agent_pipeline.reset()
    detection_service.reset_tracker()
    return {"status": "ok", "message": "Tracker state reset"}


@app.post("/api/detect/image")
async def detect_image(file: UploadFile = File(...), model: str = Form("yolo11m"), conf: float = Form(0.35)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image format.")

    img_height, img_width = img.shape[:2]

    pipeline_result = await asyncio.to_thread(
        agent_pipeline.process_frame,
        img,
        model_type=model,
        conf_threshold=conf
    )
    annotated_img = pipeline_result["annotated_frame"]
    detections = enrich_detections_with_distance(pipeline_result["detections"], img_width, img_height)

    base64_img = image_to_base64(annotated_img, quality=85)

    return {
        "image": base64_img,
        "detections": detections,
        "zones": zone_service.get_config(),
        "frame_width": img_width,
        "frame_height": img_height,
        "pipeline": True,
        "tracking": pipeline_result.get("tracking"),
        "risk": pipeline_result.get("risk"),
        "train": pipeline_result.get("train"),
        "all_trains": pipeline_result.get("all_trains"),
        "location": pipeline_result.get("location"),
        "authority": pipeline_result.get("authority"),
        "alert": pipeline_result.get("alert"),
        "notification": pipeline_result.get("notification"),
        "summary": {
            "total": len(detections),
            "safe": sum(1 for d in detections if d.get("zone") == "SAFE"),
            "medium": sum(1 for d in detections if d.get("zone") in ("MEDIUM", "WARNING")),
            "danger": sum(1 for d in detections if d.get("zone") == "DANGER")
        }
    }


@app.websocket("/ws/detect/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted.")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                # Expecting JSON: {"model": "yolo11m", "conf": 0.35, "quality": 80, "image": "base64...", "pipeline": false, "skip_image": false}
                payload = json.loads(data)
                model_type = payload.get("model", "yolo11m")
                conf_thresh = float(payload.get("conf", 0.35))
                jpeg_quality = int(payload.get("quality", 80))
                image_data = payload.get("image", "")
                use_pipeline = payload.get("pipeline", False)
                skip_image = payload.get("skip_image", False)
                frame = base64_to_image(image_data)
            except Exception as e:
                print("Error parsing message or decoding image:", e)
                await websocket.send_text(json.dumps({
                    "image": "",
                    "detections": [],
                    "error": str(e)
                }))
                continue

            if frame is None or getattr(frame, 'size', 0) == 0:
                await websocket.send_text(json.dumps({
                    "image": "",
                    "detections": [],
                    "warning": "Empty frame"
                }))
                continue

            img_height, img_width = frame.shape[:2]

            if use_pipeline:
                # === RAILWAY MONITORING PIPELINE ===
                pipeline_result = await asyncio.to_thread(
                    agent_pipeline.process_frame,
                    frame,
                    model_type=model_type,
                    conf_threshold=conf_thresh
                )

                annotated_frame = pipeline_result["annotated_frame"]
                detections = pipeline_result["detections"]
                detections = enrich_detections_with_distance(detections, img_width, img_height)

                tracking_data = pipeline_result.get("tracking")
                if tracking_data and "tracked_objects" in tracking_data:
                    tracking_data["tracked_objects"] = enrich_detections_with_distance(
                        tracking_data["tracked_objects"], img_width, img_height
                    )

                base64_img = image_to_base64(annotated_frame, quality=jpeg_quality)

                await websocket.send_text(json.dumps({
                    "image": base64_img,
                    "detections": detections,
                    "frame_width": img_width,
                    "frame_height": img_height,
                    "zones": zone_service.get_config(),
                    "pipeline": True,
                    "tracking": pipeline_result.get("tracking"),
                    "risk": pipeline_result.get("risk"),
                    "train": pipeline_result.get("train"),
                    "all_trains": pipeline_result.get("all_trains"),
                    "location": pipeline_result.get("location"),
                    "authority": pipeline_result.get("authority"),
                    "alert": pipeline_result.get("alert"),
                    "notification": pipeline_result.get("notification"),
                    "pipeline_ms": pipeline_result.get("pipeline_ms"),
                    "frame_id": pipeline_result.get("frame_id"),
                }))
            else:
                # === ORIGINAL DETECTION (preserved with zone intelligence) ===
                annotated_frame, detections = await asyncio.to_thread(
                    detection_service.process_frame,
                    frame,
                    model_type=model_type,
                    conf_threshold=conf_thresh,
                    draw_zones=True
                )
                detections = enrich_detections_with_distance(detections, img_width, img_height)

                base64_img = image_to_base64(annotated_frame, quality=jpeg_quality)

                await websocket.send_text(json.dumps({
                    "image": base64_img,
                    "detections": detections,
                    "frame_width": img_width,
                    "frame_height": img_height,
                    "zones": zone_service.get_config(),
                }))

            await asyncio.sleep(0.001)

    except WebSocketDisconnect:
        print("WebSocket client disconnected.")
    except Exception as e:
        print(f"WebSocket error: {e}")


# ============================================================
# ZONE MANAGEMENT APIs
# ============================================================

@app.get("/api/zones")
async def get_zones():
    return zone_service.get_config()


class ZoneUpdateRequest(BaseModel):
    danger_polygon: list = None
    warning_polygon: list = None
    safe_polygon: list = None
    track_center_line: list = None
    frame_width: int = None
    frame_height: int = None
    zone_enabled: bool = None


@app.put("/api/zones")
async def update_zones(req: ZoneUpdateRequest):
    zone_service.update_zones(
        danger_polygon=req.danger_polygon,
        warning_polygon=req.warning_polygon,
        safe_polygon=req.safe_polygon,
        track_center_line=req.track_center_line,
        frame_width=req.frame_width,
        frame_height=req.frame_height,
        zone_enabled=req.zone_enabled,
    )
    return {"status": "ok", "config": zone_service.get_config()}


# ============================================================
# TRAIN MANAGEMENT APIs
# ============================================================

@app.get("/api/trains")
async def get_trains():
    return {
        "trains": train_service.get_all_trains(),
        "monitoring_location": train_service.get_location_info(),
    }


@app.get("/api/trains/nearest")
async def get_nearest_train():
    train_service.simulate_movement()
    return train_service.get_nearest_train() or {"message": "No trains being tracked"}


class TrainRequest(BaseModel):
    train_number: str
    train_name: str = "Unknown"
    source_station: str = ""
    source_code: str = ""
    destination_station: str = ""
    destination_code: str = ""
    current_location: dict = {"latitude": 0, "longitude": 0}
    speed_kmph: float = 0
    direction: str = "towards_monitoring"
    status: str = "running"
    expected_arrival: str = ""


@app.post("/api/trains")
async def add_train(req: TrainRequest):
    tid = train_service.add_train(req.model_dump())
    return {"status": "ok", "train_number": tid}


@app.delete("/api/trains/{train_number}")
async def remove_train(train_number: str):
    train_service.remove_train(train_number)
    return {"status": "ok"}


class LocationUpdateRequest(BaseModel):
    latitude: float
    longitude: float
    name: str = None
    station_code: str = None
    nearest_station: str = None
    railway_zone: str = None
    division: str = None
    district: str = None
    state: str = None


@app.put("/api/monitoring-location")
async def update_monitoring_location(req: LocationUpdateRequest):
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    lat = data.pop("latitude")
    lon = data.pop("longitude")
    train_service.update_monitoring_location(lat, lon, **data)
    return {"status": "ok", "location": train_service.get_location_info()}


# ============================================================
# RISK CONFIGURATION APIs
# ============================================================

@app.get("/api/risk/config")
async def get_risk_config():
    c = risk_engine.config
    return {
        "thresholds": c.thresholds,
        "weights": c.weights,
        "object_severity_scores": c.object_severity_scores,
        "tti_thresholds_seconds": c.tti_thresholds,
        "train_distance_thresholds_km": c.train_distance_thresholds,
        "alert_cooldown_seconds": c.alert_cooldown_seconds,
        "min_persistence_seconds": c.min_persistence_seconds,
        "min_confidence": c.min_confidence,
        "min_alert_risk_level": c.min_alert_risk_level,
    }


@app.put("/api/risk/config")
async def update_risk_config(updates: dict):
    risk_engine.update_config(updates)
    return {"status": "ok"}


# ============================================================
# EVENT & ALERT HISTORY APIs
# ============================================================

@app.get("/api/events")
async def list_events(limit: int = 50, offset: int = 0,
                      risk_level: str = None, status: str = None,
                      object_type: str = None):
    filters = {}
    if risk_level:
        filters["risk_level"] = risk_level
    if status:
        filters["status"] = status
    if object_type:
        filters["object_type"] = object_type
    events = get_events(limit=limit, offset=offset, filters=filters or None)
    total = get_event_count(filters=filters or None)
    return {"events": events, "total": total, "limit": limit, "offset": offset}


@app.get("/api/events/{event_id}")
async def get_single_event(event_id: str):
    event = get_event(event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    alerts = get_alert_logs(event_id)
    return {"event": event, "alert_logs": alerts}


@app.post("/api/events/{event_id}/resolve")
async def resolve_event(event_id: str):
    event_manager.resolve_event(event_id)
    return {"status": "ok", "event_id": event_id}


@app.post("/api/events/{event_id}/acknowledge")
async def acknowledge_event(event_id: str):
    event_manager.acknowledge_event(event_id)
    return {"status": "ok", "event_id": event_id}


@app.get("/api/events/active/summary")
async def get_active_events_summary():
    return {"active_events": event_manager.get_active_event_summary()}


# ============================================================
# DASHBOARD STATE API
# ============================================================

@app.get("/api/dashboard")
async def get_dashboard():
    train_service.simulate_movement()
    location_info = train_service.get_location_info()
    return {
        "pipeline": agent_pipeline.get_dashboard_state(),
        "trains": train_service.get_all_trains(),
        "monitoring_location": location_info,
        "zones": zone_service.get_config(),
        "active_events": event_manager.get_active_event_summary(),
        "authority": authority_retriever.retrieve(location_info) if authority_retriever else [],
    }


# ============================================================
# RAG KNOWLEDGE BASE APIs
# ============================================================

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "data", "knowledge_base")


@app.post("/api/knowledge/upload")
async def upload_knowledge_document(file: UploadFile = File(...)):
    allowed = {".pdf", ".docx", ".doc", ".csv", ".json", ".txt", ".md"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported format: {ext}. Allowed: {', '.join(allowed)}")

    filepath = os.path.join(KNOWLEDGE_DIR, file.filename)
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    result = authority_retriever.ingest_file(filepath)
    return {"status": "ok", "filename": file.filename, **result}


@app.post("/api/knowledge/reindex")
async def reindex_knowledge():
    result = authority_retriever.ingest_documents()
    return {"status": "ok", **result}


@app.get("/api/knowledge/stats")
async def knowledge_stats():
    return authority_retriever.get_stats()


@app.get("/api/knowledge/search")
async def search_knowledge(q: str, top_k: int = 5):
    from rag.vector_store import vector_store
    results = vector_store.search(q, top_k=top_k)
    return {"query": q, "results": results}


@app.get("/api/knowledge/authorities")
async def get_rag_authorities(station: str = None, division: str = None, zone: str = None):
    loc = train_service.get_location_info()
    query_ctx = {
        "nearest_station": station or loc.get("nearest_station", "Coimbatore Junction"),
        "division": division or loc.get("division", "Salem Division"),
        "railway_zone": zone or loc.get("railway_zone", "Southern Railway"),
        "station_code": loc.get("station_code", "CBE"),
    }
    authorities = authority_retriever.retrieve(query_ctx)
    return {
        "query": query_ctx,
        "primary_incharge": authorities[0] if authorities else None,
        "authorities": authorities,
        "count": len(authorities)
    }


# ============================================================
# NOTIFICATION CONFIGURATION APIs
# ============================================================

@app.get("/api/notifications/config")
async def get_notification_config():
    config_path = os.path.join(os.path.dirname(__file__), "config", "notification_config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        # Mask passwords
        if "email" in config:
            config["email"]["sender_password"] = "***" if config["email"].get("sender_password") else ""
        if "whatsapp" in config:
            config["whatsapp"]["auth_token"] = "***" if config["whatsapp"].get("auth_token") else ""
        return config
    return {}


@app.put("/api/notifications/config")
async def update_notification_config(config: dict):
    config_path = os.path.join(os.path.dirname(__file__), "config", "notification_config.json")

    # Load existing to preserve passwords if masked
    existing = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            existing = json.load(f)

    # Merge — don't overwrite passwords with "***"
    merged = dict(existing)
    if "email" in config:
        email_data = dict(existing.get("email", {}))
        email_data.update(config["email"])
        if config["email"].get("sender_password") in ("***", None, ""):
            email_data["sender_password"] = existing.get("email", {}).get("sender_password", "")
        merged["email"] = email_data
        from notifications.email_service import email_service
        email_service.update_config(email_data)
    if "whatsapp" in config:
        wa_data = dict(existing.get("whatsapp", {}))
        wa_data.update(config["whatsapp"])
        if config["whatsapp"].get("auth_token") in ("***", None, ""):
            wa_data["auth_token"] = existing.get("whatsapp", {}).get("auth_token", "")
        merged["whatsapp"] = wa_data
        from notifications.whatsapp_service import whatsapp_service
        whatsapp_service.update_config(wa_data)

    for k in ("alert_cooldown_seconds", "max_alerts_per_hour", "include_evidence_image", "templates"):
        if k in config:
            merged[k] = config[k]

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    return {"status": "ok"}


@app.post("/api/notifications/test-email")
async def send_test_email(payload: dict):
    from notifications.email_service import email_service
    recipient = payload.get("email") or "rishe8080s@gmail.com"
    result = await asyncio.to_thread(email_service.send_test_alert, recipient)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
