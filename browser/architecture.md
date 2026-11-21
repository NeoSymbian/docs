<!-- SPDX-License-Identifier: Apache-2.0 -->
# Browser architecture: repositories, forks, processes

Part of the [browser docs](../browser.md). The plan of 2026-11-15, with the platform prerequisites marked.

**As built (WB4–WB5):** Servo runs in its own process. `NEOWEB.EXE` (the neoui app, the Slint chrome, in the ROM)
starts `NEOWEBE.EXE` (Servo 0.8 + SWGL, Rust `std`, on C:) and talks to it over the Symbian server `NeoWebEngine`, with
frames in a shared chunk: [protocol.md](protocol.md). The plan below put the embedder inside `NEOWEB.EXE`; as built, the
app stays a `no_std` ARMv5TE neoui app and the engine is a separate `std` ARMv7 EXE.

## Repositories

### `NeoSymbian/browser` (new; created at WB0, 2026-11-16)

- `NEOWEB.EXE` (8.3 ROM name), the embedder:
  - ServoBuilder/WebView;
  - the WebViewDelegate (navigation, titles, new windows, dialogs);
  - prefs: no multiprocess, sandbox, JIT, GStreamer, WebGL/WebGPU/XR or sampler.
- `NeoUiRenderingContext`: Servo's `RenderingContext` over the software GL. Pixels are read back, RGBA → XRGB8888,
  into the neoui surface chunk, then DAMAGE.
- neoui event translation:
  - touch → Servo input events;
  - keys and the system keyboard → text. The neoui protocol has key events but no composition/preedit contract yet
    (`neoui-proto/src/ipc.rs`), so WB5 starts with direct Unicode input;
  - Back through `PAGE`'s `can_back` and `AppEvent::Back` (protocol 1.8 removed NAV);
  - a keyboard height change → a viewport resize.
- The browser chrome and every screen, on the neoui kit: [ui.md](ui.md). They live in `app/neoweb-core`
  (Apache), `app/neoweb-ui` (GPL, Slint) and `symbian/neoweb` (GPL, the EXE), and are built first on a stand-in
  `FakeEngine` (UI0–UI6); Servo plugs in behind the same `Engine` trait at WB4.
- Bundled fonts (DejaVu Sans covers Latin, Cyrillic and Armenian; Noto for more scripts) and Servo's resources.
- Target JSON `armv7a-neosymbian-eabi`:
  - ARMv7-A/ARMv8-AArch32 with NEON;
  - the **soft-float calling convention** (softfp, never `eabihf`), so calls into 2010 libraries stay compatible.
