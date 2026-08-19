# Design System Architecture

**Status:** PROPOSED. Target: M6.

## Purpose

A design system is infrastructure, not styling. It is what makes first-party applications feel
like one system and third-party applications feel at home, while keeping theming safe.

## Token layers

```
primitive tokens     raw values            #2B7FFF, 4px, 200ms
      ↓
semantic tokens      meaning               color.action.primary, space.inset.compact
      ↓
component tokens     per-control           button.primary.background
```

Applications reference **semantic** tokens. That indirection is what lets themes, high
contrast, and density changes work without every app being rewritten — and it is why themes
can be pure data.

## Requirements

| Concern | Requirement |
|---|---|
| Theming | Light, dark, high contrast; user themes are **declarative data with no code** |
| Density | Comfortable / compact, respecting pointer vs touch |
| Motion | Honour reduced-motion; motion is never required to convey meaning |
| Colour | Contrast ratios enforced by tooling, not by reviewer judgement |
| Adaptivity | Breakpoints and input-mode adaptation as first-class concepts |
| Localisation | Text expansion, RTL mirroring, locale-aware formats |
| Accessibility | Every component ships semantics, focus order and keyboard behaviour |

## The rule that keeps it honest

**A component is not complete until it is keyboard-navigable, screen-reader-labelled,
contrast-compliant and RTL-correct.** Treating those as follow-up work is how design systems
accumulate inaccessible components that are then too widely used to fix.
