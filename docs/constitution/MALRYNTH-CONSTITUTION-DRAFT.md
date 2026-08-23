# The Malrynth Constitution — DRAFT

**Status:** DRAFT. Not immutable law. Amendable by ADR while the project is pre-1.0.
**Date:** 2026-08-19

This document states what Malrynth is *for*. It exists because the decisions that ruin an
operating system are rarely made all at once — they are made one reasonable-sounding
exception at a time, years apart. Writing the commitments down first makes each exception
visible as an exception.

Where a principle is not yet implemented, it says so. **A principle that is aspirational is
labelled aspirational.** Nothing here claims a property Malrynth currently has.

---

## I. Ownership

**1. The device belongs to its owner.**
Not to Malrynth, not to a vendor, not to an application. Where owner control conflicts with
vendor convenience, the owner wins. *(Aspirational: no ownership mechanism exists yet.)*

**2. Local accounts remain first-class.**
A Malrynth device is fully configurable and fully usable with a local account. A cloud
identity is never required to reach a working desktop. *(Aspirational.)*

**3. Core local functionality works without the Internet.**
Files, settings, media playback, and recovery are local capabilities. Network loss degrades
network features only. *(Aspirational.)*

**4. Malrynth Account is optional.**
It may unlock sync and entitlements. It may not gate the operating system. *(Aspirational.)*

**5. Sideloading remains possible.**
The owner may install software from outside any store. It may require an explicit,
informed action; it may not be impossible. *(Aspirational.)*

**6. Third-party stores are legitimate.**
Competing stores get the same technically supported installation path as the first-party
store. *(Aspirational.)*

**7. Competing applications are not intentionally degraded.**
Malrynth may not grant private platform advantages merely because software is first-party. An
ordinary first-party application and an equivalent ordinary third-party application must be able
to request the same ordinary capabilities under the same policy. First-party applications are
replaceable by design.

This is **ordinary-application parity, not universal privilege parity.** Privileged system roles
— recovery, security containment, update authority, package authority, firmware management, and
login and session infrastructure — may hold capabilities ordinary applications cannot, where the
privilege is necessary to the role. Such privilege must be role-based, documented, narrowly
scoped, auditable, and revocable where technically possible; it is never conferred by a binary
being first-party. Where Malrynth intentionally supports replacing such a role, third-party
software may occupy it on the same admission and security terms.
*(Aspirational. Amended by [ADR-0005](../adr/ADR-0005-ordinary-application-parity.md).)*

## II. Security

**8. Native applications receive only explicit authority.**
No ambient authority. A program's power is exactly the set of capabilities handed to it.
Absence of a capability is absence of the ability, not a permission prompt. *(Designed; see
`docs/architecture/CAPABILITY-MODEL.md`. Not implemented before M3.)*

**9. Security is architectural, not a scanner.**
Isolation, least authority, and small trusted computing bases are the mechanism. Detection
is a supplement to a sound architecture, never a substitute for one.

**10. Updates are transactional and rollbackable.**
An update either fully applies or does not apply. A device that fails to boot after an
update can return to the previous known-good state without external media. *(Aspirational;
M5.)*

**11. Recovery works offline.**
Recovery must not depend on a network, an account, or a server that might not exist in ten
years. *(Aspirational; M5.)*

**12. Rust is not a security argument.**
Rust eliminates a class of memory-safety defects in safe code. It does not eliminate logic
errors, capability leaks, side channels, malicious hardware, supply-chain compromise, or
mistakes inside `unsafe`. Malrynth may never claim to be secure *because* it is written in
Rust. Security claims require a threat model and evidence.

## III. Privacy

**13. User data collection is minimised.**
Data not collected cannot be leaked, subpoenaed, or sold. Collection requires a stated
purpose and a retention limit.

**14. Advertising profiles are not part of the operating system.**
Malrynth does not build, store, or export advertising identifiers or behavioural profiles.
This is a structural commitment, not a setting.

**15. Non-essential telemetry is independently controllable.**
Crash reporting, usage metrics, and diagnostics are separately switchable, off by default
where practical, and inspectable before transmission. "Essential" is narrowly defined and
documented, not decided case by case.

## IV. Artificial intelligence

**16. AI is optional and provider-neutral.**
No Malrynth feature required for normal operation may depend on a model. The user chooses
the provider, including a local one, or none.

**17. AI is never the final security authority.**
No model output may, on its own, grant a capability, authorise access, or dismiss a security
boundary. A model may advise; the capability system decides.

## V. Engineering

**18. Performance regressions are measured, not argued.**
Budgets are defined before optimisation and enforced by tests. "It feels fast" is not
evidence. See `docs/performance/PERFORMANCE-CONSTITUTION.md`.

**19. Stable APIs are not casually broken.**
Once an interface is declared LOCKED it carries a compatibility commitment and a deprecation
window. Before that, it is labelled EXPERIMENTAL and may change without notice — which is
why nothing is declared stable early.

**20. Customisation does not silently bypass security boundaries.**
The system is deeply configurable. Configuration that weakens a security boundary must say
so, explicitly, at the moment it is applied.

**21. Malrynth must not get worse because it got bigger.**
Growth is not an excuse for slower boots, larger idle memory, or degraded responsiveness.
Every milestone re-measures the previous milestone's budgets.

**22. Honesty about state.**
Every document and interface labels itself **LOCKED**, **PROPOSED**, **EXPERIMENTAL**,
**DEFERRED** or **UNSOLVED**. Documentation never describes unbuilt systems in the present
tense. A project that lies to itself in its own documentation cannot be engineered.

---

## Amendment

This is a DRAFT. Amendments are made by ADR, which must state which principle changes, why,
and what is given up. A principle deleted without an ADR has not been deleted — it has been
forgotten, which is the failure mode this document exists to prevent.
