# Attention Observatory

**Observatorio empírico de la economía de la atención digital.**

Trata la atención humana como un recurso ecológico finito (Simon, 1971) y modela su distribución asimétrica en plataformas digitales mediante un pipeline ELT reproducible con **6 fuentes activas**, espacio de estados multivariable y validación econométrica de desigualdad estructural.

Este sistema **no analiza personas, intenciones ni moraliza redes sociales**. Analiza estructuras de distribución de recursos finitos mediante matemática y estadística.

## Arquitectura

```
Bronze (raw parquet)  ──>  Silver (Polars)  ──>  Gold (feature space)
     │                                                │
  6 fuentes                                     [ER, PPI, Sentiment, AFI]
  sin transformar                               actores como vectores
```

## Fuentes activas

| Fuente | Auth | Escala |
|--------|------|--------|
| Hacker News API | Ninguna | ~280 posts/ejecución |
| Wikipedia API | User-Agent | ~400 revisions/ejecución |
| HuggingFace Datasets | Ninguna | 3000+ registros/ejecución |
| Bluesky AT Protocol | Ninguna | ~240 posts/ejecución |
| Mastodon API | Ninguna | ~120 posts/ejecución |
| GitHub API | Token gratuito | ~5000 req/h |

## Feature space

Cada actor es un vector en 4 dimensiones:

- **ER** — Engagement Rate (interacciones / followers × 100)
- **PPI** — Production Pressure Index (1 / ln(intervalo + 1.01))
- **Sentiment** — NLP score [-1, 1] (transformers distilbert)
- **AFI** — Aspirational Framing Index (densidad de keywords de prestigio)

## Instalación

```powershell
conda create -n attention_obs python=3.11
conda activate attention_obs
pip install -r requirements.txt
```

## Ejecución

```powershell
# Pipeline completo
$env:GITHUB_TOKEN='github_pat_...'
python main.py

# Solo transform + stats (si ya hay datos bronze)
python main.py --skip-elt

# Dashboard
streamlit run app.py
```

## Resultados clave

| Métrica | Valor |
|---------|-------|
| Gini | 0.983 — concentración extrema |
| Power Law α | 2.19 (HN, Bluesky) |
| Super-hubs | 10 nodos (Z>3) |
| Fuentes | 6 activas |
| Actores | 4,136 |
| NLP | distilbert transformers |

## Metodología

Spec-Driven Development: toda métrica y capa analítica se deriva de los manifiestos fundacionales en [`manifiestos/`](manifiestos/).

## Licencia

MIT
