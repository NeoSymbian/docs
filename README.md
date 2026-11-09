# NeoSymbian docs

NeoSymbian brings the open-source 2010 Symbian (EKA2, the Symbian^3 release) back to modern hardware:

- **First target:** the Google Pixel 3a XL (bonito, Qualcomm SDM670).
- **Kernel:** ported to AArch64 with 32-bit pointers (ILP32).
- **User side:** the 2010 Symbian user side runs unchanged in 32-bit mode at AArch32 EL0.
- **UI:** a new touch UI written in Rust.

## Documents

| Document | What |
|---|---|
| [roadmap.md](roadmap.md) | Plan and status: kernel (K), hardware (H), UI (U) and phone (P) tracks |
| [rust-integration.md](rust-integration.md) | Rust on the Symbian user side: stages R0–R8 |
| [smooth-ui.md](smooth-ui.md) | Making the UI smooth (60 fps): why it isn't yet, and stages S1–S6 |
| [neoui-shell.md](neoui-shell.md) | Shell services design: settings store, notifications, home pages, widgets (planned) |
| [port-map.md](port-map.md) | How EKA2 maps onto AArch64: what was reused, adapted and written new |
| [ekern-backend.md](ekern-backend.md) | The full kernel's AArch64 backend |
| [filesystem.md](filesystem.md) | File system plan: drives, flash layout, stages FS1–FS6 |
| [telephony.md](telephony.md) | Cellular calls, SMS and data: the end-to-end runbook, stages C0–C12 |
| [devices.md](devices.md) | Which phones could be next: requirements, a shortlist from the mobile Linux lists, what each reuses |
| [known-issues.md](known-issues.md) | Open problems and their workarounds |
| [sources.md](sources.md) | Survey of the source repositories and licences |
| [retired-repos.md](retired-repos.md) | The 91 repositories deleted on 2026-11-06, and how to bring one back |

## Repositories

Everything lives in the [NeoSymbian](https://github.com/NeoSymbian) organization. Nothing is pushed back to the
original projects.

| Repository | What |
|---|---|
| [kernel](https://github.com/NeoSymbian/kernel) | The EKA2 kernel (the SymbianSource kernelhwsrv fork) with the AArch64 port, drivers and boards (`baseport/arm64`) |
| [build](https://github.com/NeoSymbian/build) | The build system: `neo`, the build image (`ghcr.io/neosymbian/toolchain`), the pinned sources, the 2010 ROM |
| [e32-rs](https://github.com/NeoSymbian/e32-rs) | Rust crates for the Symbian user side |
| [neoui](https://github.com/NeoSymbian/neoui) | The Rust UI server and apps |
| [telephony](https://github.com/NeoSymbian/telephony) | The cellular modem's user side in Rust: QRTR, QMI, rmtfs, call audio, the modem server ([telephony.md](telephony.md)) |
| [symbian-qemu](https://github.com/NeoSymbian/symbian-qemu) | The Syborg board package (the adapt.Qemu fork): the baseport, QEMU 11.1 with the Syborg board in C, `run-syborg` (`ghcr.io/neosymbian/symbian-qemu`) |
| `oss.*` | The SymbianSource packages the build pins (`build/sources.lock`), forked as they are |

## Where the port's files went

These documents were written in `symbian-pixel` (now archived), so their paths are the old ones. Since 2026-11-06
the code lives in NeoSymbian/kernel:

| Old path (symbian-pixel) | New path (kernel) |
|---|---|
| `port/arm64/a64smp/`, `platform/`, `board/gicv3.*`, `boot/vectors.S` | `kernel/eka/nkernsmp/arm64/`, `kernel/eka/include/nkernsmp/arm64/` |
| `port/arm64/ekern/`, `boot/` | `kernel/eka/kernel/arm64/`, `kernel/eka/include/kernel/arm64/` |
| `port/arm64/mm/` | `kernel/eka/memmodel/epoc/flexible/{arm64,mmu/arm64}/` |
| `port/arm64/prelude/` | `kernel/eka/include/nkern/arm64/` |
| `port/arm64/nksa/` | `kerneltest/e32test/nkernsa/arm64/` |
| `port/arm64/board/`, `probes/` | `baseport/arm64/{common,virt_assp,sdm670_assp,qemu_variant,bonito_variant}/` |
| `port/arm64/tools/` | `baseport/arm64/tools/` |
| `zimaos/` | NeoSymbian/build `zimaos/` (the `a64dev` image is now `docker/toolchain`) |

The copies of `execs.h`, `u32exec.h`, `mmtypes.h` and `mpdalloc.cpp` are now `__CPU_ARM64` sections of the
originals, and the build-time `sed` patches are commits on the kernel's `main`.

## Licence

These documents are Apache-2.0 (`LICENSE`).
