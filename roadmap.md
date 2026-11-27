<!-- SPDX-License-Identifier: Apache-2.0 -->
# Roadmap: EKA2 on the Pixel 3a XL, to a daily phone with a Rust UI

Part of [the docs](README.md) · Status: active · Updated: 2026-11-27

**Goal:** a daily phone: calls, SMS, mobile data, Wi-Fi, a touch UI, and a battery that lasts a day.

How this page works:
- **Priorities** (hand-written) says what matters now and what blocks it. Each row links the stage that owns the work.
- **The board** (generated) lists every stage of every area. Each stage document owns its status in a `stages` block;
  `tools/roadmap.py` copies the blocks here, and the docs CI fails when this page is out of date. Change a status in
  the stage document, then run `python3 tools/roadmap.py`.
- The story of how the port got here (M1–M4, H0–H6, U1–U4, P1–P5, 2026-11-05 to 2026-11-27) is in
  [history/roadmap-log-2026-11.md](history/roadmap-log-2026-11.md).

## Fixed decisions

| Decision | Made by | Choice |
|---|---|---|
| Kernel | existing | The 2010 SMP EKA2 (kernelhwsrv `201043_12`) as an ILP32 AArch64 kernel ([kernel/](kernel/README.md)). |
| User side | owner | The 2010 Symbian user side at AArch32 EL0, built as one ARMv8-A AArch32 softfp flavour ([user-side/](user-side/README.md), US2–US5); old ARMv5/v6 S60 apps run unchanged. |
| UI | owner | A new Rust UI server (neoui, Slint software renderer) replaces the window server; system apps are Rust ([neoui-shell/](neoui-shell/README.md)). |
| Old apps | owner (2026-11-14) | Unmodified S60 `.sis` apps run in one guest window server inside neoui ([user-side/legacy.md](user-side/legacy.md)). |
| Driver language | lead | Timing-critical code, or anything needed before the user side boots: C++ in the kernel. Protocol logic and policy: Rust on the user side ([hardware/](hardware/README.md)). Rust has no ILP32 target, so there is no Rust in the kernel. |
| Hardware reference | lead | Mainline Linux, postmarketOS and freedreno are read for register layouts and behaviour only; no code is copied (GPL vs EPL/Apache). |
| Release gates | audit (2026-11-09) | A supported release also needs the modernization gates KM0–KM6 ([kernel/modernization.md](kernel/modernization.md)). |

## Priorities

Ordered by the goal; the order is a proposal (2026-11-27) for the owner to change. State is copied by hand from the
board below, so check the board when they differ.

