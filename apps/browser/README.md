<!-- SPDX-License-Identifier: Apache-2.0 -->
# Web browser

The hub for the native web browser (roadmap U3): Servo on the phone, in the Browser app `NEOWEB.EXE`
([NeoSymbian/browser](https://github.com/NeoSymbian/browser)). Details live in [`browser/`](./), one document per
stage or area. Reorganised 2026-11-21: the engine plan, the UI spec and the WB2 and WB3 working docs moved into the
folder.

**Legend:** ✅ done · 🟡 partly · ⬜ not started · ⏸ deferred

## Tracker (2026-11-21)

### Stages

| Stage | What | Status | PRs | Document |
|---|---|---|---|---|
| WB0 | Host proof: Servo on emulated 32-bit ARM Linux | ✅ GO 2026-11-16 | — (browser `wb0/`) | [wb0-host-proof.md](wb0-host-proof.md) |
| WB0p | Speed gate on a physical ARM board | ⏸ no board; the Pixel measures it now | — | [wb0-host-proof.md](wb0-host-proof.md) |
| WB1 | Kernel: FP/NEON for apps, 16 MiB stacks, GC memory, entropy | ✅ 2026-11-17 | kernel#19, e32-rs#3 | [wb1-kernel.md](wb1-kernel.md) |
| WB2 | Rust `std` over P.I.P.S., Tokio, TCP over NeoNet | ✅ 2026-11-19 | browser#3–#6, build#33 #34 #37, e32-rs#4 #5, kernel#21 #24, legacy#6, ossrv#1 #2 | [wb2-std.md](wb2-std.md) |
| WB3 | SpiderMonkey, interpreter only (`JSSHELL.EXE`) | ✅ 2026-11-19 | browser#7, mozjs#1 | [wb3-js.md](wb3-js.md) |
| WB4 | Servo in the Browser app (engine process NEOWEBE) | ✅ 2026-11-20 | browser#8, build#40, kernel#31, ossrv#3, mozjs#2 | [wb4-servo.md](wb4-servo.md) |
| WB5 | Input and chrome: forms, dialogs, tabs, menus, library, downloads, settings; scrolling 15–18 fps | ✅ 2026-11-21 | browser#10 #11, ossrv#5, servo#1, webrender#1, build#47, docs#52 #53 | [wb5-input-chrome.md](wb5-input-chrome.md) |
| WB6 | Browser services: certificates, cookies on C:, logins, Wi-Fi portals | 🟡 UI5 done 2026-11-22 | browser `ui5`, servo `ui5`, neoui `ui5-portal` | [wb6-services.md](wb6-services.md) |
| WB7 | Media: video and sound | ⬜ | — | [wb7-media.md](wb7-media.md) |

The estimate for all of it was about 29–56+ person-months, not counting audio-driver bring-up or upstream web
compatibility. The UI track (UI0–UI6) ran beside the stages: every screen was built first on a stand-in engine, and
each one's engine side arrives with its WB stage.

### UI phases

29 of 31 screens built; on Servo on the Pixel: 23 ✅, 5 🟡, 3 ⬜. Each screen: [ui-screens.md](ui-screens.md).

| Phase | Built | On Servo | Waits for |
|---|---|---|---|
| UI0 the app and its chrome | ✅ 5/5 | 3 ✅ 2 🟡 (Buttons mode not run) | — |
| UI1 address, loading, reading | ✅ 3/3 | 2 ✅ 1 ⬜ (the chrome doesn't hide on scroll) | — |
| UI2 opened pages and Options | ✅ 6/6 | 5 ✅ 1 🟡 (eviction not checked on the phone) | — |
| UI3 forms and dialogs | ✅ 5/5 | 5 ✅ | — |
| UI4 library and settings | 🟡 6/7 | 4 ✅ 2 🟡 1 ⬜ | Settings' Apps list (`set2-app-browser`) |
| UI5 safety and errors | ✅ 4/4 | 4 ✅ | — |
| UI6 media | ⬜ 0/1 | ⬜ | WB7 |

### Platform

Every prerequisite is met ([architecture.md](architecture.md#platform-prerequisites)). The user side moves
to ARMv8 (owner, 2026-11-21; [../../user-side/user-side-smp.md](../../user-side/user-side-smp.md)):
- **WB5's runs:** they used a user side from before US2.
- **US4:** the Rust target moves to ARMv8 and rebuilds both browser EXEs; the browser is re-tested on that ROM.

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
| NEOWEB and NEOWEBE are ARMv8 since US4 (until 2026-11-25: ARMv5TE and ARMv7) | [ui.md](ui.md#when-servo-arrives-marked-2026-11-21) | US4 |
| CSS mask icons render black; GitHub's module scripts fail their CORS check | [wb4-servo.md](wb4-servo.md) | — |
| The No connection page can't tell no-such-site from refused or timed out: Servo reports only "client error (Connect)" (a Servo patch to keep the error's cause) | [ui-screens.md](ui-screens.md#ui5-safety-and-errors) | next |

## Documents

| Document | Covers | Status |
|---|---|---|
| [design.md](design.md) | The decisions of 2026-11-15, the platform then, every candidate engine, why Servo, open questions, prior art | reference |
| [architecture.md](architecture.md) | The repositories, forks and pinning, the architecture, the platform prerequisites | ✅ prerequisites met |
| [protocol.md](protocol.md) | neoweb-proto 1.4: NEOWEB ↔ NEOWEBE, every command and event | reference |
| [ui.md](ui.md) | The app's spec: decisions B01–B11, the chrome and its rules, Back, memory, the shell calls, storage | ✅ UI0–UI4 |
| [ui-screens.md](ui-screens.md) | Phases UI0–UI6 and every canvas board, with its status | 25/31 built |
| [wb0-host-proof.md](wb0-host-proof.md) … [wb7-media.md](wb7-media.md) | One per stage: scope, gate, result, open items | see the tracker |

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
