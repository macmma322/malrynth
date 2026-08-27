# M0 Loader +512-byte Structural Analysis

**Status:** ACCEPTED review evidence. This comparison explains the checked memory-map
normalization change; it does not establish 41,472 bytes as a permanent ceiling.

## Compared artifacts

The repository's `pe_inspect.py` and `pe_diff.py` were run against representative validated
release artifacts from immediately before and after the checked normalization change.

| | Pre-fix | Checked normalization |
|---|---:|---:|
| Source lineage | `integration/pre-m1-foundation` / review artifact | `fix/pre-m1-correctness-blockers` |
| File size | 40,960 (`0xA000`) | 41,472 (`0xA200`) |
| SHA-256 | `8cfa6b812de10bb9e60c40b62d50a1cbd4907b7ab9118e6bb888e185b2d6e8d5` | `be8a031df279820e6bd20f1a0c51d2f98d1bbee479435379444bf39f4e4960b6` |
| FileAlignment | 512 (`0x200`) | 512 (`0x200`) |
| SectionAlignment | 4,096 (`0x1000`) | 4,096 (`0x1000`) |
| SizeOfImage | 53,248 (`0xD000`) | 53,248 (`0xD000`) |

## Section evidence

| Section | Virtual size before -> after | Raw size before -> after | Interpretation |
|---|---:|---:|---|
| `.text` | 27,472 -> 27,856 (**+384**) | 27,648 -> 28,160 (**+512**) | Executable content crossed the next 512-byte file-alignment boundary. |
| `.rdata` | 11,084 -> 11,160 (**+76**) | 11,264 -> 11,264 (**0**) | Content grew but stayed inside the existing raw allocation. |
| `.data` | 60 -> 60 | 512 -> 512 | No size growth. |
| `.reloc` | 260 -> 248 (**-12**) | 512 -> 512 | Relocation content shrank; raw allocation was unchanged. |

The checked implementation moved normalization into a host-testable loader library and added
bounded-capacity, page-byte, region-end, and usable-total overflow failures. Its observable
virtual/content changes are `.text +384`, `.rdata +76`, and `.reloc -12`. Only `.text` crossed
a raw `FileAlignment` boundary: `0x6C00` became `0x6E00`. Later sections shifted by `0x200`,
so the complete PE grew exactly 512 bytes. Header size, section count, virtual addresses,
`SizeOfImage`, and all other section raw sizes stayed constant.

## Reproducibility and path-remapping checks

Both PE debug-directory records are type 16 (`IMAGE_DEBUG_TYPE_REPRO`) with zero data payload.
That is the `/Brepro` reproducibility marker, not a CodeView/PDB reference. Neither artifact
contains a CodeView debug payload; the zero payload is consistent with `/DEBUG:NONE`.

ASCII and UTF-16 printable-string scans found none of the following in either binary:

- drive-rooted `C:\\`, `C:/`, `D:\\`, or `D:/` paths;
- worktree names or `Malrynth-Codex` paths;
- `.cargo` or rustup-home paths.

The unchanged `FileAlignment`, the single explainable `.text` rounding step, the REPRO marker,
and the absence of host/build paths establish intentional source/alignment growth rather than
a recurrence of missing path remapping. Future size gates should still be based on an explicit
budget decision, not silently raised to this observed value.

## Final M1A reconciliation candidate

Integrating the pre-`ExitBootServices` map-capacity verdict adds another intentional 1,024
bytes relative to the 41,472-byte checked-normalization artifact. The final candidate is
42,496 bytes (`0xA600`), SHA-256
`1e18afa5458a3da1dbca41fe247d28fe6767a62c5521f0567172f01e4be13be4`.

| Section | 41,472-byte virtual -> final | Raw size change | Cause of file delta |
|---|---:|---:|---|
| `.text` | 27,856 -> 28,544 (**+688**) | 28,160 -> 28,672 (**+512**) | Preflight verdict, diagnostic path and defensive post-EBS halt cross one alignment boundary. |
| `.rdata` | 11,160 -> 11,424 (**+264**) | 11,264 -> 11,776 (**+512**) | Human-readable fatal reasons and preflight diagnostics cross one alignment boundary. |
| `.data` | 60 -> 60 | 512 -> 512 | No size growth. |
| `.reloc` | 248 -> 252 (**+4**) | 512 -> 512 | Relocation content changes within the existing allocation. |

`FileAlignment` remains 512 bytes, `SectionAlignment` remains 4,096 bytes, `SizeOfImage`
remains 53,248 bytes, and the section count remains four. The two crossed raw boundaries
therefore account for the complete `+1,024` file delta.

The final PE again contains a type-16 `IMAGE_DEBUG_TYPE_REPRO` record with zero payload,
consistent with `/Brepro` plus `/DEBUG:NONE`; it has no CodeView/PDB record. ASCII and UTF-16
scans found no drive-rooted, worktree, Cargo-home, `.cargo`, or rustup-home paths. This final
candidate remains structurally explainable, but 42,496 bytes is an observation rather than a
new permanent ceiling.
