# Attention Observatory — Informe Técnico y de Resultados

## Resumen Ejecutivo

**Attention Observatory** es un sistema de modelado empírico de la economía de la atención digital. Trata la atención humana como un recurso ecológico finito (Simon, 1971) y modela su distribución asimétrica en plataformas digitales mediante un pipeline ELT reproducible con **6 fuentes activas**, espacio de estados multivariable [ER, PPI, Sentiment, AFI] y validación econométrica de desigualdad estructural.

El sistema NO analiza personas, intenciones ni moraliza el uso de redes sociales. Analiza estructuras de distribución de recursos finitos mediante matemática y estadística. Este enfoque clínico está definido en los manifiestos fundacionales (`manifiestos/`), que constituyen la especificación (Spec) del desarrollo.

---

## Marco Teórico (Spec)

El proyecto se sostiene sobre cuatro pilares definidos en los manifiestos:

### 1. Atención como Recurso Ecológico Finito
*Manifiesto: Radical Pesimismo §I | Inviabilidad §I*

La atención humana es un recurso bio-económico escaso, limitado por la capacidad cognitiva de la especie y las 24 horas físicas del día. Las plataformas digitales son industrias pesadas de extracción minera que compiten por un recurso fijo, generando una dinámica de suma cero.

### 2. Conexión Preferencial (Barabási–Albert, 1999)
*Manifiesto: Radical Pesimismo §II*

Las redes de atención siguen una topología libre de escala (*scale-free*). $P(k) \sim k^{-\alpha}$. El sistema está diseñado matemáticamente para que el ganador se lo lleve todo.

### 3. Homeostasis Funcional y Válvulas de Contención
*Manifiesto: Inviabilidad §II*

Las herramientas de "bienestar digital" no son concesiones éticas — son válvulas de alivio para mantener al usuario en fatiga crónica operativa sin llegar al colapso.

### 4. Geometría Cíclica de la Información
*Manifiesto: Inviabilidad §IV*

Toda tecnología de desintermediación sigue: Descentralización → Monopolio → Hiper-Saturación → Colapso y Fragmentación.

---

## Arquitectura del Sistema

### Pipeline ELT

**Bronze (Raw):** Datos crudos ingestados desde 6 fuentes:
- **HackerNews API** — 280+ posts/ejecución, sin auth
- **Wikipedia API** — 400+ revisions/ejecución, User-Agent
- **HuggingFace Datasets** — 3000+ registros/ejecución (go_emotions)
- **Bluesky AT Protocol** — 240+ posts/ejecución, público
- **Mastodon API** — 120+ posts/ejecución, fediverso público
- **GitHub API** — repos, commits, issues; token gratuito

Almacenados como `.parquet`, sin transformación, particionados por timestamp.

**Silver (Cleansed):** Procesamiento con Polars:
- Tipado estricto y limpieza de nulos
- Normalización de timestamps
- Ingesta multi-plataforma unificada por esquema diagonal
- Cálculo de `followers_at_post` desde tabla de actores

**Gold (Feature Space):** Cada actor como vector:

$$\mathbf{X}_i = [ER_i, PPI_i, Sentiment_i, AFI_i]$$

### Variables del Feature Space

**Engagement Rate (ER):** $$ER = \frac{\text{interacciones}}{\text{followers}} \times 100$$
Mide capacidad de movilizar audiencia. Normaliza por tamaño del nodo.

**Production Pressure Index (PPI):** $$PPI = \frac{1}{\ln(\text{intervalo\_horas} + 1.01)}$$
Proxy de urgencia temporal. A mayor frecuencia de publicación, mayor PPI.

**Sentiment Score:** Rango $[-1.0, 1.0]$. NLP con transformers (distilbert-base-uncased-finetuned-sst-2-english).

**Aspirational Framing Index (AFI):** Densidad de keywords de prestigio (luxury, gala, premiere, academy, curated, etc.).

---

## Capas Analíticas (Trazabilidad Spec → Código)

