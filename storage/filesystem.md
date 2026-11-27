<!-- SPDX-License-Identifier: Apache-2.0 -->
# File system plan: Symbian's storage on the Pixel 3a XL

Part of [Storage](README.md) · Status: active · Updated: 2026-11-26

First written 2026-11-07 after H2.3; each stage's status is in [Stages](#stages). Android is not kept on the phone, so
NeoSymbian owns the eMMC, except for the partitions listed under "Never touched".

The design stays Symbian's own, from the 2010 sources:
- F32 with its file system plugins;
- FAT32 on the writable drives;
- ROFS and the composite file system for `Z:`.

A new file system is written only if one of these fails in daily use (see "Later").

## Where we start

The state before FS1 (2026-11-07, after H2.3): F32 with Symbian's own plugins, `C:` as 2000 MB FAT16 from the obsolete
`sfat`, `Z:` as the whole ROM in RAM. Moved to [history/filesystem-start.md](history/filesystem-start.md).

## Target layout

Partitions are found by their GPT name, as `qcom_sdhci.cpp` does now. The GPT itself is never rewritten. The one
exception, the A/B slot attributes, is a gate in FS5b.

| GPT partition | Use | File system |
|---|---|---|
| `boot_a`, `boot_b` | Kernel and core ROM: the minimum to start the file server and mount `Z:` | XIP ROM in `boot.img` |
| `system_a`, `system_b` (~2.5 GB each) | `Z:`, the rest of the OS, one copy per slot | ROFS, with a hash tree |
| `vendor_a`, `vendor_b` | Spare: crash dumps, recovery tools, later swap for data paging | — |
| `userdata` (51 GB) | `C:` and `E:`, through our own MBR at the start of the partition | FAT32 |

**Inside `userdata`.** It starts at LBA 17359872, which is only 512 KiB aligned. Every offset below puts the drives
on 4 MiB boundaries of the whole disk, so FAT's data area can line up with the eMMC's erase groups.

| Userdata sectors | What |
|---|---|
| 0 … 7167 | Our MBR (sector 0), then unused |
| 7168 … +8 GB | `C:` (MBR type 0x0C, FAT32) |
| next 4 MiB boundary … end | `E:` (MBR type 0x0C, FAT32, large clusters) |

`C:` sits at this offset from FS1 on, so FS3 only adds the MBR and `E:`, and the files on `C:` survive FS3.

| Drive | Size | What | Exposed over USB |
|---|---|---|---|
| `Z:` | ROFS + core ROM | System binaries and resources, read-only | no |
| `C:` | 8 GB | Settings, installed apps, `\private\<SID>`, `\sys\bin` for installed code. `FS_SYSTEM_DRIVE` | never |
| `D:` | RAM | Temporary files | no |
| `E:` | the rest of `userdata` (~42 GB) | User media and documents ("mass memory", as on the N8) | yes |

Why `C:` and `E:` are separate:
- USB mass storage has to unmount the drive it shares. Sharing `E:` keeps `C:`, and so the running system, mounted.
- A full media drive cannot block the system's own writes.
- ScanDrive on a small `C:` takes seconds, not minutes.

Data caging (`\sys\bin`, `\private`, `\resource`, enforced by capabilities) is checked by F32 on paths, so it works
the same on any file system.

### Never touched

`modemst1`, `modemst2`, `fsg`, `persist`, and the boot chain (`xbl*`, `abl*`, `tz*`, `hyp*`, `rpm*`, `keymaster*`,
`devcfg*`, …). They hold the IMEI, radio and sensor calibration, and the bootloaders. Losing them disables the modem
or bricks the phone.
The modem code reads `modemst1/2`, `fsg`, `fsc`, `modemcal` and `modem_a` read-only ([modem.md](../hardware/modem.md)); writing them is gate G4.

