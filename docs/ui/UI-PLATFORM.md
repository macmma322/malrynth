# UI Platform

**Status:** PROPOSED. Target: M6.

## Layering

```
application
   └─> UI toolkit          controls, layout, animation, input, semantics   L6
        ├─> design system   tokens, theming, adaptive rules
        ├─> text engine     shaping, fallback, bidi                        L6
        ├─> accessibility   semantic tree + AT bridge                      L6
        └─> surface protocol ──> compositor                                L3
                                    └─> Vulkan ──> GPU
```

## Toolkit decisions

| Question | Direction | Reason |
|---|---|---|
| Custom or reuse? | **Custom** | The toolkit is where capability integration, accessibility and performance contracts live |
| Rendering | GPU-first via Vulkan, CPU fallback | Fallback is required for early bring-up and headless/remote cases |
| Retained vs immediate | **Undecided** — [Q7](../architecture/OPEN-QUESTIONS.md) | Determines animation quality, accessibility integration and memory |
| Language | Rust, C ABI for other languages | Consistent with [`ABI-STRATEGY.md`](../runtime/ABI-STRATEGY.md) |
| Accessibility | **Built into the control model** | Retrofitted accessibility is invariably poor |

## Performance contract

The toolkit is bound by the gates in
[`PERFORMANCE-CONSTITUTION.md`](../performance/PERFORMANCE-CONSTITUTION.md): frame time,
input-to-photon latency, application warm start, idle memory. A toolkit that cannot meet them
is not finished, regardless of how complete its widget set is.

## Adaptive UI across products

Desktop, Mobile and Console share **primitives** — layout, text, semantics, theming, input
abstraction — without pretending their interaction models are the same. A desktop context menu
and a console radial menu are different *interactions* built from the same primitives; forcing
one interaction model across all three produces something bad everywhere.

## Customisation: three trust tiers

| Tier | Examples | Authority |
|---|---|---|
| **Declarative** | Colour, spacing, fonts, wallpaper, icons, animation speed | **None.** Data, not code |
| **Sandboxed extension** | Widgets, panels, status items, launchers | Separate capability-constrained process |
| **Developer / system** | Replacement shell, compositor extensions | Explicit developer mode |

**A theme never gains file access.** A weather widget gets network and (optionally) coarse
location — not `ReadEntireHomeDirectory`. This tiering is what allows deep customisation
without turning the shell into a plugin dumpster with ambient authority.

## Input

Keyboard, mouse, touch, pen, controller and accessibility switches are routed by the
compositor to the focused surface. Input is **never** globally readable: a keylogger cannot be
built from ordinary application capabilities, because no ordinary capability grants global
input observation.
