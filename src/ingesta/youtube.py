import os
import time
import polars as pl
from datetime import datetime, timezone
from typing import Optional


def _get_api_key() -> str:
    key = os.environ.get("YOUTUBE_API_KEY", "")
    if not key:
        raise ValueError(
            "YOUTUBE_API_KEY not set. Get one at https://console.cloud.google.com/apis/credentials\n"
            "Then:  $env:YOUTUBE_API_KEY = 'your_key_here'"
        )
    return key


def _build_headers(api_key: str) -> dict:
    return {"Referer": "https://localhost"}  # some endpoints require referer


def search_channels(query: str, max_results: int = 25) -> list[dict]:
    import requests

    api_key = _get_api_key()
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "channel",
        "maxResults": min(max_results, 50),
        "key": api_key,
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    channels = []
    for item in data.get("items", []):
        channels.append({
            "channel_id": item["snippet"]["channelId"],
            "channel_title": item["snippet"]["title"],
            "description": item["snippet"].get("description", ""),
            "published_at": item["snippet"]["publishTime"],
            "platform": "youtube",
        })
    return channels


def get_channel_stats(channel_ids: list[str]) -> list[dict]:
    import requests

    api_key = _get_api_key()
    stats = []

    for cid in channel_ids:
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            "part": "statistics,snippet",
            "id": cid,
            "key": api_key,
        }
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items", []):
                s = item["statistics"]
                stats.append({
                    "actor_id": f"YT_{cid}",
                    "channel_id": cid,
                    "channel_title": item["snippet"]["title"],
                    "platform": "youtube",
                    "followers": int(s.get("subscriberCount", 0)),
                    "total_views": int(s.get("viewCount", 0)),
                    "total_videos": int(s.get("videoCount", 0)),
                    "country": item["snippet"].get("country", ""),
                    "published_at": item["snippet"]["publishedAt"],
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                })
            time.sleep(0.1)
        except Exception as e:
            print(f"[youtube] Error fetching channel {cid}: {e}")
    return stats


def get_recent_videos(channel_id: str, max_results: int = 50) -> list[dict]:
    import requests

    api_key = _get_api_key()
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "order": "date",
        "type": "video",
        "maxResults": min(max_results, 50),
        "key": api_key,
    }

    videos = []
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("items", []):
            videos.append({
                "post_id": f"YT_{item['id']['videoId']}",
                "actor_id": f"YT_{channel_id}",
                "platform": "youtube",
                "timestamp": item["snippet"]["publishTime"],
                "title": item["snippet"]["title"],
                "description": item["snippet"].get("description", ""),
                "content_text": item["snippet"]["title"] + " " + item["snippet"].get("description", ""),
            })
    except Exception as e:
        print(f"[youtube] Error fetching videos for {channel_id}: {e}")
    return videos


def get_video_stats(video_ids: list[str]) -> list[dict]:
    import requests

    api_key = _get_api_key()
    stats = []

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "statistics",
            "id": ",".join(batch),
            "key": api_key,
        }
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items", []):
                s = item["statistics"]
                stats.append({
                    "post_id": f"YT_{item['id']}",
                    "likes": int(s.get("likeCount", 0)),
                    "comments": int(s.get("commentCount", 0)),
                    "views": int(s.get("viewCount", 0)),
                })
            time.sleep(0.5)
        except Exception as e:
            print(f"[youtube] Error fetching video stats batch: {e}")
    return stats


def ingest_channel_feed(channel_query: str, max_channels: int = 10, max_videos_per_channel: int = 25):
    print(f"[youtube] Searching channels for '{channel_query}'...")
    channels = search_channels(channel_query, max_results=max_channels)
    print(f"[youtube] Found {len(channels)} channels")

    channel_ids = [c["channel_id"] for c in channels]
    channel_stats = get_channel_stats(channel_ids)

    all_videos_meta = []
    for cid in channel_ids:
        vids = get_recent_videos(cid, max_results=max_videos_per_channel)
        all_videos_meta.extend(vids)

    video_ids = [v["post_id"].replace("YT_", "") for v in all_videos_meta]
    video_stats = get_video_stats(video_ids)

    stats_map = {vs["post_id"]: vs for vs in video_stats}
    for v in all_videos_meta:
        if v["post_id"] in stats_map:
            v.update(stats_map[v["post_id"]])
        else:
            v.update({"likes": 0, "comments": 0, "views": 0})

    actors_df = pl.DataFrame(channel_stats)
    posts_df = pl.DataFrame(all_videos_meta)

    return actors_df, posts_df


def save_bronze(actors: pl.DataFrame, posts: pl.DataFrame, output_dir: str = "data/bronze"):
    import os
    os.makedirs(output_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    actors_path = f"{output_dir}/youtube_actors_{ts}.parquet"
    posts_path = f"{output_dir}/youtube_posts_{ts}.parquet"

    actors.write_parquet(actors_path)
    posts.write_parquet(posts_path)

    print(f"[youtube] Actors -> {actors_path} ({len(actors)} rows)")
    print(f"[youtube] Posts  -> {posts_path} ({len(posts)} rows)")
    return actors_path, posts_path


if __name__ == "__main__":
    actors, posts = ingest_channel_feed("data science", max_channels=5)
    if len(actors) > 0:
        save_bronze(actors, posts)
