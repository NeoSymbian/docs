<!-- SPDX-License-Identifier: Apache-2.0 -->
# OnePlus 6T (fajita): the second SoC

Written 2026-11-26, the day we got the phone. This is the port plan for the OnePlus 6T (fajita, Qualcomm SDM845): the
facts read from the phone, the decisions, and the stages OP0–OP13. The 6T was item 2 of the device recommendation in
[../README.md](../README.md#recommendation). The OnePlus 6 (enchilada) is the same board with another panel, so this
port should serve it too (untested).

**Status (2026-11-26):** OP0–OP6 done, and **neoui runs on the 6T** (RAM boot): the launcher, apps, touch, keys, the USB console, CPU clocks with touch boost, and temperatures all work. Since `ROFS=ramdisk` (kernel#45), Z:'s ROFS rides as the boot image's ramdisk, which takes the image past the bootloader's ~49.5 MB kernel limit: the Files app is back in it. UFS reads work (read-only, OP6).

## Decisions (owner, 2026-11-26)

- **A new `kernel/baseport/arm64/sdm845_assp/`**, beside `sdm670_assp`. A driver is copied in when the stage that
  needs it comes, not all at once. Most SDM670 blocks sit at the same addresses on SDM845 (see the table below), so
  most copies are the same code with new tables. Fixes to a shared block have to go into both copies until the two
  folders are merged.
- **Ubuntu Touch stays on the phone.** Every test is a RAM boot (`fastboot boot`), and nothing is flashed. The UFS
  driver stays read-only. C:/E: on UFS waits for the owner's call (OP7).
- **Board:** `kernel/baseport/arm64/fajita_variant/` (the `board.h` file `specific/oneplus_fajita.cpp`), built with
  `neo kernel fajita` / `neo nkernsa fajita`. The phone's DTB is `private/fajita.dtb`, never committed (like
  `private/bonito.dtb`).

## The phone (read over adb, 2026-11-26)

These facts come from the running Ubuntu Touch: `getprop`, `/proc/cmdline` and `/proc/device-tree`, read-only.

- **Software:** Ubuntu Touch (Halium 9, the downstream kernel 4.9.112).
- **Bootloader:** unlocked (`ro.boot.flash.locked=0`, verified-boot state orange). Slot `_a`.
- **IDs:** `project_name=18801` (the 6T), `hw_version=41`, `dtbo_idx=18`.
- **RAM:** 0x80000000 + 4 GB, and 0x180000000 + about 3.9 GB (the 8 GB model). Only the part below 4 GB is ours
  until `TPhysAddr` is widened ([roadmap](../../roadmap.md) M4).
- **CPUs:** 8, MPIDR 0x000–0x700 with Aff1 = core, as on bonito. Mainline says 4 × A55 + 4 × A75 (bonito: 6 + 2).
  PSCI `smc`.
- **GICv3:** GICD 0x17a00000, GICR 0x17a60000, the same as bonito.
- **Storage:** UFS only (`androidboot.bootdevice=1d84000.ufshc`), the usual Qualcomm A/B partition set (`boot_a/b`,
  `dtbo_a/b`, `modem_a/b`, `system_a/b`, `vendor_a/b`, `userdata`, …). No eMMC.
- **Panel:** `dsi_samsung_s6e3fc2x01_cmd_display`. The bootloader (ABL) starts it in **command mode**. Mainline Linux
  drives it in video mode, but what counts for us is what ABL leaves on, as for bonito's splash.

### Reserved memory (from the live DTB)

| Region | Base | Size | Note |
|---|---|---|---|
| hyp | 0x85700000 | 0x600000 | the same as bonito, so `A64_BOOT_RAM_END=0x85700000` holds |
| xbl | 0x85e00000 | 0x100000 | |
| removed | 0x85fc0000 | 0x4b40000 | cmd-db and SMEM inside it, as on bonito |
| qseecom | 0x8ab00000 | 0x1400000 | |
| ips_fw, ipa_gsi, gpu | 0x8c400000 / 0x8c410000 / 0x8c415000 | 0x10000 / 0x5000 / 0x2000 | IPA firmware at 0x8c400000 |
| adsp | 0x8c500000 | 0x1a00000 | |
| wlan_fw | 0x8df00000 | 0x100000 | |
| modem | 0x8e000000 | 0x7800000 | |
| video, cdsp, mba, slpi, spss | 0x95800000 … 0x97b00000 | | |
| cont_splash | **0x9d400000** | 0x2400000 | the framebuffer |
| bootloader_log | 0x9fff7000 | 0x100000 | |
| param, ramoops, mtp | 0xac200000 / 0xac300000 / 0xac700000 | 1 / 4 / 11 MB | |

The early kernel heap bonito uses (0xA2000000 + 96 MB) is free here too.

### Devices on the I2C buses (from the live DTB)

| Bus | Address | Part |
|---|---|---|
| 0xa90000 (QUP1 SE4, "i2c12") | 0x20 | Synaptics RMI4 touchscreen (`s3320` in the downstream DTB; S3706B per mainline) |
| 0xa88000 | 0x55 | TI bq27xxx fuel gauge (`bq27541` downstream, BQ27411 per mainline) |
| 0xa88000 | 0x26, 0x08, 0x0c | OnePlus fast charge MCU, two SMB1355 chargers |
| 0x890000 | 0x34 / 0x3a | NXP TFA9894 speaker amp / Maxim MAX98927 (one of the two is fitted) |
| 0x88c000 | 0x28 | NXP NFC |
| 0x89c000 | 0x42 | FSA4480 USB-C audio switch |

### SDM845 against our SDM670 drivers

Mainline Linux (`sdm845.dtsi`, `sdm845-oneplus-common.dtsi`, `sdm845-oneplus-fajita.dts`) was read as a register
reference only. No code was copied.

| Block | On SDM845 / fajita | For us |
|---|---|---|
| GIC, timer (PPI 19 = virtual), watchdog 0x17980000 | the same | as is |
| SPMI arbiter (0xc440000, obsrvr 0xe600000, cnfg 0xc40a000) | the same | as is |
| DWC3 0xa600000, QUSB2 v2 PHY 0x88e2000, qscratch 0xa6f8800 | the same | as is (we keep ABL's PHY values) |
| RPMh 0x179e0000, cmd-db 0x85fe0000, SMEM 0x86000000, TCSR mutex, QMP 0xc300000, SMP2P items | the same | as is; PM8998 rail names differ |
| cpufreq (OSM, L3 0x17d41000) | the same block | 4 + 4 cores, new step tables |
| LLCC | 4 banks + broadcast (SDM670: 2) | a new slice table |
| TSENS | the same addresses | check the sensor count |
| MSS 0x4080000, IPA v3.5.1, WCN3990 0x18800000, ADSP | the same IP | new carve-outs; the modem's SMEM board record (134) may need OnePlus values (unverified) |
| eMMC (`qcom_sdhci`) | not fitted | replaced by UFS: host 0x1d84000, QMP UFS PHY v3 0x1d87000, ICE 0x1d90000 |
| TLMM | the same tiles, other GPIO numbers | new pin numbers |
| Keys | power = PM8998 PON; volume = PM8998 GPIO 5/6 (not RESIN); the alert slider on TLMM 126/52/24 | small changes |
| Battery | the bq27xxx gauge over I2C, not the PMIC gauge; the PMI8998 charger is at SPMI SID 2 (PM660: SID 0) | a new small I2C driver |
| Haptics | the PMI8998 haptics block (unverified) | new |
| Audio | WCD9340 codec over SLIMbus, the TFA9894 amp, jack detection in the WCD934x | new, the largest block after UFS |

## Stages

Each stage is a RAM boot on the 6T; a stage is done when its exit check passes there. The gates in the workspace's
CLAUDE.md apply too: the build on atlas, CI green, bonito unaffected.

| Stage | Work | Exit |
|---|---|---|
| **OP0** device facts + DTB ✅ | This page's facts. Copy the live DTB and `boot_a` off the phone, read the boot image header (version, page size, load address), pick the appended DTB whose `qcom,msm-id` / `qcom,board-id` match (SDM845 v2.1, `<8 0 18801 41>`) as `private/fajita.dtb`. `fastboot getvar all` (product name for `phone.py`) | `private/fajita.dtb`; the header facts on this page |
| **OP1** ABL probes ✅ | bonito's boot probes (`bonito_variant/probes`), built with fajita's framebuffer (`FB_BASE=0x9d400000 FB_BYTES=0x9a3f80`). If the command-mode panel doesn't show RAM writes, find the MDP frame kick | green (AArch64 EL1) and blue (AArch32 EL0) on the 6T's screen |
| **OP2** the board ✅ | `fajita_variant` (`variant.conf`, `oneplus_fajita.cpp`: GIC, timer, framebuffer console, a minimal I/O map), an empty `sdm845_assp/` | `neo nkernsa fajita`: nkernsa results on the screen; then `neo kernel fajita`: 8 CPUs, the self-test extension, the user side up to the neoui launcher (no input yet) |
| **OP3** debug link ✅ | `qcom_dwc3` + `qcom_usbpower` + the ACM monitor, the watchdog and `AUTOFASTBOOT` (the H0 equivalent), plus the OnePlus fixes below | `phone.py` reads the log, takes `shot`s and sends the phone back to fastboot |
| **OP4** input ✅ | keys (PM8998 PON + GPIO 5/6), the RMI4 touchscreen on 0xa90000 (its GCC clock, pins, supply, reset) | neoui takes taps and the volume keys |
| **OP5** clocks ✅ | cpufreq for 4 + 4, TSENS (RPMh came with OP3; the LLCC table moved to OP10, only the modem needs it) | touch boost works; temperatures in Dev tools |
| **OP6** UFS, read-only ✅ | the UFS host + QMP PHY, link start-up, READ(10) on each LUN, GPT per LUN, `blk` monitor commands | every LUN's GPT listed; read speed measured; no write path built |
| **OP7** C:/E: on UFS | **the owner's call** (Ubuntu Touch owns `userdata`): a separate partition, or wipe | files survive a reboot |
| **OP8** panel | DCS over DSI0 to the S6E3FC2X01 (brightness 0–1023, sleep, wake) | brightness slider, screen off and on |
| **OP9** battery | the bq27xxx gauge, the PMI8998 charger at SID 2 | percentage and charging state in the top panel |
| **OP10** modem | the LLCC slice table (4 banks on SDM845), then MSS on OnePlus firmware: carve-outs, rmtfs, the SMEM board record | the modem registers; a call and an SMS |
| **OP11** Wi-Fi | WCN3990 with OnePlus board data | joins a WPA2 network |
| **OP12** audio and haptics | SLIMbus + WCD9340, the TFA9894 amp, the jack; PMI8998 haptics | call audio, the speaker, headphones; a vibration |
| **OP13** install | A/B install on UFS, like FS4/FS5 on the Pixel: **the owner's call** | the phone boots NeoSymbian by itself |

## Results

### OP0 (2026-11-26)

- **`boot_a` (Ubuntu Touch's):** Android boot header **v1** (header size 1648). Page 4096; kernel at base + 0x8000,
  tags at + 0x100; a gzip arm64 Image with `text_offset` 0x80000; three DTBs appended after it.
- **The appended DTBs:** the SoC's own (`board-id` 0), one each for SDM845 v1 (`msm-id 0x141 0x10000`), v2 (0x20000)
  and **v2.1 (0x20001)**. The phone is v2.1. ABL merges that base DTB with `dtbo` entry 18, which gives the live
  tree (`board-id <8 0 18801 41>`). `private/fajita.dtb` is the v2.1 base DTB; on atlas it is in
  `/DATA/dev/build/private/fajita.dtb`.
- **`fastboot getvar`:**
  - `product:sdm845` (not a codename: `phone.py --product` needs a board → product map in OP3);
  - `variant:SDM UFS`, `unlocked:yes`, `secure:yes`, `kernel:uefi`;
  - `max-download-size` 512 MB, logical block 4096;
  - slot a successful.
- **To fastboot:** `sudo reboot bootloader` in Ubuntu Touch (plain `adb reboot bootloader` lacks the permission),
  or **Volume Up + Volume Down + Power** held, which also gets a hung image back to fastboot. Since OP3, the monitor's `fastboot` and `AUTOFASTBOOT` do it with no buttons.

### OP1 (2026-11-26)

- **The ABL takes our boot image as is:** `tools/mkboot.py`'s header v0, gzip arm64 Image with `text_offset`
  0x80000, the v2.1 DTB appended.
- **`probe-a64`:** the screen turned all green. Our AArch64 code runs at EL1 with the MMU off, and its RAM writes to
  `cont_splash` (0x9d400000) reach the command-mode panel. ABL leaves the display refreshing from RAM, so no MDP
  frame kick is needed.
- **`probe-el0`:** all blue. AArch32 code at EL0 under our EL1 runs.

### OP2 (2026-11-26, kernel branch `fajita`)

- **Board:** `fajita_variant` (bonito's board file with the 6T's framebuffer; the GIC and the watchdog mapped) and
  an empty `sdm845_assp`. Built on atlas (workspace `fajita`) with `DTB=…/fajita.dtb`; RAM-booted with
  `fastboot -s <serial> boot` (`neo flash` waits for OP3's product map).
- **nkernsa:** the whole suite ran to "Tests Completed" with **0 failures**. Suspend/Kill/Migrate, with its ~140
  cross-CPU cases, is the long part.
- **ekern + the baseline user side:**
  - the user side is the atlas baseline's, with no Rust EXEs, so no neoui;
  - it boots to the 2010 window server's **eshell prompt** on the 6T's screen.
- **Next:** a ROM with neoui (`rust/` staticlibs + `exes.txt`) for the launcher. With no input drivers yet, taps wait
  for OP4.

### OP3 (2026-11-26, kernel `58470a68`)

The Pixel's USB console drivers sent the 6T into "QUALCOMM CrashDump Mode": a secure-side bus error, which happens even
with download mode off. OnePlus's ABL leaves USB unlike Google's after `fastboot boot`. Each gap was found with
breadcrumbs pinned on screen and photographed, with the root-cause research by Codex.

| Gap left by OnePlus ABL | Seen as | Fix (`sdm845_assp/`) |
|---|---|---|
| QUSB2 PHY powered down (`0x210 = 0x23`, PLL status `0x04`; Google's ABL: `0x17`) | the first endpoint command hangs | `A64UsbPhyInit`: GCC PHY reset, then the phone's own init table (live DT `qcom,qusb-phy-init-seq`), PLL ready (`0x17`) |
| no SMMU match for USB's stream `0x740` (unmatched streams fault) | the first TRB fetch (first DMA read) hangs | `Smmu_IdentityMap(0x740, 0)`, the identity context IPA uses on the Pixel (downstream: `qcom,smmu-s1-bypass`) |
| (precaution) NoC bandwidth for USB | | BCM votes APPS→USB (`SN12`, `SN3`, `CN0`) and USB→DDR (`SN11`, `SN0`, `SH0`, `MC0`); `ACV` left out |
| the command DB is not where mainline says | | its base from the AOP's pointer at `0x0c3f000c` (two candidates mapped) |
| download mode on | every reset or watchdog bite → CrashDump | `qcom_dload.cpp`: off at boot (an SCM I/O write of 0 to `TCSR_BOOT_MISC_DETECT`), so resets are plain resets |
| PON's first SPMI channel belongs to another EE | the reboot-reason write was refused (`-21`), so `fastboot` landed in Ubuntu Touch | prefer the channel the apps EE owns (like Linux `pmic_arb_read_apid_map_v5`) |

- **Also fixed:** the aggregate USB AXI clock is at GCC `0x8201c` on SDM845, and the cold path no longer writes the
  shared clkref gates.
- **Not needed on a RAM boot:** ABL leaves the USB GDSC and clocks on. The cold path (an installed boot, OP13) is still
  untested.
- **The two-phone hazard:** both boards' consoles enumerate as "Symbian Pixel debug". With the Pixel also running,
  pass `--monitor-port /dev/cu.usbmodemN` (or `--device`). `ANDROID_SERIAL=<the 6T's serial>` only picks the fastboot device;
  `phone.py`'s fastboot wait honours it since OP3.

### OP4 (2026-11-26, kernel branch `fajita`)

The 6T gets copies of bonito's `a64_keys.cpp` and `a64_touch.cpp` (`fajita_variant/specific/fajita_keys.cpp`,
`fajita_touch.cpp`) with its own wiring (owner: the Pixel's files stay untouched; merge them with a board table later).
The wiring comes from the live DT.

| Part | 6T wiring |
|---|---|
| Power | PM8998 PON `0x810` bit 0 |
| Volume Down / Up | PM8998 GPIO5 / GPIO6 (`0xc410` / `0xc510` bit 0, active low); the Up + Down 2 s → fastboot combo kept |
| Touch IC | Synaptics RMI4 (S3706) at I2C 0x20; sensor range 1079 × 2339 |
| I2C | SE12 = QUP wrapper 1 SE4 at `0xa90000`; GCC branch `0x184d4`, RCG `0x184d8`, vote bit 26; `qcom_geni_i2c` engine 0 |
| Pins | SDA/SCL gpio49/50 (north, `qup12`), reset gpio99 (north), attention gpio125 (**east** on SDM845) |
| Supplies | 1.8 V: TLMM gpio88 (east) driven high; 2.8 V: RPMh `ldoa28` at 3.008 V |

**Verified:** all three keys report down/up; touch has 54 presses and releases, 0 errors, 0 dropped (taps and
multi-finger swipes); Volume Up + Down held returns the phone to fastboot.

**Left out:** the hall sensor (gpio124), the alert slider (TLMM 126/52/24), and the touch interrupt (polled, as on the
Pixel).

### neoui on the 6T (2026-11-26)

**Working:** the neoui launcher and apps run on the 6T. The owner opened Clock, Settings, Terminal, UI kit and Dev
tools, went home after each, swiped and used the keys. The log shows no fault and no panic; touch counted 126
presses and releases with 0 errors.

- **How it's built:** atlas workspace `fajita-ui`, a copy of `armv8p` (build `9f4e9df`, owner's OK), with the kernel
  on branch `fajita` (from a git bundle; nothing pushed). Then:
  `DTB=…/fajita.dtb AUTOFASTBOOT=1500 USBDEBUG=1 ROFS=1 ROFS_CORE='\.dll$' neo kernel fajita`. No `EMMC_C`: the 6T has
  no eMMC, so C: is the RAM drive.
- **The bootloader's size limit:** OnePlus/Qualcomm ABL unpacks the gzip kernel at base + 0x80000 and allows only
  up to its device-tree address (`TagsAddress` 0x3200000, the stock `QcomModulePkg.dec` value), so the unpacked image
  must stay under **~49.5 MB**. Past that, `fastboot boot` says OKAY and the phone silently stays in fastboot. Google's
  ABL on the Pixel takes the full 67.7 MB image.
- **The trimmed image:** `fajita-ui/build/rust/exes.txt` is the full list (kept as `exes.full.txt`) minus NEOFILES
  (11.8 MB), NEOPHONE, NEOCONT, NEOMSG (9.4 MB together) and NEOWEB/NEOWEBE. That makes the image 41.7 MB. Their
  launcher icons stay, and tapping them does nothing.
- **The hardware daemons** (MODEMD, HWHUB, AUDIOD, WIFID, NEONET, GNSSD) start and cope with no hardware: HWHUB
  reports "no hardware", NEONET falls back to loopback. The status bar shows "Starting modem…".
- **Next, the ramdisk route:** ship Z:'s ROFS as the boot image's ramdisk (ABL loads it at base + 0x3400000, up to
  base + 0x5700000, 35 MB), and have `a64_medrofs` find it through the DTB's `linux,initrd-start`. The core image
  (≤ ~45 MB) plus the ramdisk (≤ ~33 MB) then hold the full ROM, until Z: comes from UFS (OP6/OP13).

### OP5 (2026-11-26)

`sdm845_assp/qcom_cpufreq.cpp` and `qcom_tsens.cpp` are copies of the SDM670 drivers. The OSM and TSENS blocks sit at
the same addresses on SDM845, and the frequency tables are read from the hardware at boot. The only change is SDM845's
core split: cpu 0–3 silver (capacity 611), 4–7 gold (1024).

| Domain | Steps | Range | ABL leaves it at |
|---|---|---|---|
| silver (A55, cpu 0–3) | 18 | 300–1766 MHz | 1612 MHz |
| gold (A75, cpu 4–7) | 27 | 825–2803 MHz | 825 MHz |
| L3 | 14 | 300–1478 MHz | 940 MHz |

**Verified:**
- **Touch boost:** the first touch puts all three domains at their top steps, and they return to ABL's steps ~3 s after
  the last touch.
- **TSENS:** 21 of 21 sensors valid; 34.7 °C at rest, 40.2 °C after a few seconds boosted.

**Not checked:** the Dev tools temperature page.

### OP6 (2026-11-26)

`sdm845_assp/qcom_ufs.cpp`: ABL leaves UFS up, so the driver **adopts** ABL's host and link instead of bringing
them up. The QMP PHY tables, link start-up and supplies are not needed and not written (`shortcut:` in the file).
- **What ABL leaves** (`blk info`, which reads the host only after its GDSC and clocks check on):
  - the host is enabled, the device is present, and both request lists are ready (HCS 0x10f);
  - the link is in fast mode, HS-G3 series B, with **1 lane each way** (the DT says 2);
  - its transfer list is in its own memory, and the task list is stopped;
  - the PHY is started and ready.
- **SMMU:** UFS's streams 0x100/0xf already match an SMR that routes to context bank 2, with translation off
  (SCTLR.M = 0). DMA is therefore physical, as for the Pixel's eMMC, and `Smmu_IdentityMap` leaves it alone.
- **`blk init`:** points the host at our own transfer list, sends NOP OUT, then TEST UNIT READY and
  READ CAPACITY(10) on LUNs 0–7. Six answer, all with 4096-byte blocks.
- **Read only by construction:** one function builds every command, and it refuses any opcode but TEST UNIT READY,
  REQUEST SENSE, INQUIRY, READ CAPACITY(10) and READ(10). There is no `A64BlkDev_Write`. `A64BlkDev_Init` declines,
  so C: stays the RAM drive.

| LUN | Size | Holds |
|---|---|---|
| 0 | 116 GB | `ssd`, `persist`, `misc`, `param`, `keystore`, `frp`, `op2`, `config`, `system_a` (4.6 GB), `system_b` (1 GB), `odm_a/b`, `userdata` (110 GB) |
| 1, 2 | 4 MB each | `xbl_a` + `xbl_config_a`; `xbl_b` + `xbl_config_b` |
| 3 | 32 MB | `cdt`, `ddr` |
| 4 | 3 GB | the A/B firmware set: `aop`, `tz`, `hyp`, `modem` (120 MB), `abl`, `dsp`, `boot` (64 MB), `vendor` (1 GB), `vbmeta`, `dtbo`, `LOGO`, the `fw_ufs*` images; then `devinfo`, `splash`, `logdump`, `minidump` and others |
| 5 | 32 MB | `modemst1/2`, `fsg`, `fsc` |

**Verified:**
- **Read speed:** 64 MB in 303 ms, about **216 MB/s**, polled at one lane.
- **The data itself:** `boot_a`'s first 4 MB, read through `blk dump` from an unaligned 512-byte sector, has the same
  SHA-256 as the copy taken through Ubuntu Touch.
- **The rest of the phone:** the UI keeps running with no faults, and `drivers` lists `ufs` as partial.

Monitor commands:
- `blk info`: ABL's state;
- `blk init`: adopt;
- `blk luns`: every LUN's GPT;
- `blk lun N`: the LUN that `blk read`/`blk dump` use, in 512-byte sectors;
- `blk speed`.

### The ramdisk route (2026-11-26)

`ROFS=ramdisk` (kernel#45, docs filesystem.md FS7) works on the 6T unchanged:
- The kernel carries only the ROFS's 4 KB header and its hashes, and the image itself is the boot image's ramdisk.
- ABL put the ramdisk at 0x83700000–0x84eff000 and named it in `/chosen`; the kernel keeps that range out of
  its RAM banks.
- On boot, `[media] ROFS from the ramdisk`, and the hash check passes for every block.

**The ramdisk's own limit:** ABL loads it below the hypervisor region at 0x85700000, so it gets about **35 MB**. With
NEOFILES added, the ROFS was 37.5 MB, so NEOFILES goes into the core ROM instead (it runs in place there).

| | Kernel (core ROM) | Ramdisk (ROFS) |
|---|---|---|
| Limit on the 6T | ~49.5 MB | ~35 MB |
| Trimmed list + NEOFILES | 28.6 MB | 25.2 MB |

The build: `ROFS=ramdisk ROFS_CORE='(?i)\.dll$|neofiles\.exe$' neo kernel fajita` (plus `DTB`, `AUTOFASTBOOT`,
`USBDEBUG`), with NEOFILES back in `exes.txt`.

**Verified:** Files opens and browses C: and Z:. The rest of the left-out apps (NEOPHONE, NEOCONT, NEOMSG, NEOWEB,
about 14 MB together) would fit in the room left: about 21 MB in the kernel and 10 MB in the ramdisk.

## Open questions

- Whether ABL applies `dtbo` on `fastboot boot` (the kernel reads `/memory` and `/reserved-memory` from what it is handed).
