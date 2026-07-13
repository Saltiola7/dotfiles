from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILLS = ROOT / "dot_agents/skills"
COMMANDS = ROOT / "private_dot_config/opencode/commands"


def text(path: Path | str) -> str:
    return (ROOT / path).read_text() if isinstance(path, str) else path.read_text()


def test_public_lifecycle_commands_are_unversioned_and_thin():
    expected = {"discovery": "discovery", "dbsctr": "dbsctr", "qa": "qa"}
    for command, skill in expected.items():
        body = text(COMMANDS / f"{command}.md")
        assert f"skill tool to load `{skill}`" in body
        assert "Do not answer from memory" in body
        assert "\nagent:" not in body

    assert not (COMMANDS / "discovery2.md").exists()
    assert not (COMMANDS / "dbsctr2.md").exists()


def test_v3_skills_use_unversioned_names_and_full_lifecycle():
    discovery = text(SKILLS / "discovery/SKILL.md")
    dbsctr = text(SKILLS / "dbsctr/SKILL.md")

    assert "name: discovery" in discovery
    assert "trigger: /discovery" in discovery
    assert "Engineering Profile" in discovery
    assert "Gate Ledger" in discovery

    assert "name: dbsctr" in dbsctr
    assert "trigger: /dbsctr" in dbsctr
    for term in (
        "Development Kernel",
        "Review/Integrate",
        "Release",
        "Deploy",
        "Operate",
        "Maintain/Retire",
        "accepted_risk",
    ):
        assert term in dbsctr


def test_v2_is_archived_and_not_deployable():
    archive = ROOT / "docs/archive/opencode/skills/v2"
    assert (archive / "discovery2/SKILL.md").exists()
    assert (archive / "dbsctr2/SKILL.md").exists()
    assert {
        path.name for path in (archive / "dbsctr2/modules").glob("*.md")
    } == {"data.md", "cloud.md", "ml.md", "analytics_references.md"}
    assert not any(path.is_file() for path in (SKILLS / "discovery2").rglob("*"))
    assert not any(path.is_file() for path in (SKILLS / "dbsctr2").rglob("*"))

    removals = text(".chezmoiremove")
    for target in (
        ".agents/skills/discovery2",
        ".agents/skills/dbsctr2",
        ".config/opencode/commands/discovery2.md",
        ".config/opencode/commands/dbsctr2.md",
    ):
        assert target in removals


def test_v3_module_registry_is_extensible_and_normalized():
    modules = SKILLS / "dbsctr/modules"
    references = SKILLS / "dbsctr/references"
    expected = {"python.md", "security.md", "data.md", "cloud.md", "ml.md", "analytics.md", "web.md"}
    assert {path.name for path in modules.glob("*.md")} == expected
    assert {path.name for path in references.glob("*.md")} == {
        "data.md",
        "cloud.md",
        "ml.md",
        "analytics.md",
        "python.md",
        "semantic-audit.md",
        "web.md",
    }

    for path in modules.glob("*.md"):
        body = path.read_text()
        for heading in (
            "## Applicability",
            "## Engineering Profile Extensions",
            "## Required Outcomes",
            "## Conditional Controls",
            "## Validation Capabilities",
            "## Lifecycle Obligations",
        ):
            assert heading in body, f"{path}: missing {heading}"
        for label in ("REQUIRED", "CONDITIONAL", "PROJECT POLICY", "EXAMPLE"):
            assert label in body, f"{path}: missing {label} guidance"


def test_project_specific_module_rules_are_not_normative():
    module_text = "\n".join(
        path.read_text() for path in (SKILLS / "dbsctr/modules").glob("*.md")
    )
    for banned in (
        "Every IaC component returns a typed dataclass",
        "All three layers required",
        "Typer CLI alongside Prefect",
        "F1 (macro) | ≥ 0.68",
        "+6% accuracy",
    ):
        assert banned not in module_text


def test_qa_accepts_v3_capabilities_without_breaking_scoped_mode():
    qa = text(SKILLS / "qa/SKILL.md")
    for term in (
        "Engineering Profile",
        "Capability Requirement",
        "capability gap",
        "accepted_risk",
        "scoped",
        "full",
    ):
        assert term in qa
    assert "do not install tools" in qa


def test_global_routing_defaults_to_unversioned_v3():
    agents = text("private_dot_config/opencode/AGENTS.md")
    assert "Use `dbsctr`" in agents
    assert "`discovery` until no unresolved question can materially change implementation" in agents
    assert "dbsctr2" not in agents.lower()
    assert "discovery2" not in agents.lower()
    assert "Keep `/dbsctr` and `/discovery` unchanged" not in agents


def test_ci_and_specs_cover_lifecycle_sources():
    workflow = text(".github/workflows/test.yml")
    assert 'python-version: ["3.12", "3.13", "3.14"]' in workflow
    assert '"dot_agents/skills/**"' in workflow
    assert '"private_dot_config/opencode/**"' in workflow
    assert '"docs/specs/dbsctr_v3_lifecycle/**"' in workflow
    assert '".chezmoiignore"' in workflow
    assert '".chezmoiremove"' in workflow

    spec = text("docs/specs/dbsctr_v3_lifecycle/README.md")
    for term in ("Engineering Profile", "Gate Ledger", "MethodWeave", "RigorWeave"):
        assert term in spec


