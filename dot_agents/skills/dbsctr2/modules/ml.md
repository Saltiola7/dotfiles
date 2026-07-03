# DBSCTR2 Domain Module: ML / AI

**Applies when:** Task involves ML model training or serving, LLM calls (Bedrock, Gemini, OpenAI),
embeddings, classification pipelines, feature engineering, eval harnesses, or AI-powered analysis.

This module extends Phases 1 and 4 of core DBSCTR2 with ML/AI-specific patterns.
Covers both classical ML (scikit-learn, custom models) and LLM-as-external-source (API-based).

---

## Phase 1 Extensions (Domain)

### ML Domain Concepts

Name these explicitly in the bounded context:

| Concept | Definition | Example |
|---------|-----------|---------|
| **Feature** | Input signal to a model/classifier | `keyword_embedding` (3072-dim Gemini vector) |
| **Label** | Ground-truth classification or target | Taxonomy node assignment (verified by human) |
| **Prediction** | Model output before acceptance | LLM-assigned category before confidence check |
| **Confidence** | Score indicating prediction reliability | Cosine similarity to taxonomy centroid |
| **Threshold** | Decision boundary for accept/reject/escalate | Embedding tier: 0.60 (sweep-validated) |
| **Tier** | Processing level in a waterfall/cascade | TF-IDF → Embedding → LLM (cost-ordered) |
| **Eval metric** | Acceptance criterion for model quality | F1 ≥ 0.68, Precision ≥ 0.70 |
| **Drift** | Distribution shift in features or predictions | Embedding centroid shift > 0.1 cosine distance |

### Model Lineage

Document the full path from raw data to served predictions:

```
Training lineage:
  source: ClickHouse default.gsc (query strings)
    → feature: Gemini text-embedding-004 (3072 dims)
    → training: scikit-learn TF-IDF + centroid computation
    → artifact: centroids.parquet (DVC-tracked, versioned)
    → serve: classification pipeline (embedding similarity lookup)

Inference lineage:
  input: new keyword batch (from KPE extraction)
    → tier 1: TF-IDF dual-matrix (threshold 0.85) → classified subset
    → tier 2: Embedding cosine (threshold 0.60) → classified subset
    → tier 3: LLM batch (Bedrock Opus) → remaining
    → validation: EVoC cluster disagreement check
    → output: ClickHouse kw_classifications table
```

### Tiered Architecture Pattern

When a single model approach fails on cost, accuracy, or latency — use a waterfall:

```
Tier design:
  tier 1: [cheap, fast, handles easy cases] → threshold → classified
  tier 2: [moderate cost, handles medium cases] → threshold → classified
  tier 3: [expensive, handles hard cases] → all remaining
  validation: [cross-check tier assignments for disagreements]

Per-tier contract:
  - Input: what falls through from prior tier
  - Threshold: decision boundary (document how derived — sweep, heuristic, etc.)
  - Output: classified subset + confidence scores
  - Cost: $ per item at this tier
  - Coverage: % of total items handled by this tier
```

**Rule:** Tier assignment must be deterministic — a given input goes to exactly one tier.

### Reproducibility Requirements

Document these in Phase 1 for any ML component:

| Requirement | Implementation |
|-------------|---------------|
| **Data version** | DVC-tracked datasets; `data.dvc` pins exact version |
| **Code version** | Git SHA at training time recorded in model metadata |
| **Random seed** | Fixed seed for all stochastic operations (split, init, sampling) |
| **Dependency pins** | `uv.lock` / `requirements.txt` for exact package versions |
| **Environment** | Docker image SHA or explicit Python version + platform |

---

## Phase 4 Extensions (Contract)

### Feature Contracts

Define expected properties of model inputs:

```python
class FeatureContract:
    """Contract for keyword embedding features."""
    dimensions: int = 3072           # Gemini text-embedding-004 output
    dtype: str = "float32"           # precision
    norm: str = "unit"               # L2-normalized (cosine = dot product)
    null_policy: str = "reject"      # no null embeddings allowed
    staleness: str = "≤ 30 days"     # re-embed if source text changed > 30 days ago
```

| Check | Implementation |
|-------|---------------|
| **Dimension match** | Assert vector length == expected before any computation |
| **Null/NaN rejection** | No null vectors enter the pipeline; fail at ingestion |
| **Normalization** | Assert L2 norm ≈ 1.0 for cosine-based lookups |
| **Staleness** | Re-compute embeddings when source content changes (content-hash trigger) |

