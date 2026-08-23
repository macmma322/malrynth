"""Unit tests for QEMU, OVMF, and environment discovery."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add tools/windows to sys.path
_tools_dir = Path(__file__).resolve().parent.parent.parent / "tools" / "windows"
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from malrynth_tooling.config import find_repo_root
from malrynth_tooling.discovery import (
    find_ovmf,
    find_qemu,
    validate_firmware_pair,
    get_filesystem_info,
    get_git_info,
    get_host_info,
    get_rust_toolchain_info,
)


class TestDiscovery(unittest.TestCase):
    def setUp(self) -> None:
        self.orig_env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.orig_env)

    def test_repo_root_discovery(self) -> None:
        root = find_repo_root()
        self.assertTrue((root / "Cargo.toml").is_file())
        self.assertTrue((root / "core").is_dir())
        self.assertTrue((root / "tools").is_dir())

    def test_host_and_filesystem_info(self) -> None:
        host = get_host_info()
        self.assertIn("os", host)
        self.assertIn("architecture", host)
        if sys.platform == "win32":
            win_ver = sys.getwindowsversion()
            if win_ver.major == 10 and win_ver.build >= 22000:
                self.assertIn("Windows 11", host["os"])
                self.assertIn("NT 10.0", host["kernel"])

        root = find_repo_root()
        fs = get_filesystem_info(root)
        self.assertIn("filesystem", fs)
        self.assertGreater(fs["free_bytes"], 0)

        git_info = get_git_info(root)
        self.assertIsNotNone(git_info["git_version"])

    def test_rust_toolchain_info(self) -> None:
        rust = get_rust_toolchain_info()
        self.assertIsNotNone(rust["rustc_version"])
        self.assertIsNotNone(rust["cargo_version"])
        self.assertTrue(rust["loader_target_installed"])
        self.assertTrue(rust["kernel_target_installed"])

    def test_qemu_discovery_with_env_override(self) -> None:
        with tempfile.TemporaryDirectory(prefix="malrynth test spaces ") as temp_dir:
            fake_qemu = Path(temp_dir) / "fake_qemu.exe"
            fake_qemu.write_text("fake qemu executable")

            # Test valid override
            os.environ["MALRYNTH_QEMU"] = str(fake_qemu)
            qemu_bin, desc = find_qemu()
            self.assertEqual(qemu_bin, fake_qemu.resolve())
            self.assertIn("environment override", desc)

            # Test nonexistent override
            os.environ["MALRYNTH_QEMU"] = str(Path(temp_dir) / "nonexistent.exe")
            qemu_bin, desc = find_qemu()
            self.assertIsNone(qemu_bin)
            self.assertIn("does not exist", desc)

    def test_ovmf_discovery_with_env_override(self) -> None:
        with tempfile.TemporaryDirectory(prefix="malrynth test ovmf ") as temp_dir:
            temp_path = Path(temp_dir)
            code_file = temp_path / "OVMF_CODE.fd"
            vars_file = temp_path / "OVMF_VARS.fd"
            code_file.write_text("fake code")
            vars_file.write_text("fake vars")

            # 1. Test explicit pair override
            os.environ["MALRYNTH_OVMF_CODE"] = str(code_file)
            os.environ["MALRYNTH_OVMF_VARS"] = str(vars_file)
            c, v, desc = find_ovmf()
            self.assertEqual(c, code_file.resolve())
            self.assertEqual(v, vars_file.resolve())
            self.assertIn("explicit environment override", desc)

            # 2. Test incomplete override (CODE set, VARS missing)
            del os.environ["MALRYNTH_OVMF_VARS"]
            c, v, desc = find_ovmf()
            self.assertIsNone(c)
            self.assertIsNone(v)

            # 3. Test directory override via MALRYNTH_OVMF
            del os.environ["MALRYNTH_OVMF_CODE"]
            os.environ["MALRYNTH_OVMF"] = str(temp_path)
            c, v, desc = find_ovmf()
            self.assertEqual(c, code_file.resolve())
            self.assertEqual(v, vars_file.resolve())
            self.assertIn("found in", desc)

    def test_known_qemu_x86_firmware_pair_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            code = root / "edk2-x86_64-code.fd"
            vars_file = root / "edk2-i386-vars.fd"
            code.write_bytes(b"code")
            vars_file.write_bytes(b"vars")
            valid, reason = validate_firmware_pair(code, vars_file)
            self.assertTrue(valid, reason)

    def test_cross_architecture_firmware_pairs_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            x86_code = root / "edk2-x86_64-code.fd"
            arm_code = root / "edk2-aarch64-code.fd"
            x86_vars = root / "edk2-i386-vars.fd"
            arm_vars = root / "edk2-arm-vars.fd"
            for path in (x86_code, arm_code, x86_vars, arm_vars):
                path.write_bytes(path.name.encode("ascii"))
            self.assertFalse(validate_firmware_pair(x86_code, arm_vars)[0])
            self.assertFalse(validate_firmware_pair(arm_code, x86_vars)[0])

    def test_explicit_mismatched_environment_pair_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            code = root / "edk2-x86_64-code.fd"
            vars_file = root / "edk2-arm-vars.fd"
            code.write_bytes(b"code")
            vars_file.write_bytes(b"vars")
            c, v, desc = find_ovmf(str(code), str(vars_file))
            self.assertIsNone(c)
            self.assertIsNone(v)
            self.assertIn("INVALID FIRMWARE PAIR", desc)

    def test_missing_and_secure_firmware_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            normal_code = root / "edk2-x86_64-code.fd"
            secure_code = root / "edk2-x86_64-secure-code.fd"
            vars_file = root / "edk2-i386-vars.fd"
            vars_file.write_bytes(b"vars")
            self.assertFalse(validate_firmware_pair(normal_code, vars_file)[0])
            secure_code.write_bytes(b"secure")
            self.assertFalse(validate_firmware_pair(secure_code, vars_file)[0])

    def test_discovery_prefers_normal_firmware_over_secure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            normal = root / "edk2-x86_64-code.fd"
            secure = root / "edk2-x86_64-secure-code.fd"
            vars_file = root / "edk2-i386-vars.fd"
            for path in (normal, secure, vars_file):
                path.write_bytes(path.name.encode("ascii"))
            code, found_vars, _ = find_ovmf(dir_override=str(root))
            self.assertEqual(code, normal.resolve())
            self.assertEqual(found_vars, vars_file.resolve())

    def test_explicit_pair_requires_both_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            code = root / "edk2-x86_64-code.fd"
            code.write_bytes(b"code")
            c, v, desc = find_ovmf(str(code), str(root / "missing-vars.fd"))
            self.assertIsNone(c)
            self.assertIsNone(v)
            self.assertIn("VARS not found", desc)

    def test_ovmf_missing_behavior(self) -> None:
        # Clear environment variables and verify clean MISSING return without crashing
        os.environ.pop("MALRYNTH_OVMF_CODE", None)
        os.environ.pop("MALRYNTH_OVMF_VARS", None)
        os.environ.pop("MALRYNTH_OVMF", None)
        # Point cache directories to empty temp dir
        with tempfile.TemporaryDirectory() as empty_dir:
            os.environ["LOCALAPPDATA"] = empty_dir
            os.environ["USERPROFILE"] = empty_dir
            c, v, desc = find_ovmf()
            # If system doesn't have OVMF installed globally, it should be None
            # If it is None, it should return a descriptive error string
            if c is None:
                self.assertIn("OVMF firmware not found", desc)


if __name__ == "__main__":
    unittest.main()
