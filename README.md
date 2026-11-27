# NeoSymbian docs

NeoSymbian brings the open-source 2010 Symbian (EKA2, the Symbian^3 release) back to modern hardware:

- **First target:** the Google Pixel 3a XL (bonito, Qualcomm SDM670).
- **More devices:** the Pixel 3a (sargo, the same SoC) as a community port, and the OnePlus 6T (fajita, SDM845), which
  RAM-boots our kernel and neoui since 2026-11-26 ([devices](hardware/devices/README.md)).
- **Kernel:** ported to AArch64 with 32-bit pointers (ILP32).
- **User side:** the 2010 Symbian user side runs unchanged in 32-bit mode at AArch32 EL0.
- **UI:** a new touch UI written in Rust.

**Start with the [roadmap](roadmap.md):** what matters now, and every stage's status. Open problems are in
[known-issues.md](known-issues.md).

## Areas

Each folder is one area. Its `README.md` is the landing page: what the area covers, every document in it with its
status, and where related work lives. Finished specs stay in their area marked `Status: done`; superseded designs
and long bring-up logs are in the area's `history/` folder.

| Area | What |
|---|---|
| [kernel/](kernel/README.md) | The AArch64 EKA2 port: the port map, the ekern backend, the KRN issue register, modernization KM0–KM6, the 2026-11-09 audit |
| [user-side/](user-side/README.md) | The 2010 user side on ARMv8-A AArch32: the ABI rules, SMP safety and the ISA (US0–US6), Rust on the user side (R stages), old S60 apps (L stages) |
| [storage/](storage/README.md) | Drives, flash layout, F32 plugins, ROFS, A/B updates, installing a big Z: (FS1–FS7) |
| [hardware/](hardware/README.md) | Every driver (kernel C++ and neohw Rust): modem, Wi-Fi, audio, Bluetooth, battery, GNSS; devices and ports (fajita); run records |
| [neoui-shell/](neoui-shell/README.md) | The Rust UI server: the protocol (the only owner of protocol versions), the kit, navigation, the keyboard, the top panel, Settings, smooth UI |
| [apps/](apps/README.md) | The apps, each in its own repo: Phone/Contacts/Messages, Files, Clock/Calendar, the browser, the planned store |
| [developer-tools/](developer-tools/README.md) | The path from the Mac to the phone: the USB debug console, fshell over ACM, acceptance records |
| [reference/](reference/symbian-sources.md) | Facts about the 2010 sources: the source survey and licences, the phone/contacts packages |
| [history/](history/README.md) | Project history: retired repositories (with restore bundles), the old roadmap, the old paths |

Documents moved into these folders on 2026-11-27: [MOVED.md](MOVED.md) maps every old path to its new one.

## Stage IDs

