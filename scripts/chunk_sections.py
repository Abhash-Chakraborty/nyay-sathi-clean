import json
from pathlib import Path

INPUT_FILE = Path("data/processed/sections_clean.json")
OUTPUT_FILE = Path("data/processed/sections_chunks.json")

# Constants for chunking
CHUNK_SIZE = 450  # Target tokens
CHUNK_OVERLAP = 50 # Overlap tokens
TOKEN_RATIO = 4.0 # Approx characters per token

def estimate_tokens(text):
    return len(text) / TOKEN_RATIO

def split_text_into_chunks(text, max_tokens=500, overlap_tokens=50):
    """
    Splits text into chunks respecting sentence boundaries where possible.
    """
    if estimate_tokens(text) <= max_tokens:
        return [text]
    
    # Split into sentences (simple approximation)
    sentences = text.replace(";", ".").split(".")
    
    chunks = []
    current_chunk = []
    current_length = 0
    overlap_buffer = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        sentence = sentence + "."
        sent_len = estimate_tokens(sentence)
        
        # If adding this sentence exceeds strict limit, finalize current chunk
        if current_length + sent_len > max_tokens and current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)
            
            # Start new chunk with overlap
            # Keep last few sentences that fit in overlap size
            overlap_len = 0
            new_start = []
            for s in reversed(current_chunk):
                s_len = estimate_tokens(s)
                if overlap_len + s_len <= overlap_tokens:
                    new_start.insert(0, s)
                    overlap_len += s_len
                else:
                    break
            
            current_chunk = new_start
            current_length = overlap_len
            
        current_chunk.append(sentence)
        current_length += sent_len
        
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

def chunk_data():
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_chunks = []
    total_sections = 0
    
    for record in data:
        total_sections += 1
        text = record.get("text", "")
        
        text_chunks = split_text_into_chunks(text, max_tokens=CHUNK_SIZE, overlap_tokens=CHUNK_OVERLAP)
        
        for i, chunk_text in enumerate(text_chunks):
            chunk_id = f"{record['id']}_chunk_{i+1}"
            
            chunk_record = {
                "chunk_id": chunk_id,
                "parent_id": record["id"],
                "act_name": record["act_name"],
                "act_year": record["act_year"],
                "category": record["category"],
                "section_number": record["section_number"],
                "text": chunk_text,
                "source": record.get("source", "India Code")
            }
            all_chunks.append(chunk_record)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    avg_size = sum(estimate_tokens(c["text"]) for c in all_chunks) / len(all_chunks) if all_chunks else 0

    print("-" * 30)
    print("CHUNKING SUMMARY")
    print("-" * 30)
    print(f"Total sections processed: {total_sections}")
    print(f"Total chunks generated:   {len(all_chunks)}")
    print(f"Average chunk size:       {avg_size:.2f} tokens")
    print("-" * 30)
    
    if total_sections > 0 and len(all_chunks) >= total_sections:
         print(f"✅ Success! Chunked data written to: {OUTPUT_FILE}")
    else:
         print("WARNING: Chunk count suspicious.")

if __name__ == "__main__":
    chunk_data()
