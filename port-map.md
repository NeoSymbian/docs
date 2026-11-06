# Port map: EKA2 → AArch64 ILP32 kernel, AArch32 EL0 user side unchanged

Written 2026-11-05 from clones that now sit next to this repo in the NeoSymbian workspace (`../<repo>`; they were in
`ref/` until 2026-11-06): SymbianSource `oss.FCL.sf.os.kernelhwsrv` (KHS, `kernel/eka`),
Phorepoc `adaptation-x86-64`, `adaptation-a64` and `core`. Line counts come from `wc -l`; "asm" is the number of `asm(` lines.
Lines marked **GUESS** were not verified. Action legend:
- **new**: write for AArch64;
- **adapt**: copy with marked deltas;
- **reuse**: compile unchanged;
- **generic**: leave the `__*_MACHINE_CODED__` macro undefined so the portable C++ is used;
- **defer**: not needed for the first milestone.

## Key findings

1. **The x64 port is file-level overrides, not an arch rewrite.** It never edits the baseline tree. It uses four mechanisms:
   - shadow headers placed first on `-I`;
   - "marked-delta" copies of single translation units;
   - new sibling files that replace the asm-heavy ones;
   - everything else compiled unmodified, including arch C++.

   Kernel and user are both `-mx32`. With 32-bit pointers, EKA2's compile-time layout asserts stay valid. Copy this approach.
2. **They recompiled their user side; ours stays ARM32.** Only the kernel census pattern (`ekern_census_x32.sh`) transfers.
3. **In ARM SMP EKA2 the GIC, SCU and per-CPU timer are nanokernel code**, not variant code: `nkernsmp/arm/ncirq.cpp`, `include/nkernsmp/arm/arm_gic.h|arm_scu.h|arm_tmr.h` and the IRQ ack/EOI asm. GICv3 support therefore lands in our nanokernel backend.
4. **The fast/slow exec flag is bit 23 of the SWI immediate.** The kernel reads the opcode back at `lr-4` (`vectors.cia:140`). An AArch64 kernel does the same with `LDTR` at ELR-4.
5. **Phorepoc's ARM kernel already runs the 2010 user side on ARMv8 AArch32**, with fix-ups we need too:
   - SWP/SWPB emulation;
   - misaligned LDRD/STRD/LDM/STM emulation;
   - VFP short-vector emulation;
   - no ThumbEE.

   They are in `adaptation-a64/os/tools/kernel/ekern_seam.cpp:1162-1603`.
6. **Size.** x64 needed about 3.5k new lines for nanokernel + boot + traps/IRQ + SMP, and about 1k more for the ekern/MMU backend. arm64 estimate: 4–5k lines for the first milestone (section 7).

## 1. The x64 template (`adaptation-x86-64/os/tools/phorepoc-x86/`)

**Build** (`ekern/make_ekern.sh` 305, driven by `recipes/kernel.sh`):
1. neutral nkernsmp plus the x64smp backend (`-mx32`);
2. ekern census `LINK=1 MM=flexible`, then the x64ekern backend;
3. boot stub, vectors and drivers;
4. `ld -m elf32_x86_64` at EKA2's native addresses (`ekern/ekern.lds`);
5. a GRUB ISO.

Include order: `-I port/x64smp … -I port/x64mm … -I port`, plus `-include core/os/toolchain/x32/port_prelude.h`.

