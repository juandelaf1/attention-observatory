import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import polars as pl
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


from src.stats.inequality import (
    compute_inequality,
    compute_anomalies,
    compute_breakdown,
    _lorenz,
    _cooks_distance,
)

st.set_page_config(
    page_title="Attention Observatory",
    page_icon="",
    layout="wide",
)

COLOR_INEQ = "#E74C3C"
COLOR_BLUE = "#3498DB"
COLOR_HUB  = "#E67E22"
COLOR_GREEN = "#2ECC71"
COLOR_PURPLE = "#9B59B6"
BG_COLOR = "#FAFAFA"


@st.cache_data
def load_gold(path: str = "data/gold/fact_metrics.parquet") -> pl.DataFrame:
    return pl.read_parquet(path)


@st.cache_data
def load_posts(path: str = "data/bronze") -> pl.DataFrame:
    files = sorted(Path(path).glob("*posts*.parquet"))
    if not files:
        return pl.DataFrame()
    dfs = [pl.read_parquet(f) for f in files]
    return pl.concat(dfs, how="diagonal") if len(dfs) > 1 else dfs[0]


@st.cache_data
def compute_metrics(df: pl.DataFrame):
    er = df["er_mean"].to_numpy()
    ineq = compute_inequality(er)
    anomaly = compute_anomalies(df)
    breakdown = compute_breakdown(df)
    return ineq, anomaly, breakdown


# ── Chart builders ─────────────────────────────────────────────

def make_lorenz(ineq):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1],
        mode="lines",
        name="Perfect Equality",
        line=dict(dash="dash", color=COLOR_BLUE, width=1.5),
    ))

    fig.add_trace(go.Scatter(
        x=ineq.lorenz_x, y=ineq.lorenz_y,
        mode="lines",
        name=f"Lorenz (Gini={ineq.gini:.4f})",
        fill="tozeroy",
        line=dict(color=COLOR_INEQ, width=3),
        hovertemplate="Actors: %{x:.1%}<br>Attention: %{y:.1%}<extra></extra>",
    ))

    fig.add_annotation(
        x=0.25, y=0.85,
        text=f"<b>Gini = {ineq.gini:.4f}</b>",
        showarrow=False,
        font=dict(size=16, color=COLOR_INEQ),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor=COLOR_INEQ,
        borderwidth=1,
        borderpad=6,
    )

    fig.update_layout(
        title=dict(text="Lorenz Curve — Attention Concentration", font=dict(size=18)),
        xaxis=dict(title="Cumulative Share of Actors", tickformat=".0%", range=[0, 1]),
        yaxis=dict(title="Cumulative Share of Attention", tickformat=".0%", range=[0, 1]),
        plot_bgcolor=BG_COLOR,
        hovermode="x unified",
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def make_powerlaw(df_pd, ineq):
    valid = df_pd[(df_pd["max_followers"] > 0) & (df_pd["er_mean"] > 0)].copy()
    if len(valid) < 10:
        return None

    x_arr = np.log10(valid["max_followers"].values)
    y_arr = np.log10(valid["er_mean"].values)
    slope, intercept = np.polyfit(x_arr, y_arr, 1)

    line_domain = np.logspace(
        np.log10(valid["max_followers"].min()),
        np.log10(valid["max_followers"].max()), 100
    )
    line_y = 10 ** (intercept + slope * np.log10(line_domain))

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=valid["max_followers"], y=valid["er_mean"],
        mode="markers",
        name=f"Actors (n={len(valid)})",
        marker=dict(
            color=valid.get("has_external_ecosystem", pd.Series([False] * len(valid))).map(
                {True: COLOR_INEQ, False: COLOR_BLUE}
            ),
            size=6,
            opacity=0.55,
            line=dict(width=0.5, color="rgba(0,0,0,0.2)"),
        ),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Followers: %{x:,.0f}<br>"
            "ER: %{y:.2f}%<br>"
            "Platform: %{customdata[1]}<extra></extra>"
        ),
        customdata=np.column_stack([
            valid.get("actor_id", [""] * len(valid)).values,
            valid.get("platform", [""] * len(valid)).values,
        ]),
    ))

    fig.add_trace(go.Scatter(
        x=line_domain, y=line_y,
        mode="lines",
        name=f"Power Law fit (α={ineq.powerlaw_alpha:.3f})",
        line=dict(color=COLOR_PURPLE, width=2, dash="dash"),
    ))

    fig.update_layout(
        title=dict(
            text=f"Power Law — Engagement × Followers  (α={ineq.powerlaw_alpha:.3f}, Pareto={ineq.powerlaw_is_pareto})",
            font=dict(size=18),
        ),
        xaxis=dict(title="Followers", type="log", exponentformat="power"),
        yaxis=dict(title="Engagement Rate (%)", type="log", exponentformat="power"),
        plot_bgcolor=BG_COLOR,
        hovermode="closest",
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(orientation="h", y=1.02),
    )
    return fig


