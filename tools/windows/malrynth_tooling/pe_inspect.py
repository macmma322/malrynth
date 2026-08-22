"""Pure Python standard library PE/COFF binary inspector for UEFI loader binaries."""

from __future__ import annotations

import hashlib
import struct
from dataclasses import asdict, dataclass
from pathlib import Path


class PeInspectionError(Exception):
    pass


@dataclass
class PeSection:
    name: str
    virtual_size: int
    virtual_address: int
    raw_data_size: int
    raw_data_offset: int
    characteristics: int
    characteristics_flags: list[str]
    sha256: str
    entropy: float


@dataclass
class PeDataDirectory:
    name: str
    index: int
    rva: int
    size: int


@dataclass
class PeInfo:
    file_path: str
    file_size: int
    sha256: str
    dos_magic: str
    e_lfanew: int
    pe_signature: str
    machine: str
    machine_raw: int
    number_of_sections: int
    timedatestamp: int
    timedatestamp_hex: str
    size_of_optional_header: int
    characteristics: int
    magic: str
    linker_version: str
    size_of_code: int
    size_of_initialized_data: int
    size_of_uninitialized_data: int
    entry_point: int
    entry_point_hex: str
    base_of_code: int
    image_base: int
    image_base_hex: str
    section_alignment: int
    file_alignment: int
    size_of_image: int
    size_of_headers: int
    checksum: int
    subsystem: str
    subsystem_raw: int
    dll_characteristics: int
    dll_characteristics_flags: list[str]
    number_of_rva_and_sizes: int
    data_directories: list[PeDataDirectory]
    debug_directory_present: bool
    debug_directory_size: int
    certificate_table_present: bool
    relocations_present: bool
    sections: list[PeSection]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _compute_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    import math
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    entropy = 0.0
    length = len(data)
    for count in counts:
        if count > 0:
            p = count / length
            entropy -= p * math.log2(p)
    return round(entropy, 4)


