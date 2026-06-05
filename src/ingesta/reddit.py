import os
import polars as pl
from datetime import datetime, timezone
from typing import Optional


def _get_credentials() -> tuple[str, str, str, str]:
    client_id = os.environ.get("REDDIT_CLIENT_ID", "")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
    user_agent = os.environ.get("REDDIT_USER_AGENT", "attention-observatory/0.1")

    if not client_id or not client_secret:
        raise ValueError(
            "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set.\n"
            "Get them at https://www.reddit.com/prefs/apps\n"
            "Then:\n"
            "  $env:REDDIT_CLIENT_ID = 'your_id'\n"
            "  $env:REDDIT_CLIENT_SECRET = 'your_secret'"
        )
    return client_id, client_secret, user_agent


def _get_auth_token(client_id: str, client_secret: str, user_agent: str) -> str:
    import requests

    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    data = {"grant_type": "client_credentials"}
    headers = {"User-Agent": user_agent}

    resp = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=auth, data=data, headers=headers, timeout=30
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _api_get(endpoint: str, token: str, user_agent: str, params: Optional[dict] = None) -> dict:
    import requests

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": user_agent,
    }
    url = f"https://oauth.reddit.com{endpoint}"
    resp = requests.get(url, headers=headers, params=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _parse_listing(data: dict, subreddit: str) -> tuple[list[dict], list[dict]]:
    authors_seen: dict[str, dict] = {}
    posts = []

    for child in data.get("data", {}).get("children", []):
        d = child["data"]
        kind = child.get("kind", "")
        if kind not in ("t3", "Link") and "title" not in d:
            continue
        author = d.get("author", "[deleted]")
        author_fullname = d.get("author_fullname", f"u_{author}")

        if author not in authors_seen and author != "[deleted]":
            authors_seen[author] = {
                "actor_id": f"RED_{author_fullname}",
                "username": author,
                "platform": "reddit",
                "followers": d.get("subreddit_subscribers", 1),
                "account_created_utc": d.get("created_utc", 0),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }

        created = datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc)
        posts.append({
            "post_id": f"RED_{d['id']}",
            "actor_id": f"RED_{author_fullname}" if author != "[deleted]" else "RED_deleted",
            "platform": "reddit",
            "timestamp": created.isoformat(),
            "title": d.get("title", ""),
            "content_text": d.get("selftext", d.get("title", "")),
            "likes": d.get("ups", 0) - d.get("downs", 0),
            "comments": d.get("num_comments", 0),
            "shares": d.get("num_crossposts", 0),
            "views": d.get("score", 0),
            "subreddit": subreddit,
            "permalink": d.get("permalink", ""),
        })

    return list(authors_seen.values()), posts


def fetch_subreddit_posts(
    subreddit: str,
    sort: str = "hot",
    limit: int = 100,
) -> tuple[list[dict], list[dict]]:
    client_id, client_secret, user_agent = _get_credentials()
    token = _get_auth_token(client_id, client_secret, user_agent)

    data = _api_get(
        f"/r/{subreddit}/{sort}",
        token, user_agent,
        params={"limit": min(limit, 100), "raw_json": 1},
    )

    actors, posts = _parse_listing(data, subreddit)
    print(f"[reddit] r/{subreddit}: {len(posts)} posts, {len(actors)} unique authors (OAuth)")
    return actors, posts


def fetch_subreddit_public(
    subreddit: str,
    sort: str = "hot",
    limit: int = 100,
) -> tuple[list[dict], list[dict]]:
    import requests

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 attention-observatory/0.1"
    headers = {"User-Agent": user_agent}

    urls = [
        f"https://old.reddit.com/r/{subreddit}/{sort}.json",
        f"https://www.reddit.com/r/{subreddit}/{sort}.json",
    ]

    data = None
    for url in urls:
        try:
            resp = requests.get(url, headers=headers, params={"limit": min(limit, 100), "raw_json": 1}, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                break
        except Exception:
            continue

    if data is None:
        raise ConnectionError(f"Could not fetch r/{subreddit} from any endpoint")

    actors, posts = _parse_listing(data, subreddit)
    print(f"[reddit] r/{subreddit}: {len(posts)} posts, {len(actors)} unique authors (public JSON)")
    return actors, posts


def ingest_subreddits(subreddits: list[str], posts_per_sub: int = 100):
    all_actors = []
    all_posts = []

    use_oauth = bool(os.environ.get("REDDIT_CLIENT_ID") and os.environ.get("REDDIT_CLIENT_SECRET"))

    for sub in subreddits:
        try:
            if use_oauth:
                actors, posts = fetch_subreddit_posts(sub, sort="hot", limit=posts_per_sub)
            else:
                actors, posts = fetch_subreddit_public(sub, sort="hot", limit=posts_per_sub)
            all_actors.extend(actors)
            all_posts.extend(posts)
        except Exception as e:
            print(f"[reddit] Error ingesting r/{sub}: {e}")

    actors_df = pl.DataFrame(all_actors) if all_actors else pl.DataFrame({
        "actor_id": [], "username": [], "platform": [], "followers": [],
        "account_created_utc": [], "ingested_at": [],
    })

    posts_df = pl.DataFrame(all_posts) if all_posts else pl.DataFrame({
        "post_id": [], "actor_id": [], "platform": [], "timestamp": [],
        "title": [], "content_text": [], "likes": [], "comments": [],
        "shares": [], "views": [], "subreddit": [], "permalink": [],
    })

    return actors_df, posts_df


def save_bronze(actors: pl.DataFrame, posts: pl.DataFrame, output_dir: str = "data/bronze"):
    import os
    os.makedirs(output_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    actors_path = f"{output_dir}/reddit_actors_{ts}.parquet"
    posts_path = f"{output_dir}/reddit_posts_{ts}.parquet"

    actors.write_parquet(actors_path)
    posts.write_parquet(posts_path)

    print(f"[reddit] Actors -> {actors_path} ({len(actors)} rows)")
    print(f"[reddit] Posts  -> {posts_path} ({len(posts)} rows)")
    return actors_path, posts_path


if __name__ == "__main__":
    actors, posts = ingest_subreddits(["MachineLearning", "datascience", "artificial"])
    if len(actors) > 0:
        save_bronze(actors, posts)
