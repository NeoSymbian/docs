<!-- SPDX-License-Identifier: Apache-2.0 -->
# Known issues

Part of [the docs](README.md) · Status: active · Updated: 2026-11-25

Open problems seen on the phone, on QEMU or in CI. This page owns each issue's disposition (open, fixed and when, the
fix). Fixed and obsolete entries move to [history/known-issues-fixed.md](history/known-issues-fixed.md), listed under
[Fixed](#fixed) at the bottom. Kernel findings also have an ID in the [kernel issue register](kernel/issues.md), which
keeps the source evidence and closure tests and links back here for the status; the
[modernization roadmap](kernel/modernization.md) orders that work.

## Phone: fshell doesn't come back after USB debugging is switched off and on (2026-11-25)

**Status:** open, not a regression (the US4 image does the same).
- Settings > USB debugging off, then on: the port comes back (`[usb] USB debugging on (2 functions)`), but fshell
  exits `-18` (KErrNotReady) at once, every time, also while the Mac has the port open; neoui restarts it with backoff
  (up to 32 s). Only a reboot brings it back.
- Once, on the US4 image during this test, the phone then crashed with the debug port silent (no log).
- **Next:** what fshell's console open returns after the ACM function is re-added (kernel `a64_usb_acm_*`).

## Phone: X-plore closes with `EUSRNIMP` after a menu tap (2026-11-22)

**Status:** open, not a regression.
- X-plore (old S60 app) runs, then after a tap near the bottom right (a softkey/menu, 952,1636) its main thread
  panics `EUSRNIMP 5617124`: it called one of the legacy component list's generated panic stubs; the reason is the
  caller's address, `0x55B5E4`, in X-plore's code. Just before, it fails to create `Z:\System\Data\X-plore_temp\`
  (read-only Z:, `-12`/`-1`).
- Same panic, same address, on `2026-11-22-tapirtail` (ARMv5 user side) and on the US3 ARMv8 build.
- **Next:** map `0x55B5E4` to its import (X-plore's code base + import table) and implement that function
  ([user-side/legacy.md](user-side/legacy.md): panic stubs are a stop-gap).

## Phone: Dev tools "Run checks" can freeze the phone (2026-11-18)

**Status:** open, cause not confirmed.
- Twice (neohw S4 image), a few minutes after Dev tools → Devices → **Run checks**, the debug console stopped
  answering and the phone stayed frozen (no AUTOFASTBOOT); Power + Volume Down was needed. All 18 checks themselves
  passed. The last lines were a background Wi-Fi scan with the screen off.
- The same images idle for 10 minutes (screen off, Wi-Fi scans and a link drop) did not freeze.
- Suspect: the `serial1` check opens ECOMM unit 1, the USB ACM that the debug console also runs on.
- **Next:** run only the `serial1` check with the console captured; then the other checks one by one.

## Phone: the 2.4 GHz BSSID of the home AP doesn't answer unicast pings from the LAN (2026-11-19)

**Status:** open, not investigated, now mostly avoided. Since 2026-11-21 (neohw#12, neoui#32), WIFID joins a dual-band
network's 5 GHz AP when it is −70 dBm or better, so the home AP is joined on `…:6a` (channel 44).
- Joined to `…:66` (2.4 GHz, channel 1), the phone's own traffic works: DHCP, DNS, TCP, the internet check.
- But unicast pings from a wired Mac on the same subnet get no reply, though they arrive (rx counters rise).
- On the 5 GHz BSSID `…:6a` they are answered. Possibly the AP's isolation between bands; check with another client.

## QEMU only: rare half-written protected buffers in DoRWTest (nkernsa suspend/kill/migrate)

**Status:** open, parked 2026-11-06. It does not block M4. The real Pixel passes the whole suite
(`failures 0x0`, `skmpar` included).

**Symptom:**
- Under `skmpar` (four `DoRWTest` cases at once) on QEMU virt with 8 vCPUs (TCG), about 10 of 78 cases report 1–5 bad
  reads in buffers the writer fills inside a critical section or fast mutex.
- Only the interlocked suspend (type 4) and interlocked kill (type 5) cases are affected; F2/F3 are 1–5 per 10000 reads.
- Run one case at a time, it happens about once in 20k reads.

**Already fixed on the way**, so not the cause:
- `NKern::JoinGroup` re-queued a ready group at the tail.
- `send_resched_ipi_and_wait` could return before the target CPU took the IPI. The 2010 check would have returned
  early 75,256 times in one phone run. It is now a numbered request/acknowledge handshake.

**Ruled out:**
- A thread leaving its CPU suspended or killed inside a critical section: `A64_SchedCheck` never fires.
- The scheduler picking a lower-priority thread while the writer is ready on the same CPU: the only hits were migrate
  cases, where the writer is ready on the other CPU of its pair.

**Repro and diagnostics:**
```
BOARD=qemu NKSA_SCALE=1 NKSA_RWTRACE=1 NKSA_MAIN=select NKSA_TESTS=skmpar build-kernel.sh
SMP=8 run-qemu.sh 600
```
`NKSA_RWTRACE=1` makes the reader print the writer's state (`*** RWFAIL`) at the first 16 bad reads. It only reports a
buffer the writer's in/out sequence really protects.

**Next idea:**
- Read the RWTRACE output from a run with the exact filter.
- If the writer shows "suspended, critical-section count 0, ready on no CPU" while its sequence says it is in a critical
  section, the critical-section count itself is wrong. Suspect `NKern::ThreadEnterCS`'s plain `++iCsCount` racing a
  cross-CPU reader of it, i.e. memory ordering on TCG.

## Phone: fshell over USB: a typed flood, and a full C: (seen 2026-11-11, debug access T11)

**Status:** open, skipped by the owner in T11.
- **Flood:** about 8 KB typed while fshell is busy (e.g. in `sleep`) overflows ECOMM's receive ring: ECOMM drops the
  rest and fshell's read fails with `KErrCommsOverrun` (-31). A USB PDD has no RTS to drop: it must hand ECOMM only
  what its ring holds and keep the rest in its queue (which holds the host back). A first try
  (`a64_usb_acm_debug.cpp`: room from `iRxGetIndex`/`iRxPutIndex`, a re-ring from the poll) removed the overrun but
  left fshell with no input after the flood; it was reverted. `phone.py` itself never floods (commands go as one line,
  files by YMODEM).
- **Full C::** every `phone.py sh` uploads its command as a script file to `C:`, so with `C:` full no command runs,
  not even `rm`. The client should type short commands directly when the upload fails.

## Phone: the monitor's `type` can drop the end of a line

`type md c:\Long Directory On Phone` posted all 29 characters (`typed 29 chars`), but eshell on the phone received
only `md c:\Long Directory On`, so the directory was made without "Phone" (2026-11-07, FS1). The same command typed
26-character lines on QEMU without losses. Not looked into yet. Suspects: the console's key queue on the phone, or the
pacing in `A64Key_Type` (`a64_dbgmon.cpp`). Workaround: keep typed lines short.

## Phone: call audio has no calibration (2026-11-09)

**Status:** known limit.
- Without ACDB, the voice path uses the ADSP's built-in topologies (single-mic echo cancellation, default RX), so
  levels and echo are untuned.
- Dev tools' loudspeaker loopback howls when the phone is held near the mic. That is acoustic feedback, expected.

## Phone: USB power on a normal boot doesn't work yet (parked 2026-11-08)

**Status:** open. The kernel has `qcom_usbpower.cpp` (ABL's captured GCC/QUSB2 values) and the debug monitor's
`usb cold <mask>`, both in kernel `2692bea`.

**What is known:**
- after our power-up, GCC matches ABL's fastboot state, but the QUSB2 PHY's registers read 0, with or without the
  RPMh rail votes;
- an `ldob7` (3.088 V) vote issued while ABL's USB is live also makes the PHY read 0;
- **RPMh votes survive a warm reset**, so a debug run can leave a rail off for the next RAM boot. A cold power-off
  clears them.

- **T12 (2026-11-11), a real cold installed boot:** with USB debugging on, the kernel powers USB
  (`A64UsbPowerOn`) and the controller runs, but the host never sees the phone: no bus reset, no events, no device on
  the Mac. Turning the switch off and on again then fails the controller restart (`-33`, halt). So the monitor's
  `usb cold 7` on a RAM boot is not a faithful cold boot. Next: compare ABL's fastboot setup (the ldob7 rail, the
  PHY's reference clock) with the PHY's registers after our power-up.

**Effect:** the USB debug console and FS6's E: sharing work only on fastboot RAM boots for now; debug access T12 is
parked on this.

## Fixed

These moved to [history/known-issues-fixed.md](history/known-issues-fixed.md), in their old order:
- [Phone: the modem crashes under CPU load at boot; restarts fail; Wi-Fi doesn't come back (2026-11-21)](history/known-issues-fixed.md#phone-the-modem-crashes-under-cpu-load-at-boot-restarts-fail-wi-fi-doesnt-come-back-2026-11-21): fixed 2026-11-22; three small follow-ups are open in [hardware/modem.md](hardware/modem.md).
- [Phone: ESock_DIP crashes and the phone reboots (cross-thread sockets) (2026-11-20)](history/known-issues-fixed.md#phone-esock_dip-crashes-and-the-phone-reboots-cross-thread-sockets-2026-11-20): fixed 2026-11-21.
- [Phone: Wi-Fi drops after a few minutes, `reason 4` (2026-11-18)](history/known-issues-fixed.md#phone-wi-fi-drops-after-a-few-minutes-reason-4-2026-11-18): fixed 2026-11-19.
- [Phone: a modem restarted after a WLAN firmware assert crashes again (2026-11-19)](history/known-issues-fixed.md#phone-a-modem-restarted-after-a-wlan-firmware-assert-crashes-again-2026-11-19): fixed 2026-11-22.
- [Phone: TFTP `/readwrite/` writes are kept but not readable (2026-11-19)](history/known-issues-fixed.md#phone-tftp-readwrite-writes-are-kept-but-not-readable-2026-11-19): fixed 2026-11-21.
- [Phone: slot a runs out of retries (ABL switches to slot b); test images may die with a black screen](history/known-issues-fixed.md#phone-slot-a-runs-out-of-retries-abl-switches-to-slot-b-test-images-may-die-with-a-black-screen): fixed 2026-11-08 (FS5b); the ABL slot facts are there.
- [CI: neoui's `syborg` check is red (seen 2026-11-11)](history/known-issues-fixed.md#ci-neouis-syborg-check-is-red-seen-2026-11-11): obsolete 2026-11-21 (Syborg dropped).
- [Phone: the modem stays on 3G after a connected call (seen 2026-11-09)](history/known-issues-fixed.md#phone-the-modem-stays-on-3g-after-a-connected-call-seen-2026-11-09): fixed 2026-11-12.
- [Syborg: an odd screen width shears the picture (seen 2026-11-08)](history/known-issues-fixed.md#syborg-an-odd-screen-width-shears-the-picture-seen-2026-11-08): fixed 2026-11-25.
