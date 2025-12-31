import json
from pathlib import Path
from bs4 import BeautifulSoup
import re

SECTIONS_DIR = Path("data/raw/sections_html") # Contains .json files now
OUTPUT_FILE = Path("data/processed/sections_full.json")
METADATA_FILE = Path("data/raw/metadata/acts_metadata.json")

def cleanup_text(text):
    if not text:
        return ""
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_text():
    if not SECTIONS_DIR.exists():
        print("Sections dir not found.")
        return

    # Load Metadata Dict
    act_meta_map = {}
    if METADATA_FILE.exists():
         with open(METADATA_FILE, "r", encoding="utf-8") as f:
            meta_raw = json.load(f)
            # Map by act_name or construct a lookup
            # acts_metadata.json keys are weird "India Code: ..." strings.
            # We need to map `act_slug` (from filename) to metadata.
            # We don't have a direct map.
            # We will use the Act Name from the content if possible?
            # Or reliance on normalized map.
            pass

    full_sections = []
    
    # We really need Act Name and Year for the final JSON.
    # We can get "Act Title" often from the `acts_html` title, or we can look it up.
    # Let's assume we can look it up via fuzzy match or we re-read the Act HTML index to get the Title.
    
    # Pre-build slug -> Act Name/Year map
    slug_map = {}
    acts_dir = Path("data/raw/acts_html")
    for act_file in acts_dir.glob("*.html"):
        with open(act_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            title = soup.title.string.replace("India Code:", "").strip() if soup.title else ""
            # Try to parse year
            year = 0
            match = re.search(r'\d{4}', title)
            if match:
                year = int(match.group(0))
            
            slug_map[act_file.stem] = {
                "act_name": title,
                "act_year": year,
                "category": "Uncategorized" # metadata.json has real category if we want
            }

    count = 0
    for json_file in SECTIONS_DIR.glob("*.json"):
        # Ignore debug files
        if "debug" in json_file.name:
            continue
            
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            content_html = data.get("content", "")
            if not content_html:
                continue

            meta = data.get("_meta", {})
            act_slug = meta.get("act_slug", json_file.stem.split("_ord_")[0])
            # Try to get section number from meta or filename orderno
            sec_num = meta.get("section_number", "")
            if not sec_num:
                sec_num = str(meta.get("orderno", "unknown"))
            
            source_url = meta.get("url", "")

            # Parse HTML content
            soup = BeautifulSoup(content_html, "html.parser")
            
            # Extract text
            # The API returns just the content div usually.
            raw_text = soup.get_text(separator="\n")
            
            clean_lines = []
            for line in raw_text.splitlines():
                l = line.strip()
                if l: 
                    clean_lines.append(l)
            
            full_text = "\n".join(clean_lines)

            # Metadata Info
            act_info = slug_map.get(act_slug, {"act_name": act_slug, "act_year": 0, "category": "Unknown"})
            
            # Generate ID
            # clean_id
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', act_info['act_name'].lower())
            rec_id = f"{safe_name}_{act_info['act_year']}_{sec_num}"
            
            record = {
                "id": rec_id,
                "act_name": act_info['act_name'],
                "act_year": act_info['act_year'],
                "category": act_info['category'],
                "section_number": sec_num,
                "section_title": "", # Could try to extract from first line of text
                "text": full_text,
                "source": source_url
            }
            
            full_sections.append(record)
            count += 1
            
        except Exception as e:
            print(f"Error extracting {json_file}: {e}")

    # Deduplicate ID
    # If duplicates, keep longest
    unique_map = {}
    for r in full_sections:
        rid = r['id']
        if rid not in unique_map:
            unique_map[rid] = r
        else:
            if len(r['text']) > len(unique_map[rid]['text']):
                unique_map[rid] = r
    
    final_list = list(unique_map.values())
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_list, f, indent=2, ensure_ascii=False)
        
    print(f"Extracted {len(final_list)} sections.")

if __name__ == "__main__":
    extract_text()
