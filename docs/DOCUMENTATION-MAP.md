# Documentation Map

**Status:** ACCEPTED. Documentation is a platform subsystem, not a by-product.

## Maturity scale

**SKELETON** (headings only) · **DRAFT** (substantive, incomplete) · **USABLE** (a competent
reader can act on it) · **AUTHORITATIVE** (reviewed, versioned, maintained)

## Corpora

| Corpus | Location | Owner | Maturity |
|---|---|---|---|
| **Constitution** | `docs/constitution/` | Founder | DRAFT |
| **Product vision** | `docs/research/FOUNDER-VISION-SOURCE-MAP.md` | Founder | USABLE |
| **Architecture** | `docs/architecture/` | Architecture | USABLE |
| **ADRs** | `docs/adr/` | Architecture | AUTHORITATIVE |
| **Kernel** | `docs/architecture/KERNEL-BOUNDARY.md`, in-source | Kernel | DRAFT |
| **ABI / syscalls / IPC** | `docs/runtime/ABI-STRATEGY.md`, ADR-0004 | Kernel | DRAFT |
| **Capability model** | `docs/architecture/`, `docs/apps/` | Security | DRAFT |
| **DDK** | `docs/sdk/DDK-ARCHITECTURE.md` | Drivers | SKELETON |
| **SDK / API reference** | `docs/sdk/` | Platform | SKELETON |
| **Package spec** | `docs/packages/` | Platform | DRAFT |
| **Filesystem spec** | `docs/storage/` | Storage | DRAFT |
| **UI / design system** | `docs/ui/` | UI | DRAFT |
| **Security architecture** | `docs/security/` | Security | USABLE |
| **Threat models** | `docs/security/THREAT-MODEL.md` | Security | USABLE |
| **Performance** | `docs/performance/` | Performance | USABLE |
| **Compatibility** | `docs/compatibility/` | Compatibility | DRAFT |
| **Hardware certification** | — | Hardware | **MISSING** |
| **User guide** | — | Docs | **MISSING** (needs a product) |
| **Developer guide** | `docs/sdk/` | Docs | SKELETON |
| **Administrator guide** | `docs/enterprise/` | Enterprise | SKELETON |
| **Recovery guide** | — | Docs | **MISSING** |
| **Privacy** | `docs/privacy/` | Privacy | DRAFT |
| **Store rules** | `docs/store/` | Store | SKELETON |
| **Support lifecycle** | — | Product | **MISSING** |
| **Release policy** | `docs/adr/ADR-0002-*` | Release | USABLE |
| **Licensing** | `docs/legal/` | Legal | DRAFT (unresolved) |
| **Third-party notices** | `THIRD_PARTY.md` | Legal | USABLE |
| **Operations** | `docs/operations/` | Engineering | USABLE |
| **Development environment** | `docs/operations/DEVELOPMENT-ENVIRONMENT.md` | Engineering | USABLE |
| **Developer tooling (host)** | `docs/operations/DEVELOPMENT-ENVIRONMENT.md`, `tools/`, `tools/windows/` | Engineering | USABLE |
| **Roadmap** | `docs/roadmap/` | Product | USABLE |
| **Research** | `docs/research/` | Architecture | USABLE |

Owners are **roles, not people** — there is currently one person. The roles exist so
responsibility is assignable when there are more.

## Rules

1. **Every document declares a status** — LOCKED / ACCEPTED / PROPOSED / EXPERIMENTAL /
   DEFERRED / UNSOLVED.
2. **No present tense for unbuilt systems.**
3. **API documentation is versioned with the ABI.** A developer targeting Malrynth 4 must not
   read Malrynth 7 behaviour.
4. **Documentation ships offline.** Documentation that requires the Internet fails exactly when
   a user needs it most — during recovery.
5. **An undocumented interface is unfinished**, not "self-documenting".
6. **Production developer tooling is documented under `docs/operations/`**, never only under
   `docs/research/`. Research records how a decision was reached; operations records how to use
   what it produced. A developer must not have to read a research paper to find the build
   command.

## Known gaps

Hardware certification, user guide, recovery guide and support lifecycle are **missing and
acknowledged**. Three of the four require a product to document; the recovery guide should
arrive with M5's recovery environment.
