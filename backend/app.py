"""
CivicFix REST API & Web Application Server
==========================================
Integrates:
- Email-based Authentication (OTP Magic Code & Password Login)
- Deep Learning Multi-Class Defect Inference Engine
- Citizen Complaint Management & Municipal Admin Dispatch
"""

import os
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_from_directory

# Setup path imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "backend"))
sys.path.append(str(BASE_DIR / "machine_learning" / "src"))

from database import get_connection, init_db
from models import CivicFixPredictor
from auth import (
    hash_password,
    verify_password,
    generate_otp,
    generate_token,
    dispatch_email_otp,
    dispatch_sms_otp,
    save_smtp_credentials,
    get_smtp_config,
    COUNTRY_CODES
)

app = Flask(__name__, static_folder=str(BASE_DIR / "frontend"))
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB max upload

UPLOADS_DIR = BASE_DIR / "backend" / "uploads"
GRAPHS_DIR = BASE_DIR / "machine_learning" / "graphs"
REPORTS_DIR = BASE_DIR / "machine_learning" / "reports"
FRONTEND_DIR = BASE_DIR / "frontend"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize Predictor
print("[CivicFix API] Initializing Deep Learning Predictor...")
predictor = CivicFixPredictor()


# --- CORS Middleware ---
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


# --- Auth Token Helper ---
def get_auth_token_from_request():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    return request.args.get("token") or (request.get_json(silent=True) or {}).get("token")


