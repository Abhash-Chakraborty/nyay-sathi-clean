from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from contextlib import asynccontextmanager
from rag_engine import initialize_rag, retrieve_sections, explain_with_llm

# ================= SCHEMAS =================

class AskRequest(BaseModel):
    question: str

class Source(BaseModel):
    act: str
    section: str
    text: str
    score: float

class AskResponse(BaseModel):
    mode: str  # "rag" | "fallback"
    confidence: str  # "high" | "low"
    answer: str
    sources: List[Source]
    disclaimer: str = "Informational only, not legal advice"

# ================= LIFECYCLE =================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Nyay Sathi Backend...")
    initialize_rag()
    yield
    # Shutdown
    print("Shutting down...")

# ================= APP =================

app = FastAPI(title="Nyay Sathi API", lifespan=lifespan)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Nyay Sathi Backend"}

@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    query = request.question.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # 1. Retrieve
    raw_results = retrieve_sections(query)
    
    # 2. Explain
    # mode returned by rag_engine is "grounded" (which we map to "rag") or "fallback"
    rag_mode, explanation, numeric_confidence = explain_with_llm(query, raw_results)
    
    # Map internal mode "grounded" -> "rag"
    api_mode = "rag" if rag_mode == "grounded" else "fallback"
    
    # Map numeric confidence to "high" | "low"
    # Logic: If rag_mode is grounded, it implies high confidence (>= threshold)
    # If fallback, it implies low confidence.
    confidence_str = "high" if api_mode == "rag" else "low"

    # 3. Format Response
    formatted_sources = []
    if api_mode == "rag":
        for r in raw_results:
            formatted_sources.append(Source(
                act=r.get('act_name', 'Unknown'),
                section=r.get('section_number', 'Unknown'),
                text=r.get('text', ''),
                score=r.get('score', 0.0)
            ))

    return AskResponse(
        mode=api_mode,
        confidence=confidence_str,
        answer=explanation,
        sources=formatted_sources
    )
