#!/usr/bin/env python3
"""Add an episode and rebuild feed.xml. Usage: publish.py <mp3> <YYYY-MM-DD> <title> <description>"""
import sys, json, os, shutil, subprocess, datetime
from email.utils import format_datetime
from xml.sax.saxutils import escape
BASE = "https://kianahi.github.io/mandarin-news-podcast"
KEEP = 14
root = os.path.dirname(os.path.abspath(__file__))
idx_path = os.path.join(root, "episodes.json")
eps = json.load(open(idx_path)) if os.path.exists(idx_path) else []
if len(sys.argv) == 5:
    src, date, title, desc = sys.argv[1:]
    fn = f"mandarin-news-{date}.mp3"
    shutil.copy(src, os.path.join(root, "episodes", fn))
    dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",src]).strip())
    eps = [e for e in eps if e["file"] != fn]
    eps.append({"file": fn, "date": date, "title": title, "desc": desc,
                "size": os.path.getsize(src), "duration": int(dur),
                "pub": format_datetime(datetime.datetime.now(datetime.timezone.utc))})
eps.sort(key=lambda e: e["date"], reverse=True)
for old in eps[KEEP:]:
    p = os.path.join(root, "episodes", old["file"])
    if os.path.exists(p): os.remove(p)
eps = eps[:KEEP]
json.dump(eps, open(idx_path, "w"), ensure_ascii=False, indent=1)
items = "".join(f"""
  <item>
   <title>{escape(e['title'])}</title>
   <description>{escape(e['desc'])}</description>
   <enclosure url="{BASE}/episodes/{e['file']}" length="{e['size']}" type="audio/mpeg"/>
   <guid isPermaLink="false">{e['file']}</guid>
   <pubDate>{e['pub']}</pubDate>
   <itunes:duration>{e['duration']}</itunes:duration>
   <itunes:explicit>false</itunes:explicit>
  </item>""" for e in eps)
feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
 <channel>
  <title>每日中文新闻 · Mandarin News Daily</title>
  <link>{BASE}/</link>
  <atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>
  <language>zh-cn</language>
  <description>A private daily HSK 4 Mandarin news briefing: world, China and Germany, with personal vocabulary review. Generated automatically.</description>
  <itunes:author>Kian</itunes:author>
  <itunes:image href="{BASE}/cover.png"/>
  <itunes:category text="Education"><itunes:category text="Language Learning"/></itunes:category>
  <itunes:explicit>false</itunes:explicit>
  <itunes:block>Yes</itunes:block>{items}
 </channel>
</rss>
"""
open(os.path.join(root, "feed.xml"), "w").write(feed)
print("feed updated:", len(eps), "episodes")