def test_dbsctr_commits_gate_increments_and_pushes_completed_cycles():
    dbsctr = text(SKILLS / "dbsctr/SKILL.md")
    for term in (
        "Gate Commit",
        "Final Push",
        "At cycle start",
        "pre-cycle ahead commits",
        "without another confirmation",
        "Never force-push automatically",
        "dvc push",
        "worktree is clean",
    ):
        assert term in dbsctr

    agents = text("private_dot_config/opencode/AGENTS.md")
    assert "coherent Gate Commits" in agents
    assert "one Final Push" in agents


def test_v31_separates_gate_dimensions_and_scales_artifacts():
    spec = text("docs/specs/dbsctr_v3_lifecycle/README.md")
    dbsctr = text(SKILLS / "dbsctr/SKILL.md")
    discovery = text(SKILLS / "discovery/SKILL.md")
    qa = text(SKILLS / "qa/SKILL.md")

    for term in ("Gate Applicability", "Gate Result", "Gate Exception", "Cycle Record", "Method Revision"):
        assert term in spec
        assert term in dbsctr
    assert "Git common directory" in dbsctr
    assert "README" in dbsctr and "BACKLOG" in dbsctr and "CHANGELOG" in dbsctr
    assert "no unresolved question can materially change" in discovery
    assert "95%" not in discovery
    assert "structured" in qa.lower() and "Gate Result" in qa


def test_v31_templates_match_artifact_and_gate_contracts():
    spec_template = text("docs/specs/_template_spec.md")
    backlog_template = text("docs/specs/_template_backlog.md")
    changelog_template = text("docs/specs/_template_changelog.md")
    assert "Applicability | Result" in spec_template
    assert "Artifact Review" in spec_template
    assert "parallel_safe" in backlog_template
    assert "Gate commits" in changelog_template


def test_v31_helper_and_reviewer_surfaces_exist():
    helper = ROOT / "dot_local/bin/executable_dbsctrctl"
    reviewer = ROOT / "private_dot_config/opencode/agents/reviewer-openai.md"
    assert helper.exists()
    assert reviewer.exists()
    assert "mode: subagent" in reviewer.read_text()
    assert "edit: deny" in reviewer.read_text()


def test_v32_requires_planned_ordered_monotonic_cycles():
    spec = text("docs/specs/dbsctr_v3_lifecycle/README.md")
    dbsctr = text(SKILLS / "dbsctr/SKILL.md")
    discovery = text(SKILLS / "discovery/SKILL.md")
    helper = text("dot_local/bin/executable_dbsctrctl")
    roadmap = text("docs/specs/dbsctr_v3_lifecycle/ROADMAP.md")

    for term in ("Method Revision `3.10`", "applicability plan", "predecessor", "V3.1"):
        assert term in dbsctr
    assert "schema version `1`" in spec
    assert "dbsctrctl start --plan PATH" in discovery
    assert "schema_version" in helper and "raise-risk" in helper
    for milestone in ("V3.2", "V3.3", "V3.4", "V3.5", "V3.6"):
        assert milestone in roadmap


def test_v33_uses_common_worktree_registry_and_delivery_lock():
    spec = text("docs/specs/dbsctr_v3_lifecycle/README.md")
    helper = text("dot_local/bin/executable_dbsctrctl")
    for term in ("<git-common-dir>/dbsctr/cycles/", "worktrees/<worktree-id>/active", "Delivery Target Lock"):
        assert term in spec
    assert "--git-common-dir" in helper
    assert "LOCK_EX | fcntl.LOCK_NB" in helper


def test_v34_automates_isolation_and_safe_cleanup():
    spec = text("docs/specs/dbsctr_v3_lifecycle/README.md")
    helper = text("dot_local/bin/executable_dbsctrctl")
    dbsctr = text(SKILLS / "dbsctr/SKILL.md")
    for term in ("dbsctrctl begin", "24 hours", "unknown ahead commits"):
        assert term in spec
    assert "commands.add_parser(\"begin\")" in helper
    assert "commands.add_parser(\"cleanup\")" in helper
    assert "dbsctrctl begin --plan" in dbsctr


def test_v35_keeps_opencode_and_herdr_as_adapters():
    spec = text("docs/specs/dbsctr_v3_lifecycle/README.md")
    dbsctr = text(SKILLS / "dbsctr/SKILL.md")
    for term in ("dbsctr_status", "dbsctr_begin", "execution/visibility plane", "pane history disabled"):
        assert term in spec
    assert "Typed OpenCode tools are argument-safe adapters" in dbsctr


def test_v36_audit_is_fixed_commit_report_only_and_distinct_from_qa():
    spec = text("docs/specs/dbsctr_v3_lifecycle/README.md")
    dbsctr = text(SKILLS / "dbsctr/SKILL.md")
    agents = text("private_dot_config/opencode/AGENTS.md")
    for term in ("report-only", "one Git commit", "dbsctr_audit", "does not duplicate `/qa`"):
        assert term in spec
    assert "Lifecycle Reconciliation Audit" in dbsctr
    assert "Never infer" in dbsctr
    assert 'Treat "DBSCTR audit" as a report-only' in agents


