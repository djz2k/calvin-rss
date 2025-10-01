from datetime import datetime, timedelta
from pathlib import Path
import requests
import json
import html

# === Config ===
START_DATE = datetime(1985, 11, 18)
BASE_URL = "https://picayune.uclick.com/comics/ch/{year}/ch{shortdate}.gif"
USED_FILE = "used_comics.json"
RSS_FILE = "docs/feed.xml"
HTML_FILE = "docs/index.html"
FEED_TITLE = "Daily Calvin and Hobbes"
FEED_LINK = "https://djz2k.github.io/calvin-rss/feed.xml"
SITE_LINK = "https://djz2k.github.io/calvin-rss/"
FEED_DESC = "One Calvin & Hobbes comic per day"

# === Helpers ===

def load_used():
    if Path(USED_FILE).exists():
        with open(USED_FILE, "r") as f:
            return sorted(json.load(f))
    return []

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
    # find the next date not used
    current = START_DATE
    while True:
        datestr = current.strftime("%Y-%m-%d")
        if datestr not in used_dates:
            url = date_to_url(current)
            if check_url_exists(url):
                return current, url
        current += timedelta(days=1)

def build_rss(all_dates):
    # Build full RSS from scratch
    items = []
    for datestr in all_dates:
        date_obj = datetime.strptime(datestr, "%Y-%m-%d")
        comic_url = date_to_url(date_obj)
        pub_date = date_obj.strftime("%a, %d %b %Y 00:00:00 GMT")
        title = html.escape(f"Calvin and Hobbes – {pub_date}")
        description = f'<![CDATA[<img src="{comic_url}" alt="Calvin and Hobbes comic" />]]>'
        items.append(f"""
  <item>
    <title>{title}</title>
    <link>{SITE_LINK}</link>
    <guid>{comic_url}</guid>
    <pubDate>{pub_date}</pubDate>
    <description>{description}</description>
    <enclosure url="{comic_url}" type="image/gif" />
  </item>""")
    # last pubDate = newest
    last_date = datetime.strptime(all_dates[-1], "%Y-%m-%d")
    last_pub = last_date.strftime("%a, %d %b %Y 00:00:00 GMT")

    rss = f'''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>{html.escape(FEED_TITLE)}</title>
  <link>{html.escape(FEED_LINK)}</link>
  <description>{html.escape(FEED_DESC)}</description>
  <language>en-us</language>
  <pubDate>{last_pub}</pubDate>
  <lastBuildDate>{last_pub}</lastBuildDate>
{"".join(items)}
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

    used.append(datestr)
    save_used(used)

    # Build feed from all used dates
    build_rss(used)

    # Update HTML to latest comic
    write_html(comic_url)

    print(f"[SUCCESS] Posted comic for {datestr}: {comic_url}")

if __name__ == "__main__":
    main()
