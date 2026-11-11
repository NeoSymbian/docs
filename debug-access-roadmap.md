<!-- SPDX-License-Identifier: Apache-2.0 -->
# Debug access roadmap: tasks in order

Written 2026-11-10. The design is [debug-access.md](debug-access.md): fshell over ECOMM and a second USB serial
port, with the kernel monitor kept. This file is the work list. Do **one task at a time, in order**.

**Decisions (owner, 2026-11-10):**
- **SSH is dropped.** The USB-SSH work was archived, not merged; see
  [remote-access.md.draft](remote-access.md.draft).
- **The useful parts come back task by task:** USB robustness, `e32` APIs, ECOMM/serial and the Mac client.
- **USB:** split our gadget into a controller core and function drivers now. A controller driver for Symbian's own
  USB client framework (`usbcc`, `usbc.ldd`) comes later (L1).

## Rules for every task

1. **Where (owner, 2026-11-10):** edit the existing checkouts directly; no worktrees. Commit each task separately
   in each repo. One PR per repo per task, rebased on current `main` just before merging. Build pins (`sources.lock`)
   last, after the source PR is merged.
2. **Not allowed:** SSH, ECM/Ethernet, PRNG or neolink code, and no `USBNET` switch.
3. **The archive is a source to copy from, never applied whole.** It is `private/codex-archive-20261110/` (see its
   `INDEX.md`). Its kernel patches are based on Codex's local `main`, not `origin/main`.
4. **Gates:**
   - each repo's gate from the workspace `CLAUDE.md` passes before a PR;
   - C++ host tests are built with `-fsanitize=address,undefined`;
   - evidence (commands, exit codes, hashes, raw logs) goes in `private/debug-access/<task>/<run>/`.
5. **Phone:**
   - RAM boots only (`fastboot boot`), built in isolated ZimaOS copies (`kernel-da`, `build-da`, a separate volume);
   - **never** `set_active`, `fastboot flash` or partition writes; slot a is the good install;
   - DA6 (T12) needs the owner's approval.
6. **When "Done when" fails, stop:** write what failed in `private/debug-access/<task>/RESULT.md` and report. No
   workarounds outside the task.
7. **Each finished task:** tick it below (task, PR, commit) and update [debug-access.md](debug-access.md) if a fact
   changed.

## Tasks

### T1. `e32`: file and timer APIs
- **Archive:** `e32-rs/commits/0001` (fs), `0002` (timer).
- **Files:** `e32-rs/crates/e32-sys/src/lib.rs`, `crates/e32/src/{fs,time}.rs`, `crates/neotest/src/lib.rs`, the
  Syborg CI workflow.
- **Done when:**
  - `cargo fmt --check`, `cargo clippy -p e32-sys -p e32 -- -D warnings`, `cargo test -p e32-sys -p e32` and
    `cargo arm` pass;
  - the Syborg CI run shows the new `neotest` cases passing.
- **Not in this task:** anything that uses the new APIs.

### T2. Split the USB gadget (no behaviour change)
- **Goal:** `sdm670_assp/qcom_dwc3_acm.cpp` (611 lines in `main`) becomes:
  - `qcom_dwc3.cpp`, the controller core: power and bring-up, the event ring, EP0 and Chapter 9, endpoint/DMA
    ownership, and a small **function interface** (a function supplies its descriptors, class requests and endpoint
    callbacks);
  - `a64_usb_acm_monitor.cpp`, the monitor's ACM function, through that interface.
- **Done when:**
  - the descriptors are byte-identical (dump them before and after);
  - `neo kernel qemu && neo qemu 60` is unchanged;
  - a bonito RAM boot gives `phone.py cmd log`, a SHA-256-checked `phone.py dump` and `phone.py shot` as before
    (a RAM image without `EMMC_C` starts the eMMC only on the monitor's `blk init`; run it before `dump`).
- **Not in this task:** any fix or new function.

### T3. USB robustness
- **Archive:** kernel `commits/0001` (DMA ownership, EP0/control recovery, policy, core tests), `0004` (quarantine
  recovery), `0002` (UTMI wrapper clock); only their non-ECM parts, ported onto the T2 structure.
- **Done when:**
  - the host tests pass with sanitizers;
  - bonito RAM: `usb cold 7` re-enumerates and the monitor answers again;
  - cable unplug and replug recovers;
  - Mac sleep then wake recovers;
  - a 5-minute monitor soak (`log` every 10 s) has no loss.

### T4. Link tracking and a faster monitor writer (re-scoped 2026-11-10)
- **Owner, 2026-11-10:** the archive's queue, boost and resume helpers served only ECM. The byte queue
  (`commits/0003` `a64_usb_queue.h` + test) moves to **T8**, with its user. A CPU boost on large transfers was tried
  and dropped: no gain, the limit was the writer's tick sleep.
- **Goal:** the core logs and counts link suspend/resume (a host asleep); the monitor's writer polls up to 200 us
  before it sleeps a tick.
- **Done when:** host tests pass; `shot`/`dump` speed measured before and after; the T3 checks pass again.

### T5. ECOMM and a second serial port on QEMU
- **Goal:**
  - build `ECOMM.LDD` (`kernel/eka/drivers/ecomm/d_comm.cpp`);
  - write a PL011 PDD for QEMU virt's **second UART** (`VIRT_UART1` at `0x09040000`,
    `symbian-qemu/qemu/hw/arm/virt.c:206`);
  - make `run-qemu.sh` add the second serial.
