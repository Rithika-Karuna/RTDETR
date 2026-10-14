"""
Agent 6 — Authority Retrieval Agent
Retrieves relevant railway authority contacts from the RAG knowledge base
based on GPS location and event type.
"""
from datetime import datetime
from typing import Optional


class AuthorityAgent:
    """
    Retrieves authority contact information from the RAG knowledge base
    based on the current GPS location, nearest station, and event type.
    
    Only uses contacts retrieved from the approved knowledge base.
    If no verified contact is found, the system does NOT fabricate one.
    """
    
    def __init__(self, authority_retriever=None):
        self.authority_retriever = authority_retriever
    
    def process(self, location_info: dict, event: dict = None) -> dict:
        """
        Retrieve relevant authorities for the given location and event.
        
        Args:
            location_info: Output from LocationAgent
            event: Event data from AlertValidationAgent
        
        Returns:
            Authority contact information retrieved from knowledge base.
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Build query context
        query_context = {
            "latitude": location_info.get("latitude"),
            "longitude": location_info.get("longitude"),
            "nearest_station": location_info.get("nearest_station", ""),
            "station_code": location_info.get("station_code", ""),
            "railway_zone": location_info.get("railway_zone", ""),
            "division": location_info.get("division", ""),
            "district": location_info.get("district", ""),
            "state": location_info.get("state", ""),
            "event_type": event.get("object_type", "Track Obstruction") if event else "Track Obstruction",
            "risk_level": event.get("risk_level", "HIGH") if event else "HIGH"
        }
        
        # Attempt RAG retrieval
        authorities = []
        rag_available = False
        
        if self.authority_retriever:
            try:
                rag_results = self.authority_retriever.retrieve(query_context)
                if rag_results:
                    authorities = rag_results
                    rag_available = True
            except Exception as e:
                print(f"[AuthorityAgent] RAG retrieval error: {e}")
        
        primary = authorities[0] if authorities else None
        station_name = location_info.get("nearest_station", "")
        message = (
            f"RAG retrieved in-charge authority for {station_name}: {primary.get('name')} ({primary.get('designation')}) <{primary.get('email')}>"
            if primary else "No verified contacts found in knowledge base."
        )

        return {
            "agent": "authority_retrieval",
            "timestamp": timestamp,
            "rag_available": rag_available,
            "query_context": query_context,
            "authorities": authorities,
            "authority_count": len(authorities),
            "primary_authority": primary,
            "primary_email": primary.get("email") if primary else None,
            "primary_incharge": primary.get("name") if primary else None,
            "primary_role": primary.get("designation") if primary else None,
            "nearest_station": station_name,
            "railway_zone": location_info.get("railway_zone", ""),
            "division": location_info.get("division", ""),
            "message": message
        }
