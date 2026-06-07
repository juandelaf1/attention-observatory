import polars as pl
import numpy as np
import json
import os
from scipy import stats

REPORTS_DIR = "data/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

FEATURES = ["er_mean", "ppi_mean", "sentiment_avg", "afi_mean"]
PLATFORM = "platform"


def load(path: str) -> pl.DataFrame:
    return pl.read_parquet(path)


def without_hf(df: pl.DataFrame) -> pl.DataFrame:
    return df.filter(~pl.col("is_huggingface"))


def _gini(arr: np.ndarray) -> float:
    arr = np.sort(arr)
    n = len(arr)
    if n == 0 or arr.sum() == 0:
        return 0.0
    return float((2 * np.sum((np.arange(1, n + 1)) * arr) / (n * arr.sum()) - (n + 1) / n))


# ─── P1: Power Law por plataforma ─────────────────────────────────


def p1_power_law_by_platform(df: pl.DataFrame) -> dict:
    platforms = df[PLATFORM].unique().to_list()
    results = {}
    for p in platforms:
        sub = df.filter(pl.col(PLATFORM) == p)
        er = sub["er_mean"].drop_nulls().to_numpy()
        er = er[er > 0]
        if len(er) < 5:
            results[p] = {"n": len(sub), "n_with_er": len(er), "alpha": None}
            continue
        try:
            import powerlaw
            fit = powerlaw.Fit(er, verbose=False)
            results[p] = {
                "n": len(sub),
                "n_with_er": len(er),
                "alpha": round(fit.power_law.alpha, 4),
                "sigma": round(fit.power_law.sigma, 4),
                "pareto": bool(fit.power_law.alpha > 2.0),
            }
        except Exception:
            results[p] = {"n": len(sub), "n_with_er": len(er), "alpha": "error"}
    return results


# ─── P2: Sentiment vs Engagement ─────────────────────────────────


def p2_sentiment_engagement_corr(df: pl.DataFrame) -> dict:
    sub = without_hf(df)
    er = sub["er_mean"].to_numpy()
    sent = sub["sentiment_avg"].to_numpy()
    mask = ~(np.isnan(er) | np.isnan(sent))
    r_pearson, p_pearson = stats.pearsonr(er[mask], sent[mask])
    r_spear, p_spear = stats.spearmanr(er[mask], sent[mask])
    return {
        "n": int(mask.sum()),
        "pearson_r": round(r_pearson, 4),
        "pearson_p": float(p_pearson),
        "spearman_rho": round(r_spear, 4),
        "spearman_p": float(p_spear),
    }


# ─── P3: High-Leverage Nodes ─────────────────────────────────


