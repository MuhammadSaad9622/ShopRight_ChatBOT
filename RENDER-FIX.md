# Fix Render: "Preparing metadata (pyproject.toml): finished with status 'error'" / pydantic

Render is building your backend as **Python 3.14**. You must use **Docker** instead so the app runs on Python 3.11.

---

## Do this: Create a new Web Service with Docker (recommended)

Render often **does not let you change** an existing Python service to Docker. So create a **new** service and choose **Docker** from the start.

### Step 1: Delete the old service (optional but avoids confusion)

1. Go to [dashboard.render.com](https://dashboard.render.com).
2. Open your **backend** service (the one that’s failing).
3. **Settings** → scroll down → **Delete Web Service**. Confirm.  
   (You can keep it and create a second service if you prefer.)

### Step 2: Create a new Web Service

1. On the Render dashboard, click **New +** → **Web Service**.
2. Connect your **GitHub** account if needed, then select the **repo** that contains this project.
3. Configure the new service:

   | Field | Value |
   |-------|--------|
   | **Name** | `support-agent-api` (or any name) |
   | **Region** | Choose one (e.g. Oregon) |
   | **Branch** | `main` (or your default branch) |
   | **Root Directory** | Leave **empty** (we use Docker context instead) |
   | **Runtime** | **Docker** ← must be Docker, not Python |
   | **Dockerfile Path** | `backend/Dockerfile` |
   | **Docker Context** | `backend` |
   | **Instance Type** | Free |

4. Click **Advanced** (if you see it) and confirm there’s no “Build Command” or “Start Command” (Docker uses the Dockerfile).
5. Click **Create Web Service**.

### Step 3: Add your API key

1. In the new service, go to **Environment** (left sidebar).
2. **Add Environment Variable**:
   - Key: `OPENAI_API_KEY`
   - Value: your OpenAI API key (e.g. `sk-...`)
3. Save. Render will redeploy automatically, or click **Manual Deploy** → **Deploy latest commit**.

### Step 4: Confirm it’s Docker

In **Logs** or **Events** you should see something like:

- `Building Docker image...`  
- `Successfully built ...`  
- `Running 'uvicorn main:app ...'`

You should **not** see:

- `python3.14`  
- `Preparing metadata (pyproject.toml)`  
- `pip install`

If you still see the pydantic error, the service is still using the **Python** runtime. Delete this service and create another one, and double-check that **Runtime** is set to **Docker** when you create it.

---

## If you use Blueprint instead

1. Delete the current failing backend service.
2. **New +** → **Blueprint**.
3. Select the same repo. Render will read `render.yaml` and create a **Docker** web service.
4. Open that service → **Environment** → add **OPENAI_API_KEY**.
5. Deploy.

---

## Summary

- The error happens because Render is using **Python 3.14** and building pydantic from source (Rust), which fails.
- Fix: use **Docker** so the build uses the Dockerfile (Python 3.11).
- Easiest path: **create a new Web Service**, set **Runtime** to **Docker**, **Dockerfile Path** to `backend/Dockerfile`, **Docker Context** to `backend`, add **OPENAI_API_KEY**, then deploy.