### Eval Threshold Contracts (Acceptance Gates)

A model or prompt change MUST pass eval before deployment:

| Gate | Metric | Threshold | Action on breach |
|------|--------|-----------|-----------------|
| **Classification accuracy** | F1 (macro) | ≥ 0.68 | Block deployment |
| **Per-tier precision** | Precision per tier | ≥ 0.70 | Alert + review |
| **Regression check** | F1 delta from baseline | ≥ −0.02 | Block deployment |
| **Coverage** | % items classified (not "unknown") | ≥ 0.95 | Alert |
| **Cost ceiling** | $ per batch run | ≤ $2.00 | Block (escalate to Tier 3 budget) |

**Rule:** Eval runs on a held-out ground-truth set (versioned, reviewed, never used for training).
Document GT set version, size, and last review date in the spec.

### Drift Contracts

Detect when the model's world has changed:

| Signal | Detection | Threshold | Action |
|--------|-----------|-----------|--------|
| **Feature drift** | Centroid shift (cosine distance between current vs baseline centroid) | > 0.10 | Alert + re-evaluate |
| **Prediction drift** | Distribution of predicted classes shifts vs baseline | KL divergence > 0.05 | Alert + investigate |
| **Volume anomaly** | Items-per-tier ratio shifts significantly | ±30% of historical ratio | Alert |
| **Confidence drift** | Mean confidence score drops | > 0.05 from baseline mean | Re-train signal |

**Rule:** Drift detection runs on every batch. Baseline is the eval run's distribution.

### LLM-as-External-Source Contracts

Treat every LLM API call as an external data source with contracts:

#### Input Contract (Prompt)

| Aspect | Contract |
|--------|----------|
| **Prompt template** | Versioned (git-tracked); changes require eval gate |
| **Input schema** | Structured input variables with types and constraints |
| **Context window** | Max tokens documented; truncation strategy explicit |
| **System prompt** | Immutable per-version; changes = new model version |

#### Output Contract (Response)

| Aspect | Contract |
|--------|----------|
| **Response schema** | Pydantic model for structured output; validate before use |
| **Allowed values** | Enum constraints (e.g., category ∈ taxonomy nodes) |
| **Null handling** | What happens when LLM returns unexpected/empty/malformed output |
| **Confidence extraction** | How confidence is derived (LLM self-report vs embedding proxy) |

Example:
```python
class ClassificationResponse(BaseModel):
    """LLM classification output contract."""
    category: str           # must exist in taxonomy (referential contract)
    confidence: float       # 0.0-1.0 (LLM self-reported or embedding-derived)
    reasoning: str | None   # optional chain-of-thought

    @field_validator("category")
    def must_be_valid_taxonomy_node(cls, v):
        if v not in TAXONOMY_NODES:
            raise ValueError(f"Unknown taxonomy node: {v}")
        return v
```

#### Cost & Latency Contracts

| Metric | Contract | Action on breach |
|--------|----------|-----------------|
| **Cost per item** | ≤ $0.003 per keyword (Tier 3 LLM) | Batch more aggressively / switch model |
| **Cost per run** | ≤ $2.00 total (all tiers combined) | Halt if budget exceeded |
| **Latency per item** | ≤ 2s average (Tier 3) | Increase concurrency or switch model |
| **Total run time** | ≤ 10 min for full pipeline | Profile bottleneck tier |
| **Token usage** | Track input + output tokens per run | Alert on >20% increase (prompt bloat) |

#### Reliability Contracts

| Pattern | Implementation |
|---------|---------------|
| **Retry with backoff** | Transient API errors (429, 500, 503): retry 3x with exponential backoff |
| **Fallback model** | If primary (Opus) unavailable, fall back to Sonnet with degraded-quality flag |
| **Rate limiting** | Respect provider rate limits; ThreadPoolExecutor with bounded concurrency |
| **Timeout** | Per-request timeout (30s); per-batch timeout (10min) |
| **Determinism caveat** | LLM outputs are non-deterministic; eval must account for variance |

### Embedding Contracts

| Contract | Rule |
|----------|------|
| **Model version pinning** | Document exact embedding model (e.g., `text-embedding-004`); model change = re-embed all |
| **Dimension stability** | Output dimension is invariant; assert before any vector operation |
| **Caching** | Embeddings are expensive; cache by content-hash; invalidate on source change |
| **Batch efficiency** | Batch embedding calls (not one-by-one); document optimal batch size |
| **Storage format** | Parquet with fixed-size-list column; DVC-tracked for large datasets |

