# Known issues

For the broader legacy-kernel audit, source evidence, priorities and closure tests, see
[kernel-issues.md](kernel-issues.md) and the [modernization roadmap](kernel-modernization.md).
The register maps all seven sections below, retaining the resolved slot-retry history and the uncertainty of
open reports. The 2026-11-09 source audit did not rerun these hardware/emulator observations.

## Phone: slot a runs out of retries (ABL switches to slot b); test images may die with a black screen

**Status:** fixed 2026-11-08 by FS5b (kernel `5b0ba6b`): the kernel marks a slot successful (`slot ok now`, or
neoui's `ENeoHalBootOk` once that lands) and counts tries itself. Found 2026-11-07.

**ABL facts learned (bonito):**
- slot state = byte 6 of the `boot_a`/`boot_b` GPT attributes: priority bits 0–1, active 2, retries 3–5,
  successful 6, unbootable 7;
- ABL lowers the retry count on **fastboot RAM boots**, not on normal boots, but at 0 it does switch slots;
- `fastboot set_active x` resets x to 3 retries and **clears its "successful"**;
- `fastboot flash boot_x` clears "successful" too;
- `fastboot flash system_x` is refused ("should be flashed in fastbootd");
- both GPT headers point at one entry array (LBA 2). The array at the disk's end is stale.
- **After any of these**, boot a test image and run `slot ok now`.

**Symptom:**
- Every `fastboot boot` answers `Booting OKAY`, then the screen stays black (no green kernel text) and the phone is
  back in fastboot within a minute.
- Even images that booted fine earlier fail, so it looks like a broken phone or a broken build. It is neither.

**Cause:**
- `fastboot flash boot_a` clears slot a's "successful" flag. ABL then gives slot a 3 retries.
- **Correction (2026-11-08):** it was the **RAM boots** (`fastboot boot`) that used the retries, dozens of test boots;
  normal boots don't count on this ABL.
- At 0 retries, ABL marks slot a unbootable and makes **slot b** current. A normal restart then boots slot b's own
  system, not NeoSymbian.
- **Cause found (2026-11-08): the black screen means no bootable slot.** `fastboot boot` answers OKAY, then ABL has
  no slot it may boot (both unbootable, or the active one at 0 retries) and the phone falls back to fastboot. Check
  `slot-unbootable:a`/`b`; fix with `fastboot set_active a`. The "cold reset" below only seemed to help.
- **Earlier note (superseded):** slot b did **not** cause the black screens. After a cold power-off (Power held ~15 s), the
  known-good image booted to the USB console with slot b still current. The black-screen state was cleared by the
  cold reset; its cause is unknown (no log survives a death before the first print). If it recurs: check the slot
  first, then cold-reset.

**Check:** `fastboot getvar current-slot`, `slot-retry-count:a`, `slot-unbootable:a`, `slot-successful:a`.

**Fix:** `fastboot set_active a` (ABL's own slot switch; it writes no partition data). Slot a then has 3 retries
again.

**Lasting fix:** FS5b. The kernel marks slot a successful when neoui shows the launcher (HAL + monitor `slot ok`), after
a dry run of the GPT attribute write.

**Not the same thing:** a test image built for an **older** ROFS than the one in `system_a`. It refuses
`system_a` (`[media] ROFS from system_a: another build's, not used`), ESTART panics (`ESTART_17`), and the screen shows
`FAULT: KERN 0x00000004`. That is the header check working. Boot an image built from the same ROFS, or rewrite
`system_a` with a `ROFS=1 ROFS_INSTALL=1` installer image. `lastlog` on the next boot shows which case it was.

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

## Phone: the monitor's `type` can drop the end of a line

`type md c:\Long Directory On Phone` posted all 29 characters (`typed 29 chars`), but eshell on the phone received
only `md c:\Long Directory On`, so the directory was made without "Phone" (2026-11-07, FS1). The same command typed
26-character lines on QEMU without losses. Not looked into yet. Suspects: the console's key queue on the phone, or the
pacing in `A64Key_Type` (`a64_dbgmon.cpp`). Workaround: keep typed lines short.

## Phone: the modem stays on 3G after a connected call (seen 2026-11-09)

**Status:** open (telephony C7).

**What is known:**
- calls on LTE drop to 3G (CSFB);
- a call hung up while ringing comes back to LTE within seconds;
- a call that connected (its voice path ran through the ADSP) stays on 3G. The modem stays up and calls keep working;
- Linux on this phone returns to LTE 1.7 s after a connected call;
- our APR teardown matches Linux's packet for packet, and since kernel `b12d1ba` the modem no longer crashes after
  the call.

**Next to check:**
- the CDSP, which Linux runs and we don't;
- a PDR listener on the audio PD (Linux's `apr.c` registers one);
- what the modem still holds with the ADSP after END (a CVS session it created).

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

**Effect:** the USB debug console and FS6's E: sharing work only on fastboot RAM boots for now.

## Syborg: an odd screen width shears the picture (seen 2026-11-08)

**Status:** open, for the symbian-qemu work.
- **What:** neoui's ROM on symbian-qemu at `SCREEN=539x1079` (`-M syborg,width=539,height=1079`, the size neoui's
  `syborg` CI uses) shows a diagonally sheared screen. Each row is shifted a little further, as when a framebuffer is
  read with the wrong row stride.
- **The same ROM at 540x1080 is correct.** Seen with a native QEMU 11.1.2 build on the Mac (`run-syborg`, `FB`
  screenshot), ROM from `build` with neoui `f1a844b`.
- **Not the cause:**
  - neoui reports `display 539x1079, stride 2156` (539 × 4);
  - `hw/display/syborg_fb.c` reads rows of `width * 4` bytes too.
- **Still to check:** the 2010 Syborg LCD driver (the stride the guest programs or assumes), and the screenshot path.
- **Workaround:** an even width (540x1080). CI screenshots at 539x1079 may show the same shear.
