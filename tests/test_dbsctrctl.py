"""Focused subprocess contracts for dbsctrctl."""

import json
import fcntl
import hashlib
import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock
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

    def plan_path(self, intent="local"):
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
        return plan

    def start(self, intent="local"):
        plan = self.plan_path(intent)
        return run(self.repo, "start", "--cycle-id", "cycle-1", "--context", "test",
                   "--risk", "routine", "--delivery-intent", intent, "--plan", str(plan))

    def record_path(self, repo=None):
        return (repo or self.repo) / ".git/dbsctr/cycles/cycle-1.json"

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
                self.record_gate(gate)

    def pass_gate(self, gate="domain"):
        self.record_gate(gate)

    def record_gate(self, gate, code=0, paths=()):
        command = ["record-evidence", gate, "--authority", "test"]
        for path in paths:
            command += ["--path", path]
        return run(self.repo, *command, "--", sys.executable, "-c", f"raise SystemExit({code})")

    def test_start_records_current_method_revision_and_release_default(self):
        self.start()
        record = json.loads(self.record_path().read_text())
        self.assertEqual(record["method_revision"], "3.10")
        self.assertEqual(record["schema_version"], 3)
        self.assertEqual(record["evidence"], {"version": 1, "items": {}})
        self.assertEqual(record["engineering_profile"]["path"], "docs/specs/test/README.md")
        self.assertRegex(record["engineering_profile"]["blob"], r"^[0-9a-f]+$")
        self.assertEqual(record["state"], "active")
        self.assertIsNone(record["git"]["upstream"])
        self.assertEqual(record["gates"]["release"], {
            "applicability": "not_applicable", "result": "not_run", "reason": "delivery intent is not release"
        })
        self.assertEqual(set(record["artifact_reviews"]), {"README", "BACKLOG", "CHANGELOG"})

    def test_exclusive_record_failure_leaves_no_reserved_target(self):
        loader = importlib.machinery.SourceFileLoader("dbsctrctl_test_module", str(SCRIPT))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        target = Path(self.temp.name) / "record.json"
        with mock.patch.object(module.json, "dump", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                module.exclusive_json(target, {"cycle": "test"})
        self.assertFalse(target.exists())

    def test_start_refuses_dirty_worktree(self):
        (self.repo / "tracked.txt").write_text("pre-cycle\n")
        result = run(
            self.repo, "start", "--cycle-id", "cycle-1", "--context", "test",
            "--risk", "routine", "--delivery-intent", "local", "--plan", str(self.plan_path()), ok=False,
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

        duplicate = '{"profile":"docs/specs/test/README.md","profile":"docs/specs/test/README.md","gates":{}}'
        result = run(
            self.repo, "start", "--cycle-id", "cycle-1", "--context", "test",
            "--risk", "routine", "--delivery-intent", "local", "--plan", "-", ok=False,
            input_text=duplicate,
        )
        self.assertIn("duplicate JSON key", result.stderr)

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
            self.repo, "record-evidence", "behavior", "--authority", "test", "--",
            sys.executable, "-c", "raise SystemExit(0)", ok=False,
        )
        self.assertIn("predecessor", result.stderr)
        self.record_gate("behavior", 1)
        self.record_gate("domain")
        run(
            self.repo, "approve-exception", "behavior", "--kind", "deferred",
            "--rationale", "approved", "--owner", "owner", "--review-condition", "next cycle",
        )
        self.record_gate("spec")
        run(self.repo, "set-gate", "domain", "--result", "pending")
        record = json.loads(self.record_path().read_text())
        self.assertEqual(record["gates"]["spec"]["result"], "pending")

    def test_record_evidence_runs_literal_command_and_binds_gate(self):
        self.start()
        marker = self.repo / "shell-expanded"
        run(self.repo, "record-evidence", "domain", "--authority", "unit", "--",
            sys.executable, "-c", "import sys; assert sys.stdin.read() == ''; print('ok')", f"$(touch {marker})")
        record = json.loads(self.record_path().read_text())
        evidence_id = record["gates"]["domain"]["evidence"]
        envelope = record["evidence"]["items"][evidence_id]
        self.assertEqual(envelope["result"], "passed")
        self.assertEqual(envelope["argv"][-1], "[REDACTED]")
        self.assertFalse(marker.exists())
        self.assertEqual(envelope["urls"], [])
        self.assertNotIn("environment", json.dumps(record))

    def test_record_evidence_redacts_or_withholds_secrets(self):
        self.start()
        secret = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        run(self.repo, "record-evidence", "domain", "--authority", "unit", "--",
            sys.executable, "-c", f"print('{secret}')", "--token", secret)
        record = json.loads(self.record_path().read_text())
        envelope = next(iter(record["evidence"]["items"].values()))
        serialized = json.dumps(envelope)
        self.assertNotIn(secret, serialized)
        self.assertEqual(envelope["argv"][-1], "[REDACTED]")
        self.assertEqual(envelope["content"], {"status": "withheld", "reason": "unclassified"})

    def test_record_evidence_retains_only_allowlisted_output_and_sanitizes_argv(self):
        self.start()
        run(self.repo, "record-evidence", "domain", "--authority", "unit", "--",
            sys.executable, "-c", "print('ok')", "--file=private.txt", "short-secret", "-psecret")
        envelope = next(iter(json.loads(self.record_path().read_text())["evidence"]["items"].values()))
        self.assertEqual(envelope["argv"], [Path(sys.executable).name, "[REDACTED]", "[REDACTED]",
                                             "--file=[REDACTED]", "[REDACTED]", "[REDACTED]"])
        self.assertEqual(envelope["content"]["status"], "sidecar")
        self.assertIn("path", envelope["content"])

    def test_record_evidence_failure_and_set_gate_rejects_arbitrary_schema3_evidence(self):
        self.start()
        run(self.repo, "record-evidence", "domain", "--authority", "unit", "--",
            sys.executable, "-c", "raise SystemExit(2)")
        record = json.loads(self.record_path().read_text())
        self.assertEqual(record["gates"]["domain"]["result"], "failed")
        result = run(self.repo, "set-gate", "domain", "--result", "passed", "--evidence", "arbitrary", ok=False)
        self.assertIn("evidence ID", result.stderr)

    def test_record_evidence_withholds_binary_and_overflow_output(self):
        self.start()
        run(self.repo, "record-evidence", "domain", "--authority", "unit", "--",
            sys.executable, "-c", "import os; os.write(1, b'\\xff')")
        record = json.loads(self.record_path().read_text())
        binary = next(iter(record["evidence"]["items"].values()))
        self.assertEqual(binary["content"]["status"], "withheld")
        self.assertEqual(binary["result"], "passed")

        run(self.repo, "record-evidence", "behavior", "--authority", "unit", "--", sys.executable, "-c",
            "import os; os.write(1, b'x' * (1024 * 1024 + 1))")
        overflow = next(item for item in json.loads(self.record_path().read_text())["evidence"]["items"].values()
                        if item["gate"] == "behavior")
        self.assertEqual(overflow["result"], "unavailable")
        self.assertTrue(overflow["raw"]["truncated"])
        self.assertEqual(overflow["content"], {"status": "withheld", "reason": "overflow"})

    def test_record_evidence_sidecar_is_hashed_private_and_deduplicated(self):
        self.start()
        command = [sys.executable, "-c", "print('ok')"]
        run(self.repo, "record-evidence", "domain", "--authority", "unit", "--", *command)
        run(self.repo, "record-evidence", "behavior", "--authority", "unit", "--", *command)
        items = list(json.loads(self.record_path().read_text())["evidence"]["items"].values())
        digest = items[0]["content"]["sha256"]
        sidecar = self.repo / ".git/dbsctr/evidence/cycle-1" / digest
        self.assertEqual(hashlib.sha256(sidecar.read_bytes()).hexdigest(), digest)
        self.assertEqual(sidecar.stat().st_mode & 0o777, 0o600)
        self.assertEqual(items[1]["content"]["sha256"], digest)

    def test_gate_commit_binds_current_evidence_and_rejects_tampered_sidecar(self):
        self.start()
        (self.repo / "tracked.txt").write_text("domain\n")
        run(self.repo, "record-evidence", "domain", "--authority", "unit", "--path", "tracked.txt",
            "--", sys.executable, "-c", "print('ok')")
        run(self.repo, "gate-commit", "--message", "domain", "--gates", "domain", "--paths", "tracked.txt")
        record = json.loads(self.record_path().read_text())
        domain = record["evidence"]["items"][record["gates"]["domain"]["evidence"]]
        self.assertEqual(domain["commit"], subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo,
                         text=True, capture_output=True, check=True).stdout.strip())
        (self.repo / "tracked.txt").write_text("behavior\n")
        run(self.repo, "record-evidence", "behavior", "--authority", "unit", "--path", "tracked.txt",
            "--", sys.executable, "-c", "print('ok')")
        behavior = next(item for item in json.loads(self.record_path().read_text())["evidence"]["items"].values()
                        if item["gate"] == "behavior")
        (self.repo / ".git/dbsctr" / behavior["content"]["path"]).unlink()
        result = run(self.repo, "gate-commit", "--message", "behavior", "--gates", "behavior",
                     "--paths", "tracked.txt", ok=False)
        self.assertIn("sidecar", result.stderr)

    def test_schema3_rejects_stale_cross_gate_and_precreated_sidecar_evidence(self):
        self.start()
        evidence_id = self.record_gate("domain", paths=("tracked.txt",)).stdout.strip()
        cross_gate = run(self.repo, "set-gate", "behavior", "--result", "passed",
                         "--evidence", evidence_id, ok=False)
        self.assertIn("matching stored evidence ID", cross_gate.stderr)
        (self.repo / "tracked.txt").write_text("new head\n")
        subprocess.run(["git", "commit", "-am", "advance"], cwd=self.repo, check=True,
                       capture_output=True)
        stale = run(self.repo, "gate-commit", "--message", "stale", "--gates", "domain",
                    "--paths", "tracked.txt", ok=False)
        self.assertIn("evidence HEAD is stale", stale.stderr)

    def test_schema3_rejects_precreated_sidecar_symlink(self):
        self.start()
        directory = self.repo / ".git/dbsctr/evidence/cycle-1"
        directory.mkdir(parents=True, mode=0o700)
        digest = hashlib.sha256(b"ok\n").hexdigest()
        (directory / digest).symlink_to(self.repo / "tracked.txt")
        unsafe = run(self.repo, "record-evidence", "domain", "--authority", "test", "--",
                     sys.executable, "-c", "print('ok')", ok=False)
        self.assertIn("unsafe evidence sidecar", unsafe.stderr)

    def test_schema3_rejects_paths_changed_after_evidence(self):
        self.start()
        (self.repo / "tracked.txt").write_text("validated\n")
        self.record_gate("domain", paths=("tracked.txt",))
        (self.repo / "tracked.txt").write_text("changed later\n")
        result = run(self.repo, "gate-commit", "--message", "unsafe", "--gates", "domain",
                     "--paths", "tracked.txt", ok=False)
        self.assertIn("changed after validation", result.stderr)

    def test_schema3_rejects_commit_hook_path_changes(self):
        self.start()
        (self.repo / "tracked.txt").write_text("validated\n")
        self.record_gate("domain", paths=("tracked.txt",))
        hook = self.repo / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\nprintf 'hook changed\\n' > tracked.txt\ngit add tracked.txt\n")
        hook.chmod(0o755)
        result = run(self.repo, "gate-commit", "--message", "hook", "--gates", "domain",
                     "--paths", "tracked.txt", ok=False)
        self.assertIn("committed paths differ from evidence", result.stderr)

    def test_record_evidence_kills_resistant_process_group_without_leaking_argv(self):
        self.start()
        script = (
            "import os,signal,time; child=os.fork(); "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(10)"
        )
        result = run(self.repo, "record-evidence", "domain", "--authority", "unit", "--timeout", "1",
                     "--", sys.executable, "-c", script)
        evidence_id = result.stdout.strip()
        envelope = json.loads(self.record_path().read_text())["evidence"]["items"][evidence_id]
        self.assertEqual(envelope["result"], "unavailable")
        self.assertEqual(envelope["content"], {"status": "withheld", "reason": "timeout"})
        self.assertNotIn(script, json.dumps(envelope))

    def test_risk_and_applicability_only_tighten(self):
        self.start()
        record_path = self.record_path()
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
        record_path = self.record_path()
        record = json.loads(record_path.read_text())
        record.pop("schema_version")
        record.pop("engineering_profile")
        record.pop("applicability_plan")
        record["method_revision"] = "3.1"
        record_path.write_text(json.dumps(record))
        run(self.repo, "set-gate", "behavior", "--result", "passed", "--evidence", "legacy")

    def test_unknown_cycle_schema_is_rejected(self):
        self.start()
        record_path = self.record_path()
        record = json.loads(record_path.read_text())
        record["schema_version"] = 99
        record_path.write_text(json.dumps(record))
        result = run(self.repo, "status", ok=False)
        self.assertIn("unsupported Cycle Record schema", result.stderr)

    def test_linked_worktrees_have_isolated_active_cycles_and_global_ids(self):
        second = Path(self.temp.name) / "second"
        third = Path(self.temp.name) / "third"
        subprocess.run(["git", "worktree", "add", "-b", "second", str(second), "HEAD"],
                       cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "worktree", "add", "-b", "third", str(third), "HEAD"],
                       cwd=self.repo, check=True, capture_output=True)
        self.start()
        plan = Path(self.temp.name) / "plan.json"
        duplicate = run(
            second, "start", "--cycle-id", "cycle-1", "--context", "test", "--risk", "routine",
            "--delivery-intent", "local", "--plan", str(plan), ok=False,
        )
        self.assertIn("cycle record already exists", duplicate.stderr)
        run(
            second, "start", "--cycle-id", "cycle-2", "--context", "test", "--risk", "routine",
            "--delivery-intent", "local", "--plan", str(plan),
        )
        first_status = json.loads(run(self.repo, "status", "--json").stdout)
        second_status = json.loads(run(second, "status", "--json").stdout)
        self.assertEqual(first_status["cycle_id"], "cycle-1")
        self.assertEqual(second_status["cycle_id"], "cycle-2")
        self.assertEqual(run(third, "status", "--json").stdout.strip(), "null")
        self.assertNotEqual(first_status["worktree"]["id"], second_status["worktree"]["id"])
        self.assertTrue((self.repo / ".git/dbsctr/cycles/cycle-2.json").exists())

    def test_concurrent_linked_starts_reserve_cycle_id_atomically(self):
        second = Path(self.temp.name) / "second"
        subprocess.run(["git", "worktree", "add", "-b", "second", str(second), "HEAD"],
                       cwd=self.repo, check=True, capture_output=True)
        self.start()
        first_record = self.record_path().read_text()
        first_pointer = next((self.repo / ".git/dbsctr/worktrees").glob("*/active"))
        first_pointer.unlink()
        self.record_path().unlink()
        plan = str(Path(self.temp.name) / "plan.json")
        command = [sys.executable, str(SCRIPT), "start", "--cycle-id", "race", "--context", "test",
                   "--risk", "routine", "--delivery-intent", "local", "--plan", plan]
        processes = [
            subprocess.Popen(command, cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for repo in (self.repo, second)
        ]
        results = [process.communicate() + (process.returncode,) for process in processes]
        self.assertEqual(sorted(result[2] for result in results), [0, 1])
        self.assertIn("cycle record already exists", "".join(result[1] for result in results))
        self.assertTrue((self.repo / ".git/dbsctr/cycles/race.json").exists())
        self.assertEqual(sum(1 for path in (self.repo / ".git/dbsctr/worktrees").glob("*/active")
                             if path.read_text().strip() == "race"), 1)
        self.assertTrue(first_record)

    def test_remote_aliases_share_delivery_lock(self):
        remote = Path(self.temp.name) / "remote.git"
        second = Path(self.temp.name) / "second"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "remote", "add", "mirror", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        subprocess.run(["git", "fetch", "mirror"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "worktree", "add", "-b", "second", str(second), "HEAD"],
                       cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "branch", "--set-upstream-to=mirror/master", "second"],
                       cwd=self.repo, check=True, capture_output=True)
        self.start()
        plan = str(Path(self.temp.name) / "plan.json")
        run(second, "start", "--cycle-id", "cycle-2", "--context", "test", "--risk", "routine",
            "--delivery-intent", "local", "--plan", plan)
        first = json.loads(self.record_path().read_text())
        second_record = json.loads((self.repo / ".git/dbsctr/cycles/cycle-2.json").read_text())
        self.assertEqual(first["delivery"]["lock_id"], second_record["delivery"]["lock_id"])

    def test_final_push_refuses_contended_target_lock(self):
        remote = Path(self.temp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "team/origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "team/origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        self.start()
        record = json.loads(self.record_path().read_text())
        lock = self.repo / ".git/dbsctr/locks" / f"{record['delivery']['lock_id']}.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        with lock.open("a+") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = run(self.repo, "final-push", ok=False)
        self.assertIn("locked by another DBSCTR cycle", result.stderr)

    def test_begin_isolates_cycle_from_dirty_source_worktree(self):
        remote = Path(self.temp.name) / "remote.git"
        worktrees = Path(self.temp.name) / "isolated"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        (self.repo / "tracked.txt").write_text("unrelated dirty work\n")
        result = run(
            self.repo, "begin", "--cycle-id", "isolated-1", "--context", "test",
            "--risk", "routine", "--delivery-intent", "local", "--plan", str(self.plan_path()),
            "--worktree-root", str(worktrees),
        )
        handoff = json.loads(result.stdout)
        isolated = Path(handoff["worktree"])
        self.assertTrue(isolated.is_dir())
        self.assertEqual((self.repo / "tracked.txt").read_text(), "unrelated dirty work\n")
        record = json.loads((self.repo / ".git/dbsctr/cycles/isolated-1.json").read_text())
        self.assertTrue(record["worktree"]["created_by_dbsctr"])
        self.assertEqual(record["worktree"]["path"], str(isolated))
        self.assertEqual(json.loads(run(isolated, "status", "--json").stdout)["cycle_id"], "isolated-1")
        self.assertEqual(run(self.repo, "status", "--json").stdout.strip(), "null")

    def test_begin_fetches_before_classifying_ahead_commits(self):
        remote = Path(self.temp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        (self.repo / "tracked.txt").write_text("already remote\n")
        subprocess.run(["git", "commit", "-am", "already remote"], cwd=self.repo, check=True,
                       capture_output=True)
        subprocess.run(["git", "push", str(remote), "HEAD:master"], cwd=self.repo, check=True,
                       capture_output=True)
        result = run(
            self.repo, "begin", "--cycle-id", "isolated-1", "--context", "test",
            "--risk", "routine", "--delivery-intent", "local", "--plan", str(self.plan_path()),
            "--worktree-root", str(Path(self.temp.name) / "isolated"),
        )
        self.assertEqual(json.loads(result.stdout)["cycle_id"], "isolated-1")

    def test_begin_rejects_unknown_ahead_commits(self):
        remote = Path(self.temp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        (self.repo / "tracked.txt").write_text("ahead\n")
        subprocess.run(["git", "commit", "-am", "ahead"], cwd=self.repo, check=True, capture_output=True)
        result = run(
            self.repo, "begin", "--cycle-id", "isolated-1", "--context", "test",
            "--risk", "routine", "--delivery-intent", "local", "--plan", str(self.plan_path()),
            "--worktree-root", str(Path(self.temp.name) / "isolated"), ok=False,
        )
        self.assertIn("unknown commits are ahead", result.stderr)

    def test_cleanup_removes_only_clean_completed_dbsctr_worktree(self):
        remote = Path(self.temp.name) / "remote.git"
        worktrees = Path(self.temp.name) / "isolated"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        handoff = json.loads(run(
            self.repo, "begin", "--cycle-id", "isolated-1", "--context", "test",
            "--risk", "routine", "--delivery-intent", "local", "--plan", str(self.plan_path()),
            "--worktree-root", str(worktrees),
        ).stdout)
        record_path = self.repo / ".git/dbsctr/cycles/isolated-1.json"
        record = json.loads(record_path.read_text())
        record.update({"state": "completed", "completed_at": "2026-01-01T00:00:00Z"})
        record_path.write_text(json.dumps(record))
        evidence = self.repo / ".git/dbsctr/evidence/isolated-1"
        evidence.mkdir(parents=True)
        (evidence / "retained-sidecar").write_bytes(b"safe")
        pointer = self.repo / ".git/dbsctr/worktrees" / record["worktree"]["id"] / "active"
        pointer.unlink()
        loader = importlib.machinery.SourceFileLoader("dbsctrctl_cleanup_module", str(SCRIPT))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        with mock.patch.object(module, "root_dir", return_value=self.repo), \
             mock.patch.object(module.shutil, "rmtree", side_effect=OSError("interrupted cleanup")):
            with self.assertRaises(OSError):
                module.command_cleanup(SimpleNamespace(cycle_id="isolated-1", now=True))
        parked_record = json.loads(record_path.read_text())
        self.assertEqual(parked_record["cleanup"]["state"], "evidence_parked")
        self.assertTrue((evidence.parent / "isolated-1.cleanup").exists())
        run(self.repo, "cleanup", "--cycle-id", "isolated-1", "--now")
        self.assertFalse(Path(handoff["worktree"]).exists())
        self.assertFalse(record_path.exists())
        self.assertFalse(evidence.exists())

    def test_cleanup_rejects_low_level_or_drifted_worktree(self):
        self.start()
        record_path = self.record_path()
        record = json.loads(record_path.read_text())
        record.update({"state": "completed", "completed_at": "2026-01-01T00:00:00Z"})
        record_path.write_text(json.dumps(record))
        result = run(self.repo, "cleanup", "--cycle-id", "cycle-1", "--now", ok=False)
        self.assertIn("DBSCTR-created", result.stderr)

        record["worktree"]["created_by_dbsctr"] = True
        record_path.write_text(json.dumps(record))
        other = Path(self.temp.name) / "other"
        subprocess.run(["git", "worktree", "add", "-b", "other", str(other), "HEAD"],
                       cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "switch", "-c", "drift"], cwd=self.repo, check=True,
                       capture_output=True)
        result = run(other, "cleanup", "--cycle-id", "cycle-1", "--now", ok=False)
        self.assertIn("cycle worktree branch changed", result.stderr)

    def test_audit_reads_fixed_commit_and_excludes_dirty_overlay(self):
        built_from = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo, check=True,
                                    text=True, capture_output=True).stdout.strip()
        incomplete = self.repo / "docs/specs/incomplete"
        incomplete.mkdir(parents=True)
        (incomplete / "README.md").write_text("# Incomplete\n")
        graph = self.repo / "graphify-out"
        graph.mkdir()
        (graph / "GRAPH_REPORT.md").write_text(f"Built from commit: `{built_from}`\n")
        old_name = self.repo / "old name.txt"
        old_name.write_text("rename fixture\n")
        subprocess.run(["git", "add", "docs/specs/incomplete", "graphify-out", "old name.txt"], cwd=self.repo,
                       check=True)
        subprocess.run(["git", "commit", "-m", "audit fixture"], cwd=self.repo, check=True,
                       capture_output=True)
        audited = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo, check=True,
                                 text=True, capture_output=True).stdout.strip()
        (incomplete / "BACKLOG.md").write_text("dirty overlay\n")
        subprocess.run(["git", "mv", "old name.txt", "new name.txt"], cwd=self.repo, check=True)
        index_mtime = (self.repo / ".git/index").stat().st_mtime_ns
        result = json.loads(run(self.repo, "audit", "--commit", audited, "--json").stdout)
        self.assertEqual(result["commit"], audited)
        self.assertIn("docs/specs/incomplete/BACKLOG.md", result["dirty_overlay_excluded"])
        self.assertIn("old name.txt", result["dirty_overlay_excluded"])
        self.assertIn("new name.txt", result["dirty_overlay_excluded"])
        self.assertEqual((self.repo / ".git/index").stat().st_mtime_ns, index_mtime)
        findings = {(item["code"], item["path"]) for item in result["findings"]}
        self.assertIn(("missing_lifecycle_artifact", "docs/specs/incomplete/BACKLOG.md"), findings)
        self.assertIn(("missing_lifecycle_artifact", "docs/specs/incomplete/CHANGELOG.md"), findings)
        self.assertIn(("stale_graph", "graphify-out/GRAPH_REPORT.md"), findings)

    def test_audit_flags_unverifiable_graph_metadata(self):
        graph = self.repo / "graphify-out"
        graph.mkdir()
        (graph / "GRAPH_REPORT.md").write_text("Built from commit: `abc`\n")
        subprocess.run(["git", "add", "graphify-out"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "bad graph marker"], cwd=self.repo, check=True,
                       capture_output=True)
        result = json.loads(run(self.repo, "audit", "--json").stdout)
        self.assertIn("unverified_graph_freshness", {item["code"] for item in result["findings"]})

    def test_audit_reports_non_utf8_dirty_filename(self):
        raw = os.fsencode(self.repo) + b"/bad-\xff"
        try:
            descriptor = os.open(raw, os.O_WRONLY | os.O_CREAT, 0o600)
        except OSError as error:
            self.skipTest(f"filesystem rejects non-UTF-8 names: {error}")
        os.close(descriptor)
        result = json.loads(run(self.repo, "audit", "--json").stdout)
        self.assertIn(b"bad-\xff", [os.fsencode(path) for path in result["dirty_overlay_excluded"]])

    def test_inspect_reads_only_the_resolved_commit_and_reports_overlay(self):
        (self.repo / "tracked.txt").write_text("committed needle\n")
        (self.repo / "nested").mkdir()
        (self.repo / "nested" / "match.txt").write_text("needle twice: needle\n")
        (self.repo / "binary.bin").write_bytes(b"\0binary")
        subprocess.run(["git", "add", "tracked.txt", "nested", "binary.bin"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "inspect fixture"], cwd=self.repo, check=True,
                       capture_output=True)
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo, check=True, text=True,
                                capture_output=True).stdout.strip()
        (self.repo / "tracked.txt").write_text("dirty overlay\n")

        read = json.loads(run(
            self.repo, "inspect", "--commit", "HEAD", "--action", "read", "--path", "tracked.txt", "--json"
        ).stdout)
        self.assertEqual(read["commit"], commit)
        self.assertEqual(read["content"], "committed needle\n")
        self.assertIn("tracked.txt", read["dirty_overlay_excluded"])
        self.assertFalse(read["truncated"])

        binary = json.loads(run(
            self.repo, "inspect", "--commit", commit, "--action", "read", "--path", "binary.bin", "--json"
        ).stdout)
        self.assertTrue(binary["binary"])
        self.assertNotIn("content", binary)

        metadata = json.loads(run(
            self.repo, "inspect", "--commit", commit, "--action", "object", "--path", "tracked.txt", "--json"
        ).stdout)
        self.assertEqual(metadata["type"], "blob")
        self.assertEqual(metadata["size"], len("committed needle\n"))

        search = json.loads(run(
            self.repo, "inspect", "--commit", commit, "--action", "search", "--query", "needle", "--json"
        ).stdout)
        self.assertEqual([item["path"] for item in search["matches"]], ["nested/match.txt", "tracked.txt"])

    def test_inspect_rejects_unsafe_paths_and_has_deterministic_continuations(self):
        (self.repo / "many").mkdir()
        for index in range(3):
            (self.repo / "many" / f"{index}.txt").write_text(f"line {index}\n")
        subprocess.run(["git", "add", "many"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "tree fixture"], cwd=self.repo, check=True,
                       capture_output=True)
        first = json.loads(run(
            self.repo, "inspect", "--action", "tree", "--path", "many", "--limit", "2", "--json"
        ).stdout)
        self.assertEqual([item["path"] for item in first["entries"]], ["many/0.txt", "many/1.txt"])
        self.assertEqual(first["continuation"], {"cursor": 2})
        second = json.loads(run(
            self.repo, "inspect", "--action", "tree", "--path", "many", "--limit", "2", "--cursor", "2", "--json"
        ).stdout)
        self.assertEqual([item["path"] for item in second["entries"]], ["many/2.txt"])
        self.assertIsNone(second["continuation"])
        for path in ("/etc/passwd", "../tracked.txt", "many/../0.txt", "bad\npath"):
            result = run(
                self.repo, "inspect", "--action", "read", "--path", path, "--json", ok=False
            )
            self.assertIn("unsafe path", result.stderr)

    def test_inspect_bounds_scopes_and_validates_action_arguments(self):
        (self.repo / "scope").mkdir()
        (self.repo / "scope" / "literal.txt").write_text("a.b\nneedle\n")
        (self.repo / "outside.txt").write_text("needle\n")
        (self.repo / "large.txt").write_bytes(b"needle\n" + b"x" * (4 * 1024 * 1024))
        subprocess.run(["git", "add", "scope", "outside.txt", "large.txt"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "inspect bounds fixture"], cwd=self.repo, check=True,
                       capture_output=True)

        root = json.loads(run(self.repo, "inspect", "--action", "tree", "--json").stdout)
        self.assertIn("scope", [item["path"] for item in root["entries"]])
        scoped = json.loads(run(
            self.repo, "inspect", "--action", "search", "--path", "scope", "--query", "needle", "--json"
        ).stdout)
        self.assertEqual([item["path"] for item in scoped["matches"]], ["scope/literal.txt"])
        literal = json.loads(run(
            self.repo, "inspect", "--action", "search", "--query", "a.b", "--json"
        ).stdout)
        self.assertEqual([item["path"] for item in literal["matches"]], ["scope/literal.txt"])
        self.assertEqual(json.loads(run(
            self.repo, "inspect", "--action", "search", "--query", "a.b*", "--json"
        ).stdout)["matches"], [])

        for args, message in (
            (("--action", "read", "--path", "large.txt"), "4194304"),
            (("--action", "tree", "--limit", "101"), "tree limit"),
            (("--action", "search", "--query", "needle", "--excerpt", "2049"), "excerpt limit"),
            (("--action", "object", "--query", "needle"), "not valid"),
            (("--action", "read", "--path", "tracked.txt", "--cursor", "1"), "not valid"),
            (("--action", "tree", "--cursor", "999"), "cursor is outside"),
        ):
            result = run(self.repo, "inspect", *args, "--json", ok=False)
            self.assertIn(message, result.stderr)

    def test_inspect_disables_replacements_and_preserves_utf8_byte_boundaries(self):
        (self.repo / "original.txt").write_text("original\n")
        (self.repo / "replacement.txt").write_text("replacement\n")
        (self.repo / "unicode.txt").write_text("a" * 32767 + "é" + "z\n")
        (self.repo / "excerpt.txt").write_text("ééé needle\n")
        subprocess.run(["git", "add", "original.txt", "replacement.txt", "unicode.txt", "excerpt.txt"],
                       cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "replacement fixture"], cwd=self.repo, check=True,
                       capture_output=True)
        original = subprocess.run(["git", "rev-parse", "HEAD:original.txt"], cwd=self.repo, check=True,
                                  text=True, capture_output=True).stdout.strip()
        replacement = subprocess.run(["git", "rev-parse", "HEAD:replacement.txt"], cwd=self.repo, check=True,
                                     text=True, capture_output=True).stdout.strip()
        subprocess.run(["git", "replace", original, replacement], cwd=self.repo, check=True)

        read = json.loads(run(
            self.repo, "inspect", "--action", "read", "--path", "original.txt", "--json"
        ).stdout)
        self.assertEqual(read["content"], "original\n")
        first = json.loads(run(
            self.repo, "inspect", "--action", "read", "--path", "unicode.txt", "--json"
        ).stdout)
        self.assertEqual(first["continuation"], {"offset": 32767})
        second = json.loads(run(
            self.repo, "inspect", "--action", "read", "--path", "unicode.txt",
            "--offset", "32767", "--limit", "3", "--json"
        ).stdout)
        self.assertEqual(second["content"], "éz")
        invalid = run(
            self.repo, "inspect", "--action", "read", "--path", "unicode.txt",
            "--offset", "32768", "--json", ok=False,
        )
        self.assertIn("UTF-8 boundary", invalid.stderr)

        excerpt = json.loads(run(
            self.repo, "inspect", "--action", "search", "--path", "excerpt.txt",
            "--query", "needle", "--excerpt", "5", "--json",
        ).stdout)["matches"][0]
        self.assertEqual(excerpt["excerpt"], "éé")
        self.assertTrue(excerpt["excerpt_truncated"])

    def test_inspect_bounds_dirty_overlay_reporting(self):
        for index in range(101):
            (self.repo / f"dirty-{index:03}.txt").write_text("dirty\n")
        result = json.loads(run(self.repo, "inspect", "--action", "tree", "--json").stdout)
        self.assertEqual(len(result["dirty_overlay_excluded"]), 100)
        self.assertEqual(result["dirty_overlay_total"], 101)
        self.assertTrue(result["dirty_overlay_truncated"])

    def test_inspect_bounds_overlay_bytes_and_reports_both_rename_paths(self):
        (self.repo / "tracked.txt").rename(self.repo / "renamed.txt")
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True)
        renamed = json.loads(run(self.repo, "inspect", "--action", "tree", "--json").stdout)
        self.assertIn("tracked.txt", renamed["dirty_overlay_excluded"])
        self.assertIn("renamed.txt", renamed["dirty_overlay_excluded"])

        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        nested = self.repo
        for character in "abcd":
            nested /= character * 150
            nested.mkdir()
        for index in range(100):
            (nested / f"{index:03}-{'x' * 180}").write_text("dirty\n")
        bounded = json.loads(run(self.repo, "inspect", "--action", "tree", "--json").stdout)
        self.assertEqual(bounded["dirty_overlay_total"], 100)
        self.assertLess(len(bounded["dirty_overlay_excluded"]), 100)
        self.assertTrue(bounded["dirty_overlay_truncated"])

    def test_profile_change_requires_plan_update_before_commit(self):
        remote = Path(self.temp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        self.start()
        profile = self.repo / "docs/specs/test/README.md"
        profile.write_text("new profile\n")
        self.record_gate("domain", paths=("docs/specs/test/README.md",))
        run(
            self.repo, "gate-commit", "--message", "profile", "--gates", "domain",
            "--paths", "docs/specs/test/README.md",
        )
        record = json.loads(self.record_path().read_text())
        plan = {"profile": "docs/specs/test/README.md", "gates": {
            name: {key: value for key, value in gate.items() if key in ("applicability", "reason")}
            for name, gate in record["gates"].items()
        }}
        (self.repo / "tracked.txt").write_text("change\n")
        self.record_gate("domain", paths=("tracked.txt",))
        result = run(
            self.repo, "gate-commit", "--message", "change", "--gates", "domain",
            "--paths", "tracked.txt", ok=False,
        )
        self.assertIn("update the applicability plan", result.stderr)
        run(self.repo, "update-plan", "--plan", "-", input_text=json.dumps(plan))
        run(
            self.repo, "gate-commit", "--message", "change", "--gates", "domain",
            "--paths", "tracked.txt",
        )
        changelog = self.repo / "docs/specs/test/CHANGELOG.md"
        changelog.write_text("completed\n")
        self.record_gate("domain", paths=("docs/specs/test/CHANGELOG.md",))
        run(
            self.repo, "gate-commit", "--message", "changelog", "--gates", "domain",
            "--paths", "docs/specs/test/CHANGELOG.md",
        )
        run(
            self.repo, "review-artifact", "README", "--result", "changed", "--reason", "profile",
            "--path", "docs/specs/test/README.md",
        )
        run(self.repo, "review-artifact", "BACKLOG", "--result", "unchanged", "--reason", "accurate")
        run(
            self.repo, "review-artifact", "CHANGELOG", "--result", "changed", "--reason", "recorded",
            "--path", "docs/specs/test/CHANGELOG.md",
        )
        self.pass_gates()
        run(self.repo, "final-push")

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
        self.record_gate("domain", 1)
        run(
            self.repo, "approve-exception", "domain", "--kind", "deferred",
            "--rationale", "approved later", "--owner", "owner",
            "--review-condition", "next cycle",
        )
        self.record_gate("domain", 1)
        record = json.loads(self.record_path().read_text())
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
        (self.repo / "tracked.txt").write_text("wanted\n")
        self.record_gate("domain", paths=("tracked.txt",))
        (self.repo / "other.txt").write_text("base\n")
        subprocess.run(["git", "add", "other.txt"], cwd=self.repo, check=True)
        run(self.repo, "gate-commit", "--message", "wanted", "--gates", "domain", "--paths", "tracked.txt", ok=False)

    def test_gate_commit_accepts_explicit_new_file(self):
        self.start()
        (self.repo / "new.txt").write_text("new\n")
        self.record_gate("domain", paths=("new.txt",))
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
        (self.repo / "tracked.txt").unlink()
        (self.repo / "test_secret_loader.py").write_text("changed safe source\n")
        self.record_gate("domain", paths=("tracked.txt", "test_secret_loader.py"))
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

    def test_final_push_fetches_and_rejects_advanced_target_before_finalizing(self):
        remote = Path(self.temp.name) / "remote.git"
        other = Path(self.temp.name) / "other"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        self.start()
        changelog = self.repo / "docs/specs/test/CHANGELOG.md"
        changelog.write_text("completed\n")
        self.record_gate("domain", paths=("docs/specs/test/CHANGELOG.md",))
        run(self.repo, "gate-commit", "--message", "cycle", "--gates", "domain", "--paths",
            "docs/specs/test/CHANGELOG.md")
        run(self.repo, "review-artifact", "README", "--result", "unchanged", "--reason", "accurate")
        run(self.repo, "review-artifact", "BACKLOG", "--result", "unchanged", "--reason", "accurate")
        run(self.repo, "review-artifact", "CHANGELOG", "--result", "changed", "--reason", "recorded",
            "--path", "docs/specs/test/CHANGELOG.md")
        self.pass_gates()
        subprocess.run(["git", "clone", str(remote), str(other)], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "other@example.com"], cwd=other, check=True)
        subprocess.run(["git", "config", "user.name", "Other"], cwd=other, check=True)
        (other / "other.txt").write_text("advance\n")
        subprocess.run(["git", "add", "other.txt"], cwd=other, check=True)
        subprocess.run(["git", "commit", "-m", "advance"], cwd=other, check=True,
                       capture_output=True)
        subprocess.run(["git", "push"], cwd=other, check=True, capture_output=True)
        result = run(self.repo, "final-push", ok=False)
        self.assertIn("delivery target advanced", result.stderr)
        self.assertEqual(json.loads(self.record_path().read_text())["state"], "active")

    def test_final_push_refuses_changed_remote_url(self):
        remote = Path(self.temp.name) / "remote.git"
        other = Path(self.temp.name) / "other.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "init", "--bare", str(other)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=self.repo, check=True,
                       capture_output=True)
        self.start()
        (self.repo / "docs/specs/test/CHANGELOG.md").write_text("completed\n")
        self.record_gate("domain", paths=("docs/specs/test/CHANGELOG.md",))
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
        (self.repo / "tracked.txt").write_text("cycle\n")
        (self.repo / "docs/specs/test/BACKLOG.md").write_text("done\n")
        (self.repo / "docs/specs/test/CHANGELOG.md").write_text("completed\n")
        self.record_gate("domain", paths=(
            "tracked.txt", "docs/specs/test/BACKLOG.md", "docs/specs/test/CHANGELOG.md",
        ))
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
        self.assertFalse(any((self.repo / ".git/dbsctr/worktrees").glob("*/active")))
        self.assertEqual(json.loads(self.record_path().read_text())["state"], "completed")
        self.assertEqual(run(self.repo, "status", "--json").stdout.strip(), "null")
        record = json.loads(self.record_path().read_text())
        pointer = self.repo / ".git/dbsctr/worktrees" / record["worktree"]["id"] / "active"
        pointer.parent.mkdir(parents=True, exist_ok=True)
        pointer.write_text("cycle-1\n")
        run(self.repo, "final-push")
        self.assertFalse(pointer.exists())

    def test_final_push_targets_recorded_upstream_branch(self):
        remote = Path(self.temp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "push", "-u", "origin", "HEAD:main"], cwd=self.repo, check=True,
            capture_output=True,
        )
        self.start()
        (self.repo / "tracked.txt").write_text("cycle\n")
        (self.repo / "docs/specs/test/CHANGELOG.md").write_text("completed\n")
        self.record_gate("domain", paths=("tracked.txt", "docs/specs/test/CHANGELOG.md"))
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
        (self.repo / "tracked.txt").write_text("cycle\n")
        self.record_gate("domain", paths=("tracked.txt",))
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
        run(
            self.repo, "record-dvc-push", "--head", "0" * 40,
            "--evidence", "wrong", ok=False,
        )
        (self.repo / "docs/specs/test/CHANGELOG.md").write_text("completed\n")
        self.record_gate("domain", paths=("docs/specs/test/CHANGELOG.md",))
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