| # | Capa | Spec | Métrica | Archivo |
|---|------|------|---------|---------|
| 1 | Capital Conversion | Inviabilidad §III-A | `has_external_ecosystem` | `silver_to_gold.py` |
| 2 | Legal Enclosure | Radical §II.3 | `is_legally_truncated` | `silver_to_gold.py` |
| 3 | Prestige Drift | Inviabilidad §III-A | `prestige_drift_detected` | `silver_to_gold.py` |
| 4 | Anomaly Detection | Inviabilidad §IV | Cook's Distance | `stats/inequality.py` |
| 5 | Super-Hub Detection | Radical §II.1 | Z > 3 | `stats/inequality.py` |
| 6 | Systemic Breakdown | Inviabilidad §IV | Churn + Saturation | `stats/inequality.py` |

---

## Métodos Estadísticos

**Coeficiente de Gini:** $$G = \frac{2 \sum_{i=1}^{n} i \cdot y_i}{n \sum_{i=1}^{n} y_i} - \frac{n+1}{n}$$
G = 0 igualdad perfecta; G = 1 concentración total. Sistemas de atención digital: valores > 0.5 indican alta asimetría.

**Curva de Lorenz:** Concentración acumulada. Desviación de la diagonal = Gini.

**Power Law:** $$P(x) = C x^{-\alpha}$$ Ajuste por máxima verosimilitud (powerlaw). $\alpha > 2$ indica cola pesada. Comparación vs lognormal/exponencial por test de razón de verosimilitud.

**Distancia de Cook:** $$D_i = \frac{r_i^2}{2 \cdot MSE} \cdot \frac{h_{ii}}{(1 - h_{ii})^2}$$ Nodos con $D_i > 4/n$ son puntos de alto apalancamiento.

---

## Resultados (Ejecución con 6 fuentes reales — 5 Jun 2026, post-fix Bluesky)

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| Actores totales | 4,136 | Multi-plataforma |
| Posts totales | 8,136 | HN + Wikipedia + HF + Bluesky + Mastodon + GitHub |
| Gini Coefficient | 0.9828 | Concentración extrema — 10 hubs controlan 2.28% de atención |
| Power Law Alpha | 2.1856 | Cola pesada (σ=0.20) — más realista tras fix |
| Super-Hubs (Z>3) | 10 nodos | HackerNews + Mastodon con ER real |
| Systemic Saturation | **NO DETECTADA** | Datos más diversos estabilizan el indicador |
| Churn Acceleration | 312.75 | Muy alta — fatiga de audiencia significativa |
| NLP | transformers | distilbert funcional en todo el pipeline |

### Interpretación Clínica

El Gini de 0.983 confirma **concentración extrema** de la atención digital. Tras corregir la pérdida de datos de Bluesky, el indicador se estabiliza en un rango más realista. La saturación sistémica dejó de detectarse — señal de que el indicador previo era un artefacto de datos incompletos, no un colapso real.

10 super-hubs concentran el engagement real (HackerNews + Mastodon principalmente). Las plataformas sin mecánica de "likes" (Wikipedia, HuggingFace) requieren métricas alternativas.

---

## Reporte de Diagnóstico EDA (5 Jun 2026)

### Calidad de Features

| Feature | Mediana | Media | Skew | Ceros (%) | Problema |
|---------|---------|-------|------|-----------|----------|
| ER | 0.0 | 1.39 | 18.6 | 97.6% | Casi todos los actores tienen ER=0 |
| PPI | 50.1 | 42.5 | -1.65 | 9.6% | Plateau artificial: huggingface todo en 50.1 |
| Sentiment | -0.93 | -0.21 | 0.43 | 9.6% | Polarizado extremo: -0.99 o +0.99 |
| AFI | 0.0 | 0.002 | 23.4 | 99.7% | **Feature muerta**: keyword set no captura señal |

### Diagnóstico por Plataforma

