#!/usr/bin/env bash
# Shared helpers for the Malrynth developer tools.
#
# Sourced, never executed directly. Keeps host discovery in exactly one place so that
# tools/doctor reports the same facts the other tools act on.

set -Eeuo pipefail

MALRYNTH_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
readonly MALRYNTH_ROOT

# Build outputs. Overridable so developers can move build output off a slow volume
# (see docs/operations/DEVELOPMENT-ENVIRONMENT.md).
: "${CARGO_TARGET_DIR:=${MALRYNTH_ROOT}/target}"
export CARGO_TARGET_DIR
readonly ESP_DIR="${MALRYNTH_ROOT}/esp"
readonly BUILD_DIR="${MALRYNTH_ROOT}/build"

readonly TARGET_LOADER="x86_64-unknown-uefi"
readonly TARGET_KERNEL="x86_64-unknown-none"

# --- Compiler flags: single source of truth (see .cargo/config.toml) ----------------
#
# Path remapping makes builds reproducible across build directories. Without it the
# absolute build path is embedded verbatim in debug information, so the same commit built
# at two different paths produces different bytes -- which destroys the ability to use an
# independent rebuild as evidence of pipeline integrity (docs/security/SUPPLY-CHAIN.md).
#
# Three path sources must be remapped: the workspace, the cargo registry, and the Rust
# sysroot (which supplies core/alloc).
_cargo_home="${CARGO_HOME:-${HOME}/.cargo}"
_rust_sysroot="$(rustc --print sysroot 2>/dev/null || echo /nonexistent)"

REMAP_FLAGS=(
    "--remap-path-prefix=${MALRYNTH_ROOT}=/malrynth"
    "--remap-path-prefix=${_cargo_home}=/cargo"
    "--remap-path-prefix=${_rust_sysroot}=/rust"
)

# `force-frame-pointers` is required by the kernel panic backtrace, which walks the RBP
# chain. Without it the backtrace degrades -- LOUDLY, by design: the unwinder reports that
# the chain is implausible rather than printing plausible-looking garbage.
#
# `relocation-model=static` avoids GOT-relative addressing in an image that is loaded at a
# fixed address and never relocated.
KERNEL_RUSTFLAGS="-C relocation-model=static -C force-frame-pointers=yes ${REMAP_FLAGS[*]}"
# `/Brepro` is the MSVC/LLD reproducible-build switch. Without it, lld-link stamps the
# PE COFF header and the debug directory with wall-clock time, so two builds of identical
# source differ by 10 bytes. `/Brepro` replaces the timestamp with a content hash.
# `/PDBALTPATH` pins the PDB filename recorded in the PE debug directory. By default LLD
# records cargo's unit filename (malboot-<hash>.pdb), and that hash varies with the build
# path, so the recorded name -- and therefore /Brepro's content hash -- differed between
# build directories.
# `/DEBUG:NONE` suppresses the PE debug directory. Its CodeView GUID is derived from the
# side PDB, whose contents embed absolute object paths that `--remap-path-prefix` cannot
# reach (it remaps SOURCE paths, not linker output paths), leaving 8 bytes that varied
# between build directories. No Malrynth tooling consumes PE/PDB debug info; the kernel
# keeps full DWARF, which is what tools/symbolize actually reads.
LOADER_RUSTFLAGS="-C link-arg=/Brepro -C link-arg=/DEBUG:NONE ${REMAP_FLAGS[*]}"
readonly KERNEL_RUSTFLAGS LOADER_RUSTFLAGS

# The exact strings the kernel emits. CI asserts on these and nothing else.
readonly BOOT_OK_MARKER="MALRYNTH_M0_BOOT_OK"
readonly BOOT_FAIL_MARKER="MALRYNTH_M0_BOOT_FAIL"

if [[ -t 1 ]]; then
    C_RED=$'\033[31m'; C_GRN=$'\033[32m'; C_YEL=$'\033[33m'
    C_BLD=$'\033[1m'; C_RST=$'\033[0m'
else
    C_RED=''; C_GRN=''; C_YEL=''; C_BLD=''; C_RST=''
fi
readonly C_RED C_GRN C_YEL C_BLD C_RST

info()  { printf '%s==>%s %s\n' "${C_BLD}" "${C_RST}" "$*"; }
ok()    { printf '%s  ok%s   %s\n' "${C_GRN}" "${C_RST}" "$*"; }
warn()  { printf '%s  warn%s %s\n' "${C_YEL}" "${C_RST}" "$*" >&2; }
fail()  { printf '%s  FAIL%s %s\n' "${C_RED}" "${C_RST}" "$*" >&2; }
die()   { fail "$*"; exit 1; }

# Locates OVMF firmware. Prints "CODE_PATH VARS_PATH" or returns 1.
#
# Paths differ across distributions, so candidates are probed rather than hardcoded.
# The 4 MiB split CODE/VARS build is preferred: it is the layout current OVMF ships and
# the only one that supports a writable variable store without patching the code image.
find_ovmf() {
    local -a code_candidates=(
        /usr/share/OVMF/OVMF_CODE_4M.fd
        /usr/share/OVMF/OVMF_CODE.fd
        /usr/share/edk2/ovmf/OVMF_CODE.fd
        /usr/share/qemu/ovmf-x86_64-code.bin
    )
    local -a vars_candidates=(
        /usr/share/OVMF/OVMF_VARS_4M.fd
        /usr/share/OVMF/OVMF_VARS.fd
        /usr/share/edk2/ovmf/OVMF_VARS.fd
        /usr/share/qemu/ovmf-x86_64-vars.bin
    )
    local code='' vars=''
    for c in "${code_candidates[@]}"; do [[ -r "$c" ]] && { code="$c"; break; }; done
    for v in "${vars_candidates[@]}"; do [[ -r "$v" ]] && { vars="$v"; break; }; done
    [[ -n "$code" && -n "$vars" ]] || return 1
    printf '%s %s\n' "$code" "$vars"
}

need_cmd() {
    command -v "$1" >/dev/null 2>&1 || die "required command not found: $1 (run tools/doctor)"
}
