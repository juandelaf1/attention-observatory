import polars as pl
from datetime import datetime, timezone
import os
import requests

GITHUB_API = "https://api.github.com"


def _headers():
    token = os.environ.get("GITHUB_TOKEN", "")
    h = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "attention-observatory/0.1",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def search_repos(query: str, sort: str = "stars", per_page: int = 30) -> list[dict]:
    resp = requests.get(
        f"{GITHUB_API}/search/repositories",
        params={"q": query, "sort": sort, "order": "desc", "per_page": min(per_page, 100)},
        headers=_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("items", [])


def fetch_commits(owner: str, repo: str, per_page: int = 30) -> list[dict]:
    resp = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/commits",
        params={"per_page": min(per_page, 100)},
        headers=_headers(),
        timeout=30,
    )
    if resp.status_code != 200:
        return []
    return resp.json()


def fetch_issues(owner: str, repo: str, per_page: int = 30) -> list[dict]:
    resp = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/issues",
        params={"per_page": min(per_page, 100), "state": "all"},
        headers=_headers(),
        timeout=30,
    )
    if resp.status_code != 200:
        return []
    return resp.json()


def ingest_github(
    queries: list[str] | None = None,
    repos_per_query: int = 5,
    commits_per_repo: int = 20,
    issues_per_repo: int = 10,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    queries = queries or [
        "stars:>10000",
        "topic:machine-learning",
        "topic:blockchain",
        "topic:data-science",
        "topic:artificial-intelligence",
    ]
    print(f"[github] Searching {len(queries)} queries...")

    authors_seen: dict[str, dict] = {}
    posts = []

    for q in queries:
        try:
            repos = search_repos(q, per_page=repos_per_query)
        except Exception as e:
            print(f"[github] Query '{q}' failed: {e}")
            continue

        for repo in repos:
            owner = repo["owner"]["login"]
            repo_name = repo["name"]
            full_name = repo["full_name"]

            try:
                commits = fetch_commits(owner, repo_name, per_page=commits_per_repo)
            except Exception as e:
                print(f"[github] Commits for {full_name}: {e}")
                commits = []

            for c in commits:
                author_data = c.get("commit", {}).get("author", {})
                committer_data = c.get("commit", {}).get("committer", {})
                gh_user = c.get("author") or c.get("committer") or {}
                username = gh_user.get("login") if gh_user else None
                if not username:
                    username = author_data.get("name", "unknown").replace(" ", "_")
                gh_id = gh_user.get("id", hash(username))

                aid = f"GH_{gh_id}"
                if username not in authors_seen:
                    authors_seen[username] = {
                        "actor_id": aid,
                        "username": username,
                        "platform": "github",
                        "followers": gh_user.get("followers_url") and 0 or 0,
                        "repo_count": 0,
                        "type": "developer",
                        "ingested_at": datetime.now(timezone.utc).isoformat(),
                    }

                created = committer_data.get("date") or author_data.get("date") or datetime.now(timezone.utc).isoformat()
                msg = (c.get("commit", {}).get("message", "") or "")[:2000]

                posts.append({
                    "post_id": f"GH_commit_{c.get('sha', '')[:12]}",
                    "actor_id": aid,
                    "platform": "github",
                    "timestamp": created,
                    "title": msg.split("\n")[0][:200],
                    "content_text": msg,
                    "likes": 0,
                    "comments": 0,
                    "shares": 0,
                    "views": 0,
                    "followers_at_post": 1,
                    "sentiment_score": 0.0,
                    "luxury_keyword_density": 0.0,
                    "is_legally_truncated_post": False,
                    "repo": full_name,
                    "content_type": "commit",
                })

            try:
                issues = fetch_issues(owner, repo_name, per_page=issues_per_repo)
            except Exception as e:
                print(f"[github] Issues for {full_name}: {e}")
                issues = []

            for iss in issues:
                if "pull_request" in iss:
                    continue
                user = iss.get("user", {})
                username = user.get("login", f"user_{user.get('id', 0)}")
                gh_id = user.get("id", hash(username))

                aid = f"GH_{gh_id}"
                if username not in authors_seen:
                    authors_seen[username] = {
                        "actor_id": aid,
                        "username": username,
                        "platform": "github",
                        "followers": user.get("followers_url") and 0 or 0,
                        "repo_count": 0,
                        "type": "developer",
                        "ingested_at": datetime.now(timezone.utc).isoformat(),
                    }

                created = iss.get("created_at", datetime.now(timezone.utc).isoformat())
                body = (iss.get("body", "") or "")[:2000]

                posts.append({
                    "post_id": f"GH_issue_{iss.get('id', 0)}",
                    "actor_id": aid,
                    "platform": "github",
                    "timestamp": created,
                    "title": iss.get("title", ""),
                    "content_text": body,
                    "likes": iss.get("reactions", {}).get("+1", 0) if iss.get("reactions") else 0,
                    "comments": iss.get("comments", 0),
                    "shares": 0,
                    "views": 0,
                    "followers_at_post": 1,
                    "sentiment_score": 0.0,
                    "luxury_keyword_density": 0.0,
                    "is_legally_truncated_post": False,
                    "repo": full_name,
                    "content_type": "issue",
                })

        print(f"[github] Query '{q}': {len(repos)} repos")

    actors = list(authors_seen.values())
    print(f"[github] Total: {len(posts)} posts from {len(actors)} actors")
    return pl.DataFrame(actors), pl.DataFrame(posts)


def save_bronze(actors: pl.DataFrame, posts: pl.DataFrame, output_dir: str = "data/bronze"):
    import os
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    actors_path = f"{output_dir}/github_actors_{ts}.parquet"
    posts_path = f"{output_dir}/github_posts_{ts}.parquet"
    actors.write_parquet(actors_path)
    posts.write_parquet(posts_path)
    print(f"[github] Actors -> {actors_path} ({len(actors)} rows)")
    print(f"[github] Posts  -> {posts_path} ({len(posts)} rows)")
    return actors_path, posts_path


if __name__ == "__main__":
    actors, posts = ingest_github(repos_per_query=3, commits_per_repo=10, issues_per_repo=5)
    if len(actors) > 0:
        save_bronze(actors, posts)
