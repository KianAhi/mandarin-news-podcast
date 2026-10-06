# Mandarin News Daily

Private, auto-generated HSK 4 Mandarin news podcast.

- Feed: https://kianahi.github.io/mandarin-news-podcast/feed.xml
- `publish.py` adds an episode and rebuilds `feed.xml` (keeps the latest 14).
- `srs.py` picks vocabulary by spaced repetition and records exposures.
  - `vocab_state.json`: per word: times heard, schedule step, last heard, next due
  - `exposures.csv`: full log of every word heard, by date
