"""
AI Support Agent API: RAG, tool calling (get_order_status), chat memory, streaming.
Uses non-streaming OpenAI calls then simulates streaming to avoid ERR_INCOMPLETE_CHUNKED_ENCODING.
"""
import asyncio
import json
import os
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import openai

from memory import init_db, add_message, get_history
from rag import init_rag, retrieve
from tools import get_order_status

load_dotenv(Path(__file__).parent / ".env")

app = FastAPI(title="AI Support Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI tool definition for get_order_status
GET_ORDER_STATUS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_order_status",
        "description": "Get the current status and tracking information for a customer order by order ID. Use when the user asks about order status, where their order is, tracking, or delivery for a specific order number.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID or number (e.g. 123, #456)",
                }
            },
            "required": ["order_id"],
        },
    },
}


def build_system_message(rag_chunks: list[str]) -> str:
    base = """You are a helpful customer support agent for ShopRight, an e-commerce company.
Answer questions using the provided company knowledge base when relevant.
When customers ask about order status, tracking, or delivery for a specific order number, use the get_order_status tool to fetch real-time order information.
Be concise, friendly, and professional. If you don't know something, say so."""
    if rag_chunks:
        base += "\n\nRelevant company knowledge:\n\n" + "\n\n---\n\n".join(rag_chunks)
    return base


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@app.on_event("startup")
async def startup():
    # Process faq.txt, chunk, generate embeddings, store in local vector store (in-memory)
    init_rag()
    await init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Stream chat response with RAG + tool calling + memory."""
    session_id = request.session_id or "default"
    user_message = (request.message or "").strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="message is required")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not set. Add it to .env to use the chat.",
        )

    # Persist user message
    await add_message(session_id, "user", user_message)

    # Load conversation history (last N messages)
    history = await get_history(session_id, limit=20)
    # Retrieve RAG context for this query
    rag_chunks = retrieve(user_message, top_k=4)
    system_content = build_system_message(rag_chunks)

    messages = [{"role": "system", "content": system_content}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    client = openai.AsyncOpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def stream_generator() -> AsyncGenerator[str, None]:
        """Get full response from OpenAI (no stream), then yield to client in chunks so stream always completes."""
        try:
            full_content = ""
            current_messages = list(messages)
            max_tool_rounds = 3
            round_count = 0

            while round_count < max_tool_rounds:
                round_count += 1
                resp = await client.chat.completions.create(
                    model=model,
                    messages=current_messages,
                    tools=[GET_ORDER_STATUS_TOOL],
                    stream=False,
                )
                choice = resp.choices[0] if resp.choices else None
                if not choice:
                    break
                msg = choice.message
                assistant_content = (msg.content or "").strip()
                full_content += assistant_content

                tool_calls = getattr(msg, "tool_calls", None) or []
                if not tool_calls:
                    break

                current_messages.append({
                    "role": "assistant",
                    "content": assistant_content or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"},
                        }
                        for tc in tool_calls
                    ],
                })
                for tc in tool_calls:
                    if getattr(tc.function, "name", None) == "get_order_status":
                        try:
                            args = json.loads(tc.function.arguments or "{}")
                            order_id = args.get("order_id", "")
                            result = get_order_status(order_id)
                        except Exception as e:
                            result = {"error": str(e)}
                    else:
                        result = {"error": "Unknown tool"}
                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    })

            try:
                if full_content:
                    await add_message(session_id, "assistant", full_content)
            except Exception:
                pass

            # Simulate streaming: yield text in small chunks so frontend gets progressive display
            chunk_size = 3
            for i in range(0, len(full_content), chunk_size):
                piece = full_content[i : i + chunk_size]
                if piece:
                    yield f"data: {json.dumps({'type': 'text', 'content': piece})}\n\n"
                await asyncio.sleep(0.01)
            yield "data: {\"type\": \"done\"}\n\n"

        except Exception as e:
            err_msg = str(e)
            if "401" in err_msg or "invalid_api_key" in err_msg or "Incorrect API key" in err_msg:
                err_msg = "Invalid or missing OpenAI API key. Add a valid OPENAI_API_KEY to backend/.env"
            yield f"data: {json.dumps({'type': 'error', 'content': err_msg})}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
