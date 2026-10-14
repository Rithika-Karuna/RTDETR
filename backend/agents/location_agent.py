"""
Agent 4 — Location Intelligence Agent
Uses GPS coordinates to determine location context:
nearest station, railway zone, division, district, state.
"""
from datetime import datetime


class LocationAgent:
    """
    Provides location intelligence based on GPS coordinates
    and configured monitoring location data.
    """
    
    def __init__(self, train_service):
        self.train_service = train_service
    
    def process(self, risk_result: dict = None) -> dict:
        """
        Get location intelligence for the monitoring location.
        
        Returns:
            Location info with GPS, station, zone, division details.
        """
        location = self.train_service.get_location_info()
        
        return {
            "agent": "location_intelligence",
            "timestamp": datetime.utcnow().isoformat(),
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "location_name": location.get("name", ""),
            "station_code": location.get("station_code", ""),
            "nearest_station": location.get("nearest_station", ""),
            "railway_zone": location.get("railway_zone", ""),
            "division": location.get("division", ""),
            "district": location.get("district", ""),
            "state": location.get("state", ""),
            "gps_display": f"{location.get('latitude', 0):.6f}, {location.get('longitude', 0):.6f}"
        }
