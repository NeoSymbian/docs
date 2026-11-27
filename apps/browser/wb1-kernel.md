<!-- SPDX-License-Identifier: Apache-2.0 -->
# WB1: the kernel

Part of the [browser docs](../browser.md).

**Status:** ✅ done 2026-11-17 · [kernel#19](https://github.com/NeoSymbian/kernel/pull/19), [e32-rs#3](https://github.com/NeoSymbian/e32-rs/pull/3)

## Scope

| Stage | Work | Gate | Estimate (PM) |
|---|---|---|---:|
| WB1 kernel | smooth-ui S4 (kernel part), M4.3, stack limits, VM primitives, entropy. Result below | FP patterns survive preemption and migration; 8 MiB threads; GC-style reserve/decommit tests | 3–5 |

## Result (2026-11-17): done

Kernel PR [kernel#19](https://github.com/NeoSymbian/kernel/pull/19), tests [e32-rs#3](https://github.com/NeoSymbian/e32-rs/pull/3)
(`NEOWB1.EXE`). **6/6 pass on QEMU virt (4 CPUs) and on the Pixel (RAM boot).**

| Item | What changed | Test |
|---|---|---|
| FP/NEON for AArch32 apps | `CPACR_EL1.FPEN` on for every CPU; Q0–Q15 + FPSR/FPCR switched with the thread, eagerly (`a64_ctxsw.S`, `NThread::iCoprocessorState`); medverity's SHA-256 keeps the thread's registers | VFP math; 8 threads × 100 rounds fill every register and FPSCR, spin 20 ms, check. Negative control: without the switch, all 8 fail |
| Stacks | `PP::MaxUserThreadStack` 16 MiB (was 1 MiB) | an 8 MiB stack used to the end, 32 MiB refused; 128 threads alive at once |
| GC memory | none needed: disconnected chunks | reserve 1 GiB and 256 MiB; commit/decommit 1 MiB pieces at 1 MiB-aligned addresses; a decommitted page faults; recommitted memory is fresh |
| Entropy | IRQ timing feeds `DSecureRNG` once extensions start; the SDM670 PRNG seeds 512 bits at boot | `Exec::MathSecureRandom` |

- **The open question is answered:** Qualcomm's EL2 does not trap AArch32 FP.
- **Shortcuts, to revisit only if measured:**
  - FP is saved on every reschedule (no trap on first use);
  - stacks are committed in full;
  - there is no user protect call: no-JIT SpiderMonkey does not need one (WB3, [wb3-js.md](wb3-js.md)).
- **Still open from S4:** the Rust ARMv7/NEON softfp target and LDREX atomics, which come with WB2.
