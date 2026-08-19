# Video Pipeline

**Status:** PROPOSED. Target: M6.

## Path

```
source ──> demux ──> decode ──> process ──> present
                        │          │           └─> compositor surface
                        │          └─> scale, convert, colour, filter (GPU)
                        └─> hardware (Vulkan Video) or software fallback
```

Frames stay in GPU memory wherever possible. A decoded frame reaching the compositor should not
round-trip through system memory — that single property determines whether 4K playback is
efficient or embarrassing.

## Requirements

- Hardware decode and encode where available; **correct software fallback always**
- Frame-accurate seeking; A/V sync with a shared media clock
- HDR tone mapping; colour-space conversion in the pipeline, not per-application
- Variable frame rate; frame pacing coordinated with the compositor
- Subtitle and caption rendering through the text engine
- Zero-copy capture path for Broadcast

## Encode as a contended resource

Hardware encoders are limited in number. Simultaneous game recording, streaming and video
calls can exhaust them. The media service arbitrates and **degrades explicitly** — telling the
user which session dropped to software — rather than failing opaquely, which is how this
manifests on other platforms.
