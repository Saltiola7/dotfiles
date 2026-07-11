## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)

## DBSCTR Project Adaptations

When running the DBSCTR pipeline in this repo, these project-specific conventions override or extend
the base SKILL.md guidance.

### Error Handling Pattern
- **Serve writes (CH-native tables):** fail-loud. Any error in `gsc_domain_serve` / `gsc_subdomain_serve`
  writes aborts the flow immediately.
- **Backed writes (ADLS exports):** soft-failure. Errors are logged + flow continues. CH serve data stays
  consistent. Pattern: `try/except → logger.error(ctx) → continue`.
- **Benchmark persistence:** soft-failure (same as backed writes). Flow completes even if ADLS write fails.
- **Validation gates (inline):** warn-only (do not halt nightly flow). Full validation runs in a
  separate weekly benchmark flow.

### Contract Implementation Convention
- **Pydantic manifest:** `lib/src/seolib/config/prefect_infra.py` → `GscBackedConfig` + `BackedDataset`.
  Single source of truth for dataset versions, ADLS coordinates, destination config.
- **CH SQL asserts:** Post-insert validation in `gsc_dedup_serve_refresh.py` → `validate_refresh` task
  (rows > 0 AND nonzero impressions > 0). Raises ValueError on failure.
- **Validation module:** `lib/src/seolib/gsc_benchmark/` — 8 validators, composite scorer, constants
  with thresholds. All validation logic lives here (not in flows or notebooks).
- **Schema contracts:** DDL files in `iac/assets/gsc/backed_ddl/` are the ground truth.

### Domain Type Convention
- Domain types live in `_domain.py` within each package:
  - `lib/src/seolib/gsc_benchmark/_domain.py` — `ValidationResult`, `CompositeScore`, `GscValidationReport`
  - `flows/gsc/_backed_domain.py` — `BackedTarget`, `ExportDataset`, `ExportDestination`
- Use `@dataclass` for simple value objects; `pydantic.BaseModel` for config/manifest types.
- Enum members = uppercase (e.g. `ExportDestination.ADLS`).

### Testing Convention
- **pytest only.** No pytest-xdist (ADR-011 — Prefect test harness is incompatible).
- Test location mirrors source: `tests/flows/gsc/`, `tests/lib/gsc_benchmark/`.
- Run: `uv run pytest tests/flows/gsc/ tests/lib/gsc_benchmark/ -q --tb=short`
- 92+ tests currently pass. All tests must pass before any phase commit.
- Fixtures for CH client use mocks (no live DB in tests).

### Spec Location
- GSC dedup: `docs/specs/gsc_deduplication/README.md`
- GSC backed (ADLS export): `docs/specs/gsc_backed/README.md`
- Both are directory-format specs (README + BACKLOG + CHANGELOG).

### ADRs
- `docs/adr/` — 20 ADRs. Key ones for GSC:
  - ADR-016: ClickHouse-as-writer backed-table export
  - ADR-017: GSC backed rename and fill-only
  - ADR-018: HIVE-partitioned backed tables (historical; now flat layout on CH 26.2)

## QA Toolchain

Use the project's configured `uv`, Ruff, mypy, pytest, coverage, Hypothesis,
pre-commit, and CI commands as the QA toolchain. Scope routine gates to affected
code; do not treat passing mypy as complete evidence where modules suppress
errors. When project artifacts declare JFrog Xray authoritative, use it as the
sole vulnerability gate rather than adding a competing scanner.