def test_v362_requires_begin_authorization_and_method_revision_compatibility():
    spec = text("docs/specs/dbsctr_v3_lifecycle/README.md")
    dbsctr = text(SKILLS / "dbsctr/SKILL.md")
    helper = text("dot_local/bin/executable_dbsctrctl")
    tools = text("private_dot_config/opencode/tools/dbsctr.ts")
    assert "CURRENT_METHOD_REVISION = \"3.10\"" in helper
    assert '"method_revision": CURRENT_METHOD_REVISION' in helper
    assert "context.ask" in tools
    assert "before any `beginCycle`" in spec
    assert "schema-less/schema-1/schema-2" in spec
    assert "authorization before `dbsctr_begin`" in dbsctr


def test_v310_product_intent_and_web_ui_are_conditional_and_accessible():
    discovery = text(SKILLS / "discovery/SKILL.md")
    dbsctr = text(SKILLS / "dbsctr/SKILL.md")
    web = text(SKILLS / "dbsctr/modules/web.md")
    references = text(SKILLS / "dbsctr/references/web.md")
    spec = text("docs/specs/dbsctr_v3_lifecycle/README.md")

    assert "docs/specs/<context>/PRODUCT.md" in discovery
    assert "Do not create synthetic Product Intent" in discovery
    assert "Only create or" in discovery and "when no existing artifact satisfies" in discovery
    assert "Never duplicate an existing authoritative product artifact" in discovery
    assert "selected authoritative artifact records" in spec
    assert "creates `PRODUCT.md` only when no existing artifact satisfies it" in spec
    assert "modules/web.md" in dbsctr
    assert "WCAG 2.2 AA" in web
    for outcome in ("keyboard", "focus", "semantics", "contrast", "zoom", "reflow", "target size", "reduced-motion"):
        assert outcome in web
    assert "standard-defined exception" in web
    assert "Automated checks and screenshots are supporting evidence only" in web
    assert "Playwright" in references and "Flowbite Pro" in references
    assert "Playwright" not in web and "Flowbite Pro" not in web
    assert "Configure an MCP server only" in references and "within that project" in references
    assert "Never create or modify user-global" in references
    assert "MCP output is a tool hint, not source authority or gate evidence" in references


def test_v37_inspection_is_fixed_commit_bounded_and_read_only():
    spec = text("docs/specs/dbsctr_v3_lifecycle/README.md")
    helper = text("dot_local/bin/executable_dbsctrctl")
    tools = text("private_dot_config/opencode/tools/dbsctr.ts")
    for term in ("Fixed-Commit Inspection Contract", "`read`, `tree`", "`search`, and", "`object` actions", "dirty overlay"):
        assert term in spec
    assert 'commands.add_parser("inspect")' in helper
    assert "INSPECT_RESPONSE_HARD" in helper
    assert "export const inspect = tool({" in tools


def test_v38_retains_secret_safe_evidence_and_conditional_python_reference():
    spec = text("docs/specs/dbsctr_v3_lifecycle/README.md")
    helper = text("dot_local/bin/executable_dbsctrctl")
    dbsctr = text(SKILLS / "dbsctr/SKILL.md")
    python = text(SKILLS / "dbsctr/references/python.md")
    for term in ("schema version `3`", "record-evidence", "withheld", "no_content", "256 KiB"):
        assert term in spec
    assert 'commands.add_parser("record-evidence")' in helper
    for term in ("op://", "op run", "Pydantic Settings", "SecretStr", "fake environment"):
        assert term in python
    assert "record-evidence GATE" in dbsctr


def test_v39_semantic_reconciliation_is_fixed_commit_report_only_and_authority_ordered():
    spec = text("docs/specs/dbsctr_v3_lifecycle/README.md")
    dbsctr = text(SKILLS / "dbsctr/SKILL.md")
    protocol = text(SKILLS / "dbsctr/references/semantic-audit.md")
    classifications = ("consistent", "confirmed_drift", "stale_evidence", "missing_artifact",
                       "authority_conflict", "historical_unlabelled", "unverified_claim", "out_of_scope")
    for term in classifications:
        assert term in protocol
        assert protocol.count(f"- `{term}`:") == 1
    for term in ("report-only", "resolved commit", "Absence of contradiction", "private machine paths",
                 "inventory_findings", "public=false", "authoritative=false"):
        assert term in spec
    assert "references/semantic-audit.md" in dbsctr
    assert "Graph paths never prove a claim" in protocol
    assert "never project authority" in protocol and "publishable source" in protocol
    assert "first matching rule" in protocol
    assert "dbsctrctl inspect" in protocol and "never read its filesystem" in protocol
    assert "never read withheld content" in protocol
    assert "Keep `/qa full` separate" in protocol
    for boundary in ("never changes files", "lifecycle state", "without explicit approval"):
        assert boundary in protocol
