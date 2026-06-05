import polars as pl
from datetime import datetime, timezone
import requests
import re

MASTODON_INSTANCES = [
    "mastodon.world",
    "techhub.social",
    "fosstodon.org",
    "mastodon.online",
    "hachyderm.io",
]


def _clean_html(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()


def fetch_public_timeline(instance: str, limit: int = 40) -> list[dict]:
    resp = requests.get(
        f"https://{instance}/api/v1/timelines/public",
        params={"limit": min(limit, 40), "local": "true"},
        timeout=30,
        headers={"User-Agent": "attention-observatory/0.1"},
    )
    resp.raise_for_status()
    return resp.json()


def ingest_public_timelines(
    instances: list[str] | None = None,
    posts_per_instance: int = 40,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    instances = instances or MASTODON_INSTANCES[:3]
    print(f"[mastodon] Fetching public timelines from {len(instances)} instances...")

    authors_seen: dict[str, dict] = {}
    posts = []

    for instance in instances:
        try:
            toots = fetch_public_timeline(instance, limit=posts_per_instance)
        except Exception as e:
            print(f"[mastodon] {instance}: {e}")
            continue

        for toot in toots:
            acct = toot.get("account", {})
            username = acct.get("acct", "unknown")
            acct_id = acct.get("id", "0")

            if username not in authors_seen:
                authors_seen[username] = {
                    "actor_id": f"MAST_{instance}_{acct_id}",
                    "username": username,
                    "display_name": acct.get("display_name", ""),
                    "platform": "mastodon",
                    "instance": instance,
                    "followers": acct.get("followers_count", 0),
                    "following": acct.get("following_count", 0),
                    "posts_count": acct.get("statuses_count", 0),
                    "note": _clean_html(acct.get("note", "")),
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                }

            created = toot.get("created_at", datetime.now(timezone.utc).isoformat())

            posts.append({
                "post_id": f"MAST_{instance}_{toot.get('id', '0')}",
                "actor_id": f"MAST_{instance}_{acct_id}",
                "platform": "mastodon",
                "instance": instance,
                "timestamp": created,
                "title": "",
                "content_text": _clean_html(toot.get("content", ""))[:2000],
                "likes": toot.get("favourites_count", 0),
                "comments": toot.get("replies_count", 0),
                "shares": toot.get("reblogs_count", 0),
                "views": toot.get("views", 0) or 0,
                "followers_at_post": acct.get("followers_count", 0),
                "sentiment_score": 0.0,
                "luxury_keyword_density": 0.0,
                "is_legally_truncated_post": False,
                "tags": str([t.get("name", "") for t in toot.get("tags", [])]),
            })

        print(f"[mastodon] {instance}: {len(toots)} posts")

    actors = list(authors_seen.values())
    print(f"[mastodon] Total: {len(posts)} posts from {len(actors)} actors")
    return pl.DataFrame(actors), pl.DataFrame(posts)


def save_bronze(actors: pl.DataFrame, posts: pl.DataFrame, output_dir: str = "data/bronze"):
    import os
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    actors_path = f"{output_dir}/mastodon_actors_{ts}.parquet"
    posts_path = f"{output_dir}/mastodon_posts_{ts}.parquet"
    actors.write_parquet(actors_path)
    posts.write_parquet(posts_path)
    print(f"[mastodon] Actors -> {actors_path} ({len(actors)} rows)")
    print(f"[mastodon] Posts  -> {posts_path} ({len(posts)} rows)")
    return actors_path, posts_path


if __name__ == "__main__":
    actors, posts = ingest_public_timelines(posts_per_instance=20)
    if len(actors) > 0:
        save_bronze(actors, posts)