- **Archive:** `untracked.tar` (`a64_ecomm.cpp`, `a64_pl011_comm.cpp`, `a64_pl011_io.h`, `test_pl011_io.cpp`,
  `t_a64_serial.*`) and `uncommitted.patch` (`d_comm.cpp`, `qemu_virt.cpp`, `variant.conf`, `build-ekern.sh`,
  `run-qemu.sh`). Any `d_comm.cpp` change is a marked in-place Symbian edit (EPL-2.0 rules in `CLAUDE.md`).
- **Done when:**
  - `t_a64_serial` passes on QEMU (open, write, read back, signals, close);
  - the kernel console on UART0 is unchanged.

### T6. fshell builds and runs on QEMU's screen
- **Fork:** `NeoSymbian/fshell` (renamed from `oss.FCL.sf.os.fshell`; `main` `8536b2c` holds 7 patches, `master` is
  upstream).
- **Archive:** `build/commits/0001` (`fshell_components.py`, `platform.mmh`, `fshell_prepare.py`,
  `build-steps.sh`, pin), rebased onto current `main`; `build/uncommitted.patch` for `fshell_components.py`.
- **Steps:**
  - pin `oss.FCL.sf.os.fshell` in `sources.lock`;
  - map it to the `fshell` repo in `fetch.sh` (as `kernelhwsrv` maps to `kernel`);
  - build the text-shell configuration only.
- **Done when:**
  - fshell starts through `econs` on QEMU and runs `ls`, `hash` and `ps`;
  - every missing 2010 library is listed in this task's `RESULT.md`, and each is either added or turned off in
    `platform.mmh`.
- **Not in this task:** memoryaccess, TRK, c32, OST.

### T7. DA2: fshell over the second serial port, in CI
- **Archive:** `build/uncommitted.patch` (`ldr_builtin_devices.cpp`: `ecomm`, `euart1`).
- **Goal:**
  - fshell with `--console vt100busdevcons --console-title pdd=euart1,ldd=ecomm,port=1`;
  - a **GitHub Actions job** in `build` that boots QEMU and drives that port.
- **Done when:** the CI job runs `ls`, `hash` and a ymodem round trip of a binary file, with matching SHA-256, and
  checks a positive marker line. It runs on every build PR from then on.
- **fshell patches:** keep those this test needs; drop any whose test passes without it.

### T8. DA3: second ACM function on the phone
- **First:** read `GHWPARAMS3` (endpoint count) and `GTXFIFOSIZ0..n` on bonito through the monitor. Write the FIFO
  budget for two ACM functions at 512-byte HS bulk into `RESULT.md`. If it doesn't fit, stop.
- **Goal:** a second ACM function (interfaces 2/3) through the T2 function interface, plus an ECOMM PDD over it
  (`a64_debug_serial.h` from the archive). DTR maps to carrier. Its RX/TX buffering uses the archive's byte queue
  (`commits/0003` `a64_usb_queue.h`, host test with single-byte and partial-consume cases), moved here from T4.
- **Done when:**
  - the Mac shows two `cu.usbmodem` ports;
  - the monitor port still does `log`, `dump` and `shot`;
  - fshell answers on the other port (`screen`);
  - the T3 checks pass.

### T9. DA4: Mac client in `phone.py`
- **Archive:** kernel `commits/0005`, `0006`.
- **Goal:**
  - `sh [COMMAND]`: interactive, or one command with a nonce-delimited end record and its real exit status;
  - `push`/`pull`: one file each; written to a temporary name, checked by length and SHA-256, then renamed;
    `--overwrite` required to replace;
  - port discovery by USB interface; an exclusive lock on the shell port.
- **Done when:**
  - a binary file of all byte values, an empty file and an Armenian-named file with spaces round-trip with matching
    SHA-256;
  - an EXE pushed to `C:` runs from `sh`;
  - a failing command reports its error status.

