# NeoSymbian docs

NeoSymbian brings the open-source 2010 Symbian (EKA2, the Symbian^3 release) back to modern hardware:

- **First target:** the Google Pixel 3a XL (bonito, Qualcomm SDM670).
- **Second device:** the Pixel 3a (sargo, the same SoC), a community port since 2026-11-16 ([hardware.md, devices](hardware.md#devices-where-neosymbian-can-go-next)).
- **Kernel:** ported to AArch64 with 32-bit pointers (ILP32).
- **User side:** the 2010 Symbian user side runs unchanged in 32-bit mode at AArch32 EL0.
- **UI:** a new touch UI written in Rust.

## Documents

| Document | What |
|---|---|
| [roadmap.md](roadmap.md) | Plan and status: kernel (K), hardware (H), UI (U) and phone (P) tracks |
| [hardware.md](hardware.md) | **Hardware and drivers hub:** every driver's status (kernel + neohw), the neohw processes and their IPC, milestones D0–D8, and which phones could be next (the device shortlist). Details in `hardware/`: [modem](hardware/modem.md) (C0–C12), [audio](hardware/audio.md) (A0–A8), [wifi](hardware/wifi.md) (W0–W7), [bluetooth](hardware/bluetooth.md) (B0–), [battery](hardware/battery.md) |
| [kernel-assessment.md](kernel-assessment.md) | Source audit: legacy architecture, existing defenses, reviewed baseline, coverage and limits |
| [kernel-issues.md](kernel-issues.md) | Evidence-based kernel/reliability/security register, with all existing known issues mapped |
| [kernel-modernization.md](kernel-modernization.md) | Phases KM0–KM6: fixes, owners, dependencies, tests and supported-release gates |
| [kernel audit verification](verification/kernel-audit-2026-11-09.md) | Exact documentation checks, controlled runner probe, artifacts and unexecuted kernel tests |
| [rust-integration.md](rust-integration.md) | Rust on the Symbian user side: stages R0–R8 |
| [neoui-shell.md](neoui-shell.md) | **neoui shell hub:** what the shell draws and serves, every stage and the canvas map. Details in `neoui-shell/`: [top panel](neoui-shell/top-panel.md) (status bar, notifications, media, calls/messages, live island, control centre, lock screen; TP0–TP9), [protocol](neoui-shell/protocol.md), [kit](neoui-shell/kit.md), [navigation](neoui-shell/navigation.md), [keyboard](neoui-shell/keyboard.md), [settings](neoui-shell/settings.md), [home](neoui-shell/home.md), [design system](neoui-shell/design-system.md), [smooth UI](neoui-shell/smooth-ui.md) (S1–S6) |
| [phone-apps.md](phone-apps.md) | Phone, Contacts and Messages v2: three apps that open each other; shared data; missing platform functions |
| [files-app.md](files-app.md) | Files: the new files repo, every canvas screen, platform gaps, phases FA0–FA13 |
| [store.md](store.md) | NeoStore: the Go store server, the phone app, the `.npk` format, the on-phone installer for `.npk` and `.sis`, phases ST0–ST11 |
| [browser.md](browser.md) | Web browser design: every candidate, why Servo, the browser repo and forks, stages WB0–WB7 |
| [port-map.md](port-map.md) | How EKA2 maps onto AArch64: what was reused, adapted and written new |
| [ekern-backend.md](ekern-backend.md) | The full kernel's AArch64 backend |
| [filesystem.md](filesystem.md) | File system plan: drives, flash layout, stages FS1–FS6 |
| [symbian-phone-sources.md](symbian-phone-sources.md) | What the 2010 phone, contacts and phonesrv sources give C8: dialer, smart dialling, call log, speed dial, SS codes, vCard (facts only) |
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
| [neohw](https://github.com/NeoSymbian/neohw) | The user side of the hardware in Rust (was `telephony`, with `neolink` merged in): the modem, audio, Wi-Fi and IP daemons and their crates ([hardware.md](hardware.md)) |
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
