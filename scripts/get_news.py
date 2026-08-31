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

SCI_TECH_FEEDS = [
    "https://www.pbs.org/newshour/feeds/rss/science",
    "https://www.esa.int/rssfeed/Our_Activities/Observing_the_Earth",
    "https://feeds.npr.org/1007/rss.xml",
    "https://www.sciencedaily.com/rss/top/science.xml"
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

def limit_diverse_top_n(items, n):
    # Step 1: group items by source
    by_source = {}
    for item in items:
        src = item["source"]
        by_source.setdefault(src, []).append(item)

    # Step 2: take newest item from each source
    newest_per_source = []
    for src, group in by_source.items():
        group_sorted = sorted(group, key=lambda x: x["published"], reverse=True)
        newest_per_source.append(group_sorted[0])

    # Step 3: sort those by date
    sorted_newest = sorted(newest_per_source, key=lambda x: x["published"], reverse=True)

    # Step 4: return top n
    return sorted_newest[:n]


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
    # 1. Create a naive UTC target object
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    recent_items = []
    for item in items:
        try:
            # 2. Extract date and strip any timezone tracking strings if present
            # Splits on 'Z' or '+' to ensure we isolate the clean core timestamp
            clean_pub = item["published"].split('+')[0].split('Z')[0]
            
            # 3. Parse as a naive datetime object
            # Handles 'YYYY-MM-DDTHH:MM:SS' or fall back to date layout
            if 'T' in clean_pub:
                dt_item = datetime.fromisoformat(clean_pub)
            else:
                dt_item = datetime.strptime(clean_pub, "%Y-%m-%d")
                
            # 4. Compare naive vs naive directly
            if dt_item > cutoff:
                recent_items.append(item)
                
        except Exception as e:
            print(f"⚠ Skipping item date parsing mismatch: {e}")
            continue
            
    return recent_items


def main():
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument('-S', '--science', action='store_true', help='Set to science and technology')
    parser.add_argument('-G', '--gaming', action='store_true', help='Set to gaming news')
    parser.add_argument('-R', '--rss', type=str, default='')
    parser.add_argument('-P', '--prompt', type=str, default='prompts/news.txt', help='System prompt to use')
    parser.add_argument('-O', '--output', type=str, default='today.txt')
    parser.add_argument('-L', '--latest', action='store_true', help='Get lastest news only')
    parser.add_argument('-T', '--total', type=int, default=3, help='Number of articles to use')
    args = parser.parse_args()
    topic = json.loads(Path(args.rss).read_text())
    prompt = args.prompt
    '''
    if args.science:
        topic = SCI_TECH_FEEDS
        prompt = 'prompts/science.txt'
    elif args.gaming:
        topic = XBOX_NEWS_FEEDS
        prompt = 'prompts/gamer.txt'
    else:
        if args.rss:
            topic = [args.rss]
        else:
            topic = WORLD_NEWS_FEEDS
        prompt = args.custom 
    '''
    items = fetch_items(topic)
    if args.latest:
        items = filter_recent(items)
    limited = limit_diverse_top_n(items,args.total)

    for i, item in enumerate(limited, 1):
        item["id"] = i

    json_context = json.dumps(limited, indent=2)

    from pathlib import Path
    template = Path(prompt).read_text().format(json_context=json_context)
    Path(args.output).write_text(template)
    print(template[:125])

if __name__ == '__main__':
    main()



