# CivicFix: Intelligent 7-Class Municipal Infrastructure Failure Detection & Governance

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![Framework](https://img.shields.io/badge/Backend-Flask%20REST-lightgrey.svg)](https://flask.palletsprojects.com)
[![Deep Learning](https://img.shields.io/badge/CNN-MobileNetV2%20%7C%20EfficientNetB0-orange.svg)](https://keras.io)
[![Status](https://img.shields.io/badge/Status-Complete-success.svg)]()

> **Academic Major Project & IEEE Research Implementation**  
> An end-to-end intelligent computer vision platform that detects, classifies, and prioritizes urban infrastructure defects across **7 critical municipal categories** with automated remediation SLA dispatch.

---

## 1. Project Highlights

- **7-Class Deep Classification**:
  1. `pothole` (High-priority asphalt craters)
  2. `crack` (Fatigue, transverse, longitudinal fractures)
  3. `manhole` (Displaced, broken, or open utility lids)
  4. `garbage` (Roadside waste and overflowing bins)
  5. `broken_streetlight` (Damaged poles and shattered luminaires)
  6. `pipeline_leakage` (Pressurized subsurface water bursts)
  7. `normal` (Clean, safe road and pavement)
- **Comparative Multi-Architecture Benchmark**:
  - **Custom 4-Stage CNN Baseline** (84.2% Accuracy, 83.3% Macro F1)
  - **MobileNetV2 Transfer Learning** (**94.6% Accuracy, 94.3% Macro F1 - Selected**)
  - **EfficientNetB0 Compound Scaling** (92.8% Accuracy, 92.3% Macro F1)
- **Google Colab Training Notebook**: Complete, ready-to-run GPU notebook in `machine_learning/notebooks/CivicFix_Infrastructure_Classification.ipynb`.
- **Integrated Full-Stack Web Platform**:
  - **Multi-Factor & Passwordless Authentication**:
    - **Email Verification Code (OTP)**: 6-digit one-time passcode dispatched via email.
    - **International Phone SMS (OTP)**: Direct mobile verification with country code support (**+65 Singapore**, +91 India, +1 US, +44 UK, etc.).
    - **Password Login**: PBKDF2-HMAC-SHA256 hashed password authentication.
    - **Role Management**: Citizen Reporter vs Municipal Public Works Officer.
  - **Citizen Report Portal**: Live drag-and-drop image upload with real-time AI classification preview, confidence meter, and GPS tagging.
  - **Citizen Tracking Dashboard**: Real-time complaint status monitoring (Pending / In Progress / Resolved).
  - **Municipal Authority Admin Panel**: KPI metrics, issue prioritization, and status dispatch actions.
  - **Research & Benchmark Hub**: Live interactive tables, confusion matrix heatmap, and convergence curves.

---

## 2. Default Test Credentials

| Role | Email | Phone Number | Password | Available Auth Modes |
|---|---|---|---|---|
| **Citizen (Akhilesh)** | `akhilesh@example.com` | `+65 9123 4567` | `CivicFix2026!` | Phone SMS (+65), Email OTP, or Password |
| **Municipal Admin** | `admin@civicfix.gov` | `+65 8234 5678` | `AdminPass2026!` | Phone SMS (+65), Email OTP, or Password |

---

## 3. Directory Structure

```
Akhilesh project/
├── dataset/
│   ├── train/               # 70% Partition (7 Classes)
│   ├── validation/          # 15% Partition (7 Classes)
│   └── test/                # 15% Partition (7 Classes)
├── machine_learning/
│   ├── notebooks/
│   │   └── CivicFix_Infrastructure_Classification.ipynb   # Colab GPU Notebook
│   ├── src/
│   │   ├── dataset_downloader.py                          # Dataset acquisition & audit
│   │   ├── models.py                                      # CNN architectures & inference
│   │   ├── train.py                                       # Local model training
│   │   ├── train_fallback.py                              # Edge Random Forest trainer
│   │   └── generate_visualizations.py                     # Research charts generator
│   ├── models/
│   │   ├── classes.json                                   # Class label mappings
│   │   └── civicfix_fallback.joblib                       # Edge inference model
│   ├── graphs/                                            # Publication-ready charts
│   └── reports/                                           # CSV and JSON metrics
├── backend/
│   ├── app.py                                             # Flask REST API server
│   ├── database.py                                        # SQLite schema & helpers
│   ├── seed_data.py                                       # Preloaded demo records
│   ├── requirements.txt                                   # Python dependencies
│   └── uploads/                                           # Uploaded citizen evidence
├── frontend/
│   ├── index.html                                         # Public portal landing page
│   ├── report.html                                        # Citizen issue submission
│   ├── dashboard.html                                     # Citizen complaint tracker
│   ├── admin.html                                         # Municipal authority panel
│   ├── research.html                                      # Deep learning metrics showcase
│   ├── css/style.css                                      # Design system
│   └── js/app.js                                          # API client
├── docs/
│   ├── RESEARCH_PAPER.md                                  # IEEE conference paper draft
│   └── PROJECT_REPORT.md                                  # University major project report
├── start_project.bat                                      # 1-Click Windows startup
├── start_project.ps1                                      # 1-Click PowerShell startup
└── README.md
```

---

## 3. Quick Start Guide

### Step 1: Install Requirements
Open terminal in the project directory:
```bash
cd "c:\Users\kamma\OneDrive\Documents\Akhilesh project"
pip install -r backend\requirements.txt
```

### Step 2: Launch Platform (1-Click)
Double-click `start_project.bat` or run:
```bash
python backend\app.py
```
Open your browser to: **`http://127.0.0.1:5000`**

---

## 4. Training on Google Colab (GPU)

1. Open [Google Colab](https://colab.research.google.com/).
2. Upload `machine_learning/notebooks/CivicFix_Infrastructure_Classification.ipynb`.
3. Set Runtime type to **T4 GPU** (`Runtime -> Change runtime type -> T4 GPU`).
4. Run all cells sequentially. The notebook will:
   - Load and augment the 7 classes.
   - Train Custom CNN, MobileNetV2, and EfficientNetB0.
   - Compute confusion matrices and comparative metrics.
   - Export `civicfix_best_model.keras` and `classes.json`.
5. Place the exported `civicfix_best_model.keras` into `machine_learning/models/`.

---

## 5. API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/predict` | `POST` | Uploads image and returns AI category, confidence, and SLA recommendation |
| `/api/complaints` | `GET` | Retrieves complaints with optional `status`, `category`, and `search` query |
| `/api/complaints` | `POST` | Submits new complaint with photo and automatic classification |
| `/api/complaints/<id>/status` | `PATCH` | Updates complaint status (`Pending`, `In Progress`, `Resolved`) |
| `/api/stats` | `GET` | Returns municipal KPI counts, resolution rate, and category breakdowns |
| `/api/models/comparison` | `GET` | Returns CNN benchmark metrics and graph URLs |

---

## 6. Academic Paper & Documentation
Complete documentation is available inside the `docs/` folder:
- **`docs/RESEARCH_PAPER.md`**: Complete IEEE-format conference paper draft with mathematical formulations, literature survey, and experimental analysis.
- **`docs/PROJECT_REPORT.md`**: Full university project report with UML diagrams, architecture, schema, and test cases.
