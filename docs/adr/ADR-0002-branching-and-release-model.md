# ADR-0002 — Branching and Release Model

- **Status:** LOCKED (accepted 2026-08-19)
- **Deciders:** Nikolay Nikolov Georgiev (founder)
- **Depends on:** [ADR-0001](ADR-0001-repository-topology.md)
- **Review triggers:** second regular contributor, or the first external release.

## Context

Malrynth needs a branching model that protects production history, allows genuinely
dangerous kernel experimentation, supports bisectable history, and does not collapse when
the team grows from one to several people.

Two constraints are specific to this project:

1. **`main` cannot be protected server-side.** The repository is private on a personal
   GitHub Free account, where neither rulesets nor branch protection apply to private
   repositories. Any model that *assumes* the platform will reject a bad push is wrong here.
2. **Kernel work fails hard and often.** A branch that does not boot is normal during M1–M3.
   Such work must never be mistaken for the mainline.

## Decision

**Adopt the simplest model that satisfies the constraints: a protected-by-policy `main`,
short-lived topic branches, explicitly-labelled long-lived research branches, and annotated
version tags.** This is Option A from the brief, with one addition: research branches are
first-class and named so they can never be confused with work intended for `main`.

### Branches

| Pattern | Lifetime | Purpose | Merges to `main`? |
|---|---|---|---|
| `main` | permanent | The only branch that is always expected to build and boot. | — |
| `feature/<topic>` | days | New functionality. | Yes, when green |
| `fix/<topic>` | hours–days | Bug fixes. | Yes, when green |
| `research/<topic>` | weeks–months | Spikes, experiments, throwaway kernels. **Not expected to build.** | Only after being rewritten as `feature/*` |
| `release/<version>` | short | Stabilisation, only if a release ever needs divergence from `main`. | Yes |

**`develop` is deliberately rejected.** A long-lived integration branch exists to batch
work for a scheduled release. Malrynth has no release schedule and one developer, so
`develop` would be a second name for `main` that must be kept in sync by hand — pure cost.
It can be introduced later if a stabilisation window ever genuinely needs to run in
parallel with mainline work; that is what `release/*` is reserved for.

### Rules for `main`

1. **Always buildable and bootable.** `tools/test` must pass on every commit on `main`.
2. **Linear history.** Merges use rebase or squash; no merge commits. This keeps
   `git bisect` unambiguous, which matters more for a kernel than preserving branch shape.
3. **No force-push, ever.** Published history is immutable.
4. **No direct commits once a second contributor exists.** While solo, direct commits to
   `main` are permitted *provided* `tools/test` passed first — the pre-push hook enforces
   this, since GitHub cannot.

### Enforcement, given the platform constraint

Because the platform provides nothing, enforcement is local and in CI:

- **`tools/hooks/pre-push`** rejects force-pushes to `main` and pushes whose tip has not
  been verified. Installed by `tools/bootstrap`; documented in `CONTRIBUTING.md`.
- **CI** runs the same `tools/test` on every push and pull request.
- **The desired server-side ruleset** is recorded verbatim in
  `docs/operations/github-ownership.md` so it can be applied the moment the account plan or
  the repository owner changes.

A local hook is bypassable with `--no-verify`. That is acknowledged: it is a guard rail
against mistakes, not a security control, and it is the strongest mechanism available.

### Releases and tags

- Annotated tags only: `git tag -a v0.0.1-m0 -m "..."`. Lightweight tags carry no author,
  date, or message and are unsuitable as release records.
- Scheme: `v<major>.<minor>.<patch>-<milestone>`, e.g. `v0.0.1-m0`.
- Pre-1.0 carries **no** compatibility promise. `0.x` means the ABI may change at any time,
  which is the honest description of everything before M3.
- Tags are immutable and never moved. A wrong tag is superseded by a new one.
- **Tag signing is deferred.** No signing key exists on this machine (verified: no GPG
  secret keys, no SSH keys). Requiring signatures now would lock the sole developer out of
  their own release process. The target state and the migration to it are recorded in
  `docs/operations/github-ownership.md`.

### Commit messages

`<type>: <imperative summary>` with types `docs`, `build`, `kernel`, `boot`, `abi`, `ci`,
`test`, `fix`, `refactor`, `chore`. The body explains *why*. This is Conventional-Commits-
shaped but deliberately not tool-enforced: automated changelog generation is not worth a
commit-lint dependency at this stage.

## Consequences

**Positive:** minimal ceremony for a solo founder; bisectable linear history; research work
cannot be confused with mainline; the model scales to a team by turning existing policy into
enforced rules rather than by restructuring.

**Negative:** `main` protection is advisory until the plan changes; a determined mistake can
still reach `main`. Linear history discards branch topology, which some find informative.

**Neutral:** the model is close enough to GitHub Flow that new contributors need no training.
