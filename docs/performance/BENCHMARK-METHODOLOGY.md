# Benchmark Methodology

**Status:** DRAFT.

A number without a method is not a measurement. This document fixes the method so results
are comparable across months and machines.

## Requirements

1. **State the environment completely:** machine, CPU model, memory, storage, firmware
   version, QEMU version, accelerator (KVM/TCG), Malrynth commit, build profile.
2. **Distinguish emulated from native.** QEMU+TCG numbers measure the emulator. They are
   valid for *relative* comparison between Malrynth revisions on identical configurations and
   are **never** reported as Malrynth's performance.
3. **Report p50, p95, p99 and max**, with the sample count. Means alone are prohibited.
4. **Warm up, then measure.** State both, separately.
5. **Fix the frequency governor** and disable turbo where the platform allows; otherwise
   record that it could not be fixed.
6. **Repeat across boots.** Single-boot numbers hide layout- and firmware-dependent variance.
7. **Record the raw data**, not just the summary. A summary that cannot be re-derived cannot
   be audited.

## Comparisons with other systems

Permitted only when the workload is genuinely equivalent and the configuration is disclosed
in full. An unfair comparison in Malrynth's favour is worse than no comparison: it
misinforms our own engineering decisions first.

## Regression tracking

Each metric records: value, unit, commit, date, environment ID, and method version. A change
of method **increments the method version** and invalidates comparison with earlier data.
Silently changing how a metric is gathered and continuing the same series is the most common
way performance tracking becomes fiction.

## M0 status

Only image sizes are measured (`tools/build` → `build/size-report.txt`), and they are
deterministic properties of the build rather than timing measurements, so they need no
statistical treatment. Timing instrumentation begins in M1 with the timer subsystem.
