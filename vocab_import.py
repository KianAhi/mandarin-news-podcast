#!/usr/bin/env python3
"""Helpers for importing teacher material into the vocabulary list.

  vocab_import.py lookup <candidates.json> [<vocab_words.json>]
      candidates.json: ["词", ...] or [{"hanzi": "...", "pinyin"?: "...", "meaning"?: "..."}, ...]
      vocab_words.json: hanzi already in the vocab doc table (list of strings or of {"hanzi": ...})
      Prints, per candidate: simplified hanzi, suggested pinyin (pypinyin), dictionary meaning + HSK level from
      level/bank.json, and flags: in_vocab (already in the table), known (in known_words.json).

  vocab_import.py save-sentences <sentences.json> <source label> <YYYY-MM-DD>
      sentences.json: [{"hanzi": "词", "sentence": "例句……", "translation"?: "..."}, ...]
      Appends to teacher_sentences.json (keyed by hanzi), skipping exact duplicates, and logs the import
      in imports.csv. The podcast uses these sentences in its vocabulary review.

Needs: pip install pypinyin opencc-python-reimplemented --break-system-packages -q
"""
import sys, json, os, csv
from pypinyin import lazy_pinyin, Style
from opencc import OpenCC

ROOT = os.path.dirname(os.path.abspath(__file__))
T2S = OpenCC("t2s")
BANK = {b["w"]: b for b in json.load(open(os.path.join(ROOT, "level", "bank.json"), encoding="utf-8"))}
kw = os.path.join(ROOT, "known_words.json")
KNOWN = set(json.load(open(kw, encoding="utf-8"))["words"]) if os.path.exists(kw) else set()


def hanzi_of(x):
    return (x if isinstance(x, str) else x.get("hanzi", "")).strip()


def lookup(cands, vocab):
    out, seen = [], set()
    for c in cands:
        raw = hanzi_of(c)
        h = T2S.convert(raw)
        if not h or h in seen:
            continue
        seen.add(h)
        b = BANK.get(h, {})
        out.append({
            "hanzi": h,
            "converted_from_traditional": raw if raw != h else None,
            "pinyin_given": c.get("pinyin") if isinstance(c, dict) else None,
            "pinyin_suggested": " ".join(lazy_pinyin(h, style=Style.TONE)),
            "meaning_given": c.get("meaning") if isinstance(c, dict) else None,
            "meaning_dictionary": b.get("en"),
            "hsk": (b.get("hsk") if b.get("hsk", 0) < 7 else "7-9") if b else None,
            "in_vocab": h in vocab,
            "known": h in KNOWN,
        })
    return out


def save_sentences(items, source, date):
    path = os.path.join(ROOT, "teacher_sentences.json")
    data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    added = 0
    for it in items:
        h = T2S.convert(it["hanzi"].strip())
        s = T2S.convert(it["sentence"].strip())
        lst = data.setdefault(h, [])
        if any(e["sentence"] == s for e in lst):
            continue
        lst.append({"sentence": s, "translation": it.get("translation"), "source": source, "date": date})
        added += 1
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    log = os.path.join(ROOT, "imports.csv")
    new = not os.path.exists(log)
    with open(log, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "source", "sentences_added"])
        w.writerow([date, source, added])
    return {"sentences_added": added, "words_with_sentences": len(data)}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "lookup":
        cands = json.load(open(sys.argv[2], encoding="utf-8"))
        vocab = set()
        if len(sys.argv) > 3:
            vocab = {T2S.convert(hanzi_of(x)) for x in json.load(open(sys.argv[3], encoding="utf-8"))}
        res = lookup(cands, vocab)
    elif cmd == "save-sentences":
        res = save_sentences(json.load(open(sys.argv[2], encoding="utf-8")), sys.argv[3], sys.argv[4])
    else:
        sys.exit(__doc__)
    print(json.dumps(res, ensure_ascii=False, indent=1))
