<!-- SPDX-License-Identifier: Apache-2.0 -->
# A web browser on the Pixel 3a XL

Written 2026-11-15. This is the design and estimate for a native web browser (roadmap U3). Nothing here is built yet.
The browser tile in the dock still opens a mock screen (`neoui/ui/screens/browser.slint`), and Wi-Fi captive
portals wait for a real browser (`neoui/symbian/src/wifi.rs:52`).

**The app's screens and their phases are in [browser-ui.md](browser-ui.md)** (2026-11-17), from the canvas's Browser v2
page. This doc is the engine plan.

**Sources:**
- a read of our kernel, e32-rs, neoui, neolink, legacy and build trees;
- the sibling N8 experiments in `~/WS/Symbian` (LiveTo, NeoLite, NeoNetSurf, NeoWeb);
- upstream Servo v0.8.0, mozjs-sys 153.6.0-1, WebRender 0.70.1 and surfman 0.14.0;
- three Codex research passes (candidate survey, Servo port, Servo integration).

Version numbers and dates are as of 2026-11-15. Figures marked *estimate* are engineering judgement, not
measurements.

## Decisions (owner, 2026-11-15)

- **Native only.** The browser engine runs on the phone. Remote rendering (LiveTo, WRP) is not the product; LiveTo
  stays the N8's tool.
