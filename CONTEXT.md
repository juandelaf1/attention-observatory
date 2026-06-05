# ATTENTION OBSERVATORY — PROYECTO

## MANIFIESTOS RECTORES (SPEC)

El proyecto se rige por dos documentos fundacionales en `manifiestos/`:

1. **MANIFIESTO_Inviabilidad_Evolutiva_HiperCentralizacion.pdf** — Ensayo socio-técnico sobre la ecología extractiva de la atención. Establece los fundamentos teóricos: atención como recurso finito, homeostasis funcional, geometría cíclica de la información, y el valor clínico del modelado de datos.

2. **MANIFIESTO_Radical_Pesimismo_Luz_Claridad.pdf** — Manifiesto operativo: diagnóstico desde el pesimismo radical, desnudo del mecanismo (asimetría topológica, clausura de campo, privatización del espacio semántico), e inviabilidad evolutiva como horizonte.

Ambos constituyen la **especificación** (Spec) de nuestro desarrollo: de ellos derivamos hipótesis, métricas y capas analíticas. No son documentos decorativos — son el contrato de diseño del sistema.

## ⚖️ REGLAS DE NEGOCIO (INMUTABLES)

1. **Neutralidad epistemológica** — el sistema describe, no prescribe, no moraliza.
2. **No inferencia psicológica individual** — no se etiquetan personas como "quemadas" o "fracasadas".
3. **Separación datos / interpretación** — los datos son neutros, la interpretación es contextual y está marcada como tal.
4. **Reproducibilidad total** — mismo pipeline → mismos resultados.
5. **Trazabilidad ELT** — cada transformación es rastreable desde Bronze hasta Gold.

## 🚫 LO QUE EL SISTEMA NO HACE

- No clasifica personas moral o psicológicamente
- No diagnostica comportamientos individuales
- No moraliza redes sociales
- No predice intenciones
- No emite juicios sobre contenido

## 🏗️ ARQUITECTURA

```
Bronze (raw parquet)  ──>  Silver (Polars cleansing)  ──>  Gold (feature space)
     │                                                          │
  actores + posts                                         actores como vectores
  sin transformar                                         [ER, PPI, Sentiment, AFI]
```

## 📊 FEATURE SPACE

Cada actor es un vector en espacio multivariable:

- **ER** = Engagement Rate (interacciones / followers × 100)
- **PPI** = Production Pressure Index (1 / ln(intervalo_horas + 1.01))
- **Sentiment** = NLP score [-1, 1] (distilbert transformers)
- **AFI** = Aspirational Framing Index (densidad de keywords de prestigio)

## 🧠 CAPAS ANALÍTICAS (DERIVADAS DE LOS MANIFIESTOS)

| Capa | Manifiesto | Hipótesis |
|------|-----------|-----------|
| 1. Capital Conversion | Inviabilidad §III-A | El cinismo algorítmico fuerza diversificación |
| 2. Legal Enclosure | Radical Pesimismo §II | La privatización del espacio semántico truncra nodos |
| 3. Prestige Drift | Inviabilidad §III-A | Los super-hubs mutan a capital cualitativo |
| 4. Anomaly Detection | Inviabilidad §IV | Puntos de alto apalancamiento como sensores de fase |
| 5. Super-Hub Detection | Radical Pesimismo §II | Asimetría topológica inevitable (winner-takes-all) |
| 6. Systemic Breakdown | Inviabilidad §IV | Límite termodinámico del feed infinito |

## 📐 MÉTODOS ESTADÍSTICOS

- Coeficiente de Gini
- Curva de Lorenz
- Power Law fitting (α, σ, Pareto test)
- Cook's Distance (leverage)
- Z-score para super-hubs

## 🔌 FUENTES DE DATOS

| Fuente | Auth | Estado | Escala |
|--------|------|--------|--------|
| Hacker News API | Ninguna | ✅ | ~280 posts/ejecución |
| Wikipedia API | User-Agent | ✅ | ~400 revisions/ejecución |
| HuggingFace Datasets | Ninguna | ✅ | 3000+ registros/ejecución |
| Bluesky API (AT Protocol) | Ninguna | ✅ | ~240 posts/ejecución |
| Mastodon API (público) | Ninguna | ✅ | ~120 posts/ejecución |
| GitHub API | Token gratuito | ✅ | ~5000 req/h |
| Telegram API | Bot token | 🔲 Pendiente token | ~50 posts/canal |
| YouTube API | API key (GC) | ❌ Bloqueado | N/A |
| Reddit API | OAuth | ❌ Pendiente | N/A |
| TikTok/Instagram/Meta | Business verify | ❌ No accesible | N/A |

## 📁 ESTRUCTURA DEL REPOSITORIO

```
attention_observatory/
├── manifiestos/             # Spec: documentos fundacionales (PDF + TXT)
├── data/
│   ├── bronze/              # Raw parquet por fuente
│   ├── silver/              # (preparado para capa intermedia)
│   └── gold/                # fact_metrics.parquet
├── src/
│   ├── ingesta/             # Conectores por fuente
│   ├── transform/           # silver_to_gold.py
│   ├── stats/               # inequality.py
│   └── nlp/                 # sentiment.py
├── main.py                  # Pipeline ELT
├── app.py                   # Dashboard Streamlit
├── CONTEXT.md               # Este archivo
├── PLAN.md                  # Plan de desarrollo SDD
├── ROADMAP.md               # Guía profesional del proyecto
├── REPORT.md                # Informe técnico de resultados
├── CHECKPOINT.md            # Bitácora diaria
├── SETUP.md                 # Guía de instalación
└── requirements.txt         # Dependencias
```

## 📋 ESTADO GENERAL DEL PROYECTO

### ✅ Completo
- Pipeline ELT multi-fuente (6 fuentes activas)
- Feature space (ER, PPI, AFI, Sentiment con transformers)
- Estadísticas (Gini, Lorenz, Power Law, Cook's, Z-score)
- NLP real con distilbert (transformers)
- Dashboard Streamlit funcional
- 6 conectores activos (HN, Wikipedia, HuggingFace, Bluesky, Mastodon, GitHub)
- Token GitHub configurado

### 🔲 Pendiente
- Telegram connector (requiere token de bot)
- Análisis longitudinal temporal (múltiples ejecuciones)
- Refinar dashboard con hallazgos de EDA
- EDA profundo: matriz de correlación, boxplots por plataforma
- Validación estadística extendida (bootstrap, test de hipótesis)
- Nuevos conectores (Reddit, YouTube si auth disponible)
