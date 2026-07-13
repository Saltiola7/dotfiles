# Backlog — DBSCTR V3 Lifecycle

Discovery readiness: complete.

## Active

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| V3.7-1 | Lock inspection limits and interface policy | high | approved | ROADMAP-1 | V3.7 implementation policy | approved fixed-commit contract | no | selects concrete caps before code | small | scenario/contract review |
| V3.7-2 | Implement helper inspection interface | high | pending | V3.7-1 | `dbsctrctl` | lifecycle specs | no | shared helper surface | medium | helper tests |
| V3.7-3 | Add typed read-only adapter | high | pending | V3.7-2 | OpenCode tool/config | helper JSON | yes | exposes safe inspection | small | Bun build/control tests |
| V3.7-4 | Add security and compatibility evidence | high | pending | V3.7-2,V3.7-3 | tests | helper/tool | no | gates traversal and overlay safety | medium | affected test suite |
| V3.8-1 | Specify evidence schema and retention | high | pending | V3.7-4 | lifecycle specs | inspection contract | no | establishes evidence boundary | medium | scenario/contract review |
| V3.8-2 | Implement sanitized evidence sidecars | high | pending | V3.8-1 | `dbsctrctl` | Cycle Records | no | retains bounded evidence | large | helper tests |
| V3.8-3 | Test redaction and withheld content | high | pending | V3.8-2 | tests | helper output | no | prevents secret retention | medium | secret-canary tests |
| V3.8-4 | Add Python 1Password settings reference | medium | pending | V3.8-1 | Python reference | approved local pattern | yes | documents conditional project pattern | small | static contracts |
| V3.9-1 | Specify semantic audit classifications | high | pending | V3.8-3,V3.8-4 | lifecycle specs | V3.7/V3.8 | no | fixes report semantics | medium | scenario/contract review |
| V3.9-2 | Implement semantic audit orchestration | high | pending | V3.9-1 | audit skill/tool | fixed-commit inspection | no | traces claims without mutation | medium | audit smoke/tests |
| V3.9-3 | Test report-only authority boundaries | high | pending | V3.9-2 | tests | audit surfaces | no | prevents automatic rewriting | medium | affected test suite |
| V3.10-1 | Specify conditional Product Intent | medium | pending | V3.9-3 | Discovery/lifecycle specs | Engineering Profile | no | avoids synthetic product artifacts | medium | static contracts |
| V3.10-2 | Add generic Web/UI module | medium | pending | V3.10-1 | DBSCTR module | product/accessibility policy | no | adds UI lifecycle outcomes | medium | module tests |
| V3.10-3 | Add tool references and local MCP rule | medium | pending | V3.10-2 | Web/UI references | project authorities | yes | keeps examples non-normative | small | static contracts |
| V3.10-4 | Test conditional loading/accessibility | medium | pending | V3.10-2,V3.10-3 | tests | module/reference | no | gates applicability and defaults | medium | affected test suite |

## Completed

| id | outcome | completed | commit |
|---|---|---|---|
| V3-1–V3-15 | Implement and deploy DBSCTR V3 lifecycle | 2026-07-11 | `3151772` |
| V3-16 | Automate Gate Commits and Final Push | 2026-07-11 | `f7b11ca` |
| V3.1-1–V3.1-5 | Add deterministic V3.1 cycles and OpenCode integration | 2026-07-12 | `c9827e0` |
| V3.2-1–V3.2-5 | Add planned, ordered, monotonic cycle transitions | 2026-07-12 | `da65d0b`, `66df166`, `00c2950` |
| V3.3-1–V3.3-4 | Isolate concurrent worktree cycle state and delivery | 2026-07-12 | `d444950`, `7d80d21` |
| V3.4-1–V3.4-3 | Automate isolated cycle setup and safe cleanup | 2026-07-12 | `da4ddf8`, `2b4191a` |
| V3.5-1–V3.5-4 | Add typed OpenCode and Herdr execution adapters | 2026-07-12 | `d9a7363`, `9916235` |
| V3.6-1–V3.6-3 | Add fixed-commit lifecycle reconciliation audit | 2026-07-12 | `696971c`, `178bf26` |
| V3.6.1-1 | Correct integrated roadmap and stale-base delivery | 2026-07-12 | `02bcf34`, `1b75001` |
| V3.6.2-1 | Enforce begin authorization and correct Method Revision | 2026-07-12 | `95ef8ba` |
| ROADMAP-1 | Persist approved V3.7–V3.10 roadmap and boundaries | 2026-07-12 | `08cd102` |

Further roadmap implementation remains separately approved per milestone.
