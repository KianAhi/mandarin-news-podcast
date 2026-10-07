#!/usr/bin/env python3
"""Read an episode script aloud with the Kokoro voice (Chinese + English) and write an MP3.

Usage: python3 tts.py <script.txt> <out.mp3>
       python3 tts.py --sample "<text>" <out.mp3>
       python3 tts.py --estimate <script.txt>     (predicted length in minutes, no audio; takes a second)

Pauses come from the layout of the script, so the listener can keep up:
  - blank line (new story / section) ...... 1.6 s
  - line break .............................. 0.8 s   (e.g. between a new word and its translation)
  - end of sentence inside a line ........... 0.45 s
  - [pause] anywhere ........................ 1.2 s extra
Needs: pip install sherpa-onnx soundfile ; ffmpeg (or imageio-ffmpeg).
"""
import os, re, sys, subprocess, tempfile, shutil

VOICE_ID = 50          # Kokoro multi-lang v1.0: 50 = zm_yunxi (male, Mandarin)
SPEED = 0.9
MODEL = "kokoro-multi-lang-v1_0"
URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{MODEL}.tar.bz2"
CACHE = os.path.expanduser("~/.cache/tts-voices")
GAP_PARAGRAPH, GAP_LINE, GAP_SENTENCE, GAP_MARK = 1.6, 0.8, 0.45, 1.2


def model_dir():
    d = os.path.join(CACHE, MODEL)
    if not os.path.isdir(d):
        os.makedirs(CACHE, exist_ok=True)
        tar = os.path.join(CACHE, MODEL + ".tar.bz2")
        subprocess.run(["curl", "-sSLf", "-o", tar, URL], check=True)
        subprocess.run(["tar", "xjf", tar, "-C", CACHE], check=True)
        os.remove(tar)
    return d + "/"


def engine():
    import sherpa_onnx as so
    d = model_dir()
    cfg = so.OfflineTtsConfig(
        model=so.OfflineTtsModelConfig(kokoro=so.OfflineTtsKokoroModelConfig(
            model=d + "model.onnx", voices=d + "voices.bin", tokens=d + "tokens.txt",
            data_dir=d + "espeak-ng-data", dict_dir=d + "dict",
            lexicon=d + "lexicon-us-en.txt," + d + "lexicon-zh.txt"), num_threads=4),
        rule_fsts=d + "date-zh.fst," + d + "phone-zh.fst," + d + "number-zh.fst", max_num_sentences=1)
    return so.OfflineTts(cfg)


def plan(text):
    """Turn the script into [(chunk_text, pause_after_seconds), ...]."""
    out = []  # [text, base_gap, extra_gap]
    paras = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    for pi, para in enumerate(paras):
        lines = [l.strip() for l in para.split("\n") if l.strip()]
        for li, line in enumerate(lines):
            for part in re.split(r"(\[pause\])", line):
                if part == "[pause]":
                    if out:
                        out[-1][2] += GAP_MARK
                    continue
                # sentences: Chinese 。！？ and English . ! ? followed by a space
                for s in re.split(r"(?<=[。！？!?])|(?<=\.)\s+", part):
                    if s and s.strip():
                        out.append([s.strip(), GAP_SENTENCE, 0.0])
            if out:
                out[-1][1] = GAP_LINE if li < len(lines) - 1 else (GAP_PARAGRAPH if pi < len(paras) - 1 else 0.5)
    return [(t, base + extra) for t, base, extra in out]


# measured for yunxi at speed 0.8: ~4.0 Chinese characters/s, ~2.4 English words/s
ZH_PER_SEC, EN_WORDS_PER_SEC = 4.0 * SPEED / 0.8, 2.4 * SPEED / 0.8


def estimate(text):
    secs = 0.0
    for s, gap in plan(text):
        zh = len(re.findall(r"[\u4e00-\u9fff]", s))
        en = len(re.findall(r"[A-Za-z]+", s))
        secs += zh / ZH_PER_SEC + en / EN_WORDS_PER_SEC + gap
    return secs / 60


def ffmpeg_bin():
    f = shutil.which("ffmpeg")
    if f:
        return f
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def synth(text, out_mp3):
    import numpy as np, soundfile as sf
    tts = engine()
    chunks, sr = [], 24000
    steps = plan(text)
    for i, (s, gap) in enumerate(steps, 1):
        a = tts.generate(s, sid=VOICE_ID, speed=SPEED)
        sr = a.sample_rate
        chunks += [np.asarray(a.samples, dtype="float32"), np.zeros(int(gap * sr), dtype="float32")]
        if i % 20 == 0 or i == len(steps):
            print(f"{i}/{len(steps)} sentences, {sum(len(c) for c in chunks) / sr / 60:.1f} min so far", flush=True)
    wav = tempfile.mktemp(suffix=".wav")
    sf.write(wav, np.concatenate(chunks), sr)
    subprocess.run([ffmpeg_bin(), "-loglevel", "error", "-y", "-i", wav, "-ac", "1", "-b:a", "64k", out_mp3], check=True)
    os.remove(wav)
    secs = sum(len(c) for c in chunks) / sr
    print(f"{out_mp3}: {secs / 60:.1f} min")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--estimate":
        print(f"estimated length: {estimate(open(sys.argv[2], encoding='utf-8').read()):.1f} min")
    elif len(sys.argv) == 4 and sys.argv[1] == "--sample":
        synth(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3:
        synth(open(sys.argv[1], encoding="utf-8").read(), sys.argv[2])
    else:
        sys.exit(__doc__)
