# Audio Graph

**Status:** PROPOSED. Target: M6.

## The differentiator

Per-application audio routing, natively:

```
Game ──────────┬──► Headphones
               └──► Broadcast track 1
Microphone ────┬──► Voice chat
               └──► Broadcast track 2
Voice chat ────────► Broadcast track 3
Music ─────────────► Headphones only
```

**No virtual audio cables. No loopback gymnastics.** On existing desktops this requires
third-party tools and fragile configuration; here it is a platform capability, and it is one of
the clearest wins available from owning the whole stack.

## Requirements

| Concern | Requirement |
|---|---|
| Latency | Stable 128-frame @ 48 kHz under stress (proposed gate) |
| Scheduling | Deadline reservations via capability, not self-promotion |
| Formats | Sample-rate conversion, channel mapping, surround |
| Devices | Hot-plug without dropping streams |
| Per-app control | Volume, routing, mute, capture — all user-controllable |
| Effects | Noise suppression, gate, EQ, compression, limiter, ducking |
| Plugins | **Out-of-process or WASM-sandboxed** — never injected into the audio server |

## Scheduling

A game cannot request `REALTIME_MAXIMUM`. Latency-sensitive audio receives a
**`SchedulingProfile` capability** with explicit parameters, e.g.:

```
capacity 0.50 ms · deadline 2.67 ms · period 2.67 ms      (128 frames @ 48 kHz)
```

granted by the audio service to clients that need it. This makes professional audio possible
without letting any application starve the system — the same pattern as every other capability.

## Security

Microphone access is a runtime grant with a **non-suppressible system indicator**. Per-app
audio *capture* (recording another app's output) is a separate, more sensitive capability than
playback, because it is functionally surveillance.