| x64 file | lines | What it does | KHS counterpart | Kind |
|---|---|---|---|---|
| `port/x64smp/nk_plat.h` | 206 | 64-bit register sets, `EXC_TRAP_CTX_SZ` 10→16 | `include/nkernsmp/x86/nk_plat.h` | shadow header |
| `port/x64smp/ncern.h` | 44 | VIB, AP boot info | `include/nkernsmp/x86/ncern.h` | shadow header |
| `port/x64smp/x64s_ncsched.cpp` | 1007 | **Backend surface**: spinlocks, IPIs, Lock/Unlock, Reschedule, `NThread::Create`, tied events, NFastSemaphore, TDfc state changes, NIrq/NIrqHandler | `nkernsmp/x86/{ncsched,ncthrd,ncutilf,ncglob}` | new (C++) |
| `port/x64smp/x64s_ncutils.cpp` | 151 | Interrupt enable, CurrentCpu, SubScheduler, Timestamp, DoIdle | `nkernsmp/x86/ncutils`, `nccpu` | new |
| `port/x64_ctxsw.S` | 112 | `__phore_switch`, a stack swap | context switch in `ncsched.cia` | new |
| `core/os/toolchain/x32/x64smp/x64s_atomics.cpp` | 138 | `__e32_atomic_*` on GCC builtins | `common/x86/atomics.cia` | new |
| `port/x64ekern/xe_kernel.cpp` | 361 | umemget/put + range check, TExcTrap, EpocThreadFunction, EnterUser, InvalidFastExec, PreprocessHandler | `kernel/x86/*.cia`, `klib/x86/cumem.cia` | new |
| `port/x64ekern/xe_nkern.cpp` | 230 | `NKern::Init0`, timeslice, user-mode callbacks, BTrace stubs | nkernsmp/x86 pieces | new |
| `port/x64ekern/xe_mmu.cpp` | 157 | TLB invalidates, address-space switch, DoProcessSwitch | `memmodel/.../x86/{xmmu,xsched}.cia` | new |
| `port/x64mm/mmboot.h` | 170 | **Same 32-bit linear map**, 8-byte PTEs, `KChunkShift` 21 | `.../flexible/x86/mmboot.h` | shadow header |
| `port/x64mm/mmtypes.h` | 14 | `TPde`/`TPte` = `TUint64` | `.../flexible/mmtypes.h` | shadow header |
| `port/x64mm/xmmu.cpp` | 779 | 3 deltas marked `PHOREPOC x64:` | `.../mmu/x86/xmmu.cpp` | marked-delta copy |
| `port/x64mm/{mprocess,maddressspace,pcodeseg}.cpp` | 1164/407/419 | EXE-data pinning (x86 RIP reach; **not needed on ARM**), bug fix | generic memmodel | marked-delta copy |
| `boot.S` + `ekern/xboot.cpp` | 151+669 | Boot → C++ bootstrap that builds MM tables, super page and SPageInfo, then the kernel entry | `kernel/x86/boot*.asm` (3.8k) | full rewrite |
| `ekern/xk_vectors.S` + `xk_irq.cpp` | 86+479 | Trap stubs; **exec gate in C++** (`xk_irq.cpp:161-306`), preemption on IRQ exit | `nkernsmp/x86/vectors.*` | new |
| `ekern/xk_entry.cpp` | 565 | Kernel entry, minimal static variant | `kernel/x86/k_entry` + variant | new |
| `ekern/xk_smp.cpp` + `xk_aptramp.S` | 128+93 | `NKern::BootAP` | `nkernsmp/x86/nccpu.cpp` | new |
| `ekern/xk_interrupt.cpp/.h` | 162 | `Interrupt::Bind` over the unmodified ncirq.cpp | variant | new |
| `port/ekern_census_x32.sh` | 142 | Compile every TU for the new ABI and report the undefined symbols = backend still to write | — | tooling |

## 2. Arch inventory in kernelhwsrv (ARM, SMP + flexible MM)

### 2A. Nanokernel / SMP: `nkernsmp/arm` (10.6k lines: 2.9k C++, 7.8k `.cia`)

The neutral `nkernsmp/*.cpp` (9.7k) + `nkern/nklib.cpp` are reused.

| ARM source | lines | arm64 action | notes |
|---|---|---|---|
| `ncsched.cia` | 980 (370 asm) | new (C++ + ~100 asm) | Reschedule, context switch, TPIDRURO/URW → TPIDRRO_EL0/TPIDR_EL0, VFP, IPI via GICD_SGIR → ICC_SGI1R_EL1 |
| `ncsched.cpp` | 220 | adapt | |
| `ncthrd.cia` | 1809 (779) | new / generic | Drop `__FAST_SEM_/__FAST_MUTEX_/__NTHREAD_WAITSTATE_MACHINE_CODED__` (`nk_plat.h:32-38`) |
| `ncthrd.cpp` | 1146 | adapt | Initial frame, Get/SetUserContext: keep ARM register numbering for AArch32 users |
| `ncutilf.cia` | 1750 (883) | new (C++ `__atomic`) | TDfc state machine, NIrq fast paths, spinlocks |
| `ncutils.cia` / `.cpp` | 1089 / 698 | new/generic/defer / adapt | TPriList (generic), BTrace (stub), Init0, DoIdle |
| `nctimer.cia` | 628 | generic | `__MSTIM_MACHINE_CODED__` off in SMP |
| `ncirq.cpp` / `.cia` | 480 / 240 | adapt / new | GIC driver → GICv3 |
| `nccpu.cpp` / `.cia` | 133 / 47 | new | BootAP → PSCI CPU_ON |
| `vectors.cia` | 1020 (559) | new | see 2B |
| `nk_entry.cia` | 148 | new (small) | `_E32Startup` for nkernsa |
| `include/nkernsmp/arm/{nk_plat.h,entry.h,ncern.h}` | 345/278/143 | new/new/adapt | model on `x64smp/nk_plat.h` |
| `common/arm/atomics.cia` + headers | 540 + 2.2k | new (~150 lines on builtins) | |
| `include/cpudefs.h`, `nkern/nk_cpu.h` | 663/882 | adapt | Keep `__CPU_ARM` semantics for user-visible types (TArmRegSet, TArmExcInfo are ABI) — **GUESS** |

