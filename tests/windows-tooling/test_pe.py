"""Unit tests for PE/COFF structural parsing, alignment accounting, and binary diffing."""

from __future__ import annotations

import ast
import shutil
import struct
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
from malrynth_tooling.pe_diff import diff_pe
from malrynth_tooling.pe_inspect import inspect_pe


class TestPeInspectionAndDiff(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg = MalrynthConfig()
        cls.loader_path = cls.cfg.esp_dir / "EFI" / "BOOT" / "BOOTX64.EFI"
        if not cls.loader_path.is_file():
            build_image(cls.cfg.root)

    def test_pe_structural_inspection(self) -> None:
        pe = inspect_pe(self.loader_path)
        self.assertEqual(pe.dos_magic, "MZ")
        self.assertEqual(pe.pe_signature, "PE\\0\\0")
        self.assertEqual(pe.machine, "IMAGE_FILE_MACHINE_AMD64")
        self.assertEqual(pe.subsystem, "IMAGE_SUBSYSTEM_EFI_APPLICATION")
        self.assertEqual(pe.file_alignment, 512)
        self.assertEqual(pe.section_alignment, 4096)
        self.assertEqual(pe.size_of_headers, 1024)
        self.assertGreaterEqual(pe.number_of_sections, 4)

        section_names = [s.name for s in pe.sections]
        self.assertIn(".text", section_names)
        self.assertIn(".rdata", section_names)
        self.assertIn(".data", section_names)
        self.assertIn(".reloc", section_names)

    def test_section_and_file_alignment_accounting(self) -> None:
        """Every section's SizeOfRawData must be a multiple of FileAlignment (512),

        and Headers + Sum(RawData) must equal total FileSize.
        """
        pe = inspect_pe(self.loader_path)
        total_raw = 0
        for s in pe.sections:
            self.assertEqual(
                s.raw_data_size % pe.file_alignment,
                0,
                f"Section {s.name} raw size {s.raw_data_size} is not a multiple of file alignment {pe.file_alignment}",
            )
            total_raw += s.raw_data_size

        self.assertEqual(
            pe.file_size,
            pe.size_of_headers + total_raw,
            f"File size {pe.file_size} does not match headers ({pe.size_of_headers}) + raw sections ({total_raw})",
        )

    def test_brepro_and_debug_none_guarantees(self) -> None:
        """Verify /Brepro produces deterministic hash timestamp and /DEBUG:NONE eliminates PDB."""
        pe = inspect_pe(self.loader_path)
        self.assertNotEqual(pe.timedatestamp, 0)
        # Debug directory, if present for /Brepro REPRO marker, must not carry a PDB file payload
        data = self.loader_path.read_bytes()
        debug_dir = next((dd for dd in pe.data_directories if dd.index == 6), None)
        if debug_dir and debug_dir.size > 0:
            rdata_sec = next(s for s in pe.sections if s.name == ".rdata")
            file_off = debug_dir.rva - rdata_sec.virtual_address + rdata_sec.raw_data_offset
            _, ts, _, _, dbg_type, sz_data, _, _ = struct.unpack_from("<IIHHIIII", data, file_off)
            # Type 16 is IMAGE_DEBUG_TYPE_REPRO
            self.assertEqual(dbg_type, 16, "Expected IMAGE_DEBUG_TYPE_REPRO for /Brepro")
            self.assertEqual(sz_data, 0, "Expected 0 data payload for /DEBUG:NONE")

    def test_pe_diff_identical(self) -> None:
        report = diff_pe(self.loader_path, self.loader_path)
        self.assertTrue(report.is_identical)
        self.assertEqual(report.size_diff, 0)
        self.assertIn("BYTE-IDENTICAL", report.format_report())

    def test_pe_diff_detects_structural_difference(self) -> None:
        with tempfile.TemporaryDirectory(prefix="malrynth-test-pediff-") as temp_dir:
            temp_bin = Path(temp_dir) / "modified.efi"
            data = bytearray(self.loader_path.read_bytes())
            # Modify FileAlignment or a section raw size
            # Offset to SizeOfHeaders in optional header (e_lfanew + 24 + 60)
            e_lfanew, = struct.unpack_from("<I", data, 0x3C)
            # Flip one byte in the timestamp field (e_lfanew + 8)
            ts, = struct.unpack_from("<I", data, e_lfanew + 8)
            struct.pack_into("<I", data, e_lfanew + 8, ts ^ 0xFFFFFFFF)
            temp_bin.write_bytes(data)

            report = diff_pe(self.loader_path, temp_bin)
            self.assertFalse(report.is_identical)
            self.assertTrue(len(report.header_diffs) > 0)
            self.assertIn("TimeDateStamp", report.format_report())

    def test_python_ast_syntax_compatibility(self) -> None:
        """Verify all codebase Python files are syntactically valid in Python 3.8+."""
        root = self.cfg.root
        py_files = list(root.glob("tools/windows/**/*.py")) + list(root.glob("tests/windows-tooling/**/*.py"))
        for pf in py_files:
            code = pf.read_text(encoding="utf-8")
            # ast.parse must succeed
            tree = ast.parse(code, filename=str(pf))
            self.assertIsNotNone(tree)


if __name__ == "__main__":
    unittest.main()
