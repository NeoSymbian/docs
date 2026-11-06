# ekern backend: what the AArch64 port still has to provide

Produced by `port/arm64/tools/ekern-census.sh` with `LINK=1` (2026-11-06, HEAD after 2689b0a):
- **Compile:** all 94 ekern + flexible memory-model translation units compile from unmodified 2010 kernelhwsrv source.
  The exceptions are the marked-delta copies in `port/arm64/{ekern,mm}`.
- **Link:** linked with the neutral nanokernel and our `a64smp` backend, the result has **79 undefined symbols and no
  multiple definitions**. Code is ~670 KB.

These 79 are the arch backend still to write: the M4.2 work list.

**Status (M4.2 step 2 done):**
- **Implemented:** all 79, in `port/arm64/ekern/`:
  - `a64e_nkern.cpp`: groups 7-8;
  - `a64e_cache.cpp`: group 2;
  - `a64e_trap.S` + `a64e_exc.cpp`: groups 3-4;
  - `a64e_exec.cpp`: group 5;
  - `a64e_mmu.cpp`: group 6;
  - `platform/a64_platform.cpp`: group 1's timer.
- **Link:** the census now leaves 14 undefined symbols, all provided by the board files and the variant the image
  links:
  - console: `A64_DebugPuts/Hex`;
  - GIC driver: `Gicv3_*`;
  - board constants and functions: `A64_GicdBase/GicrBase/PsciSmc/TimerPpi`, `A64_CpuCount/CpuMpidr`;
  - `A64_TickHook`.
- **Shortcuts still open:**
  - `NKern::BootAP` (one CPU);
  - user threads in `EpocThreadFunction`;
  - `PreprocessHandler` and `ThreadGetUserContext` (M4.4);
  - crash IPI / debugger. Templates:
- **Phorepoc x86-64** (`adaptation-x86-64/os/tools/phorepoc-x86`):
  - `port/x64ekern/xe_kernel.cpp`: umem, TExcTrap, EpocThreadFunction, exception info;
  - `xe_nkern.cpp`: Init0, timeslice, user-mode callbacks, BTrace stubs;
  - `xe_mmu.cpp`: process switch.
- **The ARM `.cia` files** these symbols came from, for semantics.

## 1. Board / variant (nkernsa had them in its board glue)
- `A64_CpuCount`, `A64_CpuMpidr`
- `A64_TimesliceRemaining`, `A64_TimesliceSet`: the per-CPU timer multiplexing; move from `nksa/a64_nksa.cpp` into a
  shared board/timer file.

## 2. Cache maintenance: `kernel/arm/cache_maintenance{,v7}.cia` in AArch64
- **ID registers:**
  - `InternalCache::TypeRegister` = CTR_EL0;
  - `LevelIDRegister` = CLIDR_EL1;
  - `SizeIdRegister` = CSSELR/CCSIDR_EL1.
- **D-cache, by VA (DC IVAC/CVAC/CIVAC/CVAU + DSB):** `Clean_DCache_Region`, `Clean_PoU_DCache_Region`,
  `Invalidate_DCache_Region`, `CleanAndInvalidate_DCache_Region`.
- **D-cache, whole:** `CleanAndInvalidate_DCache_All` (set/way loop).
- **I-cache:** `Invalidate_ICache_Region`, `Invalidate_ICache_All`, `IMB_CacheLine`. Use IC IALLUIS: an I-cache may be
  VIPT (see `mm/xmmu.cpp` Init1).
- **Barriers:** `DrainBuffers` = DSB SY.
- **Remap registers:** `PrimaryRegionRemapRegister` / `NormalMemoryRemapRegister` must return PRRR/NMRR-style values
  describing `KA64MairValue` types 4-7, for `TypeToCachingAttributes`.
- **`T_ISB_IPI::ISBIsr`:** ISB on each CPU.

## 3. Exceptions, traps, register state (`ckernel.cia`, `ncutils.cia`, `ncthrd.cpp`, `xkernel.cia`)
- **Register save:** `Arm::SaveState`, `Arm::UpdateState`, `DefaultRegSet`. They describe EL1/EL0 state as the
  AArch32 `SFullArmRegSet`/`TArmExcInfo`:
  - an EL1 fault is `ESvcMode` with the PC in `iR15`;
  - the shim stores ESR in `iFaultStatus` and FAR in `iFaultAddress` (the contract `M::DemandPagingFault` decodes).
- **User-visible exception path:** `PushExcInfoOnUserStack` (the 84-byte ABI frame `uc_exe.cia` unwinds),
  `DumpExcInfo`, `DumpFullRegSet`.
