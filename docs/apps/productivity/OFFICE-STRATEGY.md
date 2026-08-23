# Productivity / Office Strategy

**Status:** PROPOSED. [Q9](../../architecture/OPEN-QUESTIONS.md). Target: post-M7.

## The premise

> **Malrynth does not independently write every Office file parser from zero.**

OOXML (DOCX/XLSX/PPTX) and ODF (ODT/ODS/ODP) are vast specifications with decades of
real-world divergence, and PDF is its own universe. Fidelity is measured against what other
implementations actually produce, not against the spec — which is why from-scratch parsers
produce documents that look wrong in the applications people actually use.

## Split

```
Malrynth-native UI + editing model + collaboration
                │
        document engine (reused)
                │
      format import/export (reused)
```

| Layer | Decision | Reason |
|---|---|---|
| UI, interaction, editing model | **Custom** | Product identity; must be fast, accessible, keyboard-first |
| Layout/rendering engine | **Reuse** | Text layout, tables, pagination are enormous |
| Format import/export | **Reuse** | Interoperability is measured against other implementations |
| PDF rendering | **Reuse** | Format complexity plus a serious security surface |
| PDF generation | Reuse or custom | Generation is far simpler than parsing |

## Interoperability requirement

Round-tripping must not destroy content. **A document opened, unmodified, and saved should not
change** — the failure mode users find unforgivable is silent data loss in a file they still
need to send to someone else.

## Security

Documents are untrusted input, and macros are the classic infection vector.

- Parsers run **sandboxed, out-of-process**, with narrow capabilities.
- **Macros are disabled by default**, run in a constrained sandbox with no ambient authority,
  and require explicit per-document consent. A macro cannot obtain capabilities the document
  viewer does not hold.
- Remote content in documents is a capability, not a default.

## Priority

Low. Reused engines and web alternatives cover this need for years. A mediocre first-party
office suite that exists only to complete a checklist is worse than none — it costs engineering
attention the kernel needs, and the founder vision explicitly warns against shipping mediocre
applications to fill checkboxes.
