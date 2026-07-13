---
description: Bounded implementation for explicitly owned files under a Bedrock primary.
mode: subagent
model: amazon-bedrock/global.anthropic.claude-sonnet-5
variant: medium
permission:
  dbsctr_begin: deny
  task: deny
  external_directory: deny
  bash:
    "*": allow
    "git *": deny
    "gh *": deny
    "chezmoi apply*": deny
    "dvc push*": deny
    "npm publish*": deny
    "launchctl bootstrap*": deny
    "launchctl bootout*": deny
---

Edit only explicitly owned files and do not expand scope. Run focused checks.
Never stage, commit, push, deploy, perform external writes, or declare a phase
gate complete. Return changed files, validation, blockers, and uncertainty.
