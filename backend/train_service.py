"""
Train Tracking Service — manages train information, GPS tracking,
distance calculations, and Time-to-Impact (TTI) estimation.
"""
import json
import os
import math
import time
from datetime import datetime
from typing import Optional

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "train_config.json")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two GPS points in kilometers."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class TrainInfo:
    """Represents a single train being tracked."""
    
    def __init__(self, data: dict):
        self.train_number: str = data.get("train_number", "")
        self.train_name: str = data.get("train_name", "Unknown")
        self.source_station: str = data.get("source_station", "")
        self.source_code: str = data.get("source_code", "")
        self.destination_station: str = data.get("destination_station", "")
        self.destination_code: str = data.get("destination_code", "")
        self.speed_kmph: float = data.get("speed_kmph", 0)
        self.direction: str = data.get("direction", "unknown")
        self.status: str = data.get("status", "unknown")
        self.expected_arrival: str = data.get("expected_arrival", "")
        
        loc = data.get("current_location", {})
        self.latitude: float = loc.get("latitude", 0)
        self.longitude: float = loc.get("longitude", 0)
        
        self.last_updated: float = time.time()
        self._distance_to_monitoring: Optional[float] = None
        self._tti_seconds: Optional[float] = None
    
    def update_location(self, lat: float, lon: float, speed_kmph: float = None):
        """Update train GPS location."""
        self.latitude = lat
        self.longitude = lon
        if speed_kmph is not None:
            self.speed_kmph = speed_kmph
        self.last_updated = time.time()
        self._distance_to_monitoring = None  # Reset cached distance
        self._tti_seconds = None
    
    def calculate_distance(self, mon_lat: float, mon_lon: float) -> float:
        """Calculate distance from train to monitoring location in km."""
        self._distance_to_monitoring = haversine_km(
            self.latitude, self.longitude, mon_lat, mon_lon
        )
        return self._distance_to_monitoring
    
    def calculate_tti(self, distance_km: float = None) -> Optional[float]:
        """
        Calculate Time-to-Impact in seconds.
        Returns None if speed is zero or unknown.
        """
        dist = distance_km if distance_km is not None else self._distance_to_monitoring
        if dist is None or self.speed_kmph <= 0:
            self._tti_seconds = None
            return None
        
        # TTI = distance / speed, converted to seconds
        self._tti_seconds = (dist / self.speed_kmph) * 3600
        return self._tti_seconds
    
    def is_approaching(self) -> bool:
        """Check if train is moving toward the monitoring location."""
        return self.direction in ("towards_monitoring", "towards_obstruction", "approaching")
    
    def to_dict(self, mon_lat: float = None, mon_lon: float = None) -> dict:
        """Serialize train info for agent communication."""
        if mon_lat is not None and mon_lon is not None:
            self.calculate_distance(mon_lat, mon_lon)
            self.calculate_tti()
        
        return {
            "train_number": self.train_number,
            "train_name": self.train_name,
            "source_station": self.source_station,
            "source_code": self.source_code,
            "destination_station": self.destination_station,
            "destination_code": self.destination_code,
            "current_location": {
                "latitude": round(self.latitude, 6),
                "longitude": round(self.longitude, 6)
            },
            "speed_kmph": round(self.speed_kmph, 1),
            "direction": self.direction,
            "status": self.status,
            "expected_arrival": self.expected_arrival,
            "distance_km": round(self._distance_to_monitoring, 2) if self._distance_to_monitoring else None,
            "tti_seconds": round(self._tti_seconds, 0) if self._tti_seconds else None,
            "tti_display": self._format_tti(),
            "is_approaching": self.is_approaching(),
            "last_updated": self.last_updated
        }
    
    def _format_tti(self) -> str:
        """Format TTI for display."""
        if self._tti_seconds is None:
            return "N/A"
        minutes = int(self._tti_seconds // 60)
        seconds = int(self._tti_seconds % 60)
        if minutes > 60:
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}h {mins}m"
        return f"{minutes}m {seconds}s"


