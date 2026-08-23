# Telemetry Model

**Status:** PROPOSED.

## Rules

1. **Independently controllable categories** (Constitution §14) — not one master switch.
2. **Off by default** for everything non-essential.
3. **"Essential" is narrowly defined and documented**, never decided case by case. Currently
   the only candidate is update-check traffic, and even that must work without identifying the
   device beyond what the transport requires.
4. **Inspectable before transmission.** A user can see exactly what would be sent.
5. **No content**, ever. Telemetry carries facts about the system, never user data.

## Categories

| Category | Default | Contents | Retention |
|---|---|---|---|
| Update checks | On (essential) | Current version, channel, architecture | Minimal |
| Crash reports | **Off** | Stack trace, module versions, minimal state | Bounded |
| Performance | **Off** | Aggregate timings against budgets | Bounded |
| Feature usage | **Off** | Which features are used, no content | Bounded |
| Hardware inventory | **Off** | For driver prioritisation | Bounded |
| Shield detections | Local | Local; shared only on managed devices or by choice | Per policy |

## Crash reports specifically

Crash dumps can contain user data — that is exactly what makes them useful and what makes them
dangerous. Therefore: opt-in, scrubbed of obvious content, **previewable before sending**, and
never automatic.

## Anti-goals

- No advertising identifiers, no behavioural profiles, no cross-device correlation for analytics.
- No dark patterns in consent. "Ask me later" is a legitimate answer that stays answered.
- No telemetry-derived pressure on product decisions that conflicts with the Constitution.
