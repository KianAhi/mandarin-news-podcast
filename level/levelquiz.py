#!/usr/bin/env python3
"""Adaptive yes/no vocabulary test for Mandarin learners -> list of words the learner (probably) knows.

Method (research basis):
- Yes/No checklist test with pseudowords (Meara & Buxton 1987; Meara's X-Lex/Y-Lex; LEXTALE, Lemhöfer & Broersma 2012;
  Chinese version LEXTALE-CH, Chan & Chang 2018). Learners tick words they know; ticks on fake words measure over-claiming.
- Frequency/level-band sampling as in the Vocabulary Size Test (Nation & Beglar 2007): word knowledge falls off with
  frequency, so a stratified sample predicts knowledge of the whole list.
- An item-response style logistic model P(known) = sigmoid(a + b*ln(rank) + c*HSK level) is fitted to the answers
  (cf. Rasch/IRT vocabulary tests, adaptive testing). Round 2 samples words where the model is least certain.
- Meaning checks (multiple choice) on a few "yes" answers verify self-report; failed checks count as "unknown".
- False-alarm correction: p_adj = (p - f) / (1 - f), f = rate of "yes" on pseudowords (Huibregtse et al. 2002 style).

Commands (all print JSON):
  levelquiz.py round1 [--seed N]                     -> items for round 1 (48: 40 words over 10 bands + 8 fakes)
  levelquiz.py round2 <answers.json> [--seed N]      -> items for round 2 (32: around the learner's threshold + 4 fakes)
  levelquiz.py checks <answers.json> [--seed N]      -> up to 8 meaning checks (4 options each) on claimed words
  levelquiz.py estimate <answers.json> [--date D]    -> fits the model, writes ../known_words.json + ../level_profile.json

answers.json: {"answers": {"<item>": true|false, ...}, "checks": {"<word>": true|false, ...}}
  item = the Chinese word (or fake) shown; true = "I know it". checks: true = picked the right meaning.
"""
import sys, json, os, math, random, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BANK = json.load(open(os.path.join(HERE, "bank.json"), encoding="utf-8"))
FAKES = json.load(open(os.path.join(HERE, "pseudowords.json"), encoding="utf-8"))
BY_W = {b["w"]: b for b in BANK}
FAKESET = set(FAKES)
BANDS = [1, 300, 700, 1500, 3000, 5000, 8000, 12000, 17000, 25000, 40000]
KNOWN_P = 0.8


def arg(name, default=None):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default


def rng():
    return random.Random(int(arg("--seed", random.randrange(10**9))))


def item(b):
    return {"item": b["w"]}


def eligible(b):
    return len(b["w"]) >= 1 and b["rank"] < 1000000


def mix(words, fakes, r):
    items = [item(b) for b in words] + [{"item": f} for f in fakes]
    r.shuffle(items)
    return {"items": items, "n_words": len(words), "n_fakes": len(fakes)}


def round1():
    r = rng()
    words = []
    for lo, hi in zip(BANDS, BANDS[1:]):
        pool = [b for b in BANK if lo <= b["rank"] < hi and eligible(b)]
        words += r.sample(pool, min(4, len(pool)))
    return mix(words, r.sample(FAKES, 8), r)


def load_answers(path):
    a = json.load(open(path, encoding="utf-8"))
    return a.get("answers", {}), a.get("checks", {})


def features(b):
    return [1.0, math.log(b["rank"]), float(b["hsk"])]


def fit(answers, checks):
    """Ridge-regularised logistic regression via Newton's method (3 params)."""
    X, y = [], []
    for w, v in answers.items():
        if w in BY_W:
            known = bool(v) and checks.get(w, True)
            X.append(features(BY_W[w])); y.append(1.0 if known else 0.0)
    beta = [4.0, -0.5, -0.3]
    lam = [0.05, 0.3, 0.3]  # weak prior toward a gentle slope
    for _ in range(200):
        g = [0.0] * 3
        H = [[0.0] * 3 for _ in range(3)]
        for xi, yi in zip(X, y):
            z = sum(bj * xj for bj, xj in zip(beta, xi))
            p = 1 / (1 + math.exp(-max(-30, min(30, z))))
            for j in range(3):
                g[j] += (yi - p) * xi[j]
                for k in range(3):
                    H[j][k] += p * (1 - p) * xi[j] * xi[k]
        for j in range(3):
            g[j] -= lam[j] * (beta[j] - [4.0, -0.5, -0.3][j])
            H[j][j] += lam[j]
        step = solve(H, g)
        norm = math.sqrt(sum(x * x for x in step))
        if norm > 1.0:  # damped Newton: keeps the fit stable when nearly all answers are yes (or no)
            step = [x / norm for x in step]
        beta = [b + s for b, s in zip(beta, step)]
        if max(abs(s) for s in step) < 1e-6:
            break
    return beta, len(X), sum(y)


