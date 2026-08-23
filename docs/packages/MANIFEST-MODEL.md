# Manifest Model

**Status:** PROPOSED. Illustrative syntax only — **not frozen**.

## Role

The manifest is the machine-checkable statement of what an application is and what it may do.
It is the input to the Component Manager's capability routing and the basis of every
user-facing permission surface.

## Illustrative shape

```yaml
id: com.example.photoeditor
version: 2.4.1
abi: malrynth/1
architectures: [x86_64]

publisher:
  name: Example Ltd
  key: <publisher key id>

runtimes:
  - malrynth.runtime.ui/5
  - malrynth.runtime.media/3

entry_points:
  main: { blob: sha256:..., activation: [launch, file, uri] }

capabilities:
  required:                      # refuse to install without these
    - malrynth.ui.window
  optional:                      # requested at runtime; app must work without
    - malrynth.net.client
    - malrynth.device.camera
    - malrynth.storage.directory.write
  never:                         # explicit self-denial, enforced by the system
    - malrynth.device.usb
    - malrynth.ui.capture.screen

provides:
  file_associations: [image/jpeg, image/png]
  uri_schemes: [photoedit]
  protocols: [malrynth.image.Editor/1]

consumes:
  protocols: [malrynth.storage.Files/1, malrynth.media.Decode/2]
```

## Design rules

1. **`required` vs `optional` is load-bearing.** `required` blocks installation; `optional`
   must be handled gracefully when denied. An app declaring everything `required` is a
   reviewable smell.
2. **A `never` list is enforceable self-denial.** It lets a careful publisher make a
   commitment the system upholds, which is auditable in a way a privacy policy is not.
3. **Declaring is not receiving.** The manifest states *maximum* requested authority. Actual
   handles come from Component Manager, policy and user grants.
4. **`provides`/`consumes` are typed and versioned**, so inter-app routing does not depend on
   string matching or ambient discovery.
5. **The manifest is signed with the package.** It cannot be edited post-signing.
6. **Human-readable diffs.** A permission change between versions must be reviewable —
   silently widening capabilities in an update is a supply-chain attack.

## Enforcement

The Component Manager is the only component that reads manifests to route capabilities. The
kernel knows nothing about manifests — it enforces handles and rights. That separation keeps
policy out of the TCB.
