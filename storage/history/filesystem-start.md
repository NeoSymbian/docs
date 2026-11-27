<!-- SPDX-License-Identifier: Apache-2.0 -->
# File system: where we started (before FS1)

Part of [Storage](../README.md) · Status: record · Updated: 2026-11-07

The storage state on 2026-11-07, after H2.3 and before FS1, moved here from
[filesystem.md](../filesystem.md#where-we-start) on 2026-11-27. It is kept as written.

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
