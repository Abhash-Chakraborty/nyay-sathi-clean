from bs4 import BeautifulSoup
from pathlib import Path

ACT_FILE = Path("data/raw/acts_html/01_act.html")

with open(ACT_FILE, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

meta = soup.find("meta", attrs={"name": "DC.identifier"})
# Just find all and filter
metas = soup.find_all("meta", attrs={"name": "DC.identifier"})
for m in metas:
    c = m.get("content", "")
    print(f"Meta Identifier: {c}")
    if c.startswith("AC_") or c.startswith("act"):
        actid = c

print(f"Selected Act ID: {actid}")
expected = "AC_CEN_5_23_00048_2023-45_1719292564123"
print(f"Match Expected: {actid == expected}")
