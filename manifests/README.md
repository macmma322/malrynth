# Manifests

The superproject's record of **what Malrynth is made of** and **what a product composes**.

While Malrynth is a single repository (ADR-0001), the exact source state is identified by one
commit SHA, reported by `tools/status`. These manifests are the human-readable, diffable form
of that answer, and they are the mechanism that survives unchanged if components are later
extracted into their own repositories — at which point they gain pinned commits without
changing shape.

- `workspace/components.toml` — the component inventory and its build targets.
- `products/` — product compositions. **No product exists yet**; the axes are recorded so a
  product is later defined by composition rather than by forking.
- `releases/` — release records, created when the first tag is made.
