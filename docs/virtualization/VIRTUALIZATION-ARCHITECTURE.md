# Virtualization Architecture

**Status:** PROPOSED. **Kernel/VMM split is [Q14](../architecture/OPEN-QUESTIONS.md) — the
earliest deadline in the register (end of M3), because it constrains M1–M4.**

## Why this must be decided early

Virtualization is not only a compatibility feature. It shapes the memory model (nested paging),
the IOMMU design (device assignment), and the interrupt architecture (posted interrupts). Those
are M1 and M4 decisions. Deciding virtualization at M5 means either redesigning M1's memory
model or accepting a permanently bad virtualization story.

## Proposed split

```
user space          VM Manager (VMM)                       L3, unprivileged
                    ├── device models (virtio)
                    ├── guest memory management
                    ├── VM lifecycle, snapshots
                    └── policy
                          │  capabilities
kernel              virtualization primitives              L2
                    ├── VMX/SVM enable, VMCS/VMCB
                    ├── guest entry/exit
                    ├── EPT/NPT (nested paging)
                    ├── interrupt injection
                    └── device assignment via IOMMU
```

**In the kernel:** only what requires privilege — the hardware virtualization instructions,
nested page tables, guest entry/exit, interrupt injection, and IOMMU programming.

**In user space:** everything else — device emulation, guest memory policy, lifecycle,
snapshots, networking, storage backends. A VMM is a large, complex program that parses guest
input; it belongs outside the TCB.

This mirrors the driver model, for the same reason: a compromised VMM should cost one VM, not
the machine.

## Uses

| Use | Purpose |
|---|---|
| Linux compatibility VM | Correctness-first Linux applications |
| Windows VM | Fallback before Wine maturity |
| Android VM | The realistic Android path |
| **Driver bridge VM** | Difficult hardware via an isolated guest with exclusive IOMMU assignment |
| Development VMs | Testing Malrynth on Malrynth |
| Security isolation | Untrusted workloads |

## The driver bridge

```
physical device ── exclusive IOMMU assignment ──> isolated driver VM
                                                       │ existing driver
                                                       ▼
                                                  bridge backend
                                                       │ virtqueue
                                                       ▼
                                             Malrynth virtual device frontend
```

**This never means loading foreign kernel modules into the Malrynth kernel.** The device is
assigned to a guest; the guest's driver talks to hardware; Malrynth sees a paravirtual device.
The invariant holds — Linux is beside Malrynth, never beneath it.

A GPU bridge is explicitly **not** the primary graphics strategy: adding a VM boundary
complicates latency, display ownership and buffer sharing precisely where they matter most.

## virtio

Reused as the paravirtual device standard: a well-specified shared-descriptor-ring model with
block, network, input, GPU, sound and filesystem device classes. Writing a bespoke paravirtual
protocol would buy nothing and cost guest compatibility.