class TrainService:
    """Manages train tracking, GPS updates, and proximity calculations."""
    
    def __init__(self):
        self.monitoring_location = {
            "latitude": 11.0168,
            "longitude": 76.9558,
            "name": "Coimbatore Railway Section",
            "station_code": "CBE",
            "nearest_station": "Coimbatore Junction",
            "railway_zone": "Southern Railway",
            "division": "Salem Division",
            "district": "Coimbatore",
            "state": "Tamil Nadu"
        }
        self.trains: dict[str, TrainInfo] = {}
        self.simulation_enabled = True
        self.simulation_speed = 5
        self._last_sim_time = time.time()
        self._load_config()
    
    def _load_config(self):
        """Load train configuration from file."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    config = json.load(f)
                
                self.monitoring_location = config.get("monitoring_location", self.monitoring_location)
                self.simulation_enabled = config.get("simulation_enabled", True)
                self.simulation_speed = config.get("simulation_speed_multiplier", 5)
                
                for train_data in config.get("trains", []):
                    train = TrainInfo(train_data)
                    self.trains[train.train_number] = train
                
                print(f"[TrainService] Loaded {len(self.trains)} trains, monitoring: {self.monitoring_location['name']}")
        except Exception as e:
            print(f"[TrainService] Error loading config: {e}")
    
    def save_config(self):
        """Save current configuration."""
        config = {
            "monitoring_location": self.monitoring_location,
            "trains": [
                {
                    "train_number": t.train_number,
                    "train_name": t.train_name,
                    "source_station": t.source_station,
                    "source_code": t.source_code,
                    "destination_station": t.destination_station,
                    "destination_code": t.destination_code,
                    "current_location": {"latitude": t.latitude, "longitude": t.longitude},
                    "speed_kmph": t.speed_kmph,
                    "direction": t.direction,
                    "status": t.status,
                    "expected_arrival": t.expected_arrival
                }
                for t in self.trains.values()
            ],
            "simulation_enabled": self.simulation_enabled,
            "simulation_speed_multiplier": self.simulation_speed
        }
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
    
    def add_train(self, train_data: dict) -> str:
        """Add or update a train."""
        train = TrainInfo(train_data)
        self.trains[train.train_number] = train
        self.save_config()
        return train.train_number
    
    def remove_train(self, train_number: str):
        """Remove a train from tracking."""
        self.trains.pop(train_number, None)
        self.save_config()
    
    def update_train_location(self, train_number: str, lat: float, lon: float,
                               speed_kmph: float = None):
        """Update a specific train's GPS location."""
        if train_number in self.trains:
            self.trains[train_number].update_location(lat, lon, speed_kmph)
    
    def update_monitoring_location(self, lat: float, lon: float, name: str = None, **kwargs):
        """Update the monitoring location."""
        self.monitoring_location["latitude"] = lat
        self.monitoring_location["longitude"] = lon
        if name:
            self.monitoring_location["name"] = name
        self.monitoring_location.update(kwargs)
        self.save_config()
    
    def simulate_movement(self):
        """Simulate train movement toward monitoring location (for demo/testing)."""
        if not self.simulation_enabled:
            return
        
        now = time.time()
        dt = now - self._last_sim_time
        self._last_sim_time = now
        
        mon_lat = self.monitoring_location["latitude"]
        mon_lon = self.monitoring_location["longitude"]
        
        for train in self.trains.values():
            if train.status != "running" or not train.is_approaching():
                continue
            
            # Move train toward monitoring location
            speed_deg_per_sec = (train.speed_kmph / 111.0) / 3600.0  # Rough km to degrees
            actual_dt = dt * self.simulation_speed
            
            # Direction vector toward monitoring
            dlat = mon_lat - train.latitude
            dlon = mon_lon - train.longitude
            dist = math.sqrt(dlat**2 + dlon**2)
            
            if dist < 0.001:  # Very close, stop simulation
                continue
            
            step = min(speed_deg_per_sec * actual_dt, dist * 0.5)
            train.latitude += (dlat / dist) * step
            train.longitude += (dlon / dist) * step
            train.last_updated = now
    
    def get_nearest_train(self) -> Optional[dict]:
        """Get the nearest approaching train with distance and TTI."""
        mon_lat = self.monitoring_location["latitude"]
        mon_lon = self.monitoring_location["longitude"]
        
        nearest = None
        min_dist = float('inf')
        
        for train in self.trains.values():
            dist = train.calculate_distance(mon_lat, mon_lon)
            train.calculate_tti(dist)
            if dist < min_dist:
                min_dist = dist
                nearest = train
        
        if nearest:
            return nearest.to_dict(mon_lat, mon_lon)
        return None
    
    def get_all_trains(self) -> list:
        """Get all tracked trains with distances."""
        mon_lat = self.monitoring_location["latitude"]
        mon_lon = self.monitoring_location["longitude"]
        return [t.to_dict(mon_lat, mon_lon) for t in self.trains.values()]
    
    def get_approaching_trains(self) -> list:
        """Get only trains approaching the monitoring location."""
        return [t for t in self.get_all_trains() if t["is_approaching"]]
    
    def get_location_info(self) -> dict:
        """Get monitoring location intelligence."""
        return {
            "latitude": self.monitoring_location["latitude"],
            "longitude": self.monitoring_location["longitude"],
            "name": self.monitoring_location.get("name", ""),
            "station_code": self.monitoring_location.get("station_code", ""),
            "nearest_station": self.monitoring_location.get("nearest_station", ""),
            "railway_zone": self.monitoring_location.get("railway_zone", ""),
            "division": self.monitoring_location.get("division", ""),
            "district": self.monitoring_location.get("district", ""),
            "state": self.monitoring_location.get("state", "")
        }


# Singleton
train_service = TrainService()
