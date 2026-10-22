# NØX — Neural Network Intrusion Detection System
## Module 01, 02 & 03: Preprocessing, Deep Learning, FastAPI Backend & Threat Logging

```
      _   _  ____  __  __
     | \ | |/ __ \ \ \/ /
     |  \| | |  | | \  / 
     | |\  | |__| | /  \ 
     |_| \_|\____/ /_/\_\
  NEURAL INTRUSION DETECTION
```

---

### 1. Project Introduction
**NØX** is a deep-learning-powered Intrusion Detection System (NIDS) designed to identify, classify, and isolate malicious network traffic. Built for enterprise and modern cloud infrastructures, NØX combines high-throughput data preprocessing with multi-layer perceptron (MLP) neural networks, a lightweight FastAPI backend, and an industrial cyberpunk React telemetry dashboard.

- **Module 01**: Dataset Ingestion, Data Hygiene, Feature Encoding, Scaling, Leakage Shielding, and EDA.
- **Module 02**: PyTorch MLP Architecture, Mini-batch Backpropagation, Validation F1 Tracking, Early Stopping, Threshold Tuning, Baseline Comparison, and Neural Prediction Engine.
- **Module 03**: FastAPI REST Backend, Real-Time Flow Classification, Bounded CSV Uploads, Threat Severity Triage, SQLite Event Logging, and Swagger Telemetry API.
- **Module 04**: React Frontend & Opium Cyberpunk Telemetry Dashboard with real-time stats, CSV drag-and-drop detection, distribution analytics, audit event viewer, and system diagnostics.

---

### 2. Module 03 Overview: Backend & Detection Engine
Module 03 bridges the trained PyTorch neural model to local API services and databases:
1. **FastAPI Backend (`backend/api/main.py`)**:
   - High-throughput asynchronous REST API built with FastAPI and Pydantic v2 validation.
   - Singleton ML asset loading during application startup via FastAPI lifespan context manager.
   - CORS restricted to local development origins (`127.0.0.1:3000`, `127.0.0.1:5173`).
2. **Intrusion Detection Engine (`backend/services/detection_service.py`)**:
   - Converts raw flow records directly into 192-dimensional numerical vectors using the fitted Module 01 pipeline.
   - Runs neural inference using `torch.inference_mode()`.
   - Compares sigmoid output against the frozen decision threshold (`0.50`).
3. **Threat Severity Triage (`backend/services/threat_service.py`)**:
   - Categorizes flow alerts into operational tiers: `Normal`, `Low`, `Medium`, and `High`.
4. **SQLite Event Logging (`backend/database/`)**:
   - Parameterized database operations storing detection timestamps, class IDs, attack scores, severity ratings, and source tags (`single`, `batch`, `csv_upload`, `demo`).
5. **Interactive Swagger Documentation**:
   - Available locally at `http://127.0.0.1:8000/docs`.

---

### 3. API Endpoints Reference

| Method | Endpoint | Description | Request Payload | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | System readiness & model status | None | `HealthResponseSchema` |
| `POST` | `/api/detect` | Single flow record classification | JSON flow record | `DetectionResponseSchema` |
| `POST` | `/api/detect/batch` | Batch classification (up to 5,000 flows) | Array of JSON records | List of `DetectionResponseSchema` |
| `POST` | `/api/detect/upload` | Bounded CSV dataset upload | Multipart Form (`file.csv`) | `CSVUploadResponseSchema` |
| `GET` | `/api/stats` | Dashboard telemetry statistics | None | `TelemetryStatsSchema` |
| `GET` | `/api/history` | Paginated threat event logs | Query params (`limit`, `offset`) | List of stored event objects |
| `GET` | `/docs` | Interactive Swagger UI | None | HTML Swagger Interface |

#### Single Record Request Example (`POST /api/detect`):
```json
{
  "dur": 0.05,
  "proto": "tcp",
  "service": "http",
  "state": "FIN",
  "spkts": 10,
  "dpkts": 8,
  "sbytes": 1000,
  "dbytes": 2000,
  "rate": 50.0,
  "sttl": 64,
  "dttl": 128,
  "sload": 1000.0,
  "dload": 2000.0
}
```

