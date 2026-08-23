"""Structural binary comparison for PE/COFF binaries."""

from __future__ import annotations

from pathlib import Path

from .pe_inspect import PeInfo, inspect_pe


class PeDiffReport:
    def __init__(self, pe_a: PeInfo, pe_b: PeInfo) -> None:
        self.pe_a = pe_a
        self.pe_b = pe_b
        self.is_identical = pe_a.sha256 == pe_b.sha256
        self.size_diff = pe_b.file_size - pe_a.file_size
        self.header_diffs: list[str] = []
        self.section_diffs: list[str] = []
        self.data_dir_diffs: list[str] = []
        self._analyze()

    def _analyze(self) -> None:
        a, b = self.pe_a, self.pe_b

        # Compare Header fields
        if a.file_size != b.file_size:
            self.header_diffs.append(f"File Size: {a.file_size:,} vs {b.file_size:,} (delta: {self.size_diff:+d} bytes)")
        if a.file_alignment != b.file_alignment:
            self.header_diffs.append(f"FileAlignment: 0x{a.file_alignment:X} vs 0x{b.file_alignment:X}")
        if a.section_alignment != b.section_alignment:
            self.header_diffs.append(f"SectionAlignment: 0x{a.section_alignment:X} vs 0x{b.section_alignment:X}")
        if a.size_of_image != b.size_of_image:
            self.header_diffs.append(f"SizeOfImage: 0x{a.size_of_image:X} ({a.size_of_image:,}) vs 0x{b.size_of_image:X} ({b.size_of_image:,})")
        if a.size_of_headers != b.size_of_headers:
            self.header_diffs.append(f"SizeOfHeaders: {a.size_of_headers:,} vs {b.size_of_headers:,}")
        if a.entry_point != b.entry_point:
            self.header_diffs.append(f"EntryPoint: {a.entry_point_hex} vs {b.entry_point_hex}")
        if a.image_base != b.image_base:
            self.header_diffs.append(f"ImageBase: {a.image_base_hex} vs {b.image_base_hex}")
        if a.timedatestamp != b.timedatestamp:
            self.header_diffs.append(f"TimeDateStamp: {a.timedatestamp_hex} vs {b.timedatestamp_hex}")
        if a.linker_version != b.linker_version:
            self.header_diffs.append(f"LinkerVersion: {a.linker_version} vs {b.linker_version}")
        if a.dll_characteristics != b.dll_characteristics:
            self.header_diffs.append(f"DllCharacteristics: 0x{a.dll_characteristics:04X} vs 0x{b.dll_characteristics:04X}")
        if a.number_of_sections != b.number_of_sections:
            self.header_diffs.append(f"NumberOfSections: {a.number_of_sections} vs {b.number_of_sections}")

        # Compare Data Directories
        dirs_a = {dd.index: dd for dd in a.data_directories}
        dirs_b = {dd.index: dd for dd in b.data_directories}
        all_indices = sorted(set(dirs_a.keys()) | set(dirs_b.keys()))
        for idx in all_indices:
            da = dirs_a.get(idx)
            db = dirs_b.get(idx)
            if da and db:
                if da.size != db.size or da.rva != db.rva:
                    self.data_dir_diffs.append(
                        f"Directory [{idx:2d}] {da.name:<22}: A=(RVA 0x{da.rva:X}, Size {da.size:,}) vs B=(RVA 0x{db.rva:X}, Size {db.size:,})"
                    )
            elif da and da.size > 0:
                self.data_dir_diffs.append(f"Directory [{idx:2d}] {da.name} present in A ({da.size:,} bytes) but absent in B")
            elif db and db.size > 0:
                self.data_dir_diffs.append(f"Directory [{idx:2d}] {db.name} present in B ({db.size:,} bytes) but absent in A")

        # Compare Sections
        secs_a = {s.name: s for s in a.sections}
        secs_b = {s.name: s for s in b.sections}
        all_sec_names = list(dict.fromkeys([s.name for s in a.sections] + [s.name for s in b.sections]))

        for name in all_sec_names:
            sa = secs_a.get(name)
            sb = secs_b.get(name)
            if sa and sb:
                changes = []
                if sa.virtual_size != sb.virtual_size:
                    changes.append(f"VirtSize: 0x{sa.virtual_size:X} ({sa.virtual_size:,}) -> 0x{sb.virtual_size:X} ({sb.virtual_size:,}) [delta {sb.virtual_size - sa.virtual_size:+d}]")
                if sa.raw_data_size != sb.raw_data_size:
                    changes.append(f"RawSize: 0x{sa.raw_data_size:X} ({sa.raw_data_size:,}) -> 0x{sb.raw_data_size:X} ({sb.raw_data_size:,}) [delta {sb.raw_data_size - sa.raw_data_size:+d}]")
                if sa.raw_data_offset != sb.raw_data_offset:
                    changes.append(f"RawOffset: 0x{sa.raw_data_offset:X} -> 0x{sb.raw_data_offset:X}")
                if sa.virtual_address != sb.virtual_address:
                    changes.append(f"VirtAddr: 0x{sa.virtual_address:X} -> 0x{sb.virtual_address:X}")
                if sa.sha256 != sb.sha256:
                    changes.append(f"Content SHA256: {sa.sha256[:12]}... -> {sb.sha256[:12]}...")
                if changes:
                    self.section_diffs.append(f"Section {name:<8}: " + "; ".join(changes))
            elif sa:
                self.section_diffs.append(f"Section {name} present in A (raw {sa.raw_data_size:,} bytes) but missing in B")
            elif sb:
                self.section_diffs.append(f"Section {name} present in B (raw {sb.raw_data_size:,} bytes) but missing in A")

    def format_report(self) -> str:
        lines = [
            "PE/COFF Structural Diff Report",
            "=" * 70,
            f"File A: {self.pe_a.file_path} ({self.pe_a.file_size:,} bytes, {self.pe_a.sha256[:16]}...)",
            f"File B: {self.pe_b.file_path} ({self.pe_b.file_size:,} bytes, {self.pe_b.sha256[:16]}...)",
            "-" * 70,
        ]

        if self.is_identical:
            lines.append("RESULT: Binaries are BYTE-IDENTICAL.")
            return "\n".join(lines)

        lines.append(f"RESULT: Binaries DIFFER (Size delta: {self.size_diff:+d} bytes)")
        lines.append("")

        if self.header_diffs:
            lines.append("Header Differences:")
            for d in self.header_diffs:
                lines.append(f"  * {d}")
            lines.append("")

        if self.data_dir_diffs:
            lines.append("Data Directory Differences:")
            for d in self.data_dir_diffs:
                lines.append(f"  * {d}")
            lines.append("")

        if self.section_diffs:
            lines.append("Section Differences:")
            for d in self.section_diffs:
                lines.append(f"  * {d}")
            lines.append("")

        return "\n".join(lines)


def diff_pe(path_a: Path | str, path_b: Path | str) -> PeDiffReport:
    """Compare two PE binaries structurally and return difference report."""
    pe_a = inspect_pe(path_a)
    pe_b = inspect_pe(path_b)
    return PeDiffReport(pe_a, pe_b)
