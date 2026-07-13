# Web/UI References

Non-normative examples. They do not select a framework, component library, test
runner, MCP server, threshold, or gate.

## Browser and accessibility evidence

- Playwright can exercise keyboard flows, browser journeys, responsive states,
  and accessibility integrations. It is an example, not a universal authority.
- Browser accessibility trees, DOM assertions, axe-compatible checks, contrast
  tools, screen readers, keyboard-only review, zoom/reflow checks, and user testing
  provide different evidence; no single one proves WCAG conformance.
- Screenshots and visual regression can support layout review but cannot prove
  semantics, accessible names, focus behavior, announcements, or keyboard access.

## Components and design systems

- Flowbite Pro may supply project-licensed components when Project Policy selects
  it. Verify generated markup, interaction, focus, semantics, responsive states,
  and local design-token compatibility rather than assuming library conformance.
- Native HTML and platform behavior come before custom widgets. Existing project
  components come before adding another component system.
- License credentials, download tokens, and account data belong in the project
  secret authority, never source, prompts, Evidence Envelopes, screenshots, or
  browser-delivered configuration.

## MCP boundary

- MCP is optional. Configure an MCP server only when the project selects it for a
  bounded need and stores configuration within that project under its policy.
- Never create or modify user-global, machine-global, or unrelated-repository MCP
  configuration. Do not expose browser sessions, credentials, private source, or
  customer data beyond the approved server boundary.
- Project-local MCP output is a tool hint, not source authority or gate evidence;
  verify useful claims against project source and configured authorities.
