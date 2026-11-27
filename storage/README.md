<!-- SPDX-License-Identifier: Apache-2.0 -->
# Storage

Part of [the docs](../README.md) · Status: active · Updated: 2026-11-27

How NeoSymbian stores data on the Pixel 3a XL's eMMC with Symbian's own file server (F32) and plugins: FAT32 `C:` and
`E:` on `userdata`, `Z:` from ROFS in the A/B `system_x` slots with per-block hashes, the boot slots, USB mass
storage and installing a large `Z:`. The eMMC driver and media drivers are kernel code (`baseport/arm64`); their
history is here because they exist for storage. Kernel findings on filesystem recovery are KRN-007–010 and KRN-016 in
the [kernel issue register](../kernel/issues.md).

## Documents

| Doc | What | Status |
|---|---|---|
| [filesystem.md](filesystem.md) | The storage plan and its stages: layout, safety gates, each stage's steps and results | active |
| [history/filesystem-start.md](history/filesystem-start.md) | The storage state before FS1 (2026-11-07) | record |
| [history/fs5-install-log.md](history/fs5-install-log.md) | The slot installs of 2026-11-08 to 2026-11-17 | record |
