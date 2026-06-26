"""Extract the `initialDoctorsList` JSON array embedded in idoctor.kz pages/RSC.

The array is inside the Next.js RSC payload with JS-string escaping (\\" etc.).
We locate it, capture the balanced array, un-escape the JS-string level, and parse.
"""
import json


def extract_doctors_list(text: str):
    i = text.find("initialDoctorsList")
    if i < 0:
        return None
    start = text.index("[", i)
    depth = 0
    j = start
    end = None
    while j < len(text):
        ch = text[j]
        if ch == "\\":
            j += 2
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = j + 1
                break
        j += 1
    if end is None:
        return None
    sub = text[start:end]
    # un-escape JS-string-level escaping while preserving UTF-8 Cyrillic
    sub = (
        sub.replace('\\"', '"')
        .replace("\\/", "/")
        .replace("\\n", " ")
        .replace("\\t", " ")
        .replace("\\\\", "\\")
    )
    try:
        return json.loads(sub)
    except Exception:
        return None


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    for path in sys.argv[1:]:
        raw = open(path, encoding="utf-8", errors="replace").read()
        arr = extract_doctors_list(raw)
        if isinstance(arr, list):
            ids = [d.get("id") for d in arr]
            print(f"{path}: {len(arr)} docs | ids {ids[:5]} | first: {arr[0].get('fullName')}")
        else:
            print(f"{path}: {arr}")