def make_superhubs(df_pd, anomaly):
    top = df_pd.nlargest(30, "er_mean").copy()
    top = top.iloc[::-1]

    colors = top["has_external_ecosystem"].map({True: COLOR_INEQ, False: COLOR_BLUE}) if "has_external_ecosystem" in top.columns else COLOR_BLUE

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=top["actor_id"],
        x=top["er_mean"],
        orientation="h",
        marker=dict(
            color=colors,
            line=dict(width=0.5, color="rgba(0,0,0,0.3)"),
        ),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "ER: %{x:.2f}%<br>"
            "Followers: %{customdata[0]:,}<br>"
            "Platform: %{customdata[1]}<br>"
            "PPI: %{customdata[2]:.3f}<br>"
            "AFI: %{customdata[3]:.4f}<extra></extra>"
        ),
        customdata=np.column_stack([
            top.get("max_followers", [0] * len(top)).values,
            top.get("platform", [""] * len(top)).values,
            top.get("ppi_mean", [0] * len(top)).values,
            top.get("afi_mean", [0] * len(top)).values,
        ]),
    ))

    fig.update_layout(
        title=dict(
            text=f"Top 30 by Engagement — {anomaly.n_super_hubs} Super-Hubs (Z>3) controlling {anomaly.super_hub_attention_share:.1%} of attention",
            font=dict(size=18),
        ),
        xaxis=dict(title="Engagement Rate (%)"),
        yaxis=dict(title=None, autorange="reversed"),
        plot_bgcolor=BG_COLOR,
        hovermode="y unified",
        margin=dict(l=10, r=20, t=50, b=40),
        height=500,
    )
    return fig


