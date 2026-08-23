"""Configuration and path management for Malrynth Windows tooling."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

TARGET_LOADER = "x86_64-unknown-uefi"
TARGET_KERNEL = "x86_64-unknown-none"

BOOT_OK_MARKER = "MALRYNTH_M0_BOOT_OK"
BOOT_FAIL_MARKER = "MALRYNTH_M0_BOOT_FAIL"


def find_repo_root(start_path: Path | None = None) -> Path:
    """Find the root directory of the Malrynth repository."""
    if start_path is None:
        start_path = Path.cwd()
    curr = start_path.resolve()
    for parent in [curr, *curr.parents]:
        if (parent / "Cargo.toml").is_file() and (parent / "core").is_dir() and (parent / "tools").is_dir():
            return parent
    # Fallback to current directory if not found
    return curr


class MalrynthConfig:
    """Holds derived paths and compiler flags for a build session."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = find_repo_root(root)

        # Cargo target directory honoring CARGO_TARGET_DIR env var
        env_target = os.environ.get("CARGO_TARGET_DIR")
        if env_target:
            self.cargo_target_dir = Path(env_target).resolve()
        else:
            self.cargo_target_dir = self.root / "target"

        self.esp_dir = self.root / "esp"
        self.build_dir = self.root / "build"

    @property
    def cargo_home(self) -> Path:
        env_cargo_home = os.environ.get("CARGO_HOME")
        if env_cargo_home:
            return Path(env_cargo_home).resolve()
        return Path.home() / ".cargo"

    @property
    def rust_sysroot(self) -> Path:
        try:
            res = subprocess.run(
                ["rustc", "--print", "sysroot"],
                capture_output=True,
                text=True,
                check=True,
            )
            return Path(res.stdout.strip()).resolve()
        except Exception:
            return Path("/nonexistent")

    def get_remap_flags(self) -> list[str]:
        """Return rustc path remapping flags for reproducibility."""
        remaps = [
            f"--remap-path-prefix={self.root}=/malrynth",
            f"--remap-path-prefix={self.cargo_home}=/cargo",
            f"--remap-path-prefix={self.rust_sysroot}=/rust",
        ]
        # Also include forward-slash variant if backslashes are present
        root_fwd = str(self.root).replace("\\", "/")
        if root_fwd != str(self.root):
            remaps.append(f"--remap-path-prefix={root_fwd}=/malrynth")
        cargo_fwd = str(self.cargo_home).replace("\\", "/")
        if cargo_fwd != str(self.cargo_home):
            remaps.append(f"--remap-path-prefix={cargo_fwd}=/cargo")
        rust_fwd = str(self.rust_sysroot).replace("\\", "/")
        if rust_fwd != str(self.rust_sysroot):
            remaps.append(f"--remap-path-prefix={rust_fwd}=/rust")
        return remaps

    @property
    def kernel_flags_list(self) -> list[str]:
        return ["-C", "relocation-model=static", "-C", "force-frame-pointers=yes", *self.get_remap_flags()]

    @property
    def loader_flags_list(self) -> list[str]:
        return ["-C", "link-arg=/Brepro", "-C", "link-arg=/DEBUG:NONE", *self.get_remap_flags()]

    @property
    def kernel_rustflags(self) -> str:
        """Space-separated compiler flags (or for CARGO_ENCODED_RUSTFLAGS fallback)."""
        return " ".join(self.kernel_flags_list)

    @property
    def loader_rustflags(self) -> str:
        """Space-separated compiler flags (or for CARGO_ENCODED_RUSTFLAGS fallback)."""
        return " ".join(self.loader_flags_list)

    @property
    def kernel_encoded_rustflags(self) -> str:
        """Unit-separator encoded flags (CARGO_ENCODED_RUSTFLAGS), safe for paths with spaces."""
        return "\x1f".join(self.kernel_flags_list)

    @property
    def loader_encoded_rustflags(self) -> str:
        """Unit-separator encoded flags (CARGO_ENCODED_RUSTFLAGS), safe for paths with spaces."""
        return "\x1f".join(self.loader_flags_list)
