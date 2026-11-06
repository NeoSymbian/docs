# symbian-pixel

Symbian's EKA2 kernel, the 2010 open-source Symbian^3 release, ported to **64-bit ARM (AArch64)** and running on a
**Google Pixel 3a XL** (Qualcomm SDM670, 8 cores).

The long-term goal is a daily phone: the 2010 Symbian user side running unchanged in 32-bit mode, under a new touch UI
written in Rust. See the [roadmap](docs/roadmap.md).

## Status (2026-11)

- The 2010 **SMP nanokernel** boots on QEMU `virt` and on the **real phone**. It runs on all 8 cores, with GICv3,
  generic-timer timeslicing, PSCI to start the other cores, and SMP load balancing.
- The standalone nanokernel test suite (**nkernsa**) completes on the phone with a few timing failures left. Results
  show on the screen through a text console drawn into the bootloader's framebuffer.
- Next: the full kernel (`ekern`), then booting the Symbian user side to a shell. See
  [roadmap stages M1–M3](docs/roadmap.md#track-k-kernel).

## Where the code went (2026-11-06)

The AArch64 port and the board support moved into the kernel repository, [**NeoSymbian/kernel**](https://github.com/NeoSymbian/kernel)
(the kernelhwsrv fork, renamed), with their history. They sit next to Symbian's own `arm/` and `x86/` folders, and
the boards are in `baseport/arm64` ([README](https://github.com/NeoSymbian/kernel/tree/main/baseport/arm64)):

| Was here | Now in NeoSymbian/kernel |
|---|---|
| `port/arm64/a64smp/`, `platform/`, `board/gicv3.*`, `boot/vectors.S` | `kernel/eka/nkernsmp/arm64/`, `kernel/eka/include/nkernsmp/arm64/` |
| `port/arm64/ekern/`, `boot/` | `kernel/eka/kernel/arm64/`, `kernel/eka/include/kernel/arm64/` |
| `port/arm64/mm/` | `kernel/eka/memmodel/epoc/flexible/{arm64,mmu/arm64}/` |
| `port/arm64/nksa/` | `kerneltest/e32test/nkernsa/arm64/` |
| `port/arm64/board/` (all other files), `probes/` | `baseport/arm64/{common,virt_assp,sdm670_assp,qemu_variant,bonito_variant}/` |
| `port/arm64/tools/` | `baseport/arm64/tools/` |

The build-time `sed` patches to 2010 files are now ordinary commits on the kernel's `main`. This repository still
holds the docs and the ZimaOS build environment until they move too.

## Repositories

Everything the build uses is forked into the [**neosymbian**](https://github.com/neosymbian) organization. Nothing is
pushed back to the original projects.

| Repository | Forked from | Role |
|---|---|---|
| `kernel` (was `oss.FCL.sf.os.kernelhwsrv`) | [SymbianSource](https://github.com/SymbianSource) | The EKA2 kernel with the arm64 port, drivers and boards, all on its `main` branch. |
| 98 other `oss.*` packages | SymbianSource | The rest of the 2010 Symbian source, at the commits Phorepoc pins (`core/sources.lock`) |
| `core`, `pdk` | [Phorepoc](https://github.com/Phorepoc) | The build system (`phe`, `fetch.sh`, compile fixes for modern GCC). `core` fetches from neosymbian. |
| `symbian-pixel` | — (this repo) | Docs and the ZimaOS build environment (the port moved to `kernel`) |

Rule: in every fork, the upstream branches stay untouched and our work is on `main`.

## License

Our code is Apache-2.0 (see `LICENSE`, and the SPDX header in every file). The Symbian sources it builds on are
EPL-1.0.
