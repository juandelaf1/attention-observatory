# PLAN DEL PROYECTO — Attention Observatory (SDD)

## ¿QUÉ ES SPEC-DRIVEN DEVELOPMENT (SDD)?

SDD significa que toda decisión técnica, métrica y capa analítica se deriva directamente de los **documentos de especificación** — en nuestro caso, los manifiestos en `manifiestos/`. 

No construimos "lo que se nos ocurre". Construimos lo que la **teoría** exige que midamos. Cada hipótesis se rastrea a una sección de un manifiesto, cada métrica a una hipótesis, cada transformación a una métrica.

---

## TRAZABILIDAD: MANIFIESTO → HIPÓTESIS → MÉTRICA → CÓDIGO

```
MANIFIESTO        →  HIPÓTESIS            →  MÉTRICA         →  CÓDIGO
────────────────────────────────────────────────────────────────────────
§Inviabilidad IV  →  Puntos de leverage   →  Cook's Distance  →  stats/inequality.py
                  →  predicen transición
§Radical §II      →  La red es scale-free →  Power Law α      →  stats/inequality.py
§Radical §II      →  Winner-takes-all     →  Gini, Lorenz     →  stats/inequality.py
§Inviabilidad III →  Cinismo → éxodo      →  Churn accel.     →  stats/inequality.py
§Inviabilidad III →  Super-hubs mutan     →  Prestige Drift   →  silver_to_gold.py
§Radical §II      →  Privatización legal  →  Legal truncation →  silver_to_gold.py
```

---

## FASE 0: DIAGNÓSTICO Y EDA (ESTAMOS AQUÍ)

### 0.1 Validar que las métricas actuales responden a los manifiestos
- [ ] Mapear cada columna de `fact_metrics.parquet` a una sección de manifiesto
- [ ] Detectar columnas "huérfanas" (sin respaldo en spec)
- [ ] Detectar hipótesis sin métrica asignada todavía

### 0.2 Análisis exploratorio profundo
- [x] Esquema de gold y bronce
- [x] Distribuciones univariadas (ER, PPI, Sentiment, AFI)
- [x] Detección de problemas: ceros, datos planos, columnas muertas
- [ ] **Matriz de correlación entre features** (¿ER y PPI están acoplados? ¿Sentiment y AFI?)
- [ ] **Boxplots por plataforma** (¿cada fuente tiene perfil distinto?)
- [ ] **Diagnóstico de calidad**: nulos, outliers, skewness por fuente
- [ ] **Separar huggingface del resto** (79% del dataset — ¿domina el análisis?)

### 0.3 Validación estadística de supuestos
- [ ] Bootstrap de Gini (intervalos de confianza)
- [ ] Test de hipótesis formal para Power Law (Clauset 2009)
- [ ] Comparación entre plataformas (Kruskal-Wallis, post-hoc Dunn)

---

## FASE 1: REPARACIÓN Y ALINEACIÓN CON SPEC

### 1.1 Feature engineering
- [ ] **Followers reales**: reemplazar followers=1 con estimación por plataforma
- [ ] **NLP con distilbert**: ya funcional, verificar cobertura
- [ ] **AFI**: revisar keyword set contra manifiestos (¿qué es "prestigio" según Radical Pesimismo?)
- [ ] **Legal truncation**: implementar detección real (caída abrupta a cero)
- [ ] **Prestige drift**: definir señal de activación basada en §Inviabilidad III-A

### 1.2 Decisión metodológica
- [ ] ¿HuggingFace debe tratarse por separado? (domina N, distorsiona distribuciones)
- [ ] ¿Estratificar por plataforma antes de calcular Gini global?

---

## FASE 2: PREGUNTAS DE INVESTIGACIÓN (DERIVADAS DE MANIFIESTOS)

| ID | Pregunta | Manifiesto | Métrica |
|----|----------|-----------|---------|
| P1 | ¿La atención sigue power law en todas las plataformas o difiere? | Radical §II | α por plataforma |
| P2 | ¿Hay correlación entre sentiment y engagement? | Inviabilidad §II | ρ(Sentiment, ER) |
| P3 | ¿Qué actores tienen más leverage sobre el sistema? | Inviabilidad §IV | Cook's Distance |
| P4 | ¿El prestigio (AFI) está inversamente correlacionado con producción (PPI)? | Inviabilidad §III-A | ρ(AFI, PPI) |
| P5 | ¿Hay diferencias significativas entre plataformas en desigualdad? | Radical §II | Gini por fuente |
| P6 | ¿Los super-hubs de cada plataforma tienen perfiles distintos? | Inviabilidad §III | Perfil vectorial por hub |

---

## FASE 3: ANÁLISIS Y VALIDACIÓN

- [ ] Responder cada pregunta con tests estadísticos
- [ ] Visualizaciones específicas por respuesta
- [ ] Interpretación textual marcada como "interpretación" (no como dato)

---

## FASE 4: DASHBOARD PROFESIONAL

- [ ] Refactorizar app.py con hallazgos de EDA
- [ ] Paneles por pregunta de investigación
- [ ] Selector de plataforma para comparación
- [ ] Exportable (PDF de reporte desde dashboard)

---

## FASE 5: ANÁLISIS LONGITUDINAL

- [ ] Múltiples ejecuciones del pipeline
- [ ] Tracks temporales de deriva de estado
- [ ] Detección de transiciones de fase en el tiempo

---

## PRÓXIMO PASO INMEDIATO
Completar Fase 0.2:
- Matriz de correlación
- Boxplots por plataforma
- Distribuciones separando huggingface del resto
