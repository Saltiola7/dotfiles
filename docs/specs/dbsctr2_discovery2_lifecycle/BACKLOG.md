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
| 11 | Confirm runtime model and variant identifiers | high | done | 10 | lifecycle changelog evidence | OpenCode model list, Bedrock catalog, config schema | yes | Never commit guessed identifiers | S | Runtime model listing and rendered schema passed |
| 12 | Add OpenAI primary and optimized subagents | high | done | 11 | OpenAI agent files and config entries | agent contracts, current config | yes | Route Sol to Luna/Terra efficiently | M | Agent/config parse passed; child launched but return timed out |
| 13 | Add Bedrock primary and optimized subagents | high | done | 11 | Bedrock agent files and config entries | agent contracts, current config | yes | Route Bedrock Opus to Sonnet 5 | M | Agent/config parse and Bedrock Explore route passed |
| 14 | Restore generic subagent inheritance | high | done | 11 | built-in agent overrides in OpenCode config | current agent config | no | Preserve arbitrary-provider affinity | S | Resolved generic Scout and built-in Explore have no model override |
| 15 | Tailor DBSCTR2 to OpenCode session primitives | high | done | 10 | DBSCTR2 skill, global routing | OpenCode tools, agents, permissions, sessions | no | Add phase ledger, handoff, child evidence, and fallback | M | Deployed skill contains phase, handoff, evidence, and fallback contracts |
| 16 | Enforce primary task permissions and builder boundaries | high | done | 12, 13, 14, 15 | primary/subagent permissions and prompts | resolved agent definitions | no | Prevent cross-provider and unsafe child actions | M | Rendered permission assertions passed |
| 17 | Run temporary provider-routing scenarios | high | done | 16 | changelog validation evidence | deployed config and temporary fixture | no | Check quality, latency, routing, review, and fallback without a permanent harness | M | Static matrix and Bedrock live route passed; OpenAI timeout recorded |
| 18 | Deploy and finalize lifecycle | high | done | 17 | managed targets and lifecycle artifacts | all implementation diffs and evidence | no | Complete DBSCTR2 cycle without stale artifacts | M | Dry-run, apply, resolved config, status, and affected-scope checks passed |
| 19 | Restore Plan and explicit Build roles | high | done | 18 | primary agents, commands, routing, lifecycle docs | deployed agent behavior | no | Preserve the familiar Plan-to-Build workflow | S | Resolved primaries are Plan, Build-GPT, and Build-Claude |
| 20 | Register runtime model variants | high | done | 19 | OpenAI and Bedrock model overrides | model registry and variant docs | no | Prevent configured agents from displaying inert Default variants | S | Resolved provider variants and agent selections passed assertions |
| 21 | Replace unavailable Luna routes | high | done | 20 | OpenAI agents, small model, lifecycle docs | runtime model errors and Terra smoke test | no | Stop permanent model-not-found retries | S | No active Luna references; Terra resolves for small and Explore routes |
| 22 | Add optional Sol Pro primaries | high | superseded | 21 | OpenAI primary agents and lifecycle docs | OpenAI Pro guidance and OpenCode model registry | no | Improve difficult planning and implementation without taxing routine work | S | Alias resolved and live probe passed, but OpenCode did not send genuine Pro mode; superseded by 24 |
| 23 | Add maximum-effort Sol Pro planner | high | superseded | 22 | OpenAI model variant, Plan agent, lifecycle docs | GPT-5.6 reasoning guidance and resolved config | no | Provide an explicit architectural planning ceiling without multiplying intermediate agents | S | Alias and max effort resolved, but genuine Pro mode was absent; superseded by 24 |
| 24 | Retire unsupported OAuth Pro agents | high | in_progress | 23 | OpenAI primary agents, model override, lifecycle artifacts, focused tests | OpenCode 1.17.20 OAuth filtering, PR #36694, and live OAuth rejection | no | Match selectable agents to actual ChatGPT OAuth behavior | S | Pro probe rejected with `unsupported_value`; focused tests and deployment pending |

Tasks 12 and 13 may run concurrently because they own separate agent families.
The orchestrator alone owns shared config integration, task permissions,
deployment, staging, and commits. Builders never commit.
