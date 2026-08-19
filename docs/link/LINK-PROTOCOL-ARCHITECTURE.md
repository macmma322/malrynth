# Link Protocol Architecture

**Status:** PROPOSED. Target: post-M7.

## Position

Link is an **open, encrypted, local-first device protocol** — not a cloud dependency and not a
lock-in mechanism. Two devices on the same network must work with no server involved at all.

## Transport

QUIC: multiplexed streams (each Link feature is its own stream), low-latency connection setup,
and path migration so a session survives a network change. TLS 1.3 provides the cryptographic
layer.

## Pairing

```
PC shows QR → phone scans → ephemeral authenticated key exchange
   → BOTH devices display a verification code → user confirms
   → device public keys become mutually trusted
```

The **displayed verification code is essential** — it defeats a man-in-the-middle during
pairing, and skipping it is the most common weakness in device-pairing protocols.

## Per-feature authorisation

```
Malrynth Link session
├── clipboard      ├── notifications   ├── files
├── camera         ├── browser handoff ├── device status
└── remote control
```

Each stream is **independently authorised and revocable**:

```
Galaxy Phone
  Files          Allow        Camera          Ask each time
  Clipboard      Allow        Messages        Deny
  Notifications  Allow        Remote control  Deny
```

This is the capability model applied to devices: pairing is not a blanket grant.

## Local and remote

```
same network:   Phone ═══ encrypted direct ═══ PC
remote:         Phone → encrypted → blind relay → encrypted → PC
```

**The relay never holds content keys.** It forwards ciphertext and learns as little metadata as
the design permits.

## Cross-platform

Clients target Android, Windows, Linux, macOS, iOS (within platform restrictions) and Malrynth.
Malrynth-to-Malrynth may offer deeper continuity, but **competing platforms are not
intentionally degraded** (Constitution §7). A protocol that works well only between Malrynth
devices would be lock-in wearing an open-protocol label.