#### Response Example:
```json
{
  "prediction": "Potential Attack",
  "class_id": 1,
  "attack_score": 0.9412,
  "threshold": 0.50,
  "severity": "High",
  "model": "NØX-MLP-v1",
  "timestamp": "2026-10-22T17:35:58.500782+00:00"
}
```

---

### 4. Actual Measured Model Performance (Official Test Benchmark)

The model was evaluated against the **official, untouched UNSW-NB15 test partition** containing **82,332 flows** (37,000 Normal, 45,332 Malicious). 

| Metric | NØX-MLP (PyTorch) | Logistic Regression Baseline | Performance Delta |
| :--- | :--- | :--- | :--- |
| **Accuracy** | **85.69%** (`0.8569`) | 80.94% (`0.8094`) | **+4.75%** |
| **Precision** | **80.47%** (`0.8047`) | 75.33% (`0.7533`) | **+5.14%** |
| **Recall / Sensitivity (TPR)** | **97.73%** (`0.9773`) | 97.23% (`0.9723`) | **+0.50%** |
| **F1-Score** | **88.27%** (`0.8827`) | 84.89% (`0.8489`) | **+3.38%** |
| **False Positive Rate (FPR)** | **29.05%** (`0.2905`) | 39.02% (`0.3902`) | **-9.97% (Lower is better)** |
| **ROC-AUC Score** | **0.9757** | 0.9556 | **+0.0201** |
| **Decision Threshold** | `0.50` | `0.50` | Validated |

#### Detailed Confusion Matrix (82,332 Test Flows):
- **True Negatives (TN)**: **26,250** normal flows correctly permitted.
- **False Positives (FP)**: **10,750** normal flows flagged as suspicious.
- **False Negatives (FN)**: **1,029** attacks missed (out of 45,332 attacks).
- **True Positives (TP)**: **44,303** malicious attacks successfully intercepted.

---

