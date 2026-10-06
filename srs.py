#!/usr/bin/env python3
"""Exposure-based spaced repetition for the podcast vocabulary.

The vocabulary doc is the word list; this repo keeps the exposure history.

  srs.py select <words.json> <YYYY-MM-DD>            -> prints the words to use today (JSON)
  srs.py record <words.json> <YYYY-MM-DD> <used.json> -> logs exposures, prints per-word stats (JSON)

words.json: [{"hanzi": "...", "pinyin": "...", "meaning": "...", "added": "YYYY-MM-DD", "status": "New|Learning|Hard|Known"}, ...]
used.json:  ["hanzi", ...]  (only words actually spoken in the episode)

Scheduling: after each exposure the next due date moves out along LADDER.
An exposure before the due date (used as filler) counts, but does not advance the schedule.
Status "Hard" caps the interval at 2 days; "Known" uses a fixed 60-day interval.
"""
import sys, json, os, csv, datetime as dt

LADDER = [1, 2, 4, 7, 14, 30, 60]   # days until next exposure after the 1st, 2nd, ... exposure
HARD_MAX = 2
KNOWN_INTERVAL = 60
MIN_WORDS, MAX_WORDS = 3, 8

ROOT = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(ROOT, "vocab_state.json")
LOG = os.path.join(ROOT, "exposures.csv")


def load_state():
    return json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {}


def d(s):
    return dt.date.fromisoformat(s)


def norm_words(path):
    words = json.load(open(path, encoding="utf-8"))
    out = []
    for w in words:
        h = (w.get("hanzi") or "").strip()
        if not h or h == "例子":
            continue
        w["hanzi"] = h
        w["status"] = (w.get("status") or "New").strip() or "New"
        out.append(w)
    return out


def select(words, today):
    state = load_state()
    t = d(today)
    scored = []
    for w in words:
        s = state.get(w["hanzi"], {})
        count = s.get("count", 0)
        due = d(s["next_due"]) if s.get("next_due") else None
        if count == 0:
            # never heard: top priority, newest-added first
            pri = (0, -(d(w["added"]).toordinal() if w.get("added") else 0))
            is_due = True
        else:
            overdue = (t - due).days
            is_due = overdue >= 0
            hard = 0 if w["status"] == "Hard" else 1
            pri = (1, hard, -overdue)  # Hard first, then most overdue
        scored.append((pri, is_due, w))
    scored.sort(key=lambda x: x[0])
    due_words = [w for _, is_due, w in scored if is_due]
    picked = due_words[:MAX_WORDS]
    if len(picked) < MIN_WORDS:
        # top up with the least recently heard words that are not Known
        rest = [w for _, is_due, w in scored if not is_due and w["status"] != "Known"]
        rest.sort(key=lambda w: (state[w["hanzi"]]["last"], state[w["hanzi"]]["count"]))
        picked += rest[: MIN_WORDS - len(picked)]
    return picked


def record(words, today, used):
    state = load_state()
    t = d(today)
    by_h = {w["hanzi"]: w for w in words}
    new_log = not os.path.exists(LOG)
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        if new_log:
            wr.writerow(["date", "hanzi"])
        for h in used:
            if h not in by_h:
                continue
            s = state.setdefault(h, {"count": 0, "history": []})
            if today in s["history"]:
                continue  # already recorded today
            s["count"] += 1
            s["history"].append(today)
            s["last"] = today
            status = by_h[h]["status"]
            early = s.get("next_due") and t < d(s["next_due"]) and status != "Hard"
            if early:
                # heard before it was due (filler): counts as exposure, schedule unchanged
                wr.writerow([today, h])
                continue
            s["step"] = s.get("step", 0) + 1
            if status == "Known":
                interval = KNOWN_INTERVAL
            else:
                interval = LADDER[min(s["step"] - 1, len(LADDER) - 1)]
                if status == "Hard":
                    interval = min(interval, HARD_MAX)
            s["interval"] = interval
            s["next_due"] = (t + dt.timedelta(days=interval)).isoformat()
            wr.writerow([today, h])
    json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    # stats for every word in the doc, to mirror into the table
    out = []
    for w in words:
        s = state.get(w["hanzi"], {})
        out.append({"hanzi": w["hanzi"], "heard": s.get("count", 0), "step": s.get("step", 0),
                    "last_heard": s.get("last", "–"), "next_due": s.get("next_due", "–")})
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    words = norm_words(sys.argv[2])
    if cmd == "select":
        print(json.dumps(select(words, sys.argv[3]), ensure_ascii=False, indent=1))
    elif cmd == "record":
        used = json.load(open(sys.argv[4], encoding="utf-8"))
        print(json.dumps(record(words, sys.argv[3], used), ensure_ascii=False, indent=1))
    else:
        sys.exit(__doc__)
