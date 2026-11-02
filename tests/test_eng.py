"""Integration tests for the eng kit. Each test builds a disposable git repository."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
import importlib.util
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
ENG = KIT / "bin" / "eng"
CONFIGS = KIT / "configs"

sys.path.insert(0, str(KIT / "lib"))
_eng_spec = importlib.util.spec_from_file_location("eng_kit", KIT / "lib" / "eng.py")
assert _eng_spec is not None and _eng_spec.loader is not None
eng_lib = importlib.util.module_from_spec(_eng_spec)
_eng_spec.loader.exec_module(eng_lib)


def run(cmd, cwd, timeout=180):
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)


def eng(root, *args, timeout=180):
    return run([str(ENG), "--root", str(root), *args], cwd=root, timeout=timeout)


class Repo:
    def __init__(self, root: Path):
        self.root = root

    def git(self, *args):
        res = run(["git", *args], cwd=self.root)
        if res.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {res.stderr}")
        return res

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content), encoding="utf-8")

    def init(self):
        self.git("init", "-q")
        self.git("config", "user.email", "eng@example.invalid")
        self.git("config", "user.name", "eng test")
        self.git("add", "-A")
        self.git("commit", "-qm", "fixture")

    def stage(self, *names):
        self.git("add", *names)


class EngTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="eng-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.repo = Repo(self.tmp)

    def install_config(self, commands, security=None, parallel=None):
        cfg = {
            "schema": "eng-config/v1",
            "project": "fixture",
            "commands": commands,
            "security": security or {"required": [], "optional": []},
            "parallel": parallel or {"max_worktrees": 2},
        }
        self.repo.write(".agents/engineering.json", json.dumps(cfg, indent=2))
        (self.tmp / ".agents" / "config").mkdir(parents=True, exist_ok=True)
        for name in ("semgrep.yml", "gitleaks.toml", "guard-allow.txt"):
            shutil.copy2(CONFIGS / name, self.tmp / ".agents" / "config" / name)

    def init_basic(self):
        self.repo.write("Makefile", "check:\n\t@true\n")
        self.repo.write("src/lib.py", "def add(a, b):\n    return a + b\n")
        self.repo.write("tests/test_lib.py", "from src.lib import add\n\ndef test_add():\n    assert add(1, 2) == 3\n")
        self.repo.init()
        self.install_config({"fast": [{"name": "check", "run": "make check"}],
                             "full": [{"name": "check", "run": "make check"}]})
        self.repo.git("add", "-A")
        self.repo.git("commit", "-qm", "config")


class DetectTests(EngTestCase):
    def test_detects_python_and_tests(self):
        self.init_basic()
        res = eng(self.tmp, "detect", "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertIn("Python", [s["language"] for s in data["stacks"]])
        self.assertGreaterEqual(data["tests"]["count"], 1)
        self.assertIn("check", data["build"]["make_targets"])
        self.assertTrue(data["git"]["present"])

    def test_non_git_directory_still_inventories(self):
        self.repo.write("src/lib.py", "print('x')\n")
        res = eng(self.tmp, "detect", "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertFalse(data["git"]["present"])
        self.assertEqual(data["file_count"], 1)


class GuardTests(EngTestCase):
    def test_detects_staged_secret(self):
        self.repo.write("clean.py", "print('ok')\n")
        self.repo.init()
        self.repo.write("leak.py", 'KEY = "AKIAQ7Z2X4M9P1L8V3N6"\n')
        self.repo.stage("leak.py")
        res = eng(self.tmp, "guard", "staged")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("aws-access-key", res.stdout)

    def test_clean_staged_files_pass(self):
        self.repo.write("clean.py", "print('ok')\n")
        self.repo.init()
        self.repo.write("second.py", "print('second')\n")
        self.repo.stage("second.py")
        res = eng(self.tmp, "guard", "staged")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_sensitive_filename_blocks(self):
        self.repo.write("README.md", "x\n")
        self.repo.init()
        self.repo.write(".env", "TOKEN=not-a-real-token\n")
        self.repo.stage(".env")
        res = eng(self.tmp, "guard", "staged")
        self.assertEqual(res.returncode, 1)
        self.assertIn("sensitive-file", res.stdout)

    def test_allowlist_is_path_scoped(self):
        self.repo.write("README.md", "x\n")
        self.repo.init()
        self.repo.write(".agents/config/guard-allow.txt", "tests/fixtures/fake.py\n")
        self.repo.write("tests/fixtures/fake.py", 'KEY = "AKIAQ7Z2X4M9P1L8V3N6"\n')
        self.repo.stage(".agents/config/guard-allow.txt", "tests/fixtures/fake.py")
        res = eng(self.tmp, "guard", "staged")
        self.assertEqual(res.returncode, 0, res.stdout)


class VerifyTests(EngTestCase):
    def test_pass_writes_verifiable_evidence(self):
        self.init_basic()
        res = eng(self.tmp, "verify", "--profile", "fast")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        path = next((self.tmp / ".agents" / "evidence").glob("*.json"))
        data = json.loads(path.read_text())
        self.assertEqual(data["verdict"]["status"], "pass")
        self.assertEqual(data["commands"][0]["status"], "pass")
        self.assertEqual(data["schema"], "eng-evidence/v1")
        check = eng(self.tmp, "evidence", "verify")
        self.assertEqual(check.returncode, 0, check.stdout)

    def test_failure_is_recorded_not_hidden(self):
        self.init_basic()
        self.repo.write(".agents/engineering.json", json.dumps({
            "schema": "eng-config/v1",
            "commands": {"fast": [{"name": "false", "run": "false"}], "full": [{"name": "false", "run": "false"}]},
            "security": {"required": [], "optional": []},
        }))
        res = eng(self.tmp, "verify", "--profile", "fast")
        self.assertEqual(res.returncode, 1)
        data = json.loads(next((self.tmp / ".agents" / "evidence").glob("*.json")).read_text())
        self.assertEqual(data["verdict"]["status"], "fail")
        self.assertIn("command:false", data["verdict"]["required_failures"])
        self.assertEqual(data["commands"][0]["exit_code"], 1)

    def test_output_is_redacted_in_logs(self):
        self.init_basic()
        self.repo.write(".agents/engineering.json", json.dumps({
            "schema": "eng-config/v1",
            "commands": {"fast": [{"name": "print-secret",
                                    "run": "python3 -c \"print('AKIAQ7Z2X4M9P1L8V3N6')\""}],
                          "full": [{"name": "true", "run": "true"}]},
            "security": {"required": [], "optional": []},
        }))
        res = eng(self.tmp, "verify", "--profile", "fast")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        log = next((self.tmp / ".agents" / "evidence").glob("*/00-print-secret.log"))
        text = log.read_text()
        self.assertNotIn("AKIAQ7Z2X4M9P1L8V3N6", text)
        self.assertIn("REDACTED:aws-access-key", text)

    def test_tampering_is_detected(self):
        self.init_basic()
        self.assertEqual(eng(self.tmp, "verify", "--profile", "fast").returncode, 0)
        path = next((self.tmp / ".agents" / "evidence").glob("*.json"))
        data = json.loads(path.read_text())
        data["verdict"]["status"] = "pass"
        data["commands"] = []
        path.write_text(json.dumps(data, indent=2))
        res = eng(self.tmp, "evidence", "verify")
        self.assertEqual(res.returncode, 1)
        self.assertIn("hash mismatch", res.stdout)

    def test_missing_required_scanner_blocks(self):
        self.init_basic()
        self.repo.write(".agents/engineering.json", json.dumps({
            "schema": "eng-config/v1",
            "commands": {"fast": [{"name": "true", "run": "true"}],
                          "full": [{"name": "true", "run": "true"}]},
            "security": {"required": ["eng-no-such-scanner"], "optional": []},
        }))
        res = eng(self.tmp, "verify", "--profile", "full")
        self.assertEqual(res.returncode, 2, res.stdout)
        data = json.loads(next((self.tmp / ".agents" / "evidence").glob("*.json")).read_text())
        self.assertEqual(data["verdict"]["status"], "blocked")
        self.assertTrue(any("eng-no-such-scanner" in u for u in data["verdict"]["unverified"]))


class VerifyTierTests(EngTestCase):
    def latest(self):
        return json.loads(sorted((self.tmp / ".agents" / "evidence").glob("*.json"))[-1].read_text())

    def test_empty_nightly_profile_blocks_instead_of_falling_back(self):
        self.init_basic()
        res = eng(self.tmp, "verify", "--profile", "nightly")
        self.assertEqual(res.returncode, 2, res.stdout)
        data = self.latest()
        self.assertEqual(data["profile"], "nightly")
        self.assertEqual(data["verdict"]["status"], "blocked")
        self.assertEqual(data["commands"], [])

    def test_nightly_runs_its_own_commands(self):
        self.init_basic()
        self.install_config({"fast": [{"name": "fast", "run": "true"}],
                             "nightly": [{"name": "soak", "run": "false"}]})
        res = eng(self.tmp, "verify", "--profile", "nightly")
        self.assertEqual(res.returncode, 1, res.stdout)
        data = self.latest()
        self.assertEqual([c["name"] for c in data["commands"]], ["soak"])
        self.assertEqual(data["verdict"]["status"], "fail")

    def test_scope_and_duration_are_always_recorded(self):
        self.init_basic()
        self.assertEqual(eng(self.tmp, "verify").returncode, 0)
        data = self.latest()
        self.assertEqual(data["scope"], "configured fast commands")
        self.assertIsInstance(data["duration_s"], float)
        for optional in ("run", "cost", "cache"):
            self.assertNotIn(optional, data)

    def test_optional_run_fields_are_hashed_into_the_record(self):
        self.init_basic()
        self.repo.write("cache.json", '{"hits": 90, "misses": 10}')
        res = eng(self.tmp, "verify", "--scope", "crate a only", "--run-id", "r-1", "--builder", "agent-a",
                  "--verifier", "agent-b", "--cost", "0.42", "--cache-stats", "cache.json")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        data = self.latest()
        self.assertEqual(data["scope"], "crate a only")
        self.assertEqual(data["run"], {"id": "r-1", "builder": "agent-a", "verifier": "agent-b"})
        self.assertEqual(data["cost"], {"amount": 0.42, "unit": "USD"})
        self.assertEqual(data["cache"], {"hits": 90, "misses": 10})
        self.assertEqual(eng(self.tmp, "evidence", "verify").returncode, 0)
        path = sorted((self.tmp / ".agents" / "evidence").glob("*.json"))[-1]
        tampered = json.loads(path.read_text())
        tampered["run"]["verifier"] = "agent-a"
        path.write_text(json.dumps(tampered))
        res = eng(self.tmp, "evidence", "verify")
        self.assertEqual(res.returncode, 1)
        self.assertIn("hash mismatch", res.stdout)

    def test_unreadable_cache_stats_are_unverified_not_dropped(self):
        self.init_basic()
        res = eng(self.tmp, "verify", "--cache-stats", "missing.json")
        self.assertEqual(res.returncode, 0, res.stdout)
        data = self.latest()
        self.assertNotIn("cache", data)
        self.assertTrue(any(u.startswith("cache statistics not recorded") for u in data["verdict"]["unverified"]))

    def test_a_command_that_edits_tracked_files_is_reported(self):
        self.init_basic()
        self.install_config({"fast": [{"name": "edit", "run": "echo changed >> src/lib.py"}]})
        self.repo.git("add", "-A")
        self.repo.git("commit", "-qm", "edit config")
        self.assertEqual(eng(self.tmp, "verify").returncode, 0)
        unverified = self.latest()["verdict"]["unverified"]
        self.assertIn("working tree changed during verification; commands may have modified files", unverified)

    def test_records_without_the_new_fields_still_verify(self):
        self.init_basic()
        logdir = self.tmp / ".agents" / "evidence" / "old"
        logdir.mkdir(parents=True)
        legacy = {"schema": "eng-evidence/v1", "id": "old", "finished_at": "2026-10-01T00:00:00Z",
                  "profile": "fast", "commands": [], "verdict": {"status": "pass"}}
        eng_lib.write_evidence(self.tmp, legacy, logdir)
        self.assertEqual(eng(self.tmp, "verify").returncode, 0)
        res = eng(self.tmp, "evidence", "verify")
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("2 record(s)", res.stdout)


class IndependentVerificationTests(EngTestCase):
    def setUp(self):
        super().setUp()
        self.init_basic()
        cfg = json.loads((self.tmp / ".agents" / "engineering.json").read_text())
        cfg["verification"] = {"independent": True}
        self.repo.write(".agents/engineering.json", json.dumps(cfg))

    def verdict(self):
        return json.loads(sorted((self.tmp / ".agents" / "evidence").glob("*.json"))[-1].read_text())["verdict"]

    def test_full_gate_without_a_verifier_is_blocked(self):
        res = eng(self.tmp, "verify", "--profile", "full", "--builder", "agent-a")
        self.assertEqual(res.returncode, 2, res.stdout)
        self.assertTrue(any("independent verification required" in u for u in self.verdict()["unverified"]))

    def test_builder_cannot_verify_its_own_work(self):
        res = eng(self.tmp, "verify", "--profile", "full", "--builder", "agent-a", "--verifier", "agent-a")
        self.assertEqual(res.returncode, 2, res.stdout)
        self.assertTrue(any("cannot verify its own work" in u for u in self.verdict()["unverified"]))

    def test_a_different_verifier_passes(self):
        res = eng(self.tmp, "verify", "--profile", "full", "--builder", "agent-a", "--verifier", "agent-b")
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertEqual(self.verdict()["status"], "pass")

    def test_a_failure_still_fails_with_a_self_verifier(self):
        self.install_config({"fast": [{"name": "false", "run": "false"}]})
        cfg = json.loads((self.tmp / ".agents" / "engineering.json").read_text())
        cfg["verification"] = {"independent": True}
        self.repo.write(".agents/engineering.json", json.dumps(cfg))
        res = eng(self.tmp, "verify", "--profile", "full", "--builder", "a", "--verifier", "a")
        self.assertEqual(res.returncode, 1, res.stdout)

    def test_fast_profile_is_not_gated(self):
        res = eng(self.tmp, "verify", "--profile", "fast")
        self.assertEqual(res.returncode, 0, res.stdout)


class QuarantineTests(EngTestCase):
    def quarantine(self, *entries):
        self.repo.write(".agents/quarantine.json", json.dumps({"schema": "eng-quarantine/v1", "entries": list(entries)}))

    def verdict(self):
        return json.loads(sorted((self.tmp / ".agents" / "evidence").glob("*.json"))[-1].read_text())["verdict"]

    def test_active_quarantine_is_reported_unverified(self):
        self.init_basic()
        self.quarantine({"test": "tests/test_net.py::test_retry", "owner": "agent-a",
                         "expires": "2999-01-01", "reason": "flaky on CI runners"})
        res = eng(self.tmp, "verify")
        self.assertEqual(res.returncode, 0, res.stdout)
        verdict = self.verdict()
        self.assertEqual(verdict["status"], "pass")
        self.assertTrue(any("tests/test_net.py::test_retry" in u for u in verdict["unverified"]))
        self.assertIn("quarantined test not verified", res.stdout)

    def test_expired_quarantine_blocks(self):
        self.init_basic()
        self.quarantine({"test": "t", "owner": "agent-a", "expires": "2000-01-01", "reason": "flaky"})
        res = eng(self.tmp, "verify")
        self.assertEqual(res.returncode, 2, res.stdout)
        self.assertEqual(self.verdict()["status"], "blocked")

    def test_entry_without_an_owner_blocks(self):
        self.init_basic()
        self.quarantine({"test": "t", "expires": "2999-01-01", "reason": "flaky"})
        self.assertEqual(eng(self.tmp, "verify").returncode, 2)

    def test_expiry_boundary_is_inclusive(self):
        from datetime import date
        root = self.tmp
        self.repo.write(".agents/quarantine.json", json.dumps({"schema": "eng-quarantine/v1", "entries": [
            {"test": "t", "owner": "o", "expires": "2026-11-02", "reason": "r"}]}))
        active, problems = eng_lib.load_quarantine(root, today=date(2026, 11, 2))
        self.assertEqual((len(active), problems), (1, []))
        active, problems = eng_lib.load_quarantine(root, today=date(2026, 11, 3))
        self.assertEqual(len(active), 0)
        self.assertEqual(len(problems), 1)


class DigestTests(EngTestCase):
    def digest(self, *args, root=None):
        res = eng(root or self.tmp, "digest", "--json", *args)
        return res.returncode, json.loads(res.stdout)["items"]

    def kinds(self, items):
        return sorted({i["kind"] for i in items})

    def test_clean_passing_repository_needs_nothing(self):
        self.init_basic()
        self.assertEqual(eng(self.tmp, "verify").returncode, 0)
        code, items = self.digest()
        self.assertEqual((code, items), (0, []))
        res = eng(self.tmp, "digest")
        self.assertIn("nothing needs you", res.stdout)

    def test_no_evidence_is_an_exception(self):
        self.init_basic()
        code, items = self.digest()
        self.assertEqual(code, 1)
        self.assertEqual(self.kinds(items), ["no-evidence"])

    def test_failure_blocked_and_unverified_are_all_listed(self):
        self.init_basic()
        self.install_config({"fast": [{"name": "false", "run": "false"}], "nightly": []})
        eng(self.tmp, "verify")
        eng(self.tmp, "verify", "--profile", "nightly")
        code, items = self.digest()
        self.assertEqual(code, 1)
        self.assertIn("fail", self.kinds(items))
        self.assertIn("blocked", self.kinds(items))
        self.assertIn("unverified", self.kinds(items))
        self.assertTrue(any("command:false" in i["detail"] for i in items if i["kind"] == "fail"))

    def test_a_newer_pass_on_another_profile_does_not_hide_a_failure(self):
        self.init_basic()
        self.install_config({"fast": [{"name": "true", "run": "true"}], "nightly": [{"name": "false", "run": "false"}]})
        eng(self.tmp, "verify", "--profile", "nightly")
        eng(self.tmp, "verify", "--profile", "fast")
        code, items = self.digest()
        self.assertTrue(any(i["kind"] == "fail" and i["detail"].startswith("nightly") for i in items))

    def test_tampered_evidence_is_reported(self):
        self.init_basic()
        eng(self.tmp, "verify")
        path = next((self.tmp / ".agents" / "evidence").glob("*.json"))
        data = json.loads(path.read_text())
        data["commands"] = []
        path.write_text(json.dumps(data))
        code, items = self.digest()
        self.assertIn("evidence-tampered", self.kinds(items))

    def test_expiring_quarantine_and_spend_over_cap(self):
        from datetime import date, timedelta
        self.init_basic()
        soon = (date.today() + timedelta(days=2)).isoformat()
        self.repo.write(".agents/quarantine.json", json.dumps({"schema": "eng-quarantine/v1", "entries": [
            {"test": "t", "owner": "agent-a", "expires": soon, "reason": "flaky"}]}))
        eng(self.tmp, "verify", "--cost", "6")
        eng(self.tmp, "verify", "--cost", "5")
        eng(self.tmp, "verify")
        code, items = self.digest("--cost-cap", "10")
        kinds = self.kinds(items)
        self.assertIn("quarantine-expiring", kinds)
        self.assertIn("over-spend", kinds)
        self.assertIn("spend-unknown", kinds)
        code, items = self.digest("--cost-cap", "100")
        self.assertNotIn("over-spend", self.kinds(items))

    def test_malformed_records_are_reported_not_crashed_on(self):
        self.init_basic()
        eng(self.tmp, "verify")
        eng(self.tmp, "verify")
        records = sorted((self.tmp / ".agents" / "evidence").glob("*.json"))
        records[0].write_text("[]")
        data = json.loads(records[1].read_text())
        data["verdict"] = "pass"
        records[1].write_text(json.dumps(data))
        index = self.tmp / ".agents" / "evidence" / "index.jsonl"
        index.write_text(index.read_text() + '"not an object"\n{"id": "x"}\n')
        res = eng(self.tmp, "evidence", "verify")
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        self.assertNotIn("Traceback", res.stderr)
        self.assertIn("not a JSON object", res.stdout)
        self.assertIn("malformed index entry", res.stdout)
        code, items = self.digest()
        self.assertEqual(code, 1)
        self.assertIn("evidence-tampered", self.kinds(items))

    def test_index_entry_outside_the_repository_is_refused(self):
        self.init_basic()
        eng(self.tmp, "verify")
        index = self.tmp / ".agents" / "evidence" / "index.jsonl"
        index.write_text(index.read_text() + json.dumps({"id": "y", "file": "../../outside.json", "sha256": "0"}) + "\n")
        res = eng(self.tmp, "evidence", "verify")
        self.assertEqual(res.returncode, 1)
        self.assertIn("outside the evidence directory", res.stdout)

    def test_spend_is_capped_per_unit(self):
        self.init_basic()
        eng(self.tmp, "verify", "--cost", "6")
        eng(self.tmp, "verify", "--cost", "5", "--cost-unit", "EUR")
        code, items = self.digest("--cost-cap", "10")
        self.assertNotIn("over-spend", self.kinds(items))
        eng(self.tmp, "verify", "--cost", "6", "--cost-unit", "EUR")
        code, items = self.digest("--cost-cap", "10")
        over = [i["detail"] for i in items if i["kind"] == "over-spend"]
        self.assertEqual(len(over), 1)
        self.assertIn("EUR", over[0])

    def test_string_cost_cap_in_config(self):
        self.init_basic()
        cfg = json.loads((self.tmp / ".agents" / "engineering.json").read_text())
        cfg["budget"] = {"cost_cap": "1"}
        self.repo.write(".agents/engineering.json", json.dumps(cfg))
        eng(self.tmp, "verify", "--cost", "2")
        res = eng(self.tmp, "digest", "--json")
        self.assertNotIn("Traceback", res.stderr)
        self.assertIn("over-spend", res.stdout)

    def test_stalled_worktree_is_reported(self):
        self.init_basic()
        eng(self.tmp, "verify")
        self.assertEqual(eng(self.tmp, "worktree", "create", "unit-a", "--owner", "agent-a",
                             "--allow-dirty").returncode, 0)
        code, items = self.digest("--stale-hours", "1000")
        self.assertNotIn("stalled", self.kinds(items))
        code, items = self.digest("--stale-hours", "0")
        stalled = [i for i in items if i["kind"] == "stalled"]
        self.assertEqual(len(stalled), 1)
        self.assertIn("agent-a", stalled[0]["detail"])

    def test_several_repositories_in_one_digest(self):
        self.init_basic()
        eng(self.tmp, "verify")
        other = self.tmp / "missing-repo"
        res = eng(self.tmp, "digest", "--json", str(self.tmp), str(other))
        items = json.loads(res.stdout)["items"]
        self.assertEqual(res.returncode, 1)
        self.assertEqual([i["kind"] for i in items], ["unreadable"])


class ActionPinTests(EngTestCase):
    def workflow(self, ref):
        self.repo.write(".github/workflows/test.yml",
                        f"name: t\non: [push]\njobs:\n  t:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: {ref}\n")
        self.repo.init()

    def test_pinned_sha_passes(self):
        self.workflow("actions/checkout@11d5960a326750d5838078e36cf38b85af677262")
        res = eng(self.tmp, "audit-actions")
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("clean", res.stdout)

    def test_mutable_tag_fails(self):
        self.workflow("actions/checkout@v4")
        res = eng(self.tmp, "audit-actions")
        self.assertEqual(res.returncode, 1)
        self.assertIn("mutable ref", res.stdout)

    def test_local_action_passes(self):
        self.workflow("./.github/actions/local")
        res = eng(self.tmp, "audit-actions")
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_docker_digest_passes(self):
        self.workflow("docker://alpine@sha256:" + "a" * 64)
        res = eng(self.tmp, "audit-actions")
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_reviewed_exception_passes(self):
        self.repo.write(".agents/config/actions-allow.txt", "actions/checkout@v4\n")
        self.workflow("actions/checkout@v4")
        res = eng(self.tmp, "audit-actions")
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("exception", res.stdout)


class ReleaseTests(EngTestCase):
    def prepare_release(self):
        self.init_basic()
        self.repo.write(".gitignore", ".agents/evidence/\n")
        self.repo.write("CHANGELOG.md", "## 1.2.3\n\n- test release\n")
        self.repo.write("notes.md", "Release 1.2.3 notes\n")
        self.repo.write("rollback.md", "Restore the previous artifact and rerun migrations.\n")
        self.repo.write("dist/app.txt", "artifact\n")
        self.repo.git("add", "-A")
        self.repo.git("commit", "-qm", "release fixture")

    def test_artifact_hash(self):
        self.repo.write("dist/app.txt", "artifact\n")
        res = eng(self.tmp, "artifact", "dist/app.txt", "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertEqual(data["artifacts"][0]["size"], 9)
        self.assertEqual(len(data["artifacts"][0]["sha256"]), 64)

    def test_release_requires_passing_full_evidence(self):
        self.prepare_release()
        res = eng(self.tmp, "release-check", "--version", "1.2.3", "--artifact", "dist/app.txt",
                  "--notes", "notes.md", "--rollback", "rollback.md")
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("passing full evidence", res.stdout)

    def test_release_passes_and_records_evidence(self):
        self.prepare_release()
        self.assertEqual(eng(self.tmp, "verify", "--profile", "full").returncode, 0)
        res = eng(self.tmp, "release-check", "--version", "1.2.3", "--artifact", "dist/app.txt",
                  "--notes", "notes.md", "--rollback", "rollback.md")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("PASS", res.stdout)
        self.assertIn("release evidence", res.stdout)
        self.assertEqual(eng(self.tmp, "evidence", "verify").returncode, 0)

    def test_release_refuses_a_performance_regression(self):
        self.prepare_release()
        self.assertEqual(eng(self.tmp, "verify", "--profile", "full").returncode, 0)
        evidence = self.tmp / ".agents" / "evidence"
        base = evidence / "base.json"
        cur = evidence / "current.json"
        base.write_text(json.dumps({"schema": "eng-perf/v1", "metrics": {"score": {"value": 100, "direction": "higher"}}}))
        cur.write_text(json.dumps({"schema": "eng-perf/v1", "metrics": {"score": {"value": 60, "direction": "higher"}}}))
        res = eng(self.tmp, "release-check", "--version", "1.2.3", "--artifact", "dist/app.txt",
                  "--notes", "notes.md", "--rollback", "rollback.md",
                  "--performance-baseline", str(base), "--performance-current", str(cur))
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("performance comparison", res.stdout)

    def test_release_refuses_dirty_tree_and_wrong_version(self):
        self.prepare_release()
        self.assertEqual(eng(self.tmp, "verify", "--profile", "full").returncode, 0)
        self.repo.write("notes.md", "Release 9.9.9 notes\n")
        res = eng(self.tmp, "release-check", "--version", "9.9.9", "--artifact", "dist/app.txt",
                  "--notes", "notes.md", "--rollback", "rollback.md")
        self.assertEqual(res.returncode, 1)
        self.assertIn("clean tree", res.stdout)
        self.assertIn("changelog names version", res.stdout)


class PerfTests(EngTestCase):
    def write_perf(self, name, metrics):
        path = self.tmp / ".agents" / "evidence" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"schema": "eng-perf/v1", "metrics": metrics}))
        return path

    def test_higher_and_lower_metrics_pass(self):
        base = self.write_perf("base.json", {
            "score": {"value": 100, "direction": "higher", "unit": "score"},
            "p95_ms": {"value": 10, "direction": "lower", "unit": "ms"},
        })
        cur = self.write_perf("current.json", {
            "score": {"value": 101, "direction": "higher", "unit": "score"},
            "p95_ms": {"value": 10.4, "direction": "lower", "unit": "ms"},
        })
        res = eng(self.tmp, "perf-check", "--baseline", str(base), "--current", str(cur), "--max-regression", "5")
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_a_regression_fails(self):
        base = self.write_perf("base.json", {"score": {"value": 100, "direction": "higher"}})
        cur = self.write_perf("current.json", {"score": {"value": 80, "direction": "higher"}})
        res = eng(self.tmp, "perf-check", "--baseline", str(base), "--current", str(cur))
        self.assertEqual(res.returncode, 1)
        self.assertIn("FAIL", res.stdout)


class ImpactTests(EngTestCase):
    def test_references_and_tests_are_found(self):
        self.repo.write("lib.py", "def divide(a, b):\n    return a / b\n")
        self.repo.write("use.py", "from lib import divide\nprint(divide(1, 0))\n")
        self.repo.write("tests/test_lib.py", "from lib import divide\n\ndef test_divide():\n    assert divide(4, 2) == 2\n")
        self.repo.init()
        self.repo.write("lib.py", "def divide(a, b):\n    if b == 0:\n        raise ValueError('zero')\n    return a / b\n")
        res = eng(self.tmp, "impact", "--base", "HEAD", "--json")
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertEqual(data["symbols"][0]["name"], "divide")
        refs = {r["file"] for r in data["references"]}
        self.assertIn("use.py", refs)
        self.assertIn("tests/test_lib.py", refs)
        self.assertTrue(data["heuristic"])

    def test_unknown_base_is_an_error(self):
        self.init_basic()
        res = eng(self.tmp, "impact", "--base", "does-not-exist")
        self.assertEqual(res.returncode, 2)
        self.assertIn("cannot diff", res.stderr)


class WorktreeTests(EngTestCase):
    def test_create_list_remove(self):
        self.init_basic()
        res = eng(self.tmp, "worktree", "create", "task-a", "--owner", "agent-a")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        path = self.tmp / ".worktrees" / "task-a"
        self.assertTrue((path / "Makefile").exists())
        listing = eng(self.tmp, "worktree", "list", "--json")
        self.assertEqual(listing.returncode, 0)
        items = json.loads(listing.stdout)
        self.assertEqual(items[0]["owner"], "agent-a")
        removed = eng(self.tmp, "worktree", "remove", "task-a")
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertFalse(path.exists())

    def test_dirty_tree_refused(self):
        self.init_basic()
        self.repo.write("scratch.txt", "uncommitted\n")
        res = eng(self.tmp, "worktree", "create", "task-b")
        self.assertEqual(res.returncode, 2)
        self.assertIn("dirty", res.stderr)

    def test_traversal_name_refused(self):
        self.init_basic()
        res = eng(self.tmp, "worktree", "remove", "../../etc")
        self.assertEqual(res.returncode, 2)
        self.assertIn("invalid", res.stderr)


class InitTests(EngTestCase):
    def test_init_is_idempotent_and_preserves_policy(self):
        self.repo.write("AGENTS.md", "# Policy\n\nKeep this invariant.\n")
        self.repo.write("Makefile", "check:\n\t@true\n")
        self.repo.init()
        first = run([str(KIT / "install.sh"), "--target", str(self.tmp)], cwd=KIT)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        second = run([str(KIT / "install.sh"), "--target", str(self.tmp)], cwd=KIT)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        text = (self.tmp / "AGENTS.md").read_text()
        self.assertIn("Keep this invariant.", text)
        self.assertEqual(text.count("<!-- eng:begin -->"), 1)
        self.assertTrue((self.tmp / ".agents" / "engineering.json").exists())
        self.assertTrue((self.tmp / ".agents" / "README.md").exists())
        self.assertTrue((self.tmp / ".agents" / "skills" / "repo-intelligence" / "SKILL.md").exists())
        self.assertTrue((self.tmp / ".claude" / "skills").is_symlink())
        self.assertTrue((self.tmp / ".opencode" / "skills").is_symlink())

    def test_install_without_agents_uses_template(self):
        self.repo.write("Makefile", "check:\n\t@true\n")
        self.repo.init()
        res = run([str(KIT / "install.sh"), "--target", str(self.tmp)], cwd=KIT)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        text = (self.tmp / "AGENTS.md").read_text()
        self.assertIn("Engineering controls", text)
        self.assertIn("make check", text)
        self.assertNotIn("{{PROJECT}}", text)

    def test_hook_blocks_staged_secret(self):
        self.repo.write("Makefile", "check:\n\t@true\n")
        self.repo.init()
        res = run([str(KIT / "install.sh"), "--target", str(self.tmp), "--hooks"], cwd=KIT)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.repo.write("leak.py", 'KEY = "AKIAQ7Z2X4M9P1L8V3N6"\n')
        self.repo.stage("leak.py")
        commit = run(["git", "commit", "-m", "should be blocked"], cwd=self.tmp)
        self.assertNotEqual(commit.returncode, 0)
        self.assertIn("aws-access-key", commit.stdout + commit.stderr)


class SkillTests(unittest.TestCase):
    def test_skills_have_frontmatter_and_required_sections(self):
        skills = sorted((KIT / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(skills), 17)
        for path in skills:
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), path)
            front, body = text.split("---", 2)[1], text.split("---", 2)[2]
            self.assertIn("name:", front, path)
            self.assertIn("description:", front, path)
            self.assertIn(f"name: {path.parent.name}", front, path)
            self.assertLessEqual(len(text.splitlines()), 150, path)
            for heading in ("## Activate when", "## Permissions", "## Verification", "## Done when"):
                self.assertIn(heading, body, f"{path} missing {heading}")

    def test_scanner_configs_exist(self):
        self.assertTrue((CONFIGS / "semgrep.yml").exists())
        self.assertTrue((CONFIGS / "gitleaks.toml").exists())
        self.assertTrue((KIT / "ci" / "agent-verify.yml").exists())


class ScannerTests(EngTestCase):
    def setUp(self):
        super().setUp()
        if not shutil.which("semgrep"):
            self.skipTest("semgrep not installed")
        self.init_basic()

    def test_semgrep_finds_shell_true(self):
        self.repo.write("bad.py", "import subprocess\nsubprocess.run('echo x', shell=True)\n")
        self.repo.write(".agents/engineering.json", json.dumps({
            "schema": "eng-config/v1",
            "commands": {"fast": [{"name": "true", "run": "true"}], "full": [{"name": "true", "run": "true"}]},
            "security": {"required": ["semgrep"], "optional": []},
        }))
        res = eng(self.tmp, "security", "--json")
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        data = json.loads(res.stdout)
        semgrep = next(r for r in data["results"] if r["tool"] == "semgrep")
        self.assertEqual(semgrep["status"], "findings")
        self.assertGreaterEqual(semgrep["findings"], 1)

    def test_new_rules_have_positive_and_negative_fixtures(self):
        self.repo.write(".agents/engineering.json", json.dumps({
            "schema": "eng-config/v1",
            "commands": {"fast": [{"name": "true", "run": "true"}], "full": [{"name": "true", "run": "true"}]},
            "security": {"required": ["semgrep"], "optional": []},
        }))
        positive = KIT / "evals" / "security-fixtures" / "positive"
        negative = KIT / "evals" / "security-fixtures" / "negative"
        for path in positive.iterdir():
            shutil.copy2(path, self.tmp / path.name)
        res = eng(self.tmp, "security", "--json")
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        data = json.loads(res.stdout)
        semgrep = next(r for r in data["results"] if r["tool"] == "semgrep")
        self.assertGreaterEqual(semgrep["findings"], 3)
        for path in (self.tmp / p.name for p in positive.iterdir()):
            path.unlink()
        for path in negative.iterdir():
            shutil.copy2(path, self.tmp / path.name)
        res = eng(self.tmp, "security", "--json")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        data = json.loads(res.stdout)
        semgrep = next(r for r in data["results"] if r["tool"] == "semgrep")
        self.assertEqual(semgrep["status"], "pass")


class GitleaksTests(EngTestCase):
    def setUp(self):
        super().setUp()
        if not shutil.which("gitleaks"):
            self.skipTest("gitleaks not installed")
        self.init_basic()

    def test_gitleaks_finds_tracked_secret(self):
        self.repo.write("leak.py", 'KEY = "ghp_7Qm2Kd9Xp4Vb8Nz3Rc6Tf1Lw5Hs0Jg2Yd4Ae"\n')
        self.repo.stage("leak.py")
        self.repo.git("commit", "-qm", "leak")
        self.repo.write(".agents/engineering.json", json.dumps({
            "schema": "eng-config/v1",
            "commands": {"fast": [{"name": "true", "run": "true"}], "full": [{"name": "true", "run": "true"}]},
            "security": {"required": ["gitleaks"], "optional": []},
        }))
        res = eng(self.tmp, "security", "--json")
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        data = json.loads(res.stdout)
        gl = next(r for r in data["results"] if r["tool"] == "gitleaks")
        self.assertEqual(gl["status"], "findings")
        self.assertGreaterEqual(gl["findings"], 1)


class LockfileDiscovery(unittest.TestCase):
    """osv-scanner is driven by explicit lockfiles so a worktree checkout still scans."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="eng-lock-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.repo = Repo(self.tmp)

    def test_finds_project_lockfiles_and_skips_vendored_trees(self):
        self.repo.write("Cargo.lock", "[[package]]\nname = \"fixture\"\n")
        self.repo.write("web/package-lock.json", "{\"lockfileVersion\": 3}\n")
        self.repo.write("README.md", "# fixture\n")
        self.repo.write(".gitignore", "generated/\n")
        # Vendored, generated and evidence copies of a lockfile are not project inputs.
        self.repo.write("web/node_modules/dep/package-lock.json", "{}\n")
        self.repo.write(".worktrees/task/Cargo.lock", "x\n")
        self.repo.write(".agents/evidence/run/gitleaks-tree/Cargo.lock", "x\n")
        self.repo.init()
        # Untracked but real lockfiles count; ignored ones do not.
        self.repo.write("svc/uv.lock", "version = 1\n")
        self.repo.write("generated/pnpm-lock.yaml", "lockfileVersion: 9\n")
        self.assertEqual(eng_lib.lockfiles(self.tmp), ["Cargo.lock", "svc/uv.lock", "web/package-lock.json"])

    def test_empty_repository_falls_back_to_a_source_scan(self):
        self.repo.write("README.md", "# fixture\n")
        self.repo.init()
        self.assertEqual(eng_lib.lockfiles(self.tmp), [])

    def test_scan_args_keep_the_walk_then_fall_back_to_lockfiles(self):
        self.repo.write("Cargo.lock", "[[package]]\nname = \"fixture\"\n")
        # A colon in a directory name must not read as an explicit parser type.
        self.repo.write("services/api:v2/package-lock.json", "{\"lockfileVersion\": 3}\n")
        self.repo.init()
        out = self.tmp / "out.json"
        walk = eng_lib.osv_scan_args("osv-scanner", self.tmp, out)
        self.assertIn("--recursive", walk)
        self.assertEqual(walk[-1], str(self.tmp))
        self.assertNotIn("-L", walk, "the walk must stay the first pass, unfiltered")

        fallback = eng_lib.osv_lockfile_args("osv-scanner", self.tmp, out)
        explicit = [fallback[i + 1] for i, a in enumerate(fallback) if a == "-L"]
        self.assertEqual(explicit, [":Cargo.lock", ":services/api:v2/package-lock.json"])
        self.assertNotIn(str(self.tmp), fallback, "the fallback must not re-run the walk")


if __name__ == "__main__":
    unittest.main()