### 2B. Exception vectors and the exec (SWI) path

| ARM source | lines | arm64 action | notes |
|---|---|---|---|
| `nkernsmp/arm/vectors.cia` | 1020 | **new**: VBAR_EL1 table (EL1h; lower-EL AArch32 sync/IRQ/FIQ/SError) + C++ dispatcher | `__ArmVectorSwi` 132-271 = fast/slow dispatch, system lock, extra args, preprocess, callbacks. Template: `xk_irq.cpp:161-306` |
| `kernel/arm/cexec.cia` | 925 | new (C++) | Fast execs, **`FastAtomic*`/`SlowAtomic*`** (the ARMv5 user side does atomics through execs), InvalidFastExec, PreprocessHandler |
| `kernel/execs.txt` + `genexec.pl` | 2483 | **reuse** | Generates the exec enum, user stubs and kernel tables |
| `kernel/arm/ckernel.cpp` / `.cia` | 507 / 609 | adapt / new | `Exc::Dispatch`, `PushExcInfoOnUserStack` (user frame is ABI), TExcTrap |
| `include/kernel/arm/arm.h`, `arm_types.h` | 542 / 264 | adapt | keep ARM register layouts |

### 2C. Memory model (flexible)

| ARM source | lines | arm64 action | notes |
|---|---|---|---|
| `memmodel/epoc/flexible/mmu/arm/xmmu.cpp` | 1106 | adapt (marked-delta) | Short-descriptor attrs → VMSAv8; IPC `Alias` uses **domains**, which VMSAv8-64 lacks: move `KIPCAlias` into kernel space as x64 did |
| `.../mmu/arm/xmmu.h` / `.cia` | 830 / 118 | adapt / new | PTE bits, TLBI/cache inlines, TTBCR, DACR |
| `memmodel/epoc/flexible/arm/*` | 828 | new asm / reuse C++ | DoProcessSwitch (TTBR0 + ASID), RestoreAddressSpace |
| `include/.../flexible/arm/mmboot.h` | 240 | **adapt, as `x64mm/mmboot.h`** | Keep the 32-bit linear map. 4K granule + T0SZ=32 has the same geometry as x86 long mode under x32 |
| generic `memmodel/.../mmu/*` + `mmubase/*` | 43.8k | reuse | x64 compiled them unmodified, except 2 copies |
| `kernel/arm/cache_maintenance*.{cpp,cia}`, `cache.cpp` | 2.2k | new asm / adapt C++ | v7 uses set/way loops. Under a hypervisor, use VA-to-PoC operations instead |

### 2D. Kernel arch code (`kernel/arm`, 14k lines)

| ARM source | lines | arm64 action | notes |
|---|---|---|---|
| `ckernel.cia` | 609 | new | `EpocThreadFunction` (first entry to user), traps, VFP save, IsMagicAtomic64 |
| `cutils.cia` | 1525 | new / generic | KPrintf, NanoWait, KUSafeInc/Dec, RequestComplete, pagecpy |
| `cipc.cia` / `.cpp` | 437 / 103 | generic / new | `__MESSAGE_MACHINE_CODED__` off |
| `csched.cia` | 163 | new (C++) | SafeRead/SafeWrite |
| `klib/arm/cumem.cia` | 684 | **new**: umemget/put with **LDTR/STTR** + fault fixup | |
| `klib/arm/{cbma,ckdes8}.cia`, `common/arm/{cmem,cdes8,cdes16,carray,cgcchelp}.cia` | ~6.6k | generic | as x64 |
| `vfp.cia` / `.cpp` | 146 / 177 | new / adapt | AArch32 VFP = V0–V15 + FPSCR → FPSR/FPCR |
| `cinit.cpp`, `cglobals.cpp`, `byte_pair.cia`, `*_entry.*`, monitors | small | adapt / generic / defer | |

