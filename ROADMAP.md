# ROADMAP — Attention Observatory
## Guía Profesional SDD · Trazabilidad Total · Resultados Medibles

```
╔══════════════════════════════════════════════════════════════╗
║               ATTENTION OBSERVATORY                          ║
║   Spec-Driven Development · Pipeline ELT · Observabilidad    ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 1. FILOSOFÍA DEL PROYECTO

### ¿Qué es Attention Observatory?

Un sistema de **observabilidad estructural** sobre la economía de la atención digital. No es una herramienta de marketing, no es un panel de influencers, no es un juicio moral sobre redes sociales. Es un **instrumento clínico** que modela la distribución de un recurso finito —la atención humana— y detecta transiciones de fase en el ecosistema digital.

### ¿Qué es Spec-Driven Development (SDD)?

SDD significa que **todo** en este proyecto —cada métrica, cada transformación, cada capa analítica— se deriva explícitamente de los documentos de especificación:

```
  ┌──────────────────┐
  │   MANIFIESTOS    │  ← Documents fundacionales (la "Spec")
  │   (PDF + TXT)    │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │   HIPÓTESIS      │  ← Preguntas de investigación
  │   (PLAN.md Fase2)│
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │   MÉTRICAS       │  ← Feature space + Estadísticas
  │   (Gold schema)  │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │   CÓDIGO         │  ← Pipeline ELT + Dashboard
  │   (src/)         │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │   VALIDACIÓN     │  ← Tests estadísticos + visualización
  │   (resultados)   │
  └──────────────────┘
```

Cada flecha es **trazable**: puedes ir de cualquier línea de código a la sección del manifiesto que la justifica.

---

## 2. MAPA DE TRAZABILIDAD (Cobertura Actual)

| Manifiesto | Sección | Hipótesis | Métrica | Archivo | Estado |
|-----------|---------|-----------|---------|---------|--------|
| Inviabilidad | §I | Atención como recurso finito | ER, Gini | `silver_to_gold.py`, `inequality.py` | ✅ |
| Inviabilidad | §II | Homeostasis funcional (válvulas) | PPI | `silver_to_gold.py` | ✅ |
| Inviabilidad | §III-A | Cinismo algorítmico → diversificación | `has_external_ecosystem` | `silver_to_gold.py` | ✅ |
| Inviabilidad | §III-B | Éxodo a catacumbas digitales | Churn acceleration | `inequality.py` | ✅ |
| Inviabilidad | §IV | Puntos de leverage → transición de fase | Cook's Distance | `inequality.py` | ✅ |
| Radical | §II.1 | Asimetría topológica (winner-takes-all) | Power Law α, Super-hubs | `inequality.py` | ✅ |
| Radical | §II.2 | Sofisticación y clausura de campo | Prestige Drift | `silver_to_gold.py` | ✅ |
| Radical | §II.3 | Privatización del espacio semántico | Legal truncation | `silver_to_gold.py` | ✅ |
| Inviabilidad | §IV | Límite termodinámico → fragmentación | Systemic saturation | `inequality.py` | ✅ |
| — | — | NLP para medir tono | Sentiment | `nlp/sentiment.py` | ✅ |

### Brechas detectadas (hipótesis sin métrica)

Las identificaremos en Fase 0.2 del plan.

---

## 3. ARQUITECTURA DE DATOS (ELT)

```
BRONZE                                SILVER                              GOLD
─────────                             ──────                              ────
┌──────────────┐                     ┌──────────────┐                   ┌──────────────┐
│ HN           │  actors.parquet     │              │                   │              │
│ Wikipedia    │ ───────────────────►│  Polars      │  fact_metrics    │  Streamlit   │
│ HuggingFace  │  posts.parquet      │  cleansing   │ ───────────────►│  Dashboard   │
│ Bluesky      │ ───────────────────►│  + merge     │  .parquet       │  + Stats     │
│ Mastodon     │                     │              │                   │              │
│ GitHub       │                     └──────────────┘                   └──────────────┘
│ Telegram(*)  │
└──────────────┘
     RAW                               TRANSFORMED                         ANALYZED

Capa Silver (preparada, no implementada):
  - stg_actors.parquet
  - stg_posts.parquet
  - Enriquecimiento NLP
  - Feature engineering
