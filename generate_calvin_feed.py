from datetime import datetime, timedelta
from pathlib import Path
import requests
import json
import html
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
    try:
        r = requests.head(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False

def find_next_comic(used_dates):
    # start the search from one day after the most recent used date
    if used_dates:
        last_date = datetime.strptime(used_dates[-1], "%Y-%m-%d")
        current = last_date + timedelta(days=1)
    else:
        current = START_DATE

    while True:
        datestr = current.strftime("%Y-%m-%d")
        url = date_to_url(current)
        if check_url_exists(url):
            print(f"[DEBUG] Found next comic {datestr} at {url}")
            return current, url
        current += timedelta(days=1)

def build_rss_items(latest_date, comic_url):
    pub_date_str = latest_date.strftime("%a, %d %b %Y 00:00:00 GMT")
    title = f"Calvin and Hobbes – {pub_date_str}"

    item = ET.Element("item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = SITE_LINK
    ET.SubElement(item, "guid").text = comic_url
    ET.SubElement(item, "pubDate").text = pub_date_str
    ET.SubElement(item, "description").text = (
        f'<![CDATA[<img src="{comic_url}" alt="Calvin and Hobbes comic" />]]>'
    )
    ET.SubElement(item, "enclosure", attrib={"url": comic_url, "type": "image/gif"})

    items = [item]

    # append existing items (keep previous MAX_ITEMS - 1)
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
            print("[WARN] Could not parse existing feed.xml")

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

def write_html(comic_url):
    html_text = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset='UTF-8'>
  <meta property='og:title' content='Daily Calvin and Hobbes' />
  <meta property='og:image' content='{comic_url}' />
  <meta name='twitter:card' content='summary_large_image' />
  <title>Daily Calvin and Hobbes</title>
</head>
<body>
  <h1>Daily Calvin and Hobbes</h1>
  <img src='{comic_url}' alt='Calvin and Hobbes comic'/>
</body>
</html>"""
    Path(HTML_FILE).write_text(html_text)

def main():
    used = load_used()
    next_date, comic_url = find_next_comic(used)
    datestr = next_date.strftime("%Y-%m-%d")
    pub_date_rss = next_date.strftime("%a, %d %b %Y 00:00:00 GMT")

    items = build_rss_items(next_date, comic_url)
    write_rss(pub_date_rss, items)
    write_html(comic_url)

    used.append(datestr)
    save_used(used)
    print(f"[SUCCESS] Posted comic for {datestr}: {comic_url}")

if __name__ == "__main__":
    main()
