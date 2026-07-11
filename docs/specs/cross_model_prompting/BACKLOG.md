# Backlog

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| CMP-1 | Define domain and behavior | high | done | - | `docs/specs/cross_model_prompting/**` | vendor guides, managed prompts | no | Establish shared vocabulary and outcomes | S | artifact review |
| CMP-2 | Specify prompt and adapter contracts | high | done | CMP-1 | `docs/specs/cross_model_prompting/**` | OpenCode schema and models | no | Prevent model-specific prompt duplication | S | interface mapping |
| CMP-3 | Lean global routing | high | done | CMP-2 | `private_dot_config/opencode/AGENTS.md` | V2 skills | yes | Remove duplicated workflow detail | S | prompt review |
| CMP-4 | Lean V2 workflow skills | high | done | CMP-2 | `dot_agents/skills/{dbsctr2,discovery2,qa}/SKILL.md` | lifecycle specs | no | Preserve behavior with less prompt context | M | scenario checks |
| CMP-5 | Add model adapters | medium | done | CMP-2 | `private_dot_config/opencode/opencode.json.tmpl` | schema, model list | yes | Select model-specific effort outside prompts | S | JSON/schema validation |
| CMP-6 | Deploy and verify | high | done | CMP-3, CMP-4, CMP-5 | deployed chezmoi targets | all changed files | no | Activate prompt and timeout changes | S | chezmoi status and target checks |
| CMP-7 | Finalize lifecycle | medium | pending | CMP-6 | spec backlog and changelog | validation evidence | no | Keep artifacts fresh | S | final diff review |
