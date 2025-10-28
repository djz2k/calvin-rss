from datetime import datetime, timedelta
from pathlib import Path
import requests
import json
import xml.etree.ElementTree as ET

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
MAX_ITEMS = 50

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
    try:
        r = requests.head(url, headers={"User-Agent": "Mozilla/5.0"})
        return r.status_code == 200
    except Exception:
        return False

def find_next_comic(used_dates):
    current = START_DATE
    while True:
        datestr = current.strftime("%Y-%m-%d")
        if datestr not in used_dates:
            url = date_to_url(current)
            if check_url_exists(url):
                print(f"[DEBUG] Found next comic {datestr} at {url}")
                return current, url
        current += timedelta(days=1)

def build_rss_items(latest_date, comic_url):
    items = []

    pub_date_str = latest_date.strftime("%a, %d %b %Y 00:00:00 GMT")
    title = f"Calvin and Hobbes – {pub_date_str}"
    link_url = f"{SITE_LINK}calvin-{latest_date.strftime('%Y-%m-%d')}.html"

    item = ET.Element("item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = link_url
    ET.SubElement(item, "guid").text = link_url
    ET.SubElement(item, "pubDate").text = pub_date_str
    ET.SubElement(item, "description").text = f'<![CDATA[<img src="{comic_url}" alt="Calvin and Hobbes comic" />]]>'
    ET.SubElement(item, "enclosure", attrib={
        "url": comic_url,
        "type": "image/gif"
    })

    items.append(item)

    # Append existing items
    if Path(RSS_FILE).exists():
        try:
            tree = ET.parse(RSS_FILE)
            root = tree.getroot()
            channel = root.find("channel")
            if channel is not None:
                for old_item in channel.findall("item"):
                    if len(items) >= MAX_ITEMS:
                        break
                    items.append(old_item)
        except ET.ParseError:
            print("[WARN] Failed to parse existing feed.xml, skipping old items")

    return items

def write_rss(pub_date, items):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = FEED_TITLE
    ET.SubElement(channel, "link").text = FEED_LINK
    ET.SubElement(channel, "description").text = FEED_DESC
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "pubDate").text = pub_date
    ET.SubElement(channel, "lastBuildDate").text = pub_date

    for item in items:
        channel.append(item)

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ", level=0)
    tree.write(RSS_FILE, encoding="utf-8", xml_declaration=True)

def write_html(comic_url, date):
    """Write both index.html and dated HTML page for the comic"""
    date_str = date.strftime("%Y-%m-%d")
    filename = f"docs/calvin-{date_str}.html"

    html_text = f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta property="og:title" content="Calvin and Hobbes – {date_str}" />
  <meta property="og:image" content="{comic_url}" />
  <meta name="twitter:card" content="summary_large_image" />
  <title>Calvin and Hobbes – {date_str}</title>
</head>
<body>
  <h1>Calvin and Hobbes – {date_str}</h1>
  <img src="{comic_url}" alt="Calvin and Hobbes comic"/>
</body>
</html>'''

    Path(filename).write_text(html_text)
    Path(HTML_FILE).write_text(html_text)

def main():
    used = load_used()
    next_date, comic_url = find_next_comic(used)
    datestr = next_date.strftime("%Y-%m-%d")
    pub_date_rss = next_date.strftime("%a, %d %b %Y 00:00:00 GMT")

    items = build_rss_items(next_date, comic_url)
    write_rss(pub_date_rss, items)
    write_html(comic_url, next_date)

    used.add(datestr)
    save_used(used)
    print(f"[SUCCESS] Posted comic for {datestr}: {comic_url}")

if __name__ == "__main__":
    main()
