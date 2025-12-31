import requests
import time
from pathlib import Path
from urllib.parse import urlparse

# -------- CONFIG --------
HEADERS = {
    "User-Agent": "Educational-Legal-Research/1.0 (student project)"
}

DELAY_SECONDS = 8  # polite delay
TIMEOUT = 30

BASE_DIR = Path(__file__).resolve().parent.parent
HTML_DIR = BASE_DIR / "data" / "raw" / "acts_html"
PDF_DIR = BASE_DIR / "data" / "raw" / "acts_pdf"

HTML_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)

URLS_FILE = BASE_DIR / "acts_urls.txt"

# -------- FUNCTIONS --------
def is_pdf(url: str) -> bool:
    return url.lower().endswith(".pdf")

def safe_filename(url: str, index: int) -> str:
    parsed = urlparse(url)
    name = parsed.path.split("/")[-1]
    if not name:
        name = f"act_{index}"
    return f"{index:02d}_{name}"

def download(url: str, index: int):
    print(f"\nDownloading ({index}) → {url}")
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()

    if is_pdf(url):
        filename = safe_filename(url, index)
        path = PDF_DIR / filename
        with open(path, "wb") as f:
            f.write(response.content)
        print(f"Saved PDF → {path}")

    else:
        filename = safe_filename(url, index) + ".html"
        path = HTML_DIR / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"Saved HTML → {path}")

# -------- MAIN --------
def main():
    if not URLS_FILE.exists():
        raise FileNotFoundError("acts_urls.txt not found")

    with open(URLS_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    for idx, url in enumerate(urls, start=1):
        try:
            download(url, idx)
        except Exception as e:
            print(f"❌ Failed to download {url}")
            print(e)

        print(f"Waiting {DELAY_SECONDS} seconds...")
        time.sleep(DELAY_SECONDS)

    print("\n✅ Download complete.")

if __name__ == "__main__":
    main()
