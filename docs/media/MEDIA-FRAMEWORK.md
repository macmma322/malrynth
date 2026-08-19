# Media Framework

**Status:** PROPOSED. Target: M6.

## Purpose

One shared media infrastructure for Photos, Video, Music, Camera, Recorder, Capture, Canvas,
Broadcast **and third-party applications**. If Broadcast needs plumbing nothing else has, the
platform is missing something — that is the design test for this layer.

## Structure

```
sources ──> processing ──> sinks
   │            │            │
 file        decode       display
 camera      filter       audio out
 screen      convert      encode ──> file / stream
 microphone  compose      virtual device
 network     scale
```

Graphs are built from typed nodes; buffers move by **handle**, not by copy
([`IPC-MODEL.md`](../architecture/IPC-MODEL.md)). A frame decoded into GPU memory reaches the
compositor without a round trip through system memory.

## Build vs reuse

| Component | Decision | Reason |
|---|---|---|
| Codecs | **Reuse** | Enormous, patent-encumbered, security-critical. **Never written from scratch.** |
| Containers / muxers | **Reuse** | Format complexity, little architectural value |
| Image decoders | **Reuse**, sandboxed | Classic exploit surface |
| Graph, routing, capabilities | **Custom** | This is the architecture |
| Hardware encode/decode | **Reuse** via Vulkan Video | Keeps the media path inside one standard |

**Every decoder runs unprivileged and sandboxed.** Media parsing is untrusted-input handling
with a long exploit history.

## Colour and HDR

Colour management is end-to-end from the start: content colour space → processing → compositor
→ display. Retrofitting HDR is painful because intermediate stages silently assume sRGB, so the
pipeline carries colour metadata even before HDR displays are supported.

## Capabilities

| Capability | Notes |
|---|---|
| `media.playback` | Ordinary; may be granted for background |
| `media.decode` | Implicit in playback |
| `media.encode` | Explicit; hardware encoders are a contended resource |
| `device.camera` / `device.microphone` | Runtime grant + **non-suppressible indicator** |
| `ui.capture.screen` | Compositor-authorised, never implicit |

## Codec licensing

Codec patent obligations are independent of source licensing and can foreclose distribution
models. This is [Q10](../architecture/OPEN-QUESTIONS.md) and requires professional legal review
before any media application ships.
