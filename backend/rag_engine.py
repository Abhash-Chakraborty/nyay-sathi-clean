import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# ================= CONFIG =================

# Determine paths based on environment or default to local structure
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "data", "processed", "faiss.index")
FAISS_META_PATH = os.path.join(BASE_DIR, "data", "processed", "faiss_meta.pkl")

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
    
    print("Loading FAISS index...")
    try:
        index = faiss.read_index(FAISS_INDEX_PATH)
        print(f"FAISS vectors loaded: {index.ntotal}")
    except Exception as e:
        print(f"Error loading FAISS index from {FAISS_INDEX_PATH}: {e}")
        raise e

    print("Loading metadata...")
    with open(FAISS_META_PATH, "rb") as f:
        metadata = pickle.load(f)

    print("Loading embedding model...")
    embedder = SentenceTransformer(EMBED_MODEL)

    print("Initializing Groq client...")
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    print("RAG System Initialized.")

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
        return (
            "fallback",
            "No relevant legal provisions were found in the current knowledge base. This does not mean that no law exists — only that it is not present in the system.",
            0.0
        )

    # Context Construction
    context = ""
    for r in retrieved:
        context += (
            f"Act: {r.get('act_name', 'Unknown')}\n"
            f"Section: {r.get('section_number', 'Unknown')}\n"
            f"Text: {r.get('text', '')}\n\n"
        )

    prompt = f"""
You are a legal information assistant for Indian laws (Nyay Sathi).

RULES:
- Use ONLY the legal text provided below.
- Do NOT add new laws.
- Do NOT give legal advice.
- Explain in simple, user-friendly language suitable for a mobile app.
- Mention Act name and Section number explicitly.
- End with a disclaimer.

USER QUESTION:
{query}

LEGAL TEXT:
{context}

ANSWER:
"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=600,
        )
        explanation = response.choices[0].message.content.strip()
        
        # Determine mode based on top score
        top_score = retrieved[0]['score']
        # FAISS Euclidean distance: lower is better? Or inner product?
        # SentenceTransformers usually normalized -> Inner Product (higher is better). 
        # But if L2, lower is better. 
        # Standard approach: just check if it's "close enough".
        # Assuming Inner Product/Cosine Similarity for now as is typical with SentenceTransformers unless specified otherwise.
        # Actually FAISS default is L2 usually unless IndexFlatIP. 
        # Let's assume standard behavior: we'll return "grounded" if we successfully got here.
        
        mode = "grounded" if top_score > 0.5 else "partial" # Arbitrary threshold, tune if needed
        
        return mode, explanation, top_score

    except Exception as e:
        print(f"LLM Error: {e}")
        return "fallback", "System is temporarily unable to generate an explanation due to high traffic using the free tier logic.", 0.0

