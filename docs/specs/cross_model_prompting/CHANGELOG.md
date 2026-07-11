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