def _cooks(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    n = len(x)
    if n < 3:
        return np.zeros(n)
    try:
        X = np.column_stack([np.ones(n), x])
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        y_pred = X @ beta
        res = y - y_pred
        mse = np.sum(res ** 2) / max(1, n - 2)
        lev = np.diag(X @ np.linalg.inv(X.T @ X) @ X.T)
        d = (res ** 2 / (2 * mse + 1e-10)) * (lev / ((1 - lev) ** 2 + 1e-10))
        return np.nan_to_num(d, nan=0.0, posinf=0.0, neginf=0.0)
    except np.linalg.LinAlgError:
        return np.zeros(n)


def p3_high_leverage(df: pl.DataFrame) -> dict:
    sub = without_hf(df)
    ppi = sub["ppi_mean"].to_numpy()
    er = sub["er_mean"].to_numpy()
    cooks = _cooks(ppi, er)
    threshold = 4.0 / max(1, len(cooks))
    leverage_mask = cooks > threshold
    high = sub.filter(pl.Series("_cooks", cooks) > threshold).select([
        "actor_id", "username", "platform", "er_mean", "ppi_mean"
    ]).sort("er_mean", descending=True)
    return {
        "n_total": len(sub),
        "threshold": round(threshold, 6),
        "n_high_leverage": int(leverage_mask.sum()),
        "top_nodes": [
            {"actor_id": r["actor_id"], "username": r["username"],
             "platform": r["platform"], "er": round(r["er_mean"], 4), "ppi": round(r["ppi_mean"], 4)}
            for r in high.head(10).iter_rows(named=True)
        ],
    }


# ─── P4: AFI vs PPI ─────────────────────────────────


def p4_afi_ppi_corr(df: pl.DataFrame) -> dict:
    sub = without_hf(df)
    afi = sub["afi_mean"].to_numpy()
    ppi = sub["ppi_mean"].to_numpy()
    mask = ~(np.isnan(afi) | np.isnan(ppi))
    r_s, p_s = stats.spearmanr(afi[mask], ppi[mask])
    return {
        "n": int(mask.sum()),
        "spearman_rho": round(r_s, 4),
        "spearman_p": float(p_s),
    }


# ─── P5: Gini por plataforma + Bootstrap ─────────────────────────────────


def _bootstrap_gini(arr: np.ndarray, n_iter: int = 1000) -> dict:
    ginis = []
    for _ in range(n_iter):
        sample = np.random.choice(arr, size=len(arr), replace=True)
        ginis.append(_gini(sample))
    ginis = np.array(ginis)
    return {
        "mean": round(float(np.mean(ginis)), 4),
        "std": round(float(np.std(ginis)), 4),
        "ci_95": [round(float(np.percentile(ginis, 2.5)), 4),
                   round(float(np.percentile(ginis, 97.5)), 4)],
    }


def p5_gini_by_platform(df: pl.DataFrame) -> dict:
    platforms = df[PLATFORM].unique().to_list()
    results = {}
    for p in platforms:
        sub = df.filter(pl.col(PLATFORM) == p)
        er = sub["er_mean"].drop_nulls().to_numpy()
        if len(er) < 3:
            results[p] = {"n": len(sub), "gini": None}
            continue
        g = _gini(er)
        boot = _bootstrap_gini(er, 500) if len(er) >= 10 else None
        results[p] = {
            "n": len(sub),
            "gini": round(g, 4),
            "bootstrap": boot,
        }
    return results


# ─── P6: Perfil de Super-Hubs ─────────────────────────────────


def p6_super_hub_profiles(df: pl.DataFrame) -> dict:
    sub = without_hf(df)
    er = sub["er_mean"].to_numpy()
    mean = np.nanmean(er)
    std = np.nanstd(er)
    threshold = mean + 3 * std
    hubs = sub.filter(pl.col("er_mean") > threshold).select([
        "actor_id", "username", "platform", "er_mean", "ppi_mean",
        "sentiment_avg", "afi_mean", "total_interactions", "post_count",
    ]).sort("er_mean", descending=True)

    return {
        "z_threshold": round(threshold, 4),
        "n_hubs": len(hubs),
        "mean_vector": {
            "er": round(float(hubs["er_mean"].mean()), 4),
            "ppi": round(float(hubs["ppi_mean"].mean()), 4),
            "sentiment": round(float(hubs["sentiment_avg"].mean()), 4),
            "afi": round(float(hubs["afi_mean"].mean()), 4),
        },
        "by_platform": hubs.group_by("platform").agg(pl.len().alias("n")).to_dict(as_series=False),
        "top_hubs": [
            {"username": r["username"], "platform": r["platform"],
             "er": round(r["er_mean"], 2), "ppi": round(r["ppi_mean"], 2)}
            for r in hubs.head(10).iter_rows(named=True)
        ],
    }


# ─── Runner ──────────────────────────────────────────────────────────


def run_all(gold_path: str):
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    df = load(gold_path)
    print("[research] Loaded %d actors" % len(df))

    os.makedirs("%s/research" % REPORTS_DIR, exist_ok=True)

    print("[P1] Power Law por plataforma...")
    p1 = p1_power_law_by_platform(df)
    with open("%s/research/p1_powerlaw.json" % REPORTS_DIR, "w", encoding="utf-8") as f:
        json.dump(p1, f, indent=2, ensure_ascii=False)
    for plat, v in p1.items():
        a = v.get("alpha", "N/A")
        print("  %s alpha=%s" % (plat.ljust(14), str(a)))

    print("[P2] Sentiment vs Engagement...")
    p2 = p2_sentiment_engagement_corr(df)
    with open("%s/research/p2_sentiment_er.json" % REPORTS_DIR, "w", encoding="utf-8") as f:
        json.dump(p2, f, indent=2, ensure_ascii=False)
    print("  Spearman rho=%.4f (p=%.4f)" % (p2['spearman_rho'], p2['spearman_p']))

    print("[P3] High-Leverage Nodes...")
    p3 = p3_high_leverage(df)
    with open("%s/research/p3_leverage.json" % REPORTS_DIR, "w", encoding="utf-8") as f:
        json.dump(p3, f, indent=2, ensure_ascii=False)
    print("  %d/%d high-leverage nodes" % (p3['n_high_leverage'], p3['n_total']))

    print("[P4] AFI vs PPI...")
    p4 = p4_afi_ppi_corr(df)
    with open("%s/research/p4_afi_ppi.json" % REPORTS_DIR, "w", encoding="utf-8") as f:
        json.dump(p4, f, indent=2, ensure_ascii=False)
    print("  Spearman rho=%.4f (p=%.4f)" % (p4['spearman_rho'], p4['spearman_p']))

    print("[P5] Gini por plataforma...")
    p5 = p5_gini_by_platform(df)
    with open("%s/research/p5_gini_platform.json" % REPORTS_DIR, "w", encoding="utf-8") as f:
        json.dump(p5, f, indent=2, ensure_ascii=False)
    for plat, v in p5.items():
        g = v.get("gini", "N/A")
        ci = v.get("bootstrap", {})
        if ci:
            print("  %s Gini=%.4f CI95=[%.4f,%.4f]" % (plat.ljust(14), g, ci['ci_95'][0], ci['ci_95'][1]))
        else:
            print("  %s Gini=%s" % (plat.ljust(14), str(g)))

    print("[P6] Super-Hub Profiles...")
    p6 = p6_super_hub_profiles(df)
    with open("%s/research/p6_superhubs.json" % REPORTS_DIR, "w", encoding="utf-8") as f:
        json.dump(p6, f, indent=2, ensure_ascii=False)
    print("  %d super-hubs" % p6['n_hubs'])

    print("[research] All results in %s/research/" % REPORTS_DIR)


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/gold/fact_metrics.parquet"
    run_all(path)
