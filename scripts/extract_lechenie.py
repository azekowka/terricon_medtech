"""Inspect the idoctor lechenie (diseases) page RSC to find the disease catalog."""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

html = open(r"_idoctor/lechenie.html", encoding="utf-8", errors="replace").read()
chunks = re.findall(r"self\.__next_f\.push\(\[1,\"(.*?)\"\]\)", html, re.S)
data = "".join(chunks)
# JS-string unescape (preserve UTF-8): handle \" \/ \n \\
data = (
    data.replace('\\"', '"')
    .replace("\\/", "/")
    .replace("\\n", " ")
    .replace("\\t", " ")
    .replace("\\\\", "\\")
)
print("payload chars:", len(data))

# illness objects {"id":N,"alias":"N-slug","name":"..."}
objs = re.findall(r'\{"id":\d+,"alias":"\d+-[a-z0-9\-]+","name":"[^"]{2,70}"[^}]*\}', data)
print("illness-like objects:", len(objs))
seen = set()
illnesses = []
for o in objs:
    try:
        d = json.loads(o)
    except Exception:
        m = re.match(r'\{"id":(\d+),"alias":"([^"]+)","name":"([^"]+)"', o)
        if not m:
            continue
        d = {"id": int(m.group(1)), "alias": m.group(2), "name": m.group(3)}
    if d["alias"] in seen:
        continue
    seen.add(d["alias"])
    illnesses.append({"id": d["id"], "alias": d["alias"], "name": d["name"]})
print("unique illnesses:", len(illnesses))
for it in illnesses[:12]:
    print("  ", it["alias"][:34], "|", it["name"][:40])

# look for category structure
for kw in ['"categories"', '"category"', '"groups"', '"byCategory"', '"skills"', '"title"']:
    i = data.find(kw)
    if i > 0:
        print(f"key {kw} @ {i}: {data[i:i+140]}")

json.dump(illnesses, open(r"_idoctor/lechenie_illnesses.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
