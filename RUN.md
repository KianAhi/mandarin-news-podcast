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
Pick 6 stories from the past 24 hours (48 hours if a section has too little). The routine's environment allows aljazeera.com and taz.de; the Webz.io connector (tool `news_search_by_webz`) needs no network permission. Kian's interests per section:

- **Middle East (2): Al Jazeera, focus on Iran and Gaza.** Read the RSS feed: `curl -sL https://www.aljazeera.com/xml/rss/all.xml` (Middle East feed: `https://www.aljazeera.com/xml/rss/middleeast.xml` if it exists). Pick the 2 most important stories about Iran, Gaza/Palestine, Israel, Lebanon or the wider region; prefer Iran and Gaza. Fetch an article page with curl for detail. If the feed fails, use `news_search_by_webz` (query e.g. "Iran" or "Gaza", `days: 1`, `sort_by: "date_desc"`, `language: ["english"]`) or WebSearch, and name the fallback in the final reply.
- **Germany (2): taz, national politics.** Read taz's RSS feed: `curl -sL "https://taz.de/!p4608;rss/"` (fallback `curl -sL https://taz.de/rss.xml`, then the homepage https://taz.de/). Pick the 2 most relevant stories on **federal German politics**: Bundesregierung, Bundestag, coalition, parties, federal laws and budget, national debates. Skip local or small-town news. taz commentary and opinion pieces are welcome; when you use one, say in the episode that it is a taz opinion (taz评论认为……). taz writes in German; summarise in simple Chinese. If taz can't be reached, use `news_search_by_webz` with `language: ["german"]`, `country: ["DE"]`, `days: 1` and name the fallback.
- **China (2): what Western media rarely covers.** Interesting domestic stories: everyday life and social trends, consumer and tech trends, local innovations, culture, education, work and youth life, regional developments, unusual local stories. Avoid the big geopolitical topics Western outlets already cover heavily. Use `news_search_by_webz` with `domain: ["sixthtone.com", "caixinglobal.com", "scmp.com", "chinadaily.com.cn", "news.cgtn.com", "cgtn.com", "globaltimes.cn", "xinhuanet.com", "news.cn"]`, `days: 1`, `sort_by: "date_desc"`, trying a few different queries (e.g. "young people China trend", "Chinese city new policy residents", "China consumers", "China technology everyday life"); WebSearch as fallback. Report factually and neutrally; with state media, use the facts, not the framing, and don't present commentary as fact.

Check key facts against a second source when something is unclear.