Every stage ID has one owning document; its status lives in that document's `stages` block (the
[board](roadmap.md#the-board) collects them). Where two areas use the same letter, qualify the ID with the area.

| Prefix | Owner | Note |
|---|---|---|
| M1–M4, H0–H6, U1–U4, P1–P5 | [kernel/](kernel/README.md) (M); [history/roadmap-log-2026-11.md](history/roadmap-log-2026-11.md) (H, U, P) | The first roadmap's tracks. Roadmap M2 = ekern-backend's steps M4.2–M4.7; roadmap M4 = performance |
| KM0–KM6 | [kernel/modernization.md](kernel/modernization.md) | |
| KRN-001… | [kernel/issues.md](kernel/issues.md) | Findings; their fixes are recorded in [known-issues.md](known-issues.md) |
| US0–US6 | [user-side/user-side-smp.md](user-side/user-side-smp.md) | |
| R0–R10, H3a | [user-side/rust-integration.md](user-side/rust-integration.md) | |
| L0–L5 | [user-side/legacy.md](user-side/legacy.md) | Not debug-access's L1–L3 |
| FS1–FS7, G1–G4 | [storage/filesystem.md](storage/filesystem.md) | G = safety gates. Not navigation's G2–G5 |
| D0–D8 | [hardware/README.md](hardware/README.md) | Driver milestones. Not settings-data's D1–D19 |
| C0–C12 | [hardware/modem.md](hardware/modem.md) | |
| W0–W7 | [hardware/wifi.md](hardware/wifi.md) | |
| A0–A8 | [hardware/audio.md](hardware/audio.md) | Not the kit's A1–A5 |
| B0–B9 | [hardware/bluetooth.md](hardware/bluetooth.md) | |
| GN0–GN5 | [hardware/gnss.md](hardware/gnss.md) | |
| OP0–OP13 | [hardware/devices/fajita.md](hardware/devices/fajita.md) | |
| TP0–TP9, POWER | [neoui-shell/top-panel.md](neoui-shell/top-panel.md) | POWER = the power menu v2 |
| SE0–SE7, V0–V3, LG0–LG2 | [neoui-shell/settings.md](neoui-shell/settings.md) | LG = display language (SE5) |
| D1–D19 | [neoui-shell/settings-data.md](neoui-shell/settings-data.md) | Settings data. Not hardware's D0–D8 |
| NV1–NV12, G2–G5 | [neoui-shell/navigation.md](neoui-shell/navigation.md) | |
| S1–S6 | [neoui-shell/smooth-ui.md](neoui-shell/smooth-ui.md) | |
| A1–A5, MV1–MV2 | [neoui-shell/kit.md](neoui-shell/kit.md) | Not audio's A0–A8. MV = repo moves (neoterm, Classic apps) |
| FA0–FA13, FA12b | [apps/files/README.md](apps/files/README.md) | FA12b's plan: [apps/files/video-sync.md](apps/files/video-sync.md) |
| DT0–DT7 | [apps/datetime.md](apps/datetime.md) | |
| ST0–ST11, NS01–NS12 | [apps/store.md](apps/store.md) | NS = decisions |
| WB0–WB7, UI0–UI6 | [apps/browser/README.md](apps/browser/README.md) | |
| DA0–DA6, T1–T12 | [developer-tools/debug-access.md](developer-tools/debug-access.md), [debug-access-roadmap.md](developer-tools/debug-access-roadmap.md) | |

A new stage series takes a prefix that isn't in this table, and adds its row here. Protocol versions and opcodes are
not stages: they are allocated only in [neoui-shell/protocol.md](neoui-shell/protocol.md).

## Repositories

Everything lives in the [NeoSymbian](https://github.com/NeoSymbian) organization. Nothing is pushed back to the
original projects.

| Repository | What |
|---|---|
| [kernel](https://github.com/NeoSymbian/kernel) | The EKA2 kernel (the SymbianSource kernelhwsrv fork) with the AArch64 port, drivers and boards (`baseport/arm64`) |
| [build](https://github.com/NeoSymbian/build) | The build system: `neo`, the build image (`ghcr.io/neosymbian/toolchain`), the pinned sources, the 2010 user side as ARMv8 |
| [e32-rs](https://github.com/NeoSymbian/e32-rs) | Rust crates for the Symbian user side |
| [neoui](https://github.com/NeoSymbian/neoui) | The Rust UI server and its apps |
| [neohw](https://github.com/NeoSymbian/neohw) | The user side of the hardware in Rust (was `telephony`, with `neolink` merged in): the modem, audio, Wi-Fi and IP daemons and their crates |
| [phone](https://github.com/NeoSymbian/phone), [files](https://github.com/NeoSymbian/files), [datetime](https://github.com/NeoSymbian/datetime), [browser](https://github.com/NeoSymbian/browser) | The apps ([apps/](apps/README.md)) |
| [neoqemu](https://github.com/NeoSymbian/neoqemu) | QEMU for the AArch64 kernel's `virt` runs: upstream QEMU plus our fixes, `run-qemu.sh` and `ui-qemu.py`. Replaced symbian-qemu (2026-11-25, [retired](history/retired-repos.md)) |
| `oss.*` | The SymbianSource packages the build pins (`build/sources.lock`), forked as they are |

The docs' own checks: `python3 tools/check-links.py` (every relative link and anchor) and
`python3 tools/roadmap.py --check` (the board matches the stage blocks); the `docs` workflow runs both.

## Licence

These documents are Apache-2.0 (`LICENSE`).
