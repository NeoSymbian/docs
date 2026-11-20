# The user side on modern cores: SMP-safe, ARMv7/ARMv8-AArch32 (proposal US0–US5)

Written 2026-11-20 (browser WB4c session). It extends [smooth-ui.md](smooth-ui.md) S4 (the Rust ARMv7 target) to
the whole user side, and puts one urgent fix in front.

## Why

- **Two worlds today.**
  - The kernel is AArch64 SMP on 8 cores.
  - The user side is the 2010 code built for one ARMv5TE core.
- **Already modern:**
  - the kernel saves NEON per thread (WB1);
  - the browser's Rust and C/C++ (`armv7a-symbian-eabi`, WB2a) are ARMv7 with NEON;
  - euser's assembly files (`.cia`) are built as ARMv7 for LDREX/STREX (`build_euser_device.py`).
- **Still ARMv5TE:**
  - every other user-side binary: euser's C++, efsrv, P.I.P.S., the window server stack, legacy apps;
  - all no_std Rust (`armv5te-none-eabi`: neoui, phone, files, neohw).

### Finding (2026-11-20): user-side locks have no memory barriers

- euser's `.cia` files are compiled for `__CPU_CORTEX_A8N__` without `__SMP__`.
- In `uc_utl.cia`, `uc_exec.cia` and `atomics.cia` the barriers exist only `#ifdef __SMP__`.
- So the built euser has **no DMB** in:
  - `RFastLock::Wait`/`Signal`;
  - `__e32_atomic_*_acq/_rel/_ord`;
  - the release path in `uc_exec.cia`.

  Checked by disassembling `euser0.elf`: LDREX/STREX loops, then `mov pc, lr`.
- **Impact:** on the Pixel's weakly ordered cores, a lock doesn't order the data it guards. RHybridHeap's lock is an
  RFastLock, so every multithreaded process can corrupt its heap.
- **Seen:** NEOWEBE (Servo, about 30 threads) dies after 1–2 minutes:
  - in `RHybridHeap::SlabFree`/`DlFree`;
  - with garbage strings and jumps to data.
- **Fix:** in those three files, `__SMP__` only adds barriers (`cpudefs.h` selects `DMB` for ARMv7). It is a build-flag
  change. Cortex-A8 (QEMU Syborg) runs DMB too.

## What "modern" means here

- **Instruction set: ARMv8-A AArch32** (owner's decision, 2026-11-20: as current as the hardware allows). The Pixel's
  A55/A75 are ARMv8.2-A. In AArch32 that adds to ARMv7: acquire/release loads and stores (`LDA`/`STL`, cheaper locks
  than LDREX + DMB), CRC32, AES/SHA (TLS, zip), and the ARMv8 NEON/VFP additions. Flags: `-march=armv8-a+crc+crypto`
  (C/C++), an ARMv8 AArch32 Rust target.
  - **QEMU Syborg is not a blocker.** It emulates a Cortex-A8 (ARMv7), so ARMv8 binaries don't run there. Updating
    it is its own stage (US6). Until then, Syborg keeps building the ARMv7 flavour, and the phone images move ahead.
- **Calling convention: soft-float stays.**
  - New code may use VFP/NEON inside a function, but floats still pass in core registers.
  - Never `eabihf`: it breaks every call into the 2010 libraries.
- **Locks and atomics:** LDREX/STREX with DMB (SMP semantics), with no SWP and no kernel-assisted atomics.
  - The kernel's SWP emulation (`a64e_a32fix.cpp`) stays for old binaries.
- **Code:** Thumb-2 where it's smaller, NEON for the hot loops.
- **Old S60 apps still run.** They are ARMv5 code, ARMv8-AArch32 executes it, and their SWP keeps trapping to the
  emulation.

## Stages

| Stage | What | Where | Exit |
|---|---|---|---|
| **US0** | euser `.cia` built with `-D__CPU_CORTEX_A9__ -D__SMP__` (A8N + `__SMP__` is a `cpudefs.h` `#error`): 133 DMBs, none before | build `emitter/build_euser_device.py` (`_extra_flags_tu`), **build#41** | **Pixel 2026-11-20:** 3.5 min of browsing with no crash, against 3/3 crashes within 2 min before; a 15-min soak is pending. The UI ROM boots on Syborg |
| **US1** | The user side's other synchronisation, audited for single-core assumptions; [list below](#us1-the-audit). Fixes: `RReadWriteLock` order and the SWP emulation's barrier (kernel), 11 P.I.P.S. races (ossrv), a barrier after a polled `TRequestStatus` (e32-rs) | kernel, ossrv, e32-rs (branches `user-side-smp-us1`) | Every site fixed or marked safe; STDTEST's `smp` checks fail before and pass after on the Pixel |
| **US2** | All of euser (C++ too) as ARMv8-A AArch32 softfp (`-march=armv8-a+crc+crypto -mfloat-abi=softfp`), with `__SMP__`; the same for efsrv and hal | build emitter | Pixel boots; neotest, R0–R3; size and boot time recorded |
| **US3** | The rest of the 2010 ROM (P.I.P.S., ESOCK, the window server stack, …) as ARMv8-A AArch32: one `-march` switch in `build_mmp.py`/`symcc` | build | The full UI ROM boots on the Pixel; SWP-trap counter (smooth-ui S4 open question) near 0 |
| **US4** | no_std Rust on an ARMv8 AArch32 target (smooth-ui S4): real `core::sync::atomic`, `Arc`, NEON in neoui-render; the browser's `armv7a-symbian-eabi` moves up too | e32-rs, neoui, phone, files, neohw, browser | neotest on the Pixel; neoui ns/px before/after (S4 exit) |
| **US5** | Clean-up: drop the ARMv5TE build paths from the emitter; docs (rust-integration, port-map, CLAUDE.md ABI rules) | build, docs | One user-side ABI left: ARMv8-A AArch32 softfp |
| **US6** | QEMU catches up: an ARMv8 CPU for the Syborg board (`symbian-qemu`), or the tests move to QEMU virt under our AArch64 kernel (`neo kernel qemu`). Until then Syborg builds the ARMv7 flavour | symbian-qemu, build, CI | The CI boots the same ARMv8 user side the phone runs |

US0 is urgent and small. US1 decides how much of US2–US3 is correctness work and how much is speed. US4 can run in
parallel once US0 is in. US6 never blocks US2–US5.

## US1: the audit

Checked: euser and the kernel's user-visible paths, every `.cia` the emitter builds, the pinned 2010 packages (grep for
hand-written locks, `__e32_atomic`, `LockedInc`, `__sync`), P.I.P.S. (libpthread, backend, libc), and the Rust crates.

