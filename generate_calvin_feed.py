from datetime import datetime, timedelta
from pathlib import Path
import requests
import json
import html  # ← For escaping special characters

# === Config ===
START_DATE = datetime(1985, 11, 18)
BASE_URL = "https://picayune.uclick.com/comics/ch/{year}/ch{shortdate}.gif"
USED_FILE = "used_comics.json"
RSS_FILE = "docs/feed.xml"
HTML_FILE = "docs/index.html"
FEED_TITLE = "Daily Calvin and Hobbes"
FEED_LINK = "https://djz2k.github.io/calvin-rss/feed.xml"
SITE_LINK = "https://djz2k.github.io/calvin-rss/"
FEED_DESC = "One Calvin &amp Hobbes comic per day"

# === Helpers ===

def load_used():
    if Path(USED_FILE).exists():
        with open(USED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_used(used):
    with open(USED_FILE, "w") as f:
        json.dump(sorted(used), f, indent=2)

def date_to_url(date):
    year = date.year
    shortdate = date.strftime("%y%m%d")
    return BASE_URL.format(year=year, shortdate=shortdate)

def check_url_exists(url):
    r = requests.head(url)
    return r.status_code == 200

def find_next_comic(used_dates):
    current = START_DATE
    while True:
        datestr = current.strftime("%Y-%m-%d")
        if datestr not in used_dates:
            url = date_to_url(current)
            if check_url_exists(url):
                return current, url
        current += timedelta(days=1)

def write_rss(comic_url, pub_date):
    # Escape special characters
    title = html.escape(f"Calvin and Hobbes – {pub_date}")
    link = html.escape(SITE_LINK)
    guid = html.escape(comic_url)
    pub_date_escaped = html.escape(pub_date)

    description = f'<![CDATA[<img src="{comic_url}" alt="Calvin and Hobbes comic" />]]>'

    rss = f'''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>{html.escape(FEED_TITLE)}</title>
  <link>{html.escape(FEED_LINK)}</link>
  <description>{html.escape(FEED_DESC)}</description>
  <language>en-us</language>
  <pubDate>{pub_date_escaped}</pubDate>
  <lastBuildDate>{pub_date_escaped}</lastBuildDate>
  <item>
    <title>{title}</title>
    <link>{link}</link>
    <guid>{guid}</guid>
    <pubDate>{pub_date_escaped}</pubDate>
    <description>{description}</description>
    <enclosure url="{comic_url}" type="image/gif" />
  </item>
</channel>
</rss>'''
    Path(RSS_FILE).write_text(rss)

def write_html(comic_url):
    html_text = f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta property="og:title" content="Daily Calvin and Hobbes" />
  <meta property="og:image" content="{comic_url}" />
  <meta name="twitter:card" content="summary_large_image" />
  <title>Daily Calvin and Hobbes</title>
</head>
<body>
  <h1>Daily Calvin and Hobbes</h1>
  <img src="{comic_url}" alt="Calvin and Hobbes comic"/>
</body>
</html>'''
    Path(HTML_FILE).write_text(html_text)

# === Main ===

def main():
    used = load_used()
    next_date, comic_url = find_next_comic(used)
    datestr = next_date.strftime("%Y-%m-%d")
    pub_date_rss = next_date.strftime("%a, %d %b %Y 00:00:00 GMT")

    write_rss(comic_url, pub_date_rss)
    write_html(comic_url)

    used.add(datestr)
    save_used(used)
    print(f"[SUCCESS] Posted comic for {datestr}: {comic_url}")

if __name__ == "__main__":
    main()
