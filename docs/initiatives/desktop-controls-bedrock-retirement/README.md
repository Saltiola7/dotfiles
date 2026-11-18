# Desktop controls and local Bedrock retirement

## Approved intent

The operator approved two work areas in the personal dotfiles repository:
reliable local volume access with hover-only Apple menu-bar behavior, and local
MGM/Bedrock retirement. One coordinated Build slice owns their shared SketchyBar
configuration and deployment. No child sessions or concurrent writers are needed.

Home: `Saltiola7/dotfiles`. `host_tool_maintenance` owns host deployment and the
desktop controls contract; `aws_creds` owns the retirement contract and preserved
authentication source. Their authoritative feature specifications are listed in
MANIFEST.json. The existing primary checkout has unrelated work and is not an
implementation target.

## Scope and exclusions

Add a click-open volume slider and mute control; retain a small speaker icon.
Diagnose Apple menu-bar hiding and remove demonstrated local interference with
native auto-hide. Remove local MGM/Bedrock scheduled and reactive authentication,
shell defaults, profile/session configuration and attributable cached tokens.
Preserve Backblaze B2 credentials/profile, the shared AWS CLI and unrelated data.
Preserve existing authentication source outside deployment for future Vertex work.
Cloud deletion, account closure, Vertex implementation and additional audio
software are excluded. Earlier broad AWS deletion intent is superseded by this
bounded scope.

## Delivery

DBSCTR V3 Method Revision 3.29; elevated risk because local authentication material
is retired. Required kernel, Review/Integrate, Deploy, Operate and Maintain/Retire
gates. Release is not applicable to this unversioned host configuration. Deliver
one feature-branch draft PR into `main`, with targeted local deployment and
focused regression checks. Exact launch preflight requires separate approval.

### Local completion amendment

The preceding paragraph records the original delivery plan. After failed host
validation, the operator selected lighter local completion: retain the installed
hover helper with below-native SketchyBar layering, start it from SketchyBar only
when missing, and commit locally without a push. The volume slider and auto-hide
were subsequently confirmed to behave as expected. The original Initiative slice
is blocked for DBSCTR closure, not falsely marked delivered; its original launch,
import, commits and failed deployment evidence remain intact. Source changes and
host results are documented separately from that incomplete lifecycle.

## Visual Evidence

Boundary, interaction, state and data/trust: not_applicable here; the two linked
feature contracts own those decisions. Schema, dependency/deployment and
quantitative: not_applicable; one repository and one serial deployment slice are
fully described above, with no new schema or quantitative claim.
