"""Trigger and security invariants for the native Windows M0 workflow.

The workflow is the only automated check that the native Windows toolchain still works.
Two classes of change would quietly remove that protection:

* narrowing the triggers, so relevant changes reach main unvalidated;
* relaxing the security posture (unpinned actions, write permissions, credential
  persistence, `pull_request_target`), so CI becomes an attack surface.

Neither shows up as a failing build, so both are asserted here. Parsing is deliberately
text-based: the repository's Python tooling has no third-party dependencies, and these are
presence/absence questions rather than questions about YAML semantics.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent.parent
WORKFLOW = _repo_root / ".github" / "workflows" / "windows-native-m0.yml"

# Paths the workflow's outcome actually depends on. Documentation-only changes are
# deliberately excluded so they do not consume the Actions allowance.
REQUIRED_PATH_FILTERS = {
    ".github/workflows/windows-native-m0.yml",
    ".cargo/**",
    "core/**",
    "tools/windows/**",
    "tools/lib.sh",
    "tests/windows-tooling/**",
    "Cargo.toml",
    "Cargo.lock",
    "rust-toolchain.toml",
}


def read_workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def strip_comments(text: str) -> str:
    """Drop whole-line comments so prose about a term is not mistaken for the term."""
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )


def trigger_path_lists(text: str) -> dict[str, list[str]]:
    """Return the `paths:` list under each top-level trigger in the `on:` block."""
    lines = strip_comments(text).splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip() == "on:")
    except StopIteration:  # pragma: no cover - guarded by its own test
        raise AssertionError("workflow has no `on:` block")

    results: dict[str, list[str]] = {}
    trigger: str | None = None
    collecting = False
    for line in lines[start + 1 :]:
        if line.strip() and not line.startswith(" "):
            break  # left the `on:` block
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if not stripped:
            continue
        if indent == 2 and stripped.endswith(":"):
            trigger = stripped[:-1]
            collecting = False
        elif indent == 4 and stripped == "paths:":
            collecting = True
            results[trigger or "?"] = []
        elif indent == 4:
            collecting = False
        elif collecting and stripped.startswith("- "):
            results[trigger or "?"].append(stripped[2:].strip().strip("'\""))
    return results


class TestWindowsWorkflowContract(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(WORKFLOW.is_file(), f"missing workflow: {WORKFLOW}")
        self.text = read_workflow()
        self.body = strip_comments(self.text)

    # --- triggers ---------------------------------------------------------------

    def test_runs_for_pushes_to_main(self) -> None:
        paths = trigger_path_lists(self.text)
        self.assertIn("push", paths, "workflow must have a push trigger with path filters")
        push_branches = re.search(r"^  push:\n(?:.*\n)*?    branches: \[(.*)\]", self.body, re.MULTILINE)
        self.assertIsNotNone(push_branches, "push trigger has no branches list")
        self.assertIn("main", [b.strip() for b in push_branches.group(1).split(",")])

    def test_runs_for_pull_requests_targeting_main(self) -> None:
        pr_branches = re.search(
            r"^  pull_request:\n(?:.*\n)*?    branches: \[(.*)\]", self.body, re.MULTILINE
        )
        self.assertIsNotNone(pr_branches, "workflow must have a pull_request trigger")
        self.assertIn("main", [b.strip() for b in pr_branches.group(1).split(",")])

    def test_path_filters_cover_everything_the_job_depends_on(self) -> None:
        for trigger, paths in trigger_path_lists(self.text).items():
            with self.subTest(trigger=trigger):
                missing = REQUIRED_PATH_FILTERS - set(paths)
                self.assertFalse(missing, f"{trigger} path filter is missing {sorted(missing)}")

    def test_push_and_pull_request_path_filters_are_identical(self) -> None:
        """They are duplicated because Actions has no anchors; they must not drift."""
        paths = trigger_path_lists(self.text)
        self.assertEqual(paths.get("push"), paths.get("pull_request"))

    def test_documentation_only_changes_are_not_covered(self) -> None:
        """The point of the filter: a docs change must not spend Windows CI minutes."""
        for trigger, paths in trigger_path_lists(self.text).items():
            with self.subTest(trigger=trigger):
                self.assertNotIn("docs/**", paths)
                self.assertNotIn("**", paths)

    # --- security posture -------------------------------------------------------

    def test_never_uses_pull_request_target(self) -> None:
        self.assertNotIn("pull_request_target", self.body)

    def test_permissions_are_read_only(self) -> None:
        self.assertIn("permissions:", self.body)
        self.assertIn("contents: read", self.body)
        granted = re.findall(r"^\s+(\w[\w-]*): (write|write-all)$", self.body, re.MULTILINE)
        self.assertFalse(granted, f"workflow grants write authority: {granted}")
        self.assertNotIn("permissions: write-all", self.body)

    def test_checkout_does_not_persist_credentials(self) -> None:
        self.assertIn("persist-credentials: false", self.body)

    def test_third_party_actions_are_pinned_by_commit_sha(self) -> None:
        uses = re.findall(r"^\s*uses:\s*(\S+)", self.body, re.MULTILINE)
        self.assertTrue(uses, "expected at least one action reference")
        for reference in uses:
            with self.subTest(uses=reference):
                self.assertRegex(
                    reference,
                    r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$",
                    "actions must be pinned by 40-character commit SHA, never by tag",
                )

    def test_no_secrets_are_referenced(self) -> None:
        self.assertNotIn("secrets.", self.body)

    def test_hosted_boot_is_not_introduced(self) -> None:
        """Boot stays on a configured host; hosted runners would only measure TCG."""
        self.assertNotIn("qemu-system-x86_64", self.body)


if __name__ == "__main__":
    unittest.main()
