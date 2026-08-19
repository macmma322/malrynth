# ADR-0001 — Repository Topology

- **Status:** LOCKED (accepted 2026-08-19)
- **Deciders:** Nikolay Nikolov Georgiev (founder)
- **Supersedes:** none
- **Research:** [`docs/research/repository-topology-research.md`](../research/repository-topology-research.md)
- **Review triggers:** completion of M3, or first non-founder contributor, whichever is first.

---

## Context

Malrynth is an independent operating-system family with its own kernel: firmware → Malrynth
Boot → Malrynth kernel → system services → runtime → applications. Linux is a development
host, a compatibility target and a source of lessons — never the production host kernel.

The project is at **M0**: nothing exists but the intent to boot a kernel and print to serial.
The eventual system spans a kernel, drivers, services, a compositor, an SDK, compatibility
layers, four product variants and a first-party application suite.

The initial hypothesis in the founding brief was a "federated monorepo": seven or eight
repositories (`malrynth`, `-core`, `-products`, `-ui`, `-apps`, `-sdk`, `-compat`, `-infra`)
coordinated by a superproject using Git submodules. The brief explicitly asked for this
hypothesis to be challenged.

Three facts dominate the decision:

1. **The kernel ABI does not exist yet.** Repository boundaries freeze interfaces. Every
   boundary drawn now would freeze an interface that has not been designed.
2. **Splitting later is cheap and lossless; merging later is expensive.**
   `git subtree split --prefix=<dir>` extracts a subdirectory into a standalone repository with
   full history. Merging independent repositories back together destroys release identity and
   requires history rewriting — LLVM's 2019 monorepo migration is the reference example of the cost.
3. **This GitHub account is a personal account on GitHub Free.** Private repositories on that
   plan support **neither rulesets nor branch protection**, and secret-scanning push protection
   is unavailable. Every additional private repository therefore adds an *unprotectable* default
   branch, and (with submodules) requires a broad standing PAT in CI to clone privately.

The closest architectural analogue, Fuchsia — also a capability-based microkernel with a new
ABI and multiple products — keeps all first-party code in a single `fuchsia.git` repository.
LLVM and SerenityOS, whose cross-cutting churn profile matches Malrynth's, are monorepos.
Multi-repo appears where a component has genuinely independent verification or release
semantics (seL4), which no Malrynth component has today.

---

## Decision

**Malrynth uses a single private Git repository, `malrynth`, for all first-party source and
documentation, structured so that every anticipated future split boundary is already a real
top-level directory boundary.**

Concretely:

- Exactly **one** repository is created: `macmma322/malrynth` (private).
- The repository root performs the **superproject role**: constitution, architecture, ADRs,
  research, roadmap, security, performance, manifests, and the `tools/` entry points.
- First-party system code lives under `core/` (`core/boot/`, `core/kernel/`, `core/abi/`), so
  that `git subtree split --prefix=core` is a mechanical operation when `core` earns separation.
- **No** `malrynth-core`, `malrynth-products`, `malrynth-ui`, `malrynth-apps`, `malrynth-sdk`,
  `malrynth-compat` or `malrynth-infra` repository is created.
- **Git submodules are not used at this time.** `.gitmodules` does not exist.
- A Cargo workspace at the root shares one `Cargo.lock` and one `rust-toolchain.toml`.

### Applying the project's own decision rule

A component earns a repository when it has an independent release lifecycle (A), an independent
security boundary (B), restricted access (C), an independent contributor community (D),
multiple unrelated consumers (E), history that would damage the main repository (F), a
different license/governance model (G), a need to pin to an exact independent version (H), or
enough stability that cross-repo atomic changes are rare (I).

**No proposed component satisfies any of A–I today.** Conversely, `core` satisfies every
"keep together" criterion: its APIs change together with the docs that specify them,
cross-cutting refactors are the defining activity of M0–M3, single commits legitimately touch
loader + kernel + ABI + ADR, it shares one lockfile and toolchain, and the separation would be
cosmetic while adding real Git and CI complexity.

---

## Alternatives considered

