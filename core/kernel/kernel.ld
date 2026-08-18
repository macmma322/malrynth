/* Malrynth kernel linker script -- M0.
 *
 * M0 runs identity-mapped under the page tables UEFI leaves in place, so the kernel is
 * linked at a fixed PHYSICAL address that malboot requests explicitly from the firmware.
 * This address must equal malrynth_abi::KERNEL_PHYS_BASE; the kernel asserts this at
 * runtime and refuses to continue if they disagree.
 *
 * M1 replaces this with a higher-half layout at 0xFFFF_FFFF_8000_0000 once Malrynth builds
 * its own page tables. Sections are page-aligned so each becomes its own PT_LOAD segment
 * and can later be mapped with distinct permissions (W^X).
 */

ENTRY(_start)

KERNEL_PHYS_BASE = 0x10000000;

PHDRS
{
    text   PT_LOAD FLAGS(5);  /* R-X */
    rodata PT_LOAD FLAGS(4);  /* R-- */
    data   PT_LOAD FLAGS(6);  /* RW- */
}

SECTIONS
{
    . = KERNEL_PHYS_BASE;

    __kernel_start = .;

    .text ALIGN(4K) : { *(.text.entry) *(.text .text.*) } :text

    .rodata ALIGN(4K) : { *(.rodata .rodata.*) } :rodata

    .data ALIGN(4K) : { *(.data .data.*) } :data

    .bss ALIGN(4K) : {
        __bss_start = .;
        *(.bss .bss.*)
        *(COMMON)
        __bss_end = .;
    } :data

    __kernel_end = .;

    /* Discard host/unwinding metadata that has no meaning in a freestanding kernel. */
    /DISCARD/ : { *(.eh_frame) *(.eh_frame_hdr) *(.note .note.*) *(.comment) }
}