def make_cooks_plot(df_pd):
    er = df_pd["er_mean"].values
    ppi = df_pd["ppi_mean"].values
    cooks = _cooks_distance(ppi, er)
    threshold = 4.0 / max(1, len(cooks))

    df_c = df_pd.copy()
    df_c["cooks_d"] = cooks
    df_c["is_high"] = cooks > threshold

    fig = go.Figure()

    for is_high, name, color, symbol in [
        (False, "Normal", COLOR_BLUE, "circle"),
        (True, "High-Leverage", COLOR_INEQ, "star"),
    ]:
        subset = df_c[df_c["is_high"] == is_high]
        if subset.empty:
            continue
        fig.add_trace(go.Scatter(
            x=subset["ppi_mean"], y=subset["er_mean"],
            mode="markers",
            name=name,
            marker=dict(
                color=color,
                size=6 + 15 * subset["cooks_d"] / max(1, subset["cooks_d"].max()),
                symbol=symbol,
                opacity=0.7 if not is_high else 0.9,
                line=dict(width=0.5, color="rgba(0,0,0,0.2)"),
            ),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "PPI: %{x:.3f}<br>"
                "ER: %{y:.2f}%<br>"
                "Cook's D: %{customdata[1]:.4f}<br>"
                "Platform: %{customdata[2]}<extra></extra>"
            ),
            customdata=np.column_stack([
                subset["actor_id"].values,
                subset["cooks_d"].values,
                subset.get("platform", [""] * len(subset)).values,
            ]),
        ))

    fig.add_hline(
        y=threshold,
        line_dash="dash", line_color=COLOR_INEQ, line_width=1.5,
        annotation_text=f"threshold = {threshold:.4f}",
        annotation_position="bottom right",
    )

    fig.update_layout(
        title=dict(text=f"Leverage Plot — {df_c['is_high'].sum()} High-Leverage Nodes", font=dict(size=18)),
        xaxis=dict(title="Production Pressure Index (PPI)"),
        yaxis=dict(title="Engagement Rate (%)"),
        plot_bgcolor=BG_COLOR,
        hovermode="closest",
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def make_sentiment_heatmap(df_pd):
    valid = df_pd.dropna(subset=["sentiment_avg", "er_mean"])
    if len(valid) < 50:
        return None

    fig = px.density_heatmap(
        valid,
        x="sentiment_avg", y="er_mean",
        nbinsx=30, nbinsy=30,
        color_continuous_scale="Viridis",
        title="Sentiment × Engagement — Density",
        labels={
            "sentiment_avg": "Avg Sentiment",
            "er_mean": "Engagement Rate (%)",
        },
        hover_data={"count": True},
    )
    fig.update_traces(opacity=0.8)
    fig.update_layout(
        plot_bgcolor=BG_COLOR,
        margin=dict(l=40, r=20, t=50, b=40),
        coloraxis_colorbar=dict(title="Count"),
    )
    return fig


def make_temporal_trend(posts_pd):
    if posts_pd.empty or "timestamp" not in posts_pd.columns:
        return None
    df = posts_pd.copy()
    df["ts"] = pd.to_datetime(df["timestamp"], utc=True)
    df["week"] = df["ts"].dt.isocalendar().week.astype(int)
    df["year"] = df["ts"].dt.isocalendar().year.astype(int)
    df["week_label"] = df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)

    if "platform" not in df.columns:
        df["platform"] = "unknown"

    weekly = (
        df.groupby(["week_label", "platform"])
        .agg(avg_er=("engagement_rate", "mean"),
             avg_ppi=("ppi", "mean"),
             post_count=("post_id", "count"))
        .reset_index()
    )

    if weekly.empty:
        return None

    fig = px.line(
        weekly,
        x="week_label", y="avg_er",
        color="platform",
        markers=True,
        title="Engagement Rate Over Time (weekly)",
        labels={"week_label": "Week", "avg_er": "Avg Engagement Rate (%)"},
        hover_data={"avg_ppi": ":.3f", "post_count": ":,"},
    )
    fig.update_layout(
        plot_bgcolor=BG_COLOR,
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(orientation="h", y=1.02),
    )
    return fig


def make_actor_histogram(er_arr):
    fig = px.histogram(
        x=er_arr, nbins=40,
        log_y=True,
        title="Engagement Distribution (log scale)",
        labels={"x": "Engagement Rate (%)"},
        color_discrete_sequence=[COLOR_INEQ],
    )
    fig.update_traces(opacity=0.75)
    fig.update_layout(
        plot_bgcolor=BG_COLOR,
        margin=dict(l=40, r=20, t=50, b=40),
        showlegend=False,
        yaxis=dict(title="Actors"),
    )
    return fig


def make_platform_bar(filtered):
    counts = filtered.group_by("platform").len().sort("len", descending=True).to_pandas()
    fig = px.bar(
        counts,
        x="platform", y="len",
        title="Actors by Platform",
        color="platform",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"len": "Actors", "platform": ""},
        text="len",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        plot_bgcolor=BG_COLOR,
        margin=dict(l=40, r=20, t=50, b=40),
        showlegend=False,
        xaxis_title=None,
    )
    return fig


def make_actor_rankbar(top30):
    top30 = top30.copy()
    colors = top30["has_external_ecosystem"].map({True: COLOR_INEQ, False: COLOR_BLUE}) if "has_external_ecosystem" in top30.columns else COLOR_BLUE
    top30["_color"] = colors
    top30 = top30.sort_values("er_mean")

    fig = px.bar(
        top30,
        y="actor_id", x="er_mean",
        orientation="h",
        title="Top 30 Actors by Engagement Rate",
        labels={"er_mean": "ER (%)", "actor_id": ""},
        color="_color",
        color_discrete_map="identity",
        hover_data={
            "platform": True,
            "max_followers": ":,",
            "ppi_mean": ":.3f",
            "_color": False,
        },
    )
    fig.update_layout(
        plot_bgcolor=BG_COLOR,
        margin=dict(l=10, r=20, t=50, b=40),
        showlegend=False,
        height=400,
        yaxis=dict(autorange="reversed"),
    )
    return fig


