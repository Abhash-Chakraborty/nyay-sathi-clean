import requests
import time
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Optional

# ---------------- CONFIG ----------------

HEADERS = {
    "User-Agent": "LegalRAG-Research/1.0 (Educational Project)"
}

DELAY_SECONDS = 6
TIMEOUT = 30

OUTPUT_DIR = Path(r"C:\My Projects\legal-rag\data\raw\acts_html")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ACT_URLS = [
    "https://www.indiacode.nic.in/handle/123456789/20062?locale=en",
    "https://www.indiacode.nic.in/handle/123456789/20061?locale=en",
    "https://www.indiacode.nic.in/handle/123456789/1657?locale=en",
    "https://www.indiacode.nic.in/handle/123456789/1537?locale=en",
    "https://www.indiacode.nic.in/handle/123456789/2340?locale=en",
    "https://www.indiacode.nic.in/handle/123456789/3002?locale=en",
    "https://www.indiacode.nic.in/handle/123456789/4101?locale=en",
    "https://www.indiacode.nic.in/handle/123456789/2263?locale=en",
]

# ---------------- HELPERS ----------------

def get_real_act_html(handle_url: str) -> Optional[str]:
    """
    Fetch the handle page and try to find the real Act HTML page.
    """
    resp = requests.get(handle_url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    for link in soup.find_all("a", href=True):
        text = link.get_text(strip=True).lower()
        href = link["href"]

        if "view" in text or "act" in text:
            return urljoin(handle_url, href)

    # fallback: use the handle page itself
    return handle_url


def download_act(act_url: str, index: int):
    print(f"\nProcessing ({index}) → {act_url}")

    real_url = get_real_act_html(act_url)
    print(f"Resolved Act URL → {real_url}")

    resp = requests.get(real_url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()

    filename = f"{index:02d}_act.html"
    out_path = OUTPUT_DIR / filename

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(resp.text)

    print(f"Saved usable Act HTML → {out_path}")


# ---------------- MAIN ----------------

def main():
    for idx, url in enumerate(ACT_URLS, start=1):
        try:
            download_act(url, idx)
        except Exception as e:
            print(f"❌ Failed for {url}")
            print(f"Reason: {e}")

        time.sleep(DELAY_SECONDS)

    print("\n✅ All possible Acts processed.")


if __name__ == "__main__":
    main()
