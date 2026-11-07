"""
CivicFix Authentication & Email/SMS Verification Engine
=======================================================
Provides robust authentication:
- PBKDF2-HMAC-SHA256 password hashing with cryptographic salts
- 6-digit Email One-Time Passcode (OTP) verification
- 6-digit SMS Mobile Passcode (OTP) verification with Country Codes (+65, +91, etc.)
- Token-based session management
- Real SMTP email dispatch (Gmail, Outlook, etc.) with automatic .env synchronization
"""

import os
import secrets
import hashlib
import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"


def load_env_config():
    """Dynamically reloads .env configuration file."""
    if ENV_PATH.exists():
        try:
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        os.environ[k] = v
        except Exception as e:
            print(f"[Auth Engine] Warning: Could not read .env: {e}")

load_env_config()


def save_smtp_credentials(gmail_address: str, app_password: str) -> dict:
    """
    Tests and saves Gmail SMTP credentials to .env file.
    """
    cleaned_pwd = app_password.replace(" ", "").strip()
    cleaned_email = gmail_address.strip().lower()

    # Test connection to Google SMTP
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(cleaned_email, cleaned_pwd)
        server.quit()
    except Exception as e:
        return {
            "success": False,
            "error": f"Google SMTP authentication failed: {str(e)}. Please ensure 2-Step Verification is ON and you generated a 16-character App Password at https://myaccount.google.com/apppasswords"
        }

    # Write to .env
    lines = []
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

    updated_user = False
    updated_pwd = False
    updated_from = False

    new_lines = []
    for line in lines:
        if line.startswith("SMTP_USER="):
            new_lines.append(f"SMTP_USER={cleaned_email}\n")
            updated_user = True
        elif line.startswith("SMTP_PASSWORD="):
            new_lines.append(f"SMTP_PASSWORD={cleaned_pwd}\n")
            updated_pwd = True
        elif line.startswith("SMTP_FROM="):
            new_lines.append(f"SMTP_FROM=CivicFix Platform <{cleaned_email}>\n")
            updated_from = True
        else:
            new_lines.append(line)

    if not updated_user:
        new_lines.append(f"SMTP_USER={cleaned_email}\n")
    if not updated_pwd:
        new_lines.append(f"SMTP_PASSWORD={cleaned_pwd}\n")
    if not updated_from:
        new_lines.append(f"SMTP_FROM=CivicFix Platform <{cleaned_email}>\n")

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    # Reload into runtime
    os.environ["SMTP_USER"] = cleaned_email
    os.environ["SMTP_PASSWORD"] = cleaned_pwd
    os.environ["SMTP_FROM"] = f"CivicFix Platform <{cleaned_email}>"
    os.environ["SMTP_SERVER"] = "smtp.gmail.com"
    os.environ["SMTP_PORT"] = "587"

    print(f"[Auth Engine] Gmail credentials successfully verified and saved to {ENV_PATH}")
    return {"success": True, "email": cleaned_email}


def get_smtp_config():
    load_env_config()
    server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", 587))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    from_addr = os.environ.get("SMTP_FROM", f"CivicFix Verification <{user}>" if user else "CivicFix <noreply@civicfix.gov>")
    return server, port, user, password, from_addr


COUNTRY_CODES = [
    {"code": "+65", "country": "Singapore", "flag": "🇸🇬"},
    {"code": "+91", "country": "India", "flag": "🇮🇳"},
    {"code": "+1", "country": "USA / Canada", "flag": "🇺🇸"},
    {"code": "+44", "country": "United Kingdom", "flag": "🇬🇧"},
    {"code": "+61", "country": "Australia", "flag": "🇦🇺"},
    {"code": "+971", "country": "UAE", "flag": "🇦🇪"},
    {"code": "+60", "country": "Malaysia", "flag": "🇲🇾"},
    {"code": "+81", "country": "Japan", "flag": "🇯🇵"},
    {"code": "+49", "country": "Germany", "flag": "🇩🇪"}
]


def hash_password(password: str, salt: str = None) -> tuple:
    if not salt:
        salt = secrets.token_hex(16)
    pwd_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100000)
    return key.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    pwd_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100000)
    return secrets.compare_digest(key.hex(), stored_hash)


def generate_otp() -> str:
    return f"{secrets.randbelow(900000) + 100000}"


def generate_token() -> str:
    return secrets.token_hex(32)


