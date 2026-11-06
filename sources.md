# Sources for the EKA2 → AArch64 (ILP32) port

Researched 2026-11-05 with `gh api`, raw.githubusercontent.com, and web search/fetch.
Dates are **last-commit dates** from the commits API. GitHub's `pushed_at` can be later (kernelhwsrv says 2021, but its last commit is 2010).
"Unverified" means I could not confirm it directly.

## Licensing at a glance

- **SymbianSource `oss.*` repos:** GitHub detects no license file, but every source header I sampled says *Eclipse Public License v1.0*:
  - `nkernsmp/arm/ncsched.cia`
  - `kernel/execs.txt`
  - `elf2e32.cpp`
  - the SHAI headers
- **compilationtoolchains:** its last commit is "Change SFL to EPL", so some packages once carried the Symbian Foundation License (SFL). Check headers before reusing anything outside kernelhwsrv and the tools.
- **Phorepoc:** our own code is Apache-2.0. Symbian files we change become EPL-2.0 (with GPL-2.0-or-later as a Secondary License). Unchanged Symbian files stay EPL-1.0.

## Our forks (neosymbian)

Everything the build fetches is forked into https://github.com/neosymbian. Nothing is pushed back upstream.

- **The 99 SymbianSource packages** pinned in Phorepoc `core/sources.lock` (126 entries over `master` and
  `BRANCH_RCL_3`) are forked from **SymbianSource**, the root of the fork network, not from Phorepoc's identical mirrors.
- **Phorepoc `core` and `pdk`** are forked too. Our `core` fork's `fetch.sh` defaults `SOURCES_URL` to neosymbian.
- **Also forked:** Phorepoc `adaptation-a64` and `adaptation-x86-64`, as read-only references. `symbian-2010` and
  `qemu-syborg` are forked for the Rust stream.
- **Not forked** until a stage needs them: `toolchain` (its container images are published separately) and the layers
  (`tls`, `qt-symbian`, …).
- **Local layout:** every repo we work in is cloned side by side in one workspace folder, `NeoSymbian/`:
  `symbian-pixel`, `oss.FCL.sf.os.kernelhwsrv`, `core`, `pdk`, `symbian-2010`, `e32-rs`, `neoui`, `adaptation-*`.
  The workspace's `CLAUDE.md` describes them.
- **Branch rule:** upstream branches stay untouched; our work is on `main`, the default branch.
  - `oss.FCL.sf.os.kernelhwsrv` `main` starts at `0c32086` (tag `201043_12`), the commit `sources.lock` pins.
  - In-place kernel edits are commits there. After each one, `core/sources.lock` is re-pinned to it.
  - New code goes into new repos, starting with `symbian-pixel`.

## Top 10 sources (ranked)

### 1. SymbianSource/oss.FCL.sf.os.kernelhwsrv (the EKA2 kernel itself)

**URL:** https://github.com/SymbianSource/oss.FCL.sf.os.kernelhwsrv

**What it is.** The final Symbian Foundation kernel and hardware services package.
- `master` was last committed 2010-11-02 (tag `201043_12`, `kernel/eka/release.txt` 2.00.4016).
- `BRANCH_RCL_3` (2010-12-16, "201050") is the S^3 release line.
- `BRANCH_GCC_SURGE` (2010-11-25) is 99 commits ahead of master with GCC fixes.

The whole tree is about 6k files; the recursive tree API returns it untruncated.

**Paths that matter.**
- **SMP nanokernel** (`kernel/eka/nkernsmp/`):
  - generic code: `nkern.cpp`, `sched.cpp`, `dfcs.cpp`, `nk_irq.cpp`, `nk_timer.cpp`, `nk_bal.cpp`
  - per-arch dirs: `arm/` and `x86/`, each with `nccpu`, `ncirq`, `ncsched`, `ncthrd`, `ncutils`, `nk_entry`, `vectors` (`.cia`/`.cpp`)
  - `nkern_sa.mmp` builds the standalone nanokernel.
- **Arch headers:**
  - `kernel/eka/include/nkernsmp/arm/`: `nk_plat.h`, `entry.h`, `ncern.h`, `arm_gic.h`, `arm_scu.h`, `arm_tmr.h`
  - `kernel/eka/include/nkernsmp/x86/`: `apic.h`, `nk_plat.h`, `ncern.h`
  - `kernel/eka/include/kernel/arm/`: `arm.h`, `arm_types.h`, `assp.h`, `bootdefs.h`, `bootcpu.inc`, `bootmacro.inc`, `bootstrap.lnk`, `vfpsupport.h`
  - `kernel/eka/include/cpudefs.h`: the CPU feature macros
- **Flexible memory model:**
  - `kernel/eka/memmodel/epoc/flexible/` holds the generic `mmu/*.cpp`
  - arch code: `mmu/arm/xmmu.{cpp,cia,h}`, plus `arm/x*.cpp|cia` (`xinit`, `xipc`, `xkernel`, `xsched`)
  - x86 siblings: `mmu/x86/` and `x86/`
- **Kernel, arch-specific part.** `kernel/eka/kernel/arm/` holds:
  - `cexec.cia/.cpp`, `ckernel`, `cipc`, `csched.cia`, `vfp.cia/.cpp`
  - `cache_maintenance*.cia`, including `cache_maintenancev7.cia`
  - the entry points `*_entry.cia`
  - the generic bootstrap in RVCT armasm syntax: `bootmain.s`, `bootcpu.s`, `bootutils.s`
