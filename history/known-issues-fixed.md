<!-- SPDX-License-Identifier: Apache-2.0 -->
# Known issues: fixed

Part of [the docs](../README.md) · Status: record · Updated: 2026-11-27

Issues that were fixed or became obsolete, moved here from [known-issues.md](../known-issues.md) on 2026-11-27 as
they were written. Open issues stay there. Kernel findings map to the [kernel issue register](../kernel/issues.md).

## Phone: the modem crashes under CPU load at boot; restarts fail; Wi-Fi doesn't come back (2026-11-21)

**Status:** fixed 2026-11-21/22 (kernel#36 #37 #38, neohw#13 #14; details in
[hardware/modem.md](../hardware/modem.md#modem-restart-and-the-adsp-fixed-2026-11-21-kernel38-neohw14)).
- **Under load** (8 busy threads while the modem boots), three things went wrong:
  - **A kernel fault in HWHUB** (L3 translation fault in `memclr`, ADSP firmware load), then IPA -14 and a 3G-only
    modem. Cause: kernel TLB maintenance for global pages was ASID-0 only, so a user thread's walk cache kept a
    freed page table. Fixed with VAAE1 and a flush before freeing page tables, and by making the completion
    barrier a DSB (kernel#36).
  - **Modem FATAL `User-PD grace timer expired for wlan_process`.** HWHUB's blocking GLINK sends and its TFTP window
    flooded its outbox, and the modem's 3 MB `wlanmdsp.mbn` never loaded. Fixed with a try-send, best-fit intents
    and a TFTP window that waits for the transport (kernel#37, neohw#13). 5/5 stressed boots pass.
- **Restarts** didn't recover:
  - every stop forced the AXI halt and the next boot failed at step 7;
  - recovery looped, then gave up;
  - after a restart the modem asserted `ipa_hwp_init ... didnt rx any ind frm HWP`;
  - Wi-Fi never came back.
- **Fix (Linux-grade SSR):** one recovery owner with reasons, an SSCTL shutdown request, stop-ack, ADSP SSCTL events
  and GLINK-SSR cleanup, the IPA clock query answered again, `skip_uc_load = 1`, and the WIFID reset fixes
  (kernel#38, neohw#14).
- **Result:** 8/8 forced faults recover once each. The modem is back ~6 s after the stop and Wi-Fi ~25 s after it.
  The owner checked a call, an SMS and Wi-Fi internet after a restart.
- **Still open:**
  - one AXI port logs "failed to halt" after a clean stop-ack (the reset handles it);
  - a real ADSP restart is avoided;
  - Linux's `ipa_modem_crashed` teardown is not ported (needed with C10 mobile data).

## Phone: ESock_DIP crashes and the phone reboots (cross-thread sockets) (2026-11-20)

**Status:** fixed 2026-11-21 (commsfw#1, build#49).
- **Seen:** `stdtest smp_cross_thread_fd` (3 threads opening and closing UDP sockets while ESock starts) killed
  ESock_DIP. The thread is critical, so the phone rebooted. Also seen on main before the SMP work.
- **Cause:** found with a new dead-node diagnostic in `TSignatureBase::DispatchL`.
  - The core SCPR's BindTo activity in ESock_IP kept raw pointers to its data clients while it waited for a lower
    binder.
  - Meanwhile the socket closed in ESock_DIP, and the client went idle → destroy → freed.
  - `TCFDataClient::TBindTo` then hit the freed node.
- **Fix:** the activity keeps node ids and looks each client up (present, not leaving) before every send. A client
  that left is skipped and its binder released (`ESock: BindTo skips a data client that left`).
- **Result:** 3/3 boots without a crash. One boot's test failed with KErrNotReady because Wi-Fi wasn't linked yet,
  which is how sockets already behave without a bearer.

## Phone: Wi-Fi drops after a few minutes, `reason 4` (2026-11-18)

**Status:** fixed 2026-11-19 (kernel `wifi/bmiss` `7e6fd1ac`, PR kernel#25). Phone runs E1–E8 (logs in `private/wifi/w8/`).
- 2–5 minutes after joining: `[wifi] link lost (status 0, reason 4)`. The AP never sent us away: the firmware raised a
  beacon-miss ROAM event, which the driver logged as reason 4.
- **Cause: too few HTT receive buffers.** The driver posted 128 buffers to the firmware's HTT receive ring (ath10k keeps
  2047 there). The firmware then delivered about 150 receive records and nothing more, for good.
  - The count is the same idle or flooded: ~150 records after ~90 s idle, or within seconds of a ping flood.
  - Joining early or late makes no difference.
  - The host side was clean at every stall: every copy engine reaped (hardware index = ours), every buffer reposted,
    and HTT control still answering a version request.
  - After a stall, a rejoin associated over WMI but never saw EAPOL. WIFID left after 10 s, the firmware asserted
    `wlan_ps_sta_health_monitor_timeout`, and the modem crashed.
- **Fix:** 1024 buffers and a 4 MB DMA pool. On the same AP and channel the phone then took 3600+ records, a
  1500-ping unicast flood (1490 back), a 2000-ping broadcast flood, and an idle hold with pings answered.
- **Red herrings on the way:**
  - The modem's EFS write through rmtfs at ~111 s came at about the same time only because the early runs joined at
    ~30 s.
  - The EFS images match the C0 backup the Linux reference used.
  - Neither refusing the `mcfg.tmp` TFTP write nor skipping the rmtfs copy changed anything.
  - Re-sending power save off and recreating the vdev changed nothing.
- **Also fixed on the way:**
  - The beacon miss now probes the AP before leaving.
  - WIFID stops automatic rejoins after a handshake with no EAPOL at all (`fail::NO_DATA`), so a dead data path no
    longer crashes the modem again and again.
  - SMP2P no longer reports a stopped modem's stale READY|HANDOVER|FATAL bits as the restarted modem's (kernel
    `mss/fatal-stale`).

## Phone: a modem restarted after a WLAN firmware assert crashes again (2026-11-19)

**Status:** fixed 2026-11-22 by the Linux-grade restart (kernel#38, neohw#14; [above](#phone-the-modem-crashes-under-cpu-load-at-boot-restarts-fail-wi-fi-doesnt-come-back-2026-11-21)):
the FATAL before handover was the IPA microcontroller handshake (`skip_uc_load`), and Wi-Fi now restarts with the modem.
History:
- **The restart now behaves:** with the SMP2P fix, a restart after `wlan_ps_sta_health_monitor_timeout` waits for the new
  modem's own READY (`slave-kernel 00000002`) instead of the old 0x7, and QRTR comes up.
- **But the new modem raises FATAL again before handover** (`00000003`), and HWHUB restarts it again. The re-init after
  a modem stop (wifi.md W7) is still unproven.
- Not reproduced since the HTT buffer fix removed the assert's trigger.

## Phone: TFTP `/readwrite/` writes are kept but not readable (2026-11-19)

**Status:** fixed 2026-11-21 (neohw#13). A `/readwrite/` file the modem wrote is served back from RAM, and unwritten
ones still get "not found". The modem's `mcfg.tmp` now goes: not found, then written, then read back (1 byte), as
under Linux. No change to Wi-Fi or carrier config was seen. History:
- HWHUB keeps a written `/readwrite/` file in RAM but refuses to read it back. Linux's tqftpserv maps `/readwrite/` both
  ways.
- The modem writes `/readwrite/mcfg.tmp` (1 byte) at ~30 s and finds it unreadable. Refusing the write instead makes
  the modem retry endlessly.
- Neither variant affects Wi-Fi (E3). Serving the bytes back might change what the modem's carrier-config code does;
  test it before changing.

## Phone: slot a runs out of retries (ABL switches to slot b); test images may die with a black screen

**Update 2026-11-21:** a kernel crash on a *test* image (AUTOFASTBOOT) used to leave a black screen with a dead
console until AUTOFASTBOOT, because the other CPUs kept petting the watchdog. Now it lands in fastboot 10 s later
(kernel#36, `a64_reboot.cpp`).

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

## CI: neoui's `syborg` check is red (seen 2026-11-11)

**Status:** obsolete. Syborg was dropped as a target (2026-11-21); its UI checks run on QEMU `virt` since US6b
(2026-11-25, neoui's `virt-taps` workflow, [user-side/user-side-smp.md](../user-side/user-side-smp.md)). History: neoui #5 (battery UI) was merged
past it by the owner.
- **What:** the QEMU boot test counts the Clock app's `clock: tick` lines and wants at least 2. It logs 1: the
  script taps as soon as Clock shows its surface, then goes back. Both runs of neoui #5 failed this way. Everything
  else in the run passes (boot, launcher, Terminal with `neotest` 10/0, Files, the switcher).
- **History:** red on `main` since `ed9202f` (Dev tools rebuild; a boot timeout then). `4beec4f` (T10) didn't
  compile (clippy `collapsible_if` in `usb_debug.rs`, fixed in #5). So #5 is the first run past compile in a day.
- **Not known:** whether the battery poller (every 5 s, a history file on C:) slows the Clock app on QEMU, or the
  check is only timing-sensitive.
- **Likely fix:** the script waits for a second tick (`expect "clock: tick"` twice) before tapping.

## Phone: the modem stays on 3G after a connected call (seen 2026-11-09)

**Status:** fixed 2026-11-12 (kernel `69bb4cd3`). The call audio voted two codec rails on the wrong PMIC.
- **The cause:** `a64_audio.cpp` `CdcProbe` voted `ldoa1`/`ldoa7` (PM660). The DTB puts vdd-cdc-tx-rx-cx (0.88 V)
  and vdd-micbias (3.088 V) on **PM660L**, `ldob1`/`ldob7`. PM660's ldo7 is a 1.2 V rail: the 3.088 V vote timed
  out (`[rpmh] ldoa7 ... -> -33`) at the first audio start of every call.
- **What it did:** afterwards the AOP stopped answering. The modem either stayed on 3G or raised FATAL in its own
  RPMh client (`rpmh_image_os.c:162 ... [Q6zip_Clk|ipa_ctl] suspected`), and QMP `load_state` timed out, so it
  could not be restarted either. The C7 runs of 2026-11-12 hit the FATAL; main stayed on 3G, then lost service.
- **The proof:** on the phone after a cold power-off (RPMh votes survive a warm reset), two connected calls voted
  `ldob1`/`ldob7 -> 0` and NAS came back on LTE right after each END.
- **Also in that commit:** `Rpmh_Write` serialized, and shared rails holder-counted (USB and the codec share
  ldob1/ldob7).

The notes below are the history.

The 2026-11-10 C7 implementation candidate adds bounded recovery and stricter APR
failure handling, but does not establish a cause or correction for this issue.
Acceptance requires normal call END and acknowledged audio teardown followed by
LTE registration, without restarting the modem/ADSP or cycling the radio.

**What is known:**
- calls on LTE drop to 3G (CSFB);
- a call hung up while ringing comes back to LTE within seconds;
- a call that connected (its voice path ran through the ADSP) stays on 3G. The modem stays up and calls keep working;
- Linux on this phone returns to LTE 1.7 s after a connected call;
- Earlier C6 testing found matching APR teardown and no post-call crash after kernel `b12d1ba`.
  C7 testing later captured a modem fatal (`wfw_demfront_sched.c:685`) after acknowledged teardown;
  the newer apparent freeze has no complete diagnostic reply, so its cause remains unconfirmed.

**Next to check:**
- the CDSP, which Linux runs and we don't;
- a PDR listener on the audio PD (Linux's `apr.c` registers one);
- what the modem still holds with the ADSP after END (a CVS session it created).

## Syborg: an odd screen width shears the picture (seen 2026-11-08)

**Status:** fixed 2026-11-25. The screenshot path was the cause: QEMU's `ppm_save` (`ui/ui-qmp-cmds.c`) wrote each PPM row
at pixman's 4-byte-rounded stride, 1620 bytes for a 1617-byte row at 539 px, so every row of the file was a pixel
further along. The guest's frame was right all along. Found again on `virt` in US6b; fixed in NeoSymbian/neoqemu's QEMU
(the toolchain image since build#63), and neoqemu's `ui-qemu.py` reads either form. History below.
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