**The allow-list.** The block driver keeps a list of the partition names it may write: `userdata`, `system_a/b` and
`vendor_a/b`.
- Writes anywhere else fail in the driver, whatever the caller asks for.
- Each entry is enabled only when its stage is approved. At first only `userdata` was; FS4b added `system_a/b` (see
  FS7's facts).

### Safety gates

Some stages went past what was approved at first: RAM boot only, and eMMC writes only inside `userdata`. Each needs
the owner's explicit approval at the time (G1–G3 were given for FS4b and FS5b):

| Gate | What it allows | Stage |
|---|---|---|
| G1 | Writes to `system_a/b` by our bounded driver | FS4b |
| G2 | The first write to `boot_a/b`: the phone then boots NeoSymbian without `fastboot boot` | FS5b |
| G3 | Changing the A/B slot attributes: GPT entry attribute bits, rewritten with both GPT copies and their CRCs, or `fastboot --set-active` from a PC | FS5b |
| G4 | Writes to the radio partitions (`modemst1`, `modemst2`, `fsg`, `fsc`, `modemcal`, `persist`, `modem_a/b`), e.g. rmtfs persisting the modem's EFS | [modem.md](../hardware/modem.md) C12 |

## Stages

Each stage is usable on its own. FS1–FS3 complete roadmap stage H2 (storage).

<!-- stages -->
| Stage | What | State | Updated | Next / evidence |
|---|---|---|---|---|
| FS1 | The FAT32 plugin: 8 GB C: | done | 2026-11-07 | kernel 6c404ef, build 584ba4e; f32test FAT tests not in the ROM |
| FS2 | eMMC speed: DDR52, write allow-list | done | 2026-11-07 | kernel fc0c929: 70 MB/s read, 39 MB/s write |
| FS3 | C: and E: on userdata, TRIM | done | 2026-11-07 | kernel 92586a0; survives a watchdog reset during a copy |
| FS4 | Z: on ROFS, from RAM then flash | done | 2026-11-07 | kernel f93a432 (FS4a), 2fd7deb (FS4b); the phone is installed |
| FS5 | Block hashes and A/B updates | done | 2026-11-08 | kernel 20b8f44 (FS5a), 5b0ba6b (FS5b); a bad update rolls back |
| FS6 | USB mass storage for E: | parked | 2026-11-08 | researched; blocked on USB power on a normal boot (known issues) |
| FS7 | Install a big Z: | active | 2026-11-26 | step 0 done (ROFS=ramdisk, kernel#45); plan steps 2–4 open |
| Later | Encryption, journaled C:, exFAT, MTP, paging, CQHCI | open | — | each when needed; encryption before personal data (KRN-016) |
<!-- /stages -->

Every stage is tested on QEMU first (virtio-blk disk), then on the phone with a RAM boot, with the watchdog armed and
`lastlog` for crashes.

### FS1: the FAT32 plugin

**Done 2026-11-07** (kernel `6c404ef`, build `584ba4e`): every exit below passed except the f32test FAT tests, which
the ROM doesn't carry yet. The on-phone log doesn't show whether ScanDrive ran.

Steps:
1. **`build/emitter/build_elocal_fsy.py`:** the source set of `efat32.mmp` plus `fs_utils`, still written out as
   `ELOCAL.FSY` with UID3 0x100000d6. The build's "no writable static data" check stays.
2. **`build/tools/mkfat.py`:** VFAT long-name entries (the LFN slots and their checksum) for names that are not 8.3,
   so the syborg `c_drive.img` gets long names too.
3. **`estart.txt`:** `C: 0 ELOCAL FAT 0 FS_FORMAT_CORRUPT,FS_SYNC_DRIVE,FS_SCANDRIVE,FS_SYSTEM_DRIVE`.
4. **`qcom_sdhci.cpp`:** the `C:` window moves to userdata + 7168 sectors and grows to 8 GB. The 2000 MB FAT16 test
   volume is dropped, and the new window is formatted once.
5. **`a64_medblk.cpp`:** report `iEraseBlockSize` (the eMMC's erase group from EXT_CSD; 0 on virtio). `sfat32`'s
   format then aligns the first data sector to it (`sl_fatmisc32.cpp` `AdjustFirstDataSectorAlignment`).

**Exit:**
- A long file name (`md c:\Long Directory Name`) round-trips on `C:` across a reboot.
- `estart` formats the 8 GB `C:` as FAT32, and ScanDrive runs at boot.
- QEMU still boots the 256 MB disk, the no-disk (RAM drive) case, and neoui.
- The f32test FAT tests (`t_fat32`, `t_scan`, `t_vfat`) pass where the ROM carries them.

**Risk:** `sfat32` may carry writable static data, which our DLL format can't hold. If it does, find and fix the
cause; don't drop the check.

### FS2: eMMC speed

**Done 2026-11-07** (kernel `fc0c929`): the eMMC runs 8-bit DDR52 at boot. Measured on the phone with `blk speed`
(64 MB sequential, through the driver's 64 KB transfers):

| Mode | Read | Write |
|---|---|---|
| legacy 1-bit 19.2 MHz | 2.2 MB/s | 2.2 MB/s |
| HS52 8-bit 50 MHz (non-cached bounce) | 26 MB/s | 19 MB/s |
| DDR52 8-bit, non-cached bounce | 35 MB/s | 23 MB/s |
| **DDR52 8-bit, cached bounce** | **70 MB/s** | **39 MB/s** |

- The bus alone reads 79 MB/s (`blk speed raw`). Copying out of a non-cached bounce buffer cost more than the bus,
  so the data buffer is cached, with `Cache::SyncMemory*` around each transfer; the ADMA descriptors stay
  non-cached. Bigger transfers (step 4) and HS200 (step 3) were not needed.
- The 50 MHz clock comes from GPLL0 / 12 (CFG 0x117) and DDR52's 100 MHz core clock from GPLL0 / 6 (0x10b), not
  GPLL0_EVEN.
- Each mode step re-reads EXT_CSD and compares it; a failure restarts the card from CMD0 one mode lower.
  `EMMC_MODE=0..2` caps the mode at build time, and `blk mode <n>` switches it at run time.
- The allow-list: `blk guard` refuses LBA 0 (the GPT), `persist` (outside the list), `system_a` (listed, not
  enabled) and the sector after `userdata`, and allows both ends of `userdata`.
- Three boots in a row reached DDR52; `C:`'s files (written in legacy mode in FS1) read back, and new ones persist.

Steps (`qcom_sdhci.cpp`, with Linux `sdhci-msm.c`, `sdhci.c` and `gcc-sdm845.c` as references), each one measured
before the next:
1. **8-bit HS52:**
   - CMD6 sets EXT_CSD `BUS_WIDTH` = 2 and `HS_TIMING` = 1;
   - the host gets an 8-bit bus and high speed;
   - the GCC sdcc1 clock goes to 50 MHz (GPLL0 / 12).
   - No tuning. About 45 MB/s expected.
2. **DDR52:**
   - `BUS_WIDTH` = 6 (8-bit DDR), UHS mode DDR50;
   - the core clock goes to 100 MHz (GPLL0 / 6), because the msm host runs at twice the card clock in DDR modes.
   - No tuning. About 90 MB/s expected.
3. **HS200, only if DDR52 is not enough:**
   - `HS_TIMING` = 2, core clock 192 MHz (GPLL6 / 2);
   - the msm DLL init, then CMD21 tuning;
   - CX voted up to the device tree OPP's level (`Arc_Vote`).
4. **A larger ADMA bounce buffer** (256 KB, several descriptors), if the per-command cost limits throughput.
5. **The writable-partition allow-list by GPT name,** with one window per partition. A monitor command checks the
   guard without issuing I/O.
6. **`blk speed`:** a monitor command that reads 64 MB and prints MB/s.

**Exit:**
- More than 50 MB/s sequential read on the phone.
- A write aimed at `persist` is refused by the guard.

### FS3: `C:` and `E:` on `userdata`

**Done 2026-11-07** (kernel `92586a0`). This completes H2.
- The media driver (`a64_medblk.cpp`) reads our MBR in userdata sector 0, else writes the default layout once. On
  the phone: `C:` = userdata + 7168, 16777216 sectors (the FS1 drive, kept with its files); `E:` = + 16784384,
  87998431 sectors (42 GB, FAT32 with 32 KB clusters). The window below it is now all of userdata.
- ELOCD's partition checks (`CheckAndAdjustForPartition`) keep `C:`, `E:` and the MBR apart.
- TRIM: sfat32's delete notifications reach the eMMC as CMD35/36/38 (TRIM). They never report an error upward,
  because a failed DeleteNotify faults the file server.
- Verified:
  - QEMU: 9 GB (`C:` + `E:`), 256 MB (`C:` only) and no disk (the RAM drive);
  - the phone: `C:` kept; `E:` formatted and persistent; TRIM 1 with 0 errors; a watchdog reset during a copy to
    `E:` leaves both drives clean (`chkdsk`); the neoui ROM.
- Also fixed: the boot re-init retries, since the first CMD3 after ABL sometimes times out.

Steps:
1. **The MBR in userdata sector 0,** laid out as above.
   - It is written once, and only when `C:`'s window already starts with a FAT boot sector, so `C:` is kept.
   - It is read the way Symbian's MMC driver reads partition tables (`kernel/eka/drivers/medmmc/emmcptn.cpp`).
2. **`a64_medblk.cpp`** exposes two partitions as local drives 0 (`C:`) and 1 (`E:`).
3. **`estart.txt`** adds `E: 1 ELOCAL FAT 0 FS_FORMAT_CORRUPT,FS_SCANDRIVE`. The format picks large clusters by size.
4. **TRIM:** `sfat32`'s delete notifications (`DLocalDrive::EDeleteNotify`) become eMMC ERASE_GROUP_START/END +
   ERASE with the TRIM argument, inside the window. On virtio they are a no-op.

**Exit:**
- Files on `C:` and `E:` survive a reboot.
- Force-reset the phone during a large copy (the monitor's `wdt`). The next boot's ScanDrive repairs the drive.

### FS4: `Z:` on ROFS

**Done 2026-11-07** (FS4a kernel `f93a432`, build `e1239a5`; FS4b kernel `2fd7deb`). The phone is installed:
- `boot_a` holds the kernel and the core ROM (857 KB);
- `system_a` holds the ROFS (7.6 MB).

FS4b differs from the plan below:
- the ROFS is written to `system_a` by an installer kernel image (`ROFS=1 ROFS_INSTALL=1`), which needs no
  `blk load` over USB. It writes only the 64 KB chunks that differ and reads each one back;
- the installed core (`ROFS=flash`) carries the ROFS header and mounts `system_a` only if its header matches exactly.

- **FS4a, ROFS from RAM (no new writes):**
  - build `rofsbuild` from `oss.FCL.sftools.dev.build` in the toolchain image;
  - split the obey files into a core ROM (kernel, file server, the drivers needed to mount `Z:`) and one ROFS image;
  - carry the ROFS image in `boot.img` next to the core, behind a read-only RAM media drive;
  - build `EROFS`/`ECOMP` like `ELOCAL`;
  - mount `Z:` through the composite file system (`FS_COMPOSITE` in `estart.txt`).
- **FS4b, ROFS on flash (gate G1):**
  - `blk load system_a` writes the ROFS image to the slot over the USB debug link, through the bounded driver;
  - the RAM media drive is replaced by a read-only window on `system_<slot>`.

**Exit:**
- FS4a: the phone boots with `Z:` composed of the core ROM and the ROFS image.
- FS4b: `Z:` comes from flash, and `boot.img` shrinks to the core.

### FS5: updates and integrity

**Done 2026-11-08** (FS5a kernel `20b8f44`; FS5b kernel `5b0ba6b`).
- **FS5a:** a flat SHA-256 per 4 KB block (no tree), carried in `boot.img` (`a64_medverity.cpp`, a
  `DMediaDriverExtension` derived from Symbian's NFE test extension, with the kernel's own `SHA256`). A changed block
  fails its read with `KErrCorrupt`. Since kernel `fc4ab26` the hash uses the CPU's SHA-256 instructions (1 MB in 2 ms
on the phone; `a64_sha256.S`, self-tested at boot, the C one as fallback), so the check costs almost nothing.
- **FS5b** (`qcom_bootctrl.cpp`):
  - the kernel finds its slot from the GPT and reads `system_<slot>`;
  - it marks the slot "successful" through HAL `ENeoHalBootOk`. **neoui calls it once the launcher is drawn**
    (neoui `eb0db62`), so every install marks itself; the monitor's `slot ok now` remains for tests;
  - **it counts the tries itself**, because this phone's ABL counts them only on fastboot RAM boots;
  - a kernel fault restarts the phone through the watchdog, so a bad update rolls back.
  - Updates: `fastboot flash boot_b`; `system_b` is written by a `ROFS_INSTALL` image RAM-booted on slot b, since
    ABL refuses `system_*` outside fastbootd; then `fastboot set_active b`.
  - Tested on the phone: update into b, then a broken b rolls back to a by itself.
  - **Installs** 2026-11-08 to 2026-11-17 (revisions, sizes, build steps, images): moved to
    [history/fs5-install-log.md](history/fs5-install-log.md).
  - ABL's quirks are in [known issues](../history/known-issues-fixed.md#phone-slot-a-runs-out-of-retries-abl-switches-to-slot-b-test-images-may-die-with-a-black-screen) (fixed by FS5b).

- **FS5a, integrity (no gates):** a hash tree over the ROFS image, checked block by block in a media driver
  extension (`DMediaDriverExtension`). Its root hash is in the core ROM.
- **FS5b, A/B updates (gates G2 and G3):**
  - write updates to the inactive slot's `boot_x` and `system_x`;
  - switch with ABL's A/B slot attributes, so a failed boot falls back to the old slot.

**Exit:**
- FS5a: a changed `Z:` block is caught on read.
- FS5b: a bad update rolls back by itself.

### FS6: USB mass storage

**Status 2026-11-08:**
- **Decided:** Symbian's own stack, reused unchanged: usbcc + the usbc LDD + smassstorage (MSFS.FSY), with a new
  DWC3 PSL derived from `bsptemplate/.../pa_usbc.cpp`. `USBMS.EXE share|unshare` and a "Share E:" switch in the Dev
  tools app complete it.
- **Researched, not started.** Things to handle:
  - E: must report `KDriveAttRemovable`, or MSFS skips it;
  - the built-in-LDD loader needs an `eusbc`→`usbc` alias;
  - `usbcsc_bil.dll` must be in the ROM;
  - the debug console and mass storage take turns owning the controller.
- **Blocked on the installed phone** by USB power on a normal boot. It works on fastboot RAM boots, where ABL powers
  USB. See [known issues](../known-issues.md#phone-usb-power-on-a-normal-boot-doesnt-work-yet-parked-2026-11-08).

- **Spike first:** `smassstorage` speaks to the Symbian USB client LDD (`RDevUsbcClient`, `kernel/eka/drivers/usbc`).
  Our `qcom_dwc3_acm.cpp` is a standalone polled gadget for the debug console. The spike picks between:
  - a DWC3 controller driver (PSL) under the usbc framework, with the debug serial port kept as an interface that
    works before the user side starts;
  - or the mass-storage protocol (bulk-only transport) inside our gadget, with `E:` dismounted by F32 while it is
    shared.
- **Then:** `E:` is shared with a PC on a USB composite device, next to the debug serial port.

**Exit:** a PC sees `E:` and copies files while the phone keeps running.

### FS7: installing a big system area (Z:)

**Status 2026-11-26: step 0 (Z: as the ramdisk) works on the Pixel; the rest of the plan is not started.**

**The problem.** Test images and the installer carry the whole ROFS (Z:) *inside the kernel* (`ROFS=1`, and
`ROFS_INSTALL=1` for `a64_medrofs.cpp` `Install()`). The Pixel's bootloader refuses `fastboot boot` once the *unpacked*
kernel passes about 71.6–72.2 MB ("Volume Corrupt"; measured by the Settings session, [settings.md](../neoui-shell/settings.md#board-parity-owner-2026-11-26)).
The ~28.6 MB `boot.img` figure used before was only the gzipped stand-in for it. About 15.6 MB of kernel and core ROM
plus a 52 MB ROFS was at the limit, so Files with video and PDF (NEOFILES, 17.5 MB; 12.75 MB built for size) didn't
fit, and every app will keep growing.

**Step 0, done: Z: as the boot image's ramdisk (`ROFS=ramdisk`, kernel `rofs-ramdisk`).**
- The kernel carries only the ROFS's first 4 KB and its per-block hashes, as `ROFS=flash` does. `rofs.img` becomes
  the `boot.img` ramdisk (`mkboot.py`).
- ABL copies the ramdisk raw and names it in the DTB's `/chosen` `linux,initrd-start/end`. The bootstrap
  (`a64boot.cpp` `ParseDtb`) keeps that range out of the RAM banks and passes it in the super page (`iReserved[0..1]`).
- `a64_medrofs.cpp` maps it read-only and serves Z: from it when it starts with the carried header. The hash layer
  (FS5a) checks every block against the hashes in the kernel, so the ramdisk is as trusted as `boot.img`.
  `ROFS_INSTALL` copies from it.
- **The ramdisk doesn't count against the kernel limit.** The tp2a test kernel (71.6 MB unpacked) plus a 60 MB
  ramdisk booted. A 16.8 MB kernel plus a 64 MB Z: (Files, X-plore and Frozen Bubble in it) booted with "ROFS from
  the ramdisk (62500 KB): this build's" and every hash matching (2026-11-26).
- `fastboot boot` takes up to `max-download-size` = 0x10000000 (256 MB) on bonito. The C1 Linux test RAM-booted a
  91 MB ramdisk on this phone before.
- Test images: `ROFS=ramdisk ROFS_CORE='\.dll$' DISK_C=1 … neo kernel bonito` (`DISK_C`, C: on the phone's storage, was `EMMC_C` until 2026-11-27; the old name still works). Installers can use
  `ROFS=ramdisk ROFS_INSTALL=1` (not tried yet; it writes `system_x`, the owner's call).

**How others do it** (Codex for Android, a Claude agent for the Linux phones, 2026-11-26):
- **Nobody RAM-boots an installer that carries the system.** Boot images hold only a kernel and a small starter.
- **First install: the host flashes the system image with fastboot.** Fastboot splits an image bigger than the
  bootloader's `max-download-size` into sparse pieces and writes them one after another to the same partition, so the
  size doesn't matter (AOSP `fastboot.cpp` `load_sparse_files`). This is how Pixel factory images work (`flash-all.sh`
  → `fastboot update`), and how Ubuntu Touch, Droidian and postmarketOS install on this same phone.
- **Updates: the running system writes the other slot.** It verifies the slot, switches to it, marks it good after
  boot, and the bootloader rolls back otherwise. Examples are Android A/B `update_engine` (streamed payload, REPLACE /
  SOURCE_COPY / diff operations), RAUC, SWUpdate and Mender. RAUC's adaptive updates keep a SHA-256 per 4 KB block and
  fetch only the changed ones, the same shape as our FS5a hashes.
- **Big privileged apps:**
  - Android keeps them in the system image (`/system/priv-app`); updates land in `/data`, signature-checked.
  - Linux phones put apps on the writable partition, with permissions from a signed manifest checked at install.
- **Size:** compressed read-only file systems (EROFS, SquashFS). Our E32 images are stored uncompressed
  (`build/emitter/e32image.py`), though the 2010 loader reads deflate and bytepair images. NEOFILES gzips from
  17.5 to 7.4 MB.

**Our facts:**
- **Flashing was refused.** `fastboot flash system_a` was refused by ABL ("should be flashed in fastbootd"), and
  fastbootd is gone on our layout. Android documents a force mode of `fastboot flash` for retrofit devices; it is
  untested here.
- **The eMMC allow-list already permits `system_a/b` writes** (`qcom_sdhci.cpp`). The monitor's `blk put` takes only
  `vendor_*`.

**Plan:**
1. **NEOFILES stays in Z:**, as Android keeps privileged apps in the system image. No loader or capability change.
2. **Fastboot first.** On the inactive slot only, with the owner's OK:
   - `fastboot getvar max-download-size` and `partition-size:system_b`;
   - `fastboot flash system_b rofs.img`, then its force mode if refused;
   - read it back and compare the hash, then RAM-boot a `ROFS=flash` core on b.
   - If ABL takes it, `neo` gets an install step (`boot_x` + `system_x`) and the installer no longer carries the ROFS.
3. **Otherwise, the writer moves into the running system.** A TCB updater writes the inactive `system_x` from
   `rofs.img` on E: (fetched over Wi-Fi), with the 64 KB chunk writer and read-back. It sets the slot with
   `qcom_bootctrl`, and neoui's boot-OK mark gives the rollback. The RAM-booted installer reads the same file from E:
   for first install and recovery. This is also the base of over-the-air updates.
4. **Size, beside it:**
   - Files builds for size except its hot code (files `files-size`: 12.75 MB; merged once the Pixel shows no
     slowdown).
   - Compressed E32 images (bytepair), measured on NEOFILES.

With step 0 the RAM-booted installer is no longer size-bound (up to the 256 MB download limit), so steps 2–3 are
about updates from the running system rather than a blocker.

**Exit:** a ROFS over 60 MB is installed on the inactive slot, and the phone boots it with Files from Z:.

## Later (daily-phone stage)

| Item | Plan | When |
|---|---|---|
| Encryption | AES-XTS as a media driver extension on `userdata`, with the key derived from the user's PIN. The SDM670's inline crypto engine (ICE) speeds it up later. A hardware keystore through TrustZone is a separate, large job. | Before the phone holds personal data |
| Journaled `C:` | Only if rugged FAT fails in daily use. A new `.fsy` plugin: plugins run inside the user-side file server, so it can be mostly Rust behind a thin C++ layer (`CFileSystem`, `CMountCB`, `CFileCB`, `CDirCB`). ext4 is the pick: it has a journal, files over 4 GB and hashed directories, and Linux tools (`mkfs.ext4`, `e2fsck`, `debugfs`, mounting on the build server) build and check the images. littlefs is power-safe but slow on large volumes; F2FS is too complex. | Only if needed |
| exFAT on `E:` | For files over 4 GB (video). Not in the 2010 sources; a new plugin. | When FAT32's 4 GB file limit matters |
| MTP | Replaces mass storage so `E:` stays mounted on the phone too. Symbian's MTP framework (`mw.mtpfws`) was deleted from the org; re-fork it from SymbianSource if this is taken up. | After FS6 |
| Demand paging | EKA2 pages code in from ROFS (and data, with a swap partition such as `vendor_x`), so `Z:` code needn't stay resident in RAM. | With M4 (performance), if RAM is short |
| Command queue (CQHCI) | Several requests in flight on the eMMC; needs interrupts instead of polling. | If FS2's speed is not enough under load |

## Check before the stage that needs it

| Question | Needed for | How to check |
|---|---|---|
| ~~Whether `sfat` formats an 8 GB `C:`~~ **Answered 2026-11-07: no.** `C:` is 2000 MB (FAT16) until FS1. Also fixed: format ran in 16 KB steps (`KDefaultMaxBytesPerFormat`); the media driver now reports 1 GB per step | FS1 | done |
| ~~Where the 8.3 limit comes from~~ **Answered 2026-11-07:** `build/tools/mkfat.py` writes short names only; F32's own format and `sl_vfat.cpp` handle long names. FS1 confirms it on `C:` | FS1 | done |
| The eMMC's erase group size (EXT_CSD `HC_ERASE_GRP_SIZE`, `ERASE_GROUP_DEF`) | FS1, FS3 | `blk info` |
| The phone's partition names and sizes, and the slot attributes | FS3–FS5 | `blk gpt` (it already prints all 72 entries); `fastboot getvar all` |
| Whether the 2010 tree's `rofsbuild` and `scomp` run unchanged with our ROM tools | FS4 | Build a small ROFS on the build server and mount it on QEMU |
| Which A/B slot attributes ABL reads (active, successful, retry count) | FS5b | ABL source for SDM670 (Qualcomm LinuxLoader) and a `fastboot set_active` test |
| Whether the usbc framework's controller interface fits DWC3, and how the debug console survives the switch | FS6 | Read `kernel/eka/drivers/usbc` and its PSL interface (`usbcshared`) |
