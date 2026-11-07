# File system plan: Symbian's storage on the Pixel 3a XL

Status: plan (2026-11-07). Android is not kept on the phone, so NeoSymbian owns the eMMC, except for the partitions
listed under "Never touched".

## Where we start

- **The file server is Symbian's own.** F32 (`efile.exe`) runs on the user side and loads one plugin (`.fsy`) per
  file system. The 2010 tree (`kernel/userlibandfileserver/fileserver`) has:
  - `srom`, `srofs` and `scomp`: the ROM, ROFS and composite file systems behind `Z:`;
  - `sfat32`: FAT12/16/32 with long names, rugged FAT, ScanDrive and delete notification (TRIM);
  - `sfat`: the older FAT12/16 plugin, marked obsolete in its `.mmp`;
  - `smassstorage`, `shostmassstorage` and `automounter`: USB mass storage for a PC, USB sticks plugged into the
    phone, and mounting removable drives.
- **The drives today.** `baseport/arm64/common/estart.txt` mounts local drive 0 as `C:` with
  `ELOCAL FAT FS_FORMAT_CORRUPT,FS_SYNC_DRIVE`. `Z:` is the whole ROM, held in RAM inside `boot.img`.
- **Our `ELOCAL.FSY` is built from `sfat`, not `sfat32`.** `build/emitter/build_elocal_fsy.py` uses the
  `elocal.mmp` file set, so `C:` is FAT12/16, the obsolete plugin.
- **The 8.3 names.** The 8.3-only limit on `C:` probably comes from how `c_drive.img` is made, not from the plugin.
  Both plugins carry `sl_vfat.cpp`.
- **The phone's `C:` (H2.3).** `qcom_sdhci.cpp` gives `C:` the first 8 GB of `userdata` in `EMMC_C=1` builds. The
  eMMC runs 1-bit at 19.2 MHz (about 2 MB/s).
- **Rugged FAT.** It is on unless a drive is flagged `FS_NOT_RUGGED`. `estart` forces ScanDrive on a rugged FAT
  volume and warns when `FS_SCANDRIVE` is missing.

## Target layout

Partitions are found by their GPT name, as `qcom_sdhci.cpp` does now. The GPT itself is never rewritten.

| GPT partition | Use | File system |
|---|---|---|
| `boot_a`, `boot_b` | Kernel and core ROM: the minimum to start the file server and mount `Z:` | XIP ROM in `boot.img` |
| `system_a`, `system_b` (~2.5 GB each) | `Z:`, the rest of the OS, one copy per slot | ROFS, with a hash tree |
| `vendor_a`, `vendor_b` | Spare: crash dumps, recovery tools, later swap for data paging | — |
| `userdata` (51 GB) | `C:` and `E:`, through our own MBR at the start of the partition | FAT32 |

| Drive | Size | What | Exposed over USB |
|---|---|---|---|
| `Z:` | ROFS + core ROM | System binaries and resources, read-only | no |
| `C:` | 4–8 GB | Settings, installed apps, `\private\<SID>`, `\sys\bin` for installed code | never |
| `D:` | RAM | Temporary files | no |
| `E:` | the rest of `userdata` | User media and documents ("mass memory", as on the N8) | yes |

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

The block driver keeps an **allow-list** of writable partition names (`userdata`, `system_a/b`, `vendor_a/b`). Writes
anywhere else fail in the driver, whatever the caller asks for.

## Stages

Each stage is usable on its own. FS1–FS3 complete roadmap stage H2 (storage).