### 5. Project Directory Structure
```
NOX/
├── backend/
│   ├── api/                                  # FastAPI REST application
│   │   ├── __init__.py
│   │   ├── main.py                           # App entrypoint, lifespan & CORS
│   │   ├── routes/                           # API route definitions
│   │   │   ├── __init__.py
│   │   │   ├── health.py                     # GET /api/health
│   │   │   ├── detection.py                  # POST /detect, /batch, /upload, GET /stats
│   │   │   └── history.py                    # GET /api/history
│   │   └── schemas/                          # Pydantic data contracts
│   │       ├── __init__.py
│   │       └── detection_schema.py           # Ingestion & response schemas
│   ├── services/                             # Reusable backend service layer
│   │   ├── __init__.py
│   │   ├── model_service.py                  # PyTorch model loader & inference
│   │   ├── detection_service.py              # Detection orchestrator & streaming
│   │   └── threat_service.py                 # Severity triage logic
│   ├── database/                             # SQLite persistence
│   │   ├── __init__.py
│   │   ├── db.py                             # Connection manager & table setup
│   │   ├── models.py                         # Data Access Object (DAO)
│   │   └── nox_events.db                     # SQLite database file
│   ├── data/
│   │   ├── raw/                              # Raw UNSW-NB15 CSV datasets
│   │   │   ├── UNSW_NB15_training-set.csv
│   │   │   └── UNSW_NB15_testing-set.csv
│   │   └── processed/                        # Preprocessed neural matrices
│   │       ├── X_train.npy                   # (140272, 192) float32
│   │       ├── X_val.npy                     # (35069, 192) float32
│   │       ├── X_test.npy                    # (82332, 192) float32
│   │       ├── y_train.npy                   # (140272,) int64 binary targets
│   │       ├── y_val.npy                     # (35069,) int64 binary targets
│   │       ├── y_test.npy                    # (82332,) int64 binary targets
│   │       ├── attack_cat_train.npy          # Metadata multi-class labels
│   │       ├── attack_cat_val.npy            # Metadata multi-class labels
│   │       ├── attack_cat_test.npy           # Metadata multi-class labels
│   │       ├── feature_names.json            # 192 feature names
│   │       ├── dataset_summary.json          # Dataset audit metadata
│   │       └── preprocessing_pipeline.joblib # Serialized pipeline
│   ├── models/
│   │   ├── __init__.py
│   │   ├── mlp_model.py                      # NoxMLP PyTorch architecture
│   │   └── saved/                            # Saved model weights & metadata
│   │       ├── nox_mlp.pth                   # PyTorch state dict checkpoint
│   │       └── model_metadata.json           # Model configuration & metrics
│   ├── training/
│   │   ├── __init__.py
│   │   ├── train.py                          # Training loop with early stopping
│   │   └── evaluate.py                       # Evaluation & baseline comparison
│   ├── inference/
│   │   ├── __init__.py
│   │   └── predict.py                        # Reusable NoxPredictor engine
│   ├── outputs/
│   │   ├── plots/                            # Training & evaluation charts
│   │   │   ├── training_loss.png
│   │   │   ├── validation_loss.png
│   │   │   ├── validation_f1.png
│   │   │   ├── confusion_matrix.png
│   │   │   └── roc_curve.png
│   │   └── metrics/
│   │       └── evaluation_results.json       # Genuine benchmark results
│   ├── logs/
│   │   └── nox_backend.log                   # Server runtime logs
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_preprocessing.py             # Module 1 tests (9 tests)
│   │   ├── test_mlp.py                       # Model architecture tests (4 tests)
│   │   ├── test_training.py                  # Loss & backprop tests (3 tests)
│   │   ├── test_inference.py                 # Predictor engine tests (4 tests)
│   │   ├── test_evaluation.py                # Metrics & evaluation tests (2 tests)
│   │   ├── test_api.py                       # FastAPI integration tests (6 tests)
│   │   ├── test_detection_service.py         # Detection service tests (3 tests)
│   │   ├── test_threat_service.py            # Severity rules tests (4 tests)
│   │   ├── test_database.py                  # SQLite DAO tests (3 tests)
│   │   └── test_csv_upload.py                # CSV upload & streaming tests (4 tests)
│   ├── demo_model.py                         # Module 2 offline demonstration
│   └── demo_detection.py                     # Module 3 end-to-end detection demo
├── frontend/                                 # Reserved for Module 4 (React Dashboard)
│   └── README.md                             # Opium UI design tokens
├── requirements.txt                          # Python dependencies
├── README.md                                 # Master documentation
└── .gitignore                                # Version control rules
```

---

### 6. Installation & Environment Setup (PowerShell / Windows)

Open **PowerShell** in the `NOX` root directory:

```powershell
# 1. Verify Python version (Requires Python 3.11+)
python --version

# 2. Create the virtual environment
python -m venv .venv

# 3. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# (If script execution is restricted on Windows)
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# 4. Install all dependencies
pip install -r requirements.txt
```

---

### 7. Step-by-Step Execution Commands

#### Start the FastAPI Local Server:
```powershell
# Launch Uvicorn dev server bound to 127.0.0.1:8000
.\.venv\Scripts\python -m uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
```
Open your browser at **`http://127.0.0.1:8000/docs`** to view and test interactive Swagger documentation.

#### Run the Module 03 End-to-End Detection Demonstration:
```powershell
# Evaluates test flows through the detection service and logs them to SQLite
.\.venv\Scripts\python backend/demo_detection.py
```

#### Run All 43 Automated Unit & Integration Tests:
```powershell
.\.venv\Scripts\pytest backend/tests/ -v
```

---

### 8. Module 04 — Opium Cybersecurity Dashboard & Frontend Integration

Module 04 implements a production-grade single-page application adhering to an **Opium-inspired industrial cyberpunk design system**:

#### 1. Architecture & UI Technology Stack:
- **Core**: React 18, Vite, TypeScript, Tailwind CSS
- **Motion & Interactions**: Framer Motion (respects `prefers-reduced-motion`)
- **Telemetry Visualizations**: Recharts (Pie/Donut & Bar charts)
- **Icons**: Lucide React
- **Client Routing**: React Router v6
- **Test Framework**: Vitest & React Testing Library

