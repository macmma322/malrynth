# Product Compositions

**Status:** PROPOSED. No product exists.

Desktop, Server, Mobile and Console are **compositions of one platform**, never separate
operating systems (`docs/architecture/PRODUCT-COMPOSITION.md`). There is one kernel.

A product manifest will answer exactly these questions, and nothing else:

| Axis | Question |
|---|---|
| `shell` | Which UI shell and session model, or none |
| `services` | Which system services start, in what order |
| `drivers` | Which driver profile |
| `policy` | Security defaults: updates, sideloading, network exposure |
| `packages` | Default package set |
| `channel` | Update channel and cadence |
| `performance` | Which budget profile applies |
| `hardware` | Which platform/board definitions are in scope |

Manifests are **not** written yet because there are no services, packages, policies or
drivers to compose. A manifest referencing nothing would describe a roadmap while looking
like a build input — precisely the kind of scaffolding ADR-0001 exists to prevent.

Planned: `desktop` and `server` first (M7); `mobile` and `console` begin as documents.