### 2E. Bootstrap
- **Replace:** `kernel/arm/bootmain.s` / `bootcpu.s` / `bootutils.s` (5.2k lines armasm) and `include/kernel/arm/boot*.inc`. x64 did this with `boot.S` (151) + `xboot.cpp` (669).
- **What the bootstrap must leave behind:** ROM header, super page and CPU pages, RAM/ROM bank lists, page tables per mmboot.h, SPageInfo array, initial stack. Then it calls `entry(romHdr, superPage)`.
- **Board table references:** `bsptemplate/.../template_variant/bootstrap/template.s` and `adaptation-a64/.../a64/bootstrap/a64.s` (762).

### 2F. GIC and timer
- **In the nanokernel:**
  - `ncirq.cpp` (ArmGic, `NIrq::Hw*`);
  - `include/nkernsmp/arm/arm_gic.h` (GICv1/v2 MMIO), `arm_scu.h`, `arm_tmr.h` (A9 private timer);
  - ack/EOI asm in `entry.h`, `ncsched.cia`, `ncutils.cia`.
- **GICv3 changes:**
  - CPU interface → `ICC_IAR1/EOIR1/PMR/IGRPEN1/SRE_EL1`;
  - IPIs → `ICC_SGI1R_EL1`;
  - SGI/PPI config → per-CPU GICR;
  - SPI routing → `GICD_IROUTER`.
- **Variant:** system tick, `Interrupt::Bind`, timestamp. Phorepoc's QEMU-virt variant (`adaptation-a64/os/src/phorepoc-arm/virt/specific/interrupts.cpp`, `assp.cpp`) is GICv2 with the tick on CNTP PPI 30.
- **Generic timer the Phorepoc way:** `nkernsmp-gt/arm_tmr.h` (CNTV proxies; timeslice on PPI 27), `variant_timestamp.h`, `nkernsmp_gt_patch.py`. For arm64, write these directly as `CNTV_*_EL0` / `CNTP_*_EL0` code.

## 3. User/kernel boundary (must keep working with AArch32 EL0)

**User exec stubs:**
- `include/u32exec.h:140-190`: `swi n; bx lr`, with `EXECUTIVE_FAST` = `0x00800000`.
- Generated `exec_user.h` (copy in `core/os/toolchain/generated/`).
- `euser/epoc/arm/uc_exec.cia`: extra arguments in r4–r8.

**Kernel dispatch** (`vectors.cia:132-271`):
- Save r0–r14_usr into `SThreadExcStack`; `ldr r12,[lr,#-4]` reads the opcode; bit 23 selects fast vs slow.
- **Fast:** interrupts off, `iFastExecTable`. Exec 0 = WaitForAnyRequest. One argument in r0, result in r0, everything else preserved.
- **Slow:** interrupts on, `iSlowExecTable` {flags, fn}. Arguments r0–r3, result r0.
- Slow-exec flags: Claim 0x80000000, Release 0x40000000, Preprocess 0x20000000, ExtraArgMask 0x1C000000 (r2 := pointer to the saved r4..).

**AArch64 mapping:**
- AArch32 r0–r14_usr → x0–x14; PC → ELR_EL1; CPSR → SPSR_EL1.
- EC 0x11 = AArch32 SVC.
- Read the opcode at ELR-4 with LDTR; ESR ISS only holds imm16 (**GUESS**, check the ARM ARM).
- Thumb-state SVC is invalid (the 2010 kernel only handles ARM-state SWI).

**Thread start** (`kernel/arm/ckernel.cia:29-140`):
- `SThreadCreateInfo` is copied to the top of the user stack; r13_usr points at it; r4 holds the entry reason; the thread jumps to `iEntryPtVeneer` or `iReentryPoint`.
- Optionally `TLocalThreadData` + TPIDRURW (→ TPIDR_EL0).

