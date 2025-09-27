import requests
from bs4 import BeautifulSoup
import json
import datetime
from pathlib import Path

# === Config ===
HTML_URL = "https://www.s-anand.net/calvinandhobbes.html"
USED_FILE = "used_comics.json"
RSS_FILE = "docs/feed.xml"
HTML_FILE = "docs/index.html"
FEED_TITLE = "Daily Calvin and Hobbes"
FEED_LINK = "https://djz2k.github.io/calvin-rss/feed.xml"
SITE_LINK = "https://djz2k.github.io/calvin-rss/"
FEED_DESC = "One Calvin & Hobbes comic per day"

# === Comic Logic ===
def get_all_comics():
    response = requests.get(HTML_URL)
    print(f"[DEBUG] Status code: {response.status_code}")
    html = response.text[:1000]  # print only first 1000 chars
    print(f"[DEBUG] Page snippet:\n{html}\n--- END SNIPPET ---")

    soup = BeautifulSoup(response.text, "html.parser")
    imgs = soup.find_all("img")
    print(f"[INFO] Found {len(imgs)} total <img> tags")

    # print first 3 image URLs
    for i, img in enumerate(imgs[:3]):
        print(f"[DEBUG] Image {i+1}: {img.get('src')}")

    comic_imgs = [img["src"] for img in imgs if "assets.s-anand.net/calvinandhobbes" in img.get("src", "")]
    print(f"[INFO] Found {len(comic_imgs)} Calvin & Hobbes comic images.")

    return comic_imgs

def load_used():
    if Path(USED_FILE).exists():
        with open(USED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_used(used):
    with open(USED_FILE, "w") as f:
        json.dump(sorted(used), f, indent=2)

# === RSS Generation ===
def write_rss(comic_url, pub_date):
    rss = f'''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>{FEED_TITLE}</title>
  <link>{FEED_LINK}</link>
  <description>{FEED_DESC}</description>
  <language>en-us</language>
  <pubDate>{pub_date}</pubDate>
  <lastBuildDate>{pub_date}</lastBuildDate>
  <item>
    <title>Calvin and Hobbes – {pub_date}</title>
    <link>{SITE_LINK}</link>
    <guid>{comic_url}</guid>
    <pubDate>{pub_date}</pubDate>
    <description><![CDATA[<img src="{comic_url}" alt="Calvin and Hobbes comic" />]]></description>
    <enclosure url="{comic_url}" type="image/png" />
  </item>
</channel>
</rss>'''
    Path(RSS_FILE).write_text(rss)

# === HTML Open Graph for Social Sharing ===
def write_html(comic_url):
    html = f'''<!DOCTYPE html>
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
    Path(HTML_FILE).write_text(html)

# === Main Logic ===
def main():
    all_comics = get_all_comics()
    used = load_used()

    for comic_url in all_comics:
        if comic_url not in used:
            today = datetime.datetime.utcnow().strftime("%a, %d %b %Y 00:00:00 GMT")
            write_rss(comic_url, today)
            write_html(comic_url)
            used.add(comic_url)
            save_used(used)
            print(f"[SUCCESS] Posted comic: {comic_url}")
            return

    print("[DONE] No new comics to post.")

if __name__ == "__main__":
    main()
