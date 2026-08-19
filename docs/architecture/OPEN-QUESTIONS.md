# Critical Open Questions

**Status:** LOCKED (the register); each question is UNSOLVED until decided.

Uncertainty is recorded here rather than buried in prose. Every entry states why it is
unresolved, **when it must be decided**, and **what evidence would settle it** — because a
question with no deadline is a question that gets answered by accident.

---

## Q1 — Which libc? **(highest leverage)**

**Unresolved because** the candidates trade very differently against Malrynth's capability
model, and none is an obvious fit.

| Option | For | Against |
|---|---|---|
| Port **musl** | Complete, small, clean, permissive (MIT) | Deeply Linux-syscall-shaped; the port is a rewrite of its bottom layer |
| **LLVM libc** | Modern, modular, actively developed, LLVM-aligned | Full build is **static-only, no dynamic loader**, many functions missing — verified 2026 |
| Write our own | Exact fit to capabilities | Enormous, and re-solving solved problems |
| **relibc**-style (Redox) | Proven on a capability-ish microkernel | Small ecosystem; couples us to another project's pace |

**Decide by:** end of M4 (M5 cannot start without it).
**Evidence required:** a spike porting musl's bottom layer to the M3 syscall surface;
measurement of how much of libc the POSIX facade actually needs; current LLVM-libc dynamic
loader status at decision time.
**Blocks:** POSIX, Rust `std`, SDK, every application, Wine.

## Q2 — Is POSIX the native personality, or a facade?

**Unresolved because** POSIX presumes ambient authority over a global namespace, which is
exactly what Malrynth rejects. `open("/etc/passwd")` has no capability-model meaning.

Current recommendation (PROPOSED): **facade**. Native API is capability-first; POSIX is a
compatibility layer holding capabilities on a program's behalf.

**Decide by:** end of M4, with Q1.
**Evidence required:** how much real software the facade can carry; what Wine actually needs.
**Blocks:** libc shape, Linux personality, software porting strategy.

## Q3 — GPU driver strategy **(highest technical risk)**

**Unresolved because** every path is bad in a different way: writing GPU drivers is enormous,
porting Mesa drags in Linux DRM/KMS assumptions, and vendor cooperation cannot be assumed.

**Decide by:** start of M6.
**Evidence required:** a spike assessing how much of a Mesa Vulkan driver is genuinely
kernel-interface-independent; realistic vendor engagement.
**Blocks:** compositor, UI, gaming, media encode — most of the visible product.

## Q4 — Initial production filesystem

MalrynthFS must not be the default for years, so something must carry M5. Options: a simple
Malrynth-designed FS, a ported ext-family reader/writer, or read-only system images plus a
separate data volume.

**Decide by:** start of M5. **Evidence:** crash-consistency test results.

## Q5 — Native stable ABI mechanism

Rust has no stable ABI. Long-term binary compatibility needs a stable boundary — C ABI is the
default answer, but it degrades the native Rust experience.

**Decide by:** M5 (before any third-party binary exists). **Evidence:** prototype of a Rust
API over a C ABI; ergonomics assessment.

## Q6 — Package signing root and key custody

Threshold signing with an offline root is the intent; where keys physically live is undecided,
and **no production key may exist before this is answered**.

**Decide by:** before the first signed release (M5). **Evidence:** HSM/hardware-token options.

## Q7 — UI toolkit rendering strategy

Retained vs immediate mode; GPU-only vs CPU fallback. Determines animation quality,
accessibility integration and memory footprint.

**Decide by:** start of M6. **Evidence:** prototypes measured against the frame-time budget.

## Q8 — Browser engine

Writing a modern engine is out of scope. Chromium and WebKit are enormous but real; Servo is
Rust-native but measured at 62% weighted WPT against Chromium's 89%, with realistic daily-use
in 2028–2030.

**Decide by:** post-M7. **Evidence:** porting cost per engine against Malrynth's platform APIs.

## Q9 — Office document engines

DOCX/XLSX/PPTX/ODF interoperability without writing every parser from zero.

**Decide by:** post-M7. **Evidence:** licence and fidelity assessment of reusable engines.

## Q10 — Codec licensing and patents

Codec patent obligations are independent of source licensing and can foreclose distribution
models.

**Decide by:** before shipping any media application. **Evidence:** professional legal review.

## Q11 — Cloud key recovery

E2E encryption with no recovery path loses user data; with a recovery path it is not really
E2E. This is a genuine, unavoidable tension.

**Decide by:** before Sync ships. **Evidence:** threat model plus a documented user-facing trade.

## Q12 — Organization identity and the BYOD boundary

Company policy must be scoped to company-managed state. Enforcing that *technically* — not
just by policy — is unsolved.

**Decide by:** before Organizations ships. **Evidence:** a capability-level design where
company policy simply cannot name personal data.

## Q13 — Licensing model

Open-core is recommended by the founder research and recorded as an input, not a decision.

**Decide by:** before any repository is made public or any external contribution is accepted.

## Q14 — Virtualization: kernel vs VMM split **(constrains M1–M4)**

Which primitives are kernel-resident and which belong in a user-space VMM. Getting this wrong
either bloats the TCB or makes virtualization unusably slow.

**Decide by:** end of M3 — **the earliest deadline in this register**, because M1's memory
model and M4's IOMMU work both depend on it.
**Evidence:** measurement of guest exit costs against a candidate split.

## Q15 — Anti-cheat

Kernel-level anti-cheat requires vendor cooperation that a new OS cannot assume. This may
simply be unavailable, and Malrynth must not promise it.

**Decide by:** n/a — tracked as a known limitation, not a solvable engineering task.

---

## Deadline summary

| By | Questions |
|---|---|
| End of M3 | Q14 (virtualization split) |
| End of M4 | Q1 (libc), Q2 (POSIX) |
| Start/during M5 | Q4 (filesystem), Q5 (ABI), Q6 (signing root) |
| Start of M6 | Q3 (GPU), Q7 (UI rendering) |
| Post-M7 | Q8 (browser), Q9 (office), Q11 (key recovery), Q12 (org boundary) |
| Before public release | Q10 (codecs), Q13 (licensing) |
| Not solvable by us | Q15 (anti-cheat) |
