import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ACT_FILE = Path("data/raw/acts_html/01_act.html")

def test():
    with open(ACT_FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    links = soup.find_all("a", href=True)
    count = 0
    for link in links:
        href = link["href"]
        if "show-data" in href:
            count += 1
            print(f"Link {count}:")
            print(f"  Href: {href}")
            parsed = urlparse(href)
            print(f"  Query: {parsed.query}")
            qs = parse_qs(parsed.query)
            print(f"  Keys: {qs.keys()}")
            
            if count >= 30:
                break

if __name__ == "__main__":
    test()
