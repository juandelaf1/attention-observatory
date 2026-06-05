import polars as pl
from datetime import datetime, timezone
from typing import Optional


SOCIAL_DATASETS = {
    "go_emotions": {
        "path": "SetFit/go_emotions",
        "text_col": "text",
        "score_col": None,
        "user_col": None,
    },
    "reddit_philosophy": {
        "path": "philosophy_reddit",
        "text_col": "body",
        "score_col": "score",
        "user_col": "author",
    },
    "social_i_qa": {
        "path": "social_i_qa",
        "text_col": "context",
        "score_col": None,
        "user_col": None,
    },
    "dair_ai_emotion": {
        "path": "dair-ai/emotion",
        "text_col": "text",
        "score_col": None,
        "user_col": None,
    },
    "tweets_hate_speech": {
        "path": "tweets_hate_speech_detection",
        "text_col": "tweet",
        "score_col": None,
        "user_col": None,
    },
    "youtube_comments": {
        "path": "jefriyoga/youtube-comments-sentiment-analysis",
        "text_col": "comment",
        "score_col": None,
        "user_col": "author",
    },
}


def _try_import_datasets():
    try:
        import datasets
        return datasets
    except ImportError:
        try:
            import subprocess
            import sys
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "datasets", "-q"]
            )
            import datasets
            return datasets
        except Exception:
            raise ImportError(
                "datasets library not available. Install: pip install datasets"
            )


def discover_available_datasets(keywords: list[str] | None = None) -> list[dict]:
    ds = _try_import_datasets()
    kw = keywords or ["reddit", "twitter", "social", "youtube", "instagram", "tiktok"]
    results = []
    for k in kw:
        try:
            hits = ds.get_dataset_config_names(k) if k in ["reddit"] else []
            results.append({"keyword": k, "datasets": hits[:5] if hits else []})
        except Exception:
            pass
    return results


def load_huggingface_dataset(
    dataset_name: str,
    split: str = "train",
    max_rows: int = 10000,
    text_column: str | None = None,
    score_column: str | None = None,
    user_column: str | None = None,
    platform: str = "huggingface",
) -> tuple[pl.DataFrame, pl.DataFrame]:
    ds = _try_import_datasets()

    print(f"[huggingface] Loading {dataset_name} ({split}, max {max_rows} rows)...")
    data = ds.load_dataset(dataset_name, split=split, streaming=True)
    rows = []
    for i, row in enumerate(data):
        if i >= max_rows:
            break
        rows.append(row)

    if not rows:
        print(f"[huggingface] No data loaded from {dataset_name}")
        return pl.DataFrame(), pl.DataFrame()

    pdf = pl.DataFrame(rows)

    text_col = text_column or "text" if "text" in pdf.columns else (
        pdf.columns[0] if len(pdf.columns) > 0 else "content"
    )
    score_col = score_column or "score" if "score" in pdf.columns else None
    user_col = user_column or "author" if "author" in pdf.columns else None

    authors: dict[str, dict] = {}
    posts = []

    for i in range(len(pdf)):
        row = pdf.row(i, named=True)

        user_val = str(row.get(user_col, f"user_{i}")) if user_col else f"user_{i}"
        aid = f"HF_{user_val}"

        if user_val not in authors:
            authors[user_val] = {
                "actor_id": aid,
                "username": user_val,
                "platform": platform,
                "followers": 0,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }

        text_val = str(row.get(text_col, ""))
        score_val = row.get(score_col, 0) if score_col else 0
        if score_val is None:
            score_val = 0

        posts.append({
            "post_id": f"HF_{dataset_name[:10]}_{i:06d}",
            "actor_id": aid,
            "platform": platform,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "title": f"{dataset_name} post {i}",
            "content_text": text_val[:2000],
            "likes": int(score_val) if score_val else 0,
            "comments": 0,
            "shares": 0,
            "views": int(score_val) * 10 if score_val else 0,
            "followers_at_post": 1,
            "sentiment_score": 0.0,
            "luxury_keyword_density": 0.0,
            "is_legally_truncated_post": False,
        })

    actors_df = pl.DataFrame(list(authors.values())) if authors else pl.DataFrame({
        "actor_id": [], "username": [], "platform": [], "followers": [], "ingested_at": [],
    })
    posts_df = pl.DataFrame(posts) if posts else pl.DataFrame({
        "post_id": [], "actor_id": [], "platform": [], "timestamp": [], "title": [],
        "content_text": [], "likes": [], "comments": [], "shares": [], "views": [],
        "followers_at_post": [], "sentiment_score": [], "luxury_keyword_density": [],
        "is_legally_truncated_post": [],
    })

    print(f"[huggingface] {len(actors_df)} actors, {len(posts_df)} posts from {dataset_name}")
    return actors_df, posts_df


def ingest_multiple_datasets(
    dataset_configs: list[dict],
    max_per_dataset: int = 5000,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    all_actors = []
    all_posts = []

    for cfg in dataset_configs:
        try:
            actors, posts = load_huggingface_dataset(
                cfg["name"],
                split=cfg.get("split", "train"),
                max_rows=cfg.get("max_rows", max_per_dataset),
                text_column=cfg.get("text_col"),
                score_column=cfg.get("score_col"),
                user_column=cfg.get("user_col"),
                platform=cfg.get("platform", "huggingface"),
            )
            if len(actors) > 0:
                all_actors.append(actors)
                all_posts.append(posts)
        except Exception as e:
            print(f"[huggingface] Failed to load {cfg.get('name')}: {e}")

    merged_actors = pl.concat(all_actors, how="diagonal") if all_actors else pl.DataFrame()
    merged_posts = pl.concat(all_posts, how="diagonal") if all_posts else pl.DataFrame()

    if len(merged_actors) > 0:
        merged_actors = merged_actors.unique(subset=["actor_id"])

    print(f"[huggingface] Total: {len(merged_actors)} actors, {len(merged_posts)} posts")
    return merged_actors, merged_posts


def save_bronze(actors: pl.DataFrame, posts: pl.DataFrame, output_dir: str = "data/bronze"):
    import os
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    actors_path = f"{output_dir}/hf_actors_{ts}.parquet"
    posts_path = f"{output_dir}/hf_posts_{ts}.parquet"
    actors.write_parquet(actors_path)
    posts.write_parquet(posts_path)
    print(f"[huggingface] Actors -> {actors_path} ({len(actors)} rows)")
    print(f"[huggingface] Posts  -> {posts_path} ({len(posts)} rows)")
    return actors_path, posts_path


if __name__ == "__main__":
    cfg = [
        {"name": "go_emotions", "split": "train", "max_rows": 3000, "text_col": "text", "platform": "huggingface"},
    ]
    actors, posts = ingest_multiple_datasets(cfg)
    if len(actors) > 0:
        save_bronze(actors, posts)
