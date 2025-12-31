import os
import sys

# Ensure backend dir is in path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from rag_engine import initialize_rag, retrieve_sections, explain_with_llm

def test_rag():
    print("Initializing RAG...")
    initialize_rag()
    
    query = "What is the punishment for theft?"
    print(f"\nQuery: {query}")
    
    print("Retrieving...")
    results = retrieve_sections(query)
    for r in results:
        print(f"- {r.get('act_name')} ({r.get('section_number')})")
        
    print("\nExplaining (checking Groq key)...")
    mode, explanation, conf = explain_with_llm(query, results)
    print(f"Mode: {mode}")
    print(f"Confidence: {conf}")
    print(f"Explanation Preview: {explanation[:100]}...")
    
    if mode == 'grounded' and len(results) > 0:
        print("\nSUCCESS: RAG pipeline is working with Real Data.")
    else:
        print("\nWARNING: Pipeline finished but results seem weak.")

if __name__ == "__main__":
    test_rag()
