from urllib.parse import urlparse, parse_qs

href = "/show-data?abv=CEN&statehandle=123456789/1362&actid=AC_CEN_5_23_00048_2023-45_1719292564123&sectionId=90366&sectionno=1&orderno=1&orgactid=AC_CEN_5_23_00048_2023-45_1719292564123"

print(f"Testing href: {href}")
parsed = urlparse(href)
qs = parse_qs(parsed.query)
print(f"QS Keys: {qs.keys()}")
print(f"QS: {qs}")

actid = None
for k, v in qs.items():
    if k.lower() == "actid":
        actid = v[0] if v else None
        print(f"Match actid: {k} -> {actid}")

sectionId = None
for k, v in qs.items():
    if k.lower() == "sectionid":
        sectionId = v[0] if v else None
        print(f"Match sectionId: {k} -> {sectionId}")

if actid and sectionId:
    print("SUCCESS: Params found.")
else:
    print("FAILURE: Params missing.")