def inspect_pe(path: Path | str) -> PeInfo:
    """Parse and extract detailed structural information from a PE/COFF binary."""
    p = Path(path).resolve()
    if not p.is_file():
        raise PeInspectionError(f"File not found: {p}")

    data = p.read_bytes()
    file_size = len(data)
    file_sha256 = hashlib.sha256(data).hexdigest()

    if file_size < 64:
        raise PeInspectionError(f"File too small for PE/COFF DOS header: {file_size} bytes")

    if data[:2] != b"MZ":
        raise PeInspectionError(f"Invalid DOS magic: {data[:2]!r}")

    e_lfanew, = struct.unpack_from("<I", data, 0x3C)
    if e_lfanew + 24 > file_size:
        raise PeInspectionError(f"Invalid e_lfanew offset {e_lfanew} beyond file size {file_size}")

    pe_sig = data[e_lfanew:e_lfanew + 4]
    if pe_sig != b"PE\x00\x00":
        raise PeInspectionError(f"Invalid PE signature: {pe_sig!r}")

    coff_offset = e_lfanew + 4
    (
        machine,
        num_sections,
        timedatestamp,
        ptr_symbol_table,
        num_symbols,
        opt_hdr_size,
        characteristics,
    ) = struct.unpack_from("<HHIIIHH", data, coff_offset)

    machine_names = {
        0x014C: "IMAGE_FILE_MACHINE_I386",
        0x8664: "IMAGE_FILE_MACHINE_AMD64",
        0xAA64: "IMAGE_FILE_MACHINE_ARM64",
    }
    machine_str = machine_names.get(machine, f"UNKNOWN (0x{machine:04X})")

    opt_offset = coff_offset + 20
    if opt_hdr_size < 2:
        raise PeInspectionError(f"Optional header size too small: {opt_hdr_size}")

    opt_magic, = struct.unpack_from("<H", data, opt_offset)
    is_pe32_plus = opt_magic == 0x20B
    magic_str = "PE32+ (64-bit)" if is_pe32_plus else ("PE32 (32-bit)" if opt_magic == 0x10B else f"0x{opt_magic:04X}")

    if not is_pe32_plus:
        raise PeInspectionError(f"Expected PE32+ (64-bit) optional header, got {magic_str}")

    (
        major_linker,
        minor_linker,
        size_of_code,
        size_of_init_data,
        size_of_uninit_data,
        entry_point,
        base_of_code,
    ) = struct.unpack_from("<BBIIIII", data, opt_offset + 2)

    image_base, = struct.unpack_from("<Q", data, opt_offset + 24)
    (
        section_alignment,
        file_alignment,
        major_os,
        minor_os,
        major_img,
        minor_img,
        major_subsys,
        minor_subsys,
        win32_ver,
        size_of_image,
        size_of_headers,
        checksum,
        subsystem,
        dll_characteristics,
        size_stack_reserve,
        size_stack_commit,
        size_heap_reserve,
        size_heap_commit,
        loader_flags,
        num_rva_sizes,
    ) = struct.unpack_from("<IIHHHHHHIIIIHHQQQQII", data, opt_offset + 32)

    subsystem_names = {
        1: "IMAGE_SUBSYSTEM_NATIVE",
        2: "IMAGE_SUBSYSTEM_WINDOWS_GUI",
        3: "IMAGE_SUBSYSTEM_WINDOWS_CUI",
        10: "IMAGE_SUBSYSTEM_EFI_APPLICATION",
        11: "IMAGE_SUBSYSTEM_EFI_BOOT_SERVICE_DRIVER",
        12: "IMAGE_SUBSYSTEM_EFI_RUNTIME_DRIVER",
        13: "IMAGE_SUBSYSTEM_EFI_ROM",
    }
    subsystem_str = subsystem_names.get(subsystem, f"UNKNOWN ({subsystem})")

    # Data directories
    dir_names = [
        "Export Table",
        "Import Table",
        "Resource Table",
        "Exception Table",
        "Certificate Table",
        "Base Relocation Table",
        "Debug Directory",
        "Architecture",
        "Global Ptr",
        "TLS Table",
        "Load Config Table",
        "Bound Import",
        "IAT",
        "Delay Import",
        "CLR Runtime Header",
        "Reserved",
    ]

    data_dirs_offset = opt_offset + 112
    data_directories: list[PeDataDirectory] = []
    for i in range(min(num_rva_sizes, len(dir_names))):
        dd_off = data_dirs_offset + i * 8
        if dd_off + 8 <= file_size:
            rva, sz = struct.unpack_from("<II", data, dd_off)
            data_directories.append(PeDataDirectory(dir_names[i], i, rva, sz))

    debug_dir_entry = next((dd for dd in data_directories if dd.index == 6), None)
    debug_present = debug_dir_entry is not None and debug_dir_entry.size > 0
    debug_size = debug_dir_entry.size if debug_dir_entry else 0

    cert_dir_entry = next((dd for dd in data_directories if dd.index == 4), None)
    cert_present = cert_dir_entry is not None and cert_dir_entry.size > 0

    reloc_dir_entry = next((dd for dd in data_directories if dd.index == 5), None)
    reloc_present = reloc_dir_entry is not None and reloc_dir_entry.size > 0

    # Section headers
    sections_offset = opt_offset + opt_hdr_size
    sections: list[PeSection] = []

    for i in range(num_sections):
        sec_off = sections_offset + i * 40
        if sec_off + 40 > file_size:
            break
        raw_name = data[sec_off:sec_off + 8]
        sec_name = raw_name.split(b"\x00")[0].decode("latin-1", errors="replace")

        v_size, v_addr, raw_size, raw_ptr, _, _, _, _, characteristics_sec = struct.unpack_from(
            "<IIIIIIHHI", data, sec_off + 8
        )

        char_flags: list[str] = []
        if characteristics_sec & 0x00000020:
            char_flags.append("CNT_CODE")
        if characteristics_sec & 0x00000040:
            char_flags.append("CNT_INITIALIZED_DATA")
        if characteristics_sec & 0x00000080:
            char_flags.append("CNT_UNINITIALIZED_DATA")
        if characteristics_sec & 0x20000000:
            char_flags.append("MEM_EXECUTE")
        if characteristics_sec & 0x40000000:
            char_flags.append("MEM_READ")
        if characteristics_sec & 0x80000000:
            char_flags.append("MEM_WRITE")
        if characteristics_sec & 0x02000000:
            char_flags.append("MEM_DISCARDABLE")

        # Extract section payload
        sec_data = data[raw_ptr:raw_ptr + raw_size] if raw_ptr + raw_size <= file_size else b""
        sec_hash = hashlib.sha256(sec_data).hexdigest()
        sec_entropy = _compute_entropy(sec_data)

        sections.append(
            PeSection(
                name=sec_name,
                virtual_size=v_size,
                virtual_address=v_addr,
                raw_data_size=raw_size,
                raw_data_offset=raw_ptr,
                characteristics=characteristics_sec,
                characteristics_flags=char_flags,
                sha256=sec_hash,
                entropy=sec_entropy,
            )
        )

    # DLL characteristics flags
    dll_flags: list[str] = []
    if dll_characteristics & 0x0020:
        dll_flags.append("HIGH_ENTROPY_VA")
    if dll_characteristics & 0x0040:
        dll_flags.append("DYNAMIC_BASE")
    if dll_characteristics & 0x0080:
        dll_flags.append("FORCE_INTEGRITY")
    if dll_characteristics & 0x0100:
        dll_flags.append("NX_COMPAT")
    if dll_characteristics & 0x0200:
        dll_flags.append("NO_ISOLATION")
    if dll_characteristics & 0x0400:
        dll_flags.append("NO_SEH")
    if dll_characteristics & 0x0800:
        dll_flags.append("NO_BIND")
    if dll_characteristics & 0x2000:
        dll_flags.append("WDM_DRIVER")
    if dll_characteristics & 0x8000:
        dll_flags.append("TERMINAL_SERVER_AWARE")

    return PeInfo(
        file_path=str(p),
        file_size=file_size,
        sha256=file_sha256,
        dos_magic="MZ",
        e_lfanew=e_lfanew,
        pe_signature="PE\\0\\0",
        machine=machine_str,
        machine_raw=machine,
        number_of_sections=num_sections,
        timedatestamp=timedatestamp,
        timedatestamp_hex=f"0x{timedatestamp:08X}",
        size_of_optional_header=opt_hdr_size,
        characteristics=characteristics,
        magic=magic_str,
        linker_version=f"{major_linker}.{minor_linker}",
        size_of_code=size_of_code,
        size_of_initialized_data=size_of_init_data,
        size_of_uninitialized_data=size_of_uninit_data,
        entry_point=entry_point,
        entry_point_hex=f"0x{entry_point:08X}",
        base_of_code=base_of_code,
        image_base=image_base,
        image_base_hex=f"0x{image_base:016X}",
        section_alignment=section_alignment,
        file_alignment=file_alignment,
        size_of_image=size_of_image,
        size_of_headers=size_of_headers,
        checksum=checksum,
        subsystem=subsystem_str,
        subsystem_raw=subsystem,
        dll_characteristics=dll_characteristics,
        dll_characteristics_flags=dll_flags,
        number_of_rva_and_sizes=num_rva_sizes,
        data_directories=data_directories,
        debug_directory_present=debug_present,
        debug_directory_size=debug_size,
        certificate_table_present=cert_present,
        relocations_present=reloc_present,
        sections=sections,
    )


