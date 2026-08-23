"""Binary artifact validation for Malrynth kernel (ELF) and loader (PE/UEFI)."""

from __future__ import annotations

import struct
from pathlib import Path


class BinaryValidationError(Exception):
    pass


def validate_kernel_elf(path: Path) -> dict[str, object]:
    """Validate that the kernel binary is a 64-bit x86-64 ET_EXEC ELF."""
    if not path.is_file():
        raise BinaryValidationError(f"Kernel binary not found: {path}")

    data = path.read_bytes()
    if len(data) < 64:
        raise BinaryValidationError(f"File too small to be valid ELF ({len(data)} bytes): {path}")

    if data[:4] != b"\x7fELF":
        raise BinaryValidationError(f"Invalid ELF magic: {data[:4]!r}")

    ei_class = data[4]
    if ei_class != 2:
        raise BinaryValidationError(f"Expected 64-bit ELF (class 2), found class {ei_class}")

    ei_data = data[5]
    if ei_data != 1:
        raise BinaryValidationError(f"Expected little-endian ELF (data 1), found {ei_data}")

    e_type, e_machine = struct.unpack_from("<HH", data, 0x10)
    e_entry, = struct.unpack_from("<Q", data, 0x18)

    # e_type == 2 is ET_EXEC (executable), 3 is ET_DYN (shared object / PIE)
    if e_type != 2:
        type_str = "ET_DYN (PIE/Shared)" if e_type == 3 else f"unknown ({e_type})"
        raise BinaryValidationError(
            f"Kernel ELF must be ET_EXEC (type 2), but found {type_str}. "
            "malboot does not perform relocation; kernel must be linked with static relocation model."
        )

    # e_machine == 0x3E is EM_X86_64
    if e_machine != 0x3E:
        raise BinaryValidationError(f"Expected EM_X86_64 (0x3E), found machine {hex(e_machine)}")

    if e_entry == 0:
        raise BinaryValidationError("Kernel ELF entry point is 0x0")

    return {
        "format": "ELF64",
        "type": "ET_EXEC",
        "machine": "x86_64",
        "entry_point": hex(e_entry),
        "size_bytes": len(data),
    }


def validate_loader_pe(path: Path) -> dict[str, object]:
    """Validate that the loader binary is a 64-bit UEFI application PE32+ image."""
    if not path.is_file():
        raise BinaryValidationError(f"Loader binary not found: {path}")

    data = path.read_bytes()
    if len(data) < 128:
        raise BinaryValidationError(f"File too small to be valid PE ({len(data)} bytes): {path}")

    # DOS header magic MZ (0x5A4D)
    if data[:2] != b"MZ":
        raise BinaryValidationError(f"Invalid DOS magic: {data[:2]!r}")

    e_lfanew, = struct.unpack_from("<I", data, 0x3C)
    if e_lfanew + 24 > len(data):
        raise BinaryValidationError(f"Invalid e_lfanew offset {e_lfanew}")

    # PE signature PE\0\0 (0x00004550)
    pe_sig = data[e_lfanew:e_lfanew + 4]
    if pe_sig != b"PE\x00\x00":
        raise BinaryValidationError(f"Invalid PE signature: {pe_sig!r}")

    coff_offset = e_lfanew + 4
    machine, num_sections = struct.unpack_from("<HH", data, coff_offset)
    opt_header_size, = struct.unpack_from("<H", data, coff_offset + 16)

    # Machine 0x8664 is IMAGE_FILE_MACHINE_AMD64
    if machine != 0x8664:
        raise BinaryValidationError(f"Expected IMAGE_FILE_MACHINE_AMD64 (0x8664), found {hex(machine)}")

    opt_offset = coff_offset + 20
    if opt_header_size >= 70:
        magic, = struct.unpack_from("<H", data, opt_offset)
        # 0x20B is PE32+ (64-bit)
        if magic != 0x20B:
            raise BinaryValidationError(f"Expected PE32+ magic (0x20B), found {hex(magic)}")
        subsystem, = struct.unpack_from("<H", data, opt_offset + 68)
        # Subsystem 10 is IMAGE_SUBSYSTEM_EFI_APPLICATION
        if subsystem != 10:
            raise BinaryValidationError(f"Expected EFI Application subsystem (10), found {subsystem}")

    return {
        "format": "PE32+",
        "machine": "AMD64",
        "subsystem": "IMAGE_SUBSYSTEM_EFI_APPLICATION",
        "sections": num_sections,
        "size_bytes": len(data),
    }
