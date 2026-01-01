# Render deployment path fix applied
import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

# Load env vars
load_dotenv()

# ================= CONFIG =================

# Resolve project root reliably (…/src)
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data" / "processed"

FAISS_INDEX_PATH = DATA_DIR / "faiss.index"
FAISS_META_PATH = DATA_DIR / "faiss_meta.pkl"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.1-8b-instant"
TOP_K = 5

# ================= GLOBALS =================
index = None
metadata = None
embedder = None
client = None

def initialize_rag():
    """Load models and index into memory."""
    global index, metadata, embedder, client

    print("Starting Nyay Sathi Backend...")
    print("Loading FAISS index...")

    try:
        if not FAISS_INDEX_PATH.exists():
            raise FileNotFoundError(f"FAISS index not found at {FAISS_INDEX_PATH}")

        index = faiss.read_index(str(FAISS_INDEX_PATH))
        print(f"FAISS vectors loaded: {index.ntotal}")

    except Exception as e:
        print(f"Error loading FAISS index from {FAISS_INDEX_PATH}: {e}")
        raise e

    print("Loading metadata...")
    try:
        with open(FAISS_META_PATH, "rb") as f:
            metadata = pickle.load(f)
    except Exception as e:
        print(f"Error loading metadata from {FAISS_META_PATH}: {e}")
        raise e

    print("Loading embedding model...")
    embedder = SentenceTransformer(EMBED_MODEL)

    print("Initializing Groq client...")
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    print("RAG System Initialized successfully.")

# ================= PROMPTS =================

SYSTEM_PROMPT_A = """You are Nyay Sathi, a helpful Indian legal assistant.
MODE: RAG-BACKED (HIGH CONFIDENCE).

INSTRUCTIONS:
1. You are provided with retrieved legal sections from Indian laws.
2. Answer the USER QUESTION using ONLY the provided LEGAL TEXT.
3. Explicitly mention the Act Name and Section Number if available in the text.
4. Explain the legal provision in simple, clear English suitable for a layperson.
5. If the provided text does not answer the specific question, strictly state that the retrieved sections do not cover it.
6. DO NOT invent laws, punishments, or procedures.
7. DO NOT give legal advice (e.g., "You should file a case").

MANDATORY DISCLAIMER:
End your response with: "Disclaimer: This information is for educational purposes only and does not constitute legal advice."
"""

SYSTEM_PROMPT_B = """You are Nyay Sathi, a helpful Indian legal assistant.
MODE: GENERAL FALLBACK (LOW CONFIDENCE / NO MATCH).

INSTRUCTIONS:
1. No specific legal sections matched the user's query in the database.
2. DO NOT cite specific Acts or Sections.
3. DO NOT invent punishments or legal procedures.
4. Provide a high-level, educational explanation of the concepts related to the user's query.
5. Focus on general ethical, social, or common-sense legal principles in India.
6. Be polite and encouraging. Suggest the user rephrase or add more details.
7. DO NOT give legal advice.

MANDATORY DISCLAIMER:
End your response with: "Disclaimer: This information is for educational purposes only and does not constitute legal advice."
"""

CONFIDENCE_THRESHOLD = 0.50

# ================= CORE LOGIC =================

def retrieve_sections(query):
    query_vec = embedder.encode([query]).astype("float32")
    scores, indices = index.search(query_vec, TOP_K)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        record = metadata[idx].copy()
        record["score"] = float(score)
        results.append(record)

    return results

def explain_with_llm(query, retrieved):
    if not retrieved:
        mode = "fallback"
        top_score = 0.0
    else:
        top_score = retrieved[0]["score"]
        mode = "grounded" if top_score >= CONFIDENCE_THRESHOLD else "fallback"

    if mode == "grounded":
        context_str = ""
        for r in retrieved:
            context_str += (
                f"--- ITEM ---\n"
                f"Act: {r.get('act_name', 'Unknown')}\n"
                f"Section: {r.get('section_number', 'Unknown')}\n"
                f"Text: {r.get('text', '')}\n"
                f"Confidence: {r.get('score'):.2f}\n"
            )

        user_message_content = f"USER QUESTION: {query}\n\nLEGAL TEXT FOUND:\n{context_str}"
        system_role = SYSTEM_PROMPT_A

    else:
        user_message_content = (
            f"USER QUESTION: {query}\n\n"
            f"(No high-confidence legal sections found under threshold {CONFIDENCE_THRESHOLD})"
        )
        system_role = SYSTEM_PROMPT_B

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": user_message_content},
            ],
            temperature=0.1,
            max_tokens=500,
        )

        explanation = response.choices[0].message.content.strip()
        return mode, explanation, top_score

    except Exception as e:
        print(f"LLM Error: {e}")
        return (
            "fallback",
            "System is temporarily unable to generate an explanation due to technical issues. "
            "Disclaimer: This information is for educational purposes only and does not constitute legal advice.",
            0.0,
        )