# ── Main ───────────────────────────────────────────────────────

def main():
    df = load_gold()
    ineq, anomaly, breakdown = compute_metrics(df)

    st.title("Attention Observatory")
    st.markdown("---")

    platforms = df["platform"].unique().to_list() if "platform" in df.columns else []
    selected_platforms = st.sidebar.multiselect("Platform", platforms, default=platforms)

    min_fol = int(df["max_followers"].min()) if len(df) > 0 else 0
    max_fol = int(df["max_followers"].max()) if len(df) > 0 else 1
    follower_range = st.sidebar.slider(
        "Min followers", min_fol, max_fol,
        (min_fol, max_fol), step=1
    )

    mask = (
        (pl.col("max_followers") >= follower_range[0]) &
        (pl.col("max_followers") <= follower_range[1])
    )
    if selected_platforms:
        mask = mask & pl.col("platform").is_in(selected_platforms)

    filtered = df.filter(mask)
    filtered_np = filtered.to_pandas()

    tab1, tab2, tab3, tab4 = st.tabs([
        "System Overview",
        "Attention Inequality",
        "State Space",
        "Actor Explorer",
    ])

    # ════════════════════════════════════════════════════════════
    # TAB 1
    # ════════════════════════════════════════════════════════════
    with tab1:
        st.header("System Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Actors", len(filtered))
        col2.metric("Total Posts", int(filtered["post_count"].sum()))
        col3.metric("Platforms", len(filtered["platform"].unique()) if "platform" in filtered.columns else 1)
        col4.metric("Gini Coefficient", f"{ineq.gini:.4f}")
        st.plotly_chart(make_platform_bar(filtered), use_container_width=True)

        external_pct = (filtered["has_external_ecosystem"].sum() / max(1, len(filtered))) * 100
        truncated_count = filtered["is_legally_truncated"].sum()
        prestige_count = filtered["has_prestige_trajectory"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("With External Ecosystem", f"{external_pct:.1f}%")
        col2.metric("Legally Truncated", int(truncated_count))
        col3.metric("Prestige Trajectory", int(prestige_count))

        if breakdown.systemic_saturation:
            st.error(f"⚠ **Systemic Saturation Detected** — Gini={ineq.gini:.4f}, Churn Acceleration={breakdown.churn_acceleration_mean:.4f}")

        if st.checkbox("Show temporal engagement trend", value=False):
            posts = load_posts()
            if posts.height > 0:
                trend = make_temporal_trend(posts.to_pandas())
                if trend is not None:
                    st.plotly_chart(trend, use_container_width=True)

        with st.expander(" Note — Acknowledgment of Creative Agency"):
            st.markdown(
                "This system models structural asymmetries in digital attention distribution. "
                "The critical analysis of extractive dynamics does not negate the **distinctive value "
                "of individual talent, craft, and cultural contribution**."
            )

    # ════════════════════════════════════════════════════════════
    # TAB 2
    # ════════════════════════════════════════════════════════════
    with tab2:
        st.header("Attention Inequality Metrics")

        col1, col2, col3 = st.columns(3)
        col1.metric("Gini Coefficient", f"{ineq.gini:.4f}")
        col2.metric("Power Law α", f"{ineq.powerlaw_alpha:.4f}")
        col3.metric("Pareto Distribution", "YES" if ineq.powerlaw_is_pareto else "NO")

        row1 = st.columns([3, 2])
        with row1[0]:
            st.plotly_chart(make_lorenz(ineq), use_container_width=True)
        with row1[1]:
            st.plotly_chart(make_actor_histogram(filtered["er_mean"].to_numpy()), use_container_width=True)

        st.markdown("---")
        pl_chart = make_powerlaw(filtered_np, ineq)
        if pl_chart:
            st.plotly_chart(pl_chart, use_container_width=True)
        else:
            st.warning("Not enough data for Power Law fit.")

        st.markdown("---")
        st.plotly_chart(make_superhubs(filtered_np, anomaly), use_container_width=True)

        with st.expander("  Methodological Note — Legal Enclosure"):
            st.markdown(
                "The asymmetry of the system is not sustained solely through algorithmic "
                "optimization of attention, but through the **punitive privatization of semantic space**. "
                "The `is_legally_truncated` flag captures nodes whose activity was forcibly interrupted."
            )

    # ════════════════════════════════════════════════════════════
    # TAB 3
    # ════════════════════════════════════════════════════════════
    with tab3:
        st.header("State Space Exploration")

        gold_pd = filtered_np
        color_map_3d = {True: COLOR_INEQ, False: COLOR_BLUE}

        fig_3d = px.scatter_3d(
            gold_pd,
            x="er_mean", y="ppi_mean", z="sentiment_avg",
            color="has_external_ecosystem" if "has_external_ecosystem" in gold_pd.columns else None,
            color_discrete_map=color_map_3d,
            hover_name="actor_id",
            hover_data={
                "er_mean": ":,.2f",
                "ppi_mean": ":,.2f",
                "sentiment_avg": ":,.2f",
                "afi_mean": ":,.4f",
                "max_followers": ":,",
            },
            title="Actor State Space — Engagement × PPI × Sentiment",
            labels={
                "er_mean": "ER (%)",
                "ppi_mean": "Production Pressure Index",
                "sentiment_avg": "Avg Sentiment",
            },
            opacity=0.7,
        )
        fig_3d.update_traces(marker=dict(size=5, line=dict(width=0.3, color="rgba(0,0,0,0.2)")))
        st.plotly_chart(fig_3d, use_container_width=True)

        st.markdown("---")
        col_cook, col_hex = st.columns(2)
        with col_cook:
            st.plotly_chart(make_cooks_plot(gold_pd), use_container_width=True)
        with col_hex:
            heat_chart = make_sentiment_heatmap(gold_pd)
            if heat_chart:
                st.plotly_chart(heat_chart, use_container_width=True)
            else:
                st.info("Need ≥50 actors with sentiment data for density heatmap.")

        with st.expander("  Clinical Note — Network Vulnerability"):
            st.markdown(
                "High-leverage points confirm network vulnerability to critical node failure. "
                "When super-hub attention load exceeds agent stability threshold, "
                "node behavior enters erratic regimes."
            )

    # ════════════════════════════════════════════════════════════
    # TAB 4
    # ════════════════════════════════════════════════════════════
    with tab4:
        st.header("Actor Explorer")

        actor_ids = filtered["actor_id"].to_list()
        selected = st.selectbox("Select Actor", actor_ids)

        if selected:
            actor = filtered.filter(pl.col("actor_id") == selected)
            if len(actor) > 0:
                row = actor.row(0, named=True)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Platform", row.get("platform", "N/A"))
                c2.metric("Followers", f"{row.get('max_followers', 0):,}")
                c3.metric("ER", f"{row.get('er_mean', 0):.2f}%")
                c4.metric("PPI", f"{row.get('ppi_mean', 0):.3f}")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Sentiment", f"{row.get('sentiment_avg', 0):.3f}")
                c2.metric("AFI", f"{row.get('afi_mean', 0):.4f}")
                c3.metric("External Ecosystem", "YES" if row.get("has_external_ecosystem") else "no")
                c4.metric("Legally Truncated", "YES" if row.get("is_legally_truncated") else "no")

        st.markdown("---")
        st.subheader("All Actors — Ranked by Engagement")
        ranked = filtered.sort("er_mean", descending=True).to_pandas()
        st.plotly_chart(make_actor_rankbar(ranked.head(30)), use_container_width=True)

        with st.expander("  Phase Transition Note — Prestige Drift"):
            st.markdown(
                "A node's shift toward lower posting frequency but higher "
                "Aspirational Framing Index (AFI) confirms a **capital reconversion strategy**: "
                "the agent reduces exposure to raw algorithmic extractivism "
                "through institutional prestige assets."
            )

    st.markdown("---")
    st.caption(
        "Attention Observatory — Empirical modeling of digital attention distribution. "
        "This is not a moral study of social media; it is a mathematical model of finite "
        "resource allocation under preferential attachment dynamics."
    )


if __name__ == "__main__":
    main()