- **x86 template for a new arch:** `kernel/eka/kernel/x86/`, `nkern/x86/`, `nkernsmp/x86/` and `memmodel/epoc/flexible/{x86,mmu/x86}`. x86 is the only non-ARM hardware arch in the tree, so it shows exactly which files a new arch must supply.
- **Exec calls:**
  - `kernel/eka/kernel/execs.txt` (337 `name` entries) is the master table.
  - `kernel/eka/kernel/genexec.pl` turns it into `u32exec.h` and the kernel tables.
  - `kernel/eka/include/u32exec.h` defines `EXECUTIVE_FAST 0x00800000` and `EXECUTIVE_SLOW 0`.
  - User stubs: `kernel/eka/euser/epoc/arm/uc_exec.cia`, which issues `swi <n|flag>`.
  - Kernel handlers: `kernel/eka/kernel/sexec.cpp` and `kernel/arm/cexec.*`.
  - The SVC handler in `nkernsmp/arm/vectors.cia` reads the opcode with `ldr r12,[lr,#-4]`.
- **Bring-up tests:**
  - `kerneltest/e32test/nkernsa/`: the standalone nanokernel test suite (threads, fast mutex/semaphore, DFCs, IPIs, tied events, rwspinlock, timers, benchmarks).
  - Arch hooks are tiny: `arm/armutils.*` and `x86/x86utils.*`.
  - `howto.txt` says the suite runs on the single memory model and outputs only through the bootstrap debug port.
  - After that comes `kerneltest/e32test/` (about 2.5k files) and `f32test`.
- **Templates and doc sources:**
  - `bsptemplate/asspandvariant/` (with `template_variant/bootstrap/template.s`) is the official ASSP/variant porting template.
  - `kernelhwsrv_info/doc_pub/` holds 41 doc files (not inspected).

**Why it matters.** This is the code we port. Its ARM assumptions are explicit:
- `.cia` files are C++ with inline-asm naked functions: 159 in the tree, 77 under `arm/`.
- The A32 assembly in them uses CP15 `mcr`/`mrc` and `swi`.
- Feature macros include `__CPU_ARMV6`, `__CPU_ARMV7`, `__CPU_ARM11MP__`, `__CPU_CORTEX_A9__`, `__CPU_HAS_VFP` and `__CPU_ARM_HAS_LDREX_STREX`.
- The SMP nanokernel knows only the ARM11MPCore and Cortex-A9 private timer, SCU and GICv1 (memory-mapped CPU interface).

Every `arm/*.cia` must be rewritten as A64. The generic `.cpp` (nkernsmp core, flexible mmu core) should mostly carry over under ILP32.

**Note on the SVC path.** On an AArch32 SVC trapped to AArch64 EL1, ESR_EL1 reports only `imm16`, so bit 23 (the fast/slow flag) is lost. Keep the original trick of reading the instruction at `ELR_EL1-4`; Thumb `svc` has an 8-bit immediate, so check that too.

**License:** EPL-1.0 in file headers.

### 2. Phorepoc/adaptation-x86-64 (the closest precedent: EKA2 on a 64-bit CPU with 32-bit pointers)

**URL:** https://github.com/Phorepoc/adaptation-x86-64 (active, last push 2026-11-05)

**Paths that matter.**
- `os/tools/phorepoc-x86/port/`:
  - `x64smp/` (SMP nanokernel arch layer: `nk_plat.h`, `ncern.h`, `x64s_ncsched.cpp`, `x64s_ncutils.cpp`, `relax_size_asserts.h`)
  - `x64mm/` (flexible memory model: `xmmu.cpp`, `mmtypes.h`, `mmboot.h`, `maddressspace.cpp`, `mprocess.cpp`, `pcodeseg.cpp`)
  - `x64ekern/`
  - `x64_ctxsw.S`, `x64_atomics.cpp`
  - test and probe scripts: `build_nkernsmp_probe.sh`, `build_sched_test.sh`, `sched_test.cpp`, `ctxsw_test.c`, `ekern_census_x32.sh`
- `os/tools/phorepoc-x86/ekern/`: `xboot.cpp`, `xk_vectors.S`, `xk_smp.cpp`, `xk_aptramp.S`, `ekern.lds`, `make_ekern.sh`
- `os/tools/phorepoc-x86/boot.S`

**Why it matters.** It is the same design as ours: a 64-bit kernel on unmodified 2010 sources, 32-bit pointers, 64-bit page tables. It shows:
- which generic files needed patches;
- how the `.cia` files were replaced by `.S` and C++;
- how size static-asserts were relaxed;
- how ROM and ELF linking were done without RVCT.

**License:** Apache-2.0 for Phorepoc code; changed Symbian files are EPL-2.0.

### 3. Phorepoc/adaptation-a64 (32-bit ARM EKA2 on ARMv8 cores, built with GCC)

**URL:** https://github.com/Phorepoc/adaptation-a64

