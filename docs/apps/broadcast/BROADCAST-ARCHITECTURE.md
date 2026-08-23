# Broadcast Architecture

**Status:** PROPOSED. Target: post-M7.

Broadcast is potentially one of Malrynth's most compelling native applications, because the OS
owns capture, audio routing, GPU surfaces, scheduling and encoders. On other platforms this
functionality fights the OS; here it composes with it.

## Design rule

> **Broadcast consumes platform capabilities. It does not build parallel plumbing.**

If Broadcast needs something the platform does not provide, the correct fix is to add it to the
platform where Photos, Video and third-party tools can use it too. An application that needs
private plumbing is a symptom of a missing platform capability.

## Object model

```
BroadcastSession
├── Scene ──> Source · Source · Filter
├── AudioGraph          ← platform audio graph
├── VideoGraph          ← platform media framework
├── Encoder             ← platform hardware encode
├── Muxer
├── RecordingOutput
└── StreamOutput
```

## Platform dependencies

| Broadcast needs | Provided by |
|---|---|
| Game/window/display capture | [`CAPTURE-ARCHITECTURE.md`](../../media/CAPTURE-ARCHITECTURE.md) |
| Per-app audio tracks | [`AUDIO-GRAPH.md`](../../media/AUDIO-GRAPH.md) |
| Hardware encode | [`VIDEO-PIPELINE.md`](../../media/VIDEO-PIPELINE.md) |
| Low-latency scheduling | Capability-granted `SchedulingProfile` |
| Virtual camera output | Media framework virtual devices |
| Browser source | Browser engine as an embeddable surface |

## Resilient recording

```
recording.session/
   000001.segment  000002.segment  000003.segment  timeline  metadata
```

A crash recovers **all committed segments**, then finalises into the chosen container. Losing a
multi-hour recording to a crash at the end is the failure users find unforgivable, and
segmented recording eliminates it structurally.

## Plugins

Plugins run **out-of-process or in a WASM-style sandbox** — never injected into the Broadcast
core. Plugin crashes must not end a live stream, and a plugin must not inherit Broadcast's
capture and audio capabilities.

## Feature target

Scenes and nested scenes, browser sources, per-app audio, six or more recording tracks,
hardware AV1/H.264/H.265, HDR, LUTs and colour correction, VST/LV2-class plugin compatibility,
noise suppression, gate, EQ, compression, limiter, ducking, virtual camera, replay buffer,
multistream output, RTMP/SRT-class protocols, remote control, local transcription and captions.

**Overhead gate:** <3% median game FPS regression at 1440p60 with hardware encode.
