<!-- SPDX-License-Identifier: Apache-2.0 -->
# Where the port's files went

Part of [history](README.md) · Status: record · Updated: 2026-11-06

Moved from the top-level README on 2026-11-27. `symbian-pixel` was deleted on 2026-11-06; its whole history is a bundle
in [retired/](retired) ([retired-repos.md](retired-repos.md)).

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