- **Works anywhere:** home Wi-Fi, other networks, mobile data. That means TLS on the phone and no home-server dependency.
- **Full scope, eventually:** reading sites, forms and logins, JS web apps, media.
- **Engine: [Servo](https://servo.org).** There is **no interim light browser**: effort goes into the full engine.
- **A separate repository, `NeoSymbian/browser`, for the integration.** Servo and its dependencies are forked only
  where a change is needed.

## Where the platform stands

| Need | Today | Where |
|---|---|---|
| Sockets | NeoNet (smoltcp: DHCP, DNS, TCP, UDP; IPv4) and the 2010 `RSocket` API over it (W5a) | [wifi.md](hardware/wifi.md) W5, W5a |
| TLS, HTTP client | **none** (only hand-written `GET /generate_204`) | `neoui/symbian/src/wifi.rs:439` |
| Hardware FP/NEON at EL0 | **off**: the per-thread FP save/restore hooks are empty | [kernel-issues.md](kernel-issues.md) KRN-019, [smooth-ui.md](neoui-shell/smooth-ui.md) S4 |
| Atomics | **none**: user code is ARMv5TE, which has no CAS, so Rust has no `Arc` | `e32-rs/crates/e32/src/cs.rs` |
| RAM | **~87 MB** on `main` for the kernel and the whole user side (`A64_BOOT_RAM_END`). M4.3 is in progress: kernel branch `ram-map` (`640aa2ff`, 2026-11-15) takes the RAM banks from the bootloader's DTB, below 4 GiB (`KPhysTop`) | `kernel/baseport/arm64/bonito_variant/variant.conf:8`, `kernel/kernel/eka/kernel/arm64/a64boot.cpp` |
| Address space | ~2 GiB private VA per process (flexible model) | `kernel/kernel/eka/include/memmodel/epoc/flexible/arm64/mmboot.h` |
| Thread stacks | **1 MiB per thread, 2 MiB per process** | `kernel/kernel/eka/memmodel/epoc/flexible/mmu/mmu.cpp:300` |
| Executable memory | Writable+executable chunks exist (a JIT is possible later) | `kernel/kernel/eka/memmodel/epoc/flexible/mprocess.cpp` |
| Rust `std` | **none**: all user Rust is `no_std` + alloc on `armv5te-none-eabi` | `e32-rs/rust-toolchain.toml` |
| libc | P.I.P.S./Open C sources (libc, libm, libpthread), today only registered for SVG-T. **`mprotect` does nothing**; `poll` is unverified | `legacy/components.py:188`; `ossrv` `genericopenlibs/openenvcore/libc/src/mmap.cpp` |
| Surface and input | Each app gets a shared XRGB8888 chunk + DAMAGE, and 16-byte touch/key events | `neoui/crates/neoui-proto/src/ipc.rs` |
| Fonts and images | Slint bakes SDF glyphs (no shaping, no fallback); PNG only | `neoui/Cargo.toml` |
| GPU | No driver; everything renders on the CPU | [smooth-ui.md](neoui-shell/smooth-ui.md) S6 |

Any modern engine needs hardware floats, real atomics, far more RAM, bigger stacks, a libc that behaves, and a TLS
stack. Those are platform work, not browser work. Every candidate below except the tiny ones needs them.

## All candidates

Effort is in person-weeks (pw) to a first useful integration on this platform, not to production quality. RAM is
the working set for useful browsing, in MiB. Both are *estimates*.

### Full engines

| Candidate | Licence | Effort | RAM | Verdict |
|---|---|---:|---:|---|
| **[Servo](https://github.com/servo/servo) 0.8.0** | MPL-2.0 | see the stages | 200–800+ | **Chosen.** Rust, an embedding API, a single-process mode. Needs `std`, SpiderMonkey and software GL |
| [WPE WebKit](https://wpewebkit.org/) 2.54 | LGPL/BSD | 150–350+ | 200–1000+ | **The fallback** if we commit to a POSIX layer. Mature compatibility, CPU Skia; but GLib/GIO, libsoup and subprocesses |
| [Ladybird](https://github.com/LadybirdBrowser/ladybird) | BSD-2 | 100–250+ | 200–1000+ | Second fallback. CPU Skia, its own LibJS (an interpreter). C++23 **and Rust**, multi-process by design, pre-alpha |
| [Chromium / Content Shell](https://chromium.googlesource.com/chromium/src/) | BSD + deps | 300–700+ | 300–1500+ | No. Too big a port for the OS, IPC, sandbox and V8 |
| [Gecko](https://firefox-source-docs.mozilla.org/) (GeckoView is Android-only) | MPL-2.0 | 200–450+ | 250–1200+ | No. Needs a new platform embedding |
| [Goanna / UXP](https://www.palemoon.org/) | MPL + branding | 100–250+ | 150–700 | No. Still a big port, and weaker on today's sites |
| QtWebKit 2.x (Qt 4.7/4.8 for Symbian) | LGPL | 20–60 | 50–250 | No. Ran on Symbian once; obsolete and insecure |
| 2010 S60 WebKit / BrowserNG ([browserui](https://github.com/SymbianSource/oss.FCL.sf.app.browserui), [mw.web](https://github.com/SymbianSource/oss.FCL.sf.mw.web)) | EPL/LGPL/BSD | 10–40 | 40–200 | No. The source exists (NeoWeb got JavaScriptCore to compile), but it's a 2010 engine |
| [Flow](https://www.ekioh.com/flow-browser/) (Ekioh) | proprietary | ? | 150–600 | No. Needs a vendor deal |
| [Ultralight](https://ultralig.ht/) 2.0 | proprietary | ? | 100–500 | No. Has a CPU renderer, but no ARMv5/Symbian SDK and commercial source |
| [Sciter](https://github.com/c-smile/sciter-js-sdk) | proprietary | ? | 20–150 | No. An app-UI engine, not a web browser |

### Light engines

| Candidate | Licence | Effort | RAM | Verdict |
|---|---|---:|---:|---|
| [NetSurf](https://www.netsurf-browser.org/) 3.11 + Duktape | GPL-2.0-only | 8–20 | 20–100 | Not chosen. The best small browser (framebuffer frontend, forms, cookies); limited CSS and ES5 JS. GPL-2.0-only can't share a binary with GPL-3.0 Slint. A port exists for the N8: `~/WS/Symbian/NeoNetSurf` |
| [litehtml](https://github.com/litehtml/litehtml) + QuickJS | BSD-3 / MIT | 6–16 | 15–80 | Not chosen (no interim browser). Permissive; the DOM, forms and navigation are ours to write. A port exists for the N8: `~/WS/Symbian/NeoLite` v0.3.0, with a Mac renderer `neolite_shot` |
| [Blitz](https://github.com/DioxusLabs/blitz) (Stylo + Taffy + Parley + Vello CPU) | Apache/MIT | 25–70+ | 30–200 | No. Needs `std` too, and has no JS or full interactivity |
| [Dillo](https://dillo-browser.github.io/) 3.2 | GPL-3.0 | 12–30 | 10–60 | No. FLTK/Unix assumptions, no JS |
| Links, ELinks, Lynx (GPL); w3m (MIT) | various | 5–20 | 5–40 | No. Terminal browsers |
| robinson/Kosmonaut-class toy engines | various | 20–100+ | 5–50 | No. Teaching engines |
| A Gemini/Gopher/text reader | ours | 2–6 | 2–20 | No. A different ecosystem, not the web |

### Old .sis browsers (through [legacy.md](legacy.md))

| Candidate | Verdict |
|---|---|
| Opera Mobile 10/11/12 (Presto) | No. Proprietary, and modern CSS/JS/TLS fail |
| Opera Mini 4–8 | No. Needs Opera's servers (whether they still work is unverified); J2ME needs a Java runtime |
| UC Browser, BOLT | No. Proprietary, and they depend on servers |
| Star Browser (Qt), the stock S^3/Anna/Belle browser | No. Old QtWebKit or firmware DLLs |

Even running them needs legacy L4+ (installing .sis at runtime), IAP records (ESOCK has none yet) and a FEP.

### Remote rendering (ruled out by the owner; listed for completeness)

| Candidate | Note |
|---|---|
| LiveTo (ours, `~/WS/Symbian/LiveTo`: Chromium screencast, JPEG + ACK, touch/text/audio, pairing) | 2–6 pw for a neoui client. Plain TCP, LAN only |
| [WRP](https://github.com/tenox7/wrp) | Already running on ZimaOS; image maps |
| [Browservice](https://github.com/ttalvitie/browservice) | CEF streaming; unmaintained since 2026-09 |
| Opera-Mini-style server layout (OBML-like) | 20–60+ pw; a protocol of our own |
| [Carbonyl](https://github.com/fathyb/carbonyl), [Browsh](https://github.com/browsh-org/browsh) | Chromium/Firefox drawn as terminal output |
| [Neko](https://github.com/m1k1o/neko), [KasmVNC](https://github.com/kasmtech/KasmVNC), an RFB client | Needs a native decoder client |
| Video streaming (H.264/AV1) | Software decode costs battery |
| Hybrids (server readability + a local renderer; local engine + remote JS) | The first is 4–12 pw; the second is a distributed engine and a poor investment |

### JavaScript engines (for reference; Servo brings SpiderMonkey)

| Engine | Licence | Fit |
|---|---|---|
| SpiderMonkey (mozjs) | MPL-2.0 | **Servo's.** Can run interpreter-only (`JS_CODEGEN_NONE`) |
| [QuickJS](https://bellard.org/quickjs/) / [QuickJS-ng](https://github.com/quickjs-ng/quickjs) | MIT | The best small modern interpreter (NeoLite uses it) |
| [Duktape](https://duktape.org/) 2.7 | MIT | ES5; NetSurf's |
| [Boa](https://github.com/boa-dev/boa), [Nova](https://github.com/trynova/nova), [Kiesel](https://kiesel.dev/) | MIT/MPL | Rust/Zig interpreters; none is drop-in `no_std` |
| [JerryScript](https://github.com/jerryscript-project/jerryscript), [mquickjs](https://github.com/bellard/mquickjs) | Apache/MIT | Embedded; language subsets |
| [Hermes](https://github.com/facebook/hermes), V8 | MIT/BSD | Large C++ ports |

### TLS

| Stack | Note |
|---|---|
| [rustls](https://docs.rs/rustls) 0.23 | Servo's (with aws-lc-rs as the crypto provider). Needs `Arc`; the provider is the porting question |
| [Mbed TLS](https://github.com/Mbed-TLS/mbedtls) | The pragmatic C choice (TLS 1.2/1.3) |
| [embedded-tls](https://github.com/embassy-rs/embedded-tls) | TLS 1.3 for `no_std`; verification is ours to finish |
| [BearSSL](https://bearssl.org/) | Small; TLS 1.2 only |
| 2010 Symbian TLS | No modern protocol or ciphers; a legacy interface only |

## Why Servo

- **Rust**, like the rest of our user side.
- **MPL-2.0** is file-level copyleft. It can sit next to our Apache-2.0 code, and it can be combined with GPL-3.0
  Slint because MPL-2.0 lists the GPL as a secondary licence. That holds unless a file is marked
  "Incompatible With Secondary Licenses", so audit the pinned dependencies for that marking
  ([MPL FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/)). The MPL source and notice duties stay either way.
- **Embedding API** (`servo` crate):
  - it provides `ServoBuilder`, `WebViewBuilder`, `WebView` and `WebViewDelegate`;
  - `RenderingContext` is a **public trait** that the embedder implements;
  - [Slint has a Servo example](https://github.com/slint-ui/slint/tree/master/examples/servo).
- **Single process:** turn off the `multiprocess` feature **and** enable `ipc-channel/force-inprocess`. Turning the
  feature off alone still compiles ipc-channel's platform backend, which has no Symbian arm. That suits EKA2, which
  has no `fork`.
- **Active:** monthly releases. Servo's 2026 reports say Google Photos works, and Maps/OpenStreetMap render with
  interaction problems. **Unverified:** the current WPT score (79% was the end-of-2024 figure), and Gmail, Docs and
  YouTube end to end.
- **The fallbacks are WPE** (stronger compatibility, if we build a POSIX layer) **and then Ladybird.** WB0 decides
  whether Servo stays.

**Risks:**
- web compatibility;
- memory: the one-tab RSS is not measured; one full-screen 1080×2160 surface alone is 8.9 MiB (the Gestures app area 1080×2037: 8.4 MiB);
- CPU rendering speed through software GL;
- ARM32 at run time: Servo's CI builds `armv7-linux-androideabi` but runs nothing on it;
- the std port's size.

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
- The browser chrome and every screen, on the neoui kit: [browser-ui.md](browser-ui.md). They live in `app/neoweb-core`
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
| [rust-lang/rust](https://github.com/rust-lang/rust) | `std` for `target_os = "symbian"`: `library/` only, the compiler stays stock ([browser-std.md](browser-std.md#why-forks)) |
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

| Item | Owner | Where it is planned |
|---|---|---|
| ~~FP/NEON per thread at EL0~~ **done (WB1, 2026-11-17):** eager save of Q0–Q15, FPSR, FPCR; Qualcomm's EL2 does not trap AArch32 FP | kernel | [smooth-ui.md](neoui-shell/smooth-ui.md) S4, KRN-019 |
| An ARMv7/v8 AArch32 softfp target, LDREX/STREX and 64-bit atomics (LDREXD/STREXD) | e32-rs + browser | smooth-ui S4 |
| ~~The phone's RAM below 4 GiB~~ **done** (above it needs a 64-bit `TPhysAddr`) | kernel | M4.3, the RAM map under [roadmap.md](roadmap.md) M4 |
| ~~Stack limits for 8 MiB threads, and tens of threads per process~~ **done (WB1):** 16 MiB cap, 128 threads tested | kernel | WB1 |
| Reserve/align/decommit for SpiderMonkey: **works with disconnected chunks (WB1 test)**; a protect call only if WB3 needs it | kernel + ossrv | WB1, WB3 |
| `mprotect`, `poll` (or a mio `select` backend), pthread fixes | ossrv | **new** |
| ~~An entropy source for getrandom and TLS~~ **done (WB1):** IRQ timing everywhere, the SoC PRNG on SDM670 | kernel | WB1 |

## Stages

Estimates are in person-months (PM), *estimates*. A stage starts only when its gate inputs exist.

| Stage | Work | Gate | PM |
|---|---|---|---:|
| **WB0** host proof (emulated) | Create `browser`. Build Servo 0.8.0 for armv7 Linux; run it JIT-less with software GL (Mesa softpipe and SWGL) at 1080×2160 under QEMU, capped at 512 MiB and 1 GiB. Plan below | For the 10 sites below: function, RSS/PSS, peak VA (and a 2 GiB `ulimit -v` run), threads, stack peaks, a 30-minute soak. QEMU timings are recorded but don't gate | 0.5–1 |
| **WB0p** speed gate | The WB0 harness on a physical ARM board (AArch32 userland). Deferred: no board yet (owner, 2026-11-16) | Cached render < 5 s, scrolling ≥ 15 fps | — |
| **WB1** kernel ✅ 2026-11-17 | smooth-ui S4 (kernel part), M4.3, stack limits, VM primitives, entropy. Result below | FP patterns survive preemption and migration; 8 MiB threads; GC-style reserve/decommit tests | 3–5 |
| **WB2** OS personality ✅ 2026-11-19 ([browser-std.md](browser-std.md): WB2a–WB2d; a Tokio and a std HTTP fetch over Wi-Fi on the Pixel) | rust + libc forks, the std unix PAL over P.I.P.S., the mio bridge. The EXE runtime for `std`: today `e32::main!` brings its own panic handler, a 64 MiB Rust heap (`e32/src/heap.rs`) and a 1 MiB native heap (`build/emitter/build_rust_exe.py`); a `std` EXE needs std-aware start-up, allocator budgets, panic/unwind, and C/C++ linkage | Rust's std tests on Syborg and the phone; **one EXE mixing `std`, e32 and C++** runs; a Tokio TCP fetch over NeoNet | 6–12 |
| **WB3** mozjs shell ✅ 2026-11-19 ([browser-js.md](browser-js.md): `jssuite: 9 ok, 0 failed` on QEMU and the Pixel) | SpiderMonkey interpreter-only, as an EXE | JS test scripts, GC stress, threads, a clean OOM on the phone | 3–6 |
| **WB4** Servo → neoui | servo/surfman forks, SWGL, fonts, presentation. **The rustls crypto provider and entropy come here, not in WB6:** `Servo::new` always calls `prewarm_tls` | Local HTML/CSS/JS pages and images draw in `NEOWEB.EXE`; the memory is measured again | 6–12 |
| **WB5** input and chrome | Touch, scrolling, focus, direct Unicode input (a versioned composition/preedit protocol in neoui + its keyboard comes later), selection, forms, keyboard resize, Back, the Slint chrome (already built on FakeEngine by UI0–UI4, [browser-ui.md](browser-ui.md)) | Typing into forms and navigating with Back on the phone | 2–4 |
| **WB6** browser services | certificate handling and errors, cookies/storage on C:, redirects, logins; wifi.rs opens portals in NEOWEB | Signing in to a site; a captive portal over Wi-Fi | 2–4 |
| **WB7** media | The custom media backend (FFmpeg/dav1d, DevSound/MMF) | Video with sound, seeking, A/V sync, a thermal soak | 6–12+ |

**The UI track runs beside these stages** ([browser-ui.md](browser-ui.md), owner 2026-11-17): UI0–UI6 build every
screen of the canvas's Browser page as `NEOWEB.EXE` on a stand-in engine now, in parallel with WB2–WB4; each screen's
engine side arrives with the WB stage in its table.

**Total: about 29–56+ PM**, not counting audio-driver bring-up or upstream web-compatibility work.

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

### WB0 result (2026-11-16): GO

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

### WB1 result (2026-11-17): done

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
  - there is no user protect call: no-JIT SpiderMonkey does not need one (WB3, [browser-js.md](browser-js.md)).
- **Still open from S4:** the Rust ARMv7/NEON softfp target and LDREX atomics, which come with WB2.

### WB0 plan (2026-11-16)

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

## Open questions

- Does Qualcomm's EL2 trap AArch32 FP/SIMD (`CPTR_EL2`, `HCR_EL2`)?
- How complete is P.I.P.S.: thread-local storage, pthread layouts, `poll`, the C++ runtime and exceptions for C++20
  SpiderMonkey on GCC 14?
- Does SWGL match WebRender 0.70.1, and how fast is it on Kryo 360 gold cores?
- What is Servo's one-tab RSS on armv7?
- Is aws-lc-rs portable here, or should rustls use another provider?
- Does phone audio work (DevSound/MMF) for WB7?

## Prior art in `~/WS/Symbian`

- **NeoLite** (litehtml + QuickJS) and **NeoNetSurf** (NetSurf + Duktape): N8 SIS builds from 2026-11-13. Neither
  has been tested on a phone. Their Mac harnesses render real sites to PNG.
- **NeoWeb:** the 2010 S60 WebKit. JavaScriptCore compiles; WebCore is blocked on the MemMan allocator and missing
  headers.
- **LiveTo:** the Chromium screencast browser for the N8 (`server/proto.go`).