| Stage | Work | Exit |
|---|---|---|
| **FS1 FAT32 plugin** | Build `sfat32` (`efat32.fsy`, unmodified) in place of the `sfat` ELOCAL, on QEMU first. Mount `C:` as `FAT` from it. Find and fix the 8.3 limit in `c_drive.img`. Add `FS_SCANDRIVE` to the rugged drives in `estart.txt`. | A long file name round-trips on `C:`. ScanDrive runs at boot. The ROM's f32test FAT tests pass. |
| **FS2 eMMC speed** | HS200 with an 8-bit bus and tuning in `qcom_sdhci.cpp`, with polled transfers kept. The writable-partition allow-list. | More than 50 MB/s sequential read on the phone. A write outside the allow-list is refused. |
| **FS3 `C:` and `E:` on `userdata`** | A small MBR at the start of `userdata` with two partitions, read by the media driver as Symbian MMC drivers read partition tables (`drivers/medmmc/emmcptn.cpp`). `C:` and `E:` both FAT32 (E: formatted with large clusters). `estart.txt` lists both. | Files on `C:` and `E:` survive a reboot and a power cut in the middle of a write (pull the battery or force-reset during a copy, then ScanDrive repairs). |
| **FS4 `Z:` on ROFS** | Split the image: a core ROM in `boot.img` plus ROFS (`rofsbuild` from `oss.FCL.sftools.dev.build`) written to `system_<slot>`. Mount `Z:` through the composite file system (`scomp`). | The phone boots with `Z:` from flash. `boot.img` shrinks to the core. |
| **FS5 Updates and integrity** | Write updates to the inactive slot's `boot_x` and `system_x`, then switch with ABL's A/B slot attributes, so a failed boot falls back to the old slot. Add a hash tree over the ROFS image, checked block by block in a media driver extension (`DMediaDriverExtension`), with its root hash in `boot.img`. | A bad update rolls back by itself. A changed `Z:` block is caught on read. |
| **FS6 USB** | `smassstorage` shares `E:` with a PC (USB composite with the debug serial port). | A PC sees `E:` and copies files while the phone keeps running. |

## Later (daily-phone stage)

| Item | Plan | When |
|---|---|---|
| Encryption | AES-XTS as a media driver extension on `userdata`, with the key derived from the user's PIN. The SDM670's inline crypto engine (ICE) speeds it up later. A hardware keystore through TrustZone is a separate, large job. | Before the phone holds personal data |
| Journaled `C:` | Only if rugged FAT fails in daily use. A new `.fsy` plugin: plugins run inside the user-side file server, so it can be mostly Rust behind a thin C++ layer (`CFileSystem`, `CMountCB`, `CFileCB`, `CDirCB`). ext4 is the pick: it has a journal, files over 4 GB and hashed directories, and Linux tools (`mkfs.ext4`, `e2fsck`, `debugfs`, mounting on ZimaOS) build and check the images. littlefs is power-safe but slow on large volumes; F2FS is too complex. | Only if needed |
| exFAT on `E:` | For files over 4 GB (video). Not in the 2010 sources; a new plugin. | When FAT32's 4 GB file limit matters |
| MTP | Replaces mass storage so `E:` stays mounted on the phone too. Symbian's MTP framework (`mw.mtpfws`) was deleted from the org; re-fork it from SymbianSource if this is taken up. | After FS6 |
| Demand paging | EKA2 pages code in from ROFS (and data, with a swap partition such as `vendor_x`), so `Z:` code needn't stay resident in RAM. | With M4 (performance), if RAM is short |
| TRIM | `sfat32` already sends delete notifications (`DeleteNotify`). The media driver turns them into eMMC discard (CMD35/36/38). | With FS3 |

## Check before the stage that needs it

| Question | Needed for | How to check |
|---|---|---|
| The phone's partition names and sizes, and the slot attributes | FS3–FS5 | `fastboot getvar all`; the GPT dump the eMMC driver already prints |
| ~~Whether `sfat` formats an 8 GB `C:` today~~ **Answered 2026-11-07: no.** On an 8 GB volume the format "completes" but `C:` stays "Corrupt or unformatted" (QEMU and phone). `C:` is 2000 MB (FAT16) until FS1. Also fixed: format ran in 16 KB steps (`KDefaultMaxBytesPerFormat`); the media driver now reports 1 GB per step | FS1 | done |
| Where the 8.3 limit comes from | FS1 | Make a long name on `C:` from ESHELL on QEMU; read how `c_drive.img` is written |
| Whether the 2010 tree's `rofsbuild` and `scomp` run unchanged with our ROM tools | FS4 | Build a small ROFS on ZimaOS and mount it on QEMU |
| Which A/B slot attributes ABL reads (active, successful, retry count) | FS5 | ABL source for SDM670 (Qualcomm LinuxLoader) and a `fastboot set_active` test |
