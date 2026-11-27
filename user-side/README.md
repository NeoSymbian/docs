<!-- SPDX-License-Identifier: Apache-2.0 -->
# User side

Part of [the docs](../README.md) · Status: active · Updated: 2026-11-26

The 2010 Symbian user side, running unchanged in 32-bit mode at AArch32 EL0 above our AArch64 kernel: how it was
rebuilt as one SMP-safe ARMv8-A flavour, Rust on it (the `e32` crates in e32-rs and every Rust EXE built on them), and
old S60 apps running inside neoui. The kernel is in [../kernel/README.md](../kernel/README.md), the UI shell in
[../neoui-shell/README.md](../neoui-shell/README.md).

## Rules in force

The full text is in the workspace `CLAUDE.md` ("ABI rules"); each rule links to where it was decided.

- **One flavour: ARMv8-A AArch32, soft-float calling convention.** No ARMv5/v6/v7 builds and no 64-bit user side
  ([what "modern" means](user-side-smp.md#what-modern-means-here), [the 64-bit study](user-side-smp.md#parked-a-64-bit-user-side)).
  C++ goes through build's `toolchain/symcc` ([US3](user-side-smp.md#us3-results-2026-11-22)); only the GNU helpers
  libgcc/libsupc++ stay ARMv5TE. Old S60 apps (ARMv5/v6 binaries) run unchanged.
- **Never an `eabihf` target:** it passes floats in VFP registers and breaks every call into a Symbian library
  ([Rust now](rust-integration.md#rust-on-the-user-side-now)).
- **TRAP in code built with VFP** goes through the overlay macros to euser's `NeoTrapFp`, which keeps `d8`–`d15`
  across a leave; never expand a TRAP by hand ([US3: FP registers across a leave](user-side-smp.md#us3-results-2026-11-22),
  [why](user-side-smp.md#us2-what-to-fix-first)).
- **Atomics and locks:** LDREX/STREX with DMB (SMP semantics); Rust has native ARMv8 atomics and `Arc` since US4, and
  `e32::sync::Mutex` and the heap are kernel mutexes that refuse re-entry ([US4](user-side-smp.md#us4-results-2026-11-25)).
  LDA/STL are not used ([ARMv8 profile](user-side-smp.md#armv8-profile-results-2026-11-26)). Never the
  `EFastExecFastAtomic*` exec calls: this kernel lacks them.
- **Exec numbers** come from e32-rs `e32-sys/src/execs.rs`, generated from the kernel's `execs.txt`
  ([Rust now](rust-integration.md#rust-on-the-user-side-now)).
- **Rust EXEs go in the ROM by default; `drive=c` puts them on C:.** ROM EXEs get every capability and 8.3 names,
  `drive=c` ones no capabilities ([Rust now](rust-integration.md#rust-on-the-user-side-now)).

## Documents

| Doc | What | Status |
|---|---|---|
| [user-side-smp.md](user-side-smp.md) | The user side made SMP-safe and rebuilt as one ARMv8-A AArch32 flavour, with each stage's results | done |
| [rust-integration.md](rust-integration.md) | Rust on the user side: the crates, the target, how a Rust EXE gets into the ROM, the kernel calls neoui uses | done |
| [legacy.md](legacy.md) | Old S60 apps inside neoui: the guest window server, LEGACY.EXE, key pads | active |
| [history/rust-stages.md](history/rust-stages.md) | The record of each Rust stage as it landed, 2026-11-06 to 2026-11-12 | record |
