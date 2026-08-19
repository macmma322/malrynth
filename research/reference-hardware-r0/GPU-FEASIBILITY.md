# GPU feasibility for a non-Linux Malrynth host

Status: research recommendation for Reference Hardware R0

Evidence cut-off and source access date: 2026-08-19
Scope: x86-64 UEFI desktop hardware; firmware framebuffer, native display, acceleration, Vulkan/compositor, compute, and video

## Evidence vocabulary

This report deliberately separates five kinds of statement:

- **OFFICIAL FACT** — a standards body, hardware vendor, or OS project states the fact in its own specification, documentation, support matrix, or repository.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE** — current source code or upstream implementation documentation demonstrates that a path exists. It demonstrates engineering possibility, not support on Malrynth.
- **COMMUNITY EVIDENCE** — a developer report or non-upstream experiment. This is useful directionally but is not a product commitment.
- **INFERENCE** — a conclusion drawn from the cited facts. It must be tested on the exact board and firmware revision.
- **PROPOSED MALRYNTH DECISION** — a recommendation for this project, not an upstream fact.

“Open driver” is not used as shorthand for “open GPU.” Host source, firmware source, public hardware documentation, redistributability, kernel ABI, userspace API, and validation status are separate properties.

## Executive decision

**PROPOSED MALRYNTH DECISION:** separate the reference-platform ranking from the later
native-acceleration ranking:

1. **R0-A primary platform: Intel Comet Lake-S/Q470E with UHD 630 iGPU.**
2. **R0-B alternate: AMD AM4 B550 commercial mATX, Ryzen 5 5600G iGPU.**
3. **NVIDIA: expansion-only and explicitly outside the R0 graphics contract.**

For a committed native acceleration family, rank **AMD first, Intel second, NVIDIA third**.
Intel remains a useful bounded Gen9.5 display experiment because it is already in R0-A;
that convenience does not make it the preferred long-term accelerated family.

For both R0-A and R0-B, the mandatory graphics contract ends at a UEFI GOP-provided linear framebuffer plus a CPU-rendered console/compositor. Native modesetting, GPU command submission, Vulkan, compute, and video are later and separately gated claims.

| Rank | Candidate | GOP / linear framebuffer | Native display feasibility | Vulkan path | Compute / video path | R0 classification |
|---:|---|---|---|---|---|---|
| 1 | Intel UHD 630, Comet Lake-S (Gen9.5) | Strong, board-firmware qualification required | Difficult; public Gen9 material and related Coffee Lake non-Linux evidence help but do not prove the exact Comet device | ANV is mature; Malrynth still needs a KMD ABI and winsys | Open Intel runtimes exist, but remain separate ports with firmware and kernel dependencies | **Preferred R0-A platform; framebuffer-required, native acceleration exploratory** |
| 2 | Ryzen 5 5600G integrated Radeon | Strong, board-firmware qualification required | Difficult; AMD DC is a valuable seam, but 5600G evidence outside Linux is weaker | RADV is mature; explicitly depends on amdgpu DRM uAPI and libdrm | ROCm does not validate 5600G in the current Ryzen matrices; VCN is a later project | **Accepted R0-B alternate; framebuffer-required, no acceleration promise** |
| 3 | NVIDIA discrete, Turing or newer | Usually available through option ROM GOP, but adds another boot/display variable | Very difficult; either Linux-coupled Nouveau or GSP/OpenRM plus binary firmware | NVK is conformant on Linux, not a portable full stack | CUDA and NVENC/NVDEC remain vendor-stack dependent | **Non-R0 expansion only** |

**INFERENCE:** Intel wins the *R0 platform* comparison because UHD 630 GOP arrives with the
Q470E CPU/board and requires no extra GPU. This is not a native-driver win. Related Coffee
Lake evidence—public Gen9 material, i915/ANV, Haiku device coverage, Redox's Intel path and
Khronos UHD 630 submissions—reduces uncertainty but does not prove a Comet Lake Malrynth
port. AMD's open kernel/Mesa ecosystem and OS-neutral Display Core seam make it the preferred
committed acceleration family despite a broader initial firmware/IP-block surface.

## The stack Malrynth would actually have to own

### Firmware hand-off is useful but deliberately limited

