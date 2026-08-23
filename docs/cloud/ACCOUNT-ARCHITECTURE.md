# Account Architecture

**Status:** PROPOSED. Target: post-M7.

## Governing principle

> **Online is recommended because it makes Malrynth more convenient. Online is not required to
> make the computer yours.**

A local account is a **permanently supported first-class configuration** (Constitution §2, §4).
Not a degraded mode, not a setup-skip path that nags — a fully supported way to use the system
indefinitely.

## Six distinct identities

Collapsing these is how platforms end up unable to separate "this person" from "this device"
from "this company":

| Identity | Represents | Lifetime |
|---|---|---|
| **Local user** | A person on this device | Independent of everything else |
| **Malrynth Account** | Optional cloud identity | Optional, revocable |
| **Device** | This machine, its keys, its measured boot state | Device lifetime |
| **Application** | A package identity | Per package |
| **Publisher** | Who signed a package | Per publisher |
| **Organization** | An enterprise tenant | Per organisation |

A local user may have zero, one or several Malrynth Accounts. A device may be enrolled in an
organisation while its user's personal account remains outside organisational visibility —
which is what makes BYOD tractable at all.

## What an account may and may not gate

| May | May not |
|---|---|
| Sync across devices | Reaching a working desktop |
| Store entitlements and purchase history | Installing software (sideloading remains) |
| Cloud backup | Local backup |
| Device restore | Local recovery |
| Cross-device Link relay | Local Link on the same network |

**No OS feature that works offline may be moved behind an account later.** That would be a
constitutional violation, and it is the exact mechanism by which other platforms became
account-dependent one release at a time.

## Security

Authentication uses passkeys/WebAuthn where possible. Device keys are hardware-backed (TPM) and
never leave the device. Account compromise must not yield device control — the device trusts
its local credentials and its own measured state, not a cloud assertion.

Account recovery is genuinely hard and interacts with [Q11](../architecture/OPEN-QUESTIONS.md):
E2E encryption without a recovery path loses data; with one it is not truly E2E. The trade must
be explicit and user-visible, not silently chosen on the user's behalf.