```

---

## 4. PLAN DE TRABAJO (HITOS MEDIBLES)

### Hito 0: EDA FUNDACIONAL (estamos aquí — 1-2 sesiones)
**Output**: Reporte de diagnóstico con matriz de correlación, boxplots por plataforma, validación de calidad.

| Tarea | Duración | Verificación |
|-------|----------|-------------|
| Matriz de correlación ER/PPI/Sentiment/AFI | 1h | Heatmap publicado en `/data/reports/` |
| Boxplots por plataforma | 1h | Gráfico comparativo 6 fuentes |
| Diagnóstico de calidad (nulos, skewness) | 1h | Tabla de calidad por fuente |
| Separar huggingface del resto | 30min | Análisis con/sin HF |
| Bootstrap de Gini (IC 95%) | 1h | Intervalo de confianza publicado |

### Hito 1: ALINEACIÓN SDD (1 sesión)
**Output**: Mapa de trazabilidad completo + columnas huérfanas eliminadas o justificadas.

| Tarea | Verificación |
|-------|-------------|
| Mapear cada columna de gold a manifiesto | Tabla en ROADMAP.md actualizada |
| Detectar columnas sin spec | Lista de columnas a eliminar/justificar |
| Detectar hipótesis sin métrica | Lista de nuevas métricas a implementar |

### Hito 2: PREGUNTAS DE INVESTIGACIÓN (2-3 sesiones)
**Output**: Respuestas a P1-P6 con tests estadísticos y visualizaciones.

| Pregunta | Método | Output |
|----------|--------|--------|
| P1: Power Law por plataforma | MLE + LR test | α por fuente + gráfico |
| P2: Sentiment vs Engagement | Spearman ρ | Matriz de correlación |
| P3: High-leverage nodes | Cook's D | Lista rankeada |
| P4: AFI vs PPI | Spearman ρ | Scatter plot |
| P5: Gini por plataforma | Bootstrap | Barra + IC |
| P6: Perfil de super-hubs | Perfil vectorial | Cluster map |

### Hito 3: DASHBOARD PROFESIONAL (2 sesiones)
**Output**: app.py refactorizado con hallazgos, exportable.

| Tarea | Entrega |
|-------|---------|
| Panel por pregunta de investigación | 6 tabs en Streamlit |
| Selector de plataforma cross-filter | Filtro interactivo |
| Export PDF de reporte | Botón de descarga |
| Notas de interpretación contextual | Markdown por panel |

### Hito 4: ANÁLISIS LONGITUDINAL (continuo)
**Output**: Serie temporal de métricas clave.

| Tarea | Entrega |
|-------|---------|
| Timestamp en cada ejecución | Columna `execution_ts` en gold |
| Base de datos de ejecuciones | `data/executions/` |
| Tracking de deriva de Gini, α, hubs | Línea temporal en dashboard |

### Hito 5: EXPANSIÓN DE FUENTES (según disponibilidad)
**Output**: Nuevos conectores documentados y trazables.

| Fuente | Dependencia | Prioridad |
|--------|-------------|-----------|
| Telegram | Token de bot (pedir al usuario) | Alta |
| Reddit | OAuth2 app | Media |
| YouTube | API key (GC) | Baja (bloqueado) |

---

## 5. MÉTRICAS DE ÉXITO (RESULTADOS MEDIBLES)

### Calidad del sistema
- [ ] **Cobertura de trazabilidad**: 100% de columnas en gold mapeadas a manifiesto
- [ ] **Reproducibilidad**: misma ejecución produce idéntico gold (hash verificable)
- [ ] **Tiempo de pipeline**: < 5 min full ELT con 6 fuentes

### Calidad científica
- [ ] **Bootstrap de Gini**: IC 95% publicado
- [ ] **Power Law**: LR test contra lognormal publicado
- [ ] **Test de plataformas**: Kruskal-Wallis + post-hoc Dunn

### Calidad profesional
- [ ] **Dashboard**: exportable a PDF
- [ ] **Documentación**: todos los MD actualizados
- [ ] **Código**: type hints + docstrings en funciones públicas

---

## 6. ESTRUCTURA DE ARCHIVOS (FINAL)

```
attention_observatory/
│
├── manifiestos/                      # SPEC — Documentos fundacionales
│   ├── MANIFIESTO_Inviabilidad_Evolutiva_HiperCentralizacion.pdf
│   ├── MANIFIESTO_Inviabilidad_Evolutiva_HiperCentralizacion.txt
│   ├── MANIFIESTO_Radical_Pesimismo_Luz_Claridad.pdf
│   └── MANIFIESTO_Radical_Pesimismo_Luz_Claridad.txt
│
├── data/
│   ├── bronze/                       # RAW — Parquet por fuente
│   │   ├── hackernews_actors.parquet
│   │   ├── hackernews_posts.parquet
│   │   ├── wikipedia_actors.parquet
│   │   ├── wikipedia_posts.parquet
│   │   ├── huggingface_actors.parquet
│   │   ├── huggingface_posts.parquet
│   │   ├── bluesky_actors.parquet
│   │   ├── bluesky_posts.parquet
│   │   ├── mastodon_actors.parquet
│   │   ├── mastodon_posts.parquet
│   │   ├── github_actors.parquet
│   │   └── github_posts.parquet
│   ├── silver/                       # STG — Capa intermedia (pendiente)
│   └── gold/                         # GOLD — fact_metrics.parquet
│
├── src/
│   ├── ingesta/                      # Conectores por plataforma
│   │   ├── hackernews.py
│   │   ├── wikipedia.py
│   │   ├── huggingface.py
│   │   ├── bluesky.py
│   │   ├── mastodon.py
│   │   ├── github.py
│   │   ├── telegram.py               # Pendiente token
│   │   ├── youtube.py                # Bloqueado
│   │   ├── reddit.py                 # Pendiente
│   │   └── simulator.py
│   ├── transform/
│   │   └── silver_to_gold.py
│   ├── stats/
│   │   └── inequality.py
│   └── nlp/
│       └── sentiment.py
│
├── main.py                           # Orquestador del pipeline
├── app.py                            # Dashboard Streamlit
│
├── CONTEXT.md                        # Visión general del proyecto
├── PLAN.md                           # Plan SDD detallado
├── ROADMAP.md                        # Esta guía
├── REPORT.md                         # Informe de resultados
├── CHECKPOINT.md                     # Bitácora diaria
├── SETUP.md                          # Instalación y configuración
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 7. ¿POR DÓNDE EMPEZAMOS?

```
HOY ───►  EDA (Fase 0.2)  ───►  Trazabilidad (Fase 0.1)  ───►  Preguntas (Fase 2)
  │                                                             │
  │  Matriz de correlación     Mapa columna→manifiesto          P1-P6 con tests
  │  Boxplots por plataforma   Detectar brechas                 Visualizaciones
  │  Diagnóstico calidad       Cerrar el círculo SDD            Interpretación
  │
  ▼
SIGUIENTE SESIÓN
```

Elige por dónde quieres arrancar.
