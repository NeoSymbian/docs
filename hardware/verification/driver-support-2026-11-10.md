<!-- SPDX-License-Identifier: Apache-2.0 -->
# Driver foundation verification — 2026-11-10

This change implements the initial inventory and bus/audio-lifecycle foundations
of [driver support](../driver-support.md). It does not implement PCM, camera or
sensor capture. Verification used working-tree changes; unrelated fshell tools
are preserved outside this change.

## Reproduction and evidence

Private artifact root: `private/driver-support/20261110/` in the workspace.

- `python3 docs/tools/inspect-bonito.py private/bonito.dtb`: exit 0; selected
  compatible strings and effective status only. `dtb-inventory.json` records the
  hash and configured parts; it is not a physical chip-ID/readiness probe.
- `python3 -m unittest discover -s docs/tools -p 'test_*.py' -v`: exit 0,
  six passed. Covers malformed block/node/end boundaries, every truncation,
  disabled ancestry and exclusion of private fields. Raw `inventory-tests.log`
  and commands/exits in `inventory-validation.json`.
- Telephony command/cwd/exit records: `audio-validation.json`, raw `audio-*.log`.
  Host protocol tests and pinned ARM builds are recorded separately from runtime.
- Kernel artifacts are built from an isolated snapshot under
  `/DATA/AppData/symbian-build/logs/driver-support-kernel-20261110/` on ZimaOS.
  The existing shared kernel checkout is dirty and was not changed. The existing
  remote toolchain image is used without changing pins/toolchains.

## Telephony checks after review fixes

Host workspace: **64 tests passed** (58 modem-proto, four ext4ro, two IPC).
The startup-only radio-disabled build has a separate target directory; the default
artifact retains cellular startup. No runtime airplane-mode interface is added.

| Working directory | Command | Exit |
|---|---|---|
| `telephony` | `cargo fmt --all --check` | 0 |
| `telephony` | `cargo test --offline` | 0 |
| `telephony` | `cargo clippy --offline --all-targets -- -D warnings` | 0 |
| `telephony/symbian` | `cargo fmt --all --check` | 0 |
| `telephony/symbian` | `cargo arm --offline` | 0 |
| `telephony/symbian` | `cargo arm --offline --features radio-disabled --target-dir target/radio-disabled` | 0 |
| `telephony/symbian` | `cargo clippy --offline --release --target armv5te-none-eabi -Zbuild-std=core,alloc,compiler_builtins -Zbuild-std-features=compiler-builtins-mem -- -D warnings` | 0 |
| `telephony` | `git diff --check` | 0 |

Artifacts: `telephony/symbian/target/armv5te-none-eabi/release/libmodemd.a` and
`telephony/symbian/target/radio-disabled/armv5te-none-eabi/release/libmodemd.a`.
Hashes are retained in private `audio-artifacts.sha256`.


## Kernel checks

Builds used existing remote toolchain digest
`71f91f8ca42c5456859c3477092bef4f69842f6521ba1a4b5554ac7835895b32`,
without changing project pins. Both builds report **94 OK, 0 FAIL**, exit 0:

```sh
BOARD=qemu USERSIDE=0 sh baseport/arm64/tools/build-ekern.sh
BOARD=bonito USERSIDE=0 AUTOFASTBOOT=30 DTB=/bonito.dtb sh baseport/arm64/tools/build-ekern.sh
OUT=/work/out/ekern-qemu SMP=2 sh baseport/arm64/tools/run-qemu.sh 20 'probe.*PASS'
```

QEMU runner exit 0; required AArch32 exec/preemption/SWP/LDRD and kernel XTRAP,
tick and two-sleeper completion markers are present, with zero failure/panic
markers. This is a kernel-only smoke, not the full test suite. Raw `qemu-result.json`
and `qemu-smoke.log` were copied to the private artifact root.

Native actual-driver fake-MMIO tests passed, exit 0; artifacts at
`/private/tmp/neo-platform-buses-host/` (`test.cpp`, `test`, `result.log`). These
exercise invalid arguments before MMIO, cached initialization and valid transfers;
they do not prove physical register behavior.

The final reviewed Bonito image is copied to private `kernel-boot.img`, SHA-256
`239339ecab8b67265ff60bbda6f2a2645b324de0c34a2426d3cb549de94c96f6`.
It is kernel-only, has AUTOFASTBOOT=30 and leaves EMMC_C unset. The normal
installed phone ROM is not replaced by this candidate.

An initial source transfer was rejected by automatic approval review. A narrower
single-file retry, after public-origin and exact-payload inspection, was accepted.
Only the isolated snapshot was updated; the shared remote checkout was preserved.

## Phone RAM boot

The connected phone reported `product: bonito`, current slot `a`. Sandboxed USB
checks showed no device; the host check outside the sandbox found one. Ran:

```sh
python3 -I kernel/baseport/arm64/tools/phone.py run private/driver-support/20261110/kernel-boot.img --cmd drivers --log private/driver-support/20261110/phone-kernel.log --secs 10 --no-date
```

Exit **0**. SPMI reported `ok`, arbiter version `50000000`. Keys, touch, display
and RTC reported `ok`. Kernel probe and AArch32 user smoke markers passed on
all eight CPUs, with zero panic/fault/failure markers. `fastboot devices` then
returned exit 0 with one device, confirming recovery to fastboot. No flash command
was used; persistent storage was disabled for this image. ADSP/audio remained off,
as expected without MODEMD. Two identical RAM boots passed; the second also captures driver command stdout
in `phone-command.log` (the runner saves boot logs separately). Raw
`phone-kernel.log`, `phone-command.json` and `phone-result.json` remain
under the private artifact root. This does not validate the modified daemon.

Independent source review found no outstanding issues after correcting I2C base
validation, required-send retries and late radio packets after terminal failure.
All three component `git diff --check` commands exited 0; changed Markdown local
links resolve.

## Acceptance still required

A kernel-only RAM boot cannot validate the changed MODEMD: it requires a rebuilt
user ROM containing that executable. No-SIM/radio-disabled startup, injected
EFS/RMTFS/boot failures, DSP processing under IPC load and the established C6 call
sequence need explicit phone runs with the updated daemon. Synchronous HAL calls
still include firmware/storage/codec work and GLINK's intent wait; fixed polling
deadlines remove IPC starvation, not those execution budgets.

Future DMA/shared-chunk mappings, PCM/NeoAudio, amplifier protection, haptics,
sensors, cameras, power policy, networking and suspend remain pending. Do not
mark D1 or D3 complete based on these foundation checks.
