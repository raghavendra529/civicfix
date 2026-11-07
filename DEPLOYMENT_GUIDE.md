# CivicFix: Complete Production Deployment Guide

This guide provides step-by-step instructions to deploy the **CivicFix Municipal Infrastructure Platform** to cloud hosting platforms for free or on production cloud servers.

---

## Pre-Flight Checklist

The project includes all required cloud deployment assets:
- [`wsgi.py`](file:///c:/Users/kamma/OneDrive/Documents/Akhilesh%20project/wsgi.py) — Production WSGI entry point
- [`requirements.txt`](file:///c:/Users/kamma/OneDrive/Documents/Akhilesh%20project/requirements.txt) — Python dependencies
- [`Procfile`](file:///c:/Users/kamma/OneDrive/Documents/Akhilesh%20project/Procfile) — Process runner for PaaS platforms (Render, Railway, Heroku)
- [`Dockerfile`](file:///c:/Users/kamma/OneDrive/Documents/Akhilesh%20project/Dockerfile) & [`.dockerignore`](file:///c:/Users/kamma/OneDrive/Documents/Akhilesh%20project/.dockerignore) — Containerized deployment
- [`render.yaml`](file:///c:/Users/kamma/OneDrive/Documents/Akhilesh%20project/render.yaml) — 1-click Render blueprint

---

## Method 1: Render.com (Recommended — 100% Free & Simplest)

Render provides free hosting for Python web apps with automatic HTTPS and continuous deployment from GitHub.

### Step 1: Push Code to GitHub
1. Open terminal in the project directory:
   ```bash
   cd "c:\Users\kamma\OneDrive\Documents\Akhilesh project"
   git init
   git add .
   git commit -m "CivicFix production release"
   ```
2. Create a new repository on [GitHub](https://github.com/new) (e.g. `civicfix-infrastructure`).
3. Link and push your repository:
   ```bash
   git remote add origin https://github.com/<YOUR_USERNAME>/civicfix-infrastructure.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render
1. Go to [https://dashboard.render.com](https://dashboard.render.com) and sign in with GitHub.
2. Click **New +** $\to$ **Web Service**.
3. Select your GitHub repository (`civicfix-infrastructure`).
4. Configure the settings:
   - **Name**: `civicfix` (or any custom name)
   - **Region**: Closest to you (e.g., Singapore, Oregon, Frankfurt)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --workers 2 --bind 0.0.0.0:$PORT wsgi:app`
   - **Instance Type**: **Free**
5. *(Optional)* Add Environment Variables under **Environment**:
   - `SMTP_USER` = your Gmail address
   - `SMTP_PASSWORD` = your 16-character Google App Password
6. Click **Deploy Web Service**.
7. In ~2 minutes, your live public URL will be ready: `https://civicfix.onrender.com`.

---

## Method 2: Railway.app (Instant Deployment)

Railway provides 1-click zero-config deployment.

1. Go to [https://railway.app](https://railway.app) and sign in with GitHub.
2. Click **New Project** $\to$ **Deploy from GitHub repo**.
3. Select `civicfix-infrastructure`.
4. Railway automatically reads the [`Procfile`](file:///c:/Users/kamma/OneDrive/Documents/Akhilesh%20project/Procfile) and starts the Gunicorn server.
5. In your project settings, click **Generate Domain** to get a public URL (e.g., `civicfix-production.up.railway.app`).

---

## Method 3: Docker Container (Any Cloud VPS / AWS / GCP / Azure)

If deploying to your own Linux server (Ubuntu/Debian) or AWS EC2, DigitalOcean Droplet, Linode, or Google Cloud Run:

### 1. Build the Docker Image
```bash
docker build -t civicfix:latest .
```

### 2. Run the Container
```bash
docker run -d -p 5000:5000 \
  --name civicfix-app \
  --restart unless-stopped \
  -e SMTP_USER="yourname@gmail.com" \
  -e SMTP_PASSWORD="xxxx xxxx xxxx xxxx" \
  civicfix:latest
```
Access your app at `http://<SERVER_IP>:5000`.

### 3. Google Cloud Run (Serverless)
```bash
gcloud builds submit --tag gcr.io/<PROJECT_ID>/civicfix
gcloud run deploy civicfix --image gcr.io/<PROJECT_ID>/civicfix --platform managed --allow-unauthenticated
```

---

## Method 4: PythonAnywhere (Dedicated Free Python Host)

1. Sign up at [https://www.pythonanywhere.com](https://www.pythonanywhere.com).
2. Go to the **Consoles** tab and open a **Bash Console**:
   ```bash
   git clone https://github.com/<YOUR_USERNAME>/civicfix-infrastructure.git
   cd civicfix-infrastructure
   pip install --user -r requirements.txt
   ```
3. Go to the **Web** tab:
   - Click **Add a new web app** $\to$ Select **Manual configuration (Python 3.11)**.
   - Set **Source code directory**: `/home/<username>/civicfix-infrastructure`
   - Set **Working directory**: `/home/<username>/civicfix-infrastructure`
4. Edit the **WSGI configuration file** (link provided on the Web tab) and set:
   ```python
   import sys
   from pathlib import Path

   project_home = Path("/home/<username>/civicfix-infrastructure")
   if project_home not in sys.path:
       sys.path.insert(0, str(project_home))
       sys.path.insert(0, str(project_home / "backend"))
       sys.path.insert(0, str(project_home / "machine_learning" / "src"))

   from app import app as application
   from database import init_db
   init_db()
   ```
5. Click **Reload <username>.pythonanywhere.com**. Your app is live!

---

## Environment Variables Reference

| Variable | Required | Description | Example |
|---|---|---|---|
| `PORT` | Auto-set by host | HTTP Port the server binds to | `5000` or `10000` |
| `NO_BROWSER` | Auto in cloud | Suppresses browser launch thread | `1` |
| `SMTP_SERVER` | Optional | Outgoing SMTP mail server | `smtp.gmail.com` |
| `SMTP_PORT` | Optional | Outgoing SMTP TLS port | `587` |
| `SMTP_USER` | Optional | Gmail sender address for OTP codes | `yourname@gmail.com` |
| `SMTP_PASSWORD` | Optional | 16-character Google App Password | `abcd efgh ijkl mnop` |
| `TWILIO_ACCOUNT_SID` | Optional | Twilio Account SID for phone SMS | `AC...` |
| `TWILIO_AUTH_TOKEN` | Optional | Twilio Auth Token for phone SMS | `...` |

---

## Post-Deployment Verification

Once deployed, verify:
1. **Health Check**: Visit `https://<YOUR_APP_URL>/api/health` — should return HTTP 200 with model status.
2. **Landing Page**: Visit `https://<YOUR_APP_URL>/` — verify metrics load.
3. **Report Issue**: Upload an image on `/report.html` and verify AI prediction.
4. **Admin Queue**: Check `/admin.html` to confirm status updates persist.
