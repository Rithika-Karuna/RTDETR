# Indian Railways Safety Protocol & Emergency Authority Escalation Manual

## 1. Executive Summary & Purpose
This document constitutes the official railway knowledge base governing automated track vulnerability monitoring, emergency intrusion protocols, and direct authority notification routing for the Southern Railway zone and its operating divisions (Salem Division, Palakkad Division, Chennai Division).

When automated computer vision and deep learning models detect unauthorized entities (humans, wild elephants, cattle, vehicles, boulders, or debris) in the **Danger Zone** (Track Bed) or **Medium Zone** (Track Clearance Envelope), the AI Agent Pipeline queries this document repository via Retrieval-Augmented Generation (RAG) to determine the designated In-Charge Authority based on the current GPS location, nearest railway station, and divisional jurisdiction.

---

## 2. Divisional Jurisdictions & Station Master In-Charge Directory

### 2.1 Salem Division (Coimbatore Section) — Primary Operational Sector
- **Division Name**: Salem Division (SA Division)
- **Railway Zone**: Southern Railway (SR)
- **Primary Station**: Coimbatore Junction (Station Code: CBE)
- **GPS Coordinates**: 11.0168° N, 76.9558° E
- **Track Sections**: Coimbatore Junction - Podanur - Irugur - Singanallur Track Sections

#### Designated Authorities for Coimbatore Section:
1. **Chief Divisional Safety Officer & Emergency Controller (Primary In-Charge)**:
   - **Name**: Er. Rishe S
   - **Designation**: Chief Divisional Safety Officer & Emergency Operations In-Charge
   - **Email**: `rishe8080s@gmail.com`
   - **Mobile**: +91 94432 18080
   - **Jurisdiction**: Coimbatore Junction, Podanur, Madukkarai, Irugur Danger Zone Tracks
   - **Mandate**: Receives immediate Tier-1 critical track intrusion alerts, initiates caution orders to approaching locomotives, coordinates with DRM control room.

2. **Station Master (Operating In-Charge)**:
   - **Name**: K. Ramanathan
   - **Designation**: Station Master In-Charge, Coimbatore Junction
   - **Email**: `sm.coimbatore@sr.railnet.gov.in`
   - **Phone**: +91 422 2300130
   - **Jurisdiction**: Coimbatore Junction Yard, Track Lines 1-6, Passenger Platforms

3. **Senior Section Engineer (Permanent Way - Track Safety)**:
   - **Name**: M. Senthil Kumar
   - **Designation**: Senior Section Engineer (P-Way Track Maintenance)
   - **Email**: `sse.pway.cbe@sr.railnet.gov.in`
   - **Phone**: +91 94432 55670
   - **Jurisdiction**: Coimbatore Permanent Way, Rails, Sleepers, Ballast and Clearance Envelope

4. **Railway Protection Force (RPF Post In-Charge)**:
   - **Name**: Inspector R. Vijayakumar
   - **Designation**: RPF Post Commander
   - **Email**: `rpf.cbe@sr.railnet.gov.in`
   - **Phone**: +91 422 2302244
   - **Jurisdiction**: Track trespassing security and trespass eviction

---

### 2.2 Salem Division (Erode Section)
- **Station**: Erode Junction (Station Code: ED)
- **GPS Coordinates**: 11.3410° N, 77.7172° E
- **Officer In-Charge**: P. Murugesan
- **Designation**: Station Director & Emergency Incident Commander
- **Email**: `sd.erode@sr.railnet.gov.in`
- **Phone**: +91 424 2256100
- **Track Engineer**: D. Balachander (SSE P-Way, `sse.pway.ed@sr.railnet.gov.in`, +91 94432 55680)
- **Jurisdiction**: Erode Railway Yard, Kaveri River Railway Bridge, Chittsari Section

---

### 2.3 Salem Division (Tiruppur Section)
- **Station**: Tiruppur Railway Station (Station Code: TUP)
- **GPS Coordinates**: 11.1085° N, 77.3411° E
- **Officer In-Charge**: S. Anand
- **Designation**: Station Superintendent In-Charge
- **Email**: `ss.tiruppur@sr.railnet.gov.in`
- **Phone**: +91 421 2200234
- **Jurisdiction**: Tiruppur - Vanjipalayam - Uthukuli High-Speed Corridor

---

### 2.4 Palakkad Division (Walayar - Madukkarai Wildlife & Elephant Corridor)
- **Station**: Palakkad Junction (Station Code: PGT) / Walayar (Station Code: WRA)
- **GPS Coordinates**: 10.7867° N, 76.6548° E
- **Officer In-Charge**: V. Gopakumar
- **Designation**: Divisional Safety Officer & Wildlife Corridor Coordinator
- **Email**: `dso.palakkad@sr.railnet.gov.in`
- **Phone**: +91 491 2555231
- **Field Station Master**: C. Rajesh (`sm.walayar@sr.railnet.gov.in`, +91 491 2862300)
- **Special Jurisdiction**: Ghat section between Palakkad, Walayar and Madukkarai known for elephant track crossings. Emergency alerts require instant alert to loco pilots and forest ranger task forces.

---

### 2.5 Chennai Division & Zonal Headquarters Escalation
- **Station**: Chennai Central (Station Code: MAS)
- **Officer In-Charge**: Chief Traction & Safety Controller
- **Email**: `control.chennai@sr.railnet.gov.in`
- **Phone**: +91 44 25353545
- **Zonal Disaster Management**: Principal Chief Safety Officer (PCSO), Southern Railway (`pcso@sr.railnet.gov.in`, +91 44 25353123)

---

## 3. Automated Emergency Alert Escalation Protocol
1. **Danger Zone Penetration**: Whenever any tracked entity enters the designated Danger Zone polygon, the RAG agent identifies the nearest station and matching In-Charge Officer.
2. **Immediate Email Dispatch**: The notification service transmits high-priority SMTP alert emails to the retrieved In-Charge Authority's email address (for Coimbatore: `rishe8080s@gmail.com`).
3. **Information Included**:
   - Location name and GPS latitude/longitude coordinates
   - Nearest station and railway division
   - Obstruction category, count, and confidence level
   - Approaching train details: train number, name, distance, speed, and calculated Time-To-Impact (TTI)
   - Photographic evidence frame with annotated ROI bounding boxes and zone polygons.