**Fixed** (branches `user-side-smp-us1`; test: STDTEST's `smp` group, browser `std/stdtest/src/smp.rs`):

| # | Where | What was wrong |
|---|---|---|
| K1 | kernel `euser/us_rwlock.cpp` | `RReadWriteLock` took the lock with a release CAS and gave it up with an acquire CAS (upstream 2010 bug) |
| K2 | kernel `arm64/a64e_a32fix.cpp` | SWP emulation had only a trailing DMB; old binaries use SWP to release locks too |
| P1 | ossrv `backend` `fdesc.h`/`fdesc.cpp` | Descriptor dup count `++`/`--` on every read/write, from any thread |
| P2 | ossrv `backend` `ftable.cpp` | fd-table lookups, dup and detach without `iFidLock` (CArrayPtrSeg lookups even write its cache) |
| P3 | ossrv `libpthread` `condvar.cpp` | A timed wait that timed out after a signal took its node freed the node under the signaller |
| P4–P6 | ossrv `libpthread` `mutex.cpp`, `condvar.cpp`, `pthread_once.cpp` | Static initializers and `pthread_once` published and tested state without acquire/release |
| P7 | ossrv `libc` `stdio/findfp.c` | `__sfp()` had an empty lock: two threads could take one FILE |
| P8 | ossrv `libc` `gdtoa/misc.c` | `pow5mult`'s cache was published before it was complete |
| P9–P10 | ossrv `libpthread` `sem_*.cpp` | A post racing `sem_timedwait`'s timeout left a token too many; error paths kept the mutex |
| P11 | ossrv `libc` `clock_funcs.cpp` | No ISB before the generic-timer read |
| R1 | e32-rs `e32-sys` `TRequestStatus::get` | A completed status seen by polling had no acquire barrier |

**Before the fixes, on the Pixel** (main `dd7e573`): `smp_printf_g` killed threads (KERN-EXEC 0 and 3),
`smp_static_init` had 13,494 error returns, and `smp_shared_fd` aborted (KERN-EXEC 3) and hung STDTEST.

**Safe, nothing to do:** the rest of euser's sync now that its atomics have barriers (`LockedInc`/`SafeInc`,
`RCriticalSection`, `RHybridHeap`, TLS, the active scheduler); efsrv and hal have no `.cia`; the other 2010 packages only
call euser's atomics (gdi/textbase `hextree.cpp`, commsfw `User::LockedInc`); CP15 barriers are enabled at EL0; no
`__sync_*` anywhere. ARMv5TE Rust has no atomics at all (`critical-section` is a kernel `RMutex`), and every hand-off
between threads goes through a kernel object.

**Left, recorded:** libstdcpp is built with `_STLP_NO_THREADS` (the browser doesn't link it); the backend's
signal-handler flag (`localif.cpp:607`, only with `SYMBIAN_OE_POSIX_SIGNALS`); `-fno-threadsafe-statics` in the mmp
components (as the 2010 build); the SWP emulation checks access and then accesses (`a64e_a32fix.cpp:38-59`).

## US0 recipe (done: build#41)

1. In `build/emitter/build_euser_device.py`, `_extra_flags_tu`, give the `.cia` files `-D__CPU_CORTEX_A9__ -D__SMP__`
   in place of `__CPU_CORTEX_A8N__`. Leave the C++ flags alone (`__SMP__` may change structs there; that's for US2).
2. Rebuild euser. Check that `armv7-symbian-objdump -d euser0.elf` shows `dmb` in `RFastLock::Wait`, `RFastLock::Signal`
   and `__e32_atomic_add_acq32`.
3. Test on the Pixel, RAM boot only: a UI ROM with `ROFS=1 EMMC_C=1 USBDEBUG=1 AUTOFASTBOOT=…`.
   - Browse with NEOWEB/NEOWEBE for 15 minutes, **without** `C:\neowebe.check`. Its whole-heap check runs on every
     command (300–600 ms each), so the browser crawls; keep it for finding where a corruption happens.
   - Pass: no KERN-EXEC 3 in RHybridHeap, and no abort or panic in a neowebe thread.
4. Check that nothing else broke: neotest and the neoui Syborg CI.
5. Merge, re-pin `build`, and install it on slot a (the owner's call). Every multithreaded process benefits.

## Risks

- **Kernel and user side out of step:** `__SMP__` must stay off the C++ files until US2. Some euser C++ structs
  (`TLocalThreadData` …) may differ between the SMP and UP builds.
- **Code size** grows a little with Thumb-2 + NEON and barriers. The ROFS limit is 256 MB (kernel `wb4-rofs`).
- **Old binaries:** apps built for ARMv5 keep their own inline SWP. They stay correct only while the kernel emulation
  is atomic (it is: an LDXR/STXR loop plus DMB).
