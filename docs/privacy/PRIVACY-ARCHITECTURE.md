# Privacy Architecture

**Status:** PROPOSED.

## Privacy is enforced by capabilities, not policy

The distinguishing property of Malrynth's privacy story is that it is **mechanical**:

```
Calculator requests a socket
   → manifest declares no network capability
   → request denied
   → no packet ever exists
```

No firewall rule, no policy engine, no user decision. The application cannot do the thing.

That is qualitatively different from a promise not to. A privacy policy is a statement of
intent; a capability boundary is a property of the system.

## Mechanisms

| Concern | Mechanism |
|---|---|
| App reads unrelated files | No ambient filesystem authority; portals only |
| Silent camera/microphone | Runtime grant + **non-suppressible indicator** |
| Screen observation | Compositor-authorised capture capability |
| Background exfiltration | Network is a capability; background work is budgeted and visible |
| Cross-app tracking | No shared advertising identifier exists to correlate |
| Fingerprinting | Minimised entropy in platform APIs |
| Telemetry creep | Categories are separately controlled and independently auditable |

## Transparency

Users can see: which applications hold which capabilities, what was granted and when,
what is currently using camera/microphone/screen, what data categories sync, and what has
been sent.

**Sensor use is always indicated and the indicator cannot be suppressed by an application.**

## AI

AI is optional and provider-neutral (Constitution §15). Local processing is the default;
sending anything to a remote model is an explicit, per-feature choice. AI is **never the final
security authority** (§16) — a model may advise, the capability system decides.

## What this does not solve

Websites can still fingerprint. Applications the user grants broad capabilities to can still
misuse them. A user who grants everything is not protected by architecture. Malrynth reduces
*ambient* exposure and makes *granted* exposure visible; it cannot make bad grants safe, and
claiming otherwise would be dishonest.
