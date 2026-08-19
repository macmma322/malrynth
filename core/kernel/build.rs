//! Applies the Malrynth kernel linker script.
//!
//! The script is passed by absolute path derived from `CARGO_MANIFEST_DIR` so the build
//! works regardless of the directory cargo is invoked from.

fn main() {
    let manifest_dir =
        std::env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR is always set by cargo");
    println!("cargo::rustc-link-arg=-T{manifest_dir}/kernel.ld");
    println!("cargo::rustc-link-arg=--gc-sections");
    println!("cargo::rustc-link-arg=--no-pie");
    println!("cargo::rerun-if-changed=kernel.ld");
}
