import requests
from bs4 import BeautifulSoup

# URL from 01_act.html
test_href = "/show-data?abv=CEN&statehandle=123456789/1362&actid=AC_CEN_5_23_00048_2023-45_1719292564123&sectionId=90366&sectionno=1&orderno=1&orgactid=AC_CEN_5_23_00048_2023-45_1719292564123"
base_url = "https://www.indiacode.nic.in"
full_url = base_url + test_href

print(f"Testing URL: {full_url}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    resp = requests.get(full_url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Content Length: {len(resp.text)}")
    if "Invalid URL" in resp.text:
        print("Result: INVALID URL ERROR page detected.")
    else:
        print("Result: Seems VALID (no 'Invalid URL' string found).")
        # Print snippet
        soup = BeautifulSoup(resp.text, "html.parser")
        print("Title:", soup.title.string.strip() if soup.title else "No Title")
        
except Exception as e:
    print(f"Error: {e}")

# Test OrderNo URL
print("\nTesting OrderNo URL...")
# https://www.indiacode.nic.in/show-data?actid=AC_CEN_5_23_00048_2023-45_1719292564123&orderno=2
orderno_url = "https://www.indiacode.nic.in/show-data?actid=AC_CEN_5_23_00048_2023-45_1719292564123&orderno=2"
print(f"Testing URL: {orderno_url}")
try:
    resp = requests.get(orderno_url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    if "Invalid URL" in resp.text:
         print("Result: INVALID URL ERROR.")
    else:
         print("Result: Seems VALID")
         soup = BeautifulSoup(resp.text, "html.parser")
         print("Title:", soup.title.string.strip() if soup.title else "No Title")
         # Check for secId variable
         if "secId" in resp.text:
             print("Found secId in text.")
except Exception as e:
    print(f"Error: {e}")

# Test Internal API
print("\nTesting /SectionPageContent API...")
# https://www.indiacode.nic.in/SectionPageContent?actid=...&sectionID=...
api_url = "https://www.indiacode.nic.in/SectionPageContent?actid=AC_CEN_5_23_00048_2023-45_1719292564123&sectionID=90366"
print(f"Testing URL: {api_url}")

try:
    resp = requests.get(api_url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Content Type: {resp.headers.get('Content-Type')}")
    
    # It should be JSON
    try:
        data = resp.json()
        print("Keys:", data.keys())
        print("Content Snippet:", data.get("content", "")[:100])
        with open("data/raw/sections_html/debug_api_response.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as je:
        print(f"JSON Parse Error: {je}")
        print("Raw Text:", resp.text[:200])

except Exception as e:
    print(f"Error: {e}")