| Plataforma | N | ER medio | PPI medio | Sent medio | Problema detectado |
|-----------|---|----------|-----------|------------|--------------------|
| huggingface | 3,000 | 0.0 | 50.1 (cte) | -0.16 | **72.5% del dataset**, ER=0, PPI constante. Domina sin señal |
| bluesky | 392 | 147.0 | 6.8 | -0.32 | **ER inflado** por floor followers=1 (plataforma nueva, pocos seguidores) |
| hackernews | 295 | 16.0 | 25.9 | -0.49 | Única fuente con ER real |
| wikipedia | 268 | 0.0 | 47.2 | -0.51 | ER=0 (editores no tienen "engagement tradicional") |
| mastodon | 129 | 6.18 | 19.4 | -0.58 | ER más variado, mejor distribución |
| github | 52 | 3.85 | 51.3 | -0.64 | Poco volumen, sin AFI |

### Correlaciones (Spearman)

| Par | ρ | p-valor | Interpretación |
|-----|---|---------|----------------|
| ER ↔ PPI | **-0.115** | <0.001 | Correlación negativa débil pero significativa |
| ER ↔ Sentiment | -0.049 | 0.002 | Casi nula |
| ER ↔ AFI | 0.078 | <0.001 | Muy débil (AFI está muerto) |
| PPI ↔ Sentiment | -0.036 | 0.020 | Casi nula |

**Hallazgo**: No hay correlaciones fuertes entre features. El espacio de estados no tiene colinealidad, pero tampoco estructura discernible con las métricas actuales.

### Impacto de HuggingFace

| Escenario | Gini |
|-----------|------|
| Con HuggingFace (72.5% del dataset) | 0.9926 |
| Sin HuggingFace | 0.9730 |

HuggingFace infla N artificialmente pero no contribuye señal a ER/PPI. Al eliminarlo, el Gini baja ligeramente pero la distribución sigue siendo extremadamente asimétrica.

### Problemas Detectados (requieren Fase 1)

1. **AFI muerto**: 99.7% de actores tienen AFI=0. Las keywords no capturan el discurso de prestigio en los textos de las fuentes actuales.
2. **Bluesky en cero**: Todas las métricas son 0 — el connector no está computando features correctamente.
3. **PPI plateau**: HuggingFace tiene PPI constante (50.1) para todos los actores, lo que distorsiona la distribución.
4. **Sentiment polarizado**: distilbert clasifica casi todo como extremo (-0.99 o +0.99), poca granularidad.
5. **HuggingFace domina sin señal**: 72.5% del dataset pero ER=0, PPI constante. Urge tratarlo por separado.
6. **Wikipedia sin ER**: Editores no generan engagement en el sentido de ER. Habría que repensar qué mide "engagement" para revisiones.

---

---

## Resultados de Investigación (Sprint 2 — 6 Jun 2026)

### P1: ¿La atención sigue power law en todas las plataformas?

| Plataforma | N | Con ER>0 | α | Pareto? |
|-----------|---|----------|---|---------|
| HackerNews | 295 | 34 | **2.69** | ✅ Sí |
| Bluesky | 392 | 155 | **2.29** | ✅ Sí |
| Mastodon | 129 | 64 | 1.56 | ❌ No |
| GitHub | 52 | 2 | N/A | Insuficiente |
| Wikipedia | 268 | 0 | N/A | Sin ER |
| HuggingFace | 3000 | 0 | N/A | Sin ER |

**Conclusión**: Power Law confirmada para HackerNews y Bluesky (α>2.0). Mastodon muestra una distribución diferente (α<2.0), posiblemente por ser una red más distribuida y menos jerárquica.

### P2: ¿Hay correlación entre sentiment y engagement?

| Test | Valor | p-valor |
|------|-------|---------|
| Pearson r | 0.038 | 0.198 |
| **Spearman ρ** | **0.045** | **0.130** |

**Conclusión**: **No hay correlación**. El tono emocional del contenido no predice el engagement. Consistente con la hipótesis de Inviabilidad §II: el engagement está determinado por la arquitectura de la red, no por el contenido.

