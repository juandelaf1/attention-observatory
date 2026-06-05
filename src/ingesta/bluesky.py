import polars as pl
from datetime import datetime, timezone
import requests

BSKY_API = "https://api.bsky.app/xrpc"


def search_posts(query: str, limit: int = 50) -> list[dict]:
    resp = requests.get(
        f"{BSKY_API}/app.bsky.feed.searchPosts",
        params={"q": query, "limit": min(limit, 100)},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("posts", [])


def get_profile(actor: str) -> dict | None:
    try:
        resp = requests.get(
            f"{BSKY_API}/app.bsky.actor.getProfile",
            params={"actor": actor},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def ingest_search(topics: list[str] | None = None, posts_per_topic: int = 30) -> tuple[pl.DataFrame, pl.DataFrame]:
    topics = topics or [
        "artificial intelligence", "machine learning", "data science",
        "climate", "technology", "startup", "research", "science",
    ]
    print(f"[bluesky] Searching {len(topics)} topics, {posts_per_topic} posts each...")

    authors_seen: dict[str, dict] = {}
    posts = []

    for topic in topics:
        try:
            results = search_posts(topic, limit=posts_per_topic)
        except Exception as e:
            print(f"[bluesky] Search '{topic}' failed: {e}")
            continue

        for post in results:
            author = post.get("author", {})
            handle = author.get("handle", "unknown")
            did = author.get("did", f"did:{handle}")

            if handle not in authors_seen:
                authors_seen[handle] = {
                    "actor_id": f"BSKY_{did}",
                    "username": handle,
                    "display_name": author.get("displayName", ""),
                    "platform": "bluesky",
                    "followers": author.get("followersCount", 0),
                    "follows": author.get("followsCount", 0),
                    "posts_count": author.get("postsCount", 0),
                    "description": (author.get("description") or "")[:500],
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                }

            record = post.get("record", {})
            created = record.get("createdAt", datetime.now(timezone.utc).isoformat())

            posts.append({
                "post_id": f"BSKY_{post.get('uri', '').split('/')[-1]}",
                "actor_id": f"BSKY_{did}",
                "platform": "bluesky",
                "timestamp": created,
                "title": "",
                "content_text": (record.get("text", "") or "")[:2000],
                "likes": post.get("likeCount", 0),
                "comments": post.get("replyCount", 0),
                "shares": post.get("repostCount", 0) + post.get("quoteCount", 0),
                "views": 0,
                "followers_at_post": author.get("followersCount", 0),
                "sentiment_score": 0.0,
                "luxury_keyword_density": 0.0,
                "is_legally_truncated_post": False,
                "topic": topic,
            })

        print(f"[bluesky] '{topic}': {len(results)} posts")

    actors = list(authors_seen.values())
    print(f"[bluesky] Total: {len(posts)} posts from {len(actors)} actors")
    return pl.DataFrame(actors), pl.DataFrame(posts)


def save_bronze(actors: pl.DataFrame, posts: pl.DataFrame, output_dir: str = "data/bronze"):
    import os
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    actors_path = f"{output_dir}/bluesky_actors_{ts}.parquet"
    posts_path = f"{output_dir}/bluesky_posts_{ts}.parquet"
    actors.write_parquet(actors_path)
    posts.write_parquet(posts_path)
    print(f"[bluesky] Actors -> {actors_path} ({len(actors)} rows)")
    print(f"[bluesky] Posts  -> {posts_path} ({len(posts)} rows)")
    return actors_path, posts_path


if __name__ == "__main__":
    actors, posts = ingest_search(posts_per_topic=20)
    if len(actors) > 0:
        save_bronze(actors, posts)
