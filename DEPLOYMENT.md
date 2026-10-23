# NØX — Cloud Deployment Guide

This guide documents the end-to-end cloud deployment procedure for the **NØX — Neural Network Intrusion Detection System**.

---

## 1. Deployment Architecture

```
   ┌─────────────────────────────────────────────────────────────┐
   │                     VERCEL (Frontend)                       │
   │  - React 18 + Vite (SPA)                                    │
   │  - NØX Opium Cyberpunk Theme (Tailwind CSS)                 │
   │  - Static Asset & Sample CSV Hosting (/sample_network_flows)│
   │  - Environment: VITE_API_BASE_URL                           │
   └──────────────────────────────┬──────────────────────────────┘
                                  │ HTTPS Requests + Secure CORS
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                      RENDER (Backend)                       │
   │  - FastAPI REST API (Uvicorn on $PORT)                      │
   │  - PyTorch MLP Intrusion Detection Model (CPU-Optimized)    │
   │  - Fitted Scikit-Learn Preprocessing Pipeline               │
   │  - SQLite Event History (Ephemeral on Free Tier)            │
   │  - Dynamic CORS via CORS_ORIGINS & CORS_ORIGIN_REGEX        │
   └─────────────────────────────────────────────────────────────┘
```

---

## 2. Step 1: Deploy Backend to Render

### Option A: Using the Render Blueprint (Recommended)
1. Fork or push this repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com/), click **New +** > **Blueprint**.
3. Connect your GitHub repository.
4. Render will detect [`render.yaml`](file:///c:/Users/TRB/modified%20mindspace%20sdg/CrediAI/NOX/render.yaml) and automatically configure:
   - **Service Type:** Web Service
   - **Runtime:** Python
   - **Plan:** Free
   - **Build Command:**
     ```bash
     pip install --upgrade pip && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Environment Variables:**
     - `PYTHON_VERSION`: `3.11.9`
     - `CORS_ORIGIN_REGEX`: `^https://.*\.vercel\.app$`
     - `CORS_ORIGINS`: `http://localhost:5173,http://localhost:3000`
5. Click **Apply**.
6. Once deployed, note your Render backend URL (e.g., `https://nox-neural-backend.onrender.com`).

### Option B: Manual Web Service Setup on Render
1. Click **New +** > **Web Service**.
2. Connect your repository.
3. Configure settings:
   - **Name:** `nox-neural-backend`
   - **Region:** Any (e.g. Oregon / Frankfurt)
   - **Branch:** `main`
   - **Root Directory:** *(leave blank for repository root)*
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install --upgrade pip && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
     ```
4. Under **Environment Variables**, add:
   - `PYTHON_VERSION` = `3.11.9`
   - `CORS_ORIGIN_REGEX` = `^https://.*\.vercel\.app$`
   - *(Optional)* `CORS_ORIGINS` = `https://your-custom-domain.com`
5. Click **Create Web Service**.

> [!IMPORTANT]
> **Why CPU PyTorch?**
> Standard `pip install torch` downloads ~2.2 GB of GPU/CUDA binaries on Linux, exceeding Render's free tier disk and memory quota. Installing `--index-url https://download.pytorch.org/whl/cpu` installs the lightweight ~180MB CPU wheel, ensuring fast builds and zero out-of-memory errors.

> [!WARNING]
> **Render Free Tier Cold Starts:**
> Render spins down free tier web services after 15 minutes of inactivity. When a user first opens your Vercel site after inactivity, the backend takes 60–90 seconds to cold start. The NØX frontend UI includes an automatic offline banner and a **"Wake Up Backend"** button.

> [!NOTE]
> **Ephemeral SQLite Database:**
> Render's free tier filesystem is ephemeral. SQLite audit logs reset upon redeploy or container sleep. For permanent audit logs in production, attach a Render Persistent Disk or external PostgreSQL database.

---

## 3. Step 2: Deploy Frontend to Vercel

1. In the [Vercel Dashboard](https://vercel.com/), click **Add New...** > **Project**.
2. Select your GitHub repository.
3. In the project configuration:
   - **Framework Preset:** Vite
   - **Root Directory:** Click **Edit** and choose `frontend` *(or leave root if relying on root `vercel.json`)*
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Expand **Environment Variables** and add:
   - **Key:** `VITE_API_BASE_URL`
   - **Value:** Your live Render URL (e.g., `https://nox-neural-backend.onrender.com` - *no trailing slash*)
5. Click **Deploy**.
6. Once built, Vercel provides your live URL (e.g., `https://nox-neural-ids.vercel.app`).

---

## 4. Step 3: Verification & Live Testing

1. **Verify Backend Health:**
   Visit `https://<YOUR-RENDER-BACKEND>.onrender.com/api/health` in your browser.
   You should receive:
   ```json
   {
     "status": "ready",
     "model_loaded": true,
     "model_version": "NØX-MLP-v1",
     "threshold": 0.5,
     "device": "cpu"
   }
   ```

2. **Verify Frontend UI:**
   Open your Vercel URL in your browser.
   - The Header status indicator should turn **ONLINE** (green pulsating dot).
   - The Overview page will load live telemetry statistics.

3. **Test Real Neural Classification with Sample CSV:**
   - Navigate to **02 // Neural Detection**.
   - Click **"SAMPLE CSV"** in the drag-and-drop box to download `nox_sample_network_flows.csv`.
   - Drag or select the file and click **START NEURAL INFERENCE →**.
   - The backend processes the flows through the fitted standardizer and PyTorch MLP, rendering real predictions, severity categorization, and distribution charts.

4. **Verify Route Refreshing (SPA Routing):**
   - Navigate to `/history` or `/system` and press `F5` / Refresh.
   - The page should reload seamlessly without returning a 404 error (handled by `vercel.json`).