**Paths that matter.**
- `os/src/phorepoc-arm/a53shim/shim.S`: an AArch64 EL2 stub that ERETs into the AArch32 SVC-mode bootstrap. Secondary cores are started through PSCI CPU_ON.
- `os/src/phorepoc-arm/a64/bootstrap/a64.{s,inc}`: the board bootstrap.
- `os/src/phorepoc-arm/nkernsmp-gt/{arm_tmr.h,variant_timestamp.h}` and `os/tools/kernel/nkernsmp_gt_patch.py`: patches the SMP nanokernel from the A9 private timer to the **ARM generic timer**. The virtual timer PPI 27 becomes TIMESLICE_VECTOR, CNTV_TVAL is used, and the patch touches 3 sites.
- `os/tools/armasm2gas/build_bootstrap.sh` (plus `h2inc.py`, referenced): translates the RVCT armasm bootstrap to GAS.
- `os/tools/kernel/`:
  - `link_ekern.sh`, `ekern.lds`, `ekern_seam.cpp`
  - `nkern_compile_check.sh`, `nkernsmp_compile_check.sh`
  - `gcc2_aliases.py`, `build_ekern_rom.sh`
  - `README.md`: these scripts are not yet run by CI.

**Why it matters.**
- It has the only existing generic-timer and PSCI adaptations of EKA2.
- It shows the 2010 SMP nanokernel compiles with modern GCC (Arm GNU 14.2).
- It is the reference for our AArch32 user side.
- Its GIC is still the GICv2-class GIC-400; GICv3 is not covered.

**License:** Apache-2.0 / EPL-2.0 (changed files) / EPL-1.0.

### 4. Phorepoc/core, pdk and toolchain (build system, pinned sources, x32 user runtime)

**URLs:**
- https://github.com/Phorepoc/core
- https://github.com/Phorepoc/pdk
- https://github.com/Phorepoc/toolchain

**Paths that matter.**
- **core:**
  - `sources.lock` pins kernelhwsrv at `0c32086505…`, i.e. SymbianSource master.
  - `fetch.sh` downloads the pinned sources.
  - `os/toolchain/shims/` holds patched Symbian files.
  - `os/toolchain/x32/` is the x32 user runtime.
  - `registry/components.py` says how each component is built from its `.mmp`.
- **toolchain:** Docker images with GCC 13 x32, Arm GNU 14.2, QEMU, and rcomp/mifconv built from 2010 source.
- **pdk:** the `phe` CLI and `docs/layering.md`.

**Why it matters.** It is the GCC/Linux build path for the unmodified ARM user side, and the layering model a new `adaptation-a64v8`/board repo would plug into.

**License:**
- core and toolchain: EPL-1.0 / Apache-2.0 (core is mixed, as in the README).
- pdk: Apache-2.0.

### 5. SymbianSource/oss.FCL.sf.adapt.NECNaviengine (ARM11 MPCore SMP reference BSP)

**URL:** https://github.com/SymbianSource/oss.FCL.sf.adapt.NECNaviengine (last commit 2010-10-12, 269 files)

**Paths that matter.**
- `navienginebsp/naviengine_assp/interrupts.{cpp,cia}`: the GIC/IPI dispatch.
- `navienginebsp/ne1_tb/bootstrap/ne1_tb.s` and `miniboot.s`.
- `navienginebsp/ne1_tb/config.inc`.
- **The NKern standalone test platform:**
  - `navienginebsp/ne1_tb/nktest/{hw_init.cpp,hw_init.cia,interrupts.cpp,nktest.mmp}`
  - `navienginebsp/ne1_tb/single/{bld.inf,config.inc,nktest.iby,variant.mmh}`
- `navienginebsp/naviengine_assp/` (UART), `navienginebsp/ne1_tb/rom/*.iby|oby`
- `navienginebspflexible/`, `navienginebootldr/`

**Why it matters.**
- It is the only SMP board in the release, so it is the reference for SMP variant hooks, IPIs, per-CPU timers and secondary-CPU start.
- `ne1_tb/nktest` is exactly what we must reimplement for `qemu virt` to run `e32test/nkernsa`: hw_init, interrupt hookup, debug UART.
- Its GIC is the ARM11MPCore interrupt distributor, a GICv1 predecessor. The register-level code is not reusable for GICv3, but the dispatch structure is.

**License:** EPL-1.0 (headers; GitHub reports none).

### 6. SymbianSource/oss.FCL.sf.adapt.Qemu (Syborg) and the Phorepoc symbian-2010 / qemu-syborg repos

**URLs:**
- https://github.com/SymbianSource/oss.FCL.sf.adapt.Qemu (last commit 2010-10-29)
- https://github.com/Phorepoc/symbian-2010
- https://github.com/Phorepoc/qemu-syborg

**Paths that matter.**
- `baseport/syborg/bootstrap/syborg.{s,inc}`: a minimal, simple bootstrap PSL (platform-specific layer).
- `baseport/syborg/{specific,serial,fb,rom,estart,hal}`.
- `tools/e32test-driver/` (`qemuruntest.py`, `runtests.py`, `rtest.py`, `rtestreport.py`): automated e32test runs on QEMU with result parsing.
- `tools/elf4rom/`: turns a ROM into an ELF for gdb.
- `docs/wiki/*.doc`, including "Flexible Memory Model.doc", "Armv7.doc", "SVP E32-F32 Testing.doc" and "Stop-mode Debugging.doc".
- `symbian-qemu-0.9.1-12/`

**Why it matters.**
- Syborg is the simplest virtual platform, the closest analogue to `-M virt`.
- The e32test driver can be reused nearly as-is for CI.

**License:** EPL-1.0 for Symbian parts; QEMU and the driver are GPL/LGPL (`tools/e32test-driver/COPYING*`).

