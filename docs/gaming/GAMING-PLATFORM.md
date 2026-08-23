# Gaming Platform

**Status:** PROPOSED. Target: post-M7.

## Two categories, kept separate

The most useful thing this document does is separate what is **technically solvable by us**
from what **requires someone else's cooperation** — because conflating them produces promises
that cannot be kept.

### Technically solvable

| Area | Requirement |
|---|---|
| Vulkan | Conformant implementation; CTS in the test farm |
| D3D translation | Reuse DXVK / vkd3d-proton |
| Scheduler | Low, predictable latency; deadline reservations by capability |
| Input latency | Direct path from HID to focused surface; measured input-to-photon |
| Audio latency | Stable 128-frame @ 48 kHz under load |
| Frame pacing | Compositor cooperation; fullscreen direct path with no material FPS cost |
| VRR / HDR | Display service and compositor support |
| Shader caches | Persistent, per-driver-version, shared across users where safe |
| Controllers | HID + vendor protocols; hot-plug; remapping |
| Haptics | Controller feedback API |
| Capture / overlays | Compositor capture capability; overlay as a compositor feature, **not code injection** |

**Overlays are a platform capability, not injection.** On other platforms overlays hook into
game processes, which is both fragile and a security problem. Malrynth's compositor can
composite an overlay without the game's cooperation or compromise.

### Requires vendor cooperation

| Area | Reality |
|---|---|
| **GPU drivers** | The dominant risk ([Q3](../architecture/OPEN-QUESTIONS.md)) |
| **Kernel anti-cheat** | Vanguard, EAC, BattlEye need vendor support and kernel access Malrynth deliberately does not offer. **Not promised.** |
| DRM / launchers | Depend on Windows compatibility depth |
| Console-style certification | Far future |

## Performance gates (PROPOSED)

- Fullscreen direct path: no material FPS regression versus windowed baseline
- Shield overhead: <2% median FPS
- Broadcast 1440p60 hardware encode: <3% median FPS
- Input-to-photon: measured and budgeted ([`BENCHMARK-METHODOLOGY.md`](../performance/BENCHMARK-METHODOLOGY.md))

## Honest position

Gaming on Malrynth depends on the Windows compatibility chain *and* the graphics chain, both of
which are long. A realistic early claim is **"some games work well"**, not "Malrynth is a
gaming OS". Anti-cheat-protected competitive titles may never work, and saying so early is
better than disappointing players later.