### T10. SYSSTART starts fshell: Settings → Developer options → USB debugging
- **Input:** `private/debug-access/supervisor/supervisor-lib.patch`. **Not** the archived `NEOSSH.EXE` spawn.
- **Owner decision (2026-11-11), replacing "a non-development build has no fshell in its ROM":** every ROM carries
  fshell, and a Settings switch (off by default) turns it on, like Android's adb switch.
- **Done when:**
  - off: the Mac sees only the monitor port; on: the phone re-enumerates with fshell's port and SYSSTART runs fshell;
  - killed, fshell restarts with bounded backoff; off stops it and removes the port;
  - the UI never waits for it, and a ROM without fshell only logs it.

### T11. DA5: robustness run
- **Done when** each of these passes, while the monitor stays usable:
  - unplug and replug, a RAM reboot, Mac sleep and wake;
  - a long transfer while `sh` is used;
  - a full queue, disk full on `C:`, a hash mismatch;
  - a 5-minute soak.
  The results are in `RESULT.md`.

### T12. DA6: installed boot (owner approval first)
- **Goal:** normal-boot USB power (the T3 cold-power path). The policy for which builds expose fshell is decided
  (T10: every build, behind the USB debugging switch).
- **Done when:** a cold installed boot shows the monitor port, and both ports with USB debugging on.

## Later (each needs its own design first)
- **L1:** a DWC3 controller driver (PSL) for Symbian's USB client framework (`kernel/eka/drivers/usbcc`,
  `usbc.ldd`), so the standard `RDevUsbcClient` works; then usbman and MTP.
- **L2:** networking through Symbian's own stack (`oss.FCL.sf.os.networkingsrv`: ESOCK, TCPIP6) with an Ethernet NIF
  over a USB ECM/NCM function or Wi-Fi. The archived ECM descriptors are reference only.
- **L3:** fshell's memoryaccess LDD (`top`, `objinfo`, `fdb`), TRK and `runonphone`, OST traces, coredumps.

## Progress

| Task | State | PR / commit |
|---|---|---|
| T1 | done 2026-11-10: gates and Syborg CI (`fs_ops`, `timer_high_res`) pass | `e32-rs` #1, `82e3143` |
| T2 | done 2026-11-10: descriptors byte-identical, QEMU and bonito RAM boot unchanged | `kernel` #1, `96f60d6`; pin `build` #9 |
| T3 | done 2026-11-10: host test (sanitizers), `usb cold 7`, replug, Mac sleep/wake, 5-minute soak on bonito | `kernel` #2, `b7133e2`; pin `build` #9 |
| T4 | done 2026-11-10 (re-scoped): link tracking, writer spin (`shot` 9.6 → 2.1 s; `dump` 2.0 → 1.5 MB/s, open); T3 checks pass | `kernel` #3 |
| T5 | done 2026-11-10: interrupt-driven PL011 PDD + ECOMM; `test-serial-qemu.py` 4/4 (256-byte echo, `[serial] PASS`) | `kernel` #4 `326fffc`; `build` #11 |
| T6 | done 2026-11-10: 14 fshell components (+ `defcons`); on QEMU fshell runs `echo`, `ls`, `hash`, `ps`; econs `ReadCancel` fixed | `build` #12 `faf8f8c`; graphics #1 `9513de1` |
| T7 | done 2026-11-11: fshell on the second serial port, `test-fshell-qemu.py` 3/3 (ls, hash, ps, exit status, 64 KiB YMODEM round trip); the `build` CI job passes (run 42979250248) | `kernel` #6 `eecb462`; `build` #14 `0891bfd` |
| T8 | done 2026-11-11: `USBDEBUG=1` composite gadget (two IADs), debug ACM + ECOMM PDD `Comm.UsbAcm`; monitor `log`/`dump`/`shot`; fshell ls, hash, ps, status, 64 KiB YMODEM (~10 KB/s); `usb cold 7`, replug, Mac sleep/wake, 5-minute soak | `kernel` #7 `af9b3f8`; `build` #15 |
| T9 | done 2026-11-11: `phone.py sh`/`push`/`pull`, ports by USB interface, per-port lock; on the phone all byte values, an empty file and an Armenian name with a space round-trip (SHA-256), an EXE pushed to `C:\sys\bin` runs (exit 42), a failing command reports -12; 30 host tests | `kernel` #8 `277afef`; `build` #16 |
| T10 | done 2026-11-11 (re-scoped by the owner): Settings → Developer options → USB debugging (off by default) exposes fshell's port (HAL 0x4e04) and SYSSTART supervises fshell (1 s → 32 s backoff); on the phone 20/20 switches, kill → back in 1 s, the T9 checks, `usb cold 7`, a ROM without fshell. Two controller-restart fixes (events taken while halting; a 1 s disconnect) | `kernel` #9 `2a041d3`; `neoui` #4 `4beec4f`; `build` #17 |
| T11–T12 | not started | — |