**User exception re-entry:** `PushExcInfoOnUserStack` writes an 84-byte frame {ExcType, code, FAR, FSR, CPSR, r0–r15}, which `uc_exe.cia:40-125` unwinds. **This layout is ABI.**

**Address space** (`include/memmodel/epoc/flexible/arm/mmboot.h`):

| Region | Address |
|---|---|
| Local data | 0x00400000…0x7F000000 |
| ROM / global | 0x80000000 |
| User limit | 0x90000000 |
| Kernel | 0x90000000–0xEFFFFFFF |
| Super page | 0xF0000000+ |

- ROM code and data sit at rombuild-assigned absolute addresses.
- No vDSO or user-shared page (**GUESS**, confident).
- So the ILP32 kernel lives in the same 4 GiB TTBR0 space (T0SZ=32, no TTBR1 walks). Kernel pages are EL1-only and global; process pages are nG with ASID. This is the x64 shape.

**ARMv5TE user side** (Phorepoc `core/registry/components.py:2782-2789`):
- No LDREX/STREX, so user atomics go through execs.
- The user side uses **SWP** (RFastLock, critical sections), which is UNDEF on ARMv8, so it must be emulated. Port from `ekern_seam.cpp:1162-1333`.
- Also emulate misaligned LDRD/LDM (1220-1333) and VFP short vectors (1335-1603).
- `ARM_DMB` uses CP15 barriers, which needs `SCTLR_EL1.CP15BEN`.

## 4. How x86-64 handled 32-bit pointers
- **x32 for both kernel and user:** `TLinAddr`/`TUint32` stay 32-bit; exec arguments are zero-extended.
- **User-pointer checks in software** (no segment limits): `X64_UserRangeFault` → `Exc::Dispatch`.
- **Small adjustments:** `EXC_TRAP_CTX_SZ` 10→16; prelude: `VA_LIST` = builtin, `_FOFF` returns `TInt`.
- **ROM window** grown to 512 MB (`KUserMemoryLimit` 0xA0000000; rombuild must agree).
- **Census scripts:**
  - compile every unmodified TU for the new ABI, never stopping on errors;
  - report OK/FAIL counts and error classes;
  - `LINK=1` lists the undefined symbols = the backend still to write;
  - `ABI=-m64` is an "LP64 canary" counting pointer↔int warnings.
  
  We need an `ekern_census_ilp32.sh` (aarch64 `-mabi=ilp32`).

## 5. nkernsa (standalone nanokernel tests): the first QEMU milestone
- **Location:** `kerneltest/e32test/nkernsa/` (10.1k lines).
- **Tests:** threadbasic, testdfc, fastmutex, fastsem, testipi, tiedevents, rwspinlock, fastbuf, benchmark.
- **Support:** `init.cpp` (KernelMain, ApMainGeneric), `kprintf.cpp`, `tlsf.cpp`. Instructions in `howto.txt`.
- **Built from:** `nkernsmp/nkern_sa.mmp` (`__STANDALONE_NANOKERNEL__`) + `nk_exe.mmp` (`_E32Startup`) + `nktest_lib.mmp`. The NaviEngine glue that tied them together is **not in these repos**.
- **What the port must supply:**
  - the nanokernel backend (2A) and `_E32Startup`;
  - `HwInit0`, `Hw_Init1`, `Hw_InitAPs`, `Hw_Init3`, `StartSystemTimer`, `__timer_period`, `DebugPrint` (PL011);
  - the armutils equivalents (`utils.h:37-65`: cpu idle/id, fast counter, local timer, RequestComplete, `new`);
  - a minimal super page / VIB and AP boot.
- **No memory model needed:** a flat identity map with MMU and caches on is enough.
- **Fix to the 2010 kernel itself (applied by `tools/build-kernel.sh`; the ekern build must carry it too):**
  `NKern::JoinGroup` (`nkernsmp/nkern.cpp`), joining a group that is already ready on this CPU, raised the group's
  priority with `SSChgEntryP` -> `ChangePriority`, which re-adds at the *tail*. The running thread then sat behind
  its equal-priority peers and was switched out at the next reschedule, even while holding a fast mutex
  (fastmutex.cpp DoRWTest `0x138`/`0x438`: protected buffer read half-written). The group now takes the joiner's
  place at the head (`SSRemoveEntry` + `SSAddEntryHead`), as the not-ready path and LeaveGroup already do.
