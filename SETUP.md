# SETUP — Attention Observatory

## Entorno

```powershell
conda create -n attention_obs python=3.11
conda activate attention_obs
pip install -r requirements.txt
```

Dependencias clave: polars, streamlit, plotly, powerlaw, scipy, transformers, torch, fitz (PyMuPDF).

## APIs y tokens

| Fuente | Configuración |
|--------|--------------|
| **HackerNews** | Sin auth. Variable: `HN_TOP_STORIES=30`, `HN_COMMENTS_PER_STORY=10` |
| **Wikipedia** | Sin auth. Variable: `WIKI_TOPICS="topic1,topic2"`, `WIKI_PER_QUERY=5` |
| **HuggingFace** | Sin auth. Variable: `HF_DATASET=SetFit/go_emotions`, `HF_MAX_ROWS=3000` |
| **Bluesky** | Sin auth. Variable: `BLUESKY_TOPICS="topic1,topic2"`, `BLUESKY_PER_TOPIC=30` |
| **Mastodon** | Sin auth. Variable: `MASTODON_INSTANCES="instance1,instance2"` |
| **GitHub** | Token: `$env:GITHUB_TOKEN='ghp_...'`. Variables: `GITHUB_QUERIES`, `GITHUB_REPOS_PER_QUERY=3` |
| **Telegram** | Bot token: `$env:TELEGRAM_BOT_TOKEN='...'`. Variables: `TELEGRAM_CHANNELS`, `TELEGRAM_PER_CHANNEL=50` |

## Ejecutar

```powershell
cd C:\Users\JUAN\attention_observatory
$env:GITHUB_TOKEN='github_pat_...'
$env:HF_HUB_DISABLE_SYMLINKS_WARNING='1'
& "C:\Users\JUAN\miniconda3\envs\attention_obs\python.exe" main.py
```

Solo stats (sin ingesta):
```powershell
& "C:\Users\JUAN\miniconda3\envs\attention_obs\python.exe" main.py --skip-elt
```

Forzar datos simulados:
```powershell
& "C:\Users\JUAN\miniconda3\envs\attention_obs\python.exe" main.py --simulate
```

Dashboard:
```powershell
streamlit run app.py
```

## Estructura del proyecto

Ver `CONTEXT.md` para la estructura completa del repositorio y `PLAN.md` para el plan de desarrollo.
