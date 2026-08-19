# GPU feasibility on a non-Linux Malrynth kernel

**Status:** research proposal, 2026-08-19. No GPU is claimed supported.

## Evidence labels

- **OFFICIAL FACT** — stated by a vendor or specification owner.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE** — demonstrated by maintained source; it is not a
  promise that the code is portable or legally reusable as a whole.
- **INFERENCE** — engineering conclusion that still requires a pinned device and experiment.
- **PROPOSED MALRYNTH DECISION** — recommendation for later architecture review.

## Result

**PROPOSED MALRYNTH DECISION:** R0 uses the UEFI GOP framebuffer and requires no native GPU
acceleration. When acceleration work starts, rank the vendors:

1. **AMD — FEASIBLE, but DIFFICULT.** Best first accelerated family because the kernel and
   Mesa paths are open, public AMD register/ISA material exists, and RADV documents a clear
   userspace-to-kernel boundary. Freeze one well-supported generation.
2. **Intel — DIFFICULT.** Strong official programming documentation and open Mesa/kernel
   implementations make it credible, especially for one older integrated generation. The
   i915/xe split, platform display complexity, power management, and firmware components
   still make this a major port.
3. **NVIDIA — VENDOR DEPENDENT and CURRENTLY A POOR R0 CHOICE.** NVIDIA's open kernel
   modules are explicitly Linux kernel modules, require matching userspace and GSP firmware,
   and do not cover the owned Pascal mobile GPU. Nouveau/NVK are valuable implementation
   evidence, not a turnkey non-Linux stack.

This ranking is for a new independent host kernel. It is not a general performance ranking.

## The three-part driver problem

A modern GPU stack is not one driver that can be recompiled. Malrynth would need to replace
Linux-specific infrastructure at every boundary.

