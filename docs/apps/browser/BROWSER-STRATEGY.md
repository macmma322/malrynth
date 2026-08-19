# Browser Strategy

**Status:** PROPOSED. [Q8](../../architecture/OPEN-QUESTIONS.md). Target: post-M7.

## The premise

> **Malrynth is not writing a complete modern browser engine for v1.**

A competitive engine is a multi-thousand-engineer-year effort spanning HTML, CSS, JavaScript,
WebGPU, media, networking, sandboxing and a relentless security treadmill. Attempting it would
consume the operating system.

**Malrynth Browser = a Malrynth-native browser built on a reused engine.**

## Engine options

| Engine | For | Against |
|---|---|---|
| **Chromium** | Best compatibility; strong sandboxing; embeddable | Enormous; assumes deep platform integration; Google-paced |
| **WebKit** | Cleaner embedding story; genuine independence | Smaller ecosystem; platform-specific ports vary |
| **Servo** | Rust-native; embedding is improving; crates now published | **62% weighted Web Platform Tests vs Chromium's 89%** (2026); realistic daily use estimated 2028–2030 |
| Write our own | — | Not viable |

**Assessment:** Chromium or WebKit for a usable browser. **Servo is a watch item** — its
trajectory is genuinely interesting and Rust-native, but its measured compatibility is not yet
close, and shipping a browser that fails one page in three is worse than shipping none.

Whichever is chosen, the port cost is dominated by how many platform assumptions the engine
makes — which is itself an argument for evaluating embedding-friendliness over raw features.

## What makes it "Malrynth Browser"

The engine renders. Everything a user experiences as *the browser* is ours:

| Aspect | Malrynth provides |
|---|---|
| UI | Native toolkit; not a web-rendered chrome |
| Permissions | Web permissions map onto **platform capabilities** — a site's camera access is the same capability system as an app's |
| Privacy | Tracking protection, isolation defaults, no advertising identifiers (Constitution §13) |
| Passwords / passkeys | Vault integration; never a browser-private secret store |
| Media | Platform media framework; correct HDR, hardware decode, per-app audio |
| Downloads | Capability-based; a download goes where the user chose |
| Link | Browser handoff between devices |
| Local AI | Optional, provider-neutral, never required |
| Extensions | Sandboxed with explicit capabilities — not the historically over-privileged model |

## The security note that matters

A browser is the largest untrusted-input processor on any desktop. It must run **unprivileged
and capability-confined like any other application**, with its own internal sandboxing intact.
The browser having more authority than other apps would invert the whole security model.
