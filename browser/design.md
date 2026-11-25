<!-- SPDX-License-Identifier: Apache-2.0 -->
# Browser design: the choice of engine

Part of the [browser docs](../browser.md). Written 2026-11-15, the design that chose Servo (roadmap U3).

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

## Where the platform stood (2026-11-15)

All of this is solved now except the GPU: see [architecture.md](architecture.md#platform-prerequisites).
| Need | At design time (2026-11-16) | Where |
|---|---|---|
| Sockets | NeoNet (smoltcp: DHCP, DNS, TCP, UDP; IPv4) and the 2010 `RSocket` API over it (W5a) | [wifi.md](../hardware/wifi.md) W5, W5a |
| TLS, HTTP client | **none** (only hand-written `GET /generate_204`) | `neoui/symbian/src/wifi.rs:439` |
| Hardware FP/NEON at EL0 | **off**: the per-thread FP save/restore hooks are empty | [kernel-issues.md](../kernel-issues.md) KRN-019, [smooth-ui.md](../neoui-shell/smooth-ui.md) S4 |
| Atomics | **none**: user code was ARMv5TE, which has no CAS, so Rust had no `Arc` (native atomics since US4, 2026-11-25) | `e32-rs/crates/e32/src/cs.rs` |
| RAM | **~87 MB** on `main` for the kernel and the whole user side (`A64_BOOT_RAM_END`). M4.3 is in progress: kernel branch `ram-map` (`640aa2ff`, 2026-11-15) takes the RAM banks from the bootloader's DTB, below 4 GiB (`KPhysTop`) | `kernel/baseport/arm64/bonito_variant/variant.conf:8`, `kernel/kernel/eka/kernel/arm64/a64boot.cpp` |
| Address space | ~2 GiB private VA per process (flexible model) | `kernel/kernel/eka/include/memmodel/epoc/flexible/arm64/mmboot.h` |
| Thread stacks | **1 MiB per thread, 2 MiB per process** | `kernel/kernel/eka/memmodel/epoc/flexible/mmu/mmu.cpp:300` |
| Executable memory | Writable+executable chunks exist (a JIT is possible later) | `kernel/kernel/eka/memmodel/epoc/flexible/mprocess.cpp` |
| Rust `std` | **none**: all user Rust was `no_std` + alloc on `armv5te-none-eabi` (now `armv8a-neosymbian-eabi`; the browser's std EXEs use `armv8a-symbian-eabi`) | `e32-rs/rust-toolchain.toml` |
| libc | P.I.P.S./Open C sources (libc, libm, libpthread), today only registered for SVG-T. **`mprotect` does nothing**; `poll` is unverified | `legacy/components.py:188`; `ossrv` `genericopenlibs/openenvcore/libc/src/mmap.cpp` |
| Surface and input | Each app gets a shared XRGB8888 chunk + DAMAGE, and 16-byte touch/key events | `neoui/crates/neoui-proto/src/ipc.rs` |
| Fonts and images | Slint bakes SDF glyphs (no shaping, no fallback); PNG only | `neoui/Cargo.toml` |
| GPU | No driver; everything renders on the CPU | [smooth-ui.md](../neoui-shell/smooth-ui.md) S6 |

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

### Old .sis browsers (through [legacy.md](../legacy.md))

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

## Open questions (marked 2026-11-21)

- ✅ Does Qualcomm's EL2 trap AArch32 FP/SIMD (`CPTR_EL2`, `HCR_EL2`)? **No** ([WB1](wb1-kernel.md)).
- ✅ How complete is P.I.P.S.: thread-local storage, pthread layouts, `poll`, the C++ runtime and exceptions for C++20
  SpiderMonkey on GCC 14? **Measured and fixed** in WB2 (PIPSPROB, [wb2-std.md](wb2-std.md)) and WB3 (`cxxrt`,
  [wb3-js.md](wb3-js.md)).
- ✅ Does SWGL match WebRender 0.70.1, and how fast is it on Kryo 360 gold cores? **Yes** (WB0, one patch);
  scrolling 15–18 fps on the Pixel ([WB5](wb5-input-chrome.md)).
- ✅ What is Servo's one-tab RSS on armv7? **37–210 MiB per page** ([WB0](wb0-host-proof.md)).
- ✅ Is aws-lc-rs portable here, or should rustls use another provider? **aws-lc-rs works** (https pages since
  [WB4](wb4-servo.md)).
- ⬜ Does phone audio work (DevSound/MMF) for WB7? The phone plays sound through NeoAudio ([audio.md](../hardware/audio.md));
  the browser's path to it is open ([WB7](wb7-media.md)).

## Prior art in `~/WS/Symbian`

- **NeoLite** (litehtml + QuickJS) and **NeoNetSurf** (NetSurf + Duktape): N8 SIS builds from 2026-11-13. Neither
  has been tested on a phone. Their Mac harnesses render real sites to PNG.
- **NeoWeb:** the 2010 S60 WebKit. JavaScriptCore compiles; WebCore is blocked on the MemMan allocator and missing
  headers.
- **LiveTo:** the Chromium screencast browser for the N8 (`server/proto.go`).
