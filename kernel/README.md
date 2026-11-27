<!-- SPDX-License-Identifier: Apache-2.0 -->
# Kernel

Part of [the docs](../README.md) · Status: active · Updated: 2026-11-27

The 2010 SMP EKA2 kernel (kernelhwsrv `201043_12`), ported to AArch64 with 32-bit pointers (ILP32), on the Pixel 3a
XL and QEMU `virt`. The 2010 user side runs unchanged above it at AArch32 EL0. This area covers the port itself, the
kernel issue register and the modernization gates a supported release needs. Kernel code is C++ only: Rust has no
ILP32 target.

## Where the port lives

[NeoSymbian/kernel](https://github.com/NeoSymbian/kernel) is the SymbianSource kernelhwsrv fork (renamed
2026-11-06); the build scripts still check it out as `oss.FCL.sf.os.kernelhwsrv`. The AArch64 port sits in Symbian's
own layout, beside the `arm/` and `x86/` folders; changes to Symbian files are made in place and marked `NeoSymbian`.

| Path in the kernel repo | What |
|---|---|
| `kernel/eka/nkernsmp/arm64` | The SMP nanokernel backend: scheduler, context switch, IRQs, IPIs, timers |
| `kernel/eka/kernel/arm64` | ekern's arch code: bootstrap, exec gate, exceptions, user copies, AArch32 fix-ups |
| `kernel/eka/memmodel/epoc/flexible/arm64`, `…/flexible/mmu/arm64` | The flexible memory model on VMSAv8 (ASIDs, the IPC alias) |
| `kernel/eka/common/arm64` | Shared arch code (`a64s_atomics.cpp`) |
| `kernel/eka/include/{kernel,nkern,nkernsmp,memmodel/epoc/flexible}/arm64` | The arch headers |
| `kerneltest/e32test/arm64`, `kerneltest/e32test/nkernsa/arm64` | Kernel tests and the standalone nanokernel (nkernsa) glue |
| `baseport/arm64/common` | Board-independent drivers and the user-side board config (`common/user`) |
| `baseport/arm64/<soc>_assp` | SoC support, e.g. `sdm670_assp` (Pixel), `virt_assp` (QEMU) |
| `baseport/arm64/<board>_variant` | One board each, with its `variant.conf`, e.g. `bonito_variant`, `qemu_variant` |
| `baseport/arm64/tools` | `build-ekern.sh`, `phone.py`, `test-fshell-qemu.py` and the other build and test tools |

The baseport's own [README](https://github.com/NeoSymbian/kernel/blob/main/baseport/arm64/README.md) describes the
board layout. Builds: `neo kernel qemu|bonito` and `neo nkernsa qemu` from a `build` checkout; after a kernel commit,
re-pin `build/sources.lock`.

## Stages

These are roadmap Track K. Roadmap M2 is the work [ekern-backend.md](ekern-backend.md) numbers M4.2–M4.7; roadmap M4
is performance. The supported-release gates are a separate track, owned by [modernization.md](modernization.md).

<!-- stages -->
| Stage | What | State | Updated | Next / evidence |
|---|---|---|---|---|
| M1 | nkernsa clean on the phone | done | 2026-11-06 | Pixel: whole suite failures 0x0, skmpar too; rare QEMU-only failures are KRN-018 |
| M2 | Full kernel (ekern) on QEMU and the phone | done | 2026-11-06 | ekern-backend M4.2–M4.7: 8 CPUs, user mode, 2010 user side; e32test groups wait for KM0 |
| M3 | The 2010 user side boots | done | 2026-11-06 | eshell on the phone screen (7f63ec2), then neoui as the shell (366f63d) |
| M4 | Performance | active | 2026-11-26 | done: big.LITTLE balancing, DTB RAM map, CPU boost HAL (kernel#44); open: tickless idle, governor, 64-bit TPhysAddr |
<!-- /stages -->

## Documents

| Doc | What | Status |
|---|---|---|
| [port-map.md](port-map.md) | The 2026-11-05 map of EKA2's arch code to AArch64 ILP32, from the x86-64 and ARMv8 templates | reference |
| [ekern-backend.md](ekern-backend.md) | The full kernel's arch backend, step by step (M4.2–M4.7) | done |
| [issues.md](issues.md) | The kernel issue register, KRN-001 onwards: findings, closure rules, acceptance | active |
| [modernization.md](modernization.md) | The supported-release gates, ordered, and the legacy test matrix | plan |
| [audits/2026-11-09/assessment.md](audits/2026-11-09/assessment.md) | The 2026-11-09 source audit behind the register | record |
| [audits/2026-11-09/verification.md](audits/2026-11-09/verification.md) | What that audit checked, command by command | record |

Open problems and their status are in [known-issues.md](../known-issues.md).

## Kernel work recorded elsewhere

- **Drivers** (modem, Wi-Fi, audio, battery, USB, display and the rest): [hardware/](../hardware/README.md).
- **Storage** (eMMC, FAT32 `C:`/`E:`, ROFS `Z:`, A/B slots, verity): [storage/filesystem.md](../storage/filesystem.md).
- **The debug monitor, USB serial and fshell over USB:** [developer-tools/](../developer-tools/README.md).
- **FP/NEON for user code, bigger stacks, a seeded RNG** (WB1): [apps/browser/wb1-kernel.md](../apps/browser/wb1-kernel.md).
- **CPU placement and clocks, user FP, the display processor:** [smooth-ui.md](../neoui-shell/smooth-ui.md) S3–S5.
- **User-side SMP and the ARMv8 user side** (euser's locks, `NeoTrapFp`, the CPU profile):
  [user-side/user-side-smp.md](../user-side/user-side-smp.md).