| Layer | Typical responsibilities | Malrynth replacement burden |
|---|---|---|
| Firmware | GOP before boot; GPU microcontrollers; display, scheduler, security, media or power firmware depending on generation | Locate, authenticate where required, load in the required order, honor redistribution terms, and recover from version mismatch |
| Kernel mode | PCI enablement, BARs, memory manager, DMA/IOMMU mappings, queues, interrupts, reset, power, display/KMS, buffer sharing and synchronization | Native PCI/MMIO/IRQ/DMA primitives, GPU virtual memory, fence/timeline model, display API, process isolation, reset and hang containment |
| User mode | Vulkan/OpenGL API, shader compiler, command construction, resource tracking, WSI, compositor integration, compute/video frontends | Port or adapt Mesa winsys/OS layers, define a stable Malrynth GPU ABI, provide process memory/synchronization and a native window-system integration |

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux DRM supplies GEM/TTM memory management,
scheduler/fence helpers, KMS objects, dma-buf sharing, runtime PM, hotplug and subsystem
conventions used throughout current drivers. Mesa drivers normally talk to a DRM kernel uAPI.
The existence of an open source tree therefore proves that logic can be studied; it does not
prove that Linux types, helpers, locking, ABI, memory lifetime or licensing can be retained.
[Linux GPU documentation](https://docs.kernel.org/gpu/),
[Mesa RADV documentation](https://docs.mesa3d.org/drivers/radv.html)

## Staged display plan

| Phase | Deliverable | Exit evidence | Deliberately excluded |
|---|---|---|---|
| A — UEFI GOP | Loader selects a conservative linear mode and records base, size, stride and pixel format | Test pattern and serial metadata before `ExitBootServices()` | Native modeset, hotplug, acceleration |
| B — owned simple framebuffer | Kernel validates/maps the handed-off range and a software console remains usable | Text/pixels survive memory-map transition, interrupts, SMP and device discovery | Reprogramming the display engine |
| C — basic display driver | One pinned GPU/display path can take ownership and set one mode | Cold boot, blank/unblank and reset recovery on the frozen monitor/cable | Broad connectors, suspend, 3D |
| D — acceleration | Native memory, submission, synchronization and reset ABI; one Mesa path | Isolated processes render offscreen and survive a deliberately injected hang | Certification, many GPU generations |
| E — Vulkan/compositor | Vulkan subset/conformance plan, WSI and compositor integration | Pinned test suite and long-running interactive workload | Vendor-wide support claims |

**OFFICIAL FACT:** UEFI GOP exposes framebuffer mode information and a linear framebuffer
during boot. UEFI does not promise that a native OS can later change modes or that firmware
services remain callable after `ExitBootServices()`. [UEFI 2.11 GOP](https://uefi.org/specs/UEFI/2.11/12_Protocols_Console_Support.html)

**PROPOSED MALRYNTH DECISION:** freeze the GOP mode before exit, copy all mode metadata,
reserve the framebuffer physical range, and keep serial as the authoritative failure console.
No PHYSICAL-0/1 gate may require a display engine reset or native modeset.

## AMD

### Architecture and dependencies

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux `amdgpu` contains PCI/platform discovery,
firmware loading, GPU virtual memory, TTM/GEM memory management, command submission,
scheduling/fences, interrupts, reset, power/thermal control, Display Core and media blocks.
[AMDGPU documentation](https://docs.kernel.org/gpu/amdgpu/index.html)

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Mesa RADV is a Vulkan driver for AMD hardware and
documents reliance on the AMDGPU DRM uAPI. Its source includes compiler, command generation,
memory/synchronization and winsys integration. [RADV documentation](https://docs.mesa3d.org/drivers/radv.html),
[Mesa source and license](https://gitlab.freedesktop.org/mesa/mesa)

**OFFICIAL FACT:** AMD publishes GPU architecture/ISA and developer material through GPUOpen
and distributes device firmware through the linux-firmware project for supported Linux
devices. Exact blob license and device coverage must be reviewed before Malrynth distribution.
[AMD GPUOpen documentation](https://gpuopen.com/documentation/),
[linux-firmware AMD directory](https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/tree/amdgpu)

### Feasibility judgment

| Capability | Judgment | Why |
|---|---|---|
| GOP framebuffer | **FEASIBLE** | Standard firmware path; qualify the exact board/GPU and monitor |
| Native display | **DIFFICULT** | Display Core is large; clocks, PHYs, connectors, link training, hotplug and atomic state interact |
| Vulkan | **DIFFICULT** | RADV is strong reusable userspace evidence, but Malrynth needs a compatible memory/submission/sync ABI and winsys |
| Compute | **VERY DIFFICULT** | Requires stable queues, memory, compiler/runtime and process isolation beyond initial graphics |
| Video decode/encode | **VERY DIFFICULT** | Separate firmware, rings, codecs, protected content and userspace APIs |

**PROPOSED MALRYNTH DECISION:** choose one discrete AMD generation only at R2, after native
IOMMU domains and PCIe reset/error recovery work. Begin with offscreen command submission,
then one display connector. Do not promise the entire `amdgpu` hardware range.

## Intel

### Architecture and dependencies

**OFFICIAL FACT:** Intel publishes graphics programming reference manuals and platform
documentation. These are unusually useful for register, command and memory-format research,
but exact availability differs by generation. [Intel graphics documentation](https://dgpu-docs.intel.com/)

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux has both the mature i915 path and the newer xe
path. They depend on DRM memory, scheduler, synchronization, display, firmware, power and PCI
infrastructure. Mesa's Iris and ANV drivers provide OpenGL and Vulkan userspace paths tied to
kernel uAPIs. [Linux i915 documentation](https://docs.kernel.org/gpu/i915.html),
[Linux xe documentation](https://docs.kernel.org/gpu/xe/),
[Mesa Intel Vulkan source](https://gitlab.freedesktop.org/mesa/mesa/-/tree/main/src/intel/vulkan)

Intel generations can require DMC, GuC or HuC firmware for subsets of display, submission,
power or media behavior. A device-generation matrix must record which component is mandatory,
optional or unavailable and the redistribution terms of every selected file.
[linux-firmware Intel directory](https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git/tree/i915)

### Feasibility judgment

| Capability | Judgment | Why |
|---|---|---|
| GOP framebuffer | **FEASIBLE** | The selected Comet Lake iGPU is used only through firmware initially |
| Native display | **DIFFICULT** | Public PRMs help, but display/watermark/power sequencing is platform-specific and large |
| Vulkan | **DIFFICULT** | ANV and compiler code are strong evidence; a Malrynth kernel ABI/winsys remains necessary |
| Compute | **VERY DIFFICULT** | Requires robust contexts, VM, scheduling, recovery and runtime work |
| Video decode/encode | **VERY DIFFICULT** | Media firmware and APIs are a separate project |

**INFERENCE:** the R0-A UHD 630 is useful because GOP avoids a discrete card, not because it
is automatically the first accelerated target. A tightly scoped Gen9.5 experiment could be
valuable, but long-term effort must be compared against one selected AMD family.

## NVIDIA

### Architecture and dependencies

**OFFICIAL FACT:** NVIDIA publishes open GPU kernel modules as source for Linux. The release
must be paired with the corresponding NVIDIA userspace driver, and supported GPUs use the GPU
System Processor firmware architecture. This is an official Linux integration path, not a
portable hardware specification or a complete open userspace stack.
[NVIDIA open GPU kernel modules](https://github.com/NVIDIA/open-gpu-kernel-modules)

**OFFICIAL FACT:** NVIDIA's project states that the open modules support Turing and newer
GPUs; pre-Turing support is outside that GSP-based design. The owned GP107M GTX 1050 Ti is
Pascal, so it is not a candidate for this official open-module path.
[NVIDIA pre-Turing issue](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/19)

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Nouveau and Mesa NVK show independent open driver
work. NVK documents a current Vulkan implementation and a Linux DRM/Nouveau kernel baseline;
that dependency remains to be replaced on Malrynth. [Mesa NVK](https://docs.mesa3d.org/drivers/nvk.html),
[Nouveau documentation](https://docs.kernel.org/gpu/nova/index.html)

### Feasibility judgment

| Capability | Judgment | Why |
|---|---|---|
| GOP framebuffer | **FEASIBLE** on a qualified card | Firmware path only; the owned laptop adds hybrid-routing complications |
| Native display | **VERY DIFFICULT / VENDOR DEPENDENT** | Generation-specific initialization, firmware, display and power; official open path assumes Linux/GSP |
| Vulkan | **VERY DIFFICULT** | NVK is evidence, but kernel, firmware, WSI and generation support still need a Malrynth port |
| Compute | **VENDOR DEPENDENT** | CUDA userspace is proprietary and Linux-oriented; an open alternative is not an R0-equivalent substitute |
| Video decode/encode | **VENDOR DEPENDENT** | Firmware and proprietary userspace/API dependencies dominate |

**PROPOSED MALRYNTH DECISION:** do not buy or select NVIDIA for R0/R2. Keep the owned Pascal
laptop for GOP and negative discovery testing only. Revisit if NVIDIA publishes a stable
non-Linux integration contract or a bounded open stack can be demonstrated on one device.

## Vulkan practicality and conformance

**OFFICIAL FACT:** Vulkan specifies an API and conformance process, not an operating-system
driver architecture. A port still needs memory allocation, queues, synchronization, shader
compilation, presentation, external-object rules and a window-system binding.
[Vulkan specification](https://registry.khronos.org/vulkan/specs/latest/html/vkspec.html),
[Khronos conformant-products policy](https://www.khronos.org/conformance/adopters/conformant-products/vulkan)

**PROPOSED MALRYNTH DECISION:** do not advertise Vulkan from rendering a triangle. Define a
versioned native GPU ABI; port one Mesa driver and its compiler/winsys under license review;
run the appropriate conformance test suite; and use the Vulkan trademark only under Khronos
rules. Software rendering remains useful for compositor/API development before hardware.

## Port strategy

| Component | Strategy | Reason |
|---|---|---|
| GOP handoff/simple framebuffer | **WRITE NATIVE** | Small UEFI/kernel contract and no Linux dependency |
| PCI, MMIO, IRQ, DMA/IOMMU, mapping and reset | **WRITE NATIVE** | Security-critical kernel primitives |
| Register tables, packet formats, compiler algorithms | **PORT ALGORITHM/LOGIC** | High-value knowledge, but detach it from Linux object/lifetime APIs |
| Mesa compiler and API implementation | **PORT LARGE DRIVER** only after ABI prototype | Reimplementation would be wasteful; OS/winsys seam and licenses must be explicit |
| Complete Linux DRM driver | **DO NOT DIRECTLY PORT AS R0** | Too coupled to DRM, TTM/GEM, dma-buf, scheduler, PM and Linux ABI |
| Proprietary firmware/userspace | **REQUIRES VENDOR/LEGAL CLEARANCE** | Redistribution, signing, version coupling and support terms may be controlling |
| Linux GPU driver domain | **BOOTSTRAP EXPERIMENT ONLY** | Device assignment plus scanout/buffer export is complex and creates a Linux boot dependency |

## Qualification and pivot gates

Before Phase C, the pinned GPU must have documented reset, firmware inventory, IOMMU
isolation and a serial-recoverable failure path. Before Phase D, demonstrate bounded process
GPU virtual address spaces, no arbitrary physical DMA, fence timeout, engine reset and memory
reclamation after client death. Before Phase E, demonstrate that Mesa changes are contained
to an explicit Malrynth winsys/OS layer rather than a permanent fork across the driver.

Pivot away from a family if mandatory firmware cannot legally ship, display initialization
depends on an unavailable signed component, every upstream release requires invasive Linux-
internal rewrites, reset cannot contain hangs, or the exact board routes display through an
unsupported second GPU. See [PIVOT-CRITERIA.md](PIVOT-CRITERIA.md).

## Recommended integration

Future graphics architecture may adopt the five phases and stable kernel/userspace ABI gate.
Do not add GPU acceleration to the R0 support definition or roadmap without separate review.

## Source ledger contributions

| Authority | Accessed | Claim contributed | URL/reference | Licensing relevance |
|---|---|---|---|---|
| UEFI Forum | 2026-08-19 | GOP mode/framebuffer contract | https://uefi.org/specs/UEFI/2.11/ | Specification; no code copied |
| Linux kernel project | 2026-08-19 | DRM, AMDGPU, i915/xe and Nouveau architecture evidence | https://docs.kernel.org/gpu/ | GPL-2.0-only kernel code; study and clean interface design, no code copied |
| Mesa project | 2026-08-19 | RADV, ANV and NVK userspace architecture evidence | https://docs.mesa3d.org/ | Primarily MIT; exact files/dependencies require review |
| AMD GPUOpen | 2026-08-19 | Public AMD developer/architecture material | https://gpuopen.com/documentation/ | Document/source terms vary; review selected artifacts |
| Intel | 2026-08-19 | Public graphics programming documentation | https://dgpu-docs.intel.com/ | Documentation terms; no code copied |
| NVIDIA | 2026-08-19 | Linux open-module, matched userspace/GSP and generation scope | https://github.com/NVIDIA/open-gpu-kernel-modules | Dual GPL/MIT portions plus firmware/proprietary userspace; exact-file review required |
| Khronos | 2026-08-19 | Vulkan API and conformance requirements | https://registry.khronos.org/vulkan/specs/latest/html/vkspec.html | Specification/trademark terms; CTS license separately reviewed |
