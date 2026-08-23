# Organizations Architecture

**Status:** PROPOSED. Target: far post-M7. [Q12](../architecture/OPEN-QUESTIONS.md) is unsolved.

## The critical constraint

> **Company policy authority is scoped to company-managed state. On BYOD, personal data
> remains outside organisational visibility unless explicitly shared.**

This must be **technically enforced**, not merely promised. The goal is a design in which
company policy *cannot name* personal data — not one in which it could but is asked not to.
Achieving that is [Q12](../architecture/OPEN-QUESTIONS.md), and it is genuinely unsolved.

## Work profiles

```
Device
├── Personal profile      user's identity, apps, data      ← invisible to the organisation
└── Work profile          org identity, managed apps, data ← managed, wipeable
```

Separate storage, separate capabilities, separate keys. Remote wipe removes the **work
profile** and nothing else — a company must be able to protect its data without holding
authority over a person's photographs.

## Scope

| Area | Contents |
|---|---|
| Identity | Org membership, SSO, OIDC, SAML, SCIM provisioning, LDAP/AD integration |
| Authorisation | RBAC, teams, groups, guests |
| Collaboration | Channels, chat, meetings, shared files, calendar |
| Device management | MDM enrolment, policy, compliance, fleet inventory |
| Security | EDR via Shield, certificate distribution, VPN configuration |
| Distribution | Company Store, private packages, mandated applications |

## Enrolment must be consensual and legible

Enrolling a personal device shows **exactly** what the organisation can and cannot see and do,
before enrolment completes. Un-enrolment is always available to the device owner on BYOD, and
removes work data rather than personal data.

Corporate-owned devices may be more comprehensively managed — but the difference between
"corporate-owned" and "BYOD" is a technical boundary, not a policy checkbox.

## Anti-goal

Organisation features must never become a backdoor into the consumer platform. A capability
that exists "for enterprise management" and can reach personal data is a vulnerability
regardless of the policy that governs it.