- **Trap frames:** `TExcTrap::Trap/Exception`, `TIpcExcTrap::Trap/IsTIpcExcTrap`, `TPagingExcTrap::Exception`.
- **Fault helpers:** `Exc::IsMagic` (EFalse if the umem routines use XTRAP, as x86-64's do), `UserReadFault`,
  `UserWriteFault`.
- **Interrupt helpers:** `InterruptsStatus`, `Arm::Init1Interrupts`.

## 4. User memory (`klib/arm/cumem.cia`, `cutils.cia`)
- **Copies:** `kumemget`, `kumemget32`, `kumemget_no_paging_assert`, `kumemput`, `kumemput32`,
  `kumemput_no_paging_assert`, `kumemset`, `umemput`.
- **Safe accessors:** `K::USafeRead/USafeWrite`, `Kern::KUSafeDec/KUSafeWrite`, `Kern::SafeRead`.
- **Page copy:** `pagecpy`.
- **Access rule:** user pointers use LDTR/STTR (unprivileged access, so EL1 can't be tricked into touching kernel
  memory). Addresses in the IPC alias window (0x7F000000-0x7FFFFFFF) need privileged LDR/STR, because that window is
  EL1-only (APTable).

## 5. Executive calls (`kernel/arm/cexec.cia`)
- **`EpocFastExecTable` / `EpocSlowExecTable`:** one TU must instantiate them. ARM does it in `cexec.cia`; our
  `port/arm64/ekern/execs.h` already emits C arrays, so a TU including `execs.h` the way `cexec` does is enough.
- **`DThread::EpocThreadFunction`:** first entry to user mode (ERET to EL0 AArch32, SPSR M=0x10).
- **Exec gate:** not an undefined symbol (it lives in the vectors), but M4.4 needs it. EC 0x11 SVC, opcode via LDTR at
  ELR-4, bit 23 fast/slow.

## 6. Address-space switch (`memmodel/epoc/flexible/arm/xsched.cia`)
- **`DoProcessSwitch`, `DMemModelThread::RestoreAddressSpace`:**
  `TTBR0_EL1 = A64RootTablePhys + (asid<<5) | asid<<48; ISB`. Then restore a live alias PDE: store it, then
  `LocalInvalidateTLBForPage`.

## 7. Full-kernel nanokernel API not in the nkernsa backend
- `NKern::Init0`
- `NKern::BootAP`: PSCI CPU_ON with `SArmAPBootInfo::iMpidr`, plus the entry point
- `NKern::CpuIdleHandler`, `NKern::IdleGenerationCount`
- `NKern::NotifyCrash`
- `NKern::QueueUserModeCallback`
- `NKern::ThreadGetUserContext`: AArch32 user registers from the EL0 exception frame
- `NKern::TimesliceTicks`
- `TSpinLock::FlashIrq`, `TSpinLock::FlashIrqRestore`
- `__arm_cpu_number`

## 8. Small runtime bits
- **BTrace:** `OutX`, `OutN`, `OutNX`, `SetFilter`, `SetHandlers` (stubs, as x86-64).
- **Debug, nothing behind them yet:** `A::StartCrashDebugger`, `Arm::DebugOutJTAG` (KErrNotSupported).
- **Kernel helpers:** `K::DoNanoWait` (generic timer), `K::FloatingPointSystemId`.
- **C++ runtime:** `__cxa_pure_virtual`; `operator new/new[]/delete/delete[]` over `Kern::Alloc/Free` (the ARM build
  gets them from its kernel-side runtime).

**M4.2 steps 3-5 done (`4f0e613`, `bc29b8c`):** variant (`board/a64_variant.cpp`), bootstrap (`boot/a64boot.cpp`),
entry (`ekern/a64e_entry.cpp`), `boot/ekern.lds`, `tools/build-ekern.sh`. The kernel boots and passes its self-test on
QEMU and on the Pixel (1 CPU). Fixes the first boot needed:
- `KPageTableEnd` = 0xFFE00000: a fixed kernel region must be whole 2 MB chunks (`DMemoryManager::New` makes anything
  else a fine object, which must fit one page table);
- `Mmu::BlankPte`: global user-executable pages (the ROM, which holds the kernel's own code) stay executable at EL1;
- the naked trap forwarders are `noinline` and `TExcTrap::Exception` is an ordinary call: GCC inlined the naked body
  and lost the result argument;
- the asm entry points zero-extend ILP32 pointer arguments;
- the Pixel's ROM is linked at 0x80200000: ABL loads the image at 0x80080000, inside the first ROM chunk.

**M4.2 step 6 done (`211931b`):** `NKern::BootAP` starts each CPU with PSCI `CPU_ON` into `boot.S` `A64_ApEntry`,
which turns the MMU on with a private boot root (OS ASID 0's entries plus a 2 MB identity block over the boot stub)
and enters `A64_ApStart`, which moves to the kernel's root and runs `ApMainGeneric`. `A64_CpuCount()` counts CPUs with
PSCI `AFFINITY_INFO`. On QEMU (`-smp` 1/2/4/8) and on the Pixel (8 cores), every CPU comes up and the self-test passes.

Shortcuts still open: user threads in `EpocThreadFunction`, `PreprocessHandler` and `ThreadGetUserContext` (M4.4),
the crash IPI / debugger.

What was originally listed as still needed before a boot (all done):
- **Bootstrap** (`boot/a64boot.cpp`): tables, super page, ROM header, `KRootTableBase` with the kernel root, MAIR/TCR.
- **Variant** (`Asic`).
- **Linker script** at the native addresses.

All of that is M4.2.