#### 2. Design System Tokens:
- **Palette**:
  - Background: `#080808`
  - Surfaces: `#101010` (monolith surface), `#171717` (elevated)
  - Borders: `#292929` (thin industrial perimeter lines)
  - Chrome / Silver: `#dedede` (high-contrast technical text)
  - Muted: `#888888` (low-key metadata)
  - Threat Accent: `#a62735` / Critical: `#db3346` (restrained crimson alarms)
  - Success: `#79a995` (benign traffic indicator)
- **Typography**:
  - `Space Grotesk` (display headings)
  - `Inter` (readable UI body text)
  - `JetBrains Mono` (technical metrics, IDs, timestamps)

#### 3. Core Application Pages:
- **`01 // Overview` (`/`)**: Hero banner, live telemetry metric cards (`Total Analyzed`, `Potential Attacks`, `Normal Records`, `High Severity`), Recharts normal-vs-malicious donut breakdown, alert triage distribution, and latest SQLite incident stream.
- **`02 // Neural Detection` (`/detect`)**: Drag-and-drop CSV upload zone, file validation, progress state, and instant inference preview table with probability scores and severity badges.
- **`03 // Threat Analytics` (`/analytics`)**: Macro traffic ratio charts, severity breakdown, empirical sigmoid score distribution histogram, and Module 02 offline benchmark comparison panel.
- **`04 // Detection History` (`/history`)**: Immutable SQLite incident audit log with server pagination, source/severity/prediction filters, and interactive inspection modals.
- **`05 // System Information` (`/system`)**: Real-time FastAPI health check, round-trip latency probe, PyTorch MLP network topology summary, and benchmark ML limitations disclaimer.

---

### 9. Installation & Execution Guide

#### Backend Setup:
```powershell
# 1. Activate the Python virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Run the FastAPI backend (bound strictly to local interface)
.\.venv\Scripts\python -m uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive Swagger docs will be accessible at: `http://127.0.0.1:8000/docs`
- Health check API: `http://127.0.0.1:8000/api/health`

#### Frontend Setup:
Open a second terminal in `frontend/`:
```bash
cd frontend

# 1. Install Node dependencies
npm install

# 2. Verify environment configuration
# Default connects to http://127.0.0.1:8000
cp .env.example .env

# 3. Start Vite development server
npm run dev
```
- The Vite development server will bind to `http://127.0.0.1:5173`.
- Open `http://127.0.0.1:5173` to launch the NØX Cybersecurity Operations Terminal.

---

### 10. Automated Testing & Production Build

#### Frontend Automated Tests (14 Tests):
```bash
cd frontend
npm test
```
All 14 tests in 4 test suites verify navigation routing, dashboard telemetry loading/empty/error states, CSV upload and format validation, and prediction history rendering.

#### Frontend Production Build:
```bash
cd frontend
npm run build
```
Executes TypeScript compiler check (`tsc`) followed by Vite production bundling to `frontend/dist/`.

#### Backend Automated Tests (43 Tests):
```powershell
.\.venv\Scripts\pytest backend/tests/ -v
```
All 43 tests verify preprocessing, PyTorch MLP forward pass, loss computation, model saving, detection service, SQLite event persistence, and FastAPI endpoints.

---

### 11. Troubleshooting & Common Questions

- **"Backend unavailable. Start the NØX FastAPI server to enable detection"**:
  - Ensure the backend is active at `http://127.0.0.1:8000`. Test directly by navigating to `http://127.0.0.1:8000/api/health` in your browser.
  - If running on a non-default port, update `VITE_API_BASE_URL` in `frontend/.env`.
- **CORS Errors**:
  - The FastAPI backend explicitly authorizes `http://localhost:5173` and `http://127.0.0.1:5173`. Do not host the frontend on an unauthorized origin without updating `backend/api/main.py`.
- **Missing Columns in Custom CSVs**:
  - The preprocessing pipeline automatically imputes unobserved numerical columns with training medians and unseen categorical values with the default mode, ensuring resilient execution even on sparse flow logs.
