# ================= RAILWAY / FREE TIER SAFETY =================
import os

# Force CPU-only execution (critical for free tiers)
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ================= IMPORTS =================
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

# ================= ENV =================
load_dotenv()

# ================= CONFIG =================

# Resolve project root reliably
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

FAISS_INDEX_PATH = DATA_DIR / "faiss.index"
FAISS_META_PATH = DATA_DIR / "faiss_meta.pkl"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.1-8b-instant"

# Keep small to reduce memory & latency
TOP_K = 3
CONFIDENCE_THRESHOLD = 0.50

# ================= GLOBALS =================
index = None
metadata = None
embedder = None
client = None

# ================= INIT =================

def initialize_rag():
    """Initialize FAISS, metadata, embedder, and Groq client."""
    global index, metadata, embedder, client

    print("Starting Nyay Sathi Backend...")
    print("Resolving data paths...")

    if not FAISS_INDEX_PATH.exists():
        raise FileNotFoundError(f"FAISS index not found at {FAISS_INDEX_PATH}")

    if not FAISS_META_PATH.exists():
        raise FileNotFoundError(f"FAISS metadata not found at {FAISS_META_PATH}")

    print("Loading FAISS index...")
    index = faiss.read_index(str(FAISS_INDEX_PATH))
    print(f"FAISS vectors loaded: {index.ntotal}")

    print("Loading metadata...")
    with open(FAISS_META_PATH, "rb") as f:
        metadata = pickle.load(f)

    print("Loading embedding model (CPU-only)...")
    embedder = SentenceTransformer(
        EMBED_MODEL,
        device="cpu"
    )

    print("Initializing Groq client...")
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    print("RAG System Initialized successfully.")

# ================= PROMPTS =================

SYSTEM_PROMPT_A = """You are Nyay Sathi, a helpful Indian legal assistant.
MODE: RAG-BACKED (HIGH CONFIDENCE).

INSTRUCTIONS:
1. You are provided with retrieved legal sections from Indian laws.
2. Answer the USER QUESTION using ONLY the provided LEGAL TEXT.
3. Explicitly mention the Act Name and Section Number if available.
4. Explain the provision in simple English for a layperson.
5. If the text does not answer the question, clearly state so.
6. DO NOT invent laws, punishments, or procedures.
7. DO NOT give legal advice.

MANDATORY DISCLAIMER:
End your response with:
"Disclaimer: This information is for educational purposes only and does not constitute legal advice."
"""

SYSTEM_PROMPT_B = """You are Nyay Sathi, a helpful Indian legal assistant.
MODE: GENERAL FALLBACK (LOW CONFIDENCE).

INSTRUCTIONS:
1. No specific legal sections matched the query.
2. Do NOT cite Acts or Sections.
3. Do NOT invent punishments or procedures.
4. Provide a high-level educational explanation.
5. Encourage the user to rephrase if needed.
6. DO NOT give legal advice.

MANDATORY DISCLAIMER:
End your response with:
"Disclaimer: This information is for educational purposes only and does not constitute legal advice."
"""

# ================= CORE LOGIC =================

def retrieve_sections(query: str):
    query_vec = embedder.encode([query], normalize_embeddings=True).astype("float32")
    scores, indices = index.search(query_vec, TOP_K)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        record = metadata[idx].copy()
        record["score"] = float(score)
        results.append(record)

    return results


def explain_with_llm(query: str, retrieved: list):
    if not retrieved:
        mode = "fallback"
        top_score = 0.0
    else:
        top_score = retrieved[0]["score"]
        mode = "grounded" if top_score >= CONFIDENCE_THRESHOLD else "fallback"

    if mode == "grounded":
        context = ""
        for r in retrieved:
            context += (
                f"--- ITEM ---\n"
                f"Act: {r.get('act_name', 'Unknown')}\n"
                f"Section: {r.get('section_number', 'Unknown')}\n"
                f"Text: {r.get('text', '')}\n"
                f"Confidence: {r.get('score'):.2f}\n"
            )

        system_prompt = SYSTEM_PROMPT_A
        user_content = f"USER QUESTION: {query}\n\nLEGAL TEXT FOUND:\n{context}"

    else:
        system_prompt = SYSTEM_PROMPT_B
        user_content = (
            f"USER QUESTION: {query}\n\n"
            f"(No high-confidence legal sections matched)"
        )

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            max_tokens=500,
        )

        return mode, response.choices[0].message.content.strip(), top_score

    except Exception as e:
        print(f"LLM Error: {e}")
        return (
            "fallback",
            "System is temporarily unavailable. "
            "Disclaimer: This information is for educational purposes only and does not constitute legal advice.",
            0.0,
        )