### 7. SymbianSource/oss.FCL.sftools.depl.docscontent (the Base Porting Guide in DITA)

**URL:** https://github.com/SymbianSource/oss.FCL.sftools.depl.docscontent (last commit 2010-10-15, "Initial contribution of the Adaptation Documentation")

**Paths that matter.** `Adaptation/` holds 708 files. The map is `GUID-B5657E8C-770C-4322-88B2-057AAEF62E95.ditamap`. Key topics:
- `GUID-0C84FD76-87B2-4AD1-B23A-2C5C8668BC4C.dita`: "Base Porting Guide"
- `GUID-984C2A0D-…`: "ASSP/Variant Architecture"
- `GUID-6060F138-…`: "Baseport Template Overview"
- `GUID-57989FF8-…`: "Baseport Template Implementation Guide"
- `GUID-5EB03086-…`: bootstrap "Port Implementation Tutorial"
- `GUID-9595FD6F-…`: "Boot Table"
- `GUID-306A0B41-…`: "Platform-Specific Functions"
- `GUID-0DC908A1-…`: "Automatic Translation of Header Files From C++" (h2inc)
- `GUID-42F8FA5A-…`: "Personality Layer Design"
- Four topics mention SMP.

`Symbian3/PDK/Source/` duplicates many of these.

**Why it matters.** It is the authoritative documentation of the bootstrap, ASSP and variant contracts (boot table, superpage, `Asic` interface) we must re-implement. Find topics with code search:

```
gh api search/code -f q='"<term>" repo:SymbianSource/oss.FCL.sftools.depl.docscontent'
```

**License:** EPL-1.0 (per the Foundation; files are DITA without headers, so this is unverified per file).

### 8. "Symbian OS Internals" (Sales et al., Wiley 2005) on the akaWolf wiki

**URL:** https://akawolf.org/wiki/index.php/Symbian_OS_Internals. The table of contents fetches fine (verified), as does chapter 16. Some akawolf pages sit behind Anubis or 403 for curl.

**Paths that matter.** All 18 chapters plus the appendices. Most relevant:
- ch. 2 Hardware
- ch. 3 Threads
- ch. 5 Kernel Services (exec calls)
- ch. 6 Interrupts and Exceptions
- ch. 7 Memory Models
- ch. 16 Boot Processes
- ch. 17 Real Time
- App. 2 E32ImageHeader
- App. 3 TRomImageHeader

**Why it matters.** It is the design rationale behind the code. It covers EKA2 up to 2005 and predates the SMP nanokernel and the flexible memory model; the latter is covered by the Qemu repo's `docs/wiki/Flexible Memory Model.doc`.

**Other copies:**
- The Forum Nokia original is on the Wayback Machine: https://web.archive.org/web/20110121072523/http://wiki.forum.nokia.com/index.php/Symbian_OS_Internals
- https://akawolf.org/mediawiki/index.php/Kernel:Base_Porting_Quick_Start (found via search, returned 403 to curl; unverified content)

**License:** the wiki page says "Reproduced by kind permission of John Wiley & Sons". It is free to read, not an open license.

### 9. SymbianSource/oss.FCL.sftools.dev.build (host build tools: elf2e32, rombuild, raptor, h2inc)

**URL:** https://github.com/SymbianSource/oss.FCL.sftools.dev.build (last commit 2010-12-01)

Also relevant: `oss.FCL.interim.SFTools.LinuxBuild` (2010-12-01), the Linux-host fork of the same tools.

**Paths that matter.**
- `e32tools/elf2e32/{source,group,include}`: ELF to E32Image, used for the unchanged ARM user side.
- `imgtools/romtools/rombuild/`: the ROM image builder, which defines the ROM header and superpage expectations.
- `bintools/elftools/` (`elftran`).
- `sbsv1/abld/e32util/h2inc.pl`.
- `sbsv2/raptor/lib/config/{gcce.xml,arm.xml,gcc_x86.xml}` and `sbsv1/abld/platform/GCCE.mk`.

**Why it matters.**
- elf2e32 and rombuild are needed for the AArch32 user side and the ROM.
- rombuild assumes a 32-bit ARM or x86 kernel image, so we either teach it ELF64 or wrap our kernel (Phorepoc uses its own `rombuild.py` in pdk).
- `oss.FCL.sf.os.buildtools` (2010-07-13) and `oss.FCL.sftools.dev.hostenv.compilationtoolchains` (`gcce-3.4.3` only) add nothing new.

**License:** EPL-1.0 (headers).

### 10. EKA2L1 (HLE Symbian emulator) as an exec-call oracle

**URL:** https://github.com/EKA2L1/EKA2L1 (active, 2026-11-05)

**Paths that matter.**
- `src/emu/kernel/src/svc.cpp` and `src/emu/kernel/include/kernel/svc.h`: exec-call implementations keyed by number, per OS version.
- `src/emu/kernel/include/kernel/{thread,process,chunk,ipc,...}.h`.
- `src/emu/kernel/include/kernel/smp/`.

**Why it matters.** It is a second, independent reading of the exec ABI and of user-visible kernel semantics. It is useful for checking our SVC dispatch against real S60 binaries.

**License:** GPL-3.0. Use it as a reference only; do not copy into EPL/Apache code.

## Other repos checked (lower value)

