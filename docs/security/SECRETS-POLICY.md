# Secrets Policy

**Status:** LOCKED.

## Rule

**No secret is ever committed to a Malrynth repository.** Not in history, not in a branch,
not "temporarily", not in a test fixture, not encrypted-but-committed.

This applies to: API keys, tokens, passwords, private keys of any kind, certificates with
private material, `.env` files, cloud credentials, and any personal data from a developer
machine.

## Why this is enforced locally

GitHub's secret scanning and push protection are **not available** for private repositories
on this account's plan (GitHub Free, personal). There is no server-side net. Prevention is
therefore entirely local, and the policy has to be treated as load-bearing rather than as a
backstop.

## Controls

1. **`.gitignore`** excludes `.env*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa*`,
   `id_ed25519*`, and `secrets.toml`. This prevents accidents, not determined mistakes.
2. **`tools/hooks/pre-commit`** runs a pattern scan over staged content and refuses the
   commit on a hit. Installed by `tools/bootstrap`.
3. **Pre-publication history scan.** Before any repository is first pushed, its entire
   history — not just the working tree — is scanned. Performed for the initial publication;
   result recorded in `docs/operations/github-ownership.md`.
4. **CI** re-runs the scan on every push.

## If a secret is committed

1. **Treat it as compromised immediately.** Rotate or revoke it first. Assume disclosure the
   moment it entered a repository, even a private one.
2. **Do not "fix" it with a follow-up commit deleting the file.** The object remains
   reachable in history and in every clone.
3. If it has **not** been pushed: rewrite local history (`git filter-repo`) before pushing.
4. If it **has** been pushed: rotate, then rewrite history and coordinate with everyone
   holding a clone. Rewriting published history is otherwise forbidden (ADR-0002); a leaked
   secret is one of the few justifications, and rotation still comes first.

## Signing keys

Malrynth production signing keys are **not created by tooling and never enter a repository**.
No signing key exists today. When one does, it will be hardware-backed with an offline root;
`docs/operations/github-ownership.md` tracks the target state.

## Development credentials

The GitHub token on this machine is held in the system keyring by `gh`, not in a dotfile. Git
is configured to use `gh auth git-credential`, so no token is written to `.git-credentials`
or a remote URL. Remotes must always be plain `https://github.com/<owner>/<repo>.git` — a
URL containing a token is a committed secret in `.git/config`.
