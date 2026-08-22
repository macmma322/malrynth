"""Unit tests for binary artifact verification (ELF and PE/COFF)."""

from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path

# Add tools/windows to sys.path
_tools_dir = Path(__file__).resolve().parent.parent.parent / "tools" / "windows"
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from malrynth_tooling.config import MalrynthConfig
from malrynth_tooling.verify import (
    BinaryValidationError,
    validate_kernel_elf,
    validate_loader_pe,
)


class TestVerify(unittest.TestCase):
    def test_actual_build_artifacts(self) -> None:
        cfg = MalrynthConfig()
        loader_path = cfg.esp_dir / "EFI" / "BOOT" / "BOOTX64.EFI"
        kernel_path = cfg.esp_dir / "malrynth" / "kernel.elf"

        if loader_path.is_file():
            loader_info = validate_loader_pe(loader_path)
            self.assertEqual(loader_info["format"], "PE32+")
            self.assertEqual(loader_info["subsystem"], "IMAGE_SUBSYSTEM_EFI_APPLICATION")

        if kernel_path.is_file():
            kernel_info = validate_kernel_elf(kernel_path)
            self.assertEqual(kernel_info["format"], "ELF64")
            self.assertEqual(kernel_info["type"], "ET_EXEC")

    def test_reject_corrupt_elf_magic(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"NOT_AN_ELF_HEADER" + b"\x00" * 64)
            p = Path(f.name)
        try:
            with self.assertRaises(BinaryValidationError) as ctx:
                validate_kernel_elf(p)
            self.assertIn("Invalid ELF magic", str(ctx.exception))
        finally:
            p.unlink(missing_ok=True)

    def test_reject_pie_elf(self) -> None:
        """Kernel must not be ET_DYN / PIE; loader expects fixed-address ET_EXEC."""
        # Construct synthetic ELF64 header with e_type = 3 (ET_DYN)
        data = bytearray(64)
        data[:4] = b"\x7fELF"
        data[4] = 2  # 64-bit
        data[5] = 1  # little-endian
        data[6] = 1  # ELF version
        struct.pack_into("<HH", data, 0x10, 3, 0x3E)  # e_type=3 (ET_DYN), e_machine=0x3E
        struct.pack_into("<Q", data, 0x18, 0x1000000)  # e_entry

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(data)
            p = Path(f.name)
        try:
            with self.assertRaises(BinaryValidationError) as ctx:
                validate_kernel_elf(p)
            self.assertIn("Kernel ELF must be ET_EXEC", str(ctx.exception))
        finally:
            p.unlink(missing_ok=True)

    def test_reject_invalid_pe_magic(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"INVALID_DOS_HEADER" + b"\x00" * 128)
            p = Path(f.name)
        try:
            with self.assertRaises(BinaryValidationError) as ctx:
                validate_loader_pe(p)
            self.assertIn("Invalid DOS magic", str(ctx.exception))
        finally:
            p.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