- Cross wrappers (GCC 14 + P.I.P.S. headers, CMake/meson cross files), the toolchain image recipe and CI.
- `exes.txt` and the staticlib for `build/rust/`.
- **Licences:** Apache-2.0 for our glue; the app crate becomes GPL-3.0 if it links `neoapp`/Slint (as neoui's apps do).
  **Open before WB2:** a GPL-3.0 app linked over P.I.P.S., whose libpthread is EPL-1.0. EPL-1.0 and the GPL are
  incompatible ([Eclipse FAQ](https://www.eclipse.org/legal/epl/faq/)). The GPL's System Libraries exception may
  cover it, or the app keeps the GPL code on its side of a process boundary. This is unresolved, not a shown
  violation.
  The glue crates talk to neoui through the Apache `neoui-proto`, so they stay reusable.

### What stays where it is

- EKA2 APIs → `e32-rs`.
- FP/NEON, stacks, VM primitives, entropy → `kernel`.
- P.I.P.S. fixes (`mprotect`, `poll`, pthread layout) → the `oss.FCL.sf.os.ossrv` fork.
- ROM integration and pins → `build`.

### Forks

**Pinning:**
- Rust crate forks: a git `rev` in browser's `Cargo.toml` and its committed `Cargo.lock`.
- The compiler/std fork, the mozjs/SpiderMonkey and Mesa/SWGL native trees: source revisions in `build/sources.lock`
  (Cargo.lock can't pin those).
- The toolchain image: its digest in `build/images.sh`.

Changes go upstream where upstream will take them; never to SymbianSource or Phorepoc.

| Upstream | Why we fork it |
|---|---|
| [rust-lang/rust](https://github.com/rust-lang/rust) | `std` for `target_os = "symbian"`: `library/` only, the compiler stays stock ([wb2-std.md](wb2-std.md#why-forks)) |
| [rust-lang/libc](https://github.com/rust-lang/libc) | P.I.P.S. bindings: the sizes and constants PIPSPROB measured |
| [servo/servo](https://github.com/servo/servo) | About 20–50 `cfg(target_os)` sites (*estimate*, from ~172 gates in 52 files): fonts (FreeType + a bundled list, no fontconfig), memory stats, the hang monitor, net/TLS provider, sandbox selection |
| [servo/mozjs](https://github.com/servo/mozjs) | `configure.py` triplet and OS, the VM and thread layer, interpreter-only |
| [servo/surfman](https://github.com/servo/surfman) | Likely: a Symbian backend (it's an unconditional dependency) |
| [tokio-rs/mio](https://github.com/tokio-rs/mio), [socket2](https://github.com/rust-lang/socket2) | Readiness over P.I.P.S. sockets (`select`); mio refuses an unknown OS |
| [WebRender](https://github.com/servo/webrender) (SWGL) **or** [Mesa](https://gitlab.freedesktop.org/mesa/mesa) | Software GL (see below) |
| Only if needed | aws-lc-rs / AWS-LC (or switch rustls to another provider), parking_lot, harfbuzz/freetype sys crates, backtrace, memmap2. getrandom takes a custom backend without a fork |

**Branch convention (adopted 2026-11-16; in the workspace fork rules):**
- Servo and most of these upstreams use `main` themselves.
- Upstream branches and tags stay untouched.
- Our integration branch is **`neosymbian`** wherever upstream owns `main`.
- The Symbian-era forks keep `main` as today.

## Architecture

```text
neoui events ──> NEOWEB.EXE (browser repo: embedder + Slint chrome)
                    │
                  libservo  (single process; no multiprocess, sandbox, JIT, GStreamer, WebGL)
                    │   └─> mozjs (SpiderMonkey 153, interpreter-only)
                  WebRender ──> SWGL (or Mesa softpipe)
                    │
                  RGBA → XRGB8888 copy ──> neoui surface chunk + DAMAGE

Rust std / libc (forks) ──> P.I.P.S. ──> RThread, RChunk, EKA2
Tokio → mio → P.I.P.S. sockets → ESOCK → NeoNet (Wi-Fi now, mobile data with C10)
```

- **`std`: the unix PAL over P.I.P.S.** The pattern is the one of 3DS (`horizon`, newlib), Vita, ESP-IDF, QNX and
  NuttX: a new `target_os` in the unix family on a libc, with native overrides where P.I.P.S. falls short. To audit:
  - pthread layouts, thread-local storage, paths, clocks, errno;
  - SIGPIPE, guard pages;
  - unsupported process calls.
- **`std` build and distribution:**
  - develop with a pinned nightly, the target JSON and a patched `library/` through `-Zbuild-std` (an isolated
    patched sysroot);
  - ship a toolchain built from the fork with `x.py` and linked with `rustup toolchain link`;
  - upstream tier 3 later, which needs named maintainers.
  - The existing `armv5te-none-eabi` `no_std` crates don't change.
- **Software GL:**
  - **SWGL first**: Firefox's software GL for WebRender, C++17, no LLVM. Unverified: whether it matches WebRender
    0.70.1 and the extra GL calls Servo makes. SWGL is not in Servo's dependency lock; Servo's own software context
    goes through surfman and ordinary GL (Mesa). So WB0 measures **both**: Mesa through the stock context, and SWGL
    behind our own `RenderingContext`. Otherwise a Mesa benchmark would leave the chosen path unproven.
  - **Mesa softpipe** is the fallback: wider GL, but Meson, C11, threads and a custom offscreen EGL.
  - llvmpipe would add LLVM code generation. OSMesa was removed in Mesa 25.1.
  - A WebRender display-list CPU rasterizer would be big upstream renderer work. Vello CPU in Servo is Canvas2D only.
- **Threads and stacks:**
  - Servo runs tens of threads even in one process: Rayon 4, Tokio 6, Canvas 3 and WebRender 4, plus services,
    script and workers.
  - The script thread asks for **8 MiB** of stack.
  - Pthreads map onto `RThread`; the kernel's stack limits must grow (WB1).
- **SpiderMonkey memory:**
  - it reserves 1 MiB-aligned GC chunks, and needs decommit and protection even without a JIT;
  - P.I.P.S.'s `mprotect` is a no-op, so the VM layer goes to EKA2 directly (disconnected `RChunk`s are the candidate);
  - the reservations must fit ~2 GiB of VA.
- **Networking:**
  - Tokio → mio → P.I.P.S. sockets → ESOCK → NeoNet;
  - rustls for TLS;
  - `load_web_resource` intercepts `neo:` pages and the captive-portal check.
- **Media:** a custom servo-media backend, `dummy` first. Later FFmpeg/dav1d software decode, software colour
  conversion and DevSound/MMF audio (not working on the phone yet; unverified).
- **Storage:** cookies, cache and local storage in `C:\private\<NEOWEB SID>\`.

## Platform prerequisites

**All met (2026-11-21).**

| Item | Status | Owner | Where |
|---|---|---|---|
| FP/NEON per thread at EL0: eager save of Q0–Q15, FPSR, FPCR; Qualcomm's EL2 does not trap AArch32 FP | ✅ WB1, 2026-11-17 | kernel | [smooth-ui.md](../neoui-shell/smooth-ui.md) S4, KRN-019, [wb1-kernel.md](wb1-kernel.md) |
| An ARMv7/v8 AArch32 softfp target, LDREX/STREX and 64-bit atomics (LDREXD/STREXD) | ✅ WB2a (`armv7a-neosymbian-eabi`, for NEOWEBE); the ARMv8 user side is US2 (C++, done) and US4 (Rust, next) | e32-rs + browser | [wb2-std.md](wb2-std.md), [user-side-smp.md](../user-side-smp.md) |
| The phone's RAM below 4 GiB (above it needs a 64-bit `TPhysAddr`) | ✅ M4.3 | kernel | the RAM map under [roadmap.md](../roadmap.md) M4 |
| Stack limits for 8 MiB threads, and tens of threads per process: 16 MiB cap, 128 threads tested | ✅ WB1 | kernel | [wb1-kernel.md](wb1-kernel.md) |
| Reserve/align/decommit for SpiderMonkey: disconnected chunks; no protect call needed | ✅ WB1, WB3 | kernel + ossrv | [wb3-js.md](wb3-js.md) |
| `poll` (over `select`, new in libc.dll), pthread and clock fixes; `mprotect` not needed (no JIT) | ✅ WB2c, WB2d | ossrv | [wb2-std.md](wb2-std.md) |
| An entropy source for getrandom and TLS: IRQ timing everywhere, the SoC PRNG on SDM670 | ✅ WB1 | kernel | [wb1-kernel.md](wb1-kernel.md) |