def get_current_user():
    token = get_auth_token_from_request()
    if not token:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT u.id, u.name, u.email, u.role
    FROM users u
    JOIN auth_tokens t ON u.id = t.user_id
    WHERE t.token = ? AND t.expires_at > datetime('now')
    """, (token,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


# --- Static Routing & Web Pages ---
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def serve_frontend_page(filename):
    file_path = FRONTEND_DIR / filename
    if file_path.exists():
        return send_from_directory(FRONTEND_DIR, filename)
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/uploads/<filename>")
def serve_upload(filename):
    return send_from_directory(UPLOADS_DIR, filename)


@app.route("/graphs/<filename>")
def serve_graph(filename):
    return send_from_directory(GRAPHS_DIR, filename)


# --- REST API: Health ---
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "CivicFix AI Infrastructure API",
        "version": "1.1.0",
        "active_model": predictor.model_name,
        "supported_classes": predictor.classes
    })


# --- REST API: Authentication (Email, Phone & Password) ---

@app.route("/api/auth/smtp-status", methods=["GET"])
def get_smtp_status():
    server, port, user, password, from_addr = get_smtp_config()
    configured = bool(user and password)
    return jsonify({
        "status": "success",
        "configured": configured,
        "sender_email": user if configured else None,
        "server": server,
        "port": port
    })


@app.route("/api/auth/configure-smtp", methods=["POST"])
def configure_smtp():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip().lower()
    app_password = (data.get("app_password") or data.get("password") or "").strip()

    if not email or "@" not in email:
        return jsonify({"error": "Valid Gmail address is required"}), 400
    if not app_password:
        return jsonify({"error": "16-character Google App Password is required"}), 400

    result = save_smtp_credentials(email, app_password)
    if not result.get("success"):
        return jsonify({"error": result.get("error", "SMTP verification failed")}), 400

    return jsonify({
        "status": "success",
        "message": f"Gmail credentials successfully connected! Verification emails will now be sent directly from {email}.",
        "sender_email": email
    })


@app.route("/api/auth/send-otp", methods=["POST"])
def send_otp():
    """
    Sends a 6-digit verification code to the citizen's email for passwordless authentication.
    """
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()

    if not email or "@" not in email:
        return jsonify({"error": "Valid email address is required"}), 400

    otp_code = generate_otp()
    expiry_time = (datetime.utcnow() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if user:
        recipient_name = user["name"]
        cursor.execute("UPDATE users SET otp_code = ?, otp_expiry = ? WHERE id = ?", (otp_code, expiry_time, user["id"]))
    else:
        # Create new unverified citizen account
        recipient_name = name or email.split("@")[0].title()
        cursor.execute("""
        INSERT INTO users (name, email, role, otp_code, otp_expiry, is_verified)
        VALUES (?, ?, 'citizen', ?, ?, 0)
        """, (recipient_name, email, otp_code, expiry_time))

    conn.commit()
    conn.close()

    dispatch_result = dispatch_email_otp(email, recipient_name, otp_code)
    delivered = dispatch_result.get("delivered", False)
    configured = dispatch_result.get("configured", False)

    return jsonify({
        "status": "success",
        "delivered": delivered,
        "configured": configured,
        "method": dispatch_result.get("method", "unconfigured"),
        "dev_otp": otp_code if not delivered else None,
        "message": dispatch_result.get("message", "Verification code dispatched"),
        "email": email
    })


@app.route("/api/auth/verify-otp", methods=["POST"])
def verify_otp():
    """
    Verifies the 6-digit OTP received via email and issues a session token.
    """
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()

    if not email or not otp:
        return jsonify({"error": "Email and 6-digit OTP are required"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, name, email, role, otp_code, otp_expiry
    FROM users WHERE email = ?
    """, (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "No account found with this email"}), 404

    # Verify code and expiry
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    if not user["otp_code"] or user["otp_code"] != otp:
        conn.close()
        return jsonify({"error": "Invalid verification code"}), 400

    if user["otp_expiry"] and user["otp_expiry"] < now_str:
        conn.close()
        return jsonify({"error": "Verification code has expired. Please request a new one."}), 400

    # Issue session token (valid 14 days)
    token = generate_token()
    token_expiry = (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO auth_tokens (token, user_id, expires_at)
    VALUES (?, ?, ?)
    """, (token, user["id"], token_expiry))

    # Mark user verified and clear used OTP
    cursor.execute("""
    UPDATE users SET is_verified = 1, otp_code = NULL, otp_expiry = NULL
    WHERE id = ?
    """, (user["id"],))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Email authenticated successfully",
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    })


@app.route("/api/auth/country-codes", methods=["GET"])
def get_country_codes():
    """Returns list of supported international country calling codes."""
    return jsonify({"country_codes": COUNTRY_CODES})


@app.route("/api/auth/send-phone-otp", methods=["POST"])
def send_phone_otp():
    """
    Dispatches a 6-digit SMS verification code to an international mobile number (e.g. +65 Singapore).
    """
    data = request.get_json(silent=True) or request.form
    country_code = (data.get("country_code") or "+65").strip()
    phone_number = (data.get("phone_number") or data.get("phone") or "").strip()

    if not phone_number:
        return jsonify({"error": "Phone number is required"}), 400

    # Clean phone number (remove dashes, spaces, brackets)
    cleaned_number = "".join(c for c in phone_number if c.isdigit())
    if not country_code.startswith("+"):
        country_code = "+" + country_code
    full_phone = f"{country_code} {cleaned_number}"

    otp_code = generate_otp()
    expiry_time = (datetime.utcnow() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users WHERE phone = ?", (full_phone,))
    user = cursor.fetchone()

    if user:
        cursor.execute("UPDATE users SET phone_otp_code = ?, phone_otp_expiry = ? WHERE id = ?", (otp_code, expiry_time, user["id"]))
    else:
        # Create unverified account linked to this phone
        dummy_email = f"phone_{cleaned_number[-6:]}@civicfix.gov"
        citizen_name = f"Citizen ({country_code} {cleaned_number[-4:]})"
        cursor.execute("""
        INSERT INTO users (name, email, phone, role, phone_otp_code, phone_otp_expiry, is_verified)
        VALUES (?, ?, ?, 'citizen', ?, ?, 0)
        """, (citizen_name, dummy_email, full_phone, otp_code, expiry_time))

    conn.commit()
    conn.close()

    dispatch_res = dispatch_sms_otp(full_phone, otp_code)
    delivered = dispatch_res.get("delivered", False)
    configured = dispatch_res.get("configured", False)

    return jsonify({
        "status": "success",
        "phone": full_phone,
        "delivered": delivered,
        "configured": configured,
        "method": dispatch_res.get("method", "unconfigured"),
        "dev_otp": otp_code if not delivered else None,
        "message": dispatch_res.get("message", "SMS verification code generated")
    })


@app.route("/api/auth/verify-phone-otp", methods=["POST"])
def verify_phone_otp():
    """
    Verifies SMS passcode and signs the citizen into their account.
    """
    data = request.get_json(silent=True) or request.form
    country_code = (data.get("country_code") or "+65").strip()
    phone_number = (data.get("phone_number") or data.get("phone") or "").strip()
    otp = (data.get("otp") or "").strip()

    if not phone_number or not otp:
        return jsonify({"error": "Phone number and 6-digit code are required"}), 400

    cleaned_number = "".join(c for c in phone_number if c.isdigit())
    if not country_code.startswith("+"):
        country_code = "+" + country_code
    full_phone = f"{country_code} {cleaned_number}"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, name, email, phone, role, phone_otp_code, phone_otp_expiry
    FROM users WHERE phone = ?
    """, (full_phone,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "No account associated with this phone number"}), 404

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    if not user["phone_otp_code"] or user["phone_otp_code"] != otp:
        conn.close()
        return jsonify({"error": "Invalid verification code"}), 400

    if user["phone_otp_expiry"] and user["phone_otp_expiry"] < now_str:
        conn.close()
        return jsonify({"error": "Verification code has expired. Please request a new code."}), 400

    token = generate_token()
    token_expiry = (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO auth_tokens (token, user_id, expires_at)
    VALUES (?, ?, ?)
    """, (token, user["id"], token_expiry))

    cursor.execute("""
    UPDATE users SET is_verified = 1, phone_otp_code = NULL, phone_otp_expiry = NULL
    WHERE id = ?
    """, (user["id"],))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Phone number verified successfully",
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"],
            "role": user["role"]
        }
    })


@app.route("/api/auth/login", methods=["POST"])
def password_login():
    """
    Standard email + password login endpoint.
    """
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, name, email, role, password_hash, salt
    FROM users WHERE email = ?
    """, (email,))
    user = cursor.fetchone()

    if not user or not user["password_hash"] or not user["salt"]:
        conn.close()
        return jsonify({"error": "Invalid email or password"}), 401

    if not verify_password(password, user["password_hash"], user["salt"]):
        conn.close()
        return jsonify({"error": "Invalid email or password"}), 401

    token = generate_token()
    token_expiry = (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO auth_tokens (token, user_id, expires_at)
    VALUES (?, ?, ?)
    """, (token, user["id"], token_expiry))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    })


@app.route("/api/auth/register", methods=["POST"])
def register():
    """
    Registers a new citizen account with email and password.
    """
    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role", "citizen")

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    pwd_hash, salt = hash_password(password)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "An account with this email already exists"}), 409

    cursor.execute("""
    INSERT INTO users (name, email, password_hash, salt, role, is_verified)
    VALUES (?, ?, ?, ?, ?, 1)
    """, (name, email, pwd_hash, salt, role))
    user_id = cursor.lastrowid

    token = generate_token()
    token_expiry = (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO auth_tokens (token, user_id, expires_at) VALUES (?, ?, ?)", (token, user_id, token_expiry))
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Account created successfully",
        "token": token,
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "role": role
        }
    }), 201


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    """
    Revokes the current session token.
    """
    token = get_auth_token_from_request()
    if token:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
        conn.commit()
        conn.close()

    return jsonify({"status": "success", "message": "Successfully logged out"})


@app.route("/api/auth/me", methods=["GET"])
def current_user_profile():
    """
    Returns the authenticated user's profile details.
    """
    user = get_current_user()
    if not user:
        return jsonify({"authenticated": False, "user": None}), 200
    return jsonify({"authenticated": True, "user": user})


# --- REST API: AI Prediction ---

@app.route("/api/predict", methods=["POST"])
def predict_image():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided in request (field: 'image')"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename uploaded"}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        return jsonify({"error": "Unsupported image format. Use JPEG, PNG, or WebP."}), 400

    token = uuid.uuid4().hex[:10]
    filename = f"upload_{token}{ext}"
    saved_path = UPLOADS_DIR / filename
    file.save(saved_path)

    try:
        threshold = float(request.form.get("threshold", 0.50))
        result = predictor.predict(saved_path, threshold=threshold)
        result["image_url"] = f"/uploads/{filename}"
        result["filename"] = filename
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


# --- REST API: Complaints Management ---

@app.route("/api/complaints", methods=["GET"])
def get_complaints():
    status_filter = request.args.get("status")
    category_filter = request.args.get("category")
    search_query = request.args.get("search")
    user_email_filter = request.args.get("user_email")
    mine_filter = request.args.get("mine")

    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM complaints WHERE 1=1"
    params = []

    if status_filter and status_filter != "all":
        query += " AND status = ?"
        params.append(status_filter)

    if category_filter and category_filter != "all":
        query += " AND category = ?"
        params.append(category_filter)

    if user_email_filter:
        query += " AND user_email = ?"
        params.append(user_email_filter)

    if mine_filter == "true":
        current_user = get_current_user()
        if current_user:
            query += " AND user_email = ?"
            params.append(current_user["email"])

    if search_query:
        query += " AND (title LIKE ? OR description LIKE ? OR address LIKE ?)"
        like_term = f"%{search_query}%"
        params.extend([like_term, like_term, like_term])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    complaints = [dict(row) for row in rows]
    return jsonify({"count": len(complaints), "complaints": complaints})


@app.route("/api/complaints", methods=["POST"])
def create_complaint():
    # If authenticated, default to current user's profile
    current_user = get_current_user()

    user_name = request.form.get("user_name") or (current_user["name"] if current_user else "Anonymous Citizen")
    user_email = request.form.get("user_email") or (current_user["email"] if current_user else "citizen@civicfix.gov")
    title = request.form.get("title", "Infrastructure Issue")
    description = request.form.get("description", "")
    address = request.form.get("address", "Municipal Roadway")
    latitude = request.form.get("latitude", 17.4400)
    longitude = request.form.get("longitude", 78.3800)
    user_selected_category = request.form.get("category")

    if "image" not in request.files:
        return jsonify({"error": "Complaint requires photographic evidence"}), 400

    file = request.files["image"]
    ext = Path(file.filename).suffix.lower() or ".jpg"
    filename = f"issue_{uuid.uuid4().hex[:10]}{ext}"
    save_path = UPLOADS_DIR / filename
    file.save(save_path)

    # Run AI Prediction
    prediction = predictor.predict(save_path)
    ai_category = prediction["category"]
    confidence = prediction["confidence"]
    priority = prediction["priority"]
    recommendation = prediction["recommendation"]

    final_category = user_selected_category if user_selected_category and user_selected_category in predictor.classes else ai_category

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO complaints (
        user_name, user_email, title, description, category,
        confidence, priority, recommendation, image_filename,
        latitude, longitude, address, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
    """, (
        user_name, user_email, title, description, final_category,
        confidence, priority, recommendation, filename,
        float(latitude), float(longitude), address
    ))
    complaint_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Complaint successfully registered with municipal authority.",
        "complaint_id": complaint_id,
        "ai_prediction": {
            "predicted_category": ai_category,
            "final_category": final_category,
            "confidence": confidence,
            "priority": priority,
            "recommendation": recommendation,
            "image_url": f"/uploads/{filename}"
        }
    }), 201


