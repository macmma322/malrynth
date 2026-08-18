# Repository Topology Research

**Status:** LOCKED (input to [ADR-0001](../adr/ADR-0001-repository-topology.md))
**Date:** 2026-08-19
**Scope:** How the Malrynth source tree should be split across Git repositories.

This document is the research record. The binding decision lives in ADR-0001.

---

## 1. Sources consulted

Primary/official sources are marked **[P]**. Project-organisation evidence was taken
from the projects' own documentation or repositories **[E]**.

### Git mechanics
- **[P]** `git-submodule(1)`, `gitsubmodules(7)` — <https://git-scm.com/docs/git-submodule>, <https://git-scm.com/docs/gitsubmodules>
- **[P]** `git-worktree(1)` — <https://git-scm.com/docs/git-worktree>
- **[P]** `git-sparse-checkout(1)` — <https://git-scm.com/docs/git-sparse-checkout>
- **[P]** `git-clone(1)` (`--filter`, partial clone) — <https://git-scm.com/docs/git-clone>
- **[P]** `git-subtree(1)` — <https://git-scm.com/docs/git-subtree>
- **[P]** Local `git --version` → **2.53.0** (all of the above available)

### Cargo / Rust
- **[P]** Cargo Book, *Workspaces* — <https://doc.rust-lang.org/cargo/reference/workspaces.html>
- **[P]** Cargo Book, *Overriding dependencies* — <https://doc.rust-lang.org/cargo/reference/overriding-dependencies.html>
- **[P]** rustup, *Toolchain file* — <https://rust-lang.github.io/rustup/overrides.html>
- **[P]** `rustc --print target-list`, local rustup target availability (verified on host)

### GitHub platform constraints
- **[P]** *About rulesets* — <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets>
- **[P]** *About protected branches* — <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches>
- **[P]** *Push protection* — <https://docs.github.com/en/code-security/concepts/secret-security/push-protection>
- **[P]** Empirical probe of this account via `gh api` (see §12 and `docs/operations/github-ownership.md`)

### Comparable operating-system projects
- **[E]** Fuchsia, *Source code layout* — <https://fuchsia.dev/fuchsia-src/development/source_code/layout>
- **[E]** Fuchsia, *Source tree* — <https://fuchsia.dev/fuchsia-src/get-started/learn/build/source-tree>
- **[E]** Redox OS — <https://gitlab.redox-os.org/redox-os/redox>
- **[E]** seL4 — <https://github.com/seL4>
- **[E]** SerenityOS — <https://github.com/SerenityOS/serenity>
- **[E]** Haiku — <https://github.com/haiku/haiku>
- **[E]** LLVM monorepo — <https://github.com/llvm/llvm-project>

---

## 2. What comparable projects actually do

This is the single most useful body of evidence, because these projects have already
paid the cost of getting it wrong.

| Project | Model | Notes |
|---|---|---|
| **Fuchsia** | **Single first-party repo** (`fuchsia.git`) + `jiri` manifest for third-party | Kernel (`/zircon/kernel`), userspace services, drivers, and libraries all live in one tree, organised as a recursive tree of *areas*, each with `OWNERS`, docs and tests. This is the closest analogue to Malrynth: capability-based microkernel, new ABI, multi-product. |
| **LLVM** | **Monorepo** (migrated *to* it from many repos in 2019) | Explicitly moved from per-subproject repos to one repo because cross-project atomic commits were the dominant workflow. A direct precedent for "splitting too early is the expensive mistake". |
| **SerenityOS** | **Monorepo** | Kernel, libraries, userland, and applications in one tree; whole-tree refactors are routine. |
| **Haiku** | **Monorepo** (`haiku`) + separate `buildtools` | Split is along *toolchain vs OS* — a genuinely different release lifecycle, not a conceptual boundary. |
| **Redox OS** | **Superproject + many component repos** | Kernel, `relibc`, `redoxfs`, cookbook recipes are separate repos coordinated by a build orchestrator. Demonstrates the model works, but also demonstrates its cost: contributors must learn the orchestrator before they can build. |
| **seL4** | **Multi-repo** | Justified: the verified kernel has a genuinely independent release/verification lifecycle and formal-proof artifacts that must be pinned to exact kernel revisions. This is criterion (H) in its purest form. |

