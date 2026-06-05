# CHECKPOINT — 4 Jun 2026

## Estado actual
- **6 fuentes activas**: HackerNews, Wikipedia, HuggingFace, Bluesky, Mastodon, GitHub
- **NLP real**: transformers (distilbert) instalado y funcionando
- **Entorno**: conda `attention_obs` con Python 3.11 + torch 2.12 + transformers 5.9
- **Manifiestos incorporados**: `manifiestos/` con 2 docs fundacionales (PDF + TXT)
- **SDD adoptado**: Spec-Driven Development — toda métrica se deriva de los manifiestos

## Última ejecución
- Pipeline: ~3,797 actores, 4,072 posts
- Gini: 0.9933
- Super-hubs: 31 nodos
- Atención concentrada: 98.45%

## Archivos actualizados hoy
- `manifiestos/` — directorio con PDFs + TXT de los manifiestos rectores
- `CONTEXT.md` — actualizado con referencias a manifiestos, tabla de trazabilidad SDD
- `PLAN.md` — reestructurado como SDD: manifiesto → hipótesis → métrica → código
- `REPORT.md` — actualizado con 6 fuentes reales, NLP con transformers, resultados reales
- `SETUP.md` — actualizado con conectores reales (GitHub, Bluesky, etc.)
- `CHECKPOINT.md` — este archivo

## Próximos pasos (en orden)
1. **EDA Fase 0.2**: matriz de correlación, boxplots por plataforma
2. **Validar trazabilidad SDD**: mapear columnas de gold a manifiestos
3. **Refinar dashboard** con hallazgos de EDA
4. **Análisis longitudinal** (múltiples ejecuciones)
5. **Telegram connector** (si consigues token de bot)

## Cómo ejecutar
```powershell
cd C:\Users\JUAN\attention_observatory
$env:GITHUB_TOKEN='github_pat_...'
$env:HF_HUB_DISABLE_SYMLINKS_WARNING='1'
& "C:\Users\JUAN\miniconda3\envs\attention_obs\python.exe" main.py
```

Solo transform + stats (sin re-ingestar):
```powershell
& "C:\Users\JUAN\miniconda3\envs\attention_obs\python.exe" main.py --skip-elt
```