@app.route("/api/complaints/<int:complaint_id>/status", methods=["PATCH"])
def update_complaint_status(complaint_id):
    current_user = get_current_user()
    performed_by = current_user["name"] if current_user else "Admin Authority"

    data = request.get_json(silent=True) or request.form
    new_status = data.get("status")

    if new_status not in ["Pending", "In Progress", "Resolved"]:
        return jsonify({"error": "Status must be 'Pending', 'In Progress', or 'Resolved'"}), 400

    resolved_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") if new_status == "Resolved" else None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE complaints
    SET status = ?, resolved_at = COALESCE(?, resolved_at)
    WHERE id = ?
    """, (new_status, resolved_at, complaint_id))

    cursor.execute("""
    INSERT INTO audit_logs (complaint_id, action, performed_by)
    VALUES (?, ?, ?)
    """, (complaint_id, f"Status updated to '{new_status}'", performed_by))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "complaint_id": complaint_id,
        "new_status": new_status,
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route("/api/stats", methods=["GET"])
def get_dashboard_statistics():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM complaints")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'")
    in_progress = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'")
    resolved = cursor.fetchone()[0]

    cursor.execute("SELECT category, COUNT(*) FROM complaints GROUP BY category")
    by_category = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT priority, COUNT(*) FROM complaints GROUP BY priority")
    by_priority = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    return jsonify({
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "resolution_rate": round((resolved / total * 100) if total > 0 else 0, 1),
        "by_category": by_category,
        "by_priority": by_priority,
        "model_in_service": predictor.model_name
    })


@app.route("/api/models/comparison", methods=["GET"])
def get_model_comparison():
    report_file = REPORTS_DIR / "model_comparison.json"
    per_class_file = REPORTS_DIR / "per_class_classification_report.json"

    models_data = []
    if report_file.exists():
        with open(report_file) as f:
            models_data = json.load(f)

    per_class_data = {}
    if per_class_file.exists():
        with open(per_class_file) as f:
            per_class_data = json.load(f)

    return jsonify({
        "models": models_data,
        "best_model": "MobileNetV2",
        "best_macro_f1": 0.943,
        "per_class_metrics": per_class_data,
        "graphs": {
            "dataset_distribution": "/graphs/dataset_distribution.png",
            "training_curves": "/graphs/training_validation_curves.png",
            "confusion_matrix": "/graphs/confusion_matrix.png",
            "model_comparison": "/graphs/model_comparison.png"
        }
    })


if __name__ == "__main__":
    init_db()
    print("=" * 65)
    print("CIVICFIX MUNICIPAL INFRASTRUCTURE PLATFORM")
    print("Web Dashboard & REST API: http://127.0.0.1:5000")
    print("=" * 65)

    import socket
    import time
    import threading
    import webbrowser

    port = int(os.environ.get("PORT", 5000))

    def wait_for_server_and_open_browser(host="127.0.0.1", p=5000, max_attempts=40):
        """Waits until the server is actively listening on port before opening browser."""
        for _ in range(max_attempts):
            time.sleep(0.3)
            try:
                with socket.create_connection((host, p), timeout=0.5):
                    print(f"[CivicFix Launcher] Server ready on http://{host}:{p}. Opening browser...")
                    webbrowser.open(f"http://{host}:{p}")
                    return
            except (OSError, ConnectionRefusedError):
                pass
        webbrowser.open(f"http://{host}:{p}")

    if not os.environ.get("NO_BROWSER") and not os.environ.get("PORT"):
        threading.Thread(target=wait_for_server_and_open_browser, args=("127.0.0.1", port), daemon=True).start()

    app.run(host="0.0.0.0", port=port, debug=False)
