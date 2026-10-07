# Daily episode: instructions for the scheduled run

Produce today's ~10-minute Mandarin news podcast for Kian (German-based Mandarin learner, about HSK 4) as an MP3, publish it to his podcast feed, and update his vocabulary spaced-repetition tracking. Work without asking questions; nobody is watching this run.

`pod/` below means this repository's folder: it is attached to the routine, so it is already cloned and GitHub access is built in. Don't use any other credentials. TODAY = today's date in Europe/Berlin (YYYY-MM-DD).

## 0. Setup
```
cd pod && git checkout -q main && git pull -q origin main && cd ..
pip install -q rjieba sherpa-onnx soundfile        # add --break-system-packages if pip refuses
which ffmpeg || pip install -q imageio-ffmpeg      # fallback: python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"
```

## 1. Vocabulary (spaced repetition)
a) Read Kian's vocabulary doc with the Claude Docs tools: load the docs skill if listed (else `guide` topic.index), `read` ref {"object":"project","id":"67b78e92-e34f-46a5-afeb-2e7fdfd9c9f7"} to get the tab body id, read the body outline, then `{"kind":"view","parentId":"<Vocabulary table id>"}` for the table in full. Note the read's `rev` and the table id.
b) Columns: Hanzi | Pinyin | Meaning | Added | Status | Heard (×) | Last heard | Next due. Status is a dropdown New / Learning / Hard / Known (empty = New). Build words.json = [{"hanzi","pinyin","meaning","added","status"}] from every row with a Hanzi (skip the example row 例子). Also write the same list to pod/vocab_cache.json (backup copy, committed in step 5).
c) If the Docs tools are not available in this run, use pod/vocab_cache.json as words.json, skip step 6, and say "DOC NOT AVAILABLE, used cached word list" in the final reply.
d) Run `python3 pod/srs.py select words.json TODAY` → the 3–8 words to use today. Use exactly these; don't pick words yourself.

## 2. News
Pick 6 stories from the past 24 hours. The routine's environment allows aljazeera.com and taz.de; the Webz.io connector (tool `news_search_by_webz`) needs no network permission.
- **World (2): Al Jazeera.** Read its RSS feed: `curl -sL https://www.aljazeera.com/xml/rss/all.xml` and pick the 2 most important world stories from the last 24 hours; fetch an article page with curl if you need detail. If the feed fails, use `news_search_by_webz` (e.g. query "top world news", `days: 1`, `sort_by: "date_desc"`, `language: ["english"]`) or WebSearch, and name the fallback in the final reply.
- **China (2):** domestic news from inside China (society, economy, cities, culture, policy). Use `news_search_by_webz` with `domain: ["chinadaily.com.cn", "news.cgtn.com", "cgtn.com", "scmp.com", "xinhuanet.com", "news.cn", "sixthtone.com", "caixinglobal.com"]`, `days: 1`, `sort_by: "date_desc"`; WebSearch as fallback. Report factually and neutrally; where a source is state media, don't repeat its framing (e.g. opinion columns) as fact — prefer factual reports over commentary.
- **Germany (2): taz.** Read taz's RSS feed: `curl -sL "https://taz.de/!p4608;rss/"` (fallback `curl -sL https://taz.de/rss.xml`, then the homepage https://taz.de/). Pick the 2 most important German stories of the last 24 hours. taz writes in German; summarise in simple Chinese. If taz can't be reached, use `news_search_by_webz` with `language: ["german"]`, `country: ["DE"]`, `days: 1` and name the fallback.
Check key facts against a second source when something is unclear.

