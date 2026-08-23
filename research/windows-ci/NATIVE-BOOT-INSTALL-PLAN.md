# Native Windows M0 boot installation plan

Date: 2026-08-23

State: **READY TO INSTALL, NOT AUTHORIZED TO INSTALL**

## Current machine discovery

`Get-Command qemu-system-x86_64` and `where.exe qemu-system-x86_64` found nothing. WinGet and
Chocolatey inventory contain no QEMU/EDK2/OVMF package, Scoop is not installed, all known
QEMU executable paths are absent, and `malrynth.py doctor` reports both QEMU and OVMF
missing. Therefore:

- QEMU: **NOT INSTALLED**
- OVMF/EDK2: **NOT INSTALLED**
- native M0 boot: **not run**

No drive-wide scan, download, package installation, PATH change, Windows feature change, or
restart was performed.

## Trusted candidates

### Preferred: WinGet QEMU package

| Field | Verified value |
|---|---|
| Package identifier | `SoftwareFreedomConservancy.QEMU` |
| Package/version | QEMU `11.1.0` (2026-08-11) |
| Manifest publisher | QEMU Community |
| Source | Microsoft WinGet community source |
| Architecture | x64 |
| Installer | Nullsoft machine-scope EXE |
| Installer source | `https://qemu.weilnetz.de/w64/2026/qemu-w64-setup-20260811.exe` |
| WinGet SHA-256 | `F98A8AEB5F7FAEA9765B6DEE28316C266CD179D80354A2FED8E50176F9A2E59F` |
| Publisher SHA-512 | `5bcf9eed634e8575a37b74f445af41a2fe4106da512d0c30c368301d4c105037fdfab40a5287367a28a957624cddebbc8c07e16c88ab6634f554cdf3d16bf543` |
| Authenticode | Publisher states newer installers use an expired signing certificate; no current valid signature is claimed |
| Expected elevation | Yes: manifest scope is machine and destination is `%ProgramFiles%` |
| Expected reboot | No; no driver or Windows feature is required for TCG boot |
| Expected install path | `C:\Program Files\qemu` |
| Firmware included | Yes, under `C:\Program Files\qemu\share` |

QEMU's official download page explicitly directs Windows users to Stefan Weil's binaries.
WinGet adds a versioned source URL and mandatory SHA-256 verification. This is preferred over
running the same installer manually because WinGet gives a reproducible package identity and
hash gate.

### Direct publisher installer

The same x64 installer is available directly from the QEMU-referenced Stefan Weil site, with
the publisher SHA-512 file. It has the same architecture, expected path, firmware payload,
elevation, and reboot characteristics. It is acceptable only with both the published SHA-512
and WinGet SHA-256 checked before execution. WinGet remains the cleaner route.

MSYS2 is an authoritative alternative documented by QEMU, but installing an entire package
environment solely for M0 adds avoidable scope. Chocolatey is not selected because the
WinGet manifest maps directly to the QEMU-referenced publisher installer.

## Expected firmware

The QEMU package ships EDK2 firmware in `C:\Program Files\qemu\share`:

- `edk2-x86_64-code.fd`: x86_64 non-Secure-Boot CODE image; attach read-only.
- `edk2-i386-vars.fd`: upstream shared x86 VARS template used with x86_64 CODE; never attach
  the template writable. Copy it for every run.
- `edk2-x86_64-secure-code.fd`: Secure Boot-capable alternative; not selected for M0.

Provenance is QEMU's `pc-bios` EDK2 build payload, installed by the QEMU Windows installer.
No separate firmware download or committed firmware binary is needed.

## Approval-gated installation

Run only after explicit founder approval, from an elevated PowerShell:

```powershell
winget install --id SoftwareFreedomConservancy.QEMU --exact --source winget --version 11.1.0
```

Then open a new PowerShell only if the installer changed PATH and perform read-only discovery:

```powershell
$env:MALRYNTH_QEMU = 'C:\Program Files\qemu\qemu-system-x86_64.exe'
$env:MALRYNTH_OVMF_CODE = 'C:\Program Files\qemu\share\edk2-x86_64-code.fd'
$env:MALRYNTH_OVMF_VARS = 'C:\Program Files\qemu\share\edk2-i386-vars.fd'

Get-Item -LiteralPath $env:MALRYNTH_QEMU, $env:MALRYNTH_OVMF_CODE, $env:MALRYNTH_OVMF_VARS
& $env:MALRYNTH_QEMU --version
python tools/windows/malrynth.py doctor
```

Before booting, correct the runner defects recorded in `QEMU-CONTRACT-AUDIT.md`, especially
the ARM VARS fallback and interactive false-success path. Then, from
`D:\Malrynth-Codex-WindowsCI` on `ci/windows-native-m0`:

```powershell
python tools/windows/malrynth.py build
python tools/windows/malrynth.py verify
python tools/windows/malrynth.py run --timeout 60 --quiet
python tools/windows/malrynth.py run --timeout 60 --quiet
python tools/windows/malrynth.py run --timeout 60 --quiet
python tools/windows/malrynth.py test --boots 3
```

Do not count QEMU launch or exit code zero as success. Each supervised boot must contain the
exact serial marker `MALRYNTH_M0_BOOT_OK` and no failure marker. The current Windows CLI does
not implement the Linux panic-boot assertion or full cross-path reproducibility stage; run
those only after equivalent Windows commands exist rather than inventing commands.

## Sources checked

- QEMU official Windows download guidance: <https://www.qemu.org/download/#windows>
- QEMU-referenced Windows publisher index: <https://qemu.weilnetz.de/w64/2026/>
- WinGet 11.1.0 installer manifest: <https://github.com/microsoft/winget-pkgs/blob/master/manifests/s/SoftwareFreedomConservancy/QEMU/11.1.0/SoftwareFreedomConservancy.QEMU.installer.yaml>
- QEMU EDK2 build layout: <https://github.com/qemu/qemu/blob/master/roms/edk2-build.config>
