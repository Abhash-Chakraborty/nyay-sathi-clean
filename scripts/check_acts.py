import json
from pathlib import Path

INPUT_DIR = Path("data/processed/sections_json")
act_names = set()

for json_file in INPUT_DIR.glob("*.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        act_names.add(data.get("act_name", ""))

print("Unique Act Names:")
for name in sorted(act_names):
    print(f"'{name}'")
