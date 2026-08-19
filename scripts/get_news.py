import feedparser
import trafilatura
from datetime import datetime, timedelta, timezone
import json

WORLD_NEWS_FEEDS = [
    "https://www.npr.org/rss/rss.php?id=1001",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.pbs.org/newshour/feeds/rss",
    "https://www.aljazeera.com/xml/rss/all.xml"
]

XBOX_NEWS_FEEDS = [
    "https://news.xbox.com/en-us/feed",
    "https://purexbox.com/feeds/news",
    "https://trueachievements.com/newsrss",
    "https://gamerant.com/feed/tag/xbox"
]

def limit_per_source(items, per_source=3):
    limited = []
    by_source = {}

    for item in items:
        src = item["source"]
        by_source.setdefault(src, []).append(item)

    for src, group in by_source.items():
        group_sorted = sorted(group, key=lambda x: x["published"], reverse=True)
        limited.extend(group_sorted[:per_source])

    return limited


def parse_timestamp(entry):
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    return None

def fetch_items(feeds):
    items = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            ts = parse_timestamp(entry)
            if not ts:
                continue

            link = entry.get("link", "")
            full_text = ""

            if link:
                downloaded = trafilatura.fetch_url(link)
                if downloaded:
                    full_text = trafilatura.extract(downloaded) or ""

            items.append({
                "title": entry.get("title", ""),
                "source": feed.feed.get("title", "Unknown Source"),
                "published": ts.isoformat(),
                "link": link,
                "content": full_text
            })
    return items

def filter_recent(items, hours=24):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return [item for item in items if datetime.fromisoformat(item["published"]) > cutoff]

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-G', '--gaming', action='store_true', help='Set to gaming news, defaults to world news')
    parser.add_argument('-O', '--output', type=str, default='today.txt')
    args = parser.parse_args()
    items = fetch_items(XBOX_NEWS_FEEDS if args.gaming else WORLD_NEWS_FEEDS)
    recent = filter_recent(items)
    limited = limit_per_source(recent, per_source=3)

    for i, item in enumerate(limited, 1):
        item["id"] = i

    json_context = json.dumps(limited, indent=2)

    from pathlib import Path
    prompt = 'prompts/gamer.txt' if args.gaming else 'prompts/news.txt'
    template = Path(prompt).read_text().format(json_context=json_context)
    Path(args.output).write_text(template)
    print(template[:125])

if __name__ == '__main__':
    main()



