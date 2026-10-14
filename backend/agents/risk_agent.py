"""
Agent 3 — Risk Analysis Agent
Analyzes tracking data + train proximity to calculate risk scores.
Does NOT send alerts directly — passes results to Alert Validation Agent.
"""
from datetime import datetime
from typing import Optional


class RiskAgent:
    """
    Receives tracking and train information, calculates risk using
    the deterministic RiskEngine, and produces structured risk assessment.
    """
    
    def __init__(self, risk_engine, train_service):
        self.risk_engine = risk_engine
        self.train_service = train_service
    
    def process(self, tracking_result: dict) -> dict:
        """
        Analyze tracking data and produce risk assessment.
        
        Args:
            tracking_result: Output from TrackingAgent.process()
        
        Returns:
            Risk assessment with score, level, breakdown, and recommendation.
            This agent does NOT authorize alerts.
        """
        tracked_objects = tracking_result.get("tracked_objects", [])
        timestamp = tracking_result.get("timestamp", datetime.utcnow().isoformat())
        
        # Simulate train movement if enabled
        self.train_service.simulate_movement()
        
        # Get nearest approaching train
        train_info = self.train_service.get_nearest_train()
        all_trains = self.train_service.get_all_trains()
        
        # Calculate risk
        risk_result = self.risk_engine.calculate_risk(tracked_objects, train_info)
        
        return {
            "agent": "risk_analysis",
            "timestamp": timestamp,
            "frame_id": tracking_result.get("frame_id", 0),
            "risk_score": risk_result["risk_score"],
            "risk_level": risk_result["risk_level"],
            "reason": risk_result["reason"],
            "recommended_action": risk_result["recommended_action"],
            "breakdown": risk_result["breakdown"],
            "danger_objects_count": risk_result["danger_objects_count"],
            "warning_objects_count": risk_result["warning_objects_count"],
            "primary_object": risk_result["primary_object"],
            "all_object_types": risk_result["all_object_types"],
            "max_persistence_seconds": risk_result["max_persistence_seconds"],
            "train_info": train_info,
            "all_trains": all_trains,
            "tracked_objects": tracked_objects
        }
