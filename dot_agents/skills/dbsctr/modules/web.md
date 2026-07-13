# DBSCTR Module: Web/UI

## Applicability

- **CONDITIONAL:** Load for browser UI, product-facing web flows, frontend
  components, design-system changes, or user-visible rendered documents.
- **CONDITIONAL:** Internal tools load this module only when their Engineering
  Profile establishes intentional user journeys or accessibility obligations.
- **PROJECT POLICY:** The project selects frameworks, component systems, browser
  support, test authorities, design tokens, and any stronger accessibility target.
- **EXAMPLE:** Static HTML, server-rendered pages, SPAs, and embedded web views may
  all trigger the same outcome requirements without sharing a framework.

## Engineering Profile Extensions

- **REQUIRED:** Record users, supported browsers/viewports/input modes, design and
  component authorities, accessibility target, localization needs, privacy/trust
  boundaries, delivery environment, and accountable product/operational owner.
- **CONDITIONAL:** Reference `docs/specs/<context>/PRODUCT.md` when Product Intent
  applies; do not create one for non-product work.
- **PROJECT POLICY:** WCAG 2.2 AA is the default target unless project policy,
  regulation, or user need requires a stronger target.

## Required Outcomes

- **REQUIRED:** Use semantic structure, landmarks, headings, names, labels,
  instructions, relationships, and status/error announcements that assistive
  technology can determine.
- **REQUIRED:** Support keyboard operation without traps, visible and unobscured
  focus, logical focus order, and deliberate focus restoration after dynamic UI.
- **REQUIRED:** Meet applicable text/non-text contrast, zoom, reflow, orientation,
  spacing, and responsive behavior without loss of information or operation.
- **REQUIRED:** Expose loading, empty, success, validation, error, offline, denied,
  and destructive states without relying on color, motion, hover, or vision alone.
- **REQUIRED:** Preserve accessible names, roles, values, and input purpose across
  reusable components and responsive variants; meet applicable WCAG 2.2 AA target
  size or document and validate a standard-defined exception.
- **CONDITIONAL:** Provide non-drag alternatives, consistent help, redundant-entry
  reduction, and accessible authentication where those WCAG 2.2 outcomes apply.
- **CONDITIONAL:** Respect reduced-motion and other user preferences; motion never
  blocks understanding or operation.
- **REQUIRED:** Protect browser trust boundaries: validate untrusted content,
  constrain navigation/storage/embedding, minimize personal data, and avoid
  credentials or sensitive values in client bundles, logs, URLs, and screenshots.

## Conditional Controls

- **CONDITIONAL:** When UI state persists or crosses a network boundary, define
  stale, duplicate, interrupted, unauthorized, and recovery behavior.
- **CONDITIONAL:** When localization applies, preserve meaning, layout, direction,
  names, errors, dates, numbers, and pluralization across supported locales.
- **CONDITIONAL:** When analytics or experimentation applies, preserve consent,
  privacy, accessibility, deterministic fallback, and operational ownership.
- **PROJECT POLICY:** Performance budgets, telemetry, content security, session
  behavior, and browser matrices come from project authorities.
- **EXAMPLE:** A project may use a component test for semantics and a browser
  journey for focus restoration; neither tool is mandatory.

## Validation Capabilities

- **REQUIRED:** Map applicable UI and accessibility outcomes to project-selected
  authorities; missing evidence is a capability gap, not a pass.
- **REQUIRED:** Validate keyboard flow, focus, semantics, names, errors, contrast,
  zoom/reflow, target size or applicable exception, and reduced motion where
  affected.
- **REQUIRED:** Automated checks and screenshots are supporting evidence only;
  visual snapshots never replace DOM/semantic, keyboard, or assistive review.
- **CONDITIONAL:** Validate representative browsers, viewport/input combinations,
  localization, performance budgets, security boundaries, and end-to-end journeys
  when the Engineering Profile requires them.
- **PROJECT POLICY:** Existing unit, component, browser, accessibility, visual,
  manual, and assistive-technology authorities remain authoritative.

## Lifecycle Obligations

- **REQUIRED:** Carry Product Intent, accessibility, compatibility, privacy, and
  validation evidence through Review/Integrate.
- **CONDITIONAL:** For release/deployment, verify built assets, configuration,
  cache/migration behavior, health, rollback, and representative post-deploy flows.
- **CONDITIONAL:** For long-lived UI, record browser/runtime support, dependency
  maintenance, accessibility-regression intake, deprecation, migration, analytics
  privacy, and retirement obligations.
- **PROJECT POLICY:** Product analytics, experimentation, consent, support, and
  observability follow project policy and never weaken accessibility or privacy.