**Conclusion from the evidence:** the two projects most similar to Malrynth in *architecture*
(Fuchsia) and in *cross-cutting churn profile* (LLVM, SerenityOS) both use a single
first-party repository. Multi-repo appears where a component has genuinely independent
verification or release semantics (seL4) — not merely where the architecture diagram has a box.

---

## 3. Option A — Single repository (monorepo)

One Git repository containing docs, kernel, boot, ABI, services, and later products/UI/apps.

**Advantages**
- True atomic cross-component commits. A change to the kernel ABI and every caller lands as one commit and is bisectable as one commit.
- One `Cargo.lock`, one `rust-toolchain.toml`, one dependency graph, one license ledger.
- Clone-and-build is `git clone && ./tools/build`. No orchestrator, no submodule auth.
- CI is simple: one checkout, one cache, one matrix.
- Refactoring is unconstrained, which is what an unstable pre-M3 ABI actually needs.
- `git bisect` across the whole OS works without any tooling.

**Disadvantages**
- No per-component access control. Everyone who can read the repo can read everything.
- Repository grows monotonically; large binary mistakes are permanent without history rewrite.
- Cannot pin one component to an independently released version.
- CI must learn to only run affected work as the tree grows (path filters, later Bazel-style tooling).

**CI implications:** simplest possible. Single `actions/checkout`, no token plumbing.

**Developer workflow:** lowest friction. `git worktree` covers parallel branches;
`git sparse-checkout` covers "I only want `core/`" for large trees;
partial clone (`--filter=blob:none`) covers history size if it ever becomes an issue.
All three are available in Git 2.53.0 without any repository restructuring.

**Atomic change implications:** ideal. This is the model's entire point.

**Private-repo auth implications:** none beyond cloning the repo itself.

**Access control implications:** all-or-nothing. Acceptable for a solo founder; a real
constraint the day a contractor needs `apps/` but not `core/`.

**Long-term scaling:** proven to at least Fuchsia/LLVM scale, but only with investment in
build/CI tooling that Malrynth does not need for years.

---

## 4. Option B — Full multi-repository (repo per component)

`malrynth`, `malrynth-core`, `malrynth-products`, `malrynth-ui`, `malrynth-apps`,
`malrynth-sdk`, `malrynth-compat`, `malrynth-infra` as independent repositories,
coordinated only by documentation.

**Advantages**
- Hard access-control boundaries per component.
- Independent issue trackers, releases, and CI budgets.
- A catastrophic history mistake is contained to one repository.

**Disadvantages**
- **No atomic cross-component change.** An ABI change becomes an N-step choreography.
- **No single source of truth for "what is Malrynth revision X"** unless a manifest is added — which is Option E.
- `git bisect` across the OS is impossible without custom tooling.
- Eight repositories × branch config × CI config × dependency policy = eight times the platform maintenance, performed by one person.
- Rust cross-repo dependencies require either path overrides (fragile) or publishing crates (premature for an unstable ABI).

**Verdict at M0:** fails on the churn profile alone.

---

## 5. Option C — Submodule superproject

A `malrynth` superproject whose `.gitmodules` pins exact commits of component repositories.

**Advantages**
- The superproject commit *is* the answer to "which exact source state is Malrynth revision X". This is genuinely valuable and is the model's strongest property.
- Components keep independent history and can have independent access control.
- Pinning is exact and verifiable (`git submodule status`).

**Disadvantages**
- Submodules pin commits, not branches; every component change requires a second "bump the pointer" commit in the superproject. For a solo founder committing many times a day pre-M3, this roughly doubles commit count for zero architectural gain.
- Detached-HEAD submodule checkouts are a well-known source of lost work for newcomers.
- **Atomic cross-repo commits are impossible by construction.** A kernel/ABI change spans two repos and two commits; a bisect that lands between them is broken.
- Private submodules require credential plumbing in CI (`actions/checkout` with `submodules: recursive` needs a token with access to every submodule; the default `GITHUB_TOKEN` is scoped to one repository only). This is real, recurring complexity.
- URL choice (relative vs HTTPS vs SSH) becomes a migration hazard if ownership moves to an organisation later.