| Option | Verdict | Reason |
|---|---|---|
| **A. Single repository** | **Accepted** | Atomic cross-component change; matches Fuchsia/LLVM/SerenityOS; reversible into any other model. |
| **B. Full multi-repo (8 repos)** | Rejected | No atomic change, no single revision identity, 8× platform maintenance for one person, 8 unprotectable branches on GitHub Free. |
| **C. Submodule superproject** | Rejected *for now* | Correct eventual model for components that earn it. Today: doubles commit count, breaks atomicity and bisect, and requires a broad standing PAT for private submodule CI checkout. |
| **D. Subtree** | Rejected | Solves consumption of externally maintained code, which Malrynth does not yet have. Reserved for future third-party imports. |
| **E. Manifest-based multi-repo (`repo`/`jiri` style)** | Rejected *for first-party* | Requires building an orchestrator for a tree with one component. Correct future model for **third-party** mirrors. |

Modern Git removes the traditional pressure to split: partial clone (`--filter=blob:none`)
addresses clone size, `git sparse-checkout` addresses partial working trees, and `git worktree`
addresses parallel branches — all available in the installed Git 2.53.0. The only concerns with
no Git-level remedy are per-component **access control** and **independent release versioning**,
which is precisely what criteria A–I encode.

---

## Why not one repository per application

The first-party application suite (Files, Settings, Photos, Mail, Browser, Studio, …) will share
the Malrynth UI toolkit, runtime APIs, capability definitions, media framework, accessibility
primitives, localisation, packaging, CI and test infrastructure.

A repository per application would mean that a single change to a shared toolkit API requires a
coordinated release across dozens of repositories, and that no commit can atomically update the
toolkit and its consumers. The applications have no independent security boundary, no separate
contributor community, and no independent release lifecycle — they ship as part of a product
composition.

Applications will therefore live in **one application workspace**, and only when they exist.
They do not exist now, and no directories are created for them. The intended structure is
recorded in [`docs/apps/APPLICATION-MAP.md`](../apps/APPLICATION-MAP.md) so the roadmap is expressed
without generating scaffolding.

An individual application earns its own repository only if it develops a genuinely independent
release cadence and contributor community — the plausible first candidates being **Browser**
(vendored engine, enormous history, distinct license obligations → criteria F and G) and
**Studio**.

---

## Why not Git submodules (yet)

Submodules have one genuinely valuable property: the superproject commit *is* the exact answer
to "which source state is Malrynth revision X". That property is real and Malrynth will need it.

It is not needed yet, and today it costs:

- **Loss of atomicity.** A handoff-ABI change spans loader, kernel and ABI. In one repository
  that is one commit and one bisect step. Across submodules it is two commits in two
  repositories with a broken state in between.
- **Double commits.** Every component change requires a superproject pointer bump.
- **A standing credential.** A workflow's `GITHUB_TOKEN` is scoped to its own repository, so
  private submodule checkout requires a PAT or GitHub App token with read access to *every*
  Malrynth repository — a single point of compromise for the whole source tree.
- **Detached-HEAD ergonomics** that reliably cost newcomers work.

The same exact-pinning guarantee is provided today, at zero cost, by the fact that a single
commit SHA in one repository already identifies the entire source state.

**When submodules are adopted**, the URL form will be **relative** (`../malrynth-core.git`).
Relative URLs inherit the superproject's remote, so the same `.gitmodules` works over HTTPS and
SSH and survives a move from `macmma322/` to an organisation without rewriting the file — which
directly serves the migration strategy below.

---

## Superproject responsibilities (the repository root)

The root is not a code dump. It owns:

