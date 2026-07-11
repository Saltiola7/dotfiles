# OpenCode Control Plane Changelog

## 2026-07-11 — Discovery

- Approved provider-neutral workflow commands and provider-affine delegation.
- Kept OpenCode Bedrock Claude and raw LM Studio.
- Approved complete removal of Claude Code, Meridian, Headroom, OMO, and their
  historical project documentation and machine state.
- Approved OpenCode-only skill curation and removal of Claude-specific or
  Anthropic-dependent Caveman skills.
- Required Graphify preservation with a freshness/relevance fallback and no
  duplicate project plugin.
- Set Discovery2 confidence to 99%.

## 2026-07-11 — Implementation

- Made workflow commands inherit the selected primary and aligned Plan/Build
  permissions with the approved autonomy boundary.
- Denied direct Anthropic provider use while preserving Bedrock Claude and raw
  LM Studio.
- Removed Claude Code, Meridian, Headroom, OMO, incompatible skills, packages,
  services, authentication, state, wrappers, providers, and historical docs.
- Made the skills CLI the sole owner of its mutable lock and constrained installs
  to the curated OpenCode set.
- Refreshed Graphify's global skill to 0.8.46, retained both Git hooks and query
  behavior, and removed the duplicate project integration.
- Added seven focused control-plane contract tests; all passed.
- Live Plan and Build-GPT probes passed. Build-Claude resolved to Bedrock Opus
  but its live request was blocked by an expired AWS SSO token; model listing and
  resolved provider-affinity assertions passed as next-best evidence.
