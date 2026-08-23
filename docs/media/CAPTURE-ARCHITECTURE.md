# Capture Architecture

**Status:** PROPOSED. Target: M6+.

## Principle

> **Capture is a capability granted by the compositor, never an ambient ability.**

On a system where any process can read the screen, every other security boundary is
decorative. Malrynth's compositor owns capture authorisation, and this must be designed in
from the compositor's first commit — it cannot be added later without breaking clients.

## Capture kinds

| Kind | Capability | Indicator |
|---|---|---|
| Full screen | `ui.capture.screen` | **Always visible, non-suppressible** |
| Single window | `ui.capture.window` (user-picked) | Visible |
| Own surface | implicit | None needed |
| Application audio | `media.capture.app` | Visible |
| Camera | `device.camera` | Visible |

**User-picked window capture uses the portal pattern** — choosing the window *is* the grant,
which is both better UX and better security than a blanket permission
([`APPLICATION-CAPABILITY-MODEL.md`](../apps/APPLICATION-CAPABILITY-MODEL.md)).

## Zero-copy path

```
application render surface
     ├──> presentation (compositor)
     └──> read-only capture surface ──> encoder ──> Broadcast
```

The capture surface is a **read-only view of the same GPU memory**. No copy, no CPU round trip,
minimal impact on the captured application — which is what makes the proposed gate (<3% median
FPS regression for 1440p60 hardware encode) achievable at all.

## Failure behaviour

A capture consumer that stalls must never stall the application being captured. Capture is
best-effort by construction: dropping capture frames is correct, dropping game frames is not.
