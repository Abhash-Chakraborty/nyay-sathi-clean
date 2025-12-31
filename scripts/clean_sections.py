import json
from pathlib import Path

INPUT_FILE = Path("data/processed/normalized_sections.json")
OUTPUT_FILE = Path("data/processed/sections_clean.json")

def is_valid_text(text):
    if not text:
        return False
    if len(text) < 40:
        return False
    
    # Check for truncated endings
    invalid_endings = ("by", "of", "and", ":", "the", "or", "for")
    stripped_text = text.strip()
    if stripped_text.lower().endswith(invalid_endings):
        return False
        
    return True

def clean_data():
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_records = len(data)
    unique_sections = {}
    duplicates_removed = 0
    
    # Deduplication and Grouping
    for record in data:
        key = (record["act_name"], str(record["section_number"]))
        
        if key in unique_sections:
            duplicates_removed += 1
            existing_record = unique_sections[key]
            # Keep the one with longer text
            if len(record.get("text", "")) > len(existing_record.get("text", "")):
                unique_sections[key] = record
        else:
            unique_sections[key] = record

    # Quality Filtering and Schema Enforcement
    clean_records = []
    invalid_dropped = 0
    
    for record in unique_sections.values():
        text = record.get("text", "").strip()
        
        if not is_valid_text(text):
            invalid_dropped += 1
            continue
            
        # Enforce Schema
        clean_record = {
            "id": record["id"],
            "act_name": record["act_name"],
            "act_year": record["act_year"],
            "category": record["category"],
            "section_number": record["section_number"],
            "text": text,
            "source": record.get("source", "India Code")
        }
        clean_records.append(clean_record)

    # Sort for deterministic output
    clean_records.sort(key=lambda x: (x["act_name"], x["id"]))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(clean_records, f, indent=2, ensure_ascii=False)

    print("-" * 30)
    print("DATA CLEANING SUMMARY")
    print("-" * 30)
    print(f"Total input records: {total_records}")
    print(f"After deduplication: {len(unique_sections)}")
    print(f"Duplicates found:    {duplicates_removed}")
    print(f"Invalid dropped:     {invalid_dropped}")
    print(f"FINAL CLEAN COUNT:   {len(clean_records)}")
    print("-" * 30)
    
    # Final Validation
    if len(clean_records) == 0:
        print("CRITICAL WARNING: Output file is empty!")
    else:
        print(f"✅ Success! Clean data written to: {OUTPUT_FILE}")

if __name__ == "__main__":
    clean_data()