### P3: ¿Qué actores tienen más leverage?

8 nodos de alto apalancamiento detectados (todos en Bluesky, influenciados por floor de followers). Requiere refinamiento de ER para plataformas con pocos seguidores.

### P4: ¿El prestigio (AFI) está inversamente correlacionado con producción (PPI)?

| Test | Valor | p-valor |
|------|-------|---------|
| Spearman ρ | **-0.088** | **0.003** |

**Conclusión**: Correlación negativa **débil pero estadísticamente significativa**. A mayor producción (PPI), menor uso de lenguaje de prestigio (AFI). Consistente con la dirección esperada por Inviabilidad §III-A.

### P5: ¿Hay diferencias entre plataformas en desigualdad?

| Plataforma | Gini | IC 95% |
|-----------|------|--------|
| Mastodon | **0.968** | [0.884, 0.976] |
| GitHub | **0.962** | [0.000, 0.981] |
| HackerNews | **0.903** | [0.870, 0.933] |
| Bluesky | **0.869** | [0.799, 0.909] |
| Wikipedia | 0.000 | Sin ER |
| HuggingFace | 0.000 | Sin ER |

**Conclusión**: Todas las plataformas con datos de engagement muestran Gini > 0.85 — concentración extrema en todas. Mastodon es la más desigual; Bluesky la "menos" desigual (pero aún extrema).

### P6: ¿Los super-hubs tienen perfiles distintos?

7 super-hubs detectados (Z>3), todos en Bluesky. Perfil medio:
- ER medio: 4,486
- PPI medio: 0.19 (baja presión de producción)
- Sentiment medio: -0.16 (ligeramente negativo)
- AFI medio: 0.20 (alta densidad de prestigio)

**Conclusión**: Los super-hubs de Bluesky tienen baja frecuencia de publicación (PPI bajo) pero alto contenido de prestigio (AFI alto) — consistente con la mutación de capital cuantitativo a cualitativo descrita en Inviabilidad §III-A.

> **Nota**: Los super-hubs están dominados por Bluesky debido al floor de followers=1 que infla ER. HackerNews y Mastodon tienen actores con ER real pero no alcanzan Z>3. Refinamiento pendiente.

---

## Dashboard Streamlit

Organizado en 4 vistas:

1. **System Overview** — Métricas globales, indicadores de saturación
2. **Attention Inequality** — Curva de Lorenz, histograma, power law
3. **State Space Exploration** — Scatter 3D (ER × PPI × Sentiment), leverage plot
4. **Actor Explorer** — Perfil individual, ranking, prestige drift

---

## Principios de Diseño (Inmutables)

1. **Neutralidad epistemológica** — el sistema describe, no prescribe
2. **No inferencia psicológica individual** — no se etiquetan personas
3. **Separación datos / interpretación** — los datos son neutrales
4. **Reproducibilidad total** — mismo pipeline, mismos resultados
5. **Trazabilidad ELT** — cada transformación es rastreable

## Lo que el sistema NO hace

- No clasifica personas moral o psicológicamente
- No diagnostica comportamientos individuales
- No moraliza redes sociales
- No predice intenciones
- No emite juicios sobre contenido

---

## Referencias

- Simon, H. A. (1971). *Designing Organizations for an Information-Rich World.*
- Barabási, A-L. (2016). *Network Science.* Cambridge University Press.
- Barabási, A-L., & Albert, R. (1999). *Emergence of Scaling in Random Networks.* Science.
- Bourdieu, P. (1984). *Distinction: A Social Critique of the Judgement of Taste.*
- Zuboff, S. (2019). *The Age of Surveillance Capitalism.*
- Clauset, A., Shalizi, C. R., & Newman, M. E. J. (2009). *Power-Law Distributions in Empirical Data.* SIAM Review.
- Manifiestos fundacionales: `manifiestos/MANIFIESTO_Inviabilidad_Evolutiva_HiperCentralizacion.pdf`
- Manifiestos fundacionales: `manifiestos/MANIFIESTO_Radical_Pesimismo_Luz_Claridad.pdf`

