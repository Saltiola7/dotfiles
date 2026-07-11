# Analytics Examples (Local, Unverified)

These are local examples, not requirements or validated performance claims.
Project policy and the analytics module remain authoritative.

## Pairwise skill pattern

A thin knowledge router first selects a semantic/governed source, then loads a
domain reference. A separate process guide clarifies the question, retrieves the
source, performs analysis, and requests independent review when applicable.

## Reference-document skeleton

```markdown
# [Domain] tables

## Business context
## Entity grain
## Scope and exclusions
## Governed sources
## Dimensions and joins
## Gotchas
## Routing triggers
- IF [question] → use [source]
- DO NOT use [source] for [question] → use [other source]
## Cross-references
```

## Raw SQL fallback examples

Use only after documented governed-interface non-coverage. Adapt names, filters,
and access controls to the project.

```sql
-- Local, unverified example: preserve grain and provenance in the result.
SELECT event_date, COUNT(*) AS events
FROM governed.events
WHERE event_date >= DATE '2026-01-01'
GROUP BY event_date
ORDER BY event_date;
```

```sql
-- Local, unverified example: state an exclusion explicitly.
SELECT account_id, SUM(net_amount) AS net_revenue
FROM governed.revenue_daily
WHERE is_test_account = FALSE
GROUP BY account_id;
```
