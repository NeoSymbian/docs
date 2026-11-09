<!-- SPDX-License-Identifier: Apache-2.0 -->
# Kernel issue register

Baseline: kernel 792d36ef1a9169b3fc9084fcc494b209501a7487, reviewed 2026-11-09.
Read [assessment and scope](kernel-assessment.md) before interpreting these findings.
Implementation order, owners, dependencies and release gates are in [kernel-modernization.md](kernel-modernization.md).

## Reading and maintaining this register

P0 means investigate or fix first, before personal data or untrusted use. P1 means required for the supported
release scope. P2 means measured optimization or debt; it may be deferred with a clear reason and boundary.
These are work priorities, not CVSS scores or claims of demonstrated exploitation. A P0 hypothesis requires a
bounded reproduction/closure decision; it is not a confirmed vulnerability.

Evidence classes: **Defect** = a concrete static contract/error-path failure; **Configuration** = intentional
current behavior unsuitable for the stated release scope; **Risk** = a plausible path still needing proof;
**Gap** = missing implementation or acceptance evidence; **Reported** = existing historical observation;
**Optimization/Debt** = improvement requiring measurements/design; **Resolved** = retain as a regression.
No runtime kernel reproduction was performed in this audit. The runner probe is explicitly identified below.

All items remain open except KRN-032's historically resolved slot-retry behavior. A future fix needs a commit,
affected configurations, regression evidence and closure rationale; adding code or finding a passing older log
does not close it. Do not renumber IDs. Split newly distinct defects into new IDs, and link duplicates.

| ID | Priority | Origin | Class | Subject | Primary phase |
|---|---|---|---|---|---|
| KRN-001 | P0 | Build/integration | Configuration | ROM capability policy | KM2 |
| KRN-002 | P0 | Port | Configuration | Privileged USB debug monitor | KM2 |
| KRN-003 | P0 | Legacy/port | Gap | Secure RNG entropy integration | KM2 |
| KRN-004 | P1 | Legacy | Defect | Entropy publication/reset race | KM2 |
| KRN-005 | P1 | Legacy | Defect | Entropy initialization failure | KM2 |
| KRN-006 | P1 | Legacy | Gap | DRBG conformance and failure policy | KM2 |
| KRN-007 | P0 | Legacy/port | Configuration | Automatic formatting of corruption | KM1 |
| KRN-008 | P1 | Legacy | Defect | ESTART ignores recovery errors | KM1 |
| KRN-009 | P1 | Legacy | Defect | ScanDrive hides internal errors | KM1 |
| KRN-010 | P1 | Legacy | Risk | Directory cycle-check gaps | KM1 |
| KRN-011 | P0 | Legacy/port | Risk | User-copy versus privileged IPC alias | KM2 |
| KRN-012 | P2 | Legacy ABI | Debt | Kernel pointers as message handles | KM2 |
| KRN-013 | P1 | Legacy/port | Gap | ROM privilege separation and PAN | KM2 |
| KRN-014 | P0 | Port/drivers | Configuration | DMA isolation | KM2 |
| KRN-015 | P0 | Boot/update | Gap | Authenticity and rollback prevention | KM2 |
| KRN-016 | P0 | Storage/product | Gap | Encryption and secret lifecycle | KM2 |
| KRN-017 | P1 | Legacy/port | Defect | Delayed IRQ loses timer ticks | KM3 |
| KRN-018 | P1 | Scheduler/emulator | Reported | Protected-buffer failures | KM3 |
| KRN-019 | P1 | Legacy ABI/port | Gap | Register and FP context support | KM3 |
| KRN-020 | P1 | Port | Gap | SMP crash containment and diagnostics | KM3 |
| KRN-021 | P1 | Build | Gap | Diagnostics and compiler hardening | KM2 |
| KRN-022 | P0 | Build/tests | Defect | False-success runner and acceptance gaps | KM0 |
| KRN-023 | P1 | Legacy/dependencies | Gap | Unfinished parser/driver/advisory audits | KM6 |
| KRN-024 | P1 | Port/hardware | Gap | Power, thermal and interrupt lifecycle | KM4 |
| KRN-025 | P2 | Legacy/port | Optimization | IPC, allocator, storage and CPU costs | KM5 |
| KRN-026 | P2 | Port/build | Debt | Driver wiring and layering | KM5 |
| KRN-027 | P1 | Hardware | Reported | USB fails on normal cold boot | KM4 |
| KRN-028 | P2 | Input | Reported | Monitor typing drops characters | KM5 |
| KRN-029 | P1 | Modem | Reported | Connected call stays on 3G | KM4 |
| KRN-030 | P1 | Audio | Reported | No audio calibration/protection coverage | KM4 |
| KRN-031 | P2 | Syborg/display | Reported | Odd-width framebuffer shear | KM5 |
| KRN-032 | Regression | Boot/update | Resolved | ABL slot retries and image mismatch | KM4 |
| KRN-033 | P1 | Legacy ABI/VM | Gap | Address widths and resource limits | KM3 |
| KRN-034 | P1 | Product/services | Gap | Maintained firmware and system support | KM6 |

