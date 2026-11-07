"""
CivicFix Database Seeder
========================
Populates the database with:
1. Initial Citizen & Municipal Admin Users (with hashed passwords)
2. Realistic civic complaint records across all 7 infrastructure categories
"""

import shutil
from pathlib import Path
from database import get_connection, init_db
from auth import hash_password

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "backend" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
DATASET_DIR = BASE_DIR / "dataset" / "test"

DEMO_USERS = [
    {
        "name": "Akhilesh Kamma",
        "email": "akhilesh@example.com",
        "phone": "+65 9123 4567",
        "password": "CivicFix2026!",
        "role": "citizen"
    },
    {
        "name": "Municipal Officer Kamma",
        "email": "admin@civicfix.gov",
        "phone": "+65 8234 5678",
        "password": "AdminPass2026!",
        "role": "admin"
    }
]

DEMO_COMPLAINTS = [
    {
        "user_name": "Akhilesh Kamma",
        "user_email": "akhilesh@example.com",
        "title": "Hazardous Deep Asphalt Pothole near Metro Station",
        "description": "Deep crater formed after heavy rain, posing immediate risk to two-wheelers during rush hour.",
        "category": "pothole",
        "confidence": 0.974,
        "priority": "P1 - High",
        "recommendation": "Immediate road patch required. Dispatch municipal asphalt crew within 24h.",
        "image_source_cls": "pothole",
        "latitude": 17.4435,
        "longitude": 78.3882,
        "address": "Madhapur Main Rd, Near Hitec Metro Station, Hyderabad",
        "status": "In Progress"
    },
    {
        "user_name": "Priya Sharma",
        "user_email": "priya.s@example.com",
        "title": "Severe Water Main Rupture with Roadside Pooling",
        "description": "Clean drinking water bursting through bitumen layer and flooding the left lane.",
        "category": "pipeline_leakage",
        "confidence": 0.985,
        "priority": "P1 - Critical",
        "recommendation": "Water main pressure drop risk. Alert municipal water board dispatch immediately.",
        "image_source_cls": "pipeline_leakage",
        "latitude": 17.4399,
        "longitude": 78.3912,
        "address": "Kavuri Hills Phase 2, Pillar 104, Hyderabad",
        "status": "Pending"
    },
    {
        "user_name": "Rahul Verma",
        "user_email": "rahul.v@example.com",
        "title": "Damaged Dislodged Stormwater Manhole Lid",
        "description": "Cast iron cover is cracked in half with an open opening dangerous for pedestrians.",
        "category": "manhole",
        "confidence": 0.962,
        "priority": "P1 - Urgent",
        "recommendation": "Extreme safety hazard. Place caution bollards and reseat/replace manhole cover within 12h.",
        "image_source_cls": "manhole",
        "latitude": 17.4371,
        "longitude": 78.3845,
        "address": "Ayyappa Society 100ft Road, Opp. SBI, Hyderabad",
        "status": "Resolved"
    },
    {
        "user_name": "Siddharth Rao",
        "user_email": "sid.rao@example.com",
        "title": "Tilted Street Light Pole with Shattered Luminaire",
        "description": "Vehicle collision damaged pole base; hanging fixture with loose electrical wire.",
        "category": "broken_streetlight",
        "confidence": 0.951,
        "priority": "P2 - High",
        "recommendation": "Pedestrian security risk. Replace damaged lamp luminaire and inspect wiring within 48h.",
        "image_source_cls": "broken_streetlight",
        "latitude": 17.4478,
        "longitude": 78.3761,
        "address": "Cyber Towers Junction, Lane 3, Hyderabad",
        "status": "In Progress"
    },
    {
        "user_name": "Ananya Reddy",
        "user_email": "ananya.r@example.com",
        "title": "Overflowing Sidewalk Garbage Heap & Litter",
        "description": "Municipal dustbin has spilled over onto the walkway blocking pedestrian movement.",
        "category": "garbage",
        "confidence": 0.943,
        "priority": "P3 - Medium",
        "recommendation": "Sanitation notice. Route solid waste collection vehicle within 3 business days.",
        "image_source_cls": "garbage",
        "latitude": 17.4412,
        "longitude": 78.3899,
        "address": "Gachibowli Stadium Road, Near Gate 4, Hyderabad",
        "status": "Pending"
    },
    {
        "user_name": "Karthik Nair",
        "user_email": "karthik.n@example.com",
        "title": "Extensive Alligator Fatigue Cracking on Flyover Ascent",
        "description": "Interconnected surface fatigue cracking across the flyover approach ramp.",
        "category": "crack",
        "confidence": 0.938,
        "priority": "P3 - Routine",
        "recommendation": "Preventive road care. Schedule crack sealing during scheduled quarter resurfacing.",
        "image_source_cls": "crack",
        "latitude": 17.4320,
        "longitude": 78.3734,
        "address": "Biodiversity Junction Flyover, Gachibowli, Hyderabad",
        "status": "Pending"
    },
    {
        "user_name": "Meera Joshi",
        "user_email": "meera.j@example.com",
        "title": "Routine Road Survey Inspection - No Defects Found",
        "description": "Newly laid asphalt road inspected post-monsoon. Surface smooth and well marked.",
        "category": "normal",
        "confidence": 0.989,
        "priority": "P4 - Low",
        "recommendation": "No infrastructure defect detected. Pavement surface within acceptable operating standards.",
        "image_source_cls": "normal",
        "latitude": 17.4450,
        "longitude": 78.3800,
        "address": "Financial District Blvd, WaveRock Campus, Hyderabad",
        "status": "Resolved"
    }
]


def seed_database():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Re-seed users
    for u in DEMO_USERS:
        pwd_hash, salt = hash_password(u["password"])
        cursor.execute("SELECT id FROM users WHERE email = ?", (u["email"],))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
            UPDATE users SET name = ?, phone = ?, password_hash = ?, salt = ?, role = ?, is_verified = 1
            WHERE email = ?
            """, (u["name"], u.get("phone"), pwd_hash, salt, u["role"], u["email"]))
        else:
            cursor.execute("""
            INSERT INTO users (name, email, phone, password_hash, salt, role, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (u["name"], u["email"], u.get("phone"), pwd_hash, salt, u["role"]))

    # Clear complaints and re-seed
    cursor.execute("DELETE FROM complaints")
    cursor.execute("DELETE FROM audit_logs")

    for idx, c in enumerate(DEMO_COMPLAINTS, 1):
        source_cls = c["image_source_cls"]
        src_img = DATASET_DIR / source_cls / f"{source_cls}_0019.jpg"
        target_name = f"seed_{idx}_{source_cls}.jpg"
        dest_path = UPLOADS_DIR / target_name

        if src_img.exists():
            shutil.copy(src_img, dest_path)
        else:
            from PIL import Image
            Image.new("RGB", (224, 224), (100, 100, 100)).save(dest_path)

        cursor.execute("""
        INSERT INTO complaints (
            user_name, user_email, title, description, category,
            confidence, priority, recommendation, image_filename,
            latitude, longitude, address, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c["user_name"], c["user_email"], c["title"], c["description"],
            c["category"], c["confidence"], c["priority"], c["recommendation"],
            target_name, c["latitude"], c["longitude"], c["address"], c["status"]
        ))

    conn.commit()
    conn.close()
    print(f"[Seed] Successfully seeded {len(DEMO_USERS)} users and {len(DEMO_COMPLAINTS)} complaints into database.")


if __name__ == "__main__":
    seed_database()
