import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

# ---------------- CONFIG ----------------

INPUT_DIR = Path("data/raw/acts_html")
OUTPUT_DIR = Path("data/processed/sections_json")

INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------- HELPERS ----------------

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_act_name(soup: BeautifulSoup) -> str:
    if soup.find("h1"):
        return clean_text(soup.find("h1").get_text())
    if soup.title:
        return clean_text(soup.title.get_text())
    return "Unknown Act"


def extract_sections_from_text(full_text: str):
    """
    Extract sections using legal numbering patterns.
    """
    sections = []

    # Pattern matches:
    # 1. Title
    # 1A. Title
    # Section 1
    section_pattern = re.compile(
        r"(?:Section\s+)?(\d+[A-Z]?)\.\s",
        re.IGNORECASE
    )

    matches = list(section_pattern.finditer(full_text))

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)

        section_number = match.group(1)
        section_text = full_text[start:end]

        sections.append({
            "section_number": section_number,
            "section_text": clean_text(section_text)
        })

    return sections


# ---------------- MAIN ----------------

def main():
    html_files = list(INPUT_DIR.glob("*.html"))

    if not html_files:
        print("❌ No HTML files found.")
        return

    for html_file in html_files:
        print(f"\nParsing → {html_file.name}")

        with open(html_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        act_name = extract_act_name(soup)

        # Get all visible text
        full_text = soup.get_text(separator=" ", strip=True)
        full_text = clean_text(full_text)

        sections = extract_sections_from_text(full_text)

        output_data = {
            "act_name": act_name,
            "source_file": html_file.name,
            "sections_count": len(sections),
            "sections": sections
        }

        out_file = OUTPUT_DIR / f"{html_file.stem}.json"

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"Saved → {out_file} ({len(sections)} sections)")

    print("\n✅ All Acts parsed with section detection.")


if __name__ == "__main__":
    main()
