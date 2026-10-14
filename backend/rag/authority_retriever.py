"""
RAG Authority Retriever — retrieves railway authority contact information
from the vector store based on location and event context.
Ranks authorities specifically by location in-charge jurisdiction.
"""
import os
import re
from typing import Optional
from rag.vector_store import vector_store
from rag.document_processor import document_processor


class AuthorityRetriever:
    """
    Retrieves authority contacts from the RAG knowledge base.
    Searches for relevant contacts based on location, station, division, etc.
    """
    
    def __init__(self):
        self.vector_store = vector_store
        self.doc_processor = document_processor
    
    def retrieve(self, query_context: dict, top_k: int = 15) -> list:
        """
        Retrieve authority contacts based on location context.
        
        Args:
            query_context: Dict with keys like nearest_station, railway_zone, 
                          division, district, event_type, risk_level
        
        Returns:
            List of authority contact dicts ranked by location affinity:
            [{name, designation, email, whatsapp, phone, station, division, is_primary_incharge, ...}]
        """
        target_station = str(query_context.get("nearest_station", "")).strip().lower()
        target_code = str(query_context.get("station_code", "")).strip().lower()
        target_division = str(query_context.get("division", "")).strip().lower()
        target_zone = str(query_context.get("railway_zone", "")).strip().lower()
        
        # Build search query from context
        query_parts = []
        for key in ["nearest_station", "station_code", "railway_zone", "division", 
                     "district", "state", "event_type"]:
            val = query_context.get(key, "")
            if val:
                query_parts.append(str(val))
        
        # Add authoritative railway keywords
        query_parts.extend([
            "station master", "incharge", "safety officer", "control room",
            "emergency controller", "permanent way", "danger zone"
        ])
        
        query = " ".join(query_parts)
        
        # Search vector store
        results = self.vector_store.search(query, top_k=top_k)
        
        if not results:
            return []
        
        # Extract contact information from results
        contacts = []
        for result in results:
            text = result.get("text", "")
            meta = result.get("metadata", {})
            extracted = self._extract_contacts(text, meta)
            for contact in extracted:
                contact["source"] = result.get("source", "")
                contact["vector_score"] = result.get("score", 0)
                contacts.append(contact)
        
        # Deduplicate by email
        seen_emails = set()
        unique_contacts = []
        for c in contacts:
            em = c.get("email", "").strip().lower()
            if em and em not in seen_emails:
                seen_emails.add(em)
                unique_contacts.append(c)
            elif not em:
                name_key = (c.get("name", "").strip().lower(), c.get("phone", ""))
                if any(name_key) and name_key not in seen_emails:
                    seen_emails.add(name_key)
                    unique_contacts.append(c)

        # Calculate Location In-Charge Affinity Score
        for c in unique_contacts:
            loc_score = 0.0
            c_station = str(c.get("station", "")).lower()
            c_code = str(c.get("station_code", "")).lower()
            c_division = str(c.get("division", "")).lower()
            c_zone = str(c.get("railway_zone", "")).lower()
            c_jurisdiction = str(c.get("jurisdiction", "")).lower()
            c_role = str(c.get("emergency_role", "")).upper()

            # Exact station match (Highest weight)
            if target_station and (target_station in c_station or c_station in target_station or target_station in c_jurisdiction):
                loc_score += 25.0
            if target_code and (target_code in c_code or target_code in c_station):
                loc_score += 20.0
            
            # Division match
            if target_division and (target_division in c_division or c_division in target_division or target_division in c_jurisdiction):
                loc_score += 15.0

            # Railway Zone match
            if target_zone and (target_zone in c_zone or c_zone in target_zone):
                loc_score += 8.0

            # Primary Incharge role boost
            if "PRIMARY" in c_role or c.get("priority") in (1, "1"):
                loc_score += 6.0
            elif "STATION" in c_role:
                loc_score += 4.0

            c["location_match_score"] = loc_score
            c["total_rank_score"] = round(loc_score + (c.get("vector_score", 0) * 5.0), 2)

        # Sort contacts descending by total rank score
        unique_contacts.sort(key=lambda x: x.get("total_rank_score", 0), reverse=True)

        # Mark primary in-charge
        if unique_contacts:
            unique_contacts[0]["is_primary_incharge"] = True

        return unique_contacts
    
    def _extract_contacts(self, text: str, meta: dict = None) -> list:
        """
        Extract contact information from text or metadata.
        Handles structured CSV/JSON metadata and unformatted text blocks.
        """
        contacts = []
        meta = meta or {}

        # 1. Direct metadata extraction (Highest precision from CSV/JSON)
        if meta and any(k in meta for k in ("email", "contact_email", "officer_in_charge", "station_name")):
            email = meta.get("email") or meta.get("contact_email") or ""
            name = meta.get("officer_in_charge") or meta.get("name") or meta.get("incharge") or ""
            designation = meta.get("designation") or meta.get("role") or ""
            station = meta.get("station_name") or meta.get("station") or ""
            station_code = meta.get("station_code") or ""
            division = meta.get("division") or ""
            railway_zone = meta.get("railway_zone") or ""
            phone = meta.get("phone_number") or meta.get("phone") or ""
            jurisdiction = meta.get("jurisdiction_section") or meta.get("section") or meta.get("jurisdiction") or ""
            role = meta.get("emergency_role") or meta.get("role") or ""
            priority = meta.get("priority_level") or meta.get("priority") or 1

            if email or phone or name:
                contacts.append({
                    "name": name,
                    "designation": designation,
                    "email": email,
                    "phone": phone,
                    "whatsapp": phone,
                    "station": station,
                    "station_code": station_code,
                    "division": division,
                    "railway_zone": railway_zone,
                    "jurisdiction": jurisdiction,
                    "emergency_role": role,
                    "priority": priority,
                    "is_primary_incharge": False,
                    "details": text[:200]
                })
                return contacts

        # 2. Key-Value Pipe/Newline Extraction (from CSV text representations)
        kv = {}
        for part in re.split(r'[\n|]', text):
            if ':' in part:
                k, v = part.split(':', 1)
                kv[k.strip().lower().replace(" ", "_")] = v.strip()

        if kv.get("email") or kv.get("officer_in_charge") or kv.get("name"):
            email = kv.get("email") or ""
            name = kv.get("officer_in_charge") or kv.get("name") or kv.get("incharge") or ""
            designation = kv.get("designation") or kv.get("role") or ""
            station = kv.get("station_name") or kv.get("station") or ""
            station_code = kv.get("station_code") or ""
            division = kv.get("division") or ""
            railway_zone = kv.get("railway_zone") or ""
            phone = kv.get("phone_number") or kv.get("phone") or ""
            jurisdiction = kv.get("jurisdiction_section") or kv.get("section") or ""
            role = kv.get("emergency_role") or ""

            if email or phone:
                contacts.append({
                    "name": name,
                    "designation": designation,
                    "email": email,
                    "phone": phone,
                    "whatsapp": phone,
                    "station": station,
                    "station_code": station_code,
                    "division": division,
                    "railway_zone": railway_zone,
                    "jurisdiction": jurisdiction,
                    "emergency_role": role,
                    "priority": 1 if "primary" in str(role).lower() else 2,
                    "is_primary_incharge": False,
                    "details": text[:200]
                })
                return contacts

        # 3. Unstructured Text Fallback with Regex
        emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', text)
        phones = re.findall(r'(?:\+91[\s-]?)?(?:\d{10}|\d{5}[\s-]?\d{5}|\d{4}[\s-]?\d{3}[\s-]?\d{3})', text)

        if emails or phones:
            contact = {
                "name": "",
                "designation": "",
                "email": emails[0] if emails else "",
                "phone": phones[0] if phones else "",
                "whatsapp": phones[0] if phones else "",
                "station": "",
                "station_code": "",
                "division": "",
                "railway_zone": "",
                "jurisdiction": "",
                "emergency_role": "STATION_DISPATCH",
                "priority": 2,
                "is_primary_incharge": False,
                "details": text[:200]
            }

            # Search name patterns
            name_match = re.search(r'(?:Name|Officer|Er\.|Mr\.|Mrs\.|Dr\.|Sri\.?|Shri\.?)\s*[:\-]?\s*([A-Za-z\s\.]{2,35})', text)
            if name_match:
                contact["name"] = name_match.group(1).strip()

            # Search designation
            desig_match = re.search(r'(Chief Divisional Safety Officer|Station Master|Station Director|Senior Section Engineer|Station Superintendent|Divisional Railway Manager|Safety Controller|RPF Post Commander)', text, re.IGNORECASE)
            if desig_match:
                contact["designation"] = desig_match.group(1).strip()

            # Search station context
            st_match = re.search(r'(Coimbatore Junction|Erode Junction|Tiruppur|Salem Junction|Palakkad Junction|Walayar|Madukkarai|Chennai Central)', text, re.IGNORECASE)
            if st_match:
                contact["station"] = st_match.group(1).strip()

            contacts.append(contact)

        return contacts
    
    def ingest_documents(self, directory: str = None, clear_first: bool = True) -> dict:
        """
        Process all documents in the knowledge base directory
        and add them to the vector store.
        """
        if clear_first:
            self.vector_store.clear()

        chunks = self.doc_processor.process_directory(directory)
        if chunks:
            self.vector_store.add_documents(chunks)
        
        return {
            "chunks_processed": len(chunks),
            "store_stats": self.vector_store.get_stats()
        }
    
    def ingest_file(self, filepath: str) -> dict:
        """Process a single uploaded file."""
        chunks = self.doc_processor.process_file(filepath)
        if chunks:
            self.vector_store.add_documents(chunks)
        
        return {
            "chunks_processed": len(chunks),
            "source": os.path.basename(filepath),
            "store_stats": self.vector_store.get_stats()
        }
    
    def get_stats(self) -> dict:
        """Get knowledge base statistics."""
        return self.vector_store.get_stats()


# Singleton
authority_retriever = AuthorityRetriever()
