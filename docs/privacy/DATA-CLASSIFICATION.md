# Data Classification

**Status:** PROPOSED. **Not a legal privacy policy** — that requires professional legal review.
This is the engineering classification the policy would later be written against.

## Classes

| Class | Examples | Leaves device? | Encryption | Default |
|---|---|---|---|---|
| **User content** | Documents, photos, messages, code | Only via user-enabled Sync/Backup | E2E | Local only |
| **OS state** | Settings, layout, preferences | Only via Sync | E2E | Local only |
| **Credentials** | Passwords, passkeys, tokens | Only via Vault sync | E2E, hardware-backed | Local only |
| **Secrets** | Keys, certificates | **Never** | Hardware-backed | Local only |
| **Crash diagnostics** | Stack traces, minidumps | Opt-in only | TLS | **Off** |
| **Security events** | Shield detections | Local; org-visible only on managed devices | TLS | Local only |
| **Optional analytics** | Feature usage | Opt-in only | TLS | **Off** |
| **Account metadata** | Account ID, device list | Yes, if an account exists | TLS | n/a |
| **Store data** | Purchases, entitlements | Yes, if the Store is used | TLS | n/a |
| **Enterprise data** | Work-profile content, compliance | To the organisation only | TLS | Per enrolment |

## Per-category requirements

Every cloud-bound category must state: **reason · minimum data · encryption · retention ·
deletion · export · optional-or-required**. A category that cannot answer all seven does not
ship.

## Hard rules

1. **No advertising identifiers or behavioural profiles.** Structural, not a setting
   (Constitution §13).
2. **Crash reports and analytics are separately controllable and off by default**
   (Constitution §14). "Essential" is narrowly defined and documented, not decided case by case.
3. **Content is E2E encrypted in transit and at rest** when it leaves the device.
4. **Data not collected cannot leak.** Minimisation is the primary control; encryption is second.
5. **Export and deletion are product features**, not support requests.
6. **Local-first.** Processing happens on-device unless the user chose otherwise — including AI
   (Constitution §15).
