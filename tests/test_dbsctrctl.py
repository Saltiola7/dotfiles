"""Focused subprocess contracts for dbsctrctl."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "dot_local/bin/executable_dbsctrctl"
GATES = (
    "domain", "behavior", "spec", "contract", "test_driven_implementation",
    "refactor", "review_integrate", "release", "deploy", "operate", "maintain_retire",
)


def run(repo, *args, ok=True, env=None, input_text=None):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=repo, text=True, capture_output=True,
        env=env, input=input_text,
    )
    if ok and result.returncode:
        raise AssertionError(f"{args}: {result.stderr}")
    if not ok and not result.returncode:
        raise AssertionError(f"{args}: unexpectedly succeeded")
    return result


class DbsctrctlTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        artifacts = self.repo / "docs/specs/test"
        artifacts.mkdir(parents=True)
        for args in (("init",), ("config", "user.email", "test@example.com"),
                     ("config", "user.name", "Test")):
            subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True)
        (self.repo / "tracked.txt").write_text("base\n")
        for name in ("README.md", "BACKLOG.md", "CHANGELOG.md"):
            (artifacts / name).write_text("base\n")
        subprocess.run(
            ["git", "add", "tracked.txt", "docs/specs/test"],
            cwd=self.repo, check=True,
        )
        subprocess.run(["git", "commit", "-m", "base"], cwd=self.repo, check=True,
                       capture_output=True)

    def tearDown(self):
        self.temp.cleanup()

    def start(self, intent="local"):
        gates = {
            gate: {"applicability": "required"}
            for gate in GATES
        }
        if intent != "release":
            gates["release"] = {
                "applicability": "not_applicable",
                "reason": "delivery intent is not release",
            }
        plan = Path(self.temp.name) / "plan.json"
        plan.write_text(json.dumps({
            "profile": "docs/specs/test/README.md",
            "gates": gates,
        }))
        return run(self.repo, "start", "--cycle-id", "cycle-1", "--context", "test",
                   "--risk", "routine", "--delivery-intent", intent, "--plan", str(plan))

    def review_artifacts(self):
        for name, result, reason in (
            ("README", "unchanged", "no durable truth changed"),
            ("BACKLOG", "unchanged", "already tracked"),
            ("CHANGELOG", "unchanged", "not finalized"),
        ):
            run(self.repo, "review-artifact", name, "--result", result, "--reason", reason)

    def pass_gates(self):
        for gate in GATES:
            if gate != "release":
                run(self.repo, "set-gate", gate, "--result", "passed", "--evidence", "test evidence")

    def pass_gate(self, gate="domain"):
        run(self.repo, "set-gate", gate, "--result", "passed", "--evidence", "test evidence")

    def test_start_records_schema_and_release_default(self):
        self.start()
        record = json.loads((self.repo / ".git/dbsctr/cycle-1.json").read_text())
        self.assertEqual(record["method_revision"], "3.2")
        self.assertEqual(record["schema_version"], 1)
        self.assertEqual(record["engineering_profile"]["path"], "docs/specs/test/README.md")
        self.assertEqual(len(record["engineering_profile"]["blob"]), 40)
        self.assertEqual(record["state"], "active")
        self.assertIsNone(record["git"]["upstream"])
        self.assertEqual(record["gates"]["release"], {
            "applicability": "not_applicable", "result": "not_run", "reason": "delivery intent is not release"
        })
        self.assertEqual(set(record["artifact_reviews"]), {"README", "BACKLOG", "CHANGELOG"})

    def test_start_refuses_dirty_worktree(self):
        (self.repo / "tracked.txt").write_text("pre-cycle\n")
        result = run(
            self.repo, "start", "--cycle-id", "cycle-1", "--context", "test",
            "--risk", "routine", "--delivery-intent", "local", "--plan", "missing.json", ok=False,
        )
        self.assertIn("clean worktree", result.stderr)

    def test_start_rejects_unknown_delivery_intent(self):
        result = run(
            self.repo, "start", "--cycle-id", "cycle-1", "--context", "test",
            "--risk", "routine", "--delivery-intent", "relase", "--plan", "missing.json", ok=False,
        )
        self.assertIn("invalid choice", result.stderr)

    def test_start_requires_complete_valid_plan(self):
        result = run(
            self.repo, "start", "--cycle-id", "cycle-1", "--context", "test",
            "--risk", "routine", "--delivery-intent", "local", ok=False,
        )
        self.assertIn("--plan", result.stderr)

        plan = {"profile": "docs/specs/test/README.md", "gates": {}}
        result = run(
            self.repo, "start", "--cycle-id", "cycle-1", "--context", "test",
            "--risk", "routine", "--delivery-intent", "local", "--plan", "-", ok=False,
            input_text=json.dumps(plan),
        )
        self.assertIn("every gate", result.stderr)

    def test_start_rejects_dirty_or_wrong_profile_and_delivery_conflict(self):
        gates = {gate: {"applicability": "required"} for gate in GATES}
        gates["release"] = {"applicability": "not_applicable", "reason": "not releasing"}
        plan = {"profile": "docs/specs/test/README.md", "gates": gates}
        result = run(
            self.repo, "start", "--cycle-id", "cycle-1", "--context", "test",
            "--risk", "routine", "--delivery-intent", "release", "--plan", "-", ok=False,
            input_text=json.dumps(plan),
        )
        self.assertIn("release delivery", result.stderr)

        plan["profile"] = "tracked.txt"
        result = run(
            self.repo, "start", "--cycle-id", "cycle-1", "--context", "test",
            "--risk", "routine", "--delivery-intent", "local", "--plan", "-", ok=False,
            input_text=json.dumps(plan),
        )
        self.assertIn("Engineering Profile", result.stderr)

    def test_gate_pass_requires_predecessors_but_failure_does_not(self):
        self.start()
        result = run(
            self.repo, "set-gate", "behavior", "--result", "passed",
            "--evidence", "too early", ok=False,
        )
        self.assertIn("predecessor", result.stderr)
        run(self.repo, "set-gate", "behavior", "--result", "failed", "--evidence", "early failure")
        run(self.repo, "set-gate", "domain", "--result", "passed", "--evidence", "domain")
        run(
            self.repo, "approve-exception", "behavior", "--kind", "deferred",
            "--rationale", "approved", "--owner", "owner", "--review-condition", "next cycle",
        )
        run(self.repo, "set-gate", "spec", "--result", "passed", "--evidence", "spec")
        run(self.repo, "set-gate", "domain", "--result", "pending")
        record = json.loads((self.repo / ".git/dbsctr/cycle-1.json").read_text())
        self.assertEqual(record["gates"]["spec"]["result"], "pending")

    def test_risk_and_applicability_only_tighten(self):
        self.start()
        record_path = self.repo / ".git/dbsctr/cycle-1.json"
        record = json.loads(record_path.read_text())
        gates = {
            gate: {"applicability": value["applicability"], **(
                {"reason": value["reason"]} if value["applicability"] == "not_applicable" else {}
            )}
            for gate, value in record["gates"].items()
        }
        gates["release"] = {"applicability": "required"}
        plan = {"profile": "docs/specs/test/README.md", "gates": gates}
        run(
            self.repo, "raise-risk", "--to", "elevated", "--reason", "public contract",
            "--plan", "-", input_text=json.dumps(plan),
        )
        result = run(
            self.repo, "raise-risk", "--to", "routine", "--reason", "changed mind",
            "--plan", "-", input_text=json.dumps(plan), ok=False,
        )
        self.assertIn("only increase", result.stderr)
        record = json.loads(record_path.read_text())
        self.assertEqual(record["risk"], "elevated")
        self.assertEqual(record["gates"]["release"]["applicability"], "required")
        self.assertEqual(record["risk_history"][0]["from"], "routine")

    def test_schema_less_v31_record_uses_legacy_transitions(self):
        self.start()
        record_path = self.repo / ".git/dbsctr/cycle-1.json"
        record = json.loads(record_path.read_text())
        record.pop("schema_version")
        record.pop("engineering_profile")
        record.pop("applicability_plan")
        record["method_revision"] = "3.1"
        record_path.write_text(json.dumps(record))
        run(self.repo, "set-gate", "behavior", "--result", "passed", "--evidence", "legacy")

    def test_unknown_cycle_schema_is_rejected(self):
        self.start()
        record_path = self.repo / ".git/dbsctr/cycle-1.json"
        record = json.loads(record_path.read_text())
        record["schema_version"] = 99
        record_path.write_text(json.dumps(record))
        result = run(self.repo, "status", ok=False)
        self.assertIn("unsupported Cycle Record schema", result.stderr)

    def test_artifact_check_and_gate_transition_validation(self):
        self.start()
        self.assertNotEqual(run(self.repo, "check", "artifacts", ok=False).returncode, 0)
        run(self.repo, "review-artifact", "README", "--result", "unchanged", "--reason", "still accurate")
        run(self.repo, "review-artifact", "BACKLOG", "--result", "unchanged", "--reason", "tracked")
        run(self.repo, "review-artifact", "CHANGELOG", "--result", "unchanged", "--reason", "pending completion")
        run(self.repo, "check", "artifacts")
        run(self.repo, "set-gate", "domain", "--result", "not_run", ok=False)
        run(self.repo, "set-gate", "domain", "--result", "passed", ok=False)
        run(self.repo, "set-gate", "release", "--result", "passed", ok=False)
        run(
            self.repo, "approve-exception", "contract", "--kind", "deferred",
            "--rationale", "too early", "--owner", "owner",
            "--review-condition", "later", ok=False,
        )
        run(
            self.repo, "set-applicability", "operate", "--value", "not_applicable",
            "--reason", "no runtime", ok=False,
        )
        run(self.repo, "set-gate", "operate", "--result", "passed", "--evidence", "x", ok=False)
        run(self.repo, "set-gate", "domain", "--result", "failed", "--evidence", "failed check")
        run(
            self.repo, "approve-exception", "domain", "--kind", "deferred",
            "--rationale", "approved later", "--owner", "owner",
            "--review-condition", "next cycle",
        )
        run(self.repo, "set-gate", "domain", "--result", "failed", "--evidence", "new failure")
        record = json.loads((self.repo / ".git/dbsctr/cycle-1.json").read_text())
        self.assertNotIn("exception", record["gates"]["domain"])

    def test_changed_artifact_review_rejects_wrong_context_path(self):
        self.start()
        result = run(
            self.repo, "review-artifact", "CHANGELOG", "--result", "changed",
            "--reason", "wrong file", "--path", "tracked.txt", ok=False,
        )
        self.assertIn("docs/specs/test/CHANGELOG.md", result.stderr)

    def test_final_push_refuses_no_upstream(self):
        self.start()
        self.review_artifacts()
        self.pass_gates()
        run(self.repo, "final-push", ok=False)

    def test_final_push_refuses_dirty_worktree(self):
        remote = Path(self.temp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        self.start()
        self.review_artifacts()
        self.pass_gates()
        (self.repo / "tracked.txt").write_text("dirty\n")
        run(self.repo, "final-push", ok=False)

    def test_gate_commit_refuses_unrelated_staged_paths(self):
        self.start()
        self.pass_gate()
        (self.repo / "tracked.txt").write_text("wanted\n")
        (self.repo / "other.txt").write_text("base\n")
        subprocess.run(["git", "add", "other.txt"], cwd=self.repo, check=True)
        run(self.repo, "gate-commit", "--message", "wanted", "--gates", "domain", "--paths", "tracked.txt", ok=False)

    def test_gate_commit_accepts_explicit_new_file(self):
        self.start()
        self.pass_gate()
        (self.repo / "new.txt").write_text("new\n")
        result = run(self.repo, "gate-commit", "--message", "new file", "--gates", "domain", "--paths", "new.txt")
        self.assertEqual(len(result.stdout.strip()), 40)
        tracked = subprocess.run(
            ["git", "ls-files", "new.txt"], cwd=self.repo, check=True, text=True, capture_output=True
        ).stdout.strip()
        self.assertEqual(tracked, "new.txt")

    def test_gate_commit_accepts_tracked_deletion_and_nonsecret_source_name(self):
        (self.repo / "test_secret_loader.py").write_text("safe source\n")
        subprocess.run(["git", "add", "test_secret_loader.py"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=self.repo, check=True, capture_output=True)
        self.start()
        self.pass_gate()
        (self.repo / "tracked.txt").unlink()
        (self.repo / "test_secret_loader.py").write_text("changed safe source\n")
        run(
            self.repo, "gate-commit", "--message", "delete and edit", "--gates", "domain", "--paths",
            "tracked.txt", "test_secret_loader.py",
        )

    def test_final_push_refuses_precycle_ahead_commit(self):
        remote = Path(self.temp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        (self.repo / "tracked.txt").write_text("before cycle\n")
        subprocess.run(["git", "commit", "-am", "before"], cwd=self.repo, check=True, capture_output=True)
        self.start()
        self.pass_gate()
        self.review_artifacts()
        self.pass_gates()
        run(self.repo, "final-push", ok=False)

    def test_final_push_refuses_changed_remote_url(self):
        remote = Path(self.temp.name) / "remote.git"
        other = Path(self.temp.name) / "other.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "init", "--bare", str(other)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        self.start()
        self.pass_gate()
        (self.repo / "docs/specs/test/CHANGELOG.md").write_text("completed\n")
        run(
            self.repo, "gate-commit", "--message", "cycle change", "--gates", "domain", "--paths",
            "docs/specs/test/CHANGELOG.md",
        )
        self.review_artifacts()
        run(
            self.repo, "review-artifact", "CHANGELOG", "--result", "changed",
            "--reason", "recorded", "--path", "docs/specs/test/CHANGELOG.md",
        )
        self.pass_gates()
        subprocess.run(["git", "remote", "set-url", "origin", str(other)], cwd=self.repo, check=True)
        result = run(self.repo, "final-push", ok=False)
        self.assertIn("destination changed", result.stderr)

    def test_final_push_to_local_bare_remote(self):
        remote = Path(self.temp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        self.start()
        self.pass_gate()
        (self.repo / "tracked.txt").write_text("cycle\n")
        (self.repo / "docs/specs/test/BACKLOG.md").write_text("done\n")
        (self.repo / "docs/specs/test/CHANGELOG.md").write_text("completed\n")
        run(
            self.repo, "gate-commit", "--message", "cycle change", "--gates", "domain", "--paths",
            "tracked.txt", "docs/specs/test/BACKLOG.md", "docs/specs/test/CHANGELOG.md",
        )
        for name, result, reason, artifact_path in (
            ("README", "unchanged", "no durable truth changed", None),
            ("BACKLOG", "changed", "cycle completed", "docs/specs/test/BACKLOG.md"),
            ("CHANGELOG", "changed", "completion recorded", "docs/specs/test/CHANGELOG.md"),
        ):
            command = ["review-artifact", name, "--result", result, "--reason", reason]
            if artifact_path:
                command += ["--path", artifact_path]
            run(self.repo, *command)
        self.pass_gates()
        run(self.repo, "final-push")
        self.assertFalse((self.repo / ".git/dbsctr/active").exists())
        self.assertEqual(run(self.repo, "status", "--json").stdout.strip(), "null")

    def test_final_push_targets_recorded_upstream_branch(self):
        remote = Path(self.temp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "push", "-u", "origin", "HEAD:main"], cwd=self.repo, check=True,
            capture_output=True,
        )
        self.start()
        self.pass_gate()
        (self.repo / "tracked.txt").write_text("cycle\n")
        (self.repo / "docs/specs/test/CHANGELOG.md").write_text("completed\n")
        run(
            self.repo, "gate-commit", "--message", "cycle change", "--gates", "domain", "--paths",
            "tracked.txt", "docs/specs/test/CHANGELOG.md",
        )
        run(self.repo, "review-artifact", "README", "--result", "unchanged", "--reason", "accurate")
        run(self.repo, "review-artifact", "BACKLOG", "--result", "unchanged", "--reason", "accurate")
        run(
            self.repo, "review-artifact", "CHANGELOG", "--result", "changed",
            "--reason", "recorded", "--path", "docs/specs/test/CHANGELOG.md",
        )
        self.pass_gates()
        run(self.repo, "final-push")
        local = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo, check=True, text=True,
                               capture_output=True).stdout.strip()
        pushed = subprocess.run(["git", "rev-parse", "refs/heads/main"], cwd=remote, check=True,
                                text=True, capture_output=True).stdout.strip()
        self.assertEqual(local, pushed)

    def test_final_push_requires_changelog_change(self):
        remote = Path(self.temp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        self.start()
        self.pass_gate()
        (self.repo / "tracked.txt").write_text("cycle\n")
        run(self.repo, "gate-commit", "--message", "cycle change", "--gates", "domain", "--paths", "tracked.txt")
        self.review_artifacts()
        self.pass_gates()
        result = run(self.repo, "final-push", ok=False)
        self.assertIn("CHANGELOG", result.stderr)

    def test_final_push_rejects_dirty_dvc_status(self):
        (self.repo / ".dvc").mkdir()
        (self.repo / ".dvc/config").write_text("[core]\n")
        subprocess.run(["git", "add", ".dvc/config"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "dvc fixture"], cwd=self.repo, check=True,
                       capture_output=True)
        remote = Path(self.temp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        self.start()
        self.pass_gate()
        run(
            self.repo, "record-dvc-push", "--head", "0" * 40,
            "--evidence", "wrong", ok=False,
        )
        (self.repo / "docs/specs/test/CHANGELOG.md").write_text("completed\n")
        run(
            self.repo, "gate-commit", "--message", "cycle change", "--gates", "domain", "--paths",
            "docs/specs/test/CHANGELOG.md",
        )
        self.review_artifacts()
        run(
            self.repo, "review-artifact", "CHANGELOG", "--result", "changed",
            "--reason", "recorded", "--path", "docs/specs/test/CHANGELOG.md",
        )
        self.pass_gates()
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo, check=True, text=True,
                              capture_output=True).stdout.strip()
        run(self.repo, "record-dvc-push", "--head", head, "--evidence", "approved dvc push")
        fake_bin = Path(self.temp.name) / "bin"
        fake_bin.mkdir()
        fake_dvc = fake_bin / "dvc"
        fake_dvc.write_text("#!/bin/sh\nprintf 'changed data.dvc\\n'\n")
        fake_dvc.chmod(0o755)
        env = {**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}"}
        result = run(self.repo, "final-push", ok=False, env=env)
        self.assertIn("changed or missing", result.stderr)


if __name__ == "__main__":
    unittest.main()
