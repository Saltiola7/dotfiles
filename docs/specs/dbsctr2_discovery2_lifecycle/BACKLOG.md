# Backlog — DBSCTR2 and Discovery2 Lifecycle

Discovery2 confidence: 96%.

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Define v2 lifecycle domain | high | done | - | lifecycle README | existing skills | no | Establish bounded context | M | Commit `8993f76` |
| 2 | Add v2 workflow scenarios | high | done | 1 | lifecycle README | lifecycle domain | no | Define observable behavior | M | Commit `ad524ee` |
| 3 | Add v2 skill and command interfaces | high | done | 2 | v2 skills and commands | lifecycle spec | yes | Expose workflows | L | Commit `8b37fb1` |
| 4 | Add v2 routing and config contracts | high | done | 3 | OpenCode routing and config | v2 skills | no | Make v2 native | M | Commit `15e902a` |
| 5 | Verify v2 deployment | high | done | 4 | deployed managed targets | source config | no | Prove runtime availability | M | Commit `9d40496` |
| 6 | Finalize lifecycle docs | medium | done | 5 | lifecycle artifacts | validation evidence | no | Close initial rollout | S | Commit `e74ef01` |
| 7 | Add DBSCTR2 DVC sync gate | medium | done | 6 | DBSCTR2 and lifecycle spec | DVC conventions | no | Preserve data/code consistency | M | Commit `cafd07d` |
| 8 | Integrate dependency alerts into QA | medium | done | 6 | QA and lifecycle integration | Dependabot inputs | no | Centralize quality gates | M | QA lifecycle commits |
| 9 | Copy domain modules into DBSCTR2 | medium | done | 6 | DBSCTR2 modules | v1 modules | yes | Remove v1 path dependency | M | Deployed module checks |
| 10 | Define provider-affine agent domain and behavior | high | done | 9 | lifecycle README, backlog, changelog | OpenCode and model docs | no | Make implementation intent explicit | M | Artifact consistency checks |
| 11 | Confirm runtime model and variant identifiers | high | pending | 10 | lifecycle changelog evidence | OpenCode model list, Bedrock catalog, config schema | yes | Never commit guessed identifiers | S | `opencode models`, rendered schema validation |
| 12 | Add OpenAI primary and optimized subagents | high | pending | 11 | OpenAI agent files and config entries | agent contracts, current config | yes | Route Sol to Luna/Terra efficiently | M | Agent/config parse and OpenAI routing smoke tests |
| 13 | Add Bedrock primary and optimized subagents | high | pending | 11 | Bedrock agent files and config entries | agent contracts, current config | yes | Route Bedrock Opus to Sonnet 5 | M | Agent/config parse and Bedrock routing smoke tests |
| 14 | Restore generic subagent inheritance | high | pending | 11 | built-in agent overrides in OpenCode config | current agent config | no | Preserve arbitrary-provider affinity | S | Resolved config and inheritance scenario |
| 15 | Tailor DBSCTR2 to OpenCode session primitives | high | pending | 10 | DBSCTR2 skill, global routing | OpenCode tools, agents, permissions, sessions | no | Add phase ledger, handoff, child evidence, and fallback | M | Static contract scenarios and skill smoke test |
| 16 | Enforce primary task permissions and builder boundaries | high | pending | 12, 13, 14, 15 | primary/subagent permissions and prompts | resolved agent definitions | no | Prevent cross-provider and unsafe child actions | M | Permission matrix and denied-route tests |
| 17 | Run temporary provider-routing scenarios | high | pending | 16 | changelog validation evidence | deployed config and temporary fixture | no | Check quality, latency, routing, review, and fallback without a permanent harness | M | Explore, Scout, Builder, and controlled-failure scenarios |
| 18 | Deploy and finalize lifecycle | high | pending | 17 | managed targets and lifecycle artifacts | all implementation diffs and evidence | no | Complete DBSCTR2 cycle without stale artifacts | M | chezmoi dry-run/apply/status, parity, final QA |

Tasks 12 and 13 may run concurrently because they own separate agent families.
The orchestrator alone owns shared config integration, task permissions,
deployment, staging, and commits. Builders never commit.