def dispatch_email_otp(to_email: str, recipient_name: str, otp_code: str) -> dict:
    """
    Dispatches 6-digit verification code.
    If Gmail credentials configured: Sends directly to recipient inbox.
    If not configured: Returns metadata indicating configuration needed.
    """
    subject = f"Your CivicFix Verification Code is {otp_code}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px;">
        <div style="max-width: 520px; margin: 20px auto; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #2563eb; font-size: 26px; font-weight: 800; margin: 0; letter-spacing: -0.5px;">Civic<span style="color: #0f172a;">Fix</span></h1>
                <p style="color: #64748b; font-size: 13px; margin: 4px 0 0 0;">Intelligent Municipal Infrastructure Platform</p>
            </div>
            
            <p style="font-size: 15px; color: #1e293b; margin-bottom: 12px;">Hello <b>{recipient_name}</b>,</p>
            <p style="font-size: 14px; color: #475569; line-height: 1.6; margin-bottom: 24px;">
                You requested a secure one-time verification passcode to access your CivicFix account. Use the 6-digit code below:
            </p>
            
            <div style="text-align: center; margin: 28px 0; background: #eff6ff; padding: 20px; border-radius: 12px; border: 2px dashed #3b82f6;">
                <span style="font-family: monospace, Courier, monospace; font-size: 38px; font-weight: 800; letter-spacing: 8px; color: #1e40af;">
                    {otp_code}
                </span>
            </div>
            
            <p style="font-size: 12px; color: #64748b; text-align: center; line-height: 1.5;">
                This code is valid for <b>10 minutes</b>. If you did not make this request, you can safely ignore this email.
            </p>
            
            <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 28px 0 16px 0;" />
            <p style="font-size: 11px; color: #94a3b8; text-align: center; margin: 0;">
                CivicFix Municipal Governance Security System &copy; 2026.
            </p>
        </div>
    </body>
    </html>
    """

    smtp_server, smtp_port, smtp_user, smtp_password, smtp_from = get_smtp_config()

    if smtp_user and smtp_password:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_from
            msg["To"] = to_email
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(smtp_server, smtp_port, timeout=12) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_from, [to_email], msg.as_string())

            print(f"[Auth Engine] Real email successfully sent via Gmail SMTP to {to_email}!")
            return {
                "delivered": True,
                "configured": True,
                "method": "smtp",
                "message": f"Verification code has been sent directly to {to_email}. Please check your inbox."
            }
        except Exception as e:
            print(f"[Auth Engine] SMTP send failed: {e}")
            return {
                "delivered": False,
                "configured": True,
                "method": "smtp_error",
                "otp_code": otp_code,
                "error": str(e),
                "message": f"Email sending failed ({str(e)}). Please verify your Gmail App Password."
            }

    # If SMTP is not yet configured
    print("=" * 60)
    print(f"[CIVICFIX NOTICE: SMTP NOT CONFIGURED IN .ENV]")
    print(f"Target Email: {to_email}")
    print(f"Passcode: >>> {otp_code} <<< (Valid for 10 mins)")
    print(f"To deliver live emails to Gmail inboxes, set SMTP_USER and SMTP_PASSWORD in .env")
    print("=" * 60)

    return {
        "delivered": False,
        "configured": False,
        "method": "unconfigured",
        "otp_code": otp_code,
        "message": "Gmail SMTP is not configured yet. Configure your Gmail sender to deliver live emails, or use the dev passcode below."
    }


def dispatch_sms_otp(to_phone: str, otp_code: str) -> dict:
    """Dispatches SMS or returns status."""
    sms_text = f"[CivicFix] Your infrastructure verification code is: {otp_code}. Valid for 10 mins."
    
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    twilio_from = os.environ.get("TWILIO_PHONE_NUMBER", "")

    if twilio_sid and twilio_token and twilio_from:
        try:
            from urllib.parse import urlencode
            import urllib.request
            import base64

            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            clean_dest = to_phone.replace(" ", "")
            post_data = urlencode({"To": clean_dest, "From": twilio_from, "Body": sms_text}).encode("utf-8")
            req = urllib.request.Request(url, data=post_data, method="POST")
            auth_str = base64.b64encode(f"{twilio_sid}:{twilio_token}".encode("utf-8")).decode("ascii")
            req.add_header("Authorization", f"Basic {auth_str}")

            with urllib.request.urlopen(req, timeout=8) as resp:
                print(f"[Auth Engine] Real Twilio SMS dispatched to {to_phone}")
                return {"delivered": True, "configured": True, "method": "twilio", "message": f"SMS OTP dispatched to {to_phone}"}
        except Exception as e:
            print(f"[Auth Engine] Twilio SMS dispatch failed ({e})")

    print("=" * 60)
    print(f"[CIVICFIX NOTICE: SMS GATEWAY NOT CONFIGURED]")
    print(f"Target Phone: {to_phone}")
    print(f"Passcode: >>> {otp_code} <<< (Valid for 10 mins)")
    print("=" * 60)

    return {
        "delivered": False,
        "configured": False,
        "method": "unconfigured",
        "otp_code": otp_code,
        "message": f"SMS gateway is not configured. Use the dev passcode below for testing."
    }
