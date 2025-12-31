from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from contextlib import asynccontextmanager
from rag_engine import initialize_rag, retrieve_sections, explain_with_llm

# ================= SCHEMAS =================

class QueryRequest(BaseModel):
    question: str

class Section(BaseModel):
    act: str
    section: str
    text: str

class QueryResponse(BaseModel):
    mode: str
    explanation: str
    sections: List[Section]
    confidence: float
    disclaimer: str = "Nyay Sathi provides legal information for educational purposes only. It does not provide legal advice."

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

@app.post("/query", response_model=QueryResponse)
def query_legal_db(request: QueryRequest):
    query = request.question.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # 1. Retrieve
    # RAG engine handles extraction
    raw_results = retrieve_sections(query)
    
    # 2. Explain
    mode, explanation, confidence = explain_with_llm(query, raw_results)
    
    # 3. Format Response
    formatted_sections = []
    for r in raw_results:
        formatted_sections.append(Section(
            act=r.get('act_name', 'Unknown'),
            section=r.get('section_number', 'Unknown'),
            text=r.get('text', '')
        ))

    return QueryResponse(
        mode=mode,
        explanation=explanation,
        sections=formatted_sections,
        confidence=confidence
    )