## 3. Script (simplified Chinese only, written to be spoken)
- Mainly words Kian knows: pod/known_words.json plus the vocabulary words. Short sentences.
- Structure: greeting with today's date and weekday → world → China → Germany (each story: headline sentence, then 3–5 sentences of context) → 1-minute review of the selected vocabulary words.
- Use each selected vocabulary word naturally at least twice before the review.
- Review: for each selected word, say the word, then one example sentence. If pod/teacher_sentences.json has sentences for it (from Kian's teachers), use one (rotate), say "老师的例句：" first and read it as written; otherwise make a new simple sentence.
- Length: about 2,200–2,500 Chinese characters (≈10 min), explanations included.
- For text-to-speech: numbers, dates and percentages in Chinese characters; no Latin letters, abbreviations or symbols (欧盟, 美国, 百分之三 …); full Chinese punctuation; one paragraph per story, separated by a blank line.
- Check: save as script.txt, run `python3 pod/level/check_script.py script.txt words.json`. For every "unknown" word: replace it with a simpler known word, or keep it and explain it right after first use in one short, simple Chinese sentence (e.g. "……关税，也就是进口商品要交的税……"). Briefly explain lesser-known names. At most ~8 explained words; re-run until coverage ≥ 0.95. Explanations must use known words; teacher sentences are exempt.
- Write used.json = the selected vocabulary words that actually appear in the final script (exact match).

## 4. Audio
- `curl -sSL -o melo.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-melo-tts-zh_en.tar.bz2 && tar xjf melo.tar.bz2`
- Synthesize each paragraph with sherpa_onnx.OfflineTts: OfflineTtsVitsModelConfig(model="vits-melo-tts-zh_en/model.onnx", lexicon="vits-melo-tts-zh_en/lexicon.txt", tokens="vits-melo-tts-zh_en/tokens.txt", dict_dir="vits-melo-tts-zh_en/dict"), num_threads=4, rule_fsts="vits-melo-tts-zh_en/date.fst,vits-melo-tts-zh_en/phone.fst,vits-melo-tts-zh_en/number.fst"; generate(text, sid=0, speed=0.85). Join with ~0.8 s silence, write a WAV, convert with ffmpeg to mono MP3 at 64 kbps (`-ac 1 -b:a 64k`).

## 5. Publish + record (push straight to main: GitHub Pages serves the feed from main)
```
cd pod
python3 publish.py <path-to-mp3> TODAY "<title>" "<description>"
python3 srs.py record ../words.json TODAY ../used.json > ../stats.json
git add -A
git commit -qm "Episode TODAY"
git push origin HEAD:main
git fetch -q origin && test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" && echo PUSHED-OK
```
- Title: `TODAY · ` + a short Chinese headline of the top story.
- Description: 2–4 lines in English with each story's headline and source, then "Vocabulary: " + practised words (hanzi + pinyin), then "Explained: " + explained new words (hanzi + pinyin + English).
- Don't modify publish.py, srs.py, vocab_import.py, RUN.md, teacher_sentences.json, level/, known_words.json, the cover or feed settings.
- Continue to step 6 only after PUSHED-OK. If the push fails: `git pull --rebase origin main`, push again; if it still fails, skip step 6 and start the final reply with "PUSH FAILED:" plus the exact git error. Don't try other credentials or workarounds.

## 6. Mirror stats into the doc
stats.json gives heard / last_heard / next_due per word. Re-read the table (`view` + `parentId`) for a fresh `rev`, then send ONE `update` with one op per changed cell (Heard = col 5, Last heard = col 6, Next due = col 7, 0-indexed, header = row 0; match rows by Hanzi): `{"op":"replace","target":{"kind":"cell","table":"<table id>","row":R,"col":C},"ifRev":<rev>,"with":{"from":{"kind":"inline","content":"<value>"},"as":"text"}}` (load `guide` topic.editing if refused). Never touch other columns or add/delete/reorder rows. If refused because Kian edited the table, re-read once and retry; then skip and mention it.

## 7. Final reply (brief, English)
Date, story headlines with sources (and which fetch method worked for Al Jazeera and taz), practised words, explained words, final coverage, and whether the feed (PUSHED-OK) and the doc were updated. No transcript.