**OFFICIAL FACT:** UEFI’s Graphics Output Protocol exposes modes and, for direct-access pixel formats, a framebuffer base and size. UEFI also makes clear that boot-service protocols are no longer callable after ExitBootServices; the OS loader owns continued platform operation after that transition ([UEFI GOP](https://uefi.org/specs/UEFI/2.10/12_Protocols_Console_Support.html#graphics-output-protocol), [UEFI system and boot-services lifetime](https://uefi.org/specs/UEFI/2.11/04_EFI_System_Table.html)).

**INFERENCE:** GOP is a hand-off of an already programmed scanout buffer, not a continuing display-driver service. It does not promise mode changes, EDID/hotplug, vblank, power-state recovery, suspend/resume, GPU reset, buffer allocation, command submission, or acceleration after ExitBootServices. The framebuffer can remain visibly useful while the underlying hardware state is opaque.

### Kernel / user / firmware split

| Layer | Malrynth responsibility | What Linux currently supplies |
|---|---|---|
| Kernel device control | PCI ownership, BAR mapping, interrupts, DMA/IOMMU containment, reset, power transitions, error recovery | PCI, ACPI, firmware loader, IRQ/DMA and power frameworks |
| Display KMD | connectors, DDC/I2C/AUX, EDID, link training, PLLs, pipes/CRTCs, planes, scanout, vblank, hotplug, atomic validation/commit | DRM/KMS core plus helpers and vendor driver |
| Render KMD | GPU VM, buffer objects, mapping, contexts, queues, fences, scheduling, timeouts, preemption and reset | GEM or TTM, DRM scheduler, syncobj/dma-fence, driver-specific uAPI |
| User-mode driver | Vulkan/OpenGL state, command construction, shaders, pipeline cache, device feature exposure | Mesa ANV, RADV, or NVK and their common compiler/runtime code |
| Winsys / WSI | bridge from the UMD to kernel objects, queues, synchronization, presentation and compositor buffers | DRM uAPI, libdrm, dma-buf/sync-file, Wayland/X11/GBM integrations |
| Firmware | authenticated microcode for display, scheduling, media, power or security, with version and redistribution policy | linux-firmware or vendor packages plus kernel loading/authentication |
| Media / compute | separate API runtimes, queue semantics, memory sharing and codec/compute validation | VA-API/media drivers, ROCm, Intel compute-runtime, CUDA and vendor SDKs |

**OFFICIAL FACT:** Linux DRM is not just a collection of register writes. KMS implements shared modesetting objects and atomic commits; DRM’s memory documentation describes GEM and TTM buffer managers and a GPU scheduler with dependency, timeout and recovery semantics ([KMS](https://docs.kernel.org/gpu/drm-kms.html), [DRM memory and scheduler](https://docs.kernel.org/gpu/drm-mm.html)). DRM also exposes device-specific userspace interfaces in addition to common APIs ([DRM uAPI](https://docs.kernel.org/gpu/drm-uapi.html)).

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Mesa’s RADV documentation is unusually explicit: RADV is the UMD, amdgpu is the KMD, RADV’s winsys talks to the KMD through the Linux DRM uAPI, and RADV uses libdrm for part of that communication ([RADV architecture](https://docs.mesa3d.org/drivers/radv.html)). The same architectural constraint applies to ANV/i915 or Xe and NVK/Nouveau even where their documentation is less tutorial-like.

**INFERENCE:** “Port Mesa” is not the first GPU milestone. Malrynth must first define enough of a safe kernel GPU contract to support memory, submission, synchronization, reset and presentation. Copying Linux DRM wholesale is one possible compatibility strategy, but it imports a wide LinuxKPI-style maintenance surface. A small native ABI is a different strategy, but then each Mesa winsys and WSI path must be adapted.

### Stack split by candidate

| Route | Kernel side | User side | Firmware / proprietary boundary | Portability assessment |
|---|---|---|---|---|
| Intel Comet Lake/related Gen9.5 | i915 display, GEM/GGTT/PPGTT, rings, contexts, interrupts, reset; Linux path is DRM/KMS | Mesa Iris/ANV; separate compute-runtime and media-driver | Gen9 DMC plus optional GuC/HuC feature paths; firmware is not host source | Convenient R0-A experiment, still a major port |
| AMD 5600G-era APU | amdgpu IP-block bring-up, TTM/GPUVM, rings, scheduler, DC plus OS-dependent DM | Mesa radeonsi/RADV; separate ROCm and media stack | PSP/SMU and multiple graphics/media/display-related blobs; binary firmware license | Strong open reference, broader bring-up surface |
| NVIDIA OpenRM route | Open GPU kernel modules’ OS-agnostic core plus a new Malrynth kernel interface and modeset integration | Matching NVIDIA UMD would still be proprietary; NVK does not target the RM uAPI upstream | Mandatory GSP firmware and release-matched vendor components | Vendor/version dependent; unsuitable for R0 |
| NVIDIA Nouveau/NVK route | Nouveau or Nova-style Linux DRM KMD, memory, display, GSP interface | Mesa NVK/Zink | Redistributable but closed GSP; incomplete official register documentation | Open userspace, but Linux-coupled and no R0 advantage |

**PROPOSED MALRYNTH DECISION:** support only one native GPU route and one exact device generation at a time. A “vendor-neutral” kernel API may be designed, but implementation work must not start as three concurrent vendor ports.

## Intel: Gen9.5 UHD 630 assessment

### Official openness and documentation

**OFFICIAL FACT:** Intel publishes a public Coffee Lake graphics PRM page for 2017–2019 processors and a broader catalog of Intel graphics programmer references ([Coffee Lake PRM](https://www.intel.com/content/www/us/en/docs/graphics-for-linux/developer-reference/1-0/coffee-lake.html), [hardware-specification catalog](https://www.intel.com/content/www/us/en/docs/graphics-for-linux/developer-reference/1-0/hardware-specs.html)). The Coffee Lake-specific page is principally a configuration volume; older Gen9 manuals and open source remain necessary for the detailed engine, display and workaround picture. Documentation is therefore materially better than no register material, but not a self-contained driver specification.

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux i915 documents memory management, command submission, display and Gen9 microcontrollers. From Gen9 onward the hardware contains GuC, HuC and DMC; i915 loads their firmware. GuC can handle HuC authentication, scheduling and power functions, but the documentation says GuC use is not mandatory on all such platforms and disabling it loses features that require it ([i915 microcontrollers](https://docs.kernel.org/gpu/i915.html)). Mesa documents the hard requirement for GuC as beginning with Alder Lake-P and Arc, not Coffee Lake ([ANV](https://docs.mesa3d.org/drivers/anv.html)).

**INFERENCE:** Coffee Lake evidence is useful for the closely related Gen9.5 programming
model, but the selected Comet Lake device and board require their own PCI ID, VBT/OpRegion,
workaround and firmware validation. A minimal path may defer GuC submission, HuC media and
deep power features. DMC still matters for supported display low-power behavior, so
“firmware optional” must not become “no firmware inventory.”

### Non-Linux evidence

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Haiku’s in-tree native Intel kernel driver and accelerant are a non-DRM design, and its device table contains exact Coffee Lake GT1/GT2/GT3 IDs including 0x3e92, a common UHD 630 ID ([Haiku Coffee Lake device table](https://github.com/haiku/haiku/blob/master/src/add-ons/kernel/drivers/graphics/intel_extreme/driver.cpp#L173-L183), [Haiku Intel accelerant](https://github.com/haiku/haiku/tree/master/src/add-ons/accelerants/intel_extreme)). This is evidence that an independently structured non-Linux display stack can identify and operate in this family; it is not proof of Vulkan or full reliability.

**OFFICIAL FACT:** Redox’s hardware document says only Intel GPUs receive native GPU support while other vendors use BIOS VESA or UEFI GOP ([Redox hardware status](https://github.com/redox-os/redox/blob/master/HARDWARE.md)). The statement does not define which Intel generations or acceleration level, so it is directional evidence only.

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** FreeBSD offers open i915 support, but its upstream DRM repository says plainly that these drivers are ported from Linux with LinuxKPI and that binary firmware is maintained separately ([FreeBSD graphics handbook](https://docs.freebsd.org/en/books/handbook/x11/#x-graphic-card-drivers), [drm-kmod](https://github.com/freebsd/drm-kmod)). This proves feasibility by compatibility-layer porting and exposes the cost of that strategy.

**OFFICIAL FACT:** Khronos’s conformant products list includes Intel UHD Graphics 630 in Intel Vulkan submissions, including a Vulkan 1.4 Linux submission that lists UHD 630 among covered products ([Khronos Vulkan products](https://www.khronos.org/conformance/adopters/conformant-products/vulkan)).

### Functional feasibility

| Capability | Classification | Assessment |
|---|---|---|
| Initialization | **DIFFICULT** | Parse platform VBT/OpRegion information, map MMIO and stolen/aperture memory, establish GGTT/PPGTT policy, power wells, interrupts and safe reset. Firmware-left state can bootstrap display but is not a reset recipe. |
| Basic display | **DIFFICULT, BEST OF THE THREE FOR R0** | One directly wired DisplayPort output, one pipe, one primary plane and one fixed mode are plausible. PLLs, watermarks, DDI link training, hotplug and generation workarounds remain substantial. Defer HDMI level shifters/LSPCON, MST, audio, PSR, FBC, HDCP and suspend. |
| Vulkan | **VERY DIFFICULT BUT CREDIBLE** | ANV supplies compiler and command-generation knowledge. Malrynth still needs buffer allocation, GPU VM, context/queue submission, fences, query/timestamp semantics, reset, a winsys and WSI/presentation. Conformance on Linux does not transfer to a Malrynth port. |
| Compute | **VERY DIFFICULT / LATER** | Intel’s MIT-licensed compute-runtime supports Level Zero/OpenCL and lists Coffee Lake as a legacy Gen9 platform, but it expects its kernel/user infrastructure and dependencies ([compute-runtime](https://github.com/intel/compute-runtime)). Treat it as a separate port after Vulkan isolation and recovery. |
| Video | **VERY DIFFICULT / LATER** | Intel’s media-driver supports Coffee Lake and is MIT/BSD licensed, but uses VA-API, GmmLib and libdrm-oriented integration ([media-driver](https://github.com/intel/media-driver)). The “full feature” packaging includes closed EU shader binaries, whereas the free build has fewer features ([Intel Media SDK explanation](https://github.com/Intel-Media-SDK/MediaSDK/wiki/Intel-media-stack-on-Ubuntu)). HuC authentication adds another firmware boundary. |

**PROPOSED MALRYNTH DECISION:** Intel UHD 630 may be a bounded native-display experiment
after GOP is solid because it is already present. It is not R0 acceptance or a commitment to
Intel-first acceleration; scope it to exact PCI IDs and the Q470E board output topology.

## AMD: Ryzen 5 5600G assessment

### Official openness and documentation

**OFFICIAL FACT:** AMD lists the Ryzen 5 5600G as a 65 W, six-core Ryzen 5000 processor with Radeon graphics, and lists Ryzen 5000 compatibility in its AM4/B550 material ([5600G support page](https://www.amd.com/en/support/downloads/drivers.html/processors/ryzen/ryzen-5000-series/amd-ryzen-5-5600g.html), [AM4 chipset compatibility](https://www.amd.com/en/products/processors/chipsets/am4.html)). Exact motherboard support and GOP behavior remain properties of a board vendor’s BIOS revision.

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** amdgpu models each ASIC as separately versioned IP blocks. The documented set includes PSP security/firmware validation, SMU power management, DCN display, SDMA, graphics/compute, VCN media and scheduling firmware ([amdgpu core](https://docs.kernel.org/gpu/amdgpu/driver-core.html)). This modularity is useful for scoping, but a working APU still needs several blocks brought up in the right order.

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** AMD Display Core is split into OS-agnostic DC, which programs and allocates display hardware resources, and OS-dependent Display Manager, which connects DC to amdgpu and DRM ([AMD Display Core](https://docs.kernel.org/5.15/gpu/amdgpu-dc.html)). Newer documentation also stresses that display-policy calculation is complex and uses DML to avoid underflow or hangs ([DC programming model](https://docs.kernel.org/gpu/amdgpu/display/programming-model-dcn.html)).

**OFFICIAL FACT:** AMD publicly releases shader ISA references and machine-readable ISA descriptions for recent RDNA/CDNA families ([GPUOpen machine-readable ISA](https://gpuopen.com/machine-readable-isa/)). Those are valuable compiler inputs, but 5600G is an older integrated graphics generation and shader ISA documentation is not a complete initialization/display register specification.

### Linux/Mesa dependency and firmware boundary

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** RADV’s own documentation states that it is a userspace Vulkan driver, amdgpu is responsible for PCI/power, display, video memory and ring submission, and the winsys communicates through the Linux DRM uAPI with libdrm and direct calls ([RADV](https://docs.mesa3d.org/drivers/radv.html)).

**OFFICIAL FACT:** The linux-firmware project requires submitted firmware to be royalty-free redistributable, but firmware remains separately licensed source-opaque material ([linux-firmware policy](https://gitlab.com/kernel-firmware/linux-firmware)). AMD’s Radeon firmware license permits redistribution under conditions while forbidding reverse engineering, decompilation and disassembly ([LICENSE.radeon, pinned 20260309 tag](https://gitlab.com/kernel-firmware/linux-firmware/-/blob/20260309/LICENSE.radeon)).

**INFERENCE:** Malrynth can likely redistribute the exact required AMD blobs if it follows their notices and conditions, but it must not characterize those blobs as open source. Firmware names, hashes, originating package/tag, compatible PCI IDs and license text must be part of the hardware manifest.

### Non-Linux evidence

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** FreeBSD’s amdgpu support is the same LinuxKPI porting evidence described above, including a separate binary firmware repository ([drm-kmod](https://github.com/freebsd/drm-kmod)).

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Haiku has an in-tree Radeon HD kernel driver and accelerant, but its device table is centered on much older Radeon generations and does not provide exact 5600G-era native support evidence ([Haiku Radeon HD driver](https://github.com/haiku/haiku/blob/master/src/add-ons/kernel/drivers/graphics/radeon_hd/driver.cpp), [accelerant](https://github.com/haiku/haiku/tree/master/src/add-ons/accelerants/radeon_hd)).

**COMMUNITY EVIDENCE:** A 2026 Haiku discussion records a Ryzen 5 5600G test and explicitly notes that Haiku’s Radeon HD driver does not support modern APU iGPUs, so the machine is using the framebuffer path ([Haiku 5600G report](https://discuss.haiku-os.org/t/do-you-have-a-ryzen-9xxx-or-5xxxg-series-cpu/19177)). An experimental RadeonGfx effort has been discussed, but it is not upstream product evidence.

**OFFICIAL FACT:** Redox states that non-Intel GPU vendors fall back to BIOS VESA or UEFI GOP ([Redox hardware status](https://github.com/redox-os/redox/blob/master/HARDWARE.md)).

### Functional feasibility

| Capability | Classification | Assessment |
|---|---|---|
| Initialization | **VERY DIFFICULT** | VBIOS/ATOM data, PSP-mediated firmware, SMU, memory controller/GPUVM, per-IP firmware, rings, interrupts and reset all precede a trustworthy render stack. Integrated memory removes a discrete VRAM topology but not GPU VM or isolation work. |
| Basic display | **DIFFICULT** | DC is the strongest vendor-neutral seam in this comparison. Malrynth still must replace amdgpu_dm/DRM integration with allocators, locks, timers, interrupts, I2C/AUX, hotplug, atomic state and a scanout contract, and must validate the DML-selected configuration. |
| Vulkan | **VERY DIFFICULT BUT CREDIBLE** | RADV/ACO provide a strong UMD and shader compiler. A Malrynth winsys, KMD ABI, BO/VM/sync/queue implementation, WSI and recovery are mandatory. |
| Compute | **NOT AN R0 COMMITMENT** | Current official Ryzen ROCm 7.2 matrices validate selected Ryzen AI APUs on Ubuntu 24.04.3 and Windows 11; the 5600G is absent, and AMD notes that the entire ROCm stack is not supported on Windows ([Linux matrix](https://rocm.docs.amd.com/projects/radeon-ryzen/en/docs-7.2/docs/compatibility/compatibilityryz/native_linux/native_linux_compatibility.html), [Windows matrix](https://rocm.docs.amd.com/projects/radeon-ryzen/en/docs-7.2/docs/compatibility/compatibilityryz/windows/windows_compatibility.html)). A Malrynth ROCm promise would therefore be speculative. |
| Video | **VERY DIFFICULT / LATER** | VCN queue setup, firmware, buffer formats, codec-specific synchronization and API integration form a separate media stack. “RADV works” would not establish encode/decode support. |

**PROPOSED MALRYNTH DECISION:** keep the 5600G/B550 system as the alternate R0 GOP platform and as a future AMD laboratory. Do not choose AMD as the first native driver solely because DC is OS-agnostic; the exact target’s current non-Linux evidence is framebuffer fallback, not native display or acceleration.

## NVIDIA assessment

### Official openness and boundaries

**OFFICIAL FACT:** NVIDIA publishes open Linux GPU kernel-module source for Turing and newer. Its repository describes a large OS-agnostic source component plus Linux-specific kernel-interface layers, requires GSP firmware, and requires matching user-space NVIDIA components from the corresponding driver release ([open-gpu-kernel-modules](https://github.com/NVIDIA/open-gpu-kernel-modules)). NVIDIA’s published hardware-interface documentation is MIT-licensed but covers selected interfaces, class headers and topics rather than a complete GPU programming manual ([open-gpu-doc](https://github.com/NVIDIA/open-gpu-doc)).

**INFERENCE:** the OS-agnostic source layer is a genuine portability asset. It is not a vendor-supported Malrynth stack, a stable independent GSP ABI, or open NVIDIA Vulkan/CUDA userspace. Porting it still requires Malrynth implementations for kernel memory, threading, locks, timers, interrupts, DMA, VM, display integration and device-file ABI, while retaining a release-coupled binary firmware/userland relationship.

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Mesa NVK is a conformant Vulkan 1.4 implementation for officially supported NVIDIA GPUs and requires at least Linux 6.6 ([NVK](https://docs.mesa3d.org/drivers/nvk.html)). Mesa’s NVK documentation says its knowledge comes from a mixture of NVIDIA’s official headers/open kernel source and reverse-engineered resources ([NVK hardware resources](https://docs.mesa3d.org/drivers/nvk/external_hardware_docs.html)).

**INFERENCE:** NVK proves that an open Vulkan UMD can exist. It does not provide Malrynth with PCI initialization, display, memory management, GSP boot, scheduling, synchronization, reset or a WSI. Upstream NVK’s tested contract is Nouveau/Nova-style Linux infrastructure, not NVIDIA’s proprietary UMD and not a Malrynth ABI.

### Non-Linux evidence

**OFFICIAL FACT:** FreeBSD documents NVIDIA graphics as a proprietary-driver path, in contrast with open Intel and AMD drm-kmod paths ([FreeBSD graphics handbook](https://docs.freebsd.org/en/books/handbook/x11/#x-graphic-card-drivers)).

**COMMUNITY EVIDENCE:** the small X547/nvidia-haiku repository experiments with Turing+ support using NVIDIA GSP/OpenRM source, Mesa NVK and Zink. At access time it has seven commits and is not Haiku upstream ([nvidia-haiku](https://github.com/X547/nvidia-haiku)). This is valuable evidence that NVIDIA’s OS-agnostic/GSP structure can be attacked on another kernel; it is not evidence of production completeness.

**OFFICIAL FACT:** Redox’s documented non-Intel path is VESA/GOP, and Serenity’s current native Intel adapter supports only the old 0x29c2 G35 device while its other in-tree paths are generic or virtual GPUs ([Redox](https://github.com/redox-os/redox/blob/master/HARDWARE.md), [Serenity native Intel source](https://github.com/SerenityOS/serenity/blob/master/Kernel/Devices/GPU/Intel/NativeGraphicsAdapter.cpp#L17-L30)). Neither project supplies authoritative NVIDIA acceleration evidence.

### Functional feasibility

| Capability | Classification | Assessment |
|---|---|---|
| Initialization | **VERY DIFFICULT / FIRMWARE-DEPENDENT** | Turing+ reduces some register reverse engineering by moving management into GSP, but creates a mandatory signed binary, message ABI and version relationship. Pre-Turing cannot use the open module route. |
| Basic display | **VERY DIFFICULT** | Open modeset host source exists, yet published integration is a Linux module stack. GOP framebuffer use is reasonable; native Malrynth modesetting has no R0 benefit over the two iGPU candidates. |
| Vulkan | **VERY DIFFICULT** | NVK is high-quality open UMD evidence, but a compatible KMD and WSI still have to exist. NVIDIA’s production Vulkan UMD is proprietary and release-coupled. |
| Compute | **VENDOR-DEPENDENT** | CUDA userspace and its kernel ABI are not opened by publishing the kernel module. An open-module port does not imply a redistributable Malrynth CUDA stack. |
| Video | **VENDOR-DEPENDENT** | NVIDIA’s current Video Codec SDK requirements name NVIDIA Windows and Linux display drivers (and Jetson Linux), not an independent host interface ([Video Codec SDK requirements](https://developer.nvidia.com/video-codec-sdk)). |

**PROPOSED MALRYNTH DECISION:** do not place an NVIDIA GPU in the reference bill of materials and do not allow it to become the firmware console owner during R0 testing. Later, test it as a secondary, non-boot VGA device only after PCIe hot/reset, IOMMU and multi-GPU ownership policies exist.

## Cross-OS evidence: what it proves and what it does not

| OS/project | Intel | AMD | NVIDIA | Evidence class and lesson |
|---|---|---|---|---|
| FreeBSD | i915kms via drm-kmod | amdgpu/radeonkms via drm-kmod | proprietary NVIDIA packages | **OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux DRM drivers can cross kernels through a substantial LinuxKPI layer; binary firmware remains separate. This validates a strategy, not a low port cost. |
| Haiku upstream | Native kernel-driver/accelerant split; exact Coffee Lake IDs present | Native Radeon HD code for older hardware; no exact modern 5600G path | no upstream modern NVIDIA stack | **OPEN-SOURCE IMPLEMENTATION EVIDENCE:** a non-DRM graphics architecture is possible. Exact device IDs and generation depth matter more than vendor names. |
| Haiku community | Coffee Lake exists in upstream table | 5600G report uses framebuffer; RadeonGfx is experimental | small Turing+ OpenRM/GSP/NVK experiment | **COMMUNITY EVIDENCE:** modern AMD/NVIDIA paths are research projects, not deployable precedents. |
| Redox | project says Intel-only native GPU support | VESA/GOP fallback | VESA/GOP fallback | **OFFICIAL FACT:** another independent OS converged on Intel first and firmware framebuffer elsewhere. Generation and acceleration scope remain unspecified. |
| Serenity | native source currently limited to Intel G35; generic/virtual framebuffer paths | no current native target evidence | no current native target evidence | **OPEN-SOURCE IMPLEMENTATION EVIDENCE:** this is not evidence for modern Intel; it is evidence that framebuffer/virtual paths precede modern physical acceleration. |

**INFERENCE:** no cited independent OS demonstrates a small, modern, production-quality, native Vulkan stack for all three desktop vendors. FreeBSD succeeds by tracking Linux DRM. Haiku’s exact Coffee Lake recognition is the strongest target-specific non-Linux evidence here, but still falls far short of a Malrynth ANV promise.

## Staged Malrynth graphics plan

### Stage 0 — qualify firmware and freeze the hand-off

**PROPOSED MALRYNTH DECISION:**

- Require pure UEFI boot with CSM disabled and a working GOP mode on the motherboard’s integrated output.
- Before ExitBootServices, record GOP mode number, horizontal/vertical resolution, pixels per scan line, framebuffer physical base and size, pixel format/masks, EDID if separately acquired, PCI BDF/vendor/device/subsystem IDs, selected primary display and firmware revision.
- Preserve the final UEFI memory map and reserve the framebuffer aperture from the physical allocator.
- Do not call GOP or any other boot service after ExitBootServices.
- Validate both R0 systems at 1920×1080×32 first; larger modes are optional until cache and bandwidth behavior is measured.
- Keep serial logging authoritative before and after framebuffer activation.

**Go gate:** cold boot, warm reboot and repeated ExitBootServices hand-offs leave a stable visible image and a correctly bounded, reserved aperture on the exact pinned BIOS version.

### Stage 1 — kernel-owned linear framebuffer and CPU compositor

**PROPOSED MALRYNTH DECISION:**

- Implement bounds-checked pixel access, fill, glyph, scrolling, dirty rectangles, panic output and an emergency single-buffer console over the captured GOP memory.
- Measure uncacheable and write-combining mappings; never assume ordinary cached RAM semantics for a PCI/firmware framebuffer.
- Add damage tracking and a CPU compositor without page flips. The scanout mode remains firmware-owned.
- Detect stride overflow, invalid masks, unsupported pixel formats, framebuffer wrap and memory-map overlap. Fall back to serial rather than guessing.
- Treat blanking after reset, suspend or firmware changes as expected limitations, not as native display bugs.

**Go gate:** deterministic console/compositor output for 24-hour stress, panic rendering under memory pressure, and no writes outside the recorded framebuffer.

### Stage 2 — bounded native display experiment: Intel UHD 630

**PROPOSED MALRYNTH DECISION:**

- Freeze one Q470E board, one Comet Lake UHD 630 PCI ID, one direct display connector, one monitor/EDID and one safe 60 Hz mode.
- Implement probe/ownership, MMIO, VBT/OpRegion extraction, power-well prerequisites, one DDI link, one PLL, one pipe/transcoder, one primary plane, vblank interrupt and deterministic display-engine reset.
- Initially reuse the firmware scanout allocation or a physically controlled replacement. Do not expose user command submission.
- Load only firmware shown necessary by the selected path and record its hash/license. Defer GuC scheduling, HuC, media, PSR, FBC, deep RC states, audio, HDCP, MST, HDMI 2.0/LSPCON, multiple pipes, suspend and hot-unplug races.
- Preserve the GOP framebuffer driver as a separately selectable recovery path.

**Go gate:** native re-modeset after deliberate display reset, stable vblank, EDID validation, no underflow for the fixed mode, and recovery to serial/GOP policy after any failure.

### Stage 3 — protected render submission and basic acceleration

**PROPOSED MALRYNTH DECISION:**

- Add buffer objects, pinned scanout buffers, GGTT/PPGTT mappings, per-process address spaces/contexts, one render queue, fences, bounded waits, interrupt completion, timeouts and full GT reset.
- Define a small versioned Malrynth GPU uAPI. It must identify devices/features, allocate/map objects, create/destroy contexts, submit, wait and report reset/device loss.
- Require IOMMU/DMA containment, overflow-safe command/buffer validation, per-client accounting and cleanup on process death before untrusted clients.
- Start with trusted test commands or a blit/copy path; do not make “triangle rendered” the safety gate.

**Go gate:** intentional invalid submissions and hangs cannot corrupt kernel memory, escape assigned mappings, wedge the display permanently or block another client indefinitely.

### Stage 4 — ANV port, Vulkan WSI and compositor

**PROPOSED MALRYNTH DECISION:**

- Reuse Mesa’s compiler, NIR and ANV hardware logic only after a license/file review; implement a Malrynth winsys against the Stage 3 uAPI.
- Add Vulkan loader integration, device/lost semantics, synchronization, pipeline cache storage and a WSI that presents into compositor-owned scanout images.
- Establish an explicit buffer-sharing and fence contract between UMD and compositor; do not reproduce dma-buf implicitly without defining ownership and lifetime.
- Validate headless Vulkan first, then off-screen rendering, then a trusted fullscreen present path, then the compositor.
- Run the Vulkan CTS appropriate to the claimed version. Until a conformant submission is achieved, call the result experimental and do not use the Vulkan trademark as a conformance claim.

**Go gate:** repeatable CTS target, fault isolation, reset recovery, leak-free buffer lifetimes and a compositor that survives client termination and device loss.

### Stage 5 — later vendor and feature expansion

**PROPOSED MALRYNTH DECISION:**

1. Select one AMD generation for the first committed acceleration program; the exact 5600G
   APU is not mandatory if a discrete generation has better documentation/reset/isolation.
   Reuse lessons from any bounded Intel experiment, but do not make AMD wait on an Intel port.
2. Treat compute and video as independent projects with independent firmware, APIs and validation.
3. Add NVIDIA only as a secondary adapter and first decide between the OpenRM/GSP/vendor-UMD route and Nouveau/NVK; mixing the two without an ABI decision is not a plan.
4. Consider a LinuxKPI/DRM compatibility domain only after comparing its imported surface and update burden with a native winsys port.

## R0 hardware implications

### R0-A: Q470E + Comet Lake-S + UHD 630

**PROPOSED MALRYNTH DECISION:** confirm the R0-A recommendation, with the following procurement gates:

- The CPU must actually include UHD 630; exclude Intel F-suffix parts and verify the exact device ID.
- The board must expose the iGPU through a directly wired, documented output. Prefer native
  DP where the exact board offers it; avoid making an opaque converter the only path.
- UEFI must provide GOP with CSM disabled. Pin the exact image/hash after validation;
  “Q470E” alone does not guarantee equivalent GOP behavior.
- Capture VBT/OpRegion and output routing in the hardware record. A generic Gen9.5 driver
  cannot infer board connector wiring safely.
- Record BIOS graphics-memory/DVMT settings and test defaults plus the chosen pinned value.
- Keep a motherboard serial path or approved debug adapter available. Native display failure must never remove the primary diagnostic channel.
- R0 acceptance requires only GOP framebuffer. Native Intel display is a post-R0 experiment, and Vulkan/compute/video are later claims.

**INFERENCE:** the homogeneous 10th-generation CPU choice keeps the wider platform simple.
The GPU-specific reason is only reliable GOP plus mature Gen9.5 documentation/implementation
evidence; related Coffee Lake non-Linux evidence is informative, not an exact-device proof.

### R0-B: B550 + Ryzen 5 5600G

**PROPOSED MALRYNTH DECISION:** retain R0-B as a valuable independent firmware/platform alternate, with these limits:

- Require an exact board BIOS that recognizes the 5600G, enables the iGPU and supplies GOP on a tested motherboard output. Pin the image/hash; early B550 firmware support varied by board history.
- Prefer a direct DP output and record the exact connector topology and GOP mode.
- The 5600G is PCIe Gen3 even though B550 marketing emphasizes PCIe Gen4; do not base expansion expectations on chipset branding alone ([AMD 5600G specifications](https://www.amd.com/en/support/downloads/drivers.html/processors/ryzen/ryzen-5000-series/amd-ryzen-5-5600g.html)).
- For any native experiment, inventory every required amdgpu firmware blob by filename, source tag, hash and license before loading it.
- Do not make ROCm, VCN video or RADV part of the R0-B contract. Current independent evidence supports the firmware framebuffer path.

### NVIDIA expansion

**PROPOSED MALRYNTH DECISION:** leave the reference PCIe slot electrically available but ship/test R0 without an NVIDIA adapter. A later expansion card must not become primary VGA/GOP during baseline tests, must have a documented reset path, and must operate behind established IOMMU and multi-GPU ownership policy.

## Licensing and redistribution controls

**OFFICIAL FACT:** the Linux kernel as a whole is GPL-2.0-only with its syscall note, while individual files can carry compatible or dual permissive SPDX expressions; the exact file controls reuse ([Linux licensing rules](https://docs.kernel.org/process/license-rules.html)). Mesa says most code is MIT but individual files can differ ([Mesa license](https://docs.mesa3d.org/license.html)).

**INFERENCE:** repository-level slogans are insufficient for a Malrynth import. Any code reuse review must record the precise file, commit, SPDX expression, modifications and attribution. Architecture study does not create permission to paste GPL-only implementation into a differently licensed kernel.

**PROPOSED MALRYNTH DECISION:**

- Keep host driver source, UAPI headers, firmware blobs, compiler code and test assets as separate ledger categories.
- Prefer permissively licensed UMD/compiler components and cleanly designed interfaces. Escalate GPL-only kernel-source reuse for an explicit project licensing decision before implementation.
- Package firmware separately from the kernel where practical, retaining vendor notices and source/version provenance.
- Do not modify, disassemble or reverse engineer AMD firmware under the cited redistribution license; do not imply that redistributable binary means modifiable.
- For NVIDIA, track the license of open host source separately from GSP firmware and proprietary userspace. All must be compatible with the intended distribution.
- Treat patents, codec licensing and protected-content systems as separate legal work; source-code license review alone does not clear video codec distribution.

## Decision gates and stop conditions

| Gate | Proceed when | Stop / rescope when |
|---|---|---|
| R0 GOP | exact board/BIOS survives repeated boots and framebuffer reservation | GOP disappears with CSM off, buffer overlaps RAM, mode is unusable, or output requires an opaque bridge with unstable firmware |
| Intel native display | fixed DP mode can be reconstructed and reset with documented firmware inventory | only firmware-left state works, display reset is nondeterministic, underflow persists, or necessary board routing data is unavailable |
| Render KMD | VM, fences, timeout and reset are safe under hostile tests | command submission can DMA outside owned memory, reset loses display, or firmware ABI cannot be pinned |
| Vulkan | winsys/WSI survives device loss and CTS target is defined | port requires an accidental Linux ABI clone without an accepted maintenance plan |
| AMD follow-on | exact APU/board firmware set is redistributable and DC/DM boundary can be staffed | “support AMD” expands beyond one ASIC/board or depends on unsupported ROCm assumptions |
| NVIDIA follow-on | route, GSP version policy and UMD choice are explicit | open kernel source is mistaken for open Vulkan/CUDA/video, or vendor release lock cannot be maintained |

## Bottom line

**PROPOSED MALRYNTH DECISION:** R0 ships a graphics architecture, not a modern GPU promise:
UEFI GOP capture, kernel-owned linear framebuffer, CPU console/compositor, serial authority
and a versioned future GPU boundary. Comet Lake UHD 630 can host a bounded display experiment;
AMD is the preferred first committed acceleration family; NVIDIA remains expansion-only.

The two rankings answer different questions. Intel/Q470E is the safer controlled *machine*
because its iGPU supplies GOP without another device. AMD ranks first for a future native
*acceleration program* because amdgpu/DC/RADV provide the strongest broad open reference.
Neither path is short, and no Vulkan conformance result transfers to Malrynth.

## Recommended integration

Integrate only the staged GOP-to-native-display gates, kernel/user/firmware ownership split, and stop conditions after the graphics architecture pass is complete. Do not record Intel, AMD, NVIDIA, Vulkan, compute, or video as supported based on this feasibility ranking.

## Source ledger contributions

All entries were accessed on 2026-08-19. “Licensing relevance” is an engineering flag, not legal advice.

| Authority | Accessed | Claim contributed | URL | Licensing relevance |
|---|---|---|---|---|
| UEFI Forum, official specification | 2026-08-19 | GOP mode/framebuffer contract and boot-service lifetime | [UEFI GOP](https://uefi.org/specs/UEFI/2.10/12_Protocols_Console_Support.html#graphics-output-protocol) and [UEFI 2.11 system table](https://uefi.org/specs/UEFI/2.11/04_EFI_System_Table.html) | Specification terms; no GPU firmware/source grant |
| Linux kernel documentation | 2026-08-19 | KMS atomic display objects/helpers | [DRM KMS](https://docs.kernel.org/gpu/drm-kms.html) | Kernel-wide/file-level GPL/SPDX review required for reuse |
| Linux kernel documentation | 2026-08-19 | GEM/TTM and GPU scheduler are substantive shared infrastructure | [DRM memory management](https://docs.kernel.org/gpu/drm-mm.html) | Demonstrates imported compatibility surface; exact files control license |
| Linux kernel documentation | 2026-08-19 | i915 Gen9 GuC/HuC/DMC roles and firmware loading | [i915](https://docs.kernel.org/gpu/i915.html) | Host files vary by SPDX; firmware separate |
| Intel, official PRM catalog | 2026-08-19 | Public Coffee Lake configuration material and broader Gen9 references | [Coffee Lake](https://www.intel.com/content/www/us/en/docs/graphics-for-linux/developer-reference/1-0/coffee-lake.html) | Documentation availability is not source/firmware licensing |
| Mesa upstream documentation | 2026-08-19 | ANV GuC requirement begins with Alder Lake-P/Arc | [ANV](https://docs.mesa3d.org/drivers/anv.html) | Mesa mostly MIT; per-file audit |
| Khronos Group conformant-products registry | 2026-08-19 | UHD 630 appears in conformant Vulkan submissions | [Vulkan products](https://www.khronos.org/conformance/adopters/conformant-products/vulkan) | Conformance/trademark claim applies to tested implementation, not a port |
| Intel open-source project | 2026-08-19 | Coffee Lake legacy Level Zero/OpenCL runtime and MIT license | [compute-runtime](https://github.com/intel/compute-runtime) | MIT host code; dependencies and kernel ABI separate |
| Intel open-source project | 2026-08-19 | Coffee Lake media support, VA-API stack, MIT/BSD licensing | [media-driver](https://github.com/intel/media-driver) | Free/full-feature distinction and binary shaders need separate review |
| Haiku upstream source | 2026-08-19 | Exact Coffee Lake IDs in a native non-DRM driver/accelerant design | [intel_extreme device table](https://github.com/haiku/haiku/blob/master/src/add-ons/kernel/drivers/graphics/intel_extreme/driver.cpp#L173-L183) | Haiku source is MIT-licensed; attribution/per-file notices still apply |
| AMD, official product material | 2026-08-19 | 5600G has integrated Radeon graphics; AM4/B550 family fit | [5600G](https://www.amd.com/en/support/downloads/drivers.html/processors/ryzen/ryzen-5000-series/amd-ryzen-5-5600g.html) and [AM4](https://www.amd.com/en/products/processors/chipsets/am4.html) | Product facts only |
| Linux AMDGPU documentation | 2026-08-19 | AMD IP-block architecture, PSP/SMU/DCN/SDMA/GC/VCN roles | [amdgpu core](https://docs.kernel.org/gpu/amdgpu/driver-core.html) | Kernel source needs file-level SPDX review; firmware separate |
| Linux AMDGPU documentation | 2026-08-19 | DC is OS-agnostic and DM is OS-dependent/DRM-facing | [AMD Display Core](https://docs.kernel.org/5.15/gpu/amdgpu-dc.html) | Attractive seam; imported source license must be audited |
| Mesa upstream documentation | 2026-08-19 | RADV KMD/UMD split and dependency on amdgpu DRM uAPI/libdrm | [RADV](https://docs.mesa3d.org/drivers/radv.html) | Mesa mostly MIT; Linux uAPI and libdrm pieces separately inventoried |
| AMD GPUOpen | 2026-08-19 | Official public machine-readable shader ISA resources | [Machine-readable ISA](https://gpuopen.com/machine-readable-isa/) | Documentation/tool package terms must be checked; not a display spec |
| AMD ROCm documentation | 2026-08-19 | Current Ryzen APU validation excludes 5600G and names Linux/Windows scope | [Linux](https://rocm.docs.amd.com/projects/radeon-ryzen/en/docs-7.2/docs/compatibility/compatibilityryz/native_linux/native_linux_compatibility.html) and [Windows](https://rocm.docs.amd.com/projects/radeon-ryzen/en/docs-7.2/docs/compatibility/compatibilityryz/windows/windows_compatibility.html) | Prevents unsupported compute commitment; component licenses still vary |
| linux-firmware upstream | 2026-08-19 | Firmware repository requires redistributability and clear license provenance | [linux-firmware](https://kernel.googlesource.com/pub/scm/linux/kernel/git/firmware/linux-firmware) | Redistribution is not source availability |
| AMD firmware license in linux-firmware | 2026-08-19 | Radeon blob redistribution conditions and reverse-engineering prohibition | [LICENSE.radeon, pinned 20260309 tag](https://gitlab.com/kernel-firmware/linux-firmware/-/blob/20260309/LICENSE.radeon) | Must retain terms/notices and avoid prohibited acts |
| NVIDIA official open-source project | 2026-08-19 | Turing+ open Linux modules, OS-agnostic core, Linux KIL, GSP and matching UMD | [open-gpu-kernel-modules](https://github.com/NVIDIA/open-gpu-kernel-modules) | Open host code does not license GSP or proprietary UMD as source |
| NVIDIA official documentation repository | 2026-08-19 | Selected public hardware interfaces under MIT | [open-gpu-doc](https://github.com/NVIDIA/open-gpu-doc) | MIT documentation; incomplete coverage is an engineering limitation |
| Mesa upstream documentation | 2026-08-19 | NVK Vulkan 1.4 conformance and Linux 6.6 minimum | [NVK](https://docs.mesa3d.org/drivers/nvk.html) | Mesa per-file license; conformance does not transfer to Malrynth |
| FreeBSD Project handbook | 2026-08-19 | Intel/AMD open drm-kmod paths; NVIDIA proprietary path | [FreeBSD graphics](https://docs.freebsd.org/en/books/handbook/x11/#x-graphic-card-drivers) | Separates open host paths from proprietary NVIDIA packaging |
| FreeBSD drm-kmod upstream | 2026-08-19 | LinuxKPI port strategy and separate binary firmware repository | [drm-kmod](https://github.com/freebsd/drm-kmod) | Demonstrates mixed BSD/GPL/MIT and firmware compliance surface |
| Haiku upstream source | 2026-08-19 | Native Radeon driver exists but provides no exact modern 5600G evidence | [radeon_hd](https://github.com/haiku/haiku/blob/master/src/add-ons/kernel/drivers/graphics/radeon_hd/driver.cpp) | Haiku MIT source; absence is evidence only at accessed revision |
| Haiku community | 2026-08-19 | Actual 5600G report uses framebuffer because modern APU iGPU is unsupported | [Haiku 5600G discussion](https://discuss.haiku-os.org/t/do-you-have-a-ryzen-9xxx-or-5xxxg-series-cpu/19177) | Community evidence only; no license grant beyond linked content |
| X547 community repository | 2026-08-19 | Experimental Haiku Turing+ OpenRM/GSP/NVK/Zink route | [nvidia-haiku](https://github.com/X547/nvidia-haiku) | Repository says MIT unless otherwise noted; submodules/firmware retain own terms |
| Redox OS upstream | 2026-08-19 | Intel-only native GPU statement; AMD/NVIDIA use VESA/GOP | [HARDWARE.md](https://github.com/redox-os/redox/blob/master/HARDWARE.md) | Project evidence, not imported source |
| SerenityOS upstream source | 2026-08-19 | Native Intel driver is currently limited to G35 ID 0x29c2 | [NativeGraphicsAdapter.cpp](https://github.com/SerenityOS/serenity/blob/master/Kernel/Devices/GPU/Intel/NativeGraphicsAdapter.cpp#L17-L30) | BSD-2-Clause project; exact files still need notice review |
| Mesa Project | 2026-08-19 | Mesa is mostly MIT with per-file exceptions | [Mesa license](https://docs.mesa3d.org/license.html) | Requires file-level license inventory |
| Linux kernel project | 2026-08-19 | Kernel-wide GPL-2.0 and file-level SPDX/dual-license rules | [Linux licensing rules](https://docs.kernel.org/process/license-rules.html) | Controls whether implementation source may be reused in Malrynth |
