import polars as pl
import json
import os

REPORTS_DIR = "data/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

FEATURES = ["er_mean", "ppi_mean", "sentiment_avg", "afi_mean"]
PLATFORM_COL = "platform"


def quality_diagnostic(gold: pl.DataFrame) -> dict:
    diag = {}
    for col in FEATURES:
        s = gold[col]
        diag[col] = {
            "n_null": s.null_count(),
            "n_zero": (s == 0).sum(),
            "n_inf": int(s.is_infinite().sum()) if s.dtype in (pl.Float32, pl.Float64) else 0,
            "min": _safe(s.min()),
            "max": _safe(s.max()),
            "mean": _safe(s.mean()),
            "std": _safe(s.std()),
            "skew": _safe(s.skew()),
            "kurtosis": _safe(s.kurtosis()),
        }
        for p in [1, 5, 25, 50, 75, 95, 99]:
            diag[col][f"p{p}"] = _safe(s.quantile(p / 100))
    return diag


def correlation_matrix(gold: pl.DataFrame) -> dict:
    import scipy.stats as stats
    import numpy as np

    mat = gold.select(FEATURES).drop_nulls().to_numpy()
    n = mat.shape[1]
    labels = FEATURES
    result = {"pearson": {}, "spearman": {}}
    for i in range(n):
        for j in range(n):
            key = f"{labels[i]}__{labels[j]}"
            mask = ~(np.isnan(mat[:, i]) | np.isnan(mat[:, j]))
            x = mat[mask, i]
            y = mat[mask, j]
            r_p, p_p = stats.pearsonr(x, y)
            r_s, p_s = stats.spearmanr(x, y)
            result["pearson"][key] = {"r": round(r_p, 4), "p": float(p_p)}
            result["spearman"][key] = {"rho": round(r_s, 4), "p": float(p_s)}
    return result


def by_platform_diagnostics(gold: pl.DataFrame) -> dict:
    platforms = gold[PLATFORM_COL].unique().to_list()
    result = {}
    for plat in platforms:
        sub = gold.filter(pl.col(PLATFORM_COL) == plat)
        plat_diag = {}
        for col in FEATURES:
            s = sub[col]
            plat_diag[col] = {
                "n": len(sub),
                "mean": _safe(s.mean()),
                "std": _safe(s.std()),
                "median": _safe(s.median()),
                "min": _safe(s.min()),
                "max": _safe(s.max()),
                "skew": _safe(s.skew()),
            }
        result[str(plat)] = plat_diag
    return result


def n_per_platform(gold: pl.DataFrame) -> dict:
    return gold.group_by(PLATFORM_COL).agg(pl.len().alias("n")).to_dict(as_series=False)


def _safe(val):
    if val is None:
        return None
    try:
        return round(float(val), 6)
    except (TypeError, ValueError):
        return None


def run_all(gold_path: str):
    gold = pl.read_parquet(gold_path)
    n_total = len(gold)

    print(f"[eda] Loading {gold_path} — {n_total} actors")
    print(f"[eda] Platforms: {gold[PLATFORM_COL].unique().to_list()}")

    diag = quality_diagnostic(gold)
    with open(f"{REPORTS_DIR}/quality_diagnostic.json", "w", encoding="utf-8") as f:
        json.dump(diag, f, indent=2, ensure_ascii=False)
    print(f"[eda] quality_diagnostic.json written")

    corr = correlation_matrix(gold)
    with open(f"{REPORTS_DIR}/correlation_matrix.json", "w", encoding="utf-8") as f:
        json.dump(corr, f, indent=2, ensure_ascii=False)
    print(f"[eda] correlation_matrix.json written")

    plat_diag = by_platform_diagnostics(gold)
    plat_n = n_per_platform(gold)
    with open(f"{REPORTS_DIR}/by_platform.json", "w", encoding="utf-8") as f:
        json.dump({"counts": plat_n, "diagnostics": plat_diag}, f, indent=2, ensure_ascii=False)
    print(f"[eda] by_platform.json written")

    # Huggingface dominance check
    if "huggingface" in gold[PLATFORM_COL].to_list():
        hf = gold.filter(pl.col(PLATFORM_COL) == "huggingface")
        no_hf = gold.filter(pl.col(PLATFORM_COL) != "huggingface")
        hf_pct = round(len(hf) / n_total * 100, 1)
        print(f"\n[eda] HuggingFace dominates: {len(hf)}/{n_total} ({hf_pct}%)")
        print(f"[eda] With HF:    Gini={_gini(gold['er_mean'])}")
        print(f"[eda] Without HF: Gini={_gini(no_hf['er_mean'])}")
        hf_cmp = {"n_total": n_total, "hf_n": len(hf), "hf_pct": hf_pct,
                   "gini_with_hf": _gini(gold["er_mean"]),
                   "gini_without_hf": _gini(no_hf["er_mean"])}
        with open(f"{REPORTS_DIR}/huggingface_impact.json", "w", encoding="utf-8") as f:
            json.dump(hf_cmp, f, indent=2, ensure_ascii=False)
        print(f"[eda] huggingface_impact.json written")

    print("\n[eda] EDA complete. Reports in data/reports/")


def _gini(s):
    import numpy as np
    arr = s.drop_nulls().to_numpy()
    if len(arr) == 0 or arr.sum() == 0:
        return 0.0
    arr = np.sort(arr)
    n = len(arr)
    cum = np.cumsum(arr)
    return round(float((2 * np.sum((np.arange(1, n + 1)) * arr) / (n * cum[-1]) - (n + 1) / n)), 4)


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/gold/fact_metrics.parquet"
    run_all(path)
