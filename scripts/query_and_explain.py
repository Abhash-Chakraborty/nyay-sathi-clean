import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer
from groq import Groq

# ================= CONFIG =================

FAISS_INDEX_PATH = "data/processed/faiss.index"
FAISS_META_PATH = "data/processed/faiss_meta.pkl"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ✅ CURRENTLY SUPPORTED GROQ MODEL (as of now)
GROQ_MODEL = "llama3-8b-8192"

TOP_K = 5

# ================= LOADERS =================

def load_faiss_index():
    index = faiss.read_index(FAISS_INDEX_PATH)
    print(f"FAISS vectors loaded: {index.ntotal}")
    return index


def load_metadata():
    with open(FAISS_META_PATH, "rb") as f:
        return pickle.load(f)


# ================= RETRIEVAL =================

def retrieve_sections(query, index, metadata, embedder):
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


# ================= LLM EXPLANATION =================

def explain_with_llm(query, retrieved, client):
    if not retrieved:
        return (
            "No relevant legal provisions were found in the current knowledge base.\n\n"
            "This does not mean that no law exists — only that it is not present in the loaded data.\n\n"
            "Disclaimer: This information is for educational purposes only and is not legal advice."
        )

    context = ""
    for r in retrieved:
        context += (
            f"Act: {r.get('act_name', 'Unknown')}\n"
            f"Section: {r.get('section_number', 'Unknown')}\n"
            f"Text: {r.get('text', '')}\n\n"
        )

    prompt = f"""
You are a legal information assistant for Indian laws.

RULES:
- Use ONLY the legal text provided.
- Do NOT add new laws.
- Do NOT give legal advice.
- Explain in simple, user-friendly language.
- Mention Act name and Section number.
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
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        # ✅ SAFE FALLBACK (system NEVER crashes)
        fallback = (
            "Based on the retrieved legal provisions:\n\n"
        )
        for r in retrieved:
            fallback += (
                f"- {r.get('act_name', 'Unknown')} "
                f"(Section {r.get('section_number', 'Unknown')})\n"
            )

        fallback += (
            "\nA detailed explanation could not be generated at this time.\n\n"
            "Disclaimer: This information is for educational purposes only "
            "and does not constitute legal advice."
        )
        return fallback


# ================= DISPLAY =================

def display_results(results):
    print("\nRelevant Legal Sections:\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. Act: {r.get('act_name', 'Unknown')}")
        print(f"   Section: {r.get('section_number', 'Unknown')}")
        print(f"   Relevance Score: {round(r['score'], 3)}")
        print(f"   Text: {r.get('text', '')[:500]}...")
        print("-" * 80)


# ================= MAIN LOOP =================

def main():
    print("\nStarting Legal RAG System...\n")

    index = load_faiss_index()
    metadata = load_metadata()
    embedder = SentenceTransformer(EMBED_MODEL)
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    print("Legal RAG system is ready.")
    print("Type your legal question below.")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        query = input("Your question: ").strip()

        if query.lower() in {"exit", "quit"}:
            print("Exiting system.")
            break

        results = retrieve_sections(query, index, metadata, embedder)
        display_results(results)

        print("\nExplanation:\n")
        explanation = explain_with_llm(query, results, client)
        print(explanation)

        print("\n" + "=" * 100 + "\n")


# ================= ENTRY =================

if __name__ == "__main__":
    main()
