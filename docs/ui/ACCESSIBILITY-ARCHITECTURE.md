# Accessibility Architecture

**Status:** PROPOSED. Target: M6 — **designed in from the start, never retrofitted.**

## Why this is architecture, not a feature

Accessibility retrofitted onto a UI toolkit is always poor, because the semantic information
assistive technology needs was never captured. If controls do not carry meaning from the
beginning, no amount of later work recovers it.

## Model

```
application UI
   └─> toolkit controls  ── emit semantics automatically ──┐
                                                            ▼
                                                  accessibility tree
                                                            │  (capability-gated)
                                                            ▼
                                        screen reader · magnifier · switch access
```

Standard controls contribute semantics **automatically**. Only custom-drawn controls require
explicit labelling — which is the correct incentive: the easy path is the accessible one.

## Requirements

| Capability | Requirement |
|---|---|
| Screen reader | Full navigation of the tree; live regions; reading order |
| Keyboard | **Every** interaction reachable without a pointer |
| Focus | Visible indicator; logical order; focus never trapped |
| Magnification | Compositor-level, with text reflow where possible |
| Contrast | High-contrast theme; contrast validated in tooling |
| Reduced motion | Honoured system-wide; motion never carries sole meaning |
| Switch access | Scanning-based interaction |
| Captions | Media framework provides caption rendering |
| Speech | Text-to-speech and speech input as system services |

## Security

The accessibility tree is powerful: it exposes application content and can drive input. It is
therefore a **capability**, not an ambient service. Assistive technology receives it through an
explicit, user-granted, revocable grant with a visible indicator.

This is a genuine tension — accessibility software legitimately needs broad access, and
malware would love the same. The resolution is explicit user consent plus visibility, never
silent access.

## The test

**Malrynth's own applications must be fully usable with a screen reader and keyboard alone.**
If Files, Settings and Terminal are not, the platform's accessibility is not real, whatever
the API surface claims.
