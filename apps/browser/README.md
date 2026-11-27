<!-- SPDX-License-Identifier: Apache-2.0 -->
# Web browser

Part of [Apps](../README.md) · Status: active · Updated: 2026-11-25

The hub for the native web browser (roadmap U3): Servo on the phone, in the Browser app `NEOWEB.EXE`
([NeoSymbian/browser](https://github.com/NeoSymbian/browser)). Details live in [`browser/`](./), one document per
stage or area. Reorganised 2026-11-21: the engine plan, the UI spec and the WB2 and WB3 working docs moved into the
folder.

## Tracker

<!-- stages -->
| Stage | What | State | Updated | Next / evidence |
|---|---|---|---|---|
| WB0 | Host proof: Servo on emulated 32-bit ARM Linux | done | 2026-11-16 | GO; results in browser `wb0/` |
| WB0p | Speed gate on a physical ARM board | parked | 2026-11-16 | no board; the Pixel gives the numbers now (WB4, WB5) |
| WB1 | Kernel: FP/NEON, 16 MiB stacks, GC memory, entropy | done | 2026-11-17 | kernel#19, e32-rs#3 |
| WB2 | Rust std over P.I.P.S., Tokio, TCP over NeoNet | done | 2026-11-19 | browser#3–#6, build#33 #34 #37, e32-rs#4 #5, kernel#21 #24, legacy#6, ossrv#1 #2 |
| WB3 | SpiderMonkey, interpreter only (JSSHELL.EXE) | done | 2026-11-19 | browser#7, mozjs#1; jssuite 9 ok on the Pixel |
| WB4 | Servo in the Browser app (engine NEOWEBE) | done | 2026-11-20 | browser#8, build#40, kernel#31, ossrv#3, mozjs#2 |
| WB5 | Input and chrome; scrolling 15–18 fps | done | 2026-11-21 | browser#10 #11, ossrv#5, servo#1, webrender#1, build#47, docs#52 #53 |
| WB6 | Certificates, cookies, logins, Wi-Fi portals | active | 2026-11-22 | UI5 done (browser#13); certificate store, cookie rule, passwords open |
| WB7 | Media: video and sound | open | — | not started; UI6 waits for it |
| UI0 | The app and its chrome | done | 2026-11-17 | browser#1; 5/5 built; Buttons mode not run on Servo |
| UI1 | Address, loading, reading | done | 2026-11-17 | browser#2; 3/3 built; the chrome doesn't hide on scroll with Servo |
| UI2 | Opened pages and Options | done | 2026-11-21 | in WB5c (browser#10); eviction not checked on the phone |
| UI3 | Forms and dialogs | done | 2026-11-21 | in WB5a (browser#10); all 5 work on Servo |
| UI4 | Library and settings | active | 2026-11-21 | 6/7 built (browser#10); `set2-app-browser` not re-checked since the Settings app's Apps pages (SE4a) |
| UI5 | Safety and errors | done | 2026-11-22 | browser#13, servo and neoui `ui5` branches; 4/4 on Servo on the Pixel |
| UI6 | Media | open | — | with WB7 |
<!-- /stages -->

Each stage has its own document (below); each screen's status, built and on Servo, is in
[ui-screens.md](ui-screens.md). The estimate for all of it was about 29–56+ person-months, not counting audio-driver
bring-up or upstream web compatibility. The UI track (UI0–UI6) ran beside the stages: every screen was built first on
a stand-in engine, and each one's engine side arrives with its WB stage.

### Platform

Every prerequisite is met ([architecture.md](architecture.md#platform-prerequisites)). The user side moved to ARMv8
(owner, 2026-11-21; [../../user-side/user-side-smp.md](../../user-side/user-side-smp.md)): US4 (browser#15,
2026-11-25) rebuilt both browser EXEs, NEOWEB on `armv8a-neosymbian-eabi` and NEOWEBE on `armv8a-symbian-eabi`
(`cargo sym`), and the owner browsed on that ROM on the Pixel. WB5's runs used a user side from before US2.

### Open items

| Item | Where | Stage |
|---|---|---|
| Page events and frames carry no tab id: a fast tab switch or a popup can mix them up for a moment; a hidden tab's dialog shows the visible site's name | [protocol.md](protocol.md#open) | next |
| The chrome doesn't hide on scroll (`ChromeScroll` is built and host-tested, not used with Servo) | [ui-screens.md](ui-screens.md#ui1-address-loading-reading) | next |
| Scrolling at 30 fps: the threaded SWGL compositor, frames drawn straight into the shell's surface | [wb5-input-chrome.md](wb5-input-chrome.md) | next |
| contenteditable gets no keyboard; `<select>` lists over 4 KiB lose rows; link URLs over about 2 KiB are cut | [wb5-input-chrome.md](wb5-input-chrome.md) | next |
| The tab list isn't saved on Quit; no heap budget for eviction; no ←/→ history list | [ui.md](ui.md#open-items) | next |
| JavaScript on/off and the cookie rule are saved, not applied | [wb6-services.md](wb6-services.md) | WB6 |
| Passwords need a secure store (B11) | [wb6-services.md](wb6-services.md) | WB6 |
| The shade's Open lands on Files' home: Files has no page for a file another app opens | [ui.md](ui.md#open-items) | Files |
| The Settings app's Browser page (`set2-app-browser`) | [ui-screens.md](ui-screens.md#ui4-library-and-settings) | Settings |
| CSS mask icons render black; GitHub's module scripts fail their CORS check | [wb4-servo.md](wb4-servo.md) | — |
| The No connection page can't tell no-such-site from refused or timed out: Servo reports only "client error (Connect)" (a Servo patch to keep the error's cause) | [ui-screens.md](ui-screens.md#ui5-safety-and-errors) | next |

## Documents

| Document | Covers | Status |
|---|---|---|
| [design.md](design.md) | The decisions of 2026-11-15, the platform then, every candidate engine, why Servo, open questions, prior art | reference |
| [architecture.md](architecture.md) | The repositories, forks and pinning, the architecture, the platform prerequisites | reference |
| [protocol.md](protocol.md) | neoweb-proto: NEOWEB ↔ NEOWEBE, every command and event | reference |
| [ui.md](ui.md) | The app's spec: decisions B01–B11, the chrome and its rules, Back, memory, the shell calls, storage | active |
| [ui-screens.md](ui-screens.md) | Phases UI0–UI6 and every canvas board, with its status | active |
| [wb0-host-proof.md](wb0-host-proof.md) … [wb7-media.md](wb7-media.md) | One per stage: scope, gate, result, open items | see the [tracker](#tracker) |
| [wb2-layout-values.md](wb2-layout-values.md) | WB2's appendix: every P.I.P.S. size, offset and constant PIPSPROB measured | reference |

## Where the code is

| Repo | What |
|---|---|
| [browser](https://github.com/NeoSymbian/browser) | `app/` (neoweb-core, neoweb-ui, neoweb-proto; host-tested), `symbian/neoweb` (NEOWEB.EXE), `std/webengine` (NEOWEBE.EXE), `std/` test EXEs, `crates/neoweb-host` (the WB0 Linux embedder), `wb0/` |
| [servo](https://github.com/NeoSymbian/servo), [webrender](https://github.com/NeoSymbian/webrender), [mozjs](https://github.com/NeoSymbian/mozjs), rust, libc, mio, tokio… | Forks on branch `neosymbian` ([architecture.md](architecture.md#forks)) |
| [ossrv](https://github.com/NeoSymbian/oss.FCL.sf.os.ossrv) | P.I.P.S. fixes, pinned in build's `sources.lock` |

## Canvas map

The canvas's Browser page (https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#page-9cb33ae9a178): 30 `br2-*` screens,
the prototype and 3 spec sheets; `set2-app-browser` is on the Settings page.

| Boards | Document |
|---|---|
| `br2-spec-chrome`, `br2-spec-screens`, `br2-spec-shell` | [ui.md](ui.md) |
| Every screen (`br2-start` … `br2-video`), `br2-prototype`, `set2-app-browser` | [ui-screens.md](ui-screens.md) |
