# File system plan: Symbian's storage on the Pixel 3a XL

Status: plan, revised 2026-11-07 after H2.3. Android is not kept on the phone, so NeoSymbian owns the eMMC, except for
the partitions listed under "Never touched".

The design stays Symbian's own, from the 2010 sources:
- F32 with its file system plugins;
- FAT32 on the writable drives;
- ROFS and the composite file system for `Z:`.

A new file system is written only if one of these fails in daily use (see "Later").

## Where we start

- **The file server is Symbian's own.** F32 (`efile.exe`) runs on the user side and loads one plugin (`.fsy`) per
  file system. The 2010 tree (`kernel/userlibandfileserver/fileserver`) has:
  - `srom`, `srofs` (`erofs.mmp`) and `scomp` (`ecomp.mmp`): the ROM, ROFS and composite file systems behind `Z:`;
  - `sfat32` (`efat32.mmp`): FAT12/16/32 with long names, rugged FAT, ScanDrive and delete notification (TRIM). It
    also needs `fs_utils/filesystem_utils.cpp` and `bit_vector.cpp`;
  - `sfat`: the older FAT12/16 plugin, marked obsolete in its `.mmp`;
  - `smassstorage`, `shostmassstorage` and `automounter`: USB mass storage for a PC, USB sticks plugged into the
    phone, and mounting removable drives.
- **The drives today:**
  - `baseport/arm64/common/estart.txt` mounts local drive 0 as `C:` with
    `ELOCAL FAT FS_FORMAT_CORRUPT,FS_SYNC_DRIVE`;
  - `Z:` is the whole ROM, held in RAM inside `boot.img`.
- **Our `ELOCAL.FSY` is built from `sfat`, not `sfat32`.** `build/emitter/build_elocal_fsy.py` uses the
  `elocal.mmp` file set, so `C:` is FAT12/16, the obsolete plugin.
  - It cannot make a volume above 2 GB: an 8 GB `C:` stays "Corrupt or unformatted" after its format, on QEMU and on
    the phone.
  - `efat32.mmp` keeps the same UID3 (0x100000d6), so `sfat32` can be built under the name `ELOCAL`.
- **The 8.3 names come from `build/tools/mkfat.py`,** which writes the syborg `c_drive.img` with short names only.
  The plugins themselves carry `sl_vfat.cpp`, so a `C:` that F32 formats can hold long names.
- **Since FS1 (2026-11-07)** `ELOCAL.FSY` is `sfat32` and `C:` is 8 GB FAT32 at userdata + 7168 sectors; the
  points below describe the start (H2.3).
- **The phone's `C:` (H2.3, kernel `8629702`):**
  - in `EMMC_C=1` builds, `qcom_sdhci.cpp` gives `C:` the first 2000 MB of `userdata`, starting at its sector 0, as
    FAT16;
  - two guards keep writes inside that window: `a64_blk.cpp` and `A64BlkDev_Write`;
  - the eMMC runs 1-bit at 19.2 MHz, ADMA2, polled (about 2 MB/s).
- **The media driver** (`common/specific/a64_medblk.cpp`):
  - formatting is a no-op (FAT writes its own structures);
  - it reports 1 GB per format step, and no erase block size.
- **Rugged FAT** is on unless a drive is flagged `FS_NOT_RUGGED`. `estart` forces ScanDrive on a rugged FAT volume
  and warns when `FS_SCANDRIVE` is missing. Other `estart.txt` flags used below: `FS_SYSTEM_DRIVE` and
  `FS_COMPOSITE` (`estart.cpp`).

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

**The allow-list.** The block driver keeps a list of the partition names it may write: `userdata`, `system_a/b` and
`vendor_a/b`.
- Writes anywhere else fail in the driver, whatever the caller asks for.
- Each entry is enabled only when its stage is approved. Today only `userdata` is.

### Safety gates

Some stages go past what is approved today: RAM boot only, and eMMC writes only inside `userdata`. Each needs the
owner's explicit approval at the time:

| Gate | What it allows | Stage |
|---|---|---|
| G1 | Writes to `system_a/b` by our bounded driver | FS4b |
| G2 | The first write to `boot_a/b`: the phone then boots NeoSymbian without `fastboot boot` | FS5b |
| G3 | Changing the A/B slot attributes: GPT entry attribute bits, rewritten with both GPT copies and their CRCs, or `fastboot --set-active` from a PC | FS5b |

## Stages

Each stage is usable on its own. FS1–FS3 complete roadmap stage H2 (storage).

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
  - **Installed 2026-11-08 into slot b** (the current slot): kernel `bee9830`, build `26c6325`, neoui `16958f7`, e32
    `c5fda36` (H3a power/clock, S1–S3, build info). Slot a keeps the previous install as the successful fallback.
    Steps: `fastboot set_active b`; RAM-boot the `AUTOFASTBOOT=600 ROFS=1 ROFS_INSTALL=1 EMMC_C=1` installer
    (`system_b`: 10460 KB written, verified); back to fastboot at once (the installer's neoui marks b successful,
    while `boot_b` is still old); `fastboot flash boot_b` the `ROFS=flash EMMC_C=1` image; `fastboot reboot`.
    Build all images from one ROM build (one volume), so the ROFS and its hashes match.
  - ABL's quirks are in `known-issues.md`.

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
  USB. See `known-issues.md`.

- **Spike first:** `smassstorage` speaks to the Symbian USB client LDD (`RDevUsbcClient`, `kernel/eka/drivers/usbc`).
  Our `qcom_dwc3_acm.cpp` is a standalone polled gadget for the debug console. The spike picks between:
  - a DWC3 controller driver (PSL) under the usbc framework, with the debug serial port kept as an interface that
    works before the user side starts;
  - or the mass-storage protocol (bulk-only transport) inside our gadget, with `E:` dismounted by F32 while it is
    shared.
- **Then:** `E:` is shared with a PC on a USB composite device, next to the debug serial port.

**Exit:** a PC sees `E:` and copies files while the phone keeps running.

## Later (daily-phone stage)

| Item | Plan | When |
|---|---|---|
| Encryption | AES-XTS as a media driver extension on `userdata`, with the key derived from the user's PIN. The SDM670's inline crypto engine (ICE) speeds it up later. A hardware keystore through TrustZone is a separate, large job. | Before the phone holds personal data |
| Journaled `C:` | Only if rugged FAT fails in daily use. A new `.fsy` plugin: plugins run inside the user-side file server, so it can be mostly Rust behind a thin C++ layer (`CFileSystem`, `CMountCB`, `CFileCB`, `CDirCB`). ext4 is the pick: it has a journal, files over 4 GB and hashed directories, and Linux tools (`mkfs.ext4`, `e2fsck`, `debugfs`, mounting on ZimaOS) build and check the images. littlefs is power-safe but slow on large volumes; F2FS is too complex. | Only if needed |
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
| Whether the 2010 tree's `rofsbuild` and `scomp` run unchanged with our ROM tools | FS4 | Build a small ROFS on ZimaOS and mount it on QEMU |
| Which A/B slot attributes ABL reads (active, successful, retry count) | FS5b | ABL source for SDM670 (Qualcomm LinuxLoader) and a `fastboot set_active` test |
| Whether the usbc framework's controller interface fits DWC3, and how the debug console survives the switch | FS6 | Read `kernel/eka/drivers/usbc` and its PSL interface (`usbcshared`) |
