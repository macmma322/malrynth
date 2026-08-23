"""Test that Malrynth Windows tooling functions completely inside paths with spaces."""

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
from malrynth_tooling.config import MalrynthConfig, find_repo_root
from malrynth_tooling.doctor import run_doctor
from malrynth_tooling.verify import validate_kernel_elf, validate_loader_pe


class TestPathWithSpaces(unittest.TestCase):
    def test_build_and_doctor_in_path_with_spaces(self) -> None:
        src_root = find_repo_root()
        with tempfile.TemporaryDirectory(prefix="Malrynth Windows Tooling Space Test ") as temp_dir:
            space_root = Path(temp_dir) / "Sub Space Directory (Malrynth)"
            space_root.mkdir(parents=True, exist_ok=True)

            # Copy essential workspace files
            for item in ["core", "tools", "Cargo.toml", "Cargo.lock", "rust-toolchain.toml", "rustfmt.toml"]:
                src = src_root / item
                dst = space_root / item
                if src.is_dir():
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("target", "esp", "build", ".git"))
                elif src.is_file():
                    shutil.copy2(src, dst)

            # 1. Test config discovery in path with spaces
            cfg = MalrynthConfig(space_root)
            self.assertEqual(cfg.root, space_root.resolve())
            self.assertTrue(" " in str(cfg.root))

            # 2. Test doctor in path with spaces (exit code 1 due to missing QEMU/OVMF, but does not crash)
            ret_doc = run_doctor(space_root)
            self.assertIn(ret_doc, (0, 1))

            # 3. Test build in path with spaces
            ret_build = build_image(space_root)
            self.assertEqual(ret_build, 0, "Build in path with spaces failed")

            # 4. Verify output artifacts exist and are valid
            loader_path = cfg.esp_dir / "EFI" / "BOOT" / "BOOTX64.EFI"
            kernel_path = cfg.esp_dir / "malrynth" / "kernel.elf"

            self.assertTrue(loader_path.is_file())
            self.assertTrue(kernel_path.is_file())

            loader_meta = validate_loader_pe(loader_path)
            kernel_meta = validate_kernel_elf(kernel_path)

            self.assertEqual(loader_meta["format"], "PE32+")
            self.assertEqual(kernel_meta["format"], "ELF64")
            self.assertEqual(kernel_meta["type"], "ET_EXEC")


if __name__ == "__main__":
    unittest.main()
