import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import sys

# ---------------- CONFIG ----------------

FAISS_INDEX_FILE = Path("data/processed/faiss.index")
META_FILE = Path("data/processed/faiss_meta.pkl")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 5


# ---------------- LOADERS ----------------

def load_faiss():
    if not FAISS_INDEX_FILE.exists():
        print(f"Error: FAISS index not found: {FAISS_INDEX_FILE}")
        sys.exit(1)

    if not META_FILE.exists():
        print(f"Error: Metadata file not found: {META_FILE}")
        sys.exit(1)

    print("Loading FAISS index...")
    try:
        index = faiss.read_index(str(FAISS_INDEX_FILE))
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        sys.exit(1)

    print("Loading metadata...")
    try:
        with open(META_FILE, "rb") as f:
            metadata = pickle.load(f)
    except Exception as e:
        print(f"Error loading metadata: {e}")
        sys.exit(1)

    print(f"FAISS vectors loaded: {index.ntotal}")
    print(f"Metadata records loaded: {len(metadata)}")

    return index, metadata


def load_model():
    print(f"Loading embedding model: {MODEL_NAME}")
    try:
        model = SentenceTransformer(MODEL_NAME)
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)


# ---------------- SEARCH ----------------

def search(query, model, index, metadata, top_k=TOP_K):
    print(f"\nQuery: {query}")

    try:
        query_embedding = model.encode(
            query,
            normalize_embeddings=True
        )
    except Exception as e:
        print(f"Error encoding query: {e}")
        return []

    query_embedding = np.array([query_embedding])

    scores, indices = index.search(query_embedding, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        
        if idx < len(metadata):
            record = metadata[idx].copy()
            record["score"] = float(score)
            results.append(record)
        else:
            print(f"Warning: Index {idx} out of bounds for metadata.")

    return results


# ---------------- DISPLAY ----------------

def display_results(results):
    if not results:
        print("No relevant sections found.")
        return

    print("\nRelevant Legal Sections (Informational Only):\n")

    for i, r in enumerate(results, 1):
        print(f"{i}. Act: {r.get('act_name', 'Unknown')}")
        print(f"   Section: {r.get('section_number', 'N/A')}")
        print(f"   Category: {r.get('category', 'N/A')}")
        print(f"   Relevance Score: {round(r['score'], 3)}")
        print("   Text:")
        print(f"   {r.get('text', '')[:800]}...")  # limit display
        print("-" * 80)

    print(
        "\nDisclaimer: This information is for educational purposes only "
        "and does not constitute legal advice."
    )


# ---------------- MAIN LOOP ----------------

def main():
    print("Starting Legal RAG System...")
    index, metadata = load_faiss()
    model = load_model()

    print("\nLegal RAG system is ready.")
    print("Type your legal question below.")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            query = input("Your question: ").strip()
        except EOFError:
            break
            
        if query.lower() in {"exit", "quit"}:
            print("Exiting.")
            break
        
        if not query:
            continue

        results = search(query, model, index, metadata)
        display_results(results)


if __name__ == "__main__":
    main()