### Training Contracts (Classical ML)

| Contract | Rule |
|----------|------|
| **Train/test split** | Fixed seed, documented split ratio, stratified if class-imbalanced |
| **Hyperparameter bounds** | Document search space and selection criterion |
| **Convergence** | Training must converge (loss decreasing); alert on non-convergence |
| **Artifact versioning** | Model artifacts DVC-tracked; metadata includes git SHA + data version |
| **Retraining trigger** | Drift exceeds threshold OR new GT available OR schema change |

---

## Rules (ML / AI)

- Every model/classifier has an eval gate: metric ≥ threshold, tested on versioned GT set
- LLM prompt changes are model version changes — require eval before deployment
- Confidence scores use embedding proximity (cosine to centroid), NOT LLM self-reported confidence
- Tiered architectures assign items deterministically; document tier-assignment logic explicitly
- Cost estimation (dry-run mode) is mandatory for LLM-calling pipelines before full execution
- Feature contracts assert dimension, dtype, normalization, and staleness before computation
- Drift detection runs on every batch; baseline is pinned to last eval run
- Reproducibility: data version (DVC) + code version (git SHA) + seed + deps (lock file) documented per model
- Ground-truth sets are versioned, reviewed by humans, and never used for training
- LLM response validation uses Pydantic structured output; malformed responses are rejected (not silently ignored)
- Embedding model changes require full re-embedding — no mixing vectors from different models
- ThreadPoolExecutor concurrency bounded by API rate limits; document max workers per provider
- Fallback models have a degraded-quality flag propagated to downstream consumers
- ADRs required for: model architecture changes, provider switches, threshold re-calibration, taxonomy evolution

---

## Worked Example: Tiered Keyword Classification

```
# Domain (Phase 1)
Input: 7,310 non-branded keywords (from KPE extraction)
Taxonomy: 287-node hierarchy (L1 → L2 → L3 leaves)
Tiers: TF-IDF (fast/free) → Embedding (moderate/free) → LLM (expensive)
Features: Gemini text-embedding-004, 3072 dims, L2-normalized
GT set: 511 re-verified labels (v10), human-reviewed
Output: ClickHouse kw_classifications (keyword, taxonomy_path, confidence, tier)

# Contracts (Phase 4)
Feature: 3072 dims, float32, unit-normalized, no nulls
Thresholds: TF-IDF 0.85 (heuristic), Embedding 0.60 (sweep-validated), LLM = all remaining
Eval gate: F1 ≥ 0.68 macro on 511 GT labels; precision ≥ 0.70 per tier
Cost: ≤ $1.80/run total (TF-IDF $0, Embedding $0, LLM ~$1.80 for ~2,700 items)
Tier coverage: TF-IDF ~2%, Embedding ~62%, LLM ~36%
Determinism: tier assignment based on threshold — keyword goes to exactly one tier
Drift: monitor tier-coverage ratios; alert if shifts > 30%
Confidence: cosine similarity to assigned taxonomy centroid (NOT LLM self-report)
Reproducibility: centroids.parquet (DVC), taxonomy.json (git), seed=42, uv.lock
ADR: ADR-003 (tiered classification architecture)
```

## Worked Example: LLM-Powered Content Analysis

```
# Domain (Phase 1)
Input: Article body text (from crawl HTML extraction)
Model: Bedrock Claude (primary) / Gemini (fallback)
Output: Factual analysis annotations (claims, evidence, staleness signals)
Topology: Fan-out (1 article → N annotations)

# Contracts (Phase 4)
Input contract: body text ≤ 100K tokens; truncate with overlap if exceeded
Output contract: Pydantic AnnotationResult (claims: list[Claim], staleness_tier: StalenessTier)
Allowed values: StalenessTier ∈ {FRESH, AGING, STALE, CRITICAL}
Cost: ≤ $0.05 per article (estimate via dry-run token counting)
Latency: ≤ 30s per article; timeout at 60s
Reliability: retry 3x on transient errors; fallback to Gemini if Bedrock unavailable
Concurrency: 3 workers (Bedrock rate limit); 8 workers (Gemini)
Eval: Manual review of 50 annotated articles; precision ≥ 0.80 for claim extraction
Prompt versioning: templates/factual_analysis_v3.txt (git-tracked, changes require re-eval)
Degraded mode: Gemini fallback produces annotations with `source: "fallback"` flag
```
