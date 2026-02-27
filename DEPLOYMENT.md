# Deploy: Frontend on Vercel/Netlify + Backend on Railway/Render

Step-by-step for **Option 4**: backend on Railway or Render, frontend on Vercel (or Netlify).

---

## Which backends are free?

| Backend | Free tier? | Notes |
|---------|------------|--------|
| **Render** | Yes | **Free** Web Service: 750 hours/month, spins down after ~15 min idle (cold start when someone visits). Good for demos and low traffic. |
| **Fly.io** | Yes | **Free** tier: up to 3 shared-cpu VMs, 160GB outbound/month. App stays running. |
| **Railway** | Limited | **$5 free credit/month** (no longer unlimited free). Enough for light use; then paid. |
| **Google Cloud Run** | Yes | **Free** tier: 2M requests/month, 360K vCPU-seconds. Pay per use after that. |
| **DigitalOcean App Platform** | No | Free tier discontinued; paid only. |
| **AWS** | 12‑month | Free tier for 12 months on some services (e.g. Lambda, ECS); then paid. |
| **Heroku** | No | No free tier. |
| **VPS** | No | You pay for the server (e.g. ~$5–6/mo for a small Droplet). |

**Best free options for this app:** **Render** (easiest, free Web Service) or **Fly.io** (free tier, no spin-down). Frontend on **Vercel** or **Netlify** is free for personal/small projects.

---

## Part 1: Deploy the backend

### A. Using Railway

