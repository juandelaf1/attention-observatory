import polars as pl
from datetime import datetime, timezone
from typing import Optional
import warnings
import requests
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


def fetch_top_stories(limit: int = 50) -> list[int]:
    resp = requests.get(f"{HN_API_BASE}/topstories.json", timeout=30, verify=False)
    resp.raise_for_status()
    return resp.json()[:limit]


def fetch_item(item_id: int, retries: int = 3) -> Optional[dict]:
    import requests
    import time

    for attempt in range(retries):
        try:
            resp = requests.get(
                f"{HN_API_BASE}/item/{item_id}.json",
                timeout=15,
                verify=False,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            return None


def get_user_submissions(username: str, max_items: int = 50) -> list[dict]:
    resp = requests.get(f"{HN_API_BASE}/user/{username}.json", timeout=30, verify=False)
    resp.raise_for_status()
    user = resp.json()
    if not user:
        return []
    submitted = (user.get("submitted") or [])[:max_items]
    items = []
    for sid in submitted:
        item = fetch_item(sid)
        if item and item.get("type") in ("story", "comment"):
            items.append(item)
    return items


def ingest_top_stories(n_stories: int = 50, comments_per_story: int = 20) -> tuple[pl.DataFrame, pl.DataFrame]:
    print(f"[hackernews] Fetching top {n_stories} stories...")
    story_ids = fetch_top_stories(n_stories)

    authors_seen: dict[str, dict] = {}
    posts = []

    for sid in story_ids:
        story = fetch_item(sid)
        if not story or story.get("type") != "story":
            continue

        author = story.get("by", "[deleted]")
        if author not in authors_seen and author != "[deleted]":
            authors_seen[author] = {
                "actor_id": f"HN_{author}",
                "username": author,
                "platform": "hackernews",
                "followers": story.get("score", 0),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }

        created = datetime.fromtimestamp(story.get("time", 0), tz=timezone.utc)
        posts.append({
            "post_id": f"HN_{story['id']}",
            "actor_id": f"HN_{author}" if author != "[deleted]" else "HN_deleted",
            "platform": "hackernews",
            "timestamp": created.isoformat(),
            "title": story.get("title", ""),
            "content_text": story.get("title", "") + " " + (story.get("text", "") or ""),
            "likes": story.get("score", 0),
            "comments": story.get("descendants", 0),
            "shares": 0,
            "views": story.get("score", 0) * 10,
            "followers_at_post": story.get("score", 1),
            "sentiment_score": 0.0,
            "luxury_keyword_density": 0.0,
            "is_legally_truncated_post": False,
            "story_id": story["id"],
        })

        kid_ids = (story.get("kids") or [])[:comments_per_story]
        for kid_id in kid_ids:
            comment = fetch_item(kid_id)
            if not comment or comment.get("type") != "comment":
                continue
            cauthor = comment.get("by", "[deleted]")
            if cauthor not in authors_seen and cauthor != "[deleted]":
                authors_seen[cauthor] = {
                    "actor_id": f"HN_{cauthor}",
                    "username": cauthor,
                    "platform": "hackernews",
                    "followers": 0,
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                }
            ccreated = datetime.fromtimestamp(comment.get("time", 0), tz=timezone.utc)
            posts.append({
                "post_id": f"HN_{comment['id']}",
                "actor_id": f"HN_{cauthor}" if cauthor != "[deleted]" else "HN_deleted",
                "platform": "hackernews",
                "timestamp": ccreated.isoformat(),
                "title": "",
                "content_text": comment.get("text", ""),
                "likes": comment.get("score", 0),
                "comments": 0,
                "shares": 0,
                "views": comment.get("score", 1) * 5,
                "followers_at_post": 1,
                "sentiment_score": 0.0,
                "luxury_keyword_density": 0.0,
                "is_legally_truncated_post": False,
                "story_id": story["id"],
            })

    actors = list(authors_seen.values())
    print(f"[hackernews] {len(posts)} items from {len(actors)} authors")
    return pl.DataFrame(actors), pl.DataFrame(posts)


def save_bronze(actors: pl.DataFrame, posts: pl.DataFrame, output_dir: str = "data/bronze"):
    import os
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    actors_path = f"{output_dir}/hn_actors_{ts}.parquet"
    posts_path = f"{output_dir}/hn_posts_{ts}.parquet"
    actors.write_parquet(actors_path)
    posts.write_parquet(posts_path)
    print(f"[hackernews] Actors -> {actors_path} ({len(actors)} rows)")
    print(f"[hackernews] Posts  -> {posts_path} ({len(posts)} rows)")
    return actors_path, posts_path


if __name__ == "__main__":
    actors, posts = ingest_top_stories(30, 15)
    if len(actors) > 0:
        save_bronze(actors, posts)
