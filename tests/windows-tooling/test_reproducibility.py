"""Test byte-reproducibility across build paths on Windows.

Verifies that compiling Malrynth from two different source directories with different path
lengths produces byte-identical loader (BOOTX64.EFI) and kernel (kernel.elf) images.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add tools/windows to sys.path
_tools_dir = Path(__file__).resolve().parent.parent.parent / "tools" / "windows"
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from malrynth_tooling.build import build_image
from malrynth_tooling.config import MalrynthConfig
from malrynth_tooling.util import compute_sha256


class TestReproducibility(unittest.TestCase):
    def test_reproducible_across_directories(self) -> None:
        primary_cfg = MalrynthConfig()
        # Build at primary path
        ret_primary = build_image(primary_cfg.root)
        self.assertEqual(ret_primary, 0, "Primary build failed")

        primary_kernel = primary_cfg.esp_dir / "malrynth" / "kernel.elf"
        primary_loader = primary_cfg.esp_dir / "EFI" / "BOOT" / "BOOTX64.EFI"
        self.assertTrue(primary_kernel.is_file())
        self.assertTrue(primary_loader.is_file())

        primary_kernel_hash = compute_sha256(primary_kernel)
        primary_loader_hash = compute_sha256(primary_loader)

        # Copy source to alternate directory with a deliberately different path length
        with tempfile.TemporaryDirectory(prefix="malrynth-alternate-build-path-for-reproducibility-check-") as temp_dir:
            alt_root = Path(temp_dir) / "nested-alternate-src-dir"
            alt_root.mkdir(parents=True, exist_ok=True)

            # Copy required directories
            for item in ["core", "tools", "Cargo.toml", "Cargo.lock", "rust-toolchain.toml", "rustfmt.toml"]:
                src = primary_cfg.root / item
                dst = alt_root / item
                if src.is_dir():
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("target", "esp", "build", ".git"))
                elif src.is_file():
                    shutil.copy2(src, dst)

            alt_cfg = MalrynthConfig(alt_root)
            ret_alt = build_image(alt_cfg.root)
            self.assertEqual(ret_alt, 0, "Alternate build failed")

            alt_kernel = alt_cfg.esp_dir / "malrynth" / "kernel.elf"
            alt_loader = alt_cfg.esp_dir / "EFI" / "BOOT" / "BOOTX64.EFI"

            alt_kernel_hash = compute_sha256(alt_kernel)
            alt_loader_hash = compute_sha256(alt_loader)

            # Check kernel hash
            self.assertEqual(
                primary_kernel_hash,
                alt_kernel_hash,
                f"Kernel differs across build paths!\nPrimary:   {primary_kernel_hash}\nAlternate: {alt_kernel_hash}",
            )

            # Check loader hash
            self.assertEqual(
                primary_loader_hash,
                alt_loader_hash,
                f"Loader differs across build paths!\nPrimary:   {primary_loader_hash}\nAlternate: {alt_loader_hash}",
            )


if __name__ == "__main__":
    unittest.main()
