# Text Architecture

**Status:** PROPOSED. Target: M6.

## Position: reuse

Text is the clearest **reuse** case in the platform. Unicode, shaping and rasterisation are
decades of accumulated correctness across writing systems, and a bespoke implementation would
not be "custom" — it would be broken for most of the world's languages.

| Component | Decision | Reason |
|---|---|---|
| Unicode data | **Reuse** | A data standard |
| Shaping (HarfBuzz-class) | **Reuse** | Complex-script correctness is a research field |
| Rasterisation (FreeType-class) | **Reuse** | Decades of hinting and format edge cases |
| Locale data (CLDR/ICU-class) | **Reuse** | A data standard |
| Font service, layout, editing | **Custom** | Where Malrynth's architecture lives |

## Pipeline

```
string
  → itemisation      script, direction, language runs
  → font selection   family, weight, variable axes, fallback chain
  → shaping          glyphs + positions (reused engine)
  → layout           lines, wrapping, justification, ellipsis
  → rasterisation    glyph bitmaps / GPU atlas
  → composition
```

## Requirements

Bidirectional text and correct fallback are not optional extras — they are the difference
between an OS that works in some languages and one that works. Required from the start:
Unicode normalisation, grapheme/word/line segmentation, bidi, vertical text (later), variable
fonts, colour emoji, font fallback chains, subpixel positioning, and hinting policy.

## Text input

IME support for CJK and complex scripts is a **platform** concern, not an application one. An
application receives composed text plus composition state; it never implements input methods
itself. Designing this late produces a platform where non-Latin input is second class
permanently.

## Security

Fonts are untrusted input. Font parsing and rasterisation run **sandboxed and unprivileged** —
historically one of the most reliably exploited surfaces in every desktop OS, and one Malrynth
can contain by construction.
