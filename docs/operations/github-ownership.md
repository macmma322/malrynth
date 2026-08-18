# GitHub Ownership and Repository Configuration

**Status:** LOCKED for the current account. Re-verify after any plan or ownership change.
**Verified:** 2026-08-19, empirically against the live repository.

## Ownership

| | |
|---|---|
| Owner | `macmma322` (Nikolay Nikolov Georgiev) |
| Owner type | **User** (personal account) |
| Plan | **GitHub Free** — confirmed empirically, see below |
| Organisations | none |
| Repository | `macmma322/malrynth` |
| Visibility | **private** (verified via API, not from creation output) |
| Default branch | `main` |

No Malrynth organisation exists. Per the project's authority constraints, **no organisation
was created and no billing was enabled**: creating an organisation is free but a private
repository inside a Free organisation has the same protection limitations documented below,
so it would add a migration without buying anything.

## Empirically determined plan capabilities

These were **tested against the live repository**, not inferred from documentation. Exact
responses recorded because they are the evidence for every mitigation in this document.

| Feature | Result | Evidence |
|---|---|---|
| **Rulesets** | ❌ **unavailable** | `POST /repos/.../rulesets` → **HTTP 403** — *"Upgrade to GitHub Pro or make this repository public to enable this feature."* |
| **Branch protection (legacy)** | ❌ **unavailable** | Same plan restriction; protected branches on private repositories require Pro/Team/Enterprise. |
| **Secret scanning / push protection** | ❌ **unavailable** | `PATCH /repos/...` with `security_and_analysis[secret_scanning][status]=enabled` → **HTTP 422** — *"Secret scanning is not available for this repository."* |
| **Dependabot alerts** | ✅ **enabled** | `PUT /repos/.../vulnerability-alerts` → 204; verified enabled. |
| **Dependabot security updates** | ✅ **enabled** | `PUT /repos/.../automated-security-fixes` → 204; `.enabled == true`. |
| **Actions** | ✅ available | Free-tier minutes; default spending limit zero, so overage **fails** rather than bills. |

### What this means

**`main` cannot be protected server-side.** No mechanism exists on this plan to prevent a
force-push, a branch deletion, or a direct push to `main` in a private repository. This is a
platform limitation, not a configuration oversight, and it is recorded as an accepted risk in
`docs/security/THREAT-MODEL.md` (T11 — compromised developer credentials).

It is also a concrete argument for the single-repository topology: every additional private
repository would add another *unprotectable* default branch. See ADR-0001 §12.

## Configuration actually applied

| Setting | Value | Reason |
|---|---|---|
| Visibility | private | Licensing unresolved (`docs/legal/LICENSING-STATUS.md`) |
| Default branch | `main` | ADR-0002 |
| Merge commits | **disabled** | Linear history keeps `git bisect` unambiguous |
| Squash merge | enabled (title = PR title, body = PR body) | Linear history |
| Rebase merge | enabled | Linear history |
| Auto-merge | disabled | Nothing should merge without a human while there is no required review |
| Delete branch on merge | enabled | Topic branches are short-lived (ADR-0002) |
| Wiki | disabled | Documentation lives in `docs/`, versioned with the code it describes |
| Projects | disabled | Unused surface |
| Discussions | disabled | Not justified for a solo project; revisit with a community |
| Issues | **enabled** | Engineering tracking |
| Dependabot alerts | enabled | Free and useful |
| Dependabot security updates | enabled | Free and useful |

## Compensating controls for the missing protections

Because the platform provides nothing, enforcement is local and in CI:

1. **`tools/hooks/pre-push`** — refuses non-fast-forward pushes to `main` and remote branch
   deletion; runs a secret scan before every push.
2. **`tools/hooks/pre-commit`** — secret scan on staged content plus `cargo fmt --check`.
3. **`tools/scan-secrets`** — pattern scan with a `--history` mode that walks **every blob in
   every commit**, not just the working tree.
4. **CI** re-runs the secret scan and the full verification suite on every push and PR.
5. **Hooks are versioned** via `core.hooksPath = tools/hooks`, so they arrive with a clone
   instead of living untracked in `.git/hooks`.

**These are guard rails, not security controls.** All are bypassable with `--no-verify`, and
none applies to an attacker pushing via the API with a stolen token. That gap is real,
documented, and currently unmitigated.

## Target server-side configuration

Apply **verbatim** the moment the plan or the owner changes. Recorded now so it is not
redesigned under pressure later.

```jsonc
// POST /repos/{owner}/malrynth/rulesets
{
  "name": "protect-main",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["refs/heads/main"], "exclude": [] } },
  "rules": [
    { "type": "deletion" },              // main cannot be deleted
    { "type": "non_fast_forward" },      // published history cannot be rewritten
    { "type": "required_linear_history" },
    { "type": "required_signatures" },   // ONLY once a signing key exists -- see below
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [{ "context": "fmt, lint, test, boot" }]
      }
    },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,   // ONLY once a second person exists
        "require_code_owner_review": true,
        "dismiss_stale_reviews_on_push": true,
        "required_review_thread_resolution": true
      }
    }
  ]
}
```

**Two rules must not be enabled prematurely, in this order of risk:**

- `required_signatures` — **no signing key exists on this machine** (verified: no GPG secret
  keys, no SSH keys at all). Enabling it would make every commit rejected and lock the sole
  developer out of their own repository.
- `pull_request.required_approving_review_count` — with one developer there is nobody to
  approve, so this makes `main` unwritable.

Enable each only when its precondition is genuinely met.

## Commit signing: current state and target

**Current:** unsigned. Verified: `user.signingkey`, `commit.gpgsign` and `gpg.format` are all
unset; `gpg --list-secret-keys` is empty; `~/.ssh` contains no keypair.

**Target**, in order:

1. Generate an SSH signing key (simpler than GPG and sufficient for Git):
   `ssh-keygen -t ed25519 -C "malrynth signing"`
2. Add it to GitHub as a **signing** key (distinct from an authentication key).
3. `git config --global gpg.format ssh`
   `git config --global user.signingkey ~/.ssh/id_ed25519.pub`
   `git config --global commit.gpgsign true` and `tag.gpgsign true`
4. Only then add `required_signatures` to the ruleset.

Signing was **not** configured as part of this work: generating a signing key is a credential
decision for the account owner, and a key created by tooling is a key whose provenance nobody
can vouch for.

## Migration to an organisation

1. Create the organisation on a plan that costs nothing, or with explicit approval to spend.
2. **Transfer** the repository (Settings → Transfer ownership). Transfer preserves issues,
   pull requests and history, and installs redirects from the old URL so existing clones keep
   working.
3. `git remote set-url origin https://github.com/<org>/malrynth.git`
4. Apply the ruleset above — organisation plans support rulesets on private repositories.
5. Convert `CODEOWNERS` from `@macmma322` to team handles; the file is already grouped by
   area for exactly this.
6. Enable required signatures once a key exists.

**Decisions already made that keep this cheap:** a single repository means a single transfer;
there are no submodule URLs to rewrite; and if submodules are ever added they will use
**relative** URLs, which survive an ownership change unedited (ADR-0001).

## Credential handling

The GitHub token is held in the **system keyring** by `gh`, not on disk. Git uses
`gh auth git-credential` as its credential helper, so no token is written to
`.git-credentials` or embedded in a remote URL. Token scopes observed: `gist`, `read:org`,
`repo`, `workflow`.

The remote must always be `https://github.com/macmma322/malrynth.git`. A remote URL containing
a token is a secret committed to `.git/config`.
