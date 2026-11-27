<!-- SPDX-License-Identifier: Apache-2.0 -->
# WB0: the host proof (and WB0p)

Part of [Apps](../README.md) · Status: done · Updated: 2026-11-21 · Neighbours: [the browser hub](README.md)

**Status:** ✅ WB0 GO 2026-11-16 (QEMU; results in browser `wb0/results/2026-11-16/`) · ⏸ WB0p deferred (no ARM board, owner 2026-11-16); the Pixel now gives the numbers it wanted: scrolling 15–18 fps ([WB5](wb5-input-chrome.md)), local pages in about 8 s ([WB4](wb4-servo.md)).

## Scope

| Stage | Work | Gate | Estimate (PM) |
|---|---|---|---:|
| WB0 host proof (emulated) | Create `browser`. Build Servo 0.8.0 for armv7 Linux; run it JIT-less with software GL (Mesa softpipe and SWGL) at 1080×2160 under QEMU, capped at 512 MiB and 1 GiB. Plan below | For the 10 sites below: function, RSS/PSS, peak VA (and a 2 GiB `ulimit -v` run), threads, stack peaks, a 30-minute soak. QEMU timings are recorded but don't gate | 0.5–1 |
| WB0p speed gate | The WB0 harness on a physical ARM board (AArch32 userland). Deferred: no board yet (owner, 2026-11-16) | Cached render < 5 s, scrolling ≥ 15 fps | — |

## Gates and kill criteria

- **The WB0 site set:** Wikipedia, DuckDuckGo, GitHub, Stack Overflow, BBC, a WordPress blog, TodoMVC, Gmail, Google
  Docs and YouTube. For each, record a workflow (read, scroll, search, sign in, type), not just "it renders".
- **Performance gates:** a cached reading page renders in under 5 s; scrolling holds at least 15 fps on real hardware.
  QEMU timings don't count for performance.
- **Kill or re-scope (back to WPE, then Ladybird) if:**
  - the required sites fail in upstream Servo;
  - routine RAM goes over 1 GiB;
  - the mappings don't fit the private VA;
  - CPU rendering misses the gates;
  - interpreter-only JS is unusably slow.

WB0 changes nothing on the phone. It is the cheap go/no-go before the kernel and std work.
- **Emulated runs** (QEMU on the Mac) check function and memory (WB0).
- **The performance gate** (WB0p) needs a physical ARMv8 board running AArch32 userland (e.g. a Raspberry Pi 4 with
  armhf; a Pi 5 works with a 64-bit kernel). The owner chose emulation only for now (2026-11-16), so WB0p waits for
  a board.

## Result (2026-11-16): GO

Quick verdict ([NeoSymbian/browser `wb0/results/2026-11-16/summary.md`](https://github.com/NeoSymbian/browser/blob/main/wb0/results/2026-11-16/summary.md)):
Servo 0.8.0 on 32-bit ARM, JIT off, SWGL, 1080×2160 at DPR 2.75, in QEMU.

**Sites:**
- 5 of 10 load and render: Wikipedia, GitHub, Stack Overflow, TodoMVC (full workflow: typing and taps), YouTube.
- The other 5 (DuckDuckGo, BBC, WordPress, Gmail, Docs) all hit **one bug**: the web-font sanitiser (OTS, via
  `fontsan`) asserts `(Tell() & 3) == 0` on 32-bit. It must be fixed before WB4.

**Memory:**
- 37–210 MiB per page, with 36–129 threads.
- Servo's own share is ~45 MiB; the rest is software-GL texture memory, filled as the page is rasterised. It isn't a
  leak.

**SWGL works:**
- pixel-identical to Mesa softpipe, with a third of the memory and ~10× faster frames (emulated);
- one Servo patch: no picture-cache quad clears on software WebRender, as in Gecko.

**Design rule:** the embedder must pace scroll input to painted frames. Input faster than rendering piles up
WebRender work (1 GiB within minutes in emulation).

**Not measured yet:** speed (WB0p, real hardware), full per-site workflows, soaks.

**M4.3 (RAM) is done:** the phone has ~2 GB.

## Plan (2026-11-16)

Checked against Servo v0.8.0 (a Codex pass plus spot checks); items marked *unverified* are WB0's first gates.

- **Build:** in a Debian trixie arm64 container on the Mac, cross to `armv7-unknown-linux-gnueabihf` with plain Cargo
  and Rust 1.99.1 (Servo's `rust-toolchain.toml`). `mach` rejects cross targets other than Android and OHOS
  ([build_target.py](https://github.com/servo/servo/blob/v0.8.0/python/servo/platform/build_target.py)).
  - Features: `--no-default-features --features bundled,baked-in-resources,subtlecrypto`. This drops GStreamer,
    WebGL/WebGPU/XR, jemalloc, multiprocess and `js_jit` (mozjs then configures `--disable-jit`).
  - mozjs_sys 153.6.0-1 has no armv7 Linux prebuilt: `MOZJS_FROM_SOURCE=1`, cross `CC_/CXX_/AR_` variables and
    cross pkg-config. *Unverified* until it builds.
  - Linux needs fontconfig and FreeType; servoshell still links X11/Wayland even headless.
- **Interpreter only:** no `js_jit` at build time, plus the prefs `js_disable_jit=true` and `js_baseline_*`,
  `js_ion_enabled`, `js_native_regex_enabled`, `js_wasm_enabled` set false. Evidence: mozjs's configure log and the
  "Disabling JIT" start-up message.
- **Stock software GL:** headless servoshell uses `SoftwareRenderingContext` over surfman, which falls back to Mesa's
  surfaceless EGL (no OSMesa, no GBM). We force `GALLIUM_DRIVER=softpipe` (no code generation, closest to the phone)
  and record llvmpipe once for reference.
- **SWGL:** Servo locks WebRender 0.70.1, which is servo/webrender
  [`d399b904`](https://github.com/servo/webrender/commit/d399b904fdce7bab553fb6514204790155a7fb07); SWGL builds there
  standalone (C++ and `glsl-to-cxx`). Our `RenderingContext` must also hand Servo a glow handle, which SWGL lacks, so
  WB0 builds a name → SWGL table. It is time-boxed to 10 days; if SWGL fails, WB0 records the missing GL calls and SWGL
  stays a WB4 risk.
- **Harness:** `neoweb-host` in the `browser` repo is a headless embedder on Servo's public API. It drives both GL
  paths with identical geometry, real touch and key events, and frame-accurate timing, and it is the code
  `NEOWEB.EXE` grows from.
- **Emulator:** `qemu-system-arm -M virt,highmem=off -cpu cortex-a15 -smp 4` with a 2 GiB Debian armhf guest (our
  `symbian-qemu` build has `virt`), shown over VNC.
  - Memory is read in the guest (`smaps_rollup`, `VmPeak`, the task count). qemu-user's numbers include the emulator
    and aren't valid.
  - The caps are cgroup v2 `memory.max` 512M/1G with swap off: the browser's budget, not the machine's.
- **Stacks:** an `LD_PRELOAD` `pthread_create` interposer paints each stack and reports the high-water mark. It runs
  apart from the memory runs (painting commits pages) and is checked first on known recursion depths.
- **Accounts:** Gmail and Docs use a throwaway account whose credentials come from the environment at run time and
  are never committed. YouTube plays no media until WB7.
