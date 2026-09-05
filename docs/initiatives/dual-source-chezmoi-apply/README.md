# Dual-Source Chezmoi Apply

This Initiative makes the Mac mini's normal full plain `chezmoi apply` converge
both independently owned local sources in deterministic order. The personal
source remains the default and owns the bridge. `Saltiola7/dotfiles-ai` remains
the exclusive owner of AI configuration and supplies an already-supported
dedicated chezmoi config.

## Context Map

| Context | Repository | Responsibility |
|---|---|---|
| `shell_auth_startup` | `Saltiola7/dotfiles` | Default source, bridge ordering, source checks, failure propagation, and user-facing apply result |
| `dotfiles_ai_distribution` | `Saltiola7/dotfiles-ai` | Existing independent secondary source/config, AI target ownership, and rolling Codex update behavior; read-only dependency |

The operator approved this context map on 2026-09-05. No PM Kernel ticket is
created or required.

## Delivery

One elevated-risk DBSCTR Build cycle, `dual-source-apply-bridge`, is sufficient.
It changes only the personal repository. The secondary repository needs no cycle
because its independent apply contract is already deployed and its managed leaf
targets do not intersect the personal source.

Implementation is small and coupled, so parallel write subagents do not shorten
the critical path. One independent read-only review may run alongside final
affected QA after implementation. Additional OpenCode/Herdr sessions should not
run concurrently during deployment because both applies share the same home and
the secondary apply owns host/guest update locks.

## Dependency And Order

```text
personal full apply
  -> personal targets complete
  -> validate secondary config/source/origin/target separation
  -> git pull --ff-only current dotfiles-ai tracking branch
  -> dedicated dotfiles-ai full apply
  -> combined success
```

The flow is intentionally not a distributed transaction. If the secondary step
fails, the outer command fails and preserves truthful partial completion; a retry
converges from idempotent source behavior.

After source/origin and pre/post-pull ownership checks pass, the secondary apply
uses `--force` only within `dotfiles-ai` ownership. This avoids TTY prompts for
modified managed AI targets; personal and overlapping targets are never forced.
