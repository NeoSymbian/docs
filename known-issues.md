# Known issues

## Phone: after a few normal restarts, ABL switches to slot b and test images die with a black screen

**Status:** open until FS5b ("boot OK" mark, `docs/filesystem.md`). Found 2026-11-07.

**Symptom:**
- Every `fastboot boot` answers `Booting OKAY`, then the screen stays black (no green kernel text) and the phone is
  back in fastboot within a minute.
- Even images that booted fine earlier fail, so it looks like a broken phone or a broken build. It is neither.

**Cause:**
- `fastboot flash boot_a` clears slot a's "successful" flag. ABL then gives slot a 3 retries.
- Every **normal** boot of the installed NeoSymbian uses one retry, because our kernel can't yet tell ABL "this boot
  worked". RAM boots (`fastboot boot`) don't count.
- At 0 retries, ABL marks slot a unbootable and makes **slot b** current. With slot b current, our images die before
  their first print. Not investigated further: we stay on slot a.

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
