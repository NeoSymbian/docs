<!-- SPDX-License-Identifier: Apache-2.0 -->
# WB3: SpiderMonkey on NeoSymbian

Part of [Apps](../README.md) · Status: done · Updated: 2026-11-25 · Neighbours: [the browser hub](README.md)

**Status:** ✅ done 2026-11-19 · [browser#7](https://github.com/NeoSymbian/browser/pull/7), [mozjs#1](https://github.com/NeoSymbian/mozjs/pull/1)

## Scope

| Stage | Work | Gate | Estimate (PM) |
|---|---|---|---:|
| WB3 mozjs shell | SpiderMonkey interpreter-only, as an EXE | JS test scripts, GC stress, threads, a clean OOM on the phone | 3–6 |

Written 2026-11-19. This is the working doc for [the browser hub](README.md)'s stage **WB3**: Servo's JavaScript engine,
SpiderMonkey, as a NeoSymbian EXE, before Servo itself (WB4) depends on it.

**The gate (above):** JS test scripts, GC stress, threads and a clean out-of-memory, all on the phone.

**✅ Passed 2026-11-19** on QEMU and on the Pixel 3a XL: `JSSHELL.EXE` reports `jssuite: 9 ok, 0 failed`.

## What was built

| Part | Where | What |
|---|---|---|
| The engine | [NeoSymbian/mozjs](https://github.com/NeoSymbian/mozjs) (mozjs#1 into `neosymbian`) | SpiderMonkey 153 (mozjs 0.26.13 / mozjs_sys 153.6.0-1, Servo 0.8.0's). Interpreter only (`--disable-jit`), no Intl (`--without-intl-api`; WB4 decides how Servo gets Intl), libz-rs. The SpiderMonkey changes are also kept as `etc/patches/0056-symbian.patch` |
| The C/C++ SDK | browser `tools/symbian-sdk.sh` | Arm GNU 14.2.1 for macOS, the device headers (P.I.P.S., e32), and the `armv8-symbian-{gcc,g++,cpp}` wrappers (named `armv7-symbian-*` until US5, 2026-11-25) that cc-rs and mozbuild call |
| The C++ runtime | browser `std/cxxrt` | What libstdc++ and SpiderMonkey need at run time and P.I.P.S. lacks |
| The shell | browser `std/jsshell`: `JSSHELL.EXE`, UID 0xE0007006, 6.2 MB | Rust over the `mozjs` crate (Servo's path). The test suite, `-e CODE`, script files |
| A C++ smoke test | browser `std/cxxsmoke`: `CXXSMOKE.EXE`, UID 0xE0007007 | Static guards, `thread_local`, atomics and NEON from C++ in a Rust EXE |

### The target

C++ is built for the Rust target `armv8a-symbian-eabi` since US4 (2026-11-25; `armv7a-symbian-eabi`, WB2a, until then):
- ARMv8-A AArch32 + NEON with soft-float calls (`-march=armv8-a+crc+crypto -mfloat-abi=softfp -marm`);
- `-mword-relocations`, and never `-fPIC`: an E32 image takes only whole-word absolute relocations;
- 32-bit enums, a 2-byte `wchar_t`, `-fno-exceptions`.

The wrappers put the target's flags last, so they win over any guesses from cc-rs or configure.
- **Headers:** libstdc++'s headers sit over P.I.P.S.'s C headers; newlib's are never seen. The few clashes are fixed
  by small compat headers in browser `symbian/sdk-compat/`.
- **Build's Symbian prefix header** (`IMPORT_C`, `Int64`) is forced in for every compile except a pure preprocess
  (`-E`). There it would land in SpiderMonkey's self-hosted JavaScript.
- **A Mac link:** configure's link checks run against `libneostubs.a`, weak stubs for every libc, libm, libpthread
  and euser export. The real link into an E32 image happens on the build machine in `build_rust_exe.py`, as for
  every Rust EXE.

### The port: a new OS, `Symbian`

mozbuild knows only the operating systems it lists, so it gets one more: OS and kernel `Symbian`
(`__symbian__`) with the triplet `arm-unknown-symbian`. Every change is behind `__symbian__` or
`OS_ARCH == "Symbian"`, so no other target changes.

| Area | On NeoSymbian |
|---|---|
| GC memory | `gc/MemorySymbian`: one disconnected `RChunk` reserves up to 1 GiB of address space at start (WB1 proved disconnected chunks). Pages are committed and decommitted one at a time, tracked in a page bitmap. P.I.P.S. `mmap` is not used |
| Stack, random numbers, threads | `mozglue/misc/SymbianOS`: the stack base from `RThread::StackInfo`, `Math::Random`, `pthread_create` with a cleanup stack per thread (P.I.P.S. needs one) |
| Locks and clocks | No `pthread_rwlock` in P.I.P.S.: a mutex instead (correct, less concurrent). Condition variables on `CLOCK_REALTIME` (no `condattr_setclock`); `CLOCK_MONOTONIC` works since WB2c |
| Logging | `MozSymbianLog` writes to the debug port (P.I.P.S.'s stderr doesn't reach the serial log); used only on failures |
| Leftovers | No `mprotect`/`mmap` callers; `unsetenv` returns `void`; double-conversion parses ASCII without the locale |

**No user protect call is needed** ([WB1](wb1-kernel.md) asked): the interpreter never makes memory executable or
read-only.

### The C++ runtime (`std/cxxrt`)

libstdc++ is used **header-only** (`_GLIBCXX_EXTERN_TEMPLATE 0`), and `cxxrt` brings what is left:
- `__cxa_guard_*`, `__emutls_get_address`;
- `std::__throw_*` (an error message, then abort);
- `std::this_thread::__sleep_for`;
- the stack protector;
- array `new`/`delete`;
- `__aeabi_unwind_cpp_pr1/pr2` stubs, so the unwinder isn't pulled in.

The red-black tree, list and hash table pieces come from libstdc++.a's **ARMv5TE multilib**. The Thumb/ARMv7
multilib's MOVW/MOVT relocations can't go into an E32 image.

### The shell (`std/jsshell`)

- **Natives:** `print`, `gc`, `gcChunks`, plus a JS prelude of assertions.
- **The job queue:** mozjs's glue job queue (`CreateJobQueue`). SpiderMonkey's internal queue must be chosen before
  self-hosting starts, which the `mozjs` crate doesn't allow.
- **Threads:** one `JSContext` per thread. Each extra runtime is a child of the main one and runs on its own Rust
  thread.

## Results

| Test | QEMU (VM) | Pixel 3a XL |
|---|---|---|
| types, objects, collections, text, async | ok: 33, 45, 49, 257, 22 ms | ok: 5, 9, 21, 97, 4 ms |
| gc_stress (churn with `gc()`, WeakRef, FinalizationRegistry; the chunk count must come back) | ok: 8.5 s; 6 chunks after a shrinking GC | ok: 4.8 s; 6 chunks |
| threads (4 runtimes × 5 scripts at once) | ok: 3.4 s | ok: 0.34 s |
| oom_gc_heap (GC heap capped; allocate until it fails) | ok: out of memory, usable afterwards | ok |
| oom_native_heap (until `malloc` fails at the EXE's `heap=`) | ok: out of memory, usable afterwards | ok |

**How to run it:**
- **Build on the Mac:** `cargo sym -p jsshell` in browser `std/` (it needs `tools/symbian-sdk.sh` once, and GNU make
  as `MAKE`). SpiderMonkey builds from source.
- **The ROM:** put `libjsshell.a` and its `exes.txt` line into build's `rust/`.
- **On the Pixel:** a UI ROM with `ROFS=1 EMMC_C=1 USBDEBUG=1`, then `phone.py sh jsshell`. Without `EMMC_C=1`, C: is
  empty, so USB debugging is off and there is no shell.

## Gaps and next

- **No JIT** (as planned): Servo's JS runs in the interpreter. The baseline JIT would need executable memory, a
  protect call, and SpiderMonkey's ARM back end with word relocations only.
- **No Intl.** `Intl`, locale-aware `toLocaleString` and `String.prototype.normalize` are missing until WB4 settles
  ICU.
- **Not measured yet:** start-up time and peak committed memory under a real page. WB4 measures them with Servo.
- **WB4,** Servo in `NEOWEB.EXE`, is done (2026-11-20, [wb4-servo.md](wb4-servo.md)).
