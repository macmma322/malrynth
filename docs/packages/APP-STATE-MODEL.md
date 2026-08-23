# Application State Model

**Status:** PROPOSED. Target: M5.

## Partition by lifetime

```
/package     read-only, content-addressed, verified   -- removed on uninstall
/config      private, persistent, small, syncable     -- user chooses on uninstall
/data        private, persistent, potentially large   -- user chooses
/cache       disposable at ANY time, no warning       -- always removed
/temp        session-scoped                           -- always removed
/secrets     Vault handles only, never plaintext      -- removed with the app
```

User documents live **outside** the application entirely, reached through capabilities the
user granted. An app cannot scatter files across the system because it never had the authority
to write anywhere else.

## Why this specific partition

It makes several otherwise-hard problems trivial:

| Problem | Solved by |
|---|---|
| **Deterministic uninstall** | Everything the app wrote is in known locations |
| **Reclaiming disk space** | `/cache` is defined as disposable without asking |
| **Sync scope** | `/config` syncs; `/cache` never does; `/data` is a user choice |
| **Backup scope** | `/config` + `/data`; never `/cache` |
| **Migration** | Versioned `/config` and `/data` with framework migration hooks |
| **Secret hygiene** | Apps hold Vault handles, so secrets are never in app storage |

## Uninstall

```
Remove application            ✓ always
Remove cached data            ✓ always
Remove application data       ? user chooses
Keep documents you created    ✓ always kept — they were never the app's
```

**Uninstall must be deterministic and complete.** If uninstalling can leave unknown residue,
the state model has failed.

## The `/cache` contract

The system may delete `/cache` at any time, without notice, while the app is running.
Applications must treat it as a pure optimisation. Stating this as a hard contract is what
makes automatic disk reclamation safe — an app that stores something important in `/cache` has
a bug, and the contract says so up front.
