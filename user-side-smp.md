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

- **Instruction set:** ARMv7-A, which ARMv8-AArch32 runs as-is. It runs on the Pixel (A55/A75 in AArch32), on QEMU
  virt and on QEMU Syborg (Cortex-A8). No ARMv8-only AArch32 instructions (LDA/STL), so Syborg keeps working.
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
| **US0** | euser `.cia` built with `-D__SMP__`; check with objdump that DMBs are in `RFastLock::Wait/Signal` and the `__e32_atomic_*_acq/_rel/_ord` | build `emitter/build_euser_device.py` (`_extra_flags_tu`) | NEOWEBE survives 15 min of browsing on the Pixel with `C:\neowebe.check`; neotest and the Syborg CI pass |
| **US1** | Audit the user side's other hand-written synchronisation for ARMv5/UP assumptions: P.I.P.S. (libpthread, backend locks), the efsrv client, the window-server client, `User::LockedInc/Dec`, the `.cia` files of other DLLs | kernel (euser), ossrv | A list: each site is fixed or marked safe |
| **US2** | All of euser (C++ too) as ARMv7 `-march=armv7-a -mfloat-abi=softfp`; the same for efsrv and hal | build emitter | Pixel + Syborg boot; neotest, R0–R3, neoui CI; size and boot time recorded |
| **US3** | The rest of the 2010 ROM (P.I.P.S., ESOCK, the window server stack, …) as ARMv7: one `-march` switch in `build_mmp.py`/`symcc` | build | The full UI ROM boots on both; SWP-trap counter (smooth-ui S4 open question) near 0 |
| **US4** | no_std Rust moves to `armv7a-neosymbian-eabi` (smooth-ui S4): real `core::sync::atomic`, `Arc`, NEON in neoui-render | e32-rs, neoui, phone, files, neohw | neotest on both; neoui ns/px before/after (S4 exit) |
| **US5** | Clean-up: drop the ARMv5TE build paths from the emitter; docs (rust-integration, port-map, CLAUDE.md ABI rules) | build, docs | One user-side ABI left: ARMv7 softfp |

US0 is urgent and small. US1 decides how much of US2–US3 is correctness work and how much is speed. US4 can run in
parallel once US0 is in.

## Requirements to start (US0)

1. In `build/emitter/build_euser_device.py`, `_extra_flags_tu`, add `-D__SMP__` to the `.cia` flags. Leave the C++
   flags alone (`__SMP__` may change structs there; that's for US2).
2. Rebuild euser. Check that `armv7-symbian-objdump -d euser0.elf` shows `dmb` in `RFastLock::Wait`, `RFastLock::Signal`
   and `__e32_atomic_add_acq32`.
3. Test on the Pixel, RAM boot only: a UI ROM with `ROFS=1 EMMC_C=1 USBDEBUG=1 AUTOFASTBOOT=…`.
   - Browse with NEOWEB/NEOWEBE for 15 minutes with `C:\neowebe.check` present.
   - Pass: no KERN-EXEC 3 in RHybridHeap and no heap-check panic.
4. Check that nothing else broke: neotest and the neoui Syborg CI.
5. Merge, re-pin `build`, and install it on slot a (the owner's call). Every multithreaded process benefits.

## Risks

- **Kernel and user side out of step:** `__SMP__` must stay off the C++ files until US2. Some euser C++ structs
  (`TLocalThreadData` …) may differ between the SMP and UP builds.
- **Code size** grows a little with ARMv7 Thumb-2 + NEON and barriers. The ROFS limit is 256 MB (kernel `wb4-rofs`).
- **Old binaries:** apps built for ARMv5 keep their own inline SWP. They stay correct only while the kernel emulation
  is atomic (it is: an LDXR/STXR loop plus DMB).