## Legacy security and boundary findings

### KRN-001: ROM capability policy

The ROFS builder grants every executable capability=All. XIP image construction has a fallback that gives all
capabilities to an EXE whose header declares none; capability overrides are conditional on a capability map.
This undermines least privilege even though EKA2's enforcement is active. An ordinary privileged ROM application
can reach operations that would correctly reject a least-capability client. It is not evidence that every disk
application gets these capabilities.
[ROFS builder](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/tools/build-userrom.sh#L80-L88),
[header/fallback policy](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/tools/rombuild.py#L74-L104),
[XIP section](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/tools/rombuild.py#L1298-L1305).

**Fix/close:** declare required EXE/DLL capabilities and SID ownership per image, default missing declarations to
failure or none, and separate development overrides from release manifests. Preserve loader DLL-capability
compatibility. **Acceptance:** inspect emitted core/ROFS/disk image headers; least-capability clients must fail
privileged HAL, protected-server, filesystem and driver operations; intended servers still start. Recheck
effective forced security flags and prove no unlocked build define slipped into the release.

### KRN-002: Privileged USB debug monitor

The USB DFC passes received lines to A64Mon_Line without an authentication stage. The monitor supports mapped
memory reads/writes, input injection, storage and reboot operations; it is started by the common extension.
The screen-console default is not a security boundary for this transport. A connected USB host is a privileged
actor whenever this gadget is active. Normal-boot USB trouble (KRN-027) is not a dependable mitigation.
[USB dispatch](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/sdm670_assp/qcom_dwc3_acm.cpp#L424-L464),
[monitor](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/common/specific/a64_dbgmon.cpp#L543-L621),
[startup](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/common/specific/a64_variant.cpp#L328-L341).

**Fix/close:** omit privileged monitor handlers/transports from release images, or design an explicitly enabled,
authenticated development mode with scoped access. Keep a recoverable service path. **Acceptance:** check linked
symbols and USB descriptors on release builds; a hostile host cannot read logs/memory, write storage, inject input,
or change power/slot state. Development tooling must have its own positive tests.

### KRN-003: Secure RNG entropy integration

A committed-tree search finds no RandomSalt/AddTimingEntropy caller in the arm64 board, kernel or nanokernel
adapters. The inherited generator initially mixes time but remains unready; credited entropy is what changes its
secure state. This is a source integration gap, not a measured installed-image state or a demonstrated key leak.
The working-tree PRNG is not a validated replacement for this contract.
[initial state](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/securerng.cpp#L26-L51),
[secure transition](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/securerng.cpp#L341-L374),
[API readiness](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/random.cpp#L34-L74).

**Fix/close:** integrate a characterized source, health checks, conservative entropy credit, reseeding and
early-boot/resume policy; keep QEMU test entropy distinct. Resolve KRN-004/005 before enabling collectors.
**Acceptance:** adapt t_securerng and t_entropysources; inject absent/stuck/repeated/failing sources; prove
SecureRandom readiness transitions and refusal of key/session-secret generation on NotReady. Audit all consumers;
this review did not establish which, if any, misuse unready output.

### KRN-004: Entropy publication/reset race

The inherited SMP producer disables local IRQs, reads the published count N, writes buffer[N], then atomically
adds count/entropy. A drainer on another CPU can copy [0,N) and reset status N to zero between those producer
steps. The producer then publishes count 1 for a sample stored at N; the next drain hashes stale buffer[0] while
crediting the new sample's entropy. Atomic publication does not reserve the slot across a consumer reset.
This is a concrete permitted interleaving; target occurrence/cryptographic impact are unmeasured and the path is
latent if the platform has no collectors.
[producers](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/srandombuff.cpp#L55-L132),
[drainer](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/srandombuff.cpp#L154-L182).

**Fix/close:** establish an IRQ-safe per-CPU ownership/handoff protocol so every credited sample is consumed
exactly once. Pool mutexes remain in DFC/thread context. **Acceptance:** force every producer/reset interleaving,
track sample IDs and credited bits, then stress mixed 32/64-bit collectors on all CPUs, including full buffers,
disable and resume. Preserve the entropy-pool/RNG lock order.

### KRN-005: Entropy initialization failure

InitialiseEntropyBuffers does not check Kern::Alloc before deriving per-CPU pointers and returns KErrNone
unconditionally. Its caller checks an error result that cannot report that allocation failure.
[allocation](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/srandombuff.cpp#L187-L203),
[caller](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/sinit.cpp#L469-L480).

**Fix/close:** check allocation before publication, propagate failure, and audit RNG object/mutex construction.
**Acceptance:** inject failure at every initialization allocation; no invalid pointer or queued collector/DFC
uses partial state, readiness remains false, and boot takes its documented error path. This is not a demonstrated
post-boot unprivileged OOM exploit.

### KRN-006: DRBG conformance and failure policy

HashDf hashes the native-memory representation of the value 440; on this target that is B8 01 00 00. Compare its
encoding and complete algorithm to independent vectors for the intended Hash_DRBG, including NIST 800-90A
section 10.3.1. Continuous-test/reseed-limit failures also fault the kernel. Conformance and availability policy
need explicit validation; neither fact alone establishes a cryptographic break.
[HashDf](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/securerng.cpp#L235-L263),
[generation failures](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/securerng.cpp#L74-L87),
[continuous test](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/securerng.cpp#L199-L212).

**Fix/close:** document intended algorithm/encoding and failure transitions; correct mismatches found by independent
known-answer tests. **Acceptance:** instantiate/generate/reseed/derivation vectors, exhaustion and health-test
fault injection, serialized concurrency, and no insecure consumer fallback. SHA-256 vectors alone are insufficient.

### KRN-011: User-copy versus privileged IPC alias

CopyFromUser/CopyToUser/SetUser choose privileged memcpy/memset when the starting pointer is in KIPCAlias, without
checking the whole interval or proving provenance at that point. Legitimate Alias rejects remote user pointers
in that region, limits returned extents, makes mappings EL1-only and removes them afterward. These guards mean
the helper code alone does not prove an exploitable syscall schedule.
[copy helpers](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/arm64/a64e_exc.cpp#L141-L195),
[alias guards](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/memmodel/epoc/flexible/mmu/arm64/xmmu.cpp#L698-L762),
[mapping/extent](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/memmodel/epoc/flexible/mmu/arm64/xmmu.cpp#L779-L833).

**Fix/close:** first prove or rule out attacker-controlled selection of a live privileged alias, including another
thread in the server process. If reachable, separate internal alias copy from untrusted user copy and bind
ownership, full range/overflow checks and fault cleanup to the operation. **Acceptance:** forged alias pointers,
cross-boundary sizes, read-only pages, client death/unmap, preemption/migration and simultaneous copies; port
t_ipcsafety/t_ipccpy. Record a reviewed reachability proof if no reproduction is possible.

### KRN-012: Kernel pointers as message handles

RMessageU2 receives the kernel RMessageK address. Use validates bounds, state and server ownership, so this is an
address-disclosure/ABI debt, not an authorization bypass demonstrated here.
[handle export](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/sipc.cpp#L53-L94),
[validation](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/sipc.cpp#L232-L254).

**Fix/close:** evaluate a compatible opaque per-server index/generation token before address randomization work.
**Acceptance:** forged, stale, reused, cross-server and concurrently completed handles, disconnect/cancel/death,
wraparound and 2010/Rust server compatibility; measure lookup latency. A constant pointer mask is insufficient.

## Persistent data and filesystem recovery

### KRN-007: Automatic formatting of corruption

Both C: and E: enable FS_FORMAT_CORRUPT. ESTART invokes FormatDrive on KErrCorrupt, covering damaged initialized
media as well as blank media. The configuration's comment describing a fresh drive does not restrict this behavior.
[configuration](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/common/estart.txt#L1-L7),
[format branch](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/userlibandfileserver/fileserver/estart/estart.cpp#L1454-L1460).

**Fix/close:** separate explicit provisioning from ordinary boot; preserve damaged personal volumes and expose
bounded repair/read-only recovery. Keep RAM-drive initialization separate. **Acceptance:** corrupt disposable
boot sectors, FAT copies, FSInfo and directory data; normal boot never formats an initialized volume. Capture
before/after bytes and recovery outcome; only an explicitly selected provisioning path initializes blank media.

### KRN-008: ESTART ignores recovery errors

ESTART deliberately requests ScanDrive for rugged FAT but discards its result. Rugged rename recovery depends
on this repair succeeding, so mount success alone cannot establish a healthy writable volume.
[ignored result](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/userlibandfileserver/fileserver/estart/estart.cpp#L1463-L1486),
[recovery dependency](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/userlibandfileserver/fileserver/sfat32/sl_mnt.cpp#L1147-L1172).

**Fix/close:** propagate/interpret scan status and prevent ordinary writable use after required recovery fails;
do not turn that failure into KRN-007's format path. **Acceptance:** inject OOM, corruption, in-use and media errors
after successful mount; assert visible status and safe access policy. Include clean volumes and successful repair.

### KRN-009: ScanDrive hides internal errors

The sfat32 scan path traps remount into nRes but returns only the earlier scan error. It later traps
FinaliseMountL into nRes, uses an assertion and returns KErrNone. Finalization includes FAT/FSInfo/clean-bit writes.
The runtime consequences of each failed remount remain to be measured.
[suppressed errors](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/userlibandfileserver/fileserver/sfat32/sl_mnt.cpp#L4271-L4307),
[finalization](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/userlibandfileserver/fileserver/sfat32/sl_mnt.cpp#L565-L605).

**Fix/close:** preserve the first error, stop using failed reconstruction state, and leave the volume unvalidated.
**Acceptance:** fault allocations and I/O through repair/dismount/remount/finalization; verify status reaches both
FSY and ESTART and a failed finalization is not treated as clean. Test KRN-008 and KRN-009 independently.

### KRN-010: Directory cycle-check gaps

Normal FAT search has a cycle detector, but DoFindL skips it on the first MRU scan-ahead pass. MoveToDosEntryL and
FindShortNameL also walk entries without the same explicit bound. A cyclic FAT32 directory without a terminator
is a candidate hang; a public-operation/runtime reproduction is still required.
[MRU pass](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/userlibandfileserver/fileserver/sfat32/sl_mnt.cpp#L2554-L2584),
[conditional detector](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/userlibandfileserver/fileserver/sfat32/sl_mnt.cpp#L2766-L2771),
[VFAT walk](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/userlibandfileserver/fileserver/sfat32/sl_mnt.cpp#L3173-L3187),
[short-name walk](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/userlibandfileserver/fileserver/sfat32/sl_vfat.cpp#L413-L435).

**Fix/close:** bound every untrusted link walk using the existing detector or a common volume-derived iterator.
**Acceptance:** self/multiple-cluster cycles, all-VFAT entries, missing terminators and invalid links; test cold
and cached lookup, enumeration, alias generation, rename and delete. Bound CPU/I/O work and keep other drives
responsive. Start with t_fatcorrupt, t_scan and t_vfat; preserve valid-volume behavior.

## Kernel and device trust

### KRN-013: ROM privilege separation and PAN

The bootstrap maps the ROM readable/executable by both EL0 and EL1; it contains kernel and user code. PAN is
explicitly cleared and WXN disabled. Other mappings already set PXN/UXN, so this is a mapping-design/hardening gap,
not a claim that all memory is writable/executable or that a particular data leak was demonstrated.
[ROM permissions](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/arm64/a64boot.cpp#L111-L121),
[control state](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/arm64/a64boot.cpp#L424-L439),
[runtime permissions](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/memmodel/epoc/flexible/mmu/arm64/xmmu.cpp#L358-L380).

**Fix/close:** map kernel text/constants privileged, separate legacy user XIP access, inventory all writable
aliases and executable transitions, then evaluate PAN/W^X with the existing descriptor/user-copy design.
**Acceptance:** page-table audit plus EL0 read/write/execute negative probes for each mapping class; kernel data
never executes, code cannot be modified, and IPC/loader/cache/fault-recovery regressions pass. Do not simply flip
PAN/WXN and assume the legacy shared-ROM design remains compatible.

### KRN-014: DMA isolation

The IPA SMMU bank maps the entire low 4 GB with four 1 GB blocks instead of only assigned buffers. Hypervisor
stage-2 permissions may further constrain access, so an unrestricted modem-to-CPU-memory exploit is not established.
The in-tree stage-1 policy still grants much more than a buffer contract requires.
[mapping](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/sdm670_assp/qcom_smmu.cpp#L45-L85).

**Fix/close:** define per-device domains, permitted buffers/directions, map/unmap lifetime, DMA/cache synchronization,
fault reporting and teardown/reset ownership. **Acceptance:** a test device/controlled driver cannot DMA outside
assigned pages; unmap/reset revokes access, stale mappings fault, timeout/fault recovery works, and normal IPA/USB/
storage traffic retains correct cache behavior. Audit remoteproc carve-outs separately.

### KRN-015: Authenticity and rollback prevention

ROFS block hashes ride in boot.img; the code explicitly notes ABL does not verify that image while unlocked.
Hashes detect changed blocks relative to the supplied boot image, and A/B recovers failed boots; neither alone
authenticates an update or rejects an older signed vulnerable version.
[documented trust shortcut](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/common/specific/a64_medverity.cpp#L16-L23),
[hash packaging](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/tools/build-ekern.sh#L94-L102).

**Fix/close:** design authenticated boot/update metadata, key provisioning/rotation/revocation, version rollback
policy, protected rollback state, boot+ROFS binding, power-safe installation and recovery. Research the device's
actual supported trust path before any lock-state change. **Acceptance:** wrong key, tampered images/metadata,
mixed pairs, truncated update, replay/downgrade and power interruption fail safely; good updates and authorized
recovery work. No bootloader locking or device writes are authorized by this documentation.

### KRN-016: Encryption and secret lifecycle

The current filesystem plan puts userdata encryption in future work; no at-rest protection acceptance is
available for C:/E: in this assessment. Capability isolation and ROFS integrity do not protect removed/stolen
userdata. A PIN-derived key without an offline-attack/rate-limit design is not a complete solution.
[current plan](filesystem.md#later-daily-phone-stage).

**Fix/close:** specify encrypted volume/metadata scope, authenticated key wrapping, KDF and hardware-backed
rate limiting where available, unlock/recovery, backup/restore, secure deletion limits and crash-log privacy.
**Acceptance:** copied media does not reveal protected files/keys, weak credentials cannot bypass the chosen
rate-limit model, power loss preserves recoverability, logs/crash dumps contain no raw secrets, and key/source
failure blocks access safely. Depends on KRN-003/006/015; use disposable data for earlier stages.

## Correctness, compatibility and acceptance

### KRN-017: Delayed IRQ loses timer ticks

TimerIrq advances iNextTick past every elapsed deadline, then invokes the hook once. CPU0's hook calls Tick once;
the inherited queue increments its millisecond count once. Delayed IRQs can therefore lose elapsed software
ticks. The magnitude on real workloads was not measured.
[IRQ adapter](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/nkernsmp/arm64/a64_platform.cpp#L92-L106),
[baseline hook](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/common/specific/a64_variant.cpp#L202-L206),
[legacy increment](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/nkernsmp/nk_timer.cpp#L736-L746).

**Fix/close:** account monotonic elapsed intervals and deliver due callbacks exactly once with bounded catch-up.
NTimerQ::Advance assumes no timer expires; using it blindly would skip expiries.
[Advance contract](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/nkernsmp/nk_timer.cpp#L911-L925).
**Acceptance:** instrument IRQ masking for 5/20/100 ms; compare counter time, TickCount, NTimer/RTimer deadlines
and callback counts under SMP/I/O load and later suspend/resume. Correct this before tickless optimization.

### KRN-018: Protected-buffer failures

[Known issues](known-issues.md) records QEMU TCG interlocked suspend/kill/migrate failures and a separate phone
pass. The cause remains unknown. The older reschedule handshake defect was fixed; the proposed iCsCount ordering
explanation is a hypothesis, not a demonstrated root cause.
[current handshake](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/nkernsmp/arm64/a64s_ncsched.cpp#L119-L159).

**Fix/close:** preserve/reproduce exact image and emulator hashes/configuration with RWTRACE, then establish which
implementation/test/emulator invariant fails. **Acceptance:** serial and skmpar repeated soak with 1/2/8 CPUs,
forced migration/kill/suspend and DFC/tied-event activity, zero protected-buffer errors and a causal explanation/
regression. A hardware pass alone does not close the supported-emulator failure.

### KRN-019: Register and FP context support

NThread Get/SetUserContext are empty, CompleteContextSave is empty, and the generic context accessor can report a
stale frame for a thread running on another CPU. FP save/restore hooks default to no-ops. Existing S4 work remains
open; enabling user FP/NEON before complete ownership/save/restore would be unsafe.
[empty methods](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/nkernsmp/arm64/a64s_ncsched.cpp#L560-L562),
[FP defaults](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/nkernsmp/arm64/a64s_ncsched.cpp#L34-L41),
[context accessor](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/nkernsmp/arm64/a64e_nkern.cpp#L165-L183).

**Fix/close:** define supported context/debug APIs and precise unavailable-register results; implement synchronization
for live remote contexts. Add complete per-thread FP/NEON/FPSR/FPCR ownership and exception paths before enabling
it, including interaction with kernel SHA instructions. Preserve ARMv5TE soft-float calling ABI.
**Acceptance:** distinct register/FP patterns across preemption, migration, blocking, exceptions and thread death;
no state leaks; C++/Rust exec, SWP/alignment and descriptor compatibility suites. Unsupported legacy VFP short
vectors need an explicit contract or implementation and tests.

### KRN-020: SMP crash containment and diagnostics

NotifyCrash disables local interrupts, reports state and asks for reset, without a crash IPI to freeze peers.
The log ring also documents racing saved-head stores; project instructions document a 256-byte formatted-output
limit. These can reduce crash containment/evidence, but are not proof of corrupt storage after every panic.
[crash path](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/nkernsmp/arm64/a64e_nkern.cpp#L76-L88),
[log publication](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/common/specific/a64_dbgmon.cpp#L47-L68).

**Fix/close:** bounded peer-stop protocol, panic-safe output, consistent per-CPU crash records and deterministic
watchdog fallback; trace the formatting limit before claiming a formatter overflow. **Acceptance:** faults on
each CPU during I/O/locks, a nonresponsive peer, long/truncated log records, ring wrap and reset persistence;
surviving records identify the build/CPU/reason and exclude secrets. Formatting failure must not recursively panic.

### KRN-021: Diagnostics and compiler hardening

The inherited build uses -fpermissive and -w; stack protection is disabled. Some aliasing/lifetime/null-check flags
deliberately preserve old compiler assumptions. These are review gaps rather than evidence every warning is a bug.
An RWX ELF-segment warning also does not prove runtime PTEs are RWX.
[census flags](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/tools/ekern-census.sh#L32-L39),
[adapter flags](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/tools/build-ekern.sh#L28-L40).

**Fix/close:** capture a warning baseline by subsystem, enable diagnostics first for changed code and reduce
exceptions deliberately. Add freestanding canary initialization/failure handling and stack guards where supported;
use host sanitizer/fuzz harnesses for parsers and target-appropriate instrumentation. **Acceptance:** reviewed
warning dispositions, no new diagnostics, guard/canary fault injection, artifact mapping inspection, and unchanged
ABI/boot/interrupt behavior. Do not change compiler/toolchain versions merely to silence old code.

### KRN-022: False-success runner and acceptance gaps

run-qemu.sh does not require a success marker by default. It waits for QEMU, prints the log, then returns the
empty-expectation test result; neo qemu supplies no marker. A controlled probe replaced only the timeout launcher
with one exiting 42: the actual script returned 0 without a marker and 1 with a missing marker. No QEMU ran.
[runner](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/tools/run-qemu.sh#L57-L59),
[front end](https://github.com/NeoSymbian/build/blob/82be8e7a3a006bdf21325e374fa8b9b8299a12f0/neo#L44-L50).

The inspected build CI checks a Syborg user-side boot and screen content, not the full arm64 kernel security/
filesystem suites. No tracked kernel .github workflow exists at the baseline.
[build workflow](https://github.com/NeoSymbian/build/blob/82be8e7a3a006bdf21325e374fa8b9b8299a12f0/.github/workflows/build.yml#L10-L39).

**Fix/close:** distinguish interactive smoke runs from assertive gates; require completion/failure records,
validate emulator launch/exit, and fail on panic, timeout-before-completion, missing tests or unexpected skips.
Pin source/image/test manifests together. **Acceptance:** launcher failure, missing binary, crash, stalled guest,
partial suite and known-bad fixture all fail the gate; positive controls pass. Add reproducible legacy-test ROM
selection and per-test statuses. Artifact hashes and raw logs, not exit 0 alone, establish a result.

### KRN-023: Unfinished parser, driver and advisory audits

Generic channel creation/marshalling cannot establish each driver's per-operation policy or buffer lifetime.
Complete the linked-driver inventory and legacy F32/ROFS/E32/descriptor/heap review, with capability/SID, size/
overflow, async cancel/close/death, pinning and OOM checks.
[channel dispatch](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/device.cpp#L652-L676),
[DFC request path](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/device.cpp#L872-L935).

Known-advisory candidate: the tree contains a stripped crash-logger zlib 1.2.3, with the older overlaid distance/
literal buffers associated with upstream CVE-2018-25032. Compare the maintainer fix cited in
[the assessment](kernel-assessment.md#external-known-issues-and-references); reproduction against this modified
copy is pending. Its original exmon MMPs list it, but the reviewed arm64 census/build lists do not compile those
zlib/crash-logger files. Treat this as dormant legacy-source applicability work, not an active arm64 CVE finding.
The header says deflatePrime and several other APIs were removed; do not assign advisories for absent APIs.
[version/removals](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/zlib/zlib.h#L1-L32),
[overlay](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/zlib/deflate.cpp#L278-L295),
[MMP inclusion](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/kernel/exmonlog.mmp#L29-L34).

**Fix/close:** maintain a component/SBOM and advisory ledger with source modification, linkage and reachability
dispositions; patch/backport or remove affected paths before enabling them. Audit the actually fetched security/
network stacks separately. **Acceptance:** hostile input and lifetime/OOM harnesses for every release-reachable
parser/privileged driver, independent review, and regression fixtures for confirmed defects. Dormant components
are explicitly excluded or covered before use; no blanket statement that all 2010 CVEs are fixed.

### KRN-033: Address widths and resource limits

TPhysAddr remains 32-bit; the arm64 layout reserves 256 ASIDs including the kernel. These are compatibility and
capacity limits, not evidence of a specific overflow. Physical RAM/carve-out needs must be verified before widening
the ABI or enabling extra memory/paging.
[physical type](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/include/kernel/kernel.h#L51-L55),
[ASIDs](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/include/memmodel/epoc/flexible/arm64/mmboot.h#L125-L129).

**Fix/close:** document usable memory and reserved ranges, pointer/physical/size conversions, process/thread/handle/
shared-memory budgets, time-width/wrap behavior and paging configuration. Widen only with a versioned kernel/
driver/DMA migration plan. **Acceptance:** ASID exhaustion/reuse, process churn, page pin/unmap/death, high physical
addresses in simulated maps, oversized lengths, OOM recovery, counter/RTC wrap and time changes. Never truncate an
unsupported address silently. PAC/BTI/MTE and speculative-execution mitigations require a target/EL2 feature and
errata inventory; do not assume an older CPU implements newer architectural features.

## Hardware lifecycle, optimization and existing issues

### KRN-024: Power, thermal and interrupt lifecycle

Keys/touch/USB/storage rely on polling; RPMh votes are active-only and never dropped, core retirement is absent,
and cpufreq has no governor/thermal driver. Existing touch boost/capacity balancing already work.
[power votes](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/sdm670_assp/qcom_rpmh.cpp#L1-L15),
[clock policy](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/sdm670_assp/qcom_cpufreq.cpp#L1-L15),
[core retirement limit](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/kernel/eka/nkernsmp/arm64/a64s_ncutils.cpp#L106-L118).

**Fix/close:** define IRQ/DFC/device state machines, suspend/wake/reset, vote aggregation, battery/charger and thermal
policy. Replace polling where wake/latency measurements justify it. **Acceptance:** repeated suspend/resume and
hot/cold starts, screen/key wake, stalled devices, thermal/battery faults and overnight power measurements with
documented conditions. Timer correctness and DMA/reset ownership are prerequisites.

### KRN-025: Measured IPC, allocator, storage and CPU costs

The media adapter is synchronous/serialized, and virtio/eMMC have limited request concurrency. Legacy IPC,
allocation, SWP emulation and recurring timer/DFC work are candidates for measurement, not presumed bottlenecks.
[media limit](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/common/specific/a64_medblk.cpp#L8-L9).

**Fix/close:** benchmark first, then choose bounded request queues, cancellation, merging/read-ahead/cache policy,
allocator contention changes, tickless idle, or feature-detected atomics. Keep existing LL/SC fallbacks, soft-float
ABI and rugged metadata ordering. **Acceptance:** matched before/after workload/image/clock/thermal conditions;
report throughput and p50/p95/p99 latency, CPU/memory/energy and regressions. No optimization is complete without
correctness, crash-recovery and resource bounds; demand paging needs its own backing-store/trust acceptance.

### KRN-026: Driver wiring and layering

The [baseport debt list](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/README.md#L105-L148)
records weak start/monitor defaults, silent missing drivers, implicit bus order, board-owned SoC lists, basename
object collisions, duplicate GPT parsers, SoC/board policy mixing, repeated hardware constants and omitted hooks.
All remain planned; this audit implements none of them.

**Fix/close:** follow that existing registry/object-name plan, then coordinated layering moves at a quiet point;
do not reorganize drivers while changing behavior. **Acceptance:** unique object checks, expected-driver/start
order manifest, no silent fallback, symbol/link-map comparisons and equal boot/driver behavior on QEMU and bonito.
Each of the existing debt rows needs a disposition; a tree move alone does not close the list.

### KRN-027: USB fails on normal boot

[Known issues](known-issues.md) records PHY registers reading zero after attempted power-up, with RPMh votes
surviving warm reset. Debug/FS6 use works only in the reported fastboot RAM-boot state. Not reproduced here.
**Fix/close:** establish independent clock/rail/PHY/reset ownership and a cold-start sequence with bounded errors.
**Acceptance:** normal installed cold boot, warm boot, unplug/replug and failed-start recovery; prove data transfer
without inherited ABL USB state. Retain KRN-002's release access policy.

### KRN-028: Monitor typing drops characters

[Known issues](known-issues.md) reports a 29-character command truncated on the phone; short lines are the current
workaround. Queue saturation/pacing remain hypotheses. **Fix/close:** instrument enqueue/dequeue/drop counts and
apply backpressure or acknowledged injection. **Acceptance:** long/spaced command bursts under UI/I/O load on phone
and QEMU, exact received bytes and no silent truncation. Development tooling still needs reliable input.

### KRN-029: Connected call stays on 3G

[Known issues](known-issues.md) and [telephony C7](telephony.md#c7-complete-calls) record LTE return after ringing
but not after a connected call, despite a separately reported Linux return. CDSP/PDR/ADSP teardown are investigation
directions, not established causes. **Fix/close:** compare resource/session lifecycle and implement the causal fix.
**Acceptance:** repeated incoming/outgoing connected/declined/cancelled calls return to the expected network,
including remote hangup, weak signal and modem restart; no remote-processor crash or leaked resource.

### KRN-030: Audio calibration and protection

[Known issues](known-issues.md) documents uncalibrated call audio; the board driver also states amplifier protection
errors are only logged at start.
[driver limits](https://github.com/NeoSymbian/kernel/blob/792d36ef1a9169b3fc9084fcc494b209501a7487/baseport/arm64/bonito_variant/specific/a64_audio.cpp#L1-L16).
**Fix/close:** define supported calibration/provenance, safe gain limits, route ownership and amplifier fault/
shutdown handling. **Acceptance:** documented earpiece/speaker/headset levels and echo, route changes, thermal/
protection faults and long calls without resource leakage. Loopback feedback alone is not evidence of a kernel bug.

### KRN-031: Odd-width framebuffer shear

[Known issues](known-issues.md) reports shear at 539x1079 and correct output at 540x1080, with guest-driver stride
and screenshot path still unverified. **Fix/close:** trace programmed stride/end-to-end capture before assigning
cause. **Acceptance:** deterministic pixel patterns at odd/even widths, guest-visible stride, host capture and
rendered screenshots agree. Keep emulator display evidence separate from phone display acceptance.

### KRN-032: ABL slot retries and image mismatch

Historically resolved by FS5b per [known issues](known-issues.md); not revalidated here. Keep the corrected ABL
RAM-boot retry behavior and matched boot/ROFS checks as regressions. **Acceptance:** successful/failed boot,
retry exhaustion/fallback, good-boot marking, interrupted inactive-slot update and mismatched ROFS rejection on
disposable/approved test slots. Do not revive the superseded cold-reset explanation or mark this unresolved.

### KRN-034: Maintained firmware and system support

Kernel modernization alone cannot establish a supported phone. Pinned user-side networking/TLS/installers and
privileged services need audit; modem/DSP/TEE/bootloader firmware need exact versions, provenance and a patch
strategy. Google lists this hardware outside Android/security update support
([primary support statement](https://support.google.com/pixelphone/answer/4457705?hl=en)).
This is an external lifecycle risk, not a finding that a particular proprietary firmware is exploitable.

**Fix/close:** define supported hardware/use cases, service ownership/restart/isolation, networking/certificate/
update trust, disclosure/patch process, supported lifetime and firmware advisory dispositions. Keep private
firmware/device identifiers outside public artifacts. **Acceptance:** published release manifest and recovery/
patch process, service crash/restart/DoS and network negative tests, and an explicit firmware-support go/no-go.
If required firmware cannot be maintained to the chosen threat model, keep bonito as a development target and
select supportable hardware for the supported product.

## Existing known-issues coverage

No historical issue has been silently closed or re-diagnosed by this audit.

| Section of known-issues.md | Register |
|---|---|
| Slot retries / black screen / ROFS mismatch | KRN-032, historically resolved; regression retained |
| QEMU DoRWTest protected buffers | KRN-018 |
| Monitor type drops a line ending | KRN-028 |
| Modem remains on 3G after connected call | KRN-029 |
| Call audio calibration | KRN-030 |
| USB power on a normal boot | KRN-027 |
| Syborg odd-width shear | KRN-031 |

Broader existing plans map to KRN-019 (smooth-ui S4), KRN-024 (H3), KRN-025 (M4/S5/S6 and storage concurrency),
KRN-026 (all baseport layout debts), KRN-015/016 (filesystem trust/encryption), and KRN-034 (telephony/system
support). These mappings add release acceptance requirements without rewriting earlier milestone history.