- `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `GOVERNANCE.md`, `THIRD_PARTY_POLICY.md`, `THIRD_PARTY.md`
- `docs/` — `constitution/`, `architecture/`, `adr/`, `research/`, `roadmap/`, `security/`, `performance/`, `compatibility/`, `specs/`, `operations/`, `legal/`
- `manifests/` — `workspace/` (component inventory), `products/` (product compositions), `releases/` (revision records)
- `tools/` — `bootstrap`, `doctor`, `build`, `test`, `run-qemu`, `status`
- `.github/` — `CODEOWNERS`, issue/PR templates, workflows
- Workspace-level `Cargo.toml`, `rust-toolchain.toml`, `.gitattributes`, `.gitignore`

Its defining job is unchanged from the brief: **answer "this exact source state is Malrynth
revision X"**. Today it answers with a commit SHA. If components are later extracted, it answers
with a commit SHA plus pinned submodule commits, and `manifests/` continues to record it in a
human-readable, diffable form.

## Component responsibilities (`core/`)

`core/` owns the boot path, the kernel, the kernel ABI, and later the low-level libraries,
system services, driver framework and platform code. It must remain buildable and testable
through the root `tools/` entry points, and must not reach outside itself for anything except
the workspace toolchain — this discipline is what keeps a future extraction mechanical.

---

## Atomic-change strategy

While unified: **all cross-component changes are single commits.** This is the model's primary
benefit and should be used deliberately — an ABI change and its consumers land together, and
`git bisect` is meaningful across the entire operating system.

If and when a component is extracted, the following expand/migrate/contract policy applies,
because atomic cross-repository commits become impossible:

1. Add the new API in the provider, backward-compatible.
2. Release and pin the provider.
3. Migrate consumers to the new API.
4. Update the superproject pin.
5. Remove the old API after a stated compatibility window.

**A high rate of would-be cross-repository changes is evidence the boundary was drawn too
early, and is grounds for merging the component back** (see "Future merge criteria").

---

## Versioning strategy

- The repository is the unit of revision; a commit SHA identifies the whole source state.
- Human-readable revisions are annotated tags: `v0.0.1-m0`, using `<major>.<minor>.<patch>-<milestone>`.
- Milestone completion is tagged; tags are immutable and never moved.
- Crate versions inside the workspace stay at `0.0.x` and are **not** published to crates.io.
  Malrynth crates are not general-purpose libraries and publishing would imply a stability
  guarantee that does not exist.
- Tag signing is deferred until a signing key exists (see ADR-0002 and `docs/operations/github-ownership.md`).

## Submodule update policy

Not applicable while unified. Recorded now so it is not invented under pressure later:

- The superproject pins **exact commits**, never floating branch heads.
- A pointer bump is its own commit, message `deps: bump <component> to <short-sha> (<summary>)`.
- CI verifies `git submodule status` reports no `+`/`-` prefixes (no drift, all initialised).
- **A component commit must be pushed before the superproject references it.** A superproject
  commit referencing an unpushed component commit produces a repository that cannot be cloned.

---

## Clone and bootstrap strategy

```
git clone https://github.com/macmma322/malrynth.git
cd malrynth
./tools/doctor      # inspect-only: report host, toolchain, QEMU, OVMF, targets
./tools/build       # build loader + kernel + bootable ESP image
./tools/test        # fmt, clippy, unit tests, QEMU boot smoke test
```

No submodule initialisation and no orchestrator are required — a deliberate property. The
commands are written so that adding `--recurse-submodules` later changes only `tools/bootstrap`.

For large-tree scenarios in the future, without restructuring:
`git clone --filter=blob:none` (partial clone) and `git sparse-checkout set core/`.

---

## CI strategy

- One workflow, one checkout, no cross-repository token.
- Stages: `fmt` → `clippy` → host unit tests → build loader/kernel → **QEMU boot smoke test
  asserting the exact marker `MALRYNTH_M0_BOOT_OK`** with a hard timeout and deterministic teardown.
- CI must never pass merely because QEMU exited; the marker must be present and no panic/fault
  marker may appear.
- Everything CI does must be reproducible locally via `tools/`. No undocumented CI-only magic.
- Actions on private repositories consume the account's free minutes quota. The default spending
  limit is £0/$0, so overage cannot silently incur cost; if the quota is exhausted, workflows
  fail rather than bill. `tools/test` is the authoritative local equivalent and is the fallback.
- Third-party actions are pinned; see `docs/security/SUPPLY-CHAIN.md`.

---

## Future split criteria

`core/` (or any other directory) is extracted into its own repository when **any two** of the
following are demonstrably true — measured, not asserted:

1. **ABI stability.** The kernel ABI has been stable for one full milestone, and
   cross-directory atomic commits have fallen below ~10% of commits touching that directory.
2. **Access boundary.** A person needs write access to one area but must not have it to another
   (for example a contractor on `apps/`, or restricted access to security-sensitive code).
3. **Independent release.** A component ships on its own cadence to consumers that do not
   move in lockstep with the OS revision — most plausibly `sdk/` once third-party developers exist.
4. **History harm.** A directory must carry large binary artifacts or vendored third-party
   history that would materially degrade clone time for everyone else (most plausibly a browser
   engine).
5. **Divergent licensing/governance.** A component must ship under different license terms or
   governance from the rest of the tree — see `docs/legal/LICENSING-STATUS.md`.
6. **CI cost.** A directory's CI needs isolation because its runtime or budget starves the rest.

**Extraction procedure (must preserve history):**

```
git subtree split --prefix=core -b extract/core     # or: git filter-repo --subdirectory-filter core
gh repo create macmma322/malrynth-core --private
git push malrynth-core extract/core:main
git rm -r core && git commit -m "refactor: extract core into malrynth-core"
git submodule add ../malrynth-core.git core          # relative URL, see above
```

The mandatory post-conditions are: component commits pushed **before** the superproject
references them, `git clone --recurse-submodules` verified from a clean directory, and
`./tools/build` verified from that fresh clone.

## Future merge criteria

A previously split component is merged back when:

1. More than ~25% of changes to it require a coordinated change in another repository within
   the same week (the boundary is not real);
2. Its independent release cadence has not been exercised for two consecutive milestones;
3. The access-control justification disappears (the contractor leaves, the restriction lifts);
4. Submodule pointer-bump commits outnumber substantive commits in the superproject.

Splitting is explicitly **not** treated as irreversible, and merging back is **not** treated as
an admission of failure. It is the decision rule working correctly.

---

## Access-control implications

- A single repository is all-or-nothing: anyone with read access reads the entire OS source.
  Acceptable while the project is a solo effort; it is the criterion most likely to force the
  first split.
- On GitHub Free, private repositories support neither rulesets nor branch protection, so
  `main` **cannot** be server-side protected today. Mitigations, in force from the first commit:
  - a local `pre-push` hook rejecting direct pushes to `main` and non-fast-forward pushes;
  - a local `pre-commit` hook running a secret scan and `cargo fmt --check`;
  - CI as the merge gate;
  - the desired server-side ruleset recorded in `docs/operations/github-ownership.md` so it can
    be applied verbatim the moment the plan or ownership changes.
- `.github/CODEOWNERS` is created now with a future-compatible layout. It is advisory until a
  plan supporting protected branches with required review exists.

---

## Migration strategy: personal account → organisation

Recorded now because the cost of this migration is decided by choices made today.

1. Create the organisation (only on a plan that costs nothing, or with explicit approval to spend).
2. **Transfer** the repository (`Settings → Transfer ownership`). Transfer preserves issues, PRs,
   stars, and — critically — installs redirects from the old URL, so existing clones keep working.
3. Update remotes: `git remote set-url origin https://github.com/<org>/malrynth.git`.
4. Apply the ruleset recorded in `docs/operations/github-ownership.md` (organisation plans
   support rulesets on private repositories).
5. Convert `CODEOWNERS` entries from `@macmma322` to organisation teams.
6. Enable required signed commits once a signing key exists (ADR-0002).

**Choices made today that keep this cheap:** a single repository means a single transfer; no
submodule URLs need rewriting; and when submodules are eventually added they will use
**relative** URLs, which survive the move without edits.

---

## Consequences

**Positive**
- Atomic cross-component commits and meaningful `git bisect` across the whole OS during the
  period of maximum architectural churn.
- One clone, one toolchain, one lockfile, one CI, one license ledger.
- One unprotectable branch instead of eight, given the platform constraints.
- No standing broad-scope PAT is required anywhere.

**Negative**
- No per-component access control until a split happens.
- No independent component versioning until a split happens.
- The repository will eventually need path-filtered CI and possibly a real build graph. This is
  a known, deferred cost with a known remedy.

**Neutral**
- The directory layout intentionally mirrors the eventual repository layout, so the future
  boundary is already visible in the tree and extraction is mechanical.