1. Go to [railway.app](https://railway.app) and sign in (e.g. with GitHub).
2. **New Project** → **Deploy from GitHub repo** → select your repo.
3. Railway may create one service from the repo. **Delete the default service** if you want a clean setup, then add a new one:
   - **New** → **GitHub Repo** → select the same repo.
4. In the new service:
   - **Settings** → **Root Directory:** set to `backend`.
   - **Settings** → **Build Command:** leave default or set `pip install -r requirements.txt`.
   - **Settings** → **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`  
     (Railway sets `$PORT`; use it so the app listens on the right port.)
   - **Variables** → **Add Variable:**  
     - `OPENAI_API_KEY` = your OpenAI API key (e.g. `sk-...`).
   - **Settings** → **Generate Domain** (or add a custom domain). Copy the URL, e.g. `https://your-app-name.up.railway.app`.
5. Deploy. Wait until the build finishes and the service is **Active**. Test: open `https://your-backend-url.up.railway.app/health` — you should see `{"status":"ok"}`.

**Backend URL to use later:** `https://your-app-name.up.railway.app` (no trailing slash).

---

### B. Using Render (alternative)

1. Go to [render.com](https://render.com) and sign in.
2. **New +** → **Web Service**.
3. Connect your GitHub repo and select it.
4. Configure:
   - **Name:** e.g. `support-agent-api`.
   - **Root Directory:** `backend`.
   - **Runtime:** Python 3.
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free (or paid).
5. **Environment** → **Add Environment Variable:**  
   - Key: `OPENAI_API_KEY`  
   - Value: your OpenAI API key.
6. Click **Create Web Service**. When it’s live, copy the URL (e.g. `https://support-agent-api.onrender.com`).

**Backend URL to use later:** `https://your-service-name.onrender.com` (no trailing slash).

---

### D. Using Fly.io (step-by-step)

Fly.io runs your backend in a container. Free tier includes a few small VMs and stays on (no spin-down like Render).

#### 1. Install the Fly CLI

**macOS (Homebrew):**
```bash
brew install flyctl
```

**Windows (PowerShell):**
```bash
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

**Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

Or see [fly.io/docs/hands-on/install-flyctl](https://fly.io/docs/hands-on/install-flyctl/).

#### 2. Sign in

```bash
fly auth login
```

This opens a browser to sign up or log in (email or GitHub).

#### 3. Deploy from the backend directory

From your **project root**:

```bash
cd backend
fly launch
```

- **Create new app?** Yes.
- **App name:** accept the suggestion (e.g. `support-agent-api`) or type one (e.g. `my-shopright-api`).
- **Region:** pick one close to you (e.g. `iad` for Virginia).
- **Postgres / Redis:** No (we use SQLite and in-memory RAG).
- Fly will use the `Dockerfile` in `backend/` and create a `fly.toml` if one doesn’t exist (this repo includes one so port 8000 is used).

#### 4. Set your OpenAI API key (secret)

```bash
fly secrets set OPENAI_API_KEY=sk-your-actual-key-here
```

Use your real key; Fly stores it securely and restarts the app.

#### 5. Deploy

```bash
fly deploy
```

Wait for the build and release to finish. You’ll see a line like:

`--> v0 deployed successfully`

#### 6. Get your backend URL

```bash
fly status
```

Or open the hostname shown after deploy, e.g. `https://support-agent-api.fly.dev`.  
**Backend URL:** `https://<your-app-name>.fly.dev` (no trailing slash).

#### 7. Test the backend

Open in a browser or with curl:

`https://<your-app-name>.fly.dev/health`

You should see: `{"status":"ok"}`.

#### 8. Use this URL in the frontend

When deploying the frontend (Vercel or Netlify), set **VITE_API_URL** to `https://<your-app-name>.fly.dev`.

---

**Useful Fly commands**

| Command | Description |
|--------|-------------|
| `fly status` | App status and URL |
| `fly logs` | Stream logs |
| `fly secrets set OPENAI_API_KEY=sk-...` | Update API key (restarts app) |
| `fly deploy` | Rebuild and deploy after code changes |
| `fly ssh console` | SSH into the running container |

**Free tier:** Stay within 3 shared-cpu VMs and 160GB outbound/month. This backend fits in one small VM; `fly.toml` uses 256MB RAM and shared CPU so it stays within free tier.

---

### E. Other backend options

You can use any of these instead of Railway or Render. After deploying, set **VITE_API_URL** on the frontend to your backend’s HTTPS URL.

| Platform | Free tier? | Notes |
|----------|------------|--------|
| **[Fly.io](https://fly.io)** | Yes | Free tier: 3 shared VMs, 160GB outbound. Docker-based, global. Use `fly launch` from `backend/`, set `OPENAI_API_KEY` secret. |
| **[Render](https://render.com)** | Yes | Free Web Service (see Part 1B above). Spins down when idle. |
| **[Railway](https://railway.app)** | $5 credit/mo | See Part 1A above. Credit covers light use. |
| **[Google Cloud Run](https://cloud.google.com/run)** | Yes | Free tier: 2M requests/month. Deploy container, set OPENAI_API_KEY. Pay per request after. |
| **[DigitalOcean App Platform](https://www.digitalocean.com/products/app-platform)** | No | Paid only. Web Service, root `backend`, port 8080, add OPENAI_API_KEY. |
| **[AWS](https://aws.amazon.com)** | 12‑mo free | ECS/Lambda free tier limits. More setup. |
| **[Heroku](https://heroku.com)** | No | No free tier. |
| **VPS** (Droplet, Linode, EC2) | No | You pay for the server; run Docker or uvicorn yourself. |

**DigitalOcean App Platform (quick steps):** New App → GitHub repo → choose **Web Service**, Root Directory `backend`, Build Command `pip install -r requirements.txt`, Run Command `uvicorn main:app --host 0.0.0.0 --port 8080`. Add OPENAI_API_KEY in App-Level Environment Variables. Deploy; use the assigned URL as the backend URL.

---

## Part 2: Deploy the frontend on Vercel

1. Go to [vercel.com](https://vercel.com) and sign in (e.g. with GitHub).
2. **Add New** → **Project** → import your GitHub repo.
3. Configure the project:
   - **Framework Preset:** Vite (Vercel usually detects it).
   - **Root Directory:** click **Edit** and set to `frontend`.
   - **Build Command:** `npm run build` (default is fine).
   - **Output Directory:** `dist` (default for Vite).
   - **Environment Variables** → add:
     - **Name:** `VITE_API_URL`  
     - **Value:** your backend URL from Part 1, e.g. `https://your-app-name.up.railway.app`  
     - **Environment:** Production (and Preview if you want).
4. Click **Deploy**. Wait for the build to finish.
5. Open the Vercel URL (e.g. `https://your-project.vercel.app`). The chat should load and talk to your backend.

**Important:** If you change the backend URL later, update `VITE_API_URL` in Vercel and **redeploy** the frontend (new build is required).

---

## Part 3: Deploy the frontend on Netlify (instead of Vercel)

1. Go to [netlify.com](https://netlify.com) and sign in.
2. **Add new site** → **Import an existing project** → connect your Git provider and select the repo.
3. Configure:
   - **Base directory:** `frontend`
   - **Build command:** `npm run build`
   - **Publish directory:** `dist`
   - **Environment variables** → **Add a variable** / **Edit settings** → **Environment variables:**
     - Key: `VITE_API_URL`  
     - Value: your backend URL (e.g. `https://your-app-name.up.railway.app`)
     - Scopes: Production (and Deploy Previews if you want).
4. **Deploy site**. When the deploy finishes, open the Netlify URL. The widget should use your backend.

If you change the backend URL, update `VITE_API_URL` in Netlify and trigger a new deploy.

---

## Checklist

- [ ] Backend deployed (Railway, Render, Fly.io, DigitalOcean, Cloud Run, or VPS) and **OPENAI_API_KEY** set.
- [ ] Backend URL works: `https://your-backend-url/health` returns `{"status":"ok"}`.
- [ ] Frontend deployed (Vercel or Netlify) with **VITE_API_URL** = backend URL (no trailing slash).
- [ ] Frontend URL opens the chat and messages reach the backend (no CORS errors in the browser console).

## Troubleshooting

- **"Failed to fetch" / CORS:** Backend already allows all origins. If you still see CORS errors, check that the backend URL in `VITE_API_URL` is correct and uses **HTTPS**.
- **Blank or wrong API URL:** `VITE_API_URL` is baked in at **build time**. Change it in Vercel/Netlify and redeploy (trigger a new build).
- **Backend 500 / "OPENAI_API_KEY not set":** Add or fix `OPENAI_API_KEY` in your backend platform (Railway, Render, Fly.io, etc.) and redeploy.
- **Render: "Preparing metadata (pyproject.toml): finished with status 'error'" / pydantic-core / read-only file system:** Render may use Python 3.14 by default; pydantic has no prebuilt wheels for it, so the build tries to compile Rust and fails. **Fix:** The repo includes `backend/runtime.txt` with `python-3.12.7`. If Render still picks 3.14, set **Environment** → **Python Version** to `3.12.7` in the Render dashboard (or ensure the root directory is `backend` so it finds `runtime.txt`), then redeploy.