def format_pe_report(pe: PeInfo) -> str:
    """Format a human-readable structural inspection report for a PE file."""
    lines: list[str] = [
        f"PE/COFF Structural Report: {pe.file_path}",
        "=" * 70,
        f"File Size:            {pe.file_size:,} bytes (0x{pe.file_size:X})",
        f"SHA-256:              {pe.sha256}",
        f"Machine:              {pe.machine} (0x{pe.machine_raw:04X})",
        f"Format:               {pe.magic}",
        f"Subsystem:            {pe.subsystem}",
        f"Linker Version:       {pe.linker_version}",
        f"TimeDateStamp:        {pe.timedatestamp_hex} ({pe.timedatestamp})",
        f"ImageBase:            {pe.image_base_hex}",
        f"EntryPoint:           {pe.entry_point_hex}",
        f"SectionAlignment:     {pe.section_alignment} bytes (0x{pe.section_alignment:X})",
        f"FileAlignment:        {pe.file_alignment} bytes (0x{pe.file_alignment:X})",
        f"SizeOfImage:          {pe.size_of_image} bytes (0x{pe.size_of_image:X})",
        f"SizeOfHeaders:        {pe.size_of_headers} bytes (0x{pe.size_of_headers:X})",
        f"NumberOfSections:     {pe.number_of_sections}",
        f"DebugDirectory:       {'PRESENT (' + str(pe.debug_directory_size) + ' bytes)' if pe.debug_directory_present else 'NONE (/DEBUG:NONE active)'}",
        f"CertificateTable:     {'PRESENT' if pe.certificate_table_present else 'NONE'}",
        f"RelocationsTable:     {'PRESENT' if pe.relocations_present else 'NONE'}",
        f"DLL Characteristics:  0x{pe.dll_characteristics:04X} ({', '.join(pe.dll_characteristics_flags)})",
        "",
        "Section Table:",
        f"  {'Name':<10} {'VirtSize':<10} {'VirtAddr':<10} {'RawSize':<10} {'RawOffset':<10} {'Flags':<22} {'SHA256 (first 12)':<14}",
        "  " + "-" * 88,
    ]

    total_raw_section_bytes = 0
    for s in pe.sections:
        total_raw_section_bytes += s.raw_data_size
        flags_str = ",".join(s.characteristics_flags[:3])
        lines.append(
            f"  {s.name:<10} 0x{s.virtual_size:<8X} 0x{s.virtual_address:<8X} 0x{s.raw_data_size:<8X} 0x{s.raw_data_offset:<8X} {flags_str:<22} {s.sha256[:12]}"
        )

    lines.append("  " + "-" * 88)
    lines.append(f"Headers size:           {pe.size_of_headers:,} bytes")
    lines.append(f"Total section raw size: {total_raw_section_bytes:,} bytes")
    lines.append(f"Calculated file size:   {pe.size_of_headers + total_raw_section_bytes:,} bytes")

    if pe.data_directories:
        lines.append("")
        lines.append("Data Directories (Active):")
        for dd in pe.data_directories:
            if dd.size > 0:
                lines.append(f"  [{dd.index:2d}] {dd.name:<24} RVA: 0x{dd.rva:08X}  Size: 0x{dd.size:08X} ({dd.size:,} bytes)")

    return "\n".join(lines)
