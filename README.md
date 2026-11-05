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

## How it's built

The kernel is AArch64 code with **32-bit pointers (ILP32)**, so EKA2's data layouts stay the same and 32-bit ARM
Symbian programs run unchanged at EL0. The arch-neutral kernel sources are compiled **unmodified**. This repository
adds only the new architecture:

| Path | What |
|---|---|
| `port/arm64/a64smp/` | AArch64 backend of the SMP nanokernel: scheduler, context switch, atomics, spinlocks |
| `port/arm64/boot/` | Boot code, exception vectors, linker script |
| `port/arm64/board/` | GICv3, board glue for QEMU `virt` and the Pixel 3a XL (`pixel_bonito.cpp`) |
| `port/arm64/nksa/` | Glue for the nkernsa nanokernel tests |
| `port/arm64/tools/` | `build-kernel.sh`, `run-qemu.sh`, symbol census |
| `probes/` | Tiny boot images that showed what the Pixel's bootloader accepts |
| `zimaos/` | The Docker build environment (arm64 dev image, VNC desktop) |
| `docs/` | [Port map](docs/port-map.md), [sources survey](docs/sources.md), [roadmap](docs/roadmap.md) |

## Repositories

Everything the build uses is forked into the [**neosymbian**](https://github.com/neosymbian) organization. Nothing is
pushed back to the original projects.

| Repository | Forked from | Role |
|---|---|---|
| `oss.FCL.sf.os.kernelhwsrv` | [SymbianSource](https://github.com/SymbianSource) | The EKA2 kernel. Our in-place kernel changes go on its `main` branch. |
| 98 other `oss.*` packages | SymbianSource | The rest of the 2010 Symbian source, at the commits Phorepoc pins (`core/sources.lock`) |
| `core`, `pdk` | [Phorepoc](https://github.com/Phorepoc) | The build system (`phe`, `fetch.sh`, compile fixes for modern GCC). `core` fetches from neosymbian. |
| `symbian-pixel` | — (this repo) | New work: the AArch64 port, the Pixel board, docs |

Rule: in every fork, the upstream branches stay untouched and our work is on `main`.

## License

Our code is Apache-2.0 (see `LICENSE`, and the SPDX header in every file). The Symbian sources it builds on are
EPL-1.0.
