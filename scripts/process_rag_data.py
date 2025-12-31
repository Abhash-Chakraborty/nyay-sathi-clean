import json
import re
import os
from pathlib import Path
from bs4 import BeautifulSoup
import unicodedata

# Paths
BASE_DIR = Path("c:/My Projects/legal-rag")
RAW_SECTIONS_DIR = BASE_DIR / "data/raw/sections_html"
ACTS_HTML_DIR = BASE_DIR / "data/raw/acts_html"
METADATA_FILE = BASE_DIR / "data/raw/metadata/acts_metadata.json"
OUTPUT_DIR = BASE_DIR / "data/processed"
MASTER_FILE = OUTPUT_DIR / "sections_master.json"
CHUNKS_FILE = OUTPUT_DIR / "sections_chunks.json"

# Config
MIN_TEXT_LENGTH = 150
CHUNK_SIZE_LIMIT = 600  # Target tokens
CHUNK_OVERLAP = 50

def normalize_text(text):
    """Normalize whitespace and remove excessive newlines."""
    if not text: return ""
    # Remove zero-width spaces and specific footer artifacts
    text = text.replace('\u200b', '')
    text = re.sub(r'</?br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<hr[^>]*>', ' ', text, flags=re.IGNORECASE)
    
    # Strip HTML tags
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator="\n")
    
    # Normalize whitespace
    text = unicodedata.normalize('NFKD', text)
    lines = [line.strip() for line in text.split('\n')]
    text = "\n".join([l for l in lines if l])
    return text

