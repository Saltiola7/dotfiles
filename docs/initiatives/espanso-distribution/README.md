# Shared Espanso shortcuts

Status: discovery decisions accepted; implementation, publication review and launch preflight pending.

The operator wants the same shortcuts on four desktops without publishing personal text. Each machine keeps its own keyboard and service settings. Enroll in order: Try Omarchy VM, macOS Mac mini, MBP Omarchy, HP Omarchy. Pi400 hosts Git only.

| Context | Repository | Owns |
|---|---|---|
| `host_tool_maintenance` | `dotfiles` (coordinator) | Package, startup, machine settings, enrollment and full-apply integration. [Feature contract](../../specs/host_tool_maintenance/features/espanso.md). |
| `private_configuration` | `dotfiles-private` | Reviewed matches, initial adoption, editing and publication. Private authority: `docs/specs/private_configuration/features/espanso.md` in its own repository. |

The private source can be prepared without changing the Mac. VM deployment depends on reviewed private input. Each later host depends on acceptance of its predecessor. Neither the AI distribution nor the Git hosting service needs modification.

## Delivery and gates

Elevated risk: confidential replacements, executable match variables, Wayland input access and multiple writers. Delivery intent: reviewed integration followed by serial deployment. Kernel gates (Domain, Behavior, Spec, Contract, Test, Refactor), Security, Review/Integrate, Deploy, Operate and Maintain/Retire are required for both slices. Release is not applicable: the native package is built for local installation; no binary distribution channel is proposed. All gate results pending; no exceptions.

Use the existing Engineering Profiles and their feature-specific scope extensions. Recheck the configured deployment checkout against the reviewed revision. Validate private candidates in their owning repository; do not import private documents into a public change. Verify actual Forgejo lifecycle resolution before claiming launch readiness.

## Visual Evidence

| Stage | Input → output | Gate to proceed |
|---|---|---|
| Adoption | Mac live matches → private Git | Recoverable preimage and exact-candidate private review |
| Guest | Public machine settings + private matches → VM | Expansion in the VM window, repeat apply and offline preservation |
| Fleet | Same matches + each host's settings → remaining desktops | Verify local input and rollback on each host before advancing |

**Text Equivalent:** The operator adopts reviewed matches privately before the guest consumes them. Only a qualified guest permits Mac enrollment, then MBP, then HP. The table covers boundary, interaction, state, data/trust and deployment. No new persistent schema or quantitative decision. Owner: repository operator; update when ordering or ownership changes.