- **`oss.FCL.sf.adapt.beagleboard`** (2010-11-29): an OMAP3/Cortex-A8 unicore BSP.
  - Contents: `omap3530/beagleboard/bootstrap/{beagle.s,config.inc}`, `omap3530/assp/`, and `omap3530/omap3530_drivers/{uart,prcm,gpio,i2c}`.
  - Useful only as a second ARMv7 bootstrap and cache example; it has no SMP.
- **`oss.FCL.sf.os.boardsupport`** (2010-10-27): `emulator/` (WINSCW) plus `haitest/bspsvs`, BSP conformance tests run through TestExecute.
  - The tests may be useful later; the rest does not matter for the kernel.
- **`oss.FCL.sf.adapt.stubs`** (2010-10-25): user-side middleware stubs (audio, DRM, WLAN init, power-save display). Relevant later for booting the UI without real drivers; no kernel content.
- **`oss.API_REF.SHAI`** (2010-10-05): small device-driver chipset headers, not kernel porting docs:
  - `ASSP Variant/{asicinfo,cpupage,gptimer}_chipset_api.h`
  - `Idle Timers`, `Power Management`, `Boot Reason`, `CPS Kernel`
- **`oss.API_REF.Public_API`** (2010-03-31, default branch `Symbian3`): exported `epoc32/include` headers. Useful as an SDK include tree for the user side, not for the kernel.
- **Phorepoc forks:** the `oss.FCL.*` forks under github.com/Phorepoc are unmodified mirrors (same `pushed_at`/size as upstream). Phorepoc's changes live in `core/os/toolchain/shims/` and the adaptation repos, not in the forks.
- **cdaffara/symbiandump-\*** (GitHub, 2021 uploads of the Symbian^4 `FCL.single.1054` release):
  - `symbiandump-os1/sf/os/kernelhwsrv` is **older** than SymbianSource master: release.txt 2.00.4006 (27/09/2010) vs 2.00.4016.
  - Key ARM nkernsmp, GIC and flexible-mmu files are byte-identical.
  - It adds `kernel/eka/debug/crashMonitor` and `baseapitest/basesvs`, which SymbianSource lacks.
  - `symbian-pdk40a-utils/epoc32/tools` holds prebuilt host tools (not inspected).
  - Verdict: nothing kernel-critical that SymbianSource lacks.
- **archive.org mirrors:**
  - https://archive.org/details/SymbianOpenSource holds Mercurial bundles of every package (`code_FCL,sf,os,kernelhwsrv.hg.bundle`, …) plus wiki and forum dumps. Use it if you need full hg history or the original wiki.
  - `symbian-open-source-unpacked` is the same content without Mercurial.