| # | Outcome | Owning stage | State | Next gate / blocker |
|---|---|---|---|---|
| 1 | Mobile data over LTE | [C10](hardware/modem.md) | open | IPA QMI handshake and the modem's data endpoints; C11 (VoLTE) is go/no-go after it |
| 2 | A day on battery | [D8](hardware/README.md), [D2](hardware/README.md), [C12](hardware/modem.md) | open / active | Suspend and resume, overnight idle (D8); fuel policy and thermal shutdown (D2) |
| 3 | Calls that hold up | [C7](hardware/modem.md) | done | Its exit test, a 24-hour run, was never done |
| 4 | Install a big system image | [FS7](storage/filesystem.md) | active | Step 2: `fastboot flash system_b` on the inactive slot (owner's OK) |
| 5 | USB on an installed boot (debug console, `E:` on a PC) | [DA6](developer-tools/debug-access.md), [FS6](storage/filesystem.md) | parked | The host never sees the phone after an installed cold boot (KRN-027) |
| 6 | Top panel: control centre, lock screen | [TP7–TP9](neoui-shell/top-panel.md) | open | TP7 is next; its numbers are reserved in the protocol |
| 7 | Settings complete | [SE4, SE5, V3](neoui-shell/settings.md), [D7, D11](neoui-shell/settings-data.md) | active | SIM PIN changes held back until the review's fixes; V3 canvas sync |
| 8 | Media: background play, video | [TP3](neoui-shell/top-panel.md), [FA9 M1b, FA12, FA12b](apps/files/README.md) | active | FA12b step 1: check files `fb90512` on the Pixel ([video-sync.md](apps/files/video-sync.md)) |
| 9 | Browser services | [WB6](apps/browser/README.md) | active | Certificate store, cookie rule, saved passwords |
| 10 | Old S60 apps | [L1, L2, L5](user-side/legacy.md) | active | The explicit guest handshake; X-plore copy and rename |
| 11 | Smoothness | [S5](neoui-shell/smooth-ui.md), [M4](kernel/README.md) | open / active | Display processor (vsync, planes); tickless idle and a CPU governor |
| 12 | Bluetooth | [B0](hardware/bluetooth.md) | open | GENI UART and HCI: a valid version answer after a cold boot |
| 13 | GNSS first fix | [GN3, GN5](hardware/gnss.md) | parked | Paused by the owner; GN3's phone re-test first |
| 14 | The OnePlus 6T | [OP7+](hardware/devices/fajita.md) | open | New firmware since 2026-11-27 (OxygenOS 11, /e/OS); our kernel boots on it. OP7 (C: and E: on UFS) is the owner's call |
| 15 | Release readiness | [KM0–KM6](kernel/modernization.md) | open | KM0: gates that fail when a test doesn't report (KRN-022) |
| 16 | NeoStore | [ST0](apps/store.md) | open | Spikes: PlatSec on C:, HTTP, SIS enums |

## The board

<!-- board -->
### Kernel

| Stage | What | State | Updated | Next / evidence | Doc |
|---|---|---|---|---|---|
| M1 | nkernsa clean on the phone | ✅ done | 2026-11-06 | Pixel: whole suite failures 0x0, skmpar too; rare QEMU-only failures are KRN-018 | [kernel/](kernel/README.md) |
| M2 | Full kernel (ekern) on QEMU and the phone | ✅ done | 2026-11-06 | ekern-backend M4.2–M4.7: 8 CPUs, user mode, 2010 user side; e32test groups wait for KM0 | [kernel/](kernel/README.md) |
| M3 | The 2010 user side boots | ✅ done | 2026-11-06 | eshell on the phone screen (7f63ec2), then neoui as the shell (366f63d) | [kernel/](kernel/README.md) |
| M4 | Performance | 🔵 active | 2026-11-26 | done: big.LITTLE balancing, DTB RAM map, CPU boost HAL (kernel#44); open: tickless idle, governor, 64-bit TPhysAddr | [kernel/](kernel/README.md) |
| KM0 | Reproducible baseline and trustworthy gates | ⬜ open | 2026-11-25 | KRN-022 open: no marker still exits 0; Syborg CI gone, virt CI runs user-side tests | [kernel/modernization](kernel/modernization.md) |
| KM1 | Preserve persistent data, honest repair | ⬜ open | 2026-11-09 | KRN-007–010 open; C: and E: still FS_FORMAT_CORRUPT | [kernel/modernization](kernel/modernization.md) |
| KM2 | Least privilege and end-to-end trust | ⬜ open | 2026-11-17 | KRN-003 partly: seeded secure RNG (kernel c2b9c6e7); the rest open | [kernel/modernization](kernel/modernization.md) |
| KM3 | Time, SMP, VM and legacy ABI | ⬜ open | 2026-11-21 | done on the way: user FP/NEON (kernel#19), global-page TLB fix (kernel#36); KRN-017/018/020/033 open | [kernel/modernization](kernel/modernization.md) |
| KM4 | Hardware lifecycle and recovery | ⬜ open | 2026-11-22 | KRN-029 fixed; modem restart fixed with follow-ups (KRN-037); USB cold boot parked (KRN-027) | [kernel/modernization](kernel/modernization.md) |
| KM5 | Measured performance, maintainable board support | ⬜ open | 2026-11-25 | KRN-031 fixed (QEMU screenshot); KRN-025/026/028/035 open | [kernel/modernization](kernel/modernization.md) |
| KM6 | Complete audits, operate a supported release | ⬜ open | 2026-11-09 | KRN-023/034 open | [kernel/modernization](kernel/modernization.md) |

### User side

| Stage | What | State | Updated | Next / evidence | Doc |
|---|---|---|---|---|---|
| L0 | Ownership and inventory | ✅ done | 2026-11-14 | the legacy repo, the runtime in compsupp, honest audit reports | [user-side/legacy](user-side/legacy.md) |
| L0.5 | The AppArc launcher and Old apps grid | ✅ done | — | X-plore and Frozen Bubble listed with their icons, protocol 1.6 | [user-side/legacy](user-side/legacy.md) |
| L1 | A stable runtime and desktop | 🔵 active | 2026-11-20 | desktop persists, AknCapServer first; open: the explicit guest handshake | [user-side/legacy](user-side/legacy.md) |
| L2 | Two usable apps | 🔵 active | 2026-11-20 | Frozen Bubble done (legacy#4, #5); X-plore copy, rename, kept settings open | [user-side/legacy](user-side/legacy.md) |
| L3 | Shell integration, several apps at once | ⬜ open | — | not started: damage-based drawing, a task protocol | [user-side/legacy](user-side/legacy.md) |
| L4 | Runtime SIS install | ✖ dropped | 2026-11-18 | moved to NeoStore ST6 (apps/store.md): a Rust SIS installer in NEOINST; designed, not built | [user-side/legacy](user-side/legacy.md) |
| L5 | Breadth: modes, FEP, media, a corpus | 🔵 active | 2026-11-20 | key pads, sound, sockets done; open: AknFep, rotation, IAP records, a corpus | [user-side/legacy](user-side/legacy.md) |
| R0 | Toolchain spike: Rust in a C++ EXE | ✅ done | 2026-11-06 | NEOHELLO prints on Syborg; symbian-2010 `3167456` | [user-side/rust-integration](user-side/rust-integration.md) |
| R1 | An EXE written only in Rust | ✅ done | 2026-11-06 | NEOR1 exits 42, NEOPANIC panics RUST; e32-rs `8b903c1` | [user-side/rust-integration](user-side/rust-integration.md) |
| R2 | The `e32` core: heap, threads, fs | ✅ done | 2026-11-06 | NEOTEST 6/6; C: loading fixed, symbian-2010 `c6b0b10` | [user-side/rust-integration](user-side/rust-integration.md) |
| R3 | An IPC server in Rust | ✅ done | 2026-11-06 | NEOCLI 9/9 against the Rust NEOSRV; e32-rs `47d2a2d` | [user-side/rust-integration](user-side/rust-integration.md) |
| R4 | The UI on the Mac (Slint) | ✅ done | 2026-11-06 | neoui-host, first screens, snapshots; neoui `90871bb` | [user-side/rust-integration](user-side/rust-integration.md) |
| R5 | The UI server as SYSSTART | ✅ done | 2026-11-06 | launcher on the Syborg screen, taps in CI; neoui `6861aff` | [user-side/rust-integration](user-side/rust-integration.md) |
| R6 | The app model: apps as processes | ✅ done | 2026-11-06 | NEOCLOCK on a shared surface; neoui `5633ee2` | [user-side/rust-integration](user-side/rust-integration.md) |
| R6b | The terminal (ECONS, NEOTERM) | ✅ done | 2026-11-06 | ESHELL in a window; neoui `f25bc67` | [user-side/rust-integration](user-side/rust-integration.md) |
| R6c | System keyboard and live clock | ✅ done | 2026-11-06 | types `dir` by touch in CI; neoui `0efa85a` | [user-side/rust-integration](user-side/rust-integration.md) |
| R6d | Keyboard languages, terminal mode, text fields | ✅ done | 2026-11-12 | en/hy/ru; neoui `d579fa0` + `32b783a`; installed slot a | [user-side/rust-integration](user-side/rust-integration.md) |
| R7 | The UI on the Pixel, by touch | ✅ done | 2026-11-06 | neoui became the phone's shell (366f63d, kernel M3); R9, R10 ran there | [user-side/rust-integration](user-side/rust-integration.md) |
| R8 | File access and a Files app | ✅ done | 2026-11-06 | `e32::fs`, NEOFILES; the app is now NeoSymbian/files | [user-side/rust-integration](user-side/rust-integration.md) |
| R9 | neoui speed on the phone | ✅ done | 2026-11-07 | measured; the follow-up is smooth-ui S1–S6 | [user-side/rust-integration](user-side/rust-integration.md) |
| R10 | Apps keep running, app switcher | ✅ done | 2026-11-07 | neoui `fc54289`; Syborg CI and the Pixel | [user-side/rust-integration](user-side/rust-integration.md) |
| H3a | Power off, restart and the clock | ✅ done | 2026-11-08 | kernel `bee9830`, neoui `724475a`; installed slot b | [user-side/rust-integration](user-side/rust-integration.md) |
| US0 | Barriers in euser's `.cia` locks | ✅ done | 2026-11-21 | build#41; 3.5 min browsing, no crash; installed finchmane | [user-side/user-side-smp](user-side/user-side-smp.md) |
| US1 | Audit user-side sync for single-core assumptions | ✅ done | 2026-11-21 | kernel#32, ossrv#4, e32-rs#8; `smp` 3/3 on the Pixel | [user-side/user-side-smp](user-side/user-side-smp.md) |
| US2 | euser, efsrv, hal as ARMv8-A AArch32 | ✅ done | 2026-11-21 | build#46; NeoTrapFp keeps d8–d15 across a leave | [user-side/user-side-smp](user-side/user-side-smp.md) |
| US3 | The rest of the 2010 ROM as ARMv8 | ✅ done | 2026-11-22 | build#52, ossrv#6; 276/276 accepted, boot median 15.1 s | [user-side/user-side-smp](user-side/user-side-smp.md) |
| US4 | Rust and the browser on one ARMv8 target | ✅ done | 2026-11-25 | e32-rs#12 and seven repos; native atomics, `Arc`; neoui 32 ms home frame | [user-side/user-side-smp](user-side/user-side-smp.md) |
| US5 | Clean-up: one user-side ABI | ✅ done | 2026-11-25 | build#56 #58 #59; CI and phone build the same 286 E32 images | [user-side/user-side-smp](user-side/user-side-smp.md) |
| US6a | CI baseline on QEMU `virt` | ✅ done | 2026-11-25 | e32-rs#13, browser#17; NEOCPU, `smp` ×3, MIXTEST in CI | [user-side/user-side-smp](user-side/user-side-smp.md) |
| US6b | UI CI parity on `virt` | ✅ done | 2026-11-25 | kernel#40, legacy#8, build#60, neoui#36; `virt-taps` green | [user-side/user-side-smp](user-side/user-side-smp.md) |
| ARMv8 profile | `__CPU_ARMV8A__`: CRC32, LDA/STL measured | ✅ done | 2026-11-26 | kernel#43; CRC32 ships (8–11×), LDA/STL under the 10 % bar, not used | [user-side/user-side-smp](user-side/user-side-smp.md) |
| A0–A3 | A 64-bit (ILP32) user side | ⏸ parked | 2026-11-21 | studied; revisit for cores without AArch32 EL0 | [user-side/user-side-smp](user-side/user-side-smp.md) |

### Storage

| Stage | What | State | Updated | Next / evidence | Doc |
|---|---|---|---|---|---|
| FS1 | The FAT32 plugin: 8 GB C: | ✅ done | 2026-11-07 | kernel 6c404ef, build 584ba4e; f32test FAT tests not in the ROM | [storage/filesystem](storage/filesystem.md) |
| FS2 | eMMC speed: DDR52, write allow-list | ✅ done | 2026-11-07 | kernel fc0c929: 70 MB/s read, 39 MB/s write | [storage/filesystem](storage/filesystem.md) |
| FS3 | C: and E: on userdata, TRIM | ✅ done | 2026-11-07 | kernel 92586a0; survives a watchdog reset during a copy | [storage/filesystem](storage/filesystem.md) |
| FS4 | Z: on ROFS, from RAM then flash | ✅ done | 2026-11-07 | kernel f93a432 (FS4a), 2fd7deb (FS4b); the phone is installed | [storage/filesystem](storage/filesystem.md) |
| FS5 | Block hashes and A/B updates | ✅ done | 2026-11-08 | kernel 20b8f44 (FS5a), 5b0ba6b (FS5b); a bad update rolls back | [storage/filesystem](storage/filesystem.md) |
| FS6 | USB mass storage for E: | ⏸ parked | 2026-11-08 | researched; blocked on USB power on a normal boot (known issues) | [storage/filesystem](storage/filesystem.md) |
| FS7 | Install a big Z: | 🔵 active | 2026-11-26 | step 0 done (ROFS=ramdisk, kernel#45); plan steps 2–4 open | [storage/filesystem](storage/filesystem.md) |
| Later | Encryption, journaled C:, exFAT, MTP, paging, CQHCI | ⬜ open | — | each when needed; encryption before personal data (KRN-016) | [storage/filesystem](storage/filesystem.md) |

### Hardware

| Stage | What | State | Updated | Next / evidence | Doc |
|---|---|---|---|---|---|
| S0 | telephony renamed neohw; docs centralised | ✅ done | 2026-11-18 | this hub | [hardware/](hardware/README.md) |
| S1 | neolink merged into neohw | ✅ done | 2026-11-18 | neohw#4: one host and one Symbian workspace | [hardware/](hardware/README.md) |
| S2 | modem-proto split into crates; a Bus | ✅ done | 2026-11-18 | neohw#5; phone registers, Wi-Fi works | [hardware/](hardware/README.md) |
| S3 | HWHUB.EXE and NeoHub | ✅ done | 2026-11-18 | neohw#6; registration over NeoHub on the phone | [hardware/](hardware/README.md) |
| S4 | AUDIOD.EXE, NeoAudio CONTROL from MODEMD | ✅ done | 2026-11-18 | neohw#7; media on the DSP on the phone | [hardware/](hardware/README.md) |
| S5 | WIFID.EXE, the supplicant out of SYSSTART | ✅ done | 2026-11-18 | neohw#8, neoui#21; auto-join, DHCP, internet | [hardware/](hardware/README.md) |
| S6 | ROM recipe for the neohw EXEs | ✅ done | 2026-11-18 | neohw symbian/exes.txt (five EXEs; GNSSD since 2026-11-20) | [hardware/](hardware/README.md) |
| D0 | Inventory | ✅ done | 2026-11-10 | tools/inspect-bonito.py; verification record of 2026-11-10 | [hardware/](hardware/README.md) |
| D1 | Foundations | ⬜ open | 2026-11-10 | bus startup and validation done; resource votes, async streams, device DMA open | [hardware/](hardware/README.md) |
| D2 | Power | 🔵 active | 2026-11-20 | TSENS, battery, display done; fuel policy, thermal shutdown, cold USB open | [hardware/](hardware/README.md) |
| D3 | Audio and haptics | ✅ done | 2026-11-18 | NeoAudio A0–A8 (audio.md), DRV2624; no ACDB calibration | [hardware/](hardware/README.md) |
| D4 | Sensors | ⬜ open | — | ADSP sensor PD over FastRPC first | [hardware/](hardware/README.md) |
| D5 | Cameras | ⬜ open | — | CAMSS, CCI, isolated DMA; IMX355 first | [hardware/](hardware/README.md) |
| D6 | Connectivity | 🔵 active | 2026-11-21 | Wi-Fi done (wifi.md); GNSS paused before a fix; Bluetooth designed | [hardware/](hardware/README.md) |
| D7 | Remaining hardware | ⬜ open | — | NFC, fingerprint feasibility, torch | [hardware/](hardware/README.md) |
| D8 | System acceptance | ⬜ open | — | suspend/resume, overnight idle, a 24-hour run | [hardware/](hardware/README.md) |
| A0 | This page and the protocol | ✅ done | 2026-11-17 | NeoAudio v1.0 | [hardware/audio](hardware/audio.md) |
| A1 | NeoAudio with the clock sink | ✅ done | 2026-11-18 | QEMU: Dev tools tone, sink clock | [hardware/audio](hardware/audio.md) |
| A2 | Media periods on the ADSP | ✅ done | 2026-11-18 | Pixel: tone through the DSP, routes, preemption | [hardware/audio](hardware/audio.md) |
| A3 | Old apps' DevSound over NeoAudio | ✅ done | 2026-11-18 | Pixel: Frozen Bubble plays; level not checked by ear | [hardware/audio](hardware/audio.md) |
| A4 | Tones, DTMF, WAV through MMF | ✅ done | 2026-11-18 | built into the ROM; not exercised on the phone | [hardware/audio](hardware/audio.md) |
| A5 | Recording | ✅ done | 2026-11-18 | Pixel: 5 s recorded and played back | [hardware/audio](hardware/audio.md) |
| A6 | Media volume, routes, focus | ✅ done | 2026-11-18 | Pixel: Settings and the volume keys | [hardware/audio](hardware/audio.md) |
| A7 | Amp fault IRQs, mic mapping | ✅ done | 2026-11-18 | polling runs; ADSP mixing and a QEMU audio device not done | [hardware/audio](hardware/audio.md) |
| A8 | 3.5 mm jack, ACDB investigation | ✅ done | 2026-11-18 | driver up; headphones untried; no ACDB | [hardware/audio](hardware/audio.md) |
| B0 | GENI UART, HCI LDD, power pulses | ⬜ open | — | a valid version answer after cold boot | [hardware/bluetooth](hardware/bluetooth.md) |
| B1 | Firmware download, baud, address, IBS | ⬜ open | — | LE scan and inquiry without hurting LTE or Wi-Fi | [hardware/bluetooth](hardware/bluetooth.md) |
| B2 | TrouBLE behind bt-core | ⬜ open | — | executor and atomics gates first | [hardware/bluetooth](hardware/bluetooth.md) |
| B3 | Pairing, SSP, LESC, bonds | ⬜ open | — | pair, reboot, reconnect | [hardware/bluetooth](hardware/bluetooth.md) |
| B4 | L2CAP, RFCOMM, SDP, NEOBT.PRT | ⬜ open | — | an unchanged 2010 client transfers | [hardware/bluetooth](hardware/bluetooth.md) |
| B5 | OBEX and old-app contracts | ⬜ open | — | files both ways, equal hashes | [hardware/bluetooth](hardware/bluetooth.md) |
| B6 | A2DP, SBC, AVRCP | ⬜ open | — | 30 minutes of music | [hardware/bluetooth](hardware/bluetooth.md) |
| B7 | HFP AG | ⬜ open | — | a two-way CVSD call, then mSBC | [hardware/bluetooth](hardware/bluetooth.md) |
| B8 | HID over GATT, watch services | ⬜ open | — | keyboard and mouse | [hardware/bluetooth](hardware/bluetooth.md) |
| B9 | Acceptance | ⬜ open | — | Wi-Fi, BT and LTE together; a 24-hour run | [hardware/bluetooth](hardware/bluetooth.md) |
| OP0 | Device facts and DTB | ✅ done | 2026-11-26 | private/fajita.dtb; boot header facts on this page | [hardware/devices/fajita](hardware/devices/fajita.md) |
| OP1 | ABL probes | ✅ done | 2026-11-26 | green and blue on the 6T's screen | [hardware/devices/fajita](hardware/devices/fajita.md) |
| OP2 | The board | ✅ done | 2026-11-26 | fajita_variant; neoui launcher up | [hardware/devices/fajita](hardware/devices/fajita.md) |
| OP3 | Debug link | ✅ done | 2026-11-26 | USB console, AUTOFASTBOOT, phone.py (kernel 58470a68) | [hardware/devices/fajita](hardware/devices/fajita.md) |
| OP4 | Input | ✅ done | 2026-11-26 | keys and RMI4 touch | [hardware/devices/fajita](hardware/devices/fajita.md) |
| OP5 | Clocks | ✅ done | 2026-11-26 | cpufreq 4 + 4, touch boost, TSENS | [hardware/devices/fajita](hardware/devices/fajita.md) |
| OP6 | UFS, read-only | ✅ done | 2026-11-26 | every LUN's GPT read; PRs kernel#46 build#67 | [hardware/devices/fajita](hardware/devices/fajita.md) |
| U1 | UFS: Linux's split (core, vendor ops, QMP PHY) | ✅ done | 2026-11-27 | `blk init` + `blk luns` as in OP6 (kernel 90eea545) | [hardware/devices/fajita](hardware/devices/fajita.md) |
| U2 | UFS: our own bring-up | ✅ done | 2026-11-27 | `blk reset`: link, NOP, fDeviceInit, LUNs (kernel 90eea545) | [hardware/devices/fajita](hardware/devices/fajita.md) |
| U3 | UFS: 2 lanes, HS-G3 | ✅ done | 2026-11-27 | `blk gear`: pwrmode 11, lanes 2/2 (kernel 90eea545) | [hardware/devices/fajita](hardware/devices/fajita.md) |
| U4 | UFS: interrupts + request queue | ✅ done | 2026-11-27 | 1 GB at 328 MB/s, 0 errors, `boot_a` hash matches (kernel df7ff8d1) | [hardware/devices/fajita](hardware/devices/fajita.md) |
| U5 | UFS: guarded writes, C: on `system_b` | ✅ done | 2026-11-27 | guard + wtest; a file survives 3 reboots; 392 MB/s (kernel 18afb83c, 8f21452e) | [hardware/devices/fajita](hardware/devices/fajita.md) |
| U6 | UFS: error recovery, own init by default | ⬜ open | — | reset + retry after a fatal error or a stuck slot | [hardware/devices/fajita](hardware/devices/fajita.md) |
| OP7 | C: and E: on UFS | 🔵 active | 2026-11-27 | a test C: on `system_b` works (U5); the real place is the owner's call (/e/OS owns userdata) | [hardware/devices/fajita](hardware/devices/fajita.md) |
| OP8 | Panel | ⬜ open | — | DCS to the S6E3FC2X01 | [hardware/devices/fajita](hardware/devices/fajita.md) |
| OP9 | Battery | ⬜ open | — | bq27xxx gauge, PMI8998 charger | [hardware/devices/fajita](hardware/devices/fajita.md) |
| OP10 | Modem | ⬜ open | — | LLCC slice table, then MSS on OnePlus firmware | [hardware/devices/fajita](hardware/devices/fajita.md) |
| OP11 | Wi-Fi | ⬜ open | — | WCN3990 with OnePlus board data | [hardware/devices/fajita](hardware/devices/fajita.md) |
| OP12 | Audio and haptics | ⬜ open | — | SLIMbus, WCD9340, TFA9894, PMI8998 haptics | [hardware/devices/fajita](hardware/devices/fajita.md) |
| OP13 | Install | ⬜ open | — | A/B install on UFS: the owner's call | [hardware/devices/fajita](hardware/devices/fajita.md) |
| GN0 | This design | ✅ done | 2026-11-20 | read by the owner | [hardware/gnss](hardware/gnss.md) |
| GN1 | crates/loc; hub port 0x28 | ✅ done | 2026-11-20 | 18 host tests; neohw#10 | [hardware/gnss](hardware/gnss.md) |
| GN2 | GNSSD.EXE, started by MODEMD | ✅ done | 2026-11-20 | phone: LOC bound, lock and mode answered; neohw#10 | [hardware/gnss](hardware/gnss.md) |
| GN3 | XTRA download, cache, inject | ⏸ parked | 2026-11-20 | code done (HTTP fetch, neohw 208b878); phone re-test pending | [hardware/gnss](hardware/gnss.md) |
| GN4 | Dev tools row and actions | ✅ done | 2026-11-20 | phone; neoui#26 | [hardware/gnss](hardware/gnss.md) |
| GN5 | First fix | ⏸ parked | 2026-11-20 | paused by the owner; resume at GR0 below | [hardware/gnss](hardware/gnss.md) |
| C0 | Recon and backups | ✅ done | 2026-11-08 | radio partitions hashed, carve-outs safe (kernel 1253e70) | [hardware/modem](hardware/modem.md) |
| C1 | Linux reference run | ✅ done | 2026-11-08 | GO: LTE and a two-way call under mainline Linux | [hardware/modem](hardware/modem.md) |
| C2 | Kernel transport | ✅ done | 2026-11-08 | SCM, SMEM, SMP2P, QMP, GLINK (kernel a5283de) | [hardware/modem](hardware/modem.md) |
| C3 | Modem boot | ✅ done | 2026-11-08 | MSS boots from modem_a and talks QRTR (kernel a5283de) | [hardware/modem](hardware/modem.md) |
| C4 | Modem services | ✅ done | 2026-11-08 | rmtfs, locator, TFTP; the modem stays up | [hardware/modem](hardware/modem.md) |
| C5 | QMI, NeoModem, dialer (no audio) | ✅ done | 2026-11-09 | calls out and in, silent | [hardware/modem](hardware/modem.md) |
| C5b | IPA, the first half of C10 | ✅ done | 2026-11-09 | the modem stays on LTE (kernel d003355) | [hardware/modem](hardware/modem.md) |
| C6 | Call audio | ✅ done | 2026-11-09 | two-way audio on earpiece and loudspeaker (kernel b12d1ba) | [hardware/modem](hardware/modem.md) |
| C7 | Complete calls | ✅ done | 2026-11-21 | merged 2026-11-12; recovery accepted (kernel#38, neohw#14); 24-hour run not done | [hardware/modem](hardware/modem.md) |
| C8 | Call log and contacts | ✅ done | 2026-11-14 | NEOPHONE in NeoSymbian/phone, installed on slot a | [hardware/modem](hardware/modem.md) |
| C9 | SMS | ✅ done | 2026-11-16 | sent, delivered and received; installed on slot a | [hardware/modem](hardware/modem.md) |
| C10 | Mobile data | ⬜ open | — | IPA QMI handshake, modem data endpoints, IPA teardown on a modem stop | [hardware/modem](hardware/modem.md) |
| C11 | VoLTE (stretch) | ⬜ open | — | go/no-go after C10 | [hardware/modem](hardware/modem.md) |
| C12 | Persistence, power, compatibility | ⬜ open | — | G4 EFS writes need the owner's OK; suspend (H3) | [hardware/modem](hardware/modem.md) |
| W0 | The firmware's WLFW service appears | ✅ done | 2026-11-12 | cause: the locator's message id (0x21) | [hardware/wifi](hardware/wifi.md) |
| W1 | Firmware control (WLFW) | ✅ done | 2026-11-12 | firmware-ready indication on the phone | [hardware/wifi](hardware/wifi.md) |
| W2 | Copy engines, HTC, WMI | ✅ done | 2026-11-12 | WMI READY on the phone | [hardware/wifi](hardware/wifi.md) |
| W3 | Scan | ✅ done | 2026-11-12 | direct WMI path, not UMAC/WHA; networks on both bands | [hardware/wifi](hardware/wifi.md) |
| W4 | Join a WPA2-PSK network | ✅ done | 2026-11-12 | connected from Settings by touch | [hardware/wifi](hardware/wifi.md) |
| W5 | An IP address (smoltcp, NEONET) | ✅ done | 2026-11-12 | DHCP, ping, internet check over NeoNet | [hardware/wifi](hardware/wifi.md) |
| W5a | ESOCK over NeoNet | ✅ done | 2026-11-13 | NEOSOCK passed on Syborg and on the phone; no CI run on virt | [hardware/wifi](hardware/wifi.md) |
| W6 | Wi-Fi in Settings | ✅ done | 2026-11-12 | W3c and W4: list, password, connect, details | [hardware/wifi](hardware/wifi.md) |
| W7 | Interrupts, handshake guard, modem restart | ✅ done | 2026-11-21 | interrupts 2026-11-13; re-init after a restart proven (kernel#38, neohw#14) | [hardware/wifi](hardware/wifi.md) |

### Shell (neoui)

| Stage | What | State | Updated | Next / evidence | Doc |
|---|---|---|---|---|---|
| Part 3 | Home pages, pin and unpin, dock, edit mode | 🔵 active | 2026-11-27 | layout and editor built (neoui#61, D10); left: Add to home from the menu | [neoui-shell/home](neoui-shell/home.md) |
| Part 4 | Widgets: templates, catalogue, `WIDGET` | 🔵 active | 2026-11-27 | built-in Clock, Agenda, Favourites, Media in a catalogue; app widgets open | [neoui-shell/home](neoui-shell/home.md) |
| A1 | The kit, tokens, glyphs, gallery | ✅ done | 2026-11-17 | `snapshots/kit-*.png`; installed on slot a 2026-11-17 | [neoui-shell/kit](neoui-shell/kit.md) |
| A2–A3 | Apps and the shell's screens on the kit | ✅ done | 2026-11-17 | Clock, Files, Dev tools, Terminal, NEOKIT, NEOPHONE ported | [neoui-shell/kit](neoui-shell/kit.md) |
| A5 | Protocol 1.8, `nav.mode` 0..=2 | ✅ done | 2026-11-17 | with Navigation v2 (NV1) | [neoui-shell/kit](neoui-shell/kit.md) |
| G1 | Edge recognizer and gesture mode | ✅ done | 2026-11-16 | Back, Open apps, Home, Apps menu by edge swipe; an edge hint | [neoui-shell/navigation](neoui-shell/navigation.md) |
| P | v1 Five places: strip and Page API | ✅ done | 2026-11-17 | built 2026-11-16, replaced by Navigation v2 on 2026-11-17 | [neoui-shell/navigation](neoui-shell/navigation.md) |
| NV1–NV12 | Navigation v2, Gestures the default | ✅ done | 2026-11-17 | protocol 1.8, kit header, key row and band, both maps; installed on slot a | [neoui-shell/navigation](neoui-shell/navigation.md) |
| G2 | N9 peek: the screen follows the finger | ⬜ open | — | design below; not started | [neoui-shell/navigation](neoui-shell/navigation.md) |
| G3 | Open apps thumbnails, columns, close mode | ✅ done | 2026-11-27 | neoui#61 (D10): `nav.switcher_cols`, a 500 ms hold shows × on every card | [neoui-shell/navigation](neoui-shell/navigation.md) |
| G4 | Swipe down from the top closes the app | ✅ done | 2026-11-27 | neoui#61 (D10): `nav.swipe_close`; virt-taps closes Settings with it | [neoui-shell/navigation](neoui-shell/navigation.md) |
| G5 | Lanes home: Events, Home, Open apps | ✅ done | 2026-11-27 | neoui#61 (D10): `home.style`; not run on the phone yet | [neoui-shell/navigation](neoui-shell/navigation.md) |
| D1 | Shared row values, search, both roots | ✅ done | 2026-11-27 | neoui#61: one row model; left: dynamic instances, scroll to a hit | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D2 | Wi-Fi details, console overlay, slot | ✅ done | 2026-11-27 | neoui#61: WIFID link record, HAL 0x4e02/03, active slot | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D3 | Drive totals, per-drive kinds, C: free | ✅ done | 2026-11-27 | neoui#61; the per-drive kinds page waits for FS6 | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D4 | App identity, size by owner, Clear data | ✅ done | 2026-11-27 | neoui#61 (INFO 8, OWNER_REPORT, INFO 13); owners in other apps left | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D5 | Screen-on time since full charge | ✅ done | 2026-11-27 | neoui#61: charge-cycle recorder, INFO 9 | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D6 | Profile feedback, previews, your own ringtones | ✅ done | 2026-11-27 | neoui#61, neohw#21 (modem-ipc 2.8, NeoAudio 1.1); WAV import not run on the phone | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D7 | Wallpaper, font scale, display language | 🔵 active | 2026-11-27 | colours and font size built; left: pictures, language strings, other apps' font scale | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D8 | Clipboard notice, permissions, diagnostics | ✅ done | 2026-11-27 | toast and diagnostics built; read-only app permissions deferred | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D9 | Notification policy and pages | ✅ done | 2026-11-27 | with TP4, protocol 1.21; left: MODEMD's alert policy, inline reply | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D10 | Navigation settings and Edit home | ✅ done | 2026-11-27 | G3–G5 and the home editor; left: Add to home from the menu, 2×2 widgets | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D11 | SIM lock and attempts left | 🔵 active | 2026-11-27 | page reads the card; PIN changes held back until the review's fixes (below) | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D12 | Hidden Wi-Fi join | ⬜ open | 2026-11-27 | "Not yet" row; needs the kernel's directed scan (SE1c-2) | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D13 | Mobile bearer, mode, APNs, traffic | ⬜ open | 2026-11-27 | "Not yet" row; waits for C10 | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D14 | Bluetooth discovery, pairing, profiles | ⬜ open | 2026-11-27 | "Not yet" row; waits for B0–B8 | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D15 | Lock policy, device PIN, double-tap wake | ⬜ open | 2026-11-27 | "Not yet" row; waits for TP8/TP9 | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D16 | Attributed battery estimates | ⬜ open | 2026-11-27 | "Not yet" row; after D5 and radio instrumentation | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D17 | Eject E: and share over USB | ⬜ open | 2026-11-27 | "Not yet" row; waits for FS6 | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D18 | Check for OS updates | 🔵 active | 2026-11-27 | status row built ("Update service unavailable"); a signed feed is open | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| D19 | Network reset extensions, Erase C: | ⬜ open | 2026-11-27 | "Not yet" row; after D13/D14, then recovery (SE7) | [neoui-shell/settings-data](neoui-shell/settings-data.md) |
| SE0 | NEOSET app, out of the shell | ✅ done | 2026-11-26 | neoui#38, e32-rs#16, neohw#17; three Pixel runs | [neoui-shell/settings](neoui-shell/settings.md) |
| SE1 | Grid, search, zones, saved Wi-Fi, apps catalogue | ✅ done | 2026-11-26 | neoui#39 #40 #43 #44, neohw#18; SE1c-2 (hidden networks) continues as D12 | [neoui-shell/settings](neoui-shell/settings.md) |
| SE2 | Sound profiles, tones, your sounds | ✅ done | 2026-11-27 | neoui#45 #46, neohw#19; WAV import built as D6 (neoui#61) | [neoui-shell/settings](neoui-shell/settings.md) |
| SE2c-2 | Ringtones longer than 2 s | ⏸ parked | 2026-11-26 | needs a kernel audio-buffer change; the owner's call | [neoui-shell/settings](neoui-shell/settings.md) |
| SE3 | Battery, input, storage, font size, wallpaper | ✅ done | 2026-11-27 | neoui#47 #48; font size and colours as D7 (neoui#61); pictures wait (D7) | [neoui-shell/settings](neoui-shell/settings.md) |
| SE4 | Stop, Clear data, resets, notification pages | 🔵 active | 2026-11-27 | SE4a neoui#49 neohw#20; TP4 + D9 neoui#61; left: TP7, the capabilities view | [neoui-shell/settings](neoui-shell/settings.md) |
| SE5 | Language, SIM PIN, panel, navigation rows | 🔵 active | 2026-11-27 | G3–G5 rows (D10), SIM lock page read-only (D11); left: display language, PIN changes | [neoui-shell/settings](neoui-shell/settings.md) |
| SE6 | Hardware pages and lock | ⬜ open | 2026-11-27 | update status row only (D18); waits for TP8/TP9, B3, C10, FS6 | [neoui-shell/settings](neoui-shell/settings.md) |
| SE7 | Erase C: through recovery | ⬜ open | — | waits for recovery support (D19) | [neoui-shell/settings](neoui-shell/settings.md) |
| V0 | Board check tool | ✅ done | 2026-11-26 | neoui#53, docs#74 | [neoui-shell/settings](neoui-shell/settings.md) |
| V1 | Kit parts A1–A9 | ✅ done | 2026-11-26 | neoui#54 | [neoui-shell/settings](neoui-shell/settings.md) |
| V2 | Every page to its board | ✅ done | 2026-11-26 | neoui#55 #56 #57 #58 #60; board check, Codex review, Pixel run each | [neoui-shell/settings](neoui-shell/settings.md) |
| V3 | Canvas sync | ⬜ open | 2026-11-27 | the fixes listed under Board parity; AS BUILT marks | [neoui-shell/settings](neoui-shell/settings.md) |
| S1 | Input and frame pacing | ✅ done | 2026-11-08 | neoui `f1a844b`, kernel `38eb607`; no lost taps on the Pixel | [neoui-shell/smooth-ui](neoui-shell/smooth-ui.md) |
| S2 | Retained layers and a CPU compositor | ✅ done | 2026-11-08 | home swipe at budget; fades and scrolling 1–4 ms over | [neoui-shell/smooth-ui](neoui-shell/smooth-ui.md) |
| S3 | CPU placement and clocks | ✅ done | 2026-11-08 | kernel S3a–S3d; gold 300 → 1996 MHz under touch | [neoui-shell/smooth-ui](neoui-shell/smooth-ui.md) |
| S4 | FP/NEON for user code, ARMv8 build | ✅ done | 2026-11-25 | kernel#19 (WB1); US4: home renders in 32 ms, was 68–72 | [neoui-shell/smooth-ui](neoui-shell/smooth-ui.md) |
| S5 | Display processor: vsync, planes | ⬜ open | — | not started; needs the panel mode and splash pipe first | [neoui-shell/smooth-ui](neoui-shell/smooth-ui.md) |
| S6 | Adreno 615 GPU | ⏸ parked | — | stretch, not planned (roadmap U4) | [neoui-shell/smooth-ui](neoui-shell/smooth-ui.md) |
| TP0 | Docs and canvas boards | ✅ done | 2026-11-21 | canvas version 67; this folder | [neoui-shell/top-panel](neoui-shell/top-panel.md) |
| TP1 | Status bar v2 and the shade's first stop | ✅ done | 2026-11-26 | neoui#50; Pixel run on image 33 | [neoui-shell/top-panel](neoui-shell/top-panel.md) |
| TP2 | Cards; Phone and Messages post their own | ✅ done | 2026-11-27 | TP2a neoui#51 (protocol 1.18); TP2b neoui#61, phone#12 | [neoui-shell/top-panel](neoui-shell/top-panel.md) |
| TP2c | Files' copy job as Progress style | ⬜ open | 2026-11-26 | waits for files' repin (files#15) | [neoui-shell/top-panel](neoui-shell/top-panel.md) |
| TP3 | Media session, background playback | ⬜ open | — | with Files FA9 M1b | [neoui-shell/top-panel](neoui-shell/top-panel.md) |
| TP4 | Channels, banners, DND, Settings pages | ✅ done | 2026-11-27 | neoui#61, phone#12 (protocol 1.21, with D9); inline reply deferred | [neoui-shell/top-panel](neoui-shell/top-panel.md) |
| TP5 | Calls in the panel | ⬜ open | — | uses TP2/TP4 | [neoui-shell/top-panel](neoui-shell/top-panel.md) |
| TP6 | Live island | ⬜ open | — | not started | [neoui-shell/top-panel](neoui-shell/top-panel.md) |
| TP7 | Control centre and tiles | ⬜ open | 2026-11-27 | next; its numbers are reserved in protocol.md (TP7 tiles) | [neoui-shell/top-panel](neoui-shell/top-panel.md) |
| TP8 | Lock screen | ⬜ open | — | replaces Navigation G6 | [neoui-shell/top-panel](neoui-shell/top-panel.md) |
| TP9 | Screen-lock PIN | ⬜ open | — | after TP8 | [neoui-shell/top-panel](neoui-shell/top-panel.md) |

### Apps

| Stage | What | State | Updated | Next / evidence | Doc |
|---|---|---|---|---|---|
| WB0 | Host proof: Servo on emulated 32-bit ARM Linux | ✅ done | 2026-11-16 | GO; results in browser `wb0/` | [apps/browser/](apps/browser/README.md) |
| WB0p | Speed gate on a physical ARM board | ⏸ parked | 2026-11-16 | no board; the Pixel gives the numbers now (WB4, WB5) | [apps/browser/](apps/browser/README.md) |
| WB1 | Kernel: FP/NEON, 16 MiB stacks, GC memory, entropy | ✅ done | 2026-11-17 | kernel#19, e32-rs#3 | [apps/browser/](apps/browser/README.md) |
| WB2 | Rust std over P.I.P.S., Tokio, TCP over NeoNet | ✅ done | 2026-11-19 | browser#3–#6, build#33 #34 #37, e32-rs#4 #5, kernel#21 #24, legacy#6, ossrv#1 #2 | [apps/browser/](apps/browser/README.md) |
| WB3 | SpiderMonkey, interpreter only (JSSHELL.EXE) | ✅ done | 2026-11-19 | browser#7, mozjs#1; jssuite 9 ok on the Pixel | [apps/browser/](apps/browser/README.md) |
| WB4 | Servo in the Browser app (engine NEOWEBE) | ✅ done | 2026-11-20 | browser#8, build#40, kernel#31, ossrv#3, mozjs#2 | [apps/browser/](apps/browser/README.md) |
| WB5 | Input and chrome; scrolling 15–18 fps | ✅ done | 2026-11-21 | browser#10 #11, ossrv#5, servo#1, webrender#1, build#47, docs#52 #53 | [apps/browser/](apps/browser/README.md) |
| WB6 | Certificates, cookies, logins, Wi-Fi portals | 🔵 active | 2026-11-22 | UI5 done (browser#13); certificate store, cookie rule, passwords open | [apps/browser/](apps/browser/README.md) |
| WB7 | Media: video and sound | ⬜ open | — | not started; UI6 waits for it | [apps/browser/](apps/browser/README.md) |
| UI0 | The app and its chrome | ✅ done | 2026-11-17 | browser#1; 5/5 built; Buttons mode not run on Servo | [apps/browser/](apps/browser/README.md) |
| UI1 | Address, loading, reading | ✅ done | 2026-11-17 | browser#2; 3/3 built; the chrome doesn't hide on scroll with Servo | [apps/browser/](apps/browser/README.md) |
| UI2 | Opened pages and Options | ✅ done | 2026-11-21 | in WB5c (browser#10); eviction not checked on the phone | [apps/browser/](apps/browser/README.md) |
| UI3 | Forms and dialogs | ✅ done | 2026-11-21 | in WB5a (browser#10); all 5 work on Servo | [apps/browser/](apps/browser/README.md) |
| UI4 | Library and settings | 🔵 active | 2026-11-21 | 6/7 built (browser#10); `set2-app-browser` not re-checked since the Settings app's Apps pages (SE4a) | [apps/browser/](apps/browser/README.md) |
| UI5 | Safety and errors | ✅ done | 2026-11-22 | browser#13, servo and neoui `ui5` branches; 4/4 on Servo on the Pixel | [apps/browser/](apps/browser/README.md) |
| UI6 | Media | ⬜ open | — | with WB7 | [apps/browser/](apps/browser/README.md) |
| DT0 | Move Clock into the datetime repo | ✅ done | 2026-11-26 | NEOCLOCK 0xE0008001; neoui dropped `apps/clock` (datetime#1, neoui#59) | [apps/datetime](apps/datetime.md) |
| DT1 | DTSRV for alarms and timers | ✅ done | 2026-11-26 | protocol 1.19 service, stores, plan, cards; Pixel: alarm rang, came back after reboot | [apps/datetime](apps/datetime.md) |
| DT2 | Clock v2 | ✅ done | 2026-11-26 | every non-Proposed `clk2-*` board (23 snapshots); Ringing with a NeoAudio tone | [apps/datetime](apps/datetime.md) |
| DT3 | The calendar model | ✅ done | 2026-11-26 | `pim-ics`, `calendar-core` (RRULE subset with DST, fuzzed), DTSRV stores | [apps/datetime](apps/datetime.md) |
| DT4 | NEOCAL views | ✅ done | 2026-11-26 | every non-Proposed `cal2-*` board (27 snapshots); the shell mock is gone | [apps/datetime](apps/datetime.md) |
| DT5 | Reminders | ✅ done | 2026-11-26 | Pixel: a 1-minute reminder rang in Calendar | [apps/datetime](apps/datetime.md) |
| DT6 | Links: birthdays, .ics, share | ✅ done | 2026-11-26 | phone#11 (NCT2 birthdays), files#18 (Add to Calendar); Pixel-tested | [apps/datetime](apps/datetime.md) |
| DT7 | Home widgets | ✅ done | 2026-11-26 | ClockWidget and AgendaCard from `dtsrv.next` (neoui#59) | [apps/datetime](apps/datetime.md) |
| FA0 | Move Files to its own repo | ✅ done | 2026-11-17 | files `624fb01`, neoui#14; Pixel RAM boot | [apps/files/](apps/files/README.md) |
| FA1 | v2 browsing, footer tabs, icons | ✅ done | 2026-11-18 | files `4ed71d4`, e32-rs `0489694`, neoui `2047404` | [apps/files/](apps/files/README.md) |
| FA2 | Copy, move, trash, paste bar | ✅ done | 2026-11-18 | same PRs as FA1; protocol 1.11 progress in the shade | [apps/files/](apps/files/README.md) |
| FA3 | Recent, Types, search, bin, cleanup | ✅ done | 2026-11-18 | files `559c508` + `f00af5f`; Pixel: bin survives a reboot | [apps/files/](apps/files/README.md) |
| FA4 | Text and code viewer and editor | ✅ done | 2026-11-18 | files `e42811c`; Pixel: 5 MB log opens, byte-exact saves | [apps/files/](apps/files/README.md) |
| FA5 | Images: decoders, thumbnails, editor | ✅ done | 2026-11-19 | files#6; Pixel: 12 MP JPEG in 310 ms | [apps/files/](apps/files/README.md) |
| FA6 | Archives: zip, gzip, tar | ✅ done | 2026-11-19 | files#7; Pixel: 1 GB zip extracts in 70 s | [apps/files/](apps/files/README.md) |
| FA7 | vCard, iCal, fonts, certificates, hex | ✅ done | 2026-11-20 | files#8, phone#7; Add to Calendar later in files#18 (DT6) | [apps/files/](apps/files/README.md) |
| FA8 | Open with, share, file picker | ✅ done | 2026-11-20 | e32-rs#7, neohw#11, neoui#27, files#9 | [apps/files/](apps/files/README.md) |
| FA9 M0–M1 | Audio player and WAV | ✅ done | 2026-11-21 | files#10; the incoming-call test not run | [apps/files/](apps/files/README.md) |
| FA9 M1b–M6 | Background play, MP3 to MIDI | ⬜ open | 2026-11-21 | next: decoder choices, then M2 (MP3); M1b needs top panel TP3 | [apps/files/](apps/files/README.md) |
| FA10 | EPUB, docx, odt, rtf, xlsx | ✅ done | 2026-11-21 | files#11; Pixel-tested except pinch | [apps/files/](apps/files/README.md) |
| FA11 | PDF viewer (hayro fork) | ✅ done | 2026-11-25 | files#14, docs#64; Pixel-tested except pinch | [apps/files/](apps/files/README.md) |
| FA12 | Video player: H.264, VP8, VP9 | 🔵 active | 2026-11-26 | neoui#52, files#16; 720p30 plays on the Pixel; V5, V6, release layout open | [apps/files/](apps/files/README.md) |
| FA12b | A/V sync and speed fixes | ⬜ open | 2026-11-26 | seven steps in video-sync.md (FA12b plan); step 1 verifies files `fb90512` on the Pixel | [apps/files/](apps/files/README.md) |
| FA13 | Outside Files: USB, Bluetooth, MMS, .sis | ⬜ open | — | each in its owner's stages (FS6, B5, C10, ST10) | [apps/files/](apps/files/README.md) |
| ST0 | Spikes: PlatSec on C:, HTTP, SIS enums | ⬜ open | — | first; answers go into this doc | [apps/store](apps/store.md) |
| ST1 | The Go server on atlas | ⬜ open | — | can start at once; needs the `neosymbian.org` zone check | [apps/store](apps/store.md) |
| ST2 | The developer and admin console | ⬜ open | — | after ST1 | [apps/store](apps/store.md) |
| ST3 | The `.npk` format and `npk-pack` | ⬜ open | — | starts the `.npk` line | [apps/store](apps/store.md) |
| ST4 | The app registry in neoui | ⬜ open | — | after ST3; opcodes reserved in protocol.md | [apps/store](apps/store.md) |
| ST5 | NEOINST for `.npk` | ⬜ open | — | after ST4 | [apps/store](apps/store.md) |
| ST6 | SIS installs on the phone | ⬜ open | — | needs ST5; replaces legacy L4's SWI port | [apps/store](apps/store.md) |
| ST7 | NEOSTORE v1, the phone app | ⬜ open | — | needs ST1 and ST5 | [apps/store](apps/store.md) |
| ST8 | Ratings with the device key | ⬜ open | — | needs ST7 | [apps/store](apps/store.md) |
| ST9 | SisRegistry compatibility | ⬜ open | — | last group | [apps/store](apps/store.md) |
| ST10 | Links from Files and Settings | ⬜ open | — | last group; replaces Files FA13's install button | [apps/store](apps/store.md) |
| ST11 | HTTPS to the store | ⬜ open | — | needs browser WB6's certificates | [apps/store](apps/store.md) |

### Developer tools

| Stage | What | State | Updated | Next / evidence | Doc |
|---|---|---|---|---|---|
| DA0 | Design | ✅ done | 2026-11-10 | this document | [developer-tools/debug-access](developer-tools/debug-access.md) |
| DA1 | fshell runs | ✅ done | 2026-11-10 | T6: on QEMU through econs (build#12, graphics#1); on the phone over USB since DA3 | [developer-tools/debug-access](developer-tools/debug-access.md) |
| DA2 | Serial and fshell on QEMU, in CI | ✅ done | 2026-11-11 | T5, T7: kernel#4, kernel#6, build#14; the build CI job passes | [developer-tools/debug-access](developer-tools/debug-access.md) |
| DA3 | Second ACM function on the phone | ✅ done | 2026-11-11 | T8: kernel#7; two cu.usbmodem ports, monitor kept | [developer-tools/debug-access](developer-tools/debug-access.md) |
| DA4 | Files and programs from the Mac | ✅ done | 2026-11-11 | T9: kernel#8; phone.py sh, push, pull with SHA-256 | [developer-tools/debug-access](developer-tools/debug-access.md) |
| DA5 | Robustness | ✅ done | 2026-11-11 | T10, T11: kernel#9, kernel#10; the flood and full C: checks failed, skipped by the owner | [developer-tools/debug-access](developer-tools/debug-access.md) |
| DA6 | Installed boot | ⏸ parked | 2026-11-11 | T12: kernel#11; the host never sees the phone on a cold boot (KRN-027) | [developer-tools/debug-access](developer-tools/debug-access.md) |
| Later | memoryaccess, TRK, OST traces, coredumps | ⬜ open | — | each needs its own design (roadmap L1–L3) | [developer-tools/debug-access](developer-tools/debug-access.md) |

<!-- /board -->
