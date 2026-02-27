# AI Support Agent with Context and Actions

An AI customer support widget for an e-commerce company. The agent answers questions using an internal knowledge base (RAG), looks up order status via a custom tool, and keeps conversation context (chat memory). Responses stream to the frontend in real time.

## Features

- **Knowledge Base / RAG**: Company policies in `backend/faq.txt` are chunked, embedded (OpenAI), and stored in an **in-memory vector store with cosine similarity**. On startup the backend processes the file, chunks it, generates embeddings, and stores them. Policy questions retrieve relevant chunks and the AI uses them to generate answers.
- **Function Calling**: The `get_order_status` tool looks up mock order data (e.g. Order #123 → Shipped, #456 → Processing). Questions like *"Where is order #123?"* cause the LLM to call this tool, retrieve the data, and respond naturally.
- **Chat History (Memory)**: Conversation is stored in **SQLite** per session. Follow-ups like *"My order number is 123."* then *"What is its status?"* work because the AI sees prior messages and understands "its" refers to order #123.
- **Streaming**: The backend streams the assistant reply over **Server-Sent Events (SSE)**; the frontend displays content as it arrives (similar to ChatGPT).

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, **in-memory vector store (cosine similarity)**, **SQLite** (chat memory), OpenAI (LLM + embeddings).
- **Frontend**: React 18, Vite. Chat UI with streaming responses.
- **Zero-friction**: No Postgres, Pinecone, Redis, or other external infrastructure—only local SQLite and local (in-memory) vector store.

## Quick Start (Local)

### 1. Install dependencies (backend)

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set environment variables

Create `backend/.env` from `backend/.env.example` and set your OpenAI API key:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and set:
# OPENAI_API_KEY=sk-your-key-here
```

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key (used for chat and for RAG embeddings). |
| `OPENAI_MODEL` | No | Chat model name (default: `gpt-4o-mini`). |

### 3. Run the application

**Terminal 1 – Backend**

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

On first run, the app loads `faq.txt`, chunks it, generates embeddings, and stores them in memory. Chat history is stored in `backend/support_agent.db`.

**Terminal 2 – Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 (or the port Vite shows). To call the backend directly, set `VITE_API_URL=http://localhost:8000` in `frontend/.env`.

## Docker (Recommended)

From the project root:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and set OPENAI_API_KEY
docker-compose up --build
```

- **Frontend**: http://localhost (port 80)  
- **Backend**: http://localhost:8000  

The frontend container proxies `/chat` and `/health` to the backend.

## Repository Structure

```
.
├── backend/
│   ├── main.py          # FastAPI: /chat (streaming), /health; RAG + tools + memory
│   ├── rag.py           # Load faq.txt, chunk, embed, in-memory vector store, retrieve
│   ├── tools.py         # get_order_status + mock order dictionary
│   ├── memory.py        # SQLite chat history per session
│   ├── faq.txt          # Company policies (5–10 paragraphs)
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx      # Chat UI, SSE streaming
│   │   ├── App.css
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Design Notes

- **RAG**: FAQ is split into overlapping chunks (~400 words, 50 overlap). Embeddings are from OpenAI (`text-embedding-3-small`). Vectors are stored in memory; retrieval uses cosine similarity. When the user asks a policy-related question, the backend retrieves the top-k chunks and injects them into the system message so the AI answers from the knowledge base.
- **Tools**: Only `get_order_status(order_id)` is defined. The LLM autonomously calls it when the user asks about order status or tracking; we run the tool and append the result, then get the final answer.
- **Memory**: Each message (user and assistant) is stored in SQLite by `session_id`. The frontend keeps a session ID in `localStorage`. The last 20 messages are sent with each request so the agent maintains context (e.g. "its" = order 123).
- **Streaming**: The `/chat` endpoint uses Server-Sent Events. The backend sends `data: {"type":"text","content":"..."}` for each chunk and `data: {"type":"done"}` at the end. Responses appear progressively in the UI.

## Example Queries

- *"What is your return policy?"* → RAG retrieval + answer from FAQ.
- *"Where is order #123?"* → Tool call `get_order_status("123")` → answer with status and tracking.
- *"My order number is 456."* then *"What is its status?"* → History includes order 456; model calls the tool for 456 and answers.

## Deployment

Deploy the backend with **OPENAI_API_KEY** set; the frontend needs **VITE_API_URL** pointing to the backend URL if they are on different domains.

- **Option 1 – Docker on a VPS:** Install Docker and Docker Compose on a server (e.g. Ubuntu). Clone the repo, set `OPENAI_API_KEY` in `backend/.env`, run `docker compose up --build -d`. Frontend on port 80, backend on 8000. Put Nginx or Caddy in front for HTTPS.
- **Option 2 – Railway:** Deploy backend (root `backend`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`, add OPENAI_API_KEY). Deploy frontend (root `frontend`, build `npm run build`, set VITE_API_URL to backend URL at build time, serve `dist`).
- **Option 3 – Render:** Backend as Web Service (root `backend`), frontend as Static Site (root `frontend`, VITE_API_URL at build time, publish `dist`).
- **Option 4 – Vercel/Netlify + backend elsewhere:** Deploy backend on Railway/Render/VPS. Deploy frontend on Vercel or Netlify with VITE_API_URL set to the backend URL when building.

**Checklist:** OPENAI_API_KEY on backend; VITE_API_URL on frontend build if split; use HTTPS in production.

## License

MIT.
