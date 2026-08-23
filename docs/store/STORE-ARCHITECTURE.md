# Store Architecture

**Status:** PROPOSED. Target: M7+.

## Position

> **The Store is optional. Sideloading and third-party stores are legitimate**
> (Constitution §5–6).

The Store is a *trusted distribution channel*, not a gate. Malrynth must remain fully usable
for someone who never opens it.

## Responsibilities

| Area | Store provides |
|---|---|
| Discovery | Search, categories, curation |
| Identity | Verified publisher identity |
| Integrity | Countersignature over the publisher's signature |
| Analysis | Automated malware and capability analysis before listing |
| Transparency | **Capability display before install** |
| Reviews | User feedback |
| Entitlements | Purchases, licences, DLC |
| Distribution | Update delivery over the standard package mechanism |

## Capability transparency

The Store's most valuable security contribution is not scanning — it is making the manifest
legible **before** installation:

```
Photo Editor 2.4
  Required:  display
  Optional:  network · camera · a folder you choose
  Never:     USB devices · screen capture      ← publisher self-denial, system-enforced
```

A capability change between versions is highlighted at update time. Silently widening
capabilities in an update is a supply-chain attack, and it should be as visible as a price
change.

## Alternative stores and sideloading

Third-party stores use the **same package format, the same signature verification and the same
capability model**. They are not second-class: no private API, no artificial friction beyond
what security requires.

Installing packages requires the **package authority** role
([`NATIVE-APPLICATION-MODEL.md`](../apps/NATIVE-APPLICATION-MODEL.md)). That role is role-based,
not identity-based: a third-party store can hold it on exactly the same terms as the first-party
store, and holding it is explicit, narrow and auditable rather than ambient. Parity here means
**equal access to the role**, not that package installation is an ordinary capability.

Sideloading may require an explicit informed action. It may not be impossible.

## Economics

Recorded, not designed here: a low transparent transaction fee, with the durable rule that
**recurring infrastructure may justify recurring pricing, but local computation is never
artificially disabled to manufacture recurring revenue.**