## 3. Script (spoken; Chinese, with short English parts only where stated)
- Mainly words Kian knows: pod/known_words.json plus the vocabulary words. Short sentences.
- Overall: greeting with today's date and weekday (Chinese) → 6 stories in the order Middle East, China, Germany → 1-minute review of the selected vocabulary words.
- **Each story has three parts, in this order:**
  1. **English one-line intro**, one short sentence: "Our first story is from Al Jazeera and is about …" (then "Our next story is from …", "Our last story is from …"). Write numbers as English words here.
  2. **New words for this story** (only the story's unknown words that you keep; 1–4 per story; skip this part if there are none): a line "New words.", then for each word one line with the Chinese word and the next line with its English translation followed by `[pause]`. No pinyin in the spoken script.
  3. **The story in Chinese**: headline sentence, then 8–10 sentences of context (about 280 characters), on one line. Pre-taught words need no further explanation inside the story.
- **Layout = pauses.** The voice pauses 0.8 s at every line break, 1.6 s at a blank line, about 0.5 s between sentences, and 1.2 s extra at `[pause]`. So keep this layout exactly (blank line between stories):
  ```
  Our first story is from Al Jazeera and is about new talks between Iran and the United States.
  New words.
  谈判
  negotiation. [pause]
  制裁
  sanctions. [pause]
  伊朗和美国今天在阿曼开始了新的谈判。双方都说……

  Our next story is from taz and is about …
  ```
- Use each selected vocabulary word naturally at least twice before the review.
- Review: for each selected word, one line with the word followed by `[pause]`, then the next line with one example sentence. If pod/teacher_sentences.json has sentences for it (from Kian's teachers), use one (rotate), say "老师的例句：" first and read it as written; otherwise make a new simple sentence.
- Length: 10 minutes of audio, which is about 2,000 Chinese characters in total with this voice and its pauses. After the check below, run `python3 pod/tts.py --estimate script.txt`: it must say 9.5–11 min. If it's shorter, add sentences to the stories; if longer, trim them. Then re-run the check.
- For text-to-speech, in the Chinese parts: numbers, dates and percentages in Chinese characters; no Latin letters, abbreviations or symbols (欧盟, 美国, 百分之三 …); full Chinese punctuation. English is allowed only in the intro sentence and the word translations. Avoid colons.
- Check: save the spoken script as script.txt. Make check_words.json = words.json plus every pre-taught new word (as {"hanzi": …}), then run `python3 pod/level/check_script.py script.txt check_words.json`. For every remaining "unknown" word: replace it with a simpler known word, or pre-teach it in that story's "New words" part. At most ~10 pre-taught words per episode; re-run until coverage ≥ 0.95. Briefly explain lesser-known names in Chinese. Teacher sentences are exempt.
- Write transcript.txt: identical to script.txt without the `[pause]` marks, and each pre-taught word line also gets its pinyin, e.g. "谈判 (tánpàn)". It goes into the episode's show notes.
- Write used.json = the selected vocabulary words that actually appear in the final script (exact match).

## 4. Audio
- `python3 pod/tts.py script.txt episode.mp3`. Voice: Kokoro "yunxi" at speed 0.9, with the pauses from the script layout; it downloads the voice from GitHub on first use (~380 MB) and prints the episode length at the end.
- It takes about 6–8 minutes, close to the limit of one Bash call, so run it in the background and check until it's done:
  `nohup python3 pod/tts.py script.txt episode.mp3 > tts.log 2>&1 &` then every minute or two `tail -3 tts.log` until it shows `episode.mp3: … min` (or an error).
- If it fails, run it once more; if it fails again, stop and report the error. Don't switch to another voice.

## 5. Publish + record (push straight to main: GitHub Pages serves the feed from main)
```
cd pod
python3 publish.py <path-to-mp3> TODAY "<title>" "<description>" ../transcript.txt
python3 srs.py record ../words.json TODAY ../used.json > ../stats.json
git add -A
git commit -qm "Episode TODAY"
git push origin HEAD:main
git fetch -q origin && test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" && echo PUSHED-OK
```
- Title: `TODAY · ` + a short Chinese headline of the top story.
- Description (short summary; the full transcript is added automatically from transcript.txt): one line per story in English with its source, then "Vocabulary: " + practised words (hanzi + pinyin), then "New words: " + pre-taught words (hanzi + pinyin + English).
- Don't modify publish.py, srs.py, tts.py, vocab_import.py, RUN.md, teacher_sentences.json, level/, known_words.json, the cover or feed settings.
- Continue to step 6 only after PUSHED-OK. If the push fails: `git pull --rebase origin main`, push again; if it still fails, skip step 6 and start the final reply with "PUSH FAILED:" plus the exact git error. Don't try other credentials or workarounds.

## 6. Mirror stats into the doc
stats.json gives heard / last_heard / next_due per word. Re-read the table (`view` + `parentId`) for a fresh `rev`, then send ONE `update` with one op per changed cell (Heard = col 5, Last heard = col 6, Next due = col 7, 0-indexed, header = row 0; match rows by Hanzi): `{"op":"replace","target":{"kind":"cell","table":"<table id>","row":R,"col":C},"ifRev":<rev>,"with":{"from":{"kind":"inline","content":"<value>"},"as":"text"}}` (load `guide` topic.editing if refused). Never touch other columns or add/delete/reorder rows. If refused because Kian edited the table, re-read once and retry; then skip and mention it.

## 7. Final reply (brief, English)
Date, story headlines with sources (and which fetch method worked for Al Jazeera and taz), practised words, explained words, final coverage, and whether the feed (PUSHED-OK) and the doc were updated. No transcript.
