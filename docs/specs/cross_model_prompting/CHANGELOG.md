# Changelog

## 2026-07-10

### Discovery

- Defined a shared GPT-5.6 and Opus 4.8 prompt core with OpenCode model adapters.
- Kept V1 skills frozen and excluded non-target models.
- Selected lean prompts, explicit boundaries, high-recall QA discovery, and
  representative validation as the optimization strategy.

### Contract

- Assigned workflow behavior to one shared prompt core and effort selection to
  `gpt` and `opus` OpenCode primary-agent adapters.
- Fixed GPT-5.6 at `medium` and Opus 4.8 at `xhigh` as initial effort baselines.
- Confirmed OpenCode's schema supports primary agents, models, and variants and
  its model registry exposes both selected model identifiers.

### Implementation

- Reduced managed global and V2 workflow prompts from 687 to 333 lines while
  preserving lifecycle, QA, DVC, delegation, safety, and artifact contracts.
- Added `gpt` and `opus` primary agents and retained the pending OpenAI timeout
  configuration.
- Changed QA to collect broadly before verification, deduplication, ranking, and
  gate decisions.

### Validation

- Rendered JSON passed `jq` assertions and `opencode debug config`.
- Both selected model identifiers were present in `opencode models`.
- V1 skill diffs were empty and source diff checks passed.
- Chezmoi dry-run showed only intended targets; apply completed with clean status
  and byte-matching deployed prompts and rendered config.
- Dependabot retrieval was unavailable because alerts are disabled for this
  repository; no dependencies changed in the affected scope.
