#!/usr/bin/env python3
"""Check a podcast script against what Kian knows.

  check_script.py <script.txt> [<words.json>]
    words.json = the vocabulary-doc words ([{"hanzi": ...}, ...]); they count as known (they are being practised).

Known words = ../known_words.json (from the level test); if it doesn't exist yet, all HSK 1-4 words.
Prints JSON:
  coverage  - share of word tokens (excluding names and numbers) that are known. Listening research suggests
              ~95% known words for adequate comprehension (van Zeeland & Schmitt 2013; cf. Hu & Nation 2000 for reading).
  unknown   - words not known: each must be explained in simple Chinese where first used, or replaced.
  names     - proper nouns found (people, places, organisations): explain only if not widely known.
"""
import sys, json, os, re
import rjieba

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BANK = {b["w"]: b for b in json.load(open(os.path.join(HERE, "bank.json"), encoding="utf-8"))}
kw = os.path.join(ROOT, "known_words.json")
if os.path.exists(kw):
    known = set(json.load(open(kw, encoding="utf-8"))["words"])
    source = "level test"
else:
    known = {w for w, b in BANK.items() if b["hsk"] <= 4}
    source = "fallback: HSK 1-4"
if len(sys.argv) > 2:
    known |= {(w.get("hanzi") or "").strip() for w in json.load(open(sys.argv[2], encoding="utf-8"))}
known |= {c for w in known for c in w if len(w) == 1}

NAME_TAGS = ("nr", "ns", "nt", "nz")
HAN = re.compile(r"^[一-鿿]+$")


def decomposes(w):
    """True if w can be split into known words (e.g. 德国政府 = 德国 + 政府)."""
    n = len(w)
    ok = [True] + [False] * n
    for i in range(1, n + 1):
        for j in range(max(0, i - 6), i):
            if ok[j] and w[j:i] in known and (i - j > 1 or w[j:i] in known):
                ok[i] = True
                break
    return ok[n]


text = open(sys.argv[1], encoding="utf-8").read()
total = good = 0
unknown, names = {}, {}
for w, tag in rjieba.tag(text):
    if not HAN.match(w) or tag == "m" or tag.startswith("q") and w[0] in "一二三四五六七八九十百千万亿两几":
        continue
    if tag.startswith(NAME_TAGS):
        names[w] = names.get(w, 0) + 1
        continue
    total += 1
    if w in known or decomposes(w):
        good += 1
    else:
        unknown[w] = unknown.get(w, 0) + 1

out = {
    "known_source": source,
    "coverage": round(good / total, 3) if total else 1.0,
    "unknown": [{"w": w, "count": c, "py": BANK.get(w, {}).get("py", ""), "en": BANK.get(w, {}).get("en", ""),
                 "hsk": BANK.get(w, {}).get("hsk")} for w, c in sorted(unknown.items(), key=lambda x: -x[1])],
    "names": sorted(names),
}
print(json.dumps(out, ensure_ascii=False, indent=1))
