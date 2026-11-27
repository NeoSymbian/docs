<!-- SPDX-License-Identifier: Apache-2.0 -->
# FS5 install log: slot installs, 2026-11-08 to 2026-11-17

Part of [Storage](../README.md) · Status: record · Updated: 2026-11-17

The installs into the phone's A/B slots recorded under [FS5](../filesystem.md#fs5-updates-and-integrity), moved here on
2026-11-27 as they were written, newest first. ZimaOS was the build machine then (replaced by atlas 2026-11-20); its
paths are history. Later installs are recorded in each stage's own document.

- **Installed 2026-11-17 into slot a** (current as of 2026-11-17): UI v2 and NEOPHONE v2. It includes:
  - the neoui kit and protocol 1.9;
  - Phone, Contacts and Messages as three EXEs;
  - modem-ipc 2.6: conference flag, connect time, IMEI, SILENCE.

  Revisions: build `27bc36b`, kernel `f0b70dff`, neoui `e6aa05e`, phone `d7012d6`, telephony `4095a4b`, neolink `3c19f03`.

  How it was built: a clean build in a fresh volume (`FULL=1`), with `SIS=xplore,frozenbubble` and `ROFS_CORE='\.dll$'`.

  Before the install, a RAM test boot showed the UI, MODEMD registered and reading the IMEI, and Phone and Messages started.

  The install: `system_a` got 33640 KB written, verified, hash check passed; `boot_a` was flashed (6188 KB).

  Images are in `private/uiv2-20261117` and ZimaOS `logs/uiv2-1117`. Slot b keeps its earlier install as the fallback.
- **Installed 2026-11-12 (evening) into slot a** (replaced 2026-11-17): everything merged that day: Wi-Fi W4 (joins WPA2,
  Settings current network + details, status bar icon), C7 calls (IPC v2, multi-call, SIM PIN, airplane, ringtone +
  haptics, modem recovery that never stops the ADSP) and the codec-rails fix (no more modem crash or 3G after a
  call). Kernel `e4323c37`, build `f865a34`, neoui `1ee3245`, telephony `b99883f`, neolink `7db5000`.
  `system_a`: 22337 KB written, verified (hash check passed); `boot_a` flashed (1116 KB). A RAM test boot of the
  same ROM first: a call returned to LTE, Wi-Fi joined (owner checked). Images in `private/install-c7-20261112` and
  ZimaOS `logs/install-c7-20261112`. Slot b keeps the keyboard install as the fallback.
- **Installed 2026-11-12 into slot a** (replaced the same evening): shell text fields bring up the system keyboard (the Wi-Fi
  password, Contacts/Messages search), neoui `32b783a`, build `76515bd`, kernel `71c5c87d`. `system_a`: 21836 KB
  written, verified; `boot_a` flashed (1100 KB). A RAM test boot first: Settings -> Wi-Fi -> a secured network's
  sheet raised the keyboard and took a masked password. Images in ZimaOS `logs/install-fields-20261112`. Slot b
  keeps the keyboard install below as the fallback.
- **Installed 2026-11-12 into slot b**: the system keyboard (English, Armenian, Russian; terminal
  mode), neoui `d579fa0`, build `76515bd`, kernel `71c5c87d` (the Wi-Fi W3 install's sources). `system_b`: 21792 KB
  written, verified; `boot_b` flashed (1100 KB). Built in an isolated ZimaOS copy (`isolated/kbd`, volume
  `neosymbian-kbd`); images in `logs/install-kbd-20261112`. Slot a keeps the 2026-11-12 Wi-Fi install as fallback.
- **Installed 2026-11-10 into slot a** (C7 candidate; replaced by the 2026-11-12 installs above): kernel `8dbcc89f`,
  build `b52e502`, neoui `bf93051` (current Clock and Dev tools retained), telephony `63a2b1f`,
  e32 `e97e2eb`. Built on ZimaOS from coordinated `feat/c7-complete-calls` branches.
  The `ROFS=1 ROFS_INSTALL=1 EMMC_C=1` installer wrote/read-back-verified 21003 KB to
  `system_a`; the matching `ROFS=flash` image was flashed to `boot_a` (1076 KB).
  Diagnostic fault injection was disabled. A RAM boot of that exact image mounted
  `system_a`, showed the launcher and LTE, and marked slot a successful; then a normal
  reboot was sent. Normal-boot visual confirmation and C7 call acceptance remain pending.
  Slot b was preserved. Private installation logs remain outside Git.
- **Installed 2026-11-10 into slot a**: kernel `090bb5e` (device status registry, HAL `0x4e19`),
  build `269ec50` (Old apps: `LEGACY.EXE`, its UID moved to `0xE0002006` off MODEMD's), neoui `ed9202f` (Dev tools,
  Clock and the settings store rebuilt), telephony `54a8114`, e32 `e97e2eb`. `system_a`: 19991 KB written,
  verified; `boot_a` flashed (1060 KB). A RAM test boot showed Dev tools listing the drivers and the modem on LTE.
  This replaced the USB-SSH session's slot-a install of the same morning. Slot b keeps the 2026-11-09 install.
- **Installed 2026-11-09 into slot b**: telephony C6, calls with two-way audio. Kernel `792d36e`
  (`b12d1ba` + the GLINK fix that lost the modem's VOICE announcement on the first install),
  build `a1e418d` (+ the kernel override), neoui `2d55d01`, telephony `3f4af12` (MODEMD in the ROM: the modem and
  the ADSP start at every boot). `system_b`: 11106 KB written, verified; `boot_b` flashed (984 KB). Slot a keeps
  the 2026-11-08 install as the successful fallback.
- **Installed 2026-11-08 into slot a**: kernel `bee9830`, build `26c6325`, neoui `07b987c`, e32
  `e97e2eb` (smooth-ui S2: fades, home swipe, list scrolling). `system_a`: 10709 KB written, verified; it booted
  from eMMC to the launcher. Built in isolated ZimaOS copies (`build-s2`, `kernel-s2`, volume `neosymbian-s2`).
  Slot b keeps the previous install as the successful fallback.
- **Installed 2026-11-08 into slot b** (earlier the same day): kernel `bee9830`, build `26c6325`, neoui `16958f7`, e32
  `c5fda36` (H3a power/clock, S1–S3, build info).
  Steps: `fastboot set_active b`; RAM-boot the `AUTOFASTBOOT=600 ROFS=1 ROFS_INSTALL=1 EMMC_C=1` installer
  (`system_b`: 10460 KB written, verified); back to fastboot at once (the installer's neoui marks b successful,
  while `boot_b` is still old); `fastboot flash boot_b` the `ROFS=flash EMMC_C=1` image; `fastboot reboot`.
  Build all images from one ROM build (one volume), so the ROFS and its hashes match.
