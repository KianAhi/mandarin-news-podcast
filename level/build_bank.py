#!/usr/bin/env python3
"""One-off: build bank.json + pseudowords.json from drkameleon/complete-hsk-vocabulary (MIT).
Usage: build_bank.py <path/to/complete.json> <path/to/jieba/dict.txt>  (dict filters out real words)"""
import sys, json, random, re, os
import rjieba
from pypinyin import lazy_pinyin, Style  # pinyin from pypinyin: picks the common reading, lowercase
src = json.load(open(sys.argv[1], encoding="utf-8"))
out = os.path.dirname(os.path.abspath(__file__))
bank = []
for e in src:
    w = e["simplified"]
    lv = e.get("level", [])
    def pick(prefix):
        xs = [int(l.split("-")[1]) for l in lv if l.startswith(prefix + "-")]
        return min(xs) if xs else None
    hsk = pick("new") or pick("newest") or pick("old") or 7
    hsk = min(hsk, 7)  # 7 = HSK 7-9
    f = e["forms"][0]
    bank.append({"w": w, "py": " ".join(lazy_pinyin(w, style=Style.TONE)), "en": "; ".join(f["meanings"][:2])[:80],
                 "rank": e.get("frequency") or 1000000, "hsk": hsk})
bank.sort(key=lambda x: x["rank"])
json.dump(bank, open(os.path.join(out, "bank.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
words = {b["w"] for b in bank}
# word-like fakes: a char that often starts 2-char words + a char that often ends them
from collections import Counter
two = [b["w"] for b in bank if len(b["w"]) == 2 and b["hsk"] <= 5]
STOP = set("的了么们也且与于为是在不有和就都而着过吗呢吧啊之其此该这那哪个些什怎")
single = {w for w in words if len(w) == 1}  # chars that are words on their own -> combos read as phrases
first = [c for c, n in Counter(w[0] for w in two).items() if n >= 3 and c not in STOP and c not in single]
second = [c for c, n in Counter(w[1] for w in two).items() if n >= 3 and c not in STOP and c not in single]
allchars = "|".join(words)
random.seed(7)
lexicon = {line.split(" ", 1)[0] for line in open(sys.argv[2], encoding="utf-8")}
cands = [a + b for a in first for b in second
         if a != b and (a + b) not in allchars and (a + b) not in lexicon and (b + a) not in lexicon]
pseudo = random.sample(cands, min(400, len(cands)))
json.dump(sorted(pseudo), open(os.path.join(out, "pseudowords.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(len(bank), "words,", len(pseudo), "pseudowords from", len(cands), "candidates")
