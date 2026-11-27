<!-- SPDX-License-Identifier: Apache-2.0 -->
# Apps

The phone's own apps, each in its own NeoSymbian repo and each built on the neoui kit
([../neoui-shell/kit.md](../neoui-shell/kit.md)): Phone, Contacts and Messages; Files; Clock and Calendar; the web
browser; and the planned NeoStore. The shell itself (SYSSTART, Settings, the top panel, the protocol) is in
[../neoui-shell/README.md](../neoui-shell/README.md); the hardware daemons the apps talk to (MODEMD, AUDIOD, NEONET)
are in [../hardware/README.md](../hardware/README.md). Each document below owns its stages; the roadmap's board
collects them.

## Documents

| Document | What | Status |
|---|---|---|
| [phone.md](phone.md) | Phone, Contacts and Messages as three apps that open each other (NEOPHONE v2) | done |
| [files/README.md](files/README.md) | Files (NEOFILES v2): the design, the repo, the platform gaps, phases FA0–FA13 | active |
| [files/video-sync.md](files/video-sync.md) | How other players keep picture and sound together; the FA12b plan | research |
| [files/history/decisions.md](files/history/decisions.md) | Files' build records and the decisions taken while building FA1–FA11 | record |
| [datetime.md](datetime.md) | Clock, Calendar and their server DTSRV, phases DT0–DT7 | done |
| [store.md](store.md) | NeoStore: the store server, the phone app, the installer, the `.npk` format | plan |
| [browser/README.md](browser/README.md) | The web browser (Servo): the hub and the stage tracker | active |
| [browser/design.md](browser/design.md) | The choice of engine (2026-11-15): every candidate, why Servo | reference |
| [browser/architecture.md](browser/architecture.md) | The browser's repositories, forks, processes and platform prerequisites | reference |
| [browser/protocol.md](browser/protocol.md) | neoweb-proto: the Browser app ↔ the engine | reference |
| [browser/ui.md](browser/ui.md) | The Browser app's UI spec | active |
| [browser/ui-screens.md](browser/ui-screens.md) | Phases UI0–UI6 and every screen's status | active |
| [browser/wb0-host-proof.md](browser/wb0-host-proof.md) | WB0: Servo on emulated 32-bit ARM Linux (and WB0p) | done |
| [browser/wb1-kernel.md](browser/wb1-kernel.md) | WB1: the kernel work for the browser | done |
| [browser/wb2-std.md](browser/wb2-std.md) | WB2: Rust `std` over P.I.P.S., Tokio, TCP | done |
| [browser/wb2-layout-values.md](browser/wb2-layout-values.md) | WB2's appendix: every P.I.P.S. layout value | reference |
| [browser/wb3-js.md](browser/wb3-js.md) | WB3: SpiderMonkey, interpreter only | done |
| [browser/wb4-servo.md](browser/wb4-servo.md) | WB4: Servo in the Browser app | done |
| [browser/wb5-input-chrome.md](browser/wb5-input-chrome.md) | WB5: input and chrome | done |
| [browser/wb6-services.md](browser/wb6-services.md) | WB6: certificates, cookies, logins, Wi-Fi portals | active |
| [browser/wb7-media.md](browser/wb7-media.md) | WB7: video and sound in pages | plan |

## Where each app lives

| App | Repo | EXEs |
|---|---|---|
| Phone, Contacts, Messages | [NeoSymbian/phone](https://github.com/NeoSymbian/phone) | NEOPHONE, NEOCONT, NEOMSG |
| Files | [NeoSymbian/files](https://github.com/NeoSymbian/files) | NEOFILES |
| Clock, Calendar | [NeoSymbian/datetime](https://github.com/NeoSymbian/datetime) | NEOCLOCK, NEOCAL, DTSRV |
| Web browser | [NeoSymbian/browser](https://github.com/NeoSymbian/browser) (Servo and its dependencies: forks on branch `neosymbian`) | NEOWEB, NEOWEBE |
| NeoStore | `NeoSymbian/store` (planned, not created) | NEOSTORE, NEOINST, SISREGSRV |

The apps pin e32, neoui and Slint by git rev; the pins must match neoui's `symbian/Cargo.toml`.
