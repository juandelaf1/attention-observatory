import numpy as np
import polars as pl
from datetime import datetime, timedelta

N_ACTORS = 500
N_POSTS = 5000
PLATFORMS = ["youtube", "reddit", "tiktok", "instagram"]
SEED = 42

rng = np.random.default_rng(SEED)

LUXURY_KEYWORDS = [
    "exclusive", "limited", "luxury", "haute", "couture", "gala", "premiere",
    "foundation", "institute", "academy", "award", "ceremony", "editorial",
    "curated", "boutique", "heritage", "legacy", "masterpiece"
]


def _powerlaw_sample(alpha, size, low=1e3, high=5e7):
    samples = (low ** (1 - alpha) + rng.uniform(size=size) * (high ** (1 - alpha) - low ** (1 - alpha))) ** (1 / (1 - alpha))
    return np.clip(samples, low, high)


def _assign_external_ecosystem(followers, platform):
    prob = 1 / (1 + np.exp(-0.8 * (np.log10(followers) - 5)))
    return rng.binomial(1, prob)


def _assign_legal_truncation(followers):
    prob = 0.3 / (1 + np.exp(0.5 * (np.log10(followers) - 4)))
    return bool(rng.binomial(1, prob))


def _prestige_drift_prob(followers):
    return 1 / (1 + np.exp(-0.6 * (np.log10(followers) - 5.5)))


def _generate_actor_catalog():
    actors = []
    for i in range(N_ACTORS):
        platform = PLATFORMS[i % len(PLATFORMS)]
        followers = _powerlaw_sample(2.3, 1)[0]
        has_ext = _assign_external_ecosystem(followers, platform)
        legally_truncated = _assign_legal_truncation(followers)
        prestige = bool(rng.binomial(1, _prestige_drift_prob(followers)))
        actors.append({
            "actor_id": f"ACT_{platform[:3]}_{i:04d}",
            "platform": platform,
            "followers": int(followers),
            "has_external_ecosystem": bool(has_ext),
            "is_legally_truncated": legally_truncated,
            "has_prestige_trajectory": prestige,
            "creation_date": datetime(2020, 1, 1) + timedelta(days=int(rng.integers(0, 1500))),
        })
    return pl.DataFrame(actors)


def _generate_posts(actor_catalog: pl.DataFrame) -> pl.DataFrame:
    all_posts = []
    for row in actor_catalog.iter_rows(named=True):
        aid = row["actor_id"]
        platform = row["platform"]
        followers = row["followers"]
        legally_truncated = row["is_legally_truncated"]
        has_prestige = row["has_prestige_trajectory"]
        n_posts = max(1, int(rng.poisson(max(1, np.log10(followers) * 2))))

        base_interval_hours = max(4, 168 / max(1, n_posts))
        if has_prestige:
            base_interval_hours *= 1.8
            base_interval_hours = min(base_interval_hours, 120)

        base_likes = followers * rng.lognormal(-4.5, 1.2)
        base_comments = base_likes * rng.lognormal(-1.8, 0.6)
        base_shares = base_likes * rng.lognormal(-2.0, 0.7)

        start_date = row["creation_date"] + timedelta(days=30)

        for j in range(n_posts):
            if legally_truncated and j > n_posts // 2:
                likes = comments = shares = views = 0
            else:
                noise = rng.lognormal(0, 0.5)
                likes = max(0, int(base_likes * noise))
                comments = max(0, int(base_comments * noise))
                shares = max(0, int(base_shares * noise))
                views = int(followers * rng.uniform(0.5, 3.0))

            post_date = start_date + timedelta(hours=j * base_interval_hours)

            n_luxury = rng.poisson(0.3 if has_prestige else 0.05)
            luxury_frac = min(1.0, n_luxury / 3.0) if n_luxury > 0 else 0.0

            sentiment_raw = rng.normal(0.1, 0.4)
            if has_prestige:
                sentiment_raw += 0.2
            sentiment = max(-1.0, min(1.0, sentiment_raw))

            all_posts.append({
                "post_id": f"POST_{aid}_{j:04d}",
                "actor_id": aid,
                "platform": platform,
                "timestamp": post_date,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "views": views,
                "followers_at_post": followers,
                "content_length": int(rng.integers(50, 2000)),
                "sentiment_score": round(sentiment, 4),
                "luxury_keyword_density": round(luxury_frac, 4),
                "is_legally_truncated_post": legally_truncated and j > n_posts // 2,
            })

    df = pl.DataFrame(all_posts)
    return df.sort("timestamp")


def generate_bronze(output_dir: str = "data/bronze"):
    import os
    os.makedirs(output_dir, exist_ok=True)

    actors = _generate_actor_catalog()
    posts = _generate_posts(actors)

    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    actors_path = f"{output_dir}/dim_actores_{date_str}.parquet"
    posts_path = f"{output_dir}/fact_posts_{date_str}.parquet"

    actors.write_parquet(actors_path)
    posts.write_parquet(posts_path)

    print(f"[simulator] Bronze actors -> {actors_path} ({len(actors)} rows)")
    print(f"[simulator] Bronze posts  -> {posts_path} ({len(posts)} rows)")
    return actors_path, posts_path


if __name__ == "__main__":
    generate_bronze()