def solve(A, b):
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for i in range(n):
        piv = max(range(i, n), key=lambda r: abs(M[r][i]))
        M[i], M[piv] = M[piv], M[i]
        if abs(M[i][i]) < 1e-12:
            return [0.0] * n
        for r in range(n):
            if r != i:
                f = M[r][i] / M[i][i]
                M[r] = [a - f * c for a, c in zip(M[r], M[i])]
    return [M[i][n] / M[i][i] for i in range(n)]


def prob(beta, b):
    z = sum(bj * xj for bj, xj in zip(beta, features(b)))
    return 1 / (1 + math.exp(-max(-30, min(30, z))))


def false_alarm(answers):
    fk = [bool(v) for w, v in answers.items() if w in FAKESET]
    return (sum(fk) / len(fk)) if fk else 0.0, len(fk)


def round2(path):
    answers, checks = load_answers(path)
    beta, _, _ = fit(answers, checks)
    r = rng()
    seen = set(answers)
    pool = [b for b in BANK if eligible(b) and b["w"] not in seen]
    unsure = [b for b in pool if 0.2 <= prob(beta, b) <= 0.8]
    if len(unsure) < 28:
        unsure = sorted(pool, key=lambda b: abs(prob(beta, b) - 0.5))[:300]
    words = r.sample(unsure, min(28, len(unsure)))
    fakes = r.sample([f for f in FAKES if f not in seen], 4)
    return mix(words, fakes, r)


def checks(path):
    answers, _ = load_answers(path)
    beta, _, _ = fit(answers, {})
    r = rng()
    claimed = [BY_W[w] for w, v in answers.items() if v and w in BY_W]
    # verify the least likely claims first (most informative)
    claimed.sort(key=lambda b: prob(beta, b))
    target = claimed[:8]
    out = []
    for b in target:
        near = [x for x in BANK if x["w"] != b["w"] and abs(math.log(x["rank"]) - math.log(b["rank"])) < 0.7
                and x["en"].split(";")[0] != b["en"].split(";")[0]]
        opts = [x["en"].split(";")[0].strip() for x in r.sample(near, 3)] + [b["en"].split(";")[0].strip()]
        r.shuffle(opts)
        out.append({"word": b["w"], "options": opts, "answer": b["en"].split(";")[0].strip()})
    return {"checks": out}


def estimate(path):
    answers, chk = load_answers(path)
    beta, n, n_yes = fit(answers, chk)
    f, nf = false_alarm(answers)
    def padj(b):
        p = prob(beta, b)
        return max(0.0, (p - f) / (1 - f)) if f < 1 else 0.0
    known, by_level = [], {}
    for b in BANK:
        w = b["w"]
        if w in answers:
            k = bool(answers[w]) and chk.get(w, True)
        else:
            k = padj(b) >= KNOWN_P
        if k:
            known.append(w)
        by_level.setdefault(b["hsk"], []).append(padj(b) if w not in answers else float(k))
    cover = {lvl: round(sum(v) / len(v), 3) for lvl, v in sorted(by_level.items())}
    level = 0
    for lvl in range(1, 8):
        if cover.get(lvl, 0) >= 0.8:
            level = lvl
        else:
            break
    size = round(sum(padj(b) if b["w"] not in answers else float(bool(answers[b["w"]]) and chk.get(b["w"], True)) for b in BANK))
    failed = [w for w, ok in chk.items() if not ok]
    warn = []
    if f > 0.15:
        warn.append(f"High false-alarm rate ({f:.0%} of fake words ticked): estimate is less reliable; retake and only tick words you are sure of.")
    if len(chk) and len(failed) / len(chk) > 0.4:
        warn.append("Many meaning checks failed: you may be over-estimating; consider marking only words you can translate.")
    date = arg("--date", dt.date.today().isoformat())
    profile = {
        "date": date, "method": "adaptive yes/no test with pseudowords + logistic model on ln(frequency rank) and HSK level",
        "items_answered": n, "fakes_answered": nf, "false_alarm_rate": round(f, 3),
        "meaning_checks": len(chk), "meaning_checks_failed": failed,
        "model": {"intercept": round(beta[0], 3), "ln_rank": round(beta[1], 3), "hsk": round(beta[2], 3)},
        "estimated_known_words_in_bank": size, "known_list_size": len(known),
        "coverage_by_hsk_level": {("HSK " + (str(k) if k < 7 else "7-9")): v for k, v in cover.items()},
        "estimated_hsk_level": level, "warnings": warn,
    }
    json.dump({"date": date, "source": "level test", "words": known},
              open(os.path.join(ROOT, "known_words.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(profile, open(os.path.join(ROOT, "level_profile.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    hist = os.path.join(HERE, "history")
    os.makedirs(hist, exist_ok=True)
    json.dump({"answers": answers, "checks": chk, "profile": profile},
              open(os.path.join(hist, f"{date}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return profile


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "round1":
        res = round1()
    elif cmd == "round2":
        res = round2(sys.argv[2])
    elif cmd == "checks":
        res = checks(sys.argv[2])
    elif cmd == "estimate":
        res = estimate(sys.argv[2])
    else:
        sys.exit(__doc__)
    print(json.dumps(res, ensure_ascii=False, indent=1))
