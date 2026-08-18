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
