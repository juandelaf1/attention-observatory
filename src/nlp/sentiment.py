import polars as pl
import numpy as np


class BatchSentimentAnalyzer:
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        from transformers import pipeline
        self._pipe = pipeline(
            "sentiment-analysis",
            model=model_name,
            truncation=True,
            max_length=512,
            batch_size=32,
        )

    def score(self, texts: list[str]) -> list[float]:
        results = self._pipe(texts)
        scores = []
        for r in results:
            label = r["label"]
            score = r["score"]
            if label == "NEGATIVE":
                scores.append(-score)
            elif label == "POSITIVE":
                scores.append(score)
            else:
                scores.append(0.0)
        return scores


def _fallback_sentiment(texts: list[str]) -> list[float]:
    rng = np.random.default_rng(42)
    return list(rng.normal(0.0, 0.3, size=len(texts)).clip(-1.0, 1.0))


def enrich_posts_with_sentiment(posts_path: str, output_path: str | None = None) -> str:
    df = pl.read_parquet(posts_path)

    if "content_text" not in df.columns:
        print("[nlp] No content_text column; using simulated sentiment from bronze layer")
        if output_path:
            df.write_parquet(output_path)
        return posts_path

    texts = df["content_text"].to_list()

    try:
        analyzer = BatchSentimentAnalyzer()
        scores = analyzer.score(texts)
        print(f"[nlp] Transformers sentiment scored {len(scores)} texts")
    except (ImportError, Exception) as e:
        print(f"[nlp] Transformers unavailable ({e}); falling back to simulated scores")
        scores = _fallback_sentiment(texts)

    df = df.with_columns(pl.Series("sentiment_score", scores).cast(pl.Float64))

    if output_path is None:
        output_path = posts_path

    df.write_parquet(output_path)
    print(f"[nlp] Enriched posts with sentiment -> {output_path}")
    return output_path


if __name__ == "__main__":
    enrich_posts_with_sentiment("data/bronze/fact_posts.parquet")
