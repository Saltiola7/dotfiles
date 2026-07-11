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
    expected = {"python.md", "security.md", "data.md", "cloud.md", "ml.md", "analytics.md"}
    assert {path.name for path in modules.glob("*.md")} == expected
    assert {path.name for path in references.glob("*.md")} == {
        "data.md",
        "cloud.md",
        "ml.md",
        "analytics.md",
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
    assert "`discovery` to at least 95% confidence" in agents
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