**CI implications:** every workflow needs a PAT or GitHub App token to fetch private
submodules; that token is a standing credential with broad read access — a security
liability that must be rotated.

**Verdict:** the right *eventual* model for components that earn it. Wrong now.

---

## 6. Option D — Subtree

`git subtree` vendors a component's history into a subdirectory of the superproject.

**Advantages**
- Consumers clone one repository; no submodule commands to learn.
- History is preserved and can be split back out.

**Disadvantages**
- Merge/split operations are non-obvious and easy to perform incorrectly.
- Provides the *illusion* of independence while doubling history storage.
- Solves a problem (consuming an externally maintained component) that Malrynth does not yet have.

**Verdict:** not applicable now. Relevant later only for **importing third-party code** we
must carry and patch (e.g. a compatibility layer), never for first-party components.

---

## 7. Option E — Manifest-based multi-repo

A manifest file (Google `repo`, Fuchsia's `jiri`, or a Malrynth-specific TOML) lists each
component repository and its pinned revision; a tool materialises the checkout.

**Advantages**
- Same exact-pinning property as submodules, without submodules' detached-HEAD ergonomics.
- Scales to hundreds of repositories, including third-party mirrors.
- Fuchsia uses exactly this for third-party code.

**Disadvantages**
- Requires building and maintaining the orchestration tool — a real, ongoing engineering cost.
- Still no atomic cross-repo commit.
- Onboarding requires the tool before anything can be built.

**Verdict:** the correct model at large scale for **third-party** dependencies. Adopting it
for first-party code today would mean writing an orchestrator for a tree with one component in it.

---

## 8. Git features that remove the usual reasons to split

Several historical arguments for splitting repositories are obsolete in Git 2.53.0:

| Concern | Modern remedy | Requires split? |
|---|---|---|
| "Clone is too big" | partial clone: `git clone --filter=blob:none` | No |
| "I only need one subdirectory" | `git sparse-checkout set core/` | No |
| "I need several branches checked out" | `git worktree add` | No |
| "CI rebuilds everything" | path filters, then a real build graph | No |
| "I need per-component access control" | *(no Git-level remedy)* | **Yes** |
| "I need independent release versions" | *(no Git-level remedy)* | **Yes** |

Only the last two are genuine, irreducible reasons to create a repository boundary. Both are
access/lifecycle concerns, not technical ones — which is exactly what the decision rule in
ADR-0001 encodes.

---

## 9. Reversibility analysis (decisive)

The question is not "which model is best at maturity" but "which mistake is cheaper to undo".

- **Unified → split** is cheap and lossless. `git subtree split --prefix=core -b core-only`
  (or `git filter-repo --subdirectory-filter core`) extracts a subdirectory into a new
  repository **with its full history**, which is then pushed to a new remote and re-added as a
  submodule. Git 2.53.0 supports this natively.
- **Split → unified** is more expensive: it requires merging unrelated histories, rewriting
  paths, reconciling divergent `Cargo.lock`/toolchain/CI, and it destroys the independent
  release identity that motivated the split. LLVM's 2019 migration is the industry's reference
  example of how much work this is.

Splitting early is therefore the **irreversible-direction** error. Starting unified costs
nothing that cannot be recovered later.

---

## 10. Application of the decision rule

Applying the rule from the project brief to each proposed component, **as of M0**:

| Component | A release | B security | C access | D community | E multi-consumer | F history harm | G license | H pinning | I stable | **Earns repo?** |
|---|---|---|---|---|---|---|---|---|---|---|
| `core` (boot/kernel/abi) | no | no | no | no | not yet | no | no | no | **no** | **No** |
| `products` | no | no | no | no | n/a | no | no | no | n/a — does not exist | **No** |
| `ui` | no | no | no | no | n/a | no | no | no | n/a — M6 | **No** |
| `apps` | no | no | no | no | n/a | no | no | no | n/a — M7 | **No** |
| `sdk` | no | no | no | no | not yet | no | no | no | ABI unstable | **No** |
| `compat` | no | no | no | no | n/a | possibly later | **possibly** | no | n/a — post-M7 | **No** |
| `infra` | no | no | no | no | no | no | no | no | no | **No** |

And the "keep together" test, which `core` fails comprehensively:

- (A) APIs still changing together — **yes**, the ABI does not exist yet.
- (B) cross-cutting refactors common — **yes**, this is the definition of M0–M3.
- (C) one commit reasonably updates both sides — **yes**, e.g. a handoff-struct change touches loader, kernel, ABI and the ADR describing it.
- (D) shares one `Cargo.lock`/toolchain/release — **yes**.
- (E) separation is merely cosmetic — **yes**, at M0 it mirrors a diagram, not a boundary.
- (F) boundary costs more Git/CI complexity than architectural value — **yes**, especially given §12.

Not one component satisfies a single split criterion today.

---

## 11. Private-submodule authentication (why this matters here specifically)

If submodules were adopted now, every CI run would need to clone private submodules. The
`GITHUB_TOKEN` issued to a workflow is scoped to the *containing* repository only, so
`actions/checkout` with `submodules: recursive` fails on private submodules unless supplied
with a PAT or GitHub App installation token. That credential:

- must be created, stored as a secret, and rotated;
- grants standing read access to every Malrynth repository;
- is a single point of compromise for the entire source tree (see `docs/security/THREAT-MODEL.md`, "compromised developer credentials").

Creating that liability to coordinate a tree that currently has one component would be a
straightforwardly bad security trade.

---

## 12. GitHub platform constraints discovered (account-specific)

The authenticated owner is a **personal account on GitHub Free**. Verified from official docs
and probed against the account:

- **Rulesets** are available on public repositories with Free, and on private repositories
  only with **Pro/Team/Enterprise**.
- **Branch protection rules** have the same availability split.
- **Secret scanning / push protection** for private repositories requires a paid plan;
  it is free only for public repositories.

Consequences that feed ADR-0001 and `docs/operations/github-ownership.md`:

1. **Server-side branch protection cannot be enabled** on private Malrynth repositories
   without spending money, which is out of scope for this task. Protection must therefore be
   enforced **client-side** (Git hooks) and **in CI**, and the desired server-side state must be
   documented for the day the plan changes or ownership moves to an organisation.
2. Every additional repository multiplies the number of *unprotectable* branches. Fewer
   repositories means a smaller unprotected surface.
3. Secret prevention cannot rely on GitHub push protection. A local pre-commit secret scan is
   mandatory, not optional (see `docs/security/SECRETS-POLICY.md`).

This is a significant, concrete argument against multi-repo *for this account specifically*, and
it is not visible from architecture diagrams alone.

---

## 13. Recommendation

**Adopt a single private repository, `malrynth`, structured so that every future split
boundary is already a real top-level directory boundary.**

Specifically:

1. Create **one** repository now. Do not create `malrynth-core`, `-products`, `-ui`, `-apps`,
   `-sdk`, `-compat`, or `-infra`.
2. The repository root plays the **superproject role** described in the brief: it owns the
   constitution, architecture, ADRs, roadmap, manifests, and the `tools/` entry points, and it
   records "this is Malrynth revision X" in `manifests/`.
3. Place first-party code under `core/` (`boot/`, `kernel/`, `abi/`), so that
   `git subtree split --prefix=core` is a *mechanical* operation the day `core` earns its own
   repository.
4. Encode explicit, testable split criteria in ADR-0001 so that the decision to split later is
   evidence-driven rather than aesthetic.
5. Revisit at **M3** (kernel objects/capabilities/IPC — the point at which the ABI is expected
   to stabilise) and at the first non-founder contributor, whichever comes first.

The single strongest reason: **at M0 the kernel ABI does not exist yet.** Repository boundaries
freeze interfaces. Freezing an interface that has not been designed is the most expensive
mistake available at this stage, and it is the one the multi-repo hypothesis would commit us to.
