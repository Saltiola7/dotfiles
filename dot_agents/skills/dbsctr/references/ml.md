# ML / AI Reference Examples

Non-normative examples only. They do not create lifecycle gates; project
requirements, baselines, regulation, and ADRs set authoritative choices.

## Example thresholds and budgets

- A classifier may require macro F1 of at least `0.68`, per-tier precision of at
  least `0.70`, and no baseline regression greater than `0.02`.
- A batch may alert when feature-centroid cosine distance exceeds `0.10`, class
  distribution KL divergence exceeds `0.05`, or tier coverage changes by `30%`.
- An inference workflow may budget `$0.003` per item, `$2.00` per batch, two
  seconds average latency per item, and ten minutes total runtime.

## Example implementation choices

- Version data and artifacts with DVC; record the training Git SHA, seed, lock
  file, and container image digest.
- Validate structured LLM responses with Pydantic and reject unknown enum values.
- Use content-hash embedding caches; re-embed after source or embedding-model
  changes rather than mixing vector spaces.
- Retry transient provider failures up to three times with exponential backoff;
  fall back from one hosted model to another and mark output as degraded.
- A tiered classifier can use TF-IDF, embeddings, then an LLM, with deterministic
  assignment to exactly one tier.

## Example providers and tools

- Hosted models: Amazon Bedrock, Google Gemini, OpenAI.
- Classical ML: scikit-learn.
- Artifact and data tracking: DVC, Parquet.
- Evaluation and monitoring: project-selected harnesses and observability tools.
