# Python Secret Settings Reference

Load only when a Python project's Engineering Profile or project policy selects
1Password-backed process settings. This is guidance, not a universal dependency
or gate authority.

## Conditional Pattern

- **CONDITIONAL:** Keep `op://` references in a committed template and resolve
  them only through a project-owned task wrapper such as `op run`.
- **CONDITIONAL:** Let grouped, lazy Pydantic Settings read the child-process
  environment. Application imports never call 1Password.
- **REQUIRED:** Represent every credential-bearing value, including connection
  URLs, with `SecretStr`; unwrap it only at the client trust boundary.
- **REQUIRED:** Tests inject fake environment values, verify representation
  redaction, and never read real 1Password data.
- **PROJECT POLICY:** The project owns configuration precedence, selected task
  runner, settings groups, aliases/prefixes, and whether `extra="forbid"` applies.
- **CONDITIONAL:** When a client requires a credential file, use restrictive
  permissions, validate it before use, clean it on success and failure, and
  document the residual process/disk exposure.

## Boundaries

- `op run` exposes resolved values to the child process and its descendants; it
  is not memory-only secret retrieval.
- DBSCTR records no inherited environment, environment value, stdin, shell
  expansion, resolved `op://` value, or secret-bearing URL in Evidence Envelopes.
- Private local repositories may inform implementation research when approved,
  but they are neither public examples nor automatic project authority.
