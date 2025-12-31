import os
import time
import requests
import json
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ACTS_HTML_DIR = Path("data/raw/acts_html")
SECTIONS_DIR = Path("data/raw/sections_html")
BASE_URL = "https://www.indiacode.nic.in"
SHOW_DATA_URL = "https://www.indiacode.nic.in/show-data"
API_ENDPOINT = "https://www.indiacode.nic.in/SectionPageContent"

def fetch_sections():
    if not ACTS_HTML_DIR.exists():
        print(f"Error: {ACTS_HTML_DIR} does not exist.")
        return

    SECTIONS_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    })

    from bs4 import BeautifulSoup

    for act_file in ACTS_HTML_DIR.glob("*.html"):
        print(f"Processing Act: {act_file.name}")
        act_slug = act_file.stem
        
        # 1. Get Act ID from the file (meta tag)
        actid = None
        with open(act_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            # Look for <meta name="DC.identifier" content="AC_...">
            metas = soup.find_all("meta", attrs={"name": "DC.identifier"})
            for m in metas:
                c = m.get("content", "")
                if c.startswith("AC_") or c.startswith("act"):
                    actid = c
                    break
        
        # Fallback to link search if meta fails (rare)
        if not actid:
            for link in soup.find_all("a", href=True):
                if "show-data" in link["href"]:
                    qs = parse_qs(urlparse(link["href"]).query)
                    for k, v in qs.items():
                         if k.lower() == "actid":
                             actid = v[0]
                             break
                    if actid: break
        
        if not actid:
            print(f"  Could not find actid for {act_file.name}. Skipping.")
            continue
            
        print(f"  Act ID: {actid}")
        
        # 2. Iterate OrderNo
        orderno = 1
        max_errors = 20 # Tolerant range
        error_count = 0
        
        while True:
            # Check if file already exists (optimization)
            # Since we construct filename with secId, we don't know it yet.
            # But we can check if we have a file with this orderno?
            # Creating a map of existing files might be expensive every loop.
            # Let's just fetch. Be polite.
            
            # Fetch Page
            page_url = f"{SHOW_DATA_URL}?actid={actid}&orderno={orderno}"
            try:
                # print(f"    Fetching OrderNo {orderno}...")
                resp = session.get(page_url, timeout=10)
                
                if "Invalid URL" in resp.text:
                    print(f"    OrderNo {orderno}: Invalid URL.")
                    # Don't stop immediately. Tolerating consecutive errors.
                    error_count += 1
                    if error_count > max_errors: # e.g. 5 consecutive
                         print("    Too many errors. Stopping Act.")
                         break
                    orderno += 1
                    continue
                
                # Check for other errors
                if resp.status_code != 200:
                    print(f"    OrderNo {orderno}: Status {resp.status_code}.")
                    error_count += 1
                    if error_count > max_errors: break
                    orderno += 1
                    continue
                
                # Use greedy regex for secId
                match = re.search(r"secId\s*=\s*'(\d+)';", resp.text)
                if not match:
                     match = re.search(r"sectionId\s*=\s*'(\d+)';", resp.text)
                
                if not match:
                     # print(f"    OrderNo {orderno}: No secId found.")
                     # Not every orderno is a section (e.g. could be chapter header page?)
                     # But valid show-data pages usually have secId.
                     error_count += 1 # Count as error-like?
                     if error_count > max_errors: break
                     orderno += 1
                     continue
                
                secId = match.group(1)
                
                # Check if exists
                safe_sec_num = str(orderno) # User wants valid section number, but orderno is proxy.
                # Use secId in filename to be unique
                filename = f"{act_slug}_ord_{orderno}_sec_{secId}.json"
                filepath = SECTIONS_DIR / filename
                
                if filepath.exists():
                     # print(f"    Skipping {filename} (exists)")
                     orderno += 1
                     continue
                
                # Fetch API Content
                # Needs header X-Requested-With
                headers_api = session.headers.copy()
                headers_api["X-Requested-With"] = "XMLHttpRequest"
                
                api_params = {"actid": actid, "sectionID": secId}
                api_resp = session.get(API_ENDPOINT, params=api_params, headers=headers_api, timeout=10)
                
                if api_resp.status_code == 200:
                     data = api_resp.json()
                     data["_meta"] = {
                         "act_slug": act_slug,
                         "act_id": actid,
                         "section_id": secId,
                         "orderno": orderno,
                         "url": page_url
                     }
                     with open(filepath, "w", encoding="utf-8") as f_out:
                         json.dump(data, f_out, indent=2)
                     print(f"    Saved: {filename}")
                     error_count = 0 # swift success
                else:
                     print(f"    API Failed {api_resp.status_code} for {secId}")
                
            except Exception as e:
                print(f"    Error on OrderNo {orderno}: {e}")
                error_count += 1
                if error_count > max_errors: break
            
            orderno += 1
            # Simple limiter
            if orderno > 2000:
                print("    Reached safety limit 2000. Stopping Act.")
                break
                
            time.sleep(0.05) # fast

if __name__ == "__main__":
    fetch_sections()