def load_act_metadata():
    """Load high-level act metadata."""
    if not METADATA_FILE.exists():
        print("Warning: Metadata file not found.")
        return {}
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def build_section_title_map():
    """Parse Act HTMLs to map sectionId/sectionno to titles."""
    print("Building Section Title Map from Act HTMLs...")
    mapping = {} # Key: (act_slug, section_number) or (act_slug, section_id) -> Title
    
    for html_file in ACTS_HTML_DIR.glob("*.html"):
        act_slug = html_file.stem
        # Try to find act_name from file content if possible, or just use slug
        
        with open(html_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            
            # The structure in previous logs showed links with text inside
            # <a href="...sectionId=...">Title</a>
            links = soup.find_all("a", href=True)
            for link in links:
                href = link["href"]
                if "show-data" in href and "sectionId" in href:
                    text = link.get_text(" ", strip=True)
                    # Text usually contains "Section X - Title" or just "Title"
                    # But we need to link it to the ID.
                    qs_match = re.search(r'sectionId=(\d+)', href, re.IGNORECASE)
                    sec_no_match = re.search(r'sectionno=([^&]+)', href, re.IGNORECASE)
                    
                    if qs_match:
                        sec_id = qs_match.group(1)
                        mapping[(act_slug, sec_id)] = text
                    
                    if sec_no_match:
                         sec_no = sec_no_match.group(1)
                         # mapping[(act_slug, sec_no)] = text # Risk of collision if multiple acts
    print(f"Mapped {len(mapping)} titles.")
    return mapping

def simple_tokenize(text):
    """Approximate token counting (whitespace split). Good enough for now."""
    return text.split()

def chunk_text(text, chunk_size=500, overlap=50):
    """Chunk text by words/tokens, respecting sentence boundaries where possible."""
    words = simple_tokenize(text)
    if not words: return []
    
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        
        # Look ahead/behind for sentence ending to be cleaner? 
        # For simplicity, strict overlap for now, maybe soft boundary.
        
        chunk_words = words[start:end]
        chunk_str = " ".join(chunk_words)
        chunks.append(chunk_str)
        
        start += (chunk_size - overlap)
        
    return chunks

def process_data():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Metadata
    acts_meta = load_act_metadata() # Official names
    # Reverse map acts_meta keys (Titles) to slugs isn't direct. 
    # We'll rely on what's in the per-section JSON or hardcode mapping if needed.
    
    title_map = build_section_title_map()
    
    # 2. Consolidate
    consolidated = {} # Key: ID -> Record
    
    files = list(RAW_SECTIONS_DIR.glob("*.json"))
    print(f"Processing {len(files)} raw files...")
    
    files_dropped = 0
    
    for f in files:
        if f.name == "debug_api_response.json": continue
        
        try:
            with open(f, "r", encoding="utf-8") as fin:
                data = json.load(fin)
                
            meta = data.get("_meta", {})
            act_slug = meta.get("act_slug", f.stem.split("_ord_")[0]) # naming convention
            sec_id = meta.get("section_id", "")
            orderno = meta.get("orderno", "")
            
            raw_content = data.get("content", "")
            if not raw_content:
                files_dropped += 1
                continue
                
            clean_text = normalize_text(raw_content)
            
            if len(clean_text) < MIN_TEXT_LENGTH:
                files_dropped += 1
                continue

            # Metadata Enhancement
            # Try to get better info
            
            # Construct Stable ID
            # act_slug + section_number (if available) or orderno
            # We prefer section_number (e.g. "302") over orderno (index)
            # We can extract section number from the content usually? "Section 3. Title..."
            # Or use correct logic.
            
            # Heuristic to find section number in text start
            match_sec = re.match(r'^\(?(\d+[A-Za-z]?)\)?', clean_text)
            if match_sec:
                possible_sec_num = match_sec.group(1)
            else:
                possible_sec_num = str(orderno)
            
            unique_id = f"{act_slug}_section_{possible_sec_num}"
            
            # Title Lookup
            section_title = title_map.get((act_slug, sec_id), "")
            if not section_title:
                 # Try cleaning from text?
                 pass

            # Act Name Handling
            # Map slug to real name if possible. 
            # Current slug: "01_act" -> "Bharatiya Nyaya Sanhita, 2023" (Needs manual map or intelligent map)
            # For now, beautify slug
            act_name_formatted = act_slug.replace("_", " ").title()
            # Special case for known slug
            if "01_act" in act_slug: act_name_formatted = "Bharatiya Nyaya Sanhita, 2023"
            
            record = {
                "id": unique_id,
                "act_name": act_name_formatted,
                "act_year": 2023 if "2023" in act_name_formatted else 0, # Simple heuristic
                "category": "Criminal Law" if "Sanhita" in act_name_formatted else "General",
                "section_number": possible_sec_num,
                "section_title": section_title,
                "section_text": clean_text,
                "source": meta.get("url", f"file://{f.name}")
            }
            
            # Dedupe: Keep longest text
            if unique_id in consolidated:
                if len(clean_text) > len(consolidated[unique_id]["section_text"]):
                    consolidated[unique_id] = record
            else:
                consolidated[unique_id] = record
                
        except Exception as e:
            print(f"Error processing {f.name}: {e}")
            files_dropped += 1

    print(f"Consolidation Complete. Master Records: {len(consolidated)}. Dropped: {files_dropped}")
    
    # Save Master
    final_list = list(consolidated.values())
    with open(MASTER_FILE, "w", encoding="utf-8") as f_out:
        json.dump(final_list, f_out, indent=2)
        
    # 3. Chunking
    print("Chunking...")
    chunks = []
    chunk_count = 0
    
    for rec in final_list:
        text_chunks = chunk_text(rec["section_text"], chunk_size=CHUNK_SIZE_LIMIT, overlap=CHUNK_OVERLAP)
        
        for i, txt in enumerate(text_chunks):
            chunk_id = f"{rec['id']}_chunk_{i+1}"
            chunk_record = {
                "chunk_id": chunk_id,
                "parent_id": rec["id"],
                "act_name": rec["act_name"],
                "act_year": rec["act_year"],
                "category": rec["category"],
                "section_number": rec["section_number"],
                "section_title": rec["section_title"],
                "text": txt,
                "source": rec["source"]
            }
            chunks.append(chunk_record)
            chunk_count += 1
            
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f_chunk:
        json.dump(chunks, f_chunk, indent=2)
        
    print(f"Chunking Complete. Generated {chunk_count} chunks.")
    
    # Validation Stats
    avg_size = sum(len(c["text"]) for c in chunks) / chunk_count if chunk_count else 0
    print(f"Average Chunk Size (chars): {int(avg_size)}")

if __name__ == "__main__":
    process_data()
