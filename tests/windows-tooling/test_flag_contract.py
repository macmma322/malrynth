"""The shared M0 compiler/linker contract has two platform definitions; they must agree.

`tools/lib.sh` (POSIX) and `tools/windows/malrynth_tooling/config.py` (native Windows)
each define the same shared contract. Neither is authoritative over the other, so nothing
structural stops one from being changed alone -- which would produce two silently
divergent toolchains that both still build. This test is what stops that.

Only the NON-REMAP switches are compared. The `--remap-path-prefix` flags are host-derived
and deliberately differ between the two definitions (see `.cargo/config.toml`).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent.parent
_tools_dir = _repo_root / "tools" / "windows"
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from malrynth_tooling.config import MalrynthConfig

REMAP_PREFIX = "--remap-path-prefix="


def find_contract_bash() -> str | None:
    """Find a Bash that can source this Windows checkout.

    On Windows, ``bash.exe`` earlier on PATH may be the WSL launcher. It cannot use the
    native process working directory passed by ``subprocess`` and exits before running the
    command. Prefer the Git-for-Windows Bash paired with the active ``git`` executable.
    """
    if sys.platform == "win32":
        try:
            git_exec_path = subprocess.run(
                ["git", "--exec-path"], capture_output=True, text=True, check=True
            ).stdout.strip()
            candidate = Path(git_exec_path).parents[2] / "bin" / "bash.exe"
            if candidate.is_file():
                return str(candidate)
        except (FileNotFoundError, subprocess.CalledProcessError, IndexError):
            pass
    return shutil.which("bash")


def contract_switches(tokens: list[str]) -> list[str]:
    """Return the leading non-remap switches.

    Both definitions append their remap flags last, so truncating at the first remap
    token is exact -- and, unlike filtering, stays correct when a host path contains a
    space and the shell definition has already joined the remaps into one string.
    """
    contract: list[str] = []
    for token in tokens:
        if token.startswith(REMAP_PREFIX):
            break
        contract.append(token)
    return contract


class TestFlagContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bash = find_contract_bash()

    def _shell_flags(self, name: str) -> list[str]:
        if not self.bash:
            self.skipTest("bash is unavailable; cannot read the POSIX contract definition")
        res = subprocess.run(
            [self.bash, "-c", f'source tools/lib.sh; printf "%s" "${name}"'],
            cwd=_repo_root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            res.returncode, 0, f"sourcing tools/lib.sh failed: {res.stderr.strip()}"
        )
        return contract_switches(res.stdout.split())

    def _python_flags(self, attribute: str) -> list[str]:
        cfg = MalrynthConfig(_repo_root)
        return contract_switches(list(getattr(cfg, attribute)))

    def test_kernel_contract_matches_across_platform_definitions(self) -> None:
        shell = self._shell_flags("KERNEL_RUSTFLAGS")
        python = self._python_flags("kernel_flags_list")
        self.assertTrue(shell, "tools/lib.sh defined no kernel contract switches")
        self.assertEqual(
            shell,
            python,
            "KERNEL contract drifted: tools/lib.sh and "
            "tools/windows/malrynth_tooling/config.py must be updated together",
        )

    def test_loader_contract_matches_across_platform_definitions(self) -> None:
        shell = self._shell_flags("LOADER_RUSTFLAGS")
        python = self._python_flags("loader_flags_list")
        self.assertTrue(shell, "tools/lib.sh defined no loader contract switches")
        self.assertEqual(
            shell,
            python,
            "LOADER contract drifted: tools/lib.sh and "
            "tools/windows/malrynth_tooling/config.py must be updated together",
        )

    def test_contract_is_actually_parsed_and_not_silently_empty(self) -> None:
        """Two empty lists compare equal; prove the parse found real switches."""
        for attribute in ("kernel_flags_list", "loader_flags_list"):
            with self.subTest(attribute=attribute):
                contract = self._python_flags(attribute)
                self.assertGreaterEqual(len(contract), 2)
                self.assertEqual(contract[0], "-C")

    def test_remap_flags_are_excluded_from_the_compared_contract(self) -> None:
        cfg = MalrynthConfig(_repo_root)
        full = list(cfg.kernel_flags_list)
        self.assertTrue(
            any(token.startswith(REMAP_PREFIX) for token in full),
            "expected remap flags to be present in the full flag list",
        )
        self.assertFalse(
            any(token.startswith(REMAP_PREFIX) for token in contract_switches(full))
        )


if __name__ == "__main__":
    unittest.main()
