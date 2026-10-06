# Mandarin News Daily

Private, auto-generated HSK 4 Mandarin news podcast.

- Feed: https://kianahi.github.io/mandarin-news-podcast/feed.xml
- `publish.py` adds an episode and rebuilds `feed.xml` (keeps the latest 14).
- `srs.py` picks vocabulary by spaced repetition and records exposures.
  - `vocab_state.json`: per word: times heard, schedule step, last heard, next due
  - `exposures.csv`: full log of every word heard, by date
- `level/`: vocabulary level test and script checker
  - `levelquiz.py`: adaptive yes/no test with fake words → `known_words.json` (words you know) + `level_profile.json`
  - `check_script.py`: flags words in an episode script that are not in `known_words.json` or the vocab doc
  - `bank.json`: 11,470 HSK 1–9 words with frequency ranks, from [complete-hsk-vocabulary](https://github.com/drkameleon/complete-hsk-vocabulary) (MIT)
  - `pseudowords.json`: fake two-character words (checked against the jieba dictionary) used to catch over-claiming
- `vocab_import.py`: helper for importing teacher material (lookup of pinyin/meaning/HSK, saves teacher example sentences)
  - `teacher_sentences.json`: example sentences from teachers, keyed by word; used in the podcast's vocabulary review
  - `imports.csv`: log of imports
