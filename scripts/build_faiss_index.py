import json
import pickle
import os
import sys
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Constants
DATA_FILE = "data/processed/sections_chunks.json"
INDEX_FILE = "data/processed/faiss.index"
META_FILE = "data/processed/faiss_meta.pkl"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def main():
    print(f"Starting FAISS index build...")
    
    # 1. Load Data
    if not os.path.exists(DATA_FILE):
        print(f"Error: Data file not found at {DATA_FILE}")
        sys.exit(1)
        
    print(f"Loading chunks from {DATA_FILE}...")
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    if not chunks:
        print("Error: No chunks found in data file.")
        sys.exit(1)
        
    print(f"Loaded {len(chunks)} chunks.")
    
    # Extract texts for embedding
    texts = [chunk.get('text', '') for chunk in chunks]
    
    # 2. Generate Embeddings
    print(f"Loading embedding model: {MODEL_NAME}...")
    try:
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)
        
    print("Generating embeddings (this may take a while)...")
    # Normalize embeddings to use Cosine Similarity with Inner Product (IP) index
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)
    
    print(f"Embeddings shape: {embeddings.shape}")
    
    # 3. Build FAISS Index
    print("Building FAISS index...")
    dimension = embeddings.shape[1]
    
    # IndexFlatIP uses Inner Product (Dot Product). 
    # Since embeddings are normalized, this equals Cosine Similarity.
    index = faiss.IndexFlatIP(dimension)
    
    index.add(embeddings)
    
    print(f"Index built. Total vectors: {index.ntotal}")
    
    # 4. Save Outputs
    print(f"Saving index to {INDEX_FILE}...")
    try:
        os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
        faiss.write_index(index, INDEX_FILE)
    except Exception as e:
        print(f"Error saving index: {e}")
        sys.exit(1)
        
    print(f"Saving metadata to {META_FILE}...")
    try:
        with open(META_FILE, 'wb') as f:
            pickle.dump(chunks, f)
    except Exception as e:
        print(f"Error saving metadata: {e}")
        sys.exit(1)
        
    # Final Verification
    if os.path.exists(INDEX_FILE) and os.path.exists(META_FILE):
        print("\nSUCCESS: FAISS index and metadata build complete.")
        print(f"Files saved:\n- {INDEX_FILE}\n- {META_FILE}")
        print(f"Total number of vectors stored: {index.ntotal}")
    else:
        print("\nWARNING: Verification failed. Output files missing.")

if __name__ == "__main__":
    main()
