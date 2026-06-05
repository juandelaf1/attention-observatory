import polars as pl
from datetime import datetime, timezone
from typing import Optional
import re


WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_REST = "https://en.wikipedia.org/api/rest_v1"


USER_AGENT = "AttentionObservatory/1.0 (research project; contact: juandelafuenterrocca@gmail.com)"


def _wiki_request(params: dict) -> dict:
    import requests
    params["format"] = "json"
    params["origin"] = "*"
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(WIKI_API, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def search_articles(query: str, limit: int = 50) -> list[dict]:
    data = _wiki_request({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": min(limit, 50),
    })
    articles = []
    for result in data.get("query", {}).get("search", []):
        articles.append({
            "page_id": result["pageid"],
            "title": result["title"],
            "snippet": result.get("snippet", ""),
        })
    return articles


def get_page_views(title: str, days: int = 30) -> int:
    import requests
    from datetime import timedelta
    headers = {"User-Agent": USER_AGENT}

    end = datetime.now()
    start = end - timedelta(days=days)
    url = f"{WIKI_REST}/page/summary/{title.replace(' ', '_')}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("views", data.get("pageview_count", 0))
    except Exception:
        return 0


def get_page_history(title: str, limit: int = 50) -> list[dict]:
    data = _wiki_request({
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvlimit": min(limit, 50),
        "rvprop": "ids|timestamp|user|size|comment",
    })
    pages = data.get("query", {}).get("pages", {})
    revisions = []
    for pid, page in pages.items():
        for rev in page.get("revisions", []):
            revisions.append({
                "rev_id": rev["revid"],
                "user": rev.get("user", "[deleted]"),
                "timestamp": rev["timestamp"],
                "size_change": rev.get("size", 0),
                "comment": rev.get("comment", ""),
            })
    return revisions


def ingest_wikipedia_articles(
    queries: list[str],
    articles_per_query: int = 10,
    max_revisions: int = 20,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    from collections import defaultdict

    all_titles = set()
    for q in queries:
        results = search_articles(q, limit=articles_per_query)
        for r in results:
            all_titles.add((r["page_id"], r["title"]))

    print(f"[wikipedia] Found {len(all_titles)} unique articles")

    authors: dict[str, dict] = {}
    posts = []
    author_edit_count = defaultdict(int)

    for pid, title in all_titles:
        revisions = get_page_history(title, limit=max_revisions)
        views = get_page_views(title, days=30)

        for rev in revisions:
            user = rev["user"]
            author_key = f"WP_{user}"
            authors[author_key] = {
                "actor_id": author_key,
                "username": user,
                "platform": "wikipedia",
                "followers": 0,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
            author_edit_count[author_key] += 1

            created = datetime.fromisoformat(rev["timestamp"].replace("Z", "+00:00"))
            posts.append({
                "post_id": f"WP_{rev['rev_id']}",
                "actor_id": author_key,
                "platform": "wikipedia",
                "timestamp": created.isoformat(),
                "title": f"Edit: {title}",
                "content_text": f"Edited {title}: {rev['comment'][:200]}" if rev['comment'] else f"Edited {title}",
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "views": views // max(1, len(revisions)),
                "followers_at_post": 1,
                "sentiment_score": 0.0,
                "luxury_keyword_density": 0.0,
                "is_legally_truncated_post": False,
            })

    for ak in authors:
        authors[ak]["followers"] = author_edit_count.get(ak, 0)

    actors_df = pl.DataFrame(list(authors.values())) if authors else pl.DataFrame({
        "actor_id": [], "username": [], "platform": [], "followers": [], "ingested_at": [],
    })
    posts_df = pl.DataFrame(posts) if posts else pl.DataFrame({
        "post_id": [], "actor_id": [], "platform": [], "timestamp": [], "title": [],
        "content_text": [], "likes": [], "comments": [], "shares": [], "views": [],
        "followers_at_post": [], "sentiment_score": [], "luxury_keyword_density": [],
        "is_legally_truncated_post": [],
    })

    print(f"[wikipedia] {len(actors_df)} editors, {len(posts_df)} revisions")
    return actors_df, posts_df


def save_bronze(actors: pl.DataFrame, posts: pl.DataFrame, output_dir: str = "data/bronze"):
    import os
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    actors_path = f"{output_dir}/wiki_actors_{ts}.parquet"
    posts_path = f"{output_dir}/wiki_posts_{ts}.parquet"
    actors.write_parquet(actors_path)
    posts.write_parquet(posts_path)
    print(f"[wikipedia] Actors -> {actors_path} ({len(actors)} rows)")
    print(f"[wikipedia] Posts  -> {posts_path} ({len(posts)} rows)")
    return actors_path, posts_path


if __name__ == "__main__":
    actors, posts = ingest_wikipedia_articles(
        ["Artificial intelligence", "Machine learning", "Data science", "Social media", "Attention economy"],
        articles_per_query=5, max_revisions=15
    )
    if len(actors) > 0:
        save_bronze(actors, posts)