- **Calibration for 2 GHz cores (phone build only, patched copies of the tests):** tiedevents LoopCount 5000;
  fastmutex DoRWTest 4096-word blocks, 10000 reads per case. Both checks were tuned on ~400 MHz ARM11 boards.

## 6. ARMv8 specifics already in adaptation-a64
- **`a53shim/shim.S`** (212, AArch64 EL2 → AArch32 EL1):
  - `HCR_EL2.RW=0`; `CNTHCTL_EL2`=3; CPTR/HSTR no traps; **`CPUECTLR.SMPEN`** before caches and MMU; `SCTLR_EL1`=0x00C50838; PSCI resume record.
  - It needs EL2, which the Pixel doesn't give us (ABL enters EL1 under Qualcomm's hypervisor, so an AArch64 kernel is required). The SMPEN and CNTHCTL lessons still apply.
- **`a64/bootstrap/a64.s`:** PSCI over SMC32 (CPU_ON 0x84000003, SYSTEM_RESET 0x84000009); CPU count from GICD_TYPER.
- **`a64/power/a64_idle.cpp`:** PSCI CPU_OFF / AFFINITY_INFO.
- **`a64/config.inc`:** SCTLR.A off (unaligned LDRH from ROM fonts).
- **`ekern_seam.cpp`** (2158): AArch32-user compatibility plus toolchain glue.
- **The ARM kernel is the unmodified 2010 source plus a seam:** `nkernsmp_compile_check.sh` uses `-march=armv7-a -D__CPU_CORTEX_A9__ -D__SMP__ -D__CPU_ARM_HAS_GIC -D__CPU_ARM_HAS_GENERIC_TIMER -DNK_MAX_IRQS=160`.
- **QEMU virt facts:**
  - `virt/specific/syborg.h:57-78` lists GIC, PL011, PL031, PL061 and virtio.
  - PPI 30 = phys timer, 27 = virt timer; CNTFRQ is 62.5 MHz.
  - The PSCI conduit (HVC/SMC) comes from the DTB `/psci` node.

## 7. Size estimate: nanokernel + exceptions + bootstrap on QEMU virt (GICv3)

**Reused unmodified:** nkernsmp neutral (9.7k) + nkernsa tests (~8.8k).

**x64 actuals for the same scope (≈ 3.5k lines):**

| Piece | Lines |
|---|---|
| Backend | 1,376 |
| Context switch | 112 |
| Atomics | 138 |
| Boot | 820 |
| Vectors + irq | 565 |
| SMP | 221 |
| Interrupt | 162 |
| Linker script | 102 |

**arm64 estimate (GUESS, ≈ 4–5k new lines):**

| Piece | Lines |
|---|---|
| Arch headers | 500 |
| Scheduler/DFC/IRQ C++ | 1,200 |
| Context switch + thread start asm | 150 |
| Atomics + spinlocks | 200 |
| Vectors asm | 300 |
| Trap/IRQ C++ | 400 |
| GICv3 | 400 |
| Generic timer | 200 |
| PSCI AP boot | 150 |
| Boot (MMU/caches, super page stub) | 500 |
| nkernsa glue | 500 |

**Later milestones (GUESS):** (the full staged plan beyond this, to a daily phone with a Rust UI, is in `roadmap.md`)
- ekern arch (exec gate, LDTR/STTR umem, ExcTrap, EpocThreadFunction, exec atomics): ~1.5–2.5k.
- VMSAv8 MMU delta + IPC alias redesign + ASID: ~1.5k touched.
- AArch32-EL0 compat (SWP, alignment, VFP vectors): ~450, ported from ekern_seam.

## 8. Risks and unverified points
- **ILP32 toolchain:** see `sources.md` (GCC deprecated but present; clang has none). The fallback is an LP64 census to measure the damage.
- **Not checked against the ARM ARM:** ESR ISS width for AArch32 SVC, CPACR_EL1.FPEN for AArch32 EL0.
- **Not in these repos:** the NaviEngine nktest glue, Phorepoc `virt/bootstrap`, and the pdk tools (`symcc`, `rombuild.py`). The pdk is now checked out on ZimaOS.
- **Not read line by line:** `ncthrd.cpp`, `xmmu.cpp` and the boot `.s` bodies. Their actions come from function lists and grep.
