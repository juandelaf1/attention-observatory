import polars as pl
from datetime import datetime, timezone
import os
import requests

TELEGRAM_API = "https://api.telegram.org/bot"


def _get_bot_token() -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN must be set.\n"
            "Create a bot at https://t.me/BotFather and get the token."
        )
    return token


def get_chat_messages(chat_id: str, limit: int = 100) -> list[dict]:
    token = _get_bot_token()
    resp = requests.post(
        f"{TELEGRAM_API}{token}/getUpdates",
        json={"offset": -1, "limit": 1},
        timeout=15,
    )
    if resp.status_code != 200:
        return []

    # We need a different approach: search public channels
    # Telegram bot API doesn't support history access without being admin
    # Use: forward messages from public channels
    return []


def get_chat_info(chat_id: str) -> dict | None:
    token = _get_bot_token()
    try:
        resp = requests.get(
            f"{TELEGRAM_API}{token}/getChat",
            params={"chat_id": chat_id},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("result", {})
    except Exception:
        pass
    return None


def send_test_message(chat_id: str, text: str = "test") -> bool:
    token = _get_bot_token()
    try:
        resp = requests.post(
            f"{TELEGRAM_API}{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False


def ingest_telegram(
    channels: list[str] | None = None,
    max_messages: int = 100,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    channels = channels or [
        "@techcrunch", "@BBCNews", "@nytimes",
        "@NatureNews", "@ScienceNews",
    ]
    print(f"[telegram] Fetching from {len(channels)} channels...")

    authors_seen: dict[str, dict] = {}
    posts = []

    token = _get_bot_token()

    for channel in channels:
        try:
            info = get_chat_info(channel)
            if not info:
                print(f"[telegram] Cannot access {channel}")
                continue
            title = info.get("title", channel)
            username = info.get("username", channel.lstrip("@"))

            author_id = f"TG_{username}"
            if username not in authors_seen:
                authors_seen[username] = {
                    "actor_id": author_id,
                    "username": username,
                    "display_name": title,
                    "platform": "telegram",
                    "type": "channel",
                    "followers": 0,
                    "description": (info.get("description") or "")[:300],
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                }

            # Bot API only allows fetching messages the bot has seen
            # For public channels, the bot must be added as admin
            # Alternative: use getChat + getChatAdministrators
            print(f"[telegram] {channel}: info fetched (message history requires bot in channel)")

        except Exception as e:
            print(f"[telegram] {channel}: {e}")
            continue

    actors = list(authors_seen.values())
    print(f"[telegram] Total: {len(posts)} posts from {len(actors)} channels")
    return pl.DataFrame(actors), pl.DataFrame(posts)


def ingest_telegram_messages(
    channel_usernames: list[str],
    bot_token: str,
    max_messages_per_channel: int = 50,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    authors_seen: dict[str, dict] = {}
    posts = []

    for username in channel_usernames:
        chat_id = f"@{username.lstrip('@')}"
        try:
            resp = requests.get(
                f"{TELEGRAM_API}{bot_token}/getUpdates",
                params={"timeout": 5, "limit": min(max_messages_per_channel, 100)},
                timeout=15,
            )
            if resp.status_code != 200:
                print(f"[telegram] getUpdates failed for {chat_id}")
                continue

            updates = resp.json().get("result", [])
            for upd in updates:
                msg = upd.get("message") or upd.get("channel_post") or {}
                chat = msg.get("chat", {})
                if str(chat.get("id", "")).lstrip("-") != chat_id.lstrip("@"):
                    continue

                sender = msg.get("from", {})
                sender_name = sender.get("username") or sender.get("first_name", "unknown")
                sender_id = sender.get("id", hash(sender_name))
                aid = f"TG_{sender_id}"

                if sender_name not in authors_seen:
                    authors_seen[sender_name] = {
                        "actor_id": aid,
                        "username": str(sender_name),
                        "platform": "telegram",
                        "type": "user",
                        "followers": 0,
                        "ingested_at": datetime.now(timezone.utc).isoformat(),
                    }

                created = datetime.fromtimestamp(msg.get("date", 0), tz=timezone.utc)
                text = (msg.get("text") or msg.get("caption") or "")[:2000]

                posts.append({
                    "post_id": f"TG_{msg.get('message_id', hash(text))}",
                    "actor_id": aid,
                    "platform": "telegram",
                    "timestamp": created.isoformat(),
                    "title": text.split("\n")[0][:200],
                    "content_text": text,
                    "likes": 0,
                    "comments": 0,
                    "shares": 0,
                    "views": 0,
                    "followers_at_post": 1,
                    "sentiment_score": 0.0,
                    "luxury_keyword_density": 0.0,
                    "is_legally_truncated_post": False,
                    "channel": chat_id,
                })

        except Exception as e:
            print(f"[telegram] Error with {chat_id}: {e}")
            continue

    actors = list(authors_seen.values())
    print(f"[telegram] Total: {len(posts)} posts from {len(actors)} actors")
    return pl.DataFrame(actors), pl.DataFrame(posts)


def save_bronze(actors: pl.DataFrame, posts: pl.DataFrame, output_dir: str = "data/bronze"):
    import os
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    actors_path = f"{output_dir}/telegram_actors_{ts}.parquet"
    posts_path = f"{output_dir}/telegram_posts_{ts}.parquet"
    actors.write_parquet(actors_path)
    posts.write_parquet(posts_path)
    print(f"[telegram] Actors -> {actors_path} ({len(actors)} rows)")
    print(f"[telegram] Posts  -> {posts_path} ({len(posts)} rows)")
    return actors_path, posts_path


if __name__ == "__main__":
    actors, posts = ingest_telegram(max_messages=50)
    if len(actors) > 0:
        save_bronze(actors, posts)
