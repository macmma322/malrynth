# Update Model

**Status:** ACCEPTED as direction (Constitution §10). Target: M5.

## Two distinct mechanisms

| | System update | Application update |
|---|---|---|
| Unit | Whole OS image | Single package |
| Mechanism | **A/B slots** | Content-addressed swap |
| Reboot | Yes | No |
| Rollback | Boot the previous slot | Re-point to the previous root |
| Trust root | Platform signing root | Publisher + optional Store |

## System updates: A/B

```
System A  ACTIVE          System B  update target
```

```
download → verify repository metadata → verify blob hashes → verify provenance
   → write inactive slot → boot it → health check → mark known-good
```

Failure at any point leaves the active slot untouched. If the new slot fails to boot or fails
its health check, the boot manager returns to the previous one. **An update either fully
applies or does not apply** — there is no partially updated system.

## Repository trust (TUF-style)

Separate roles so no single key is catastrophic:

| Role | Keys | Exposure |
|---|---|---|
| **Root** | Offline, threshold (e.g. 3-of-5) | Never in CI |
| **Targets** | Restricted, online | Signs artifacts |
| **Snapshot** | Independent | Prevents mix-and-match |
| **Timestamp** | Short-lived | Freshness / freeze protection |

**No production signing key may exist before key custody is decided**
([Q6](../architecture/OPEN-QUESTIONS.md)). Creating one earlier means creating a key nobody can
vouch for.

## The rollback / anti-rollback tension

Constitution §10 requires updates to be rollbackable. Security requires resisting forced
downgrade to a known-vulnerable version ([`THREAT-MODEL.md`](../security/THREAT-MODEL.md) T13).
**These conflict**, and the resolution must be designed rather than discovered:

Likely shape — *user-initiated* rollback within a bounded window is permitted and logged;
*attacker-initiated* silent downgrade is blocked by a monotonic counter that survives factory
reset; and a security-critical update can close the rollback window early. This needs an ADR
before M5.

## Offline and recovery

Updates must work from local media, and **recovery must never require the network**
(Constitution §11). An OS that cannot repair itself without a server is not owned by its user.