- **mrRosset/Symbian-Archive** (https://mrrosset.github.io/Symbian-Archive/): a link hub for SDKs and docs. It points to the akaWolf wiki and hg mirror (https://akawolf.org/oss/) and the archive.org items; no kernel content of its own.
- **katastrophos.net:** `/symbian-dev` is the Belle *app* developer library. Searches found no base-porting, bootstrap or ASSP content there. `/symbian/mirrors` holds SDKs and tools.
- **Yuzixx1/symbian-x86** (2026-10): boots the real nkern and Kern on 32-bit i386 QEMU with GCC (`qemu-port/`). Its README says it is AI-generated ("vibecoded"); treat it as low-trust, but it is another GCC build of `nkern/x86`.

## AArch64 ILP32 toolchain status

| Component | Status | Source |
|---|---|---|
| GCC 14 | `-mabi=ilp32` supported, no warning. aarch64-elf builds the `lp64,ilp32` multilibs by default. Arm GNU Toolchain 14.2 aarch64-none-elf likely ships an ILP32 multilib (**unverified**). | config.gcc history; GCC 15 notes below |
| GCC 15 | **Deprecated**: "support for ILP32 (`-mabi=ilp32`) has been deprecated and will be removed in a future release". `aarch64*-elf` "no longer build the ILP32 multilibs". Using it warns under `-Wdeprecated` (an error with `-Werror`). | https://gcc.gnu.org/gcc-15/changes.html ; https://www.mail-archive.com/gcc-patches@gcc.gnu.org/msg361974.html |
| GCC 16 | Still present. The 16.1 manual says "The 'ilp32' model is deprecated". The GCC 16 changes page makes no AArch64 ILP32 change. | https://gcc.gnu.org/onlinedocs/gcc-16.1.0/gcc/AArch64-Options.html ; https://gcc.gnu.org/gcc-16/changes.html |
| GCC trunk (17 dev, checked 2026-11-05) | `aarch64.opt` still has `String(ilp32)`. `config.gcc` has the elf multilibs commented down to `lp64`. Not removed yet, but removal is announced. | gcc-mirror/gcc master `gcc/config/aarch64/aarch64.opt`, `gcc/config.gcc` |
| binutils | `aarch64_elf32_le_vec` (elf32-littleaarch64) is still in `bfd/config.bfd` on master. No ILP32 mention in gas/ld/bfd/binutils NEWS (2.46 Feb 2026, 2.47 Jul 2026). Not deprecated so far. | sourceware binutils-gdb `bfd/config.bfd` |
| Arm ABI docs | abi-aa issue #369 (closed 2026-09-22): ILP32 removed from the AArch64 ABI documents, which now refer readers to older releases. | https://github.com/ARM-software/abi-aa/issues/369 |
| LLVM/clang | The backend supports `aarch64-*-gnu_ilp32` (D94143, 2021). The clang frontend patch D104931 was never merged; lld has no ILP32. **Not usable upstream.** | https://reviews.llvm.org/D94143 ; https://reviews.llvm.org/D104931 ; https://discourse.llvm.org/t/ilp32-support-with-aarch64/72096 |
| glibc | Never merged upstream; only side branches (arm/ilp32 at 2.30, schwab/ilp32 at 2.33). | GCC deprecation patch thread; https://github.com/ilp32-a64/glibc-ilp32 |
| newlib | `libgloss/aarch64/crt0.S` still has `__ILP32__` paths on master, but GCC 15+ no longer builds ILP32 multilibs, so you must configure `--with-multilib-list=lp64,ilp32` yourself. | sourceware newlib-cygwin `libgloss/aarch64/crt0.S` |
| Community | The **ilp32-a64** org (Oct–Nov 2026) maintains: `gcc-ilp32` (GCC 14.2 + fixes), `llvm-ilp32` (clang 22 patches), `glibc-ilp32` (2.41), `musl-ilp32`, `linux-ilp32` (6.12), `debian-ilp32`, `test-ilp32` (QEMU harness). This is out-of-tree and young; debian-ilp32's compiler packages were pulled 2026-10-28 over an omp.h bug. | https://github.com/ilp32-a64 |

**Implications for us.**
- A freestanding kernel needs only cc1, gas, ld and libgcc, so libc does not matter.
- Pin **GCC 14.x** (no warning) or GCC 15/16 with `-Wno-deprecated`.
- Build libgcc for ILP32 ourselves (`--with-multilib-list=lp64,ilp32`).
- Expect GCC 17 or 18 to drop it.
- **Plan an exit:** keep the kernel buildable as LP64 C with explicit 32-bit handle/pointer types, the way Phorepoc treats x32, or vendor a pinned GCC 14/16 toolchain image.
- ILP32 pointers are zero-extended 32-bit values. All kernel virtual addresses must therefore sit in the low 4 GB, i.e. the TTBR0 range, shared with the AArch32 EL0 address space. That fits Symbian's 32-bit memory map, but it rules out a TTBR1 high-half kernel.

## Gaps (no source provides these)

1. **GICv3:**
   - No EKA2 code anywhere uses system-register GIC CPU interfaces (`ICC_*_EL1`), the redistributor, or affinity routing.
   - Only GICv1/ARM11MP-style `arm_gic.h` exists (and a GIC-400 board in Phorepoc a64).
   - We must write the GICv3 interrupt controller and the IPI code (`ICC_SGI1R_EL1`) from scratch.
2. **An A64 nanokernel arch layer:** no AArch64 code exists for EKA2:
   - context switch, `vectors`, exception entry/exit with an AArch32-EL0 frame (SPSR/ELR, banked regs to `x0–x14`);
   - `nccpu`, `ncirq`, `ncutils`;
   - atomics (`common/arm/atomic_*` are LDREX/STREX A32).

   The x86-64 port is the only 64-bit template, and it is a different ISA.
3. **The memory model on VMSAv8-64:**
   - `flexible/mmu/arm/xmmu.*` targets ARMv6/v7 short-descriptor tables.
   - Nothing implements 4 KB-granule 64-bit descriptors with 32-bit VA user and kernel spaces (or ASIDs via TTBR0 per process).
   - Phorepoc `x64mm` (x86 4-level paging) is the nearest conceptual example.
4. **Generic timer, PSCI and DTB-driven boot in our setting:**
   - Phorepoc a64 has generic-timer and PSCI patches for an *AArch32* kernel only.
   - No EKA2 code parses a DTB. The bootstrap expects a variant-specific boot table and superpage, so a DTB-to-boot-table shim is ours to write.
5. **A bootstrap at AArch64 EL1, MMU off:** the generic bootstrap (`bootmain.s`, `bootcpu.s`, `bootutils.s`) is A32 armasm. It needs a full A64 rewrite; the Phorepoc armasm2gas tooling only helps for A32.
6. **AArch32 EL0 under AArch64 EL1 specifics.** Undocumented in any Symbian source:
   - SVC immediate recovery (ESR gives only imm16; read the opcode);
   - TPIDRURO/TPIDRURW handling (Symbian uses CP15 thread ID registers);
   - VFP/NEON lazy save from EL1 (`kernel/arm/vfp.*` is AArch32 VFP).
7. **ROM tooling for a 64-bit kernel:** rombuild/elf2e32 handle 32-bit ARM or x86 kernel images only. Phorepoc's pdk `rombuild.py` is the place to extend (not inspected).
8. **Docs on the SMP nanokernel internals:** "Symbian OS Internals" (2005) predates nkernsmp. Beyond code comments, the 4 SMP topics in docscontent and the e32test SMP tests, there is no design document for `nk_bal`, tied events or IPI generation.

## Not verified

- **`kernelhwsrv_info/doc_pub` contents.**
- **akaWolf `Kernel:*` porting pages:** 403 for non-browser clients.
- **The Arm GNU 14.2 ILP32 multilib.**
- **Phorepoc pdk `rombuild.py` details.**
- **Whether BRANCH_GCC_SURGE fixes overlap Phorepoc's shims.**

## From the awesome-symbian lists

Checked 2026-11-05:
- **hstsethi/awesome-symbian** (CC0-1.0, last commit 2026-10-12): README plus `contributing.md`; there are no other sub-pages.
- **gauravssnl/awesome-symbian** (MIT, last push 2018-10-15): a flat list of about 150 links.

Dates are last-commit dates unless marked "push" (`pushed_at`). Items already covered above are only cross-referenced.

### Most useful items (ranked for the kernel port)

| # | Name | URL | What it is | Why it matters for us | Last activity | License |
|---|---|---|---|---|---|---|
| 1 | FShell (Symbian Foundation copy) | https://github.com/SymbianSource/oss.FCL.sf.os.fshell | The Symbian command shell (bash-like, with telnet), from Accenture. `build/sf/3tshell/` is a **textshell-only build "for S^3 or later, supports QEMU and beagleboard"**. It includes the `memoryaccess` LDD, which `objinfo` uses to read kernel object containers. | Our first interactive user-side test once eshell works. It runs without a GUI, and `ps`/`objinfo`/`chkdeps` look into kernel state from user side. It also exercises an LDD, so it tests our device-driver path. | 2010-12-07 | EPL-1.0 (headers) |
| 2 | FShell (d3ru mirror, later upstream) | https://github.com/d3ru/FShell | The same tree continued on SourceForge. Its last commit integrates a newer `makbsym`. | Newer than the SymbianSource copy (2012 vs 2010). If anything breaks, diff the two. | 2012-02-28 | EPL-1.0 (headers); GitHub detects none |
| 3 | Symbian bible / Symbian Seance (binarybacktrace.com) | https://binarybacktrace.com/symbian-bible ; https://binarybacktrace.com/tools/symbian_seance | Reverse-engineering notes on **Symbian OS 9.3 (EKA2), from a Nokia 5320 ROM**. They cover the SVC vector, the scheduler, handles, ROM structures (`TRomHeader`, `TRomImageHeader`, `TRomDllRefTable`) and boot. They list **269 execs (28 fast, 241 slow; 77 marked established)**, each tied to an address in the disassembly. Seance is an alpha browser workbench for emulating and debugging N-Gage 2.0 ROMs. | A third, independent view of the exec ABI, next to `execs.txt` (S^3, 337 entries) and EKA2L1. It is from a *shipped* 9.3 ROM, so it shows how the exec tables grew between 9.3 and S^3. **Unverified:** it has no author, no license and no source code, and by its own account none of it has been observed running live. | Entries dated 2026-09; added to the list 2026-10-09 | None stated |
| 4 | EKA2L1 | https://github.com/EKA2L1/EKA2L1 | HLE emulator. | Already covered as #10 above. | push 2026-11-05 | GPL-3.0 |
| 5 | Symbian OS ROMs collection | https://archive.org/details/symbian-os-roms_202010 | A single `Symbian OS ROMs.zip` of real device ROMs: Nokia 5320, 5800, N95, E5 and N-Gage. | Real EKA2 ROM images (the N-Gage one is EKA1). Use them to check our reading of the ROM header, superpage and exec tables, and to feed tools #3, #8 and #9. Nokia firmware: use it as a reference only, never ship it. Contents not inspected. | Uploaded 2020-10 | Proprietary (Nokia) |
| 6 | GnuPoc | https://github.com/mstorsjo/gnupoc-package | Patches that make the S60/UIQ SDKs build on Unix. It also has Unix builds of `elf2e32`, `petran`, `rcomp`, `makesis`, `bmconv` and `mifconv`, plus CodeSourcery GCC patches (2009q1 to 2011.09). | A known-good Unix build of `elf2e32`/`makesis` to fall back on if Phorepoc's toolchain image (#4 above) has gaps. Otherwise superseded by Phorepoc. | 2016-08-29 | GPL-2.0 |
| 7 | GCC4Symbian | https://github.com/fedor4ever/GCC4Symbian | A script that builds GCC 12.1, binutils 2.35 and gdb 10.2 for the `arm-none-symbianelf` target, plus a libstdc++ patch. | Shows how far a modern GCC goes for the symbianelf target. The README says it is incompatible with `abld` and was tested only on the S60 5th Edition SDK. Superseded by Phorepoc's Arm GNU 14.2 (`arm-none-eabi`). | 2022-06-15 | None |
| 8 | E32Explorer | https://github.com/mrRosset/E32Explorer | GUI viewer for E32Image (standard and J-format headers) and, in part, TRomImage. | Can check the E32Images our elf2e32 produces. It supports only the EKA1 import format, so it is of limited use for EKA2. | 2020-11-05 | None |
| 9 | RomBrowser and romdump (Florin9doi) | https://github.com/Florin9doi/rombrowser ; https://github.com/Florin9doi/romdump | A Visual Studio ROM-dump viewer with its own `TRomHeader.h` and `TRomImageHeader.h`, and a parser that turns a phone's hex dump into a ROM. | Small, independent ROM-header definitions to compare with `rombuild`. Windows-only. Low value. | 2021-04-22 | None |
| 10 | xsacha/SymbianGCC | https://github.com/xsacha/SymbianGCC | The Sourcery CodeBench GCC 4.8.3 tree, an attempt to modernise GCC for Symbian. | Historical only. GCC 14 already works for Phorepoc. | 2014-09-13 | GPL-2.0 / GPL-3.0 |
| 11 | "Smartphone Operating System Concepts with Symbian OS" (Jipping, Wiley 2007) | https://www.wiley.com/en-us/Smartphone+Operating+System+Concepts+with+Symbian+OS%3A+A+Tutorial+Guide-p-9780470065235 | A textbook on OS concepts that uses EKA2 for its examples. | A light companion to "Symbian OS Internals" (#8 above). Not inspected. | 2007 | Commercial |
| 12 | Symbian programming books collection (Google Drive) | https://drive.google.com/folderview?id=1vbW4hP06DeZvSwAX1MS_p52mNmSJs9iS | About 600 MB of Symbian and J2ME books. | It may hold a full PDF of "Symbian OS Internals" and the Symbian Press base or porting books. **Unverified** (not opened); copyright status unknown. | ? | Unknown |
| 13 | Symbian Archive | https://github.com/mrRosset/Symbian-Archive | Link hub. | Already covered above. | 2018-10-26 | None |
| 14 | E32Image format notes (Forum Nokia wiki and antonypranata.com, both on the Wayback Machine) | https://web.archive.org/web/20091213034509/http://wiki.forum.nokia.com/index.php/E32Image | Descriptions of the E32Image format. | Mostly EKA1 era. "Internals" App. 2 and the `elf2e32` source are authoritative. | 2007 to 2009 | Not stated |
| 15 | Communities: r/Symbian, the Symbian World Telegram, the EKA2L1 Discord, the N-Gage Discord | (see the hstsethi README) | Active user and emulator communities. | Places to ask for ROMs, books, or exec-ABI questions. The EKA2L1 Discord is the most technical. | Active (unverified) | n/a |

**Category 3 (validation apps): what exists besides fshell.**
- Neither list has kernel-level test programs.
- The best small console programs are already in kernelhwsrv, which neither list mentions:
  - `userlibandfileserver/fileserver/etshell/` (eshell, `eshell.mmp`)
  - `userlibandfileserver/fileserver/estart/`
  - the textshell ROM description `kernel/eka/rombuild/tshell.oby`
  - per-suite `tshell_*.oby` files: `hcr`, `domainmgr`, `digitiser`, `smr`, `haltests`

  Verified with the tree API.
- The list's app sources (DrJukka/Symbian_Codes, VlaoMao/symbian, sapandiwakar tutorials) are S60 GUI apps and of no use before the UI runs.

**Category 4 (apps for later, major ones only).**
- X-plore (file manager): the GitHub repo is gone; a Wayback copy exists.
- CuteTube 2 / cuteradio (marxoft, Qt).
- Star Browser (Qt).
- The OpenTTD port.
- PyS60 (fedor4ever/pys60).
- s2putty (urjaman).

All need Qt and S60 middleware on top of Phorepoc.

### What the lists mostly contain that is not useful to us

They are mostly app catalogues and app source repos (Qt/QML and S60 GUI apps), plus:
- game lists (MobyGames, MyAbandonware, speedruns);
- Carbide.ui theme editors and device plugins on mega.nz;
- app-level tutorials and books, J2ME/Python/SIS guides, SIS/MBM/AIF format notes;
- legacy IDEs (CodeWarrior, the Xcode plugin, JRE 1.3);
- a forensics paper;
- Hacking Team's RCS agent (dot-gov/core-symbian);
- many dead personal sites.

Several gauravssnl links are dead (404): `Symbian9/Symbian_Server`, `Symbian9/sisopen`, `Symbian9/cairo-for-symbian`, `htgoebel/sisinfo` and `Florin9doi/sdumper`.

### Contradicts or extends the sections above

- **Extends:**
  - **FShell (#1 and #2)** is missing from the sections above. It is the natural second user-side milestone after eshell. Its `sf/3tshell` platform already targeted QEMU and textshell ROMs in 2010.
  - **The Symbian bible (#3)** adds a third exec-ABI oracle. It counts 269 execs on 9.3, against 337 in S^3 `execs.txt`. Check the overlap before relying on it; its quality is unverified.
  - **Already in kernelhwsrv, not yet named above:** `etshell`, `estart` and `tshell.oby` (see "Category 3" above). Neither list mentions them; they belong with the bring-up tests under #1.
- **Contradicts:** nothing. Neither list has a newer kernel mirror, another source release, or any AArch64 kernel work.
- **AArch64 EKA2 efforts:** none in either list. A GitHub search on 2026-11-05 ("eka2 aarch64", "symbian aarch64", "eka2 kernel", "nanokernel symbian") found none either, which supports Gap 2 above. It turned up these repos, which are *not in either list*:
  - **AnmiTaliDev/neka** (GPL-3.0, 2026-07-08): "a free reimplementation of the Symbian EKA2 kernel architecture". It targets 32-bit ARM (`arm-none-eabi`, `qemu-system-arm -M versatilepb` running an `nktest.elf`). It is clean-room code, not EKA2 source, and too GPL to borrow from; worth watching only.
  - **atreia108/eka2_build_guide** (2023-10-22): a step-by-step build of EKA2 from **BRANCH_GCC_SURGE** of kernelhwsrv and adapt.Qemu. It uses Sourcery `arm-2010q1-190-arm-none-symbianelf`, PDK 4.0a and `oss.FCL.interim.SFTools.LinuxBuild` in an Ubuntu 10.04 VM. It is a period-correct reference build to compare Phorepoc's results against.
  - **IarChep/symix** (2026-10-31): a Linux kernel with an EKA2 compatibility layer. It is an empty idea.
  - **aweigit/EKA2L1-MiyooFlip** (2026-11-01): EKA2L1 on aarch64 Linux handhelds. Emulator packaging only; not relevant.
