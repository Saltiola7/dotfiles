# OpenCode Control Plane Backlog

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| OCP-1 | Persist approved domain and behavior | high | done | - | control-plane spec | discovery decisions | no | Establish authority | S | Artifact review |
| OCP-2 | Add control-plane contract test | high | done | OCP-1 | focused test | config and agents | yes | Prevent routing and permission drift | M | 7 focused tests passed |
| OCP-3 | Align routing and permissions | high | done | OCP-2 | OpenCode config, agents, commands, routing | contracts | no | Enforce selected behavior | M | Resolved assertions passed |
| OCP-4 | Curate OpenCode skills | high | done | OCP-1 | installer, lock, ignores | installed skills | yes | Remove duplicates and incompatible skills | M | Unique inventory passed |
| OCP-5 | Remove managed legacy integrations | high | done | OCP-1 | wrappers, Meridian, Headroom, OMO, docs | source inventory | yes | Eliminate unused surfaces | M | Static absence checks passed |
| OCP-6 | Preserve Graphify without duplicate plugin | high | done | OCP-3 | Graphify installer and project runtime files | graph and hooks | no | Keep useful graph behavior | S | Version, hooks, and query passed |
| OCP-7 | Clean approved machine runtime | high | done | OCP-3,OCP-4,OCP-5,OCP-6 | installed packages, services, state | package ownership | no | Match runtime to source | M | Runtime absence checks passed |
| OCP-8 | Deploy and validate | high | done | OCP-7 | managed targets | all changes | no | Activate safely | M | Config and OpenAI probes passed; Bedrock blocked by expired SSO |
| OCP-9 | Finalize artifacts | medium | done | OCP-8 | control-plane artifacts and indexes | evidence | no | Prevent stale docs | S | Final review passed |
| OCP-10 | Retire unsupported Pro aliases and restore native Build | high | done | OCP-9 | OpenAI provider override, native/custom primary agents, control-plane artifacts and tests | OpenCode 1.17.20 OAuth behavior, Plan handoff source, PR #36694, and live probes | no | Keep model exposure truthful and preserve supported Plan-to-Build execution | S | Pro probe rejected; 35 affected tests, deployment, resolved config, native Build, and Build-GPT probes passed |