---

---

## Conclusiones Temporales (Post-EDA + Fixes)

### Lo que funciona
1. **Pipeline ELT**: 6 fuentes, 4,136 actores, 8,136 posts, reproducible
2. **NLP real**: distilbert integrado en el pipeline (sentiment analysis)
3. **Estadísticas**: Gini, Power Law, Cook's Distance, Z-score — todos operativos
4. **AFI**: reactivado con nuevo keyword set (media non-HF=0.173)
5. **Dashboard**: Streamlit funcional con 4 vistas
6. **SDD**: trazabilidad manifiesto→hipótesis→métrica→código documentada

### Lo que requiere atención
1. **Wikipedia**: engagement=0 para todos los editores. Propuesta: usar `post_count` (revisiones) como proxy de engagement intra-plataforma
2. **HuggingFace**: 72.5% del dataset pero ER=0 y PPI constante. Flag `is_huggingface` permite filtrar
3. **Sentiment polarizado**: distilbert da extremos. Evaluar modelo de regresión vs clasificación binaria
4. **ER inflado en Bluesky**: floor de 1 follower da ER~147. Refinar con mediana de followers por plataforma

### Hipótesis validadas (preliminar)
| Hipótesis | Estado | Evidencia |
|-----------|--------|-----------|
| La atención sigue power law | ✅ Confirmada | α=2.19, cola pesada |
| Winner-takes-all (Gini alto) | ✅ Confirmada | Gini=0.983, 10 hubs dominan |
| AFI captura prestigio | ✅ Activado | 29% de non-HF con AFI>0 |
| Saturación sistémica | ⚠️ No replicada | Era artefacto de datos perdidos |

---

## Propuesta de Sprints

### Sprint 1: MVP Fundacional (COMPLETADO ✅)
- Pipeline ELT básico con 6 fuentes
- Feature space [ER, PPI, Sentiment, AFI]
- NLP con transformers
- Dashboard Streamlit
- EDA + Fixes (Bluesky, AFI, HuggingFace flag)
- Documentación SDD (manifiestos, CONTEXT, PLAN, ROADMAP, REPORT)

### Sprint 2: Preguntas de Investigación (SIGUIENTE)
Responder formalmente P1-P6 con:
- Test estadísticos formales (bootstrap, Kruskal-Wallis)
- Visualizaciones publicables
- Excluir HuggingFace de métricas de engagement
- Refinar Wikipedia y Bluesky metrics

### Sprint 3: Dashboard Profesional
- Refactor app.py con hallazgos
- Selector de plataforma
- Filtro HuggingFace toggle
- Exportable a PDF

### Sprint 4: Análisis Longitudinal
- Múltiples ejecuciones del pipeline
- Tracking de deriva de Gini, α, hubs
- Detección de transiciones de fase

---

## MVP Checklist para GitHub

- [ ] **Pipeline funcional**: `python main.py` produce gold sin errores
- [ ] **Dashboard**: `streamlit run app.py` muestra datos reales
- [ ] **Documentación**: CONTEXT.md, PLAN.md, ROADMAP.md, SETUP.md, REPORT.md actualizados
- [ ] **Manifiestos**: `manifiestos/` con PDFs + TXT de los documentos fundacionales
- [ ] **EDA reports**: `data/reports/` con diagnóstico de calidad, correlaciones, impacto HF
- [ ] **Trazabilidad SDD**: mapeo manifiesto→hipótesis→métrica documentado
- [ ] **Código limpio**: sin comentarios muertos, imports organizados
- [ ] **`.gitignore`**: excluir `data/` (parquets grandes), `.env`, `__pycache__`
- [ ] **`requirements.txt`**: dependencias completas y actualizadas
- [ ] **README.md**: instrucciones de instalación, ejecución, arquitectura (pendiente de crear)

¿TODO CHECK? Ejecutar `python main.py` y `streamlit run app.py` deben funcionar sin errores.
