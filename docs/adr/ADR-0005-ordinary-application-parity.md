# ADR-0005 — Ordinary-Application Parity, Not Universal Privilege Parity

- **Status:** ACCEPTED (2026-08-23). Amends **Constitution §7**, which remains *aspirational*: this ADR fixes the principle, not an implementation.
- **Deciders:** Nikolay Nikolov Georgiev (founder)
- **Amends:** [`MALRYNTH-CONSTITUTION-DRAFT.md`](../constitution/MALRYNTH-CONSTITUTION-DRAFT.md) §7
- **Depends on:** [ADR-0004](ADR-0004-kernel-object-model.md) (handles and rights)
- **Review trigger:** M7, when the first privileged roles actually exist and the parity gate is verified rather than asserted.

## Context

Constitution §7 stated that first-party applications receive "no capability unavailable to a
third party performing the same function." As a rule about *ordinary applications* that is
exactly right, and it is one of the commitments the project exists to keep.

As a universal rule it is false, and it was going to be discovered as false at M5–M7 rather
than now. Recovery must act on protected snapshots when the running system is untrusted.
Security containment freezes processes and revokes their authority. Update and package
authority decide what code boots next and which signatures are accepted. Firmware management
writes persistent pre-OS state. Login and session infrastructure owns credential entry. None
of these can be an ordinary capability that any application may request, because an ordinary
application holding any of them could disable the security model outright.

A constitution that states an absolute it cannot keep does not protect the commitment — it
guarantees a quiet exception later, argued under delivery pressure, with no record that the
principle ever changed. That is precisely the failure mode this document exists to prevent
(Constitution §22, "Honesty about state").

The wording was corrected across the H0.5 architecture documents in `af02298`, which left the
constitution as the last document still asserting the absolute. This ADR closes that gap and
makes the amendment procedurally valid under the constitution's own Amendment clause.

## Decision

**Constitution §7 now states ordinary-application parity, not universal privilege parity.**

1. **Parity is preserved where it matters.** Malrynth may not grant private platform advantages
   merely because software is first-party. An ordinary first-party application and an equivalent
   ordinary third-party application must be able to request the same ordinary capabilities under
   the same policy. First-party applications remain replaceable by design.

2. **Privileged system roles are admitted as a narrow, enumerated exception.** Recovery, security
   containment, update authority, package authority, firmware management, and login/session
   infrastructure may hold capabilities ordinary applications cannot, where the privilege is
   necessary to the role.

3. **Privilege is constrained.** Such privilege must be role-based, documented, narrowly scoped,
   auditable, and revocable where technically possible. It is **never** conferred by a binary
   being first-party.

4. **Roles are open where replacement is supported.** Where Malrynth intentionally supports
   replacing a privileged role, third-party software may occupy it on the same admission and
   security terms. Authority attaches to the role, not to authorship.

The operational detail — the role table, the anti-loophole rules, and how role authority is
observed — lives in
[`NATIVE-APPLICATION-MODEL.md`](../apps/NATIVE-APPLICATION-MODEL.md), not here. A constitution
states commitments; it does not specify mechanisms.

## Alternatives considered

- **Keep the absolute wording and treat every privileged role as a violation to be explained
  away.** Rejected: it makes the constitution unfalsifiable in practice and trains the project
  to read its own principles as slogans.
- **Delete §7 and rely on the architecture documents.** Rejected outright. The commitment that
  competing applications are not degraded is a founding purpose of the project, and the
  Amendment clause is explicit that a principle deleted without a record has been forgotten,
  not deleted.
- **Enumerate the privileged roles in the constitution as a closed list.** Rejected: a closed
  list in a constitution either becomes wrong or becomes an implementation document. The list
  is illustrative there and authoritative in `NATIVE-APPLICATION-MODEL.md`.
- **Define privilege by application identity ("system apps may do more").** Rejected: that is
  the privilege ladder this ADR exists to prevent. Authority attaches to a role, and a role is
  occupiable by third-party software wherever replacement is supported.

## Consequences

**What is given up.** The simplicity of an absolute. §7 can no longer be checked by asking a
single question; verifying it now requires two checks — that ordinary parity holds, and that
each privileged role holds its own authority *and no more*. M7's security gate is amended
accordingly. This is a real cost: an absolute is easier to defend than a boundary, and every
boundary invites argument about which side something falls on.

**What is protected.** The exception is enumerated, bounded and written down *before* any
privileged role exists, rather than negotiated afterwards by whoever is shipping Recovery.
"First-party" is explicitly disqualified as a reason for privilege, which is the specific abuse
the original wording was trying to prevent and which the absolute would have failed to prevent
once the first exception was quietly granted.

**Neutral.** Nothing is implemented. No privileged role exists; the earliest is Recovery at M5.
The parity gate and the per-role "and no more" check are both M7 verification work.
