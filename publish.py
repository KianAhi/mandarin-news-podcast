#!/usr/bin/env python3
"""Add an episode and rebuild feed.xml.

Usage: publish.py <mp3> <YYYY-MM-DD> <title> <description> [<transcript.txt>]

- description: short summary (headlines, vocabulary); shown where an app has little space.
- transcript.txt (optional): the full episode script. It becomes the episode's show notes
  (<content:encoded>, which Apple Podcasts shows as the episode description), together with the
  short summary. Paragraphs are separated by blank lines.
"""
import sys, json, os, shutil, subprocess, datetime, html
from email.utils import format_datetime
from xml.sax.saxutils import escape

BASE = "https://kianahi.github.io/mandarin-news-podcast"
KEEP = 14
root = os.path.dirname(os.path.abspath(__file__))
idx_path = os.path.join(root, "episodes.json")
eps = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else []

if len(sys.argv) in (5, 6):
    src, date, title, desc = sys.argv[1:5]
    transcript = open(sys.argv[5], encoding="utf-8").read().strip() if len(sys.argv) == 6 else ""
    fn = f"mandarin-news-{date}.mp3"
    shutil.copy(src, os.path.join(root, "episodes", fn))
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", src]).strip())
    eps = [e for e in eps if e["file"] != fn]
    eps.append({"file": fn, "date": date, "title": title, "desc": desc, "transcript": transcript,
                "size": os.path.getsize(src), "duration": int(dur),
                "pub": format_datetime(datetime.datetime.now(datetime.timezone.utc))})
elif sys.argv[1:] != ["--rebuild"]:
    sys.exit(__doc__)

eps.sort(key=lambda e: e["date"], reverse=True)
for old in eps[KEEP:]:
    p = os.path.join(root, "episodes", old["file"])
    if os.path.exists(p):
        os.remove(p)
eps = eps[:KEEP]
json.dump(eps, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def paras(text):
    return "".join(f"<p>{html.escape(p.strip()).replace(chr(10), '<br/>')}</p>"
                   for p in text.split("\n\n") if p.strip())


def notes(e):
    body = paras(e["desc"])
    if e.get("transcript"):
        body += "<hr/><p><b>Transcript</b></p>" + paras(e["transcript"])
    return body.replace("]]>", "]]&gt;")


items = "".join(f"""
  <item>
   <title>{escape(e['title'])}</title>
   <description>{escape(e['desc'])}</description>
   <content:encoded><![CDATA[{notes(e)}]]></content:encoded>
   <enclosure url="{BASE}/episodes/{e['file']}" length="{e['size']}" type="audio/mpeg"/>
   <guid isPermaLink="false">{e['file']}</guid>
   <pubDate>{e['pub']}</pubDate>
   <itunes:duration>{e['duration']}</itunes:duration>
   <itunes:explicit>false</itunes:explicit>
  </item>""" for e in eps)
feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
 <channel>
  <title>每日中文新闻 · Mandarin News Daily</title>
  <link>{BASE}/</link>
  <atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>
  <language>zh-cn</language>
  <description>A private daily HSK 4 Mandarin news briefing: Middle East, China and Germany, with personal vocabulary review. Generated automatically.</description>
  <itunes:author>Kian</itunes:author>
  <itunes:image href="{BASE}/cover.png"/>
  <itunes:category text="Education"><itunes:category text="Language Learning"/></itunes:category>
  <itunes:explicit>false</itunes:explicit>
  <itunes:block>Yes</itunes:block>{items}
 </channel>
</rss>
"""
open(os.path.join(root, "feed.xml"), "w", encoding="utf-8").write(feed)
print("feed updated:", len(eps), "episodes")
