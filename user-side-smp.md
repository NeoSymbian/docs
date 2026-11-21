# The user side on modern cores: SMP-safe, one ARMv8-A AArch32 flavour (US0–US6)

Written 2026-11-20 (browser WB4c session). It extends [smooth-ui.md](neoui-shell/smooth-ui.md) S4 (the Rust ARMv7 target) to
the whole user side, and puts one urgent fix in front. Revised 2026-11-21 after US1: the owner chose one user-side
flavour, 32-bit ARMv8-A; the stages below follow a Codex (`gpt-6.2-astra`) research pass, checked against the code.

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
  - **One flavour, no ARMv5/v6/v7 builds** (owner, 2026-11-21). The CI runs on QEMU `virt` under our AArch64
    kernel, which boots the same user payload as the phone (US6a/US6b).
  - **Syborg is no longer a target** (owner, 2026-11-21: "why we need syborg, ignore it"). Its 2010 ARM kernel has
    no VFP support and doesn't keep the user-side thread data, so the ARMv8 user side doesn't run there (efile dies on
    its first `vldr d16`; with VFP off, E32USER-CBase 66). build's and e32-rs's CI boot `virt` only; neoui's Syborg UI
    job is manual until US6b ports it; `neo boot`/`neo live` (Syborg) don't run new builds until `virt` has a VNC view.
  - **32-bit, not 64-bit:** the kernel is AArch64; the user side stays AArch32. A 64-bit user side is
    [parked](#parked-a-64-bit-user-side).
- **Calling convention: soft-float stays.**
  - New code may use VFP/NEON inside a function, but floats still pass in core registers.
  - Never `eabihf`: it breaks every call into the 2010 libraries.
- **Locks and atomics:** LDREX/STREX with DMB (SMP semantics), with no SWP and no kernel-assisted atomics.
  - The kernel's SWP emulation (`a64e_a32fix.cpp`) stays for old binaries.
- **Code:** Thumb-2 where it's smaller, NEON for the hot loops.
- **Old S60 apps still run.** They are frozen ARMv5/v6 binaries; ARMv8 AArch32 executes them as they are. The kernel
  keeps 32-bit EL0, the SWP emulation and the CP15 barriers (`CP15BEN`), and the rebuilt libraries keep the E32
  `ECpuArmV5` header value, the frozen `.def` ordinals and `EKernelConfigSMPUnsafeCompat`.

## Stages

| Stage | What | Where | Exit |
|---|---|---|---|
| **US0** | euser `.cia` built with `-D__CPU_CORTEX_A9__ -D__SMP__` (A8N + `__SMP__` is a `cpudefs.h` `#error`): 133 DMBs, none before | build `emitter/build_euser_device.py` (`_extra_flags_tu`), **build#41** | **Pixel 2026-11-20:** 3.5 min of browsing with no crash, against 3/3 crashes within 2 min before; a 15-min soak is pending. The UI ROM boots on Syborg |
| **US1** | The user side's other synchronisation, audited for single-core assumptions; [list below](#us1-the-audit). Fixes: `RReadWriteLock` order and the SWP emulation's barrier (kernel), 11 P.I.P.S. races (ossrv), a barrier after a polled `TRequestStatus` (e32-rs) | kernel#32, ossrv#4, e32-rs#8 (merged 2026-11-21) | Every site fixed or marked safe; STDTEST's `smp` checks fail before and pass after on the Pixel |
| **US6a** | CI baseline on QEMU `virt` (our kernel, 4 × Cortex-A55): C: fixture, R0–R3, the seven named `smp` checks, PASS markers. Record the US1 baseline: E32 hashes, sizes, 5 Pixel boot medians, AArch32 CRC/AES/SHA known-answer tests on both clusters. A time-boxed Syborg `-cpu max,has_el2=off` spike | build `.github/workflows/build.yml`, kernel `tools/test-fshell-qemu.py` | The US1 payload is green on `virt`; baseline numbers below |
| **US2** | euser, efsrv, hal as ARMv8-A AArch32 (`-march=armv8-a+crc+crypto -mfloat-abi=softfp`, A9 + `__SMP__` profile), through one target setting; [three blockers first](#us2-what-to-fix-first) | build `toolchain/symcc`, `emitter/*.py`; kernel euser | Pixel RAM boot and `virt`; export/ordinal/stub/layout diff clean; TLS and nested-TRAP FP tests; R0–R3, `smp` 3/3; X-plore and Frozen Bubble; size and boot time against the baseline |
| **US6b** | UI CI parity: neoui's Syborg tap, gesture, app-switch and old-app assertions ported to `virt` (pointer input, 539×1079) | neoui `syborg.yml`, `symbian/taps.sh`, kernel `qemu_variant` | Same assertions and screenshots on `virt`; then the Syborg user-side jobs retire |
| **US3** | The rest of the 2010 ROM (P.I.P.S., ESOCK, graphics, middleware, old-app providers) through the same setting; rebuild the reachable GNU runtime members | build | Fresh full build: no rejected relocations, lost ordinals or new stubs; full UI, old apps, 15-min browser soak, R0–R3, `smp`, CI |
| **US4** | Rust and the browser on one `armv8a-symbian-eabi.json` (`llvm-target armv8a-none-eabi`, `llvm-floatabi soft`, `max-atomic-width 64`, `+v8,+thumb2,+neon,+crc,…`, `c-enum-min-bits 32`, ARM state): real atomics, `Arc`, NEON. `e32` picks its runtime by feature, not `target_os`; `e32-sys` uses `fence(Acquire)`; NEOWB1's FP test fixed first | e32-rs, neoui, phone, files, neohw, browser | Both build-std modes; R0–R3, NEOWB1 6/6, MIXTEST 225, 64-bit atomic stress, `smp` 3/3, browser soak; neoui ns/px before/after (smooth-ui S4 exit) |
| **US5** | Clean-up: drop the ARMv5TE paths and aliases; docs (rust-integration, port-map, CLAUDE.md ABI rules) | build, docs | One user-side ABI; phone and CI run identical user E32 hashes |

US0 and US1 are done (merged 2026-11-21, installed as `2026-11-20-finchmane`). The order is US6a → US2 → US6b → US3 →
US4 → US5; about 18–32 working days. Each stage builds one user payload and boots it with `neo kernel qemu` and
`neo kernel bonito` from the same volume (`SIS=xplore,frozenbubble`, `ROFS_CORE='\.dll$'`); budgets against the US1
baseline: size +5 %, boot median +10 %. Later, only with a measured gain: an ARMv8 CPU profile in `cpudefs.h`
(`LDA`/`STL` in `atomic_32_v6.h`/`uc_utl.cia`, `CRC32` in `Mem::Crc32`).

The seven checks, run three times, must each print `7 ok, 0 failed` (`stdtest smp` alone selects nothing):

```text
stdtest smp_printf_g smp_condvar_timeout smp_static_init smp_once smp_stdio smp_shared_fd smp_sem_timeout
```

## US6a: results so far (2026-11-21)

- **The driver:** kernel#33 gives `test-fshell-qemu.py` `--cdrive` (pushes the build's drive=c EXEs to C:) and
  `--run` (runs a program in fshell, prints its exit status).
- **CI:** e32-rs#9 boots the same ROM on `virt` after Syborg and checks R0–R3 and NEOWB1 there. First run: neohello 0,
  neor1 42, neopanic `Panic RUST`, neotest 12/12, neor1c 42 (pushed to C:), neocli 9/9, **NEOWB1 6/6** (it needs our
  kernel, so it never ran in CI before).
- **SMP on virt** (atlas, the `2026-11-20-finchmane` user side with the eshell console): the seven `smp` checks print
  `7 ok, 0 failed, 0 skipped`. QEMU on an x86 host orders memory more strongly than the Pixel, so the phone stays the
  real test of ordering; `virt` catches crashes, hangs and lost wake-ups.
- **Syborg with an ARMv8 CPU:** the 2010 Syborg ROM (ARMv5 user side) boots with `-cpu max,has_el2=off` as on the
  Cortex-A8 (symbian-qemu#1, build#45), but the ARMv8 user side doesn't (above): Syborg is dropped.
- **Size baseline** (`2026-11-20-finchmane`, bonito flash image): core ROM 255 E32 images, 13,903,220 bytes
  (`romsect.bin` 13,337,812); ROFS 48 E32 images, 41,433,068 bytes (`rofs.img` 50,278,808); `boot.img` 6,569,984.
  `euser.dll` 431,648, `efsrv.dll` 60,436, `hal.dll` 4,960. Per-image list with SHA-256: atlas task `us1`,
  `logs/baseline-e32.txt`.
- **Still to do:** 5 Pixel RAM-boot medians; AArch32 CRC32/AES/SHA known-answer tests on both clusters.

## US2: what to fix first

1. **Runtime library relocations.** The v8 multilib (`thumb/v8-a+simd/softfp`) has `libgcc.a`/`libsupc++.a`, but
   their members carry `R_ARM_THM_MOVW_ABS_NC`/`MOVT_ABS` relocations (10 + 10 and 170 + 170), which the E32 writer
   rejects (`build/emitter/elf.py:269`); some stay reachable from `__cxa_throw`. Rebuild the reachable members with
   `-mword-relocations -mno-unaligned-access` (as the browser SDK, `browser/tools/symbian-sdk.sh`); the root
   (ARMv5) members only as a bridge. Check `Tag_ABI_VFP_args`, enum and `wchar_t` attributes on what is linked.
2. **TLS.** The A9 profile turns on `TLocalThreadData` (`u32std.h:763`) and moves heap, active scheduler, trap handler
   and DLL TLS to it. The emitter's euser source list lacks `euser/epoc/arm/uc_data.cpp` (`DllTls`, `DllSetTls`,
   `DllFreeTls`): add it and reject any new panic stub.
3. **FP registers across a leave.** With softfp, GCC keeps live values in `d8`–`d15` (callee-saved). `Trap`
   (`uc_trp.cia:44/90`) and P.I.P.S. `setjmp`/`longjmp` (`jmp_marm.cia`) save only core registers, so a leave can return
   with clobbered FP registers. Preserve them without growing the frozen `TTrap`/`jmp_buf`, with nested sentinel tests
   through TRAP, `longjmp` and the RVCT/EHABI leave path.

Also, measured: no exported struct changes with `__SMP__` (`RFastLock` 8, `RReadWriteLock` 40, `CActive` 28,
`RHybridHeap` 744 bytes under v5, v8 UP and v8 SMP). The MMP parser keeps its `MARM_ARMV5`/`EABI` macros
(`emitter/mmp.py:41`): they select sources and `.def` files, not the CPU. The 16 `-march=armv5te` sites in
`emitter/*.py` and the `.cia` override in `build_euser_device.py` become one `USER_TARGET_FLAGS` in `toolchain/symcc`.

**Old apps, still to test** (kernel side is set: `CP15BEN=1`, `A`/`ITD`/`SED` clear, FP on, `a64boot.cpp:612`):
SWP byte/word/contention on the phone (QEMU executes SWP itself, so only the Pixel tests the trap path); VFP short
vectors (`FPSCR.LEN`/`STRIDE`) are gone in ARMv8 and not emulated; the alignment fix-ups ignore `SETEND`. Act on these
only with a failing app or fixture.

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
| P12 | ossrv `libc` `localeinfo.cpp`, `lnumeric.cpp`, `lmonetary.cpp`, `timelocal.cpp`, `setlocale.cpp` | Without `setlocale`, every `snprintf` reloads the system locale into 20/50-byte shared buffers, moving global pointers as cursors: two threads overflowed them into the backend heap (a TLS key node's `next` became garbage). Now one recursive lock |
| P13 | ossrv `libc` `neo_posix.cpp` (ours) | `pread`/`pwrite` emulation (seek, transfer, seek back) interleaved between threads on one fd |
| P14 | ossrv `libc` `stdio/fclose.c` | `fclose` released the FILE slot before destroying its mutex; another thread's `fopen` locked the mutex being destroyed |
| R1 | e32-rs `e32-sys` `TRequestStatus::get` | A completed status seen by polling had no acquire barrier |

**Before the fixes, on the Pixel** (main `dd7e573`): `smp_printf_g` killed threads (KERN-EXEC 0 and 3),
`smp_static_init` had 13,494 error returns, and `smp_shared_fd` aborted (KERN-EXEC 3, jumps to address 0) and hung
STDTEST. P12–P14 were found by these checks, after the audit.

**After** (build `0ae7e94`: kernel `d13d70ee`, ossrv `00d888e`, the Rust apps of every repo's main): all seven `smp`
checks pass 3 runs of 3 on the Pixel, no aborts; the UI ROM boots on Syborg; the modem stays on LTE.

**Old apps (K2, the SWP path), the same build with `SIS=xplore,frozenbubble` and the installed `ROFS_CORE='\.dll$'`
split, on the Pixel:** Frozen Bubble, X-plore and PerfMon run, with no panics or kernel faults. eshell quits with -1, as
it did before US1. (Without `ROFS_CORE` the old-apps launcher fails with -5 and X-plore panics in `aknskins.dll`: a
recipe mistake, not US1.)

**Found, not US1 (it happens on main too):** the first sockets of a process, made by 3 threads at once while ESock
starts, crash `c32exe.exe::ESock_DIP` (KERN-EXEC 3, null read) and C32Start reboots the phone (STDTEST
`smp_cross_thread_fd`). Probably what made NEOWEBE see EBADF on connect and on `/dev/urandom` in one session.

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

## Parked: a 64-bit user side

Investigated 2026-11-21 (owner's question): AArch64 user code next to the old AArch32 apps.

- **Possible.** The CPUs pick AArch32 or AArch64 per thread on each return to EL0, so one process is one ISA. With
  32-bit pointers (ILP32, like the kernel), every struct, descriptor, IPC message and exec call keeps its layout, and
  both kinds of process talk to the same servers.
- **Found:** the kernel's vectors already save the same frame for AArch64 EL0, but `a64e_exc.cpp:369` rejects it
  ("there is no AArch64 user code"); exec calls come only from AArch32 SVC (ESR EC 0x11); the E32 CPU field
  (`f32image.h:37`) knows ARMv4/5/6 only. A Rust no_std ILP32 build works with a custom target spec
  (`llvm-target aarch64-unknown-linux-gnu_ilp32`, `ldaddal` atomics). GCC 14 `-mabi=ilp32` compiles, but the toolchain
  image has no ILP32 `libgcc`/`libsupc++`, GCC has no large code model with ILP32, and GCC 15 deprecated ILP32.
- **Why parked:** every library an old app uses stays AArch32 while 64-bit processes need their own copies; code
  reaches its data with PC-relative `ADRP`, but Symbian loads code and data apart (new E32 relocation types or a GOT
  in the code segment); euser's assembly needs rewriting. On the Pixel the gain over 32-bit ARMv8 is small.
- **When to revisit:** a target phone whose cores lack AArch32 EL0 (recent big cores). Old apps would then need a
  translator anyway. Stages if so: A0 kernel + loader proof with one Rust test EXE, A1 toolchain and relocations,
  A2 euser/efsrv/hal and Rust apps, A3 P.I.P.S., browser and servers.

## Risks

- **Kernel and user side out of step:** `__SMP__` on euser's C++ arrives with US2. Measured: no exported struct
  changes; `TLocalThreadData` comes with the A9 CPU profile, and the kernel already sets it up (`a64e_exec.cpp:162`).
- **Code size** grows a little with Thumb-2 + NEON and barriers. The ROFS limit is 256 MB (kernel `wb4-rofs`).
- **Old binaries:** apps built for ARMv5 keep their own inline SWP. They stay correct only while the kernel emulation
  is atomic (it is: an LDXR/STXR loop plus DMB).
