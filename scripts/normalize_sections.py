import json
from pathlib import Path

INPUT_DIR = Path("data/processed/sections_json")
METADATA_FILE = Path("data/raw/metadata/acts_metadata.json")
OUTPUT_FILE = Path("data/processed/normalized_sections.json")

with open(METADATA_FILE, "r", encoding="utf-8") as f:
    ACT_METADATA = json.load(f)

normalized_records = []

for json_file in INPUT_DIR.glob("*.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_title = data.get("act_name", "")
    act_title = raw_title.strip()

    if "Invalid URL" in act_title:
        continue

    if act_title not in ACT_METADATA:
        print(f"⚠️ Metadata not found for: {act_title}")
        continue

    meta = ACT_METADATA[act_title]

    for section in data.get("sections", []):
        section_number = section.get("section_number")
        text = section.get("section_text")

        if not section_number or not text:
            continue

        record = {
            "id": f"{meta['act_name'].lower().replace(' ', '_')}_{meta['year']}_{section_number}",
            "act_name": meta["act_name"],
            "act_year": meta["year"],
            "category": meta["category"],
            "section_number": section_number,
            "text": text,
            "source": "India Code"
        }

        normalized_records.append(record)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(normalized_records, f, indent=2, ensure_ascii=False)

print(f"✅ Normalized {len(normalized_records)} sections.")
