# Application Capability and Portal Model

**Status:** PROPOSED. Target: M7 (needs M3 capabilities and M6 UI).

## The gap this closes

ADR-0004 defines kernel handles and rights. Users do not think in handles — they think "let
this app open this photo". The **portal** layer is what turns a human decision into a
capability, and it is where most desktop security models fail.

## Lessons taken from prior art

| System | Lesson taken | Lesson rejected |
|---|---|---|
| **Fuchsia** | Explicit capability routing through a component manager | — |
| **Flatpak portals** | User-mediated grants via a trusted picker; the app never sees a path it did not receive | Underlying filesystem is still ambient beneath the sandbox |
| **Android** | Familiar runtime permission UX; per-permission revocation | Coarse groups; prompt fatigue trains users to accept |
| **macOS sandbox** | Powerbox pattern: the file picker *is* the grant | Entitlements are vendor-gated |
| **Windows AppContainer** | Capability SIDs on a legacy substrate | Retrofitted onto ambient authority, so it leaks |

The consistent failure mode: **a sandbox layered over an ambient-authority OS leaks.**
Malrynth's advantage is that there is no ambient authority underneath to leak.

## Grant kinds

| Kind | Lifetime | Example | User sees |
|---|---|---|---|
| **Manifest-declared** | install → uninstall | "this app uses the network" | At install, and in Settings |
| **Runtime grant** | until revoked | camera, microphone | Prompt + persistent indicator |
| **One-shot** | single use | "share this file once" | Implicit in the action |
| **User-picked handle** | until closed, optionally persisted | opening a document | **No prompt** — picking *is* consenting |
| **Directory capability** | persisted, revocable | "this app manages my Projects folder" | Explicit, listed in Settings |
| **Policy grant** | while policy applies | enterprise-managed | Admin-visible |

## The portal pattern

```
App: "I need a file to open"
      │
      ▼
Component Manager ──> File Picker (system-trusted, separate process)
                            │  user chooses photo.jpg
                            ▼
                      VFS creates a handle for that file
                            │
                            ▼
App receives a handle — and still cannot see anything else
```

**The picker is the grant.** No prompt is needed because the user's act of choosing *is* the
consent. This produces less UI friction *and* better security than a permission dialog — the
rare case where those align, which is why it is the primary pattern.

## Design rules

1. **Least authority by default.** A capability not requested is not held.
2. **Prefer picking over prompting.** Prompts train users to click Allow.
3. **Attenuation only** — an app cannot upgrade a read handle to write.
4. **Revocation must actually work.** A revoked capability stops working immediately. This
   requires broker-mediated handles for revocable resources rather than raw kernel handles,
   which is a real design cost, accepted deliberately.
5. **Delegation is explicit.** Passing a capability to a helper process is visible.
6. **Indicators for sensing.** Camera, microphone and screen capture always show a system
   indicator the app cannot suppress.
7. **No capability laundering.** A framework or compatibility layer must not obtain authority
   on an app's behalf that the app could not obtain itself.

## Capability vocabulary (illustrative, not frozen)

```
malrynth.storage.file.read          one user-picked file
malrynth.storage.directory.write    a chosen directory tree
malrynth.net.client                 outbound connections
malrynth.net.lan                    local network — separate, because it is far more sensitive
malrynth.net.listen                 inbound
malrynth.device.camera
malrynth.device.microphone
malrynth.device.usb.<class>
malrynth.ui.notifications
malrynth.ui.capture.screen          screen capture — never implicit
malrynth.media.playback.background
```

Hierarchical so policy can express prefixes (`malrynth.device.*`), per
[`naming.md`](../specs/naming.md).

## Enterprise interaction

Policy may *restrict* but never silently *expand* beyond what the user could grant, and
policy-driven grants are visible to the user. On BYOD, company policy is scoped to
company-managed state — see [`ORGANIZATIONS-ARCHITECTURE.md`](../enterprise/ORGANIZATIONS-ARCHITECTURE.md)
and [Q12](../architecture/OPEN-QUESTIONS.md), which is unsolved.

## Unsolved

- **Revocation cost** ([Q](../architecture/OPEN-QUESTIONS.md)) — broker mediation on every access has a performance price.
- **Comprehensibility** — showing a non-expert what an app can actually do, without lying by simplification.
- **Persisted grant hygiene** — grants accumulate; expiry or review is needed without nagging.
