# DBSCTR Module: Python

## Applicability

- **REQUIRED:** Load when the Engineering Profile, affected source, or standard project metadata identifies Python.
- **CONDITIONAL:** Load for Python packaging, runtime, automation, or service changes even when only configuration changes.
- **PROJECT POLICY:** Project instructions, metadata, manifests, lockfiles, and CI define supported runtimes and selected tools.
- **EXAMPLE:** A repository may identify Python through `pyproject.toml`, source files, or CI configuration; none is universally required.

## Engineering Profile Extensions

- **REQUIRED:** Record supported Python runtimes, deliverable type, runtime environments, dependency groups, compatibility commitments, and operational owner when applicable.
- **REQUIRED:** Name the authoritative dependency metadata and, when used, the authoritative lock artifact.
- **CONDITIONAL:** For libraries, record compatible runtime dependency ranges; for deployed applications, record whether exact deployment locks are required.
- **PROJECT POLICY:** The project selects its package manager, environment manager, build backend, and lock strategy.
- **CONDITIONAL:** When project policy selects 1Password-backed process settings,
  load `references/python.md`; do not make 1Password, Pydantic Settings, or a task
  runner universal Python requirements.
- **EXAMPLE:** Separate development, test, documentation, and runtime dependency groups can make intent reviewable.

## Required Outcomes

- **REQUIRED:** Reproducibly create an isolated environment using project-selected metadata and dependency authority.
- **REQUIRED:** Keep declared dependencies minimal, attributable to a need, and compatible with supported runtimes.
- **REQUIRED:** Apply the project-selected formatting and linting authorities, or record a capability gap.
- **REQUIRED:** Express meaningful interfaces and boundary values with types; resolve typing findings according to project policy.
- **REQUIRED:** Test changed behavior through the configured authority or equivalent evidence; coverage is evidence, not a universal threshold.
- **REQUIRED:** Handle untrusted input, unsafe deserialization, subprocess execution, filesystem access, network access, and secrets according to applicable security controls.
- **CONDITIONAL:** Build a distributable package when the delivery intent produces one; verify its metadata, contents, and installation path.
- **CONDITIONAL:** Preserve API, CLI, configuration, and serialized-data compatibility or provide a documented migration.
- **PROJECT POLICY:** CI selects authoritative commands and supported-runtime coverage; it is the authority for what must pass.
- **EXAMPLE:** Formatting, linting, type checking, and tests may be separate commands or one project task.

## Conditional Controls

- **CONDITIONAL:** When runtime support changes, validate the oldest and newest supported stable Python versions where practical.
- **CONDITIONAL:** When dependencies change, update the authoritative lock artifact if project policy requires one; do not create a lock merely because a tool supports it.
- **CONDITIONAL:** When native extensions, generated code, or platform-specific behavior changes, validate affected build and runtime targets.
- **CONDITIONAL:** When publishing or releasing, prepare version, compatibility, artifact identity, release notes, and approvals; external publication requires authorization.
- **CONDITIONAL:** When operating a service, provide configured startup, health, logging, error, and recovery evidence appropriate to the service.
- **CONDITIONAL:** When removing a supported API, runtime, or dependency, document deprecation, migration, support horizon, and retirement conditions.
- **PROJECT POLICY:** Requirements for reproducible builds, signatures, release branches, and operational telemetry come from project policy or the Engineering Profile.
- **EXAMPLE:** A library can warn before removing an API; an application can migrate internally without public notice when no external consumer exists.

## Validation Capabilities

- **REQUIRED:** Map each applicable concern to a project-selected authority or record it as missing, deferred, or accepted risk in the Gate Ledger.
- **REQUIRED:** Validate changed behavior, dependency resolution, and affected supported runtimes when their claims apply.
- **CONDITIONAL:** Validate formatting, linting, typing, packaging, security, release, and operations when those capabilities apply to the cycle.
- **PROJECT POLICY:** Existing CI, task runners, scripts, and documented review procedures are preferred authorities; do not install or mandate a universal Python tool.
- **EXAMPLE:** A project may use a task runner for all checks or individual commands for each concern.

## Lifecycle Obligations

- **REQUIRED:** Carry runtime support, dependency authority, compatibility, and validation evidence from Domain through Refactor.
- **REQUIRED:** Evaluate review/integration and maintain/retire gates; record an explicit Gate Status for each applicable Python concern.
- **CONDITIONAL:** Evaluate release, deployment, and operations gates only when the delivery intent or deliverable requires them.
- **CONDITIONAL:** Raise risk for public compatibility changes, untrusted-code execution, sensitive data, production impact, or unsupported-runtime exposure.
- **PROJECT POLICY:** Support windows, deprecation channels, patch cadence, and artifact retention are defined by project policy.
- **EXAMPLE:** A local script may rule out release and operations gates with profile-based reasons.
