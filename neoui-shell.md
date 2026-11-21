<!-- SPDX-License-Identifier: Apache-2.0 -->
# neoui shell

The hub for everything the shell (`SYSSTART.EXE`, NeoSymbian/neoui) draws and serves, and how apps talk to it.
Details live in [`neoui-shell/`](neoui-shell/), one document per area, like [hardware.md](hardware.md) and its
folder. Roadmap stage U3 ([roadmap.md](roadmap.md)). Reorganised 2026-11-21: this page was the "shell services"
design (settings, notifications, home pages, widgets); its parts moved into the folder.

## Documents

| Document | Covers | Stages | Status |
|---|---|---|---|
| [neoui-shell/top-panel.md](neoui-shell/top-panel.md) | Status bar, shade, notifications, banners, media session, calls and messages from the panel, live island, control centre, lock screen | TP0–TP9 | designed 2026-11-21 |
| [neoui-shell/protocol.md](neoui-shell/protocol.md) | Every NeoUi opcode and event 1.0–1.12, and the numbers reserved for designed work | — | reference |
| [neoui-shell/kit.md](neoui-shell/kit.md) | The kit (shared Slint components), the app API `neoapp`, protocols 1.8–1.12 in detail, creating an app | A1–A5 | built |
| [neoui-shell/navigation.md](neoui-shell/navigation.md) | Navigation v2: Buttons, Gestures (Thumb map), N9; the recognizer; Open apps, peek, Lanes | G1, NV1–NV12, G2–G5 | NV built 2026-11-17 |
| [neoui-shell/keyboard.md](neoui-shell/keyboard.md) | The system keyboard (en, hy, ru, pads, terminal) and the old apps' key pads | — | built |
| [neoui-shell/settings.md](neoui-shell/settings.md) | The settings store (Part 1) and the apps rebuilt on it | Part 1 | built 2026-11-09 |
| [neoui-shell/home.md](neoui-shell/home.md) | Home pages, pin and unpin, the dock, widgets (Parts 3–4) | Parts 3–4 | planned |
| [neoui-shell/design-system.md](neoui-shell/design-system.md) | Tokens, layout, glyphs, digits, app tiles, components | — | built |
| [neoui-shell/smooth-ui.md](neoui-shell/smooth-ui.md) | 60 fps: input pacing, layers, CPU placement, FP/NEON, DPU, GPU | S1–S6 | S1–S3 done |
| [datetime.md](datetime.md#system-time-shell-built-2026-11-13) | The shell's system time: Date & time, network time, time zones (was Parts 5–6) | — | built 2026-11-13 |
| [legacy.md](legacy.md) | Old S60 apps through LEGACY.EXE (their key pads are drawn there) | — | — |
| [files-app.md](files-app.md), [phone-apps.md](phone-apps.md), [datetime.md](datetime.md), [store.md](store.md), [browser/ui.md](browser/ui.md) | The apps built on the kit | — | — |

## Who draws what (K01)

The shell draws the status bar, the key row or the gesture band, dialogs (`QUERY`), toasts, the keyboard, the
shade and everything in [top-panel.md](neoui-shell/top-panel.md), Open apps, the Apps menu, home, the power menu and
the SIM PIN. An app draws its header, footer and content with the kit ([kit.md](neoui-shell/kit.md#who-draws-what)).

## Status by area (2026-11-21)

| Area | Built | Next |
|---|---|---|
| Settings store | Part 1, every app on it | — |
| Kit and app API | 1.8–1.12 | — |
| Navigation | NV1–NV12 (not installed) | G2–G5 |
| Keyboard | en/hy/ru, pads, terminal; old-app key pads | — |
| Top panel | status bar v1, shade with entries (1.8–1.11); TP0 (docs + canvas) | TP1 |
| Home | live clock; static mock-up cards | Parts 3–4; the Media card in TP3 |
| Lock screen | none | TP8 (replaces Navigation G6) |
| Smoothness | S1–S3 | S4 (ARMv7/ARMv8 user side) |

## Canvas map

The five canvas pages the shell owns (https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ) and the document each board
belongs to:

| Page | Boards | Document |
|---|---|---|
| Design system | `ds-tokens`, `ds-layout`, `ds-digits`, `ds-icon-formats`, `ds-app-icons`, `ds-glyphs`, `ds-components` | [design-system.md](neoui-shell/design-system.md) |
| Shell & system UI · system screens | `Main`, `sh-home-buttons`, `sh-home-clock-24h`, `sh-home-clock-12h` | [home.md](neoui-shell/home.md) |
| | `sh-apps-menu`, `sh-open-apps` | [navigation.md](neoui-shell/navigation.md) |
| | `sh-shade`, `sh-shade-quick`, `sh-statusbar-states`, `sh-power-menu`, `sh-sim-pin` | [top-panel.md](neoui-shell/top-panel.md#screen-map) |
| | `sh-dialog` | [kit.md](neoui-shell/kit.md) (QUERY) |
| | `sh-form-keyboard` | [keyboard.md](neoui-shell/keyboard.md) |
| Shell & system UI · shell services | `sh-toast`, `sh-shade-app-notify`, `sh-badges` | [top-panel.md](neoui-shell/top-panel.md#screen-map) |
| Shell & system UI · UI kit, patterns | `kit-header`, `kit-footer`, `kit-lists`, `kit-controls`, `kit-menus`, `kit-feedback`; `pat-prototype`, `pat-clock-buttons`, `pat-clock-gestures`, `pat-tabs-swipe`, `pat-files-select`, `pat-files-search`, `pat-files-refresh`, `pat-settings-top`, `pat-row-actions` | [kit.md](neoui-shell/kit.md) |
| Shell & system UI · Shell API | `api-overview`, `api-kit-reference`, `api-recipes`, `api-decisions` | [kit.md](neoui-shell/kit.md) |
| | `api-protocol` | [protocol.md](neoui-shell/protocol.md) |
| Top panel & notifications | all 26 (`tp-*`, `nt-*`, `di-*`, `api-notify-*`; 8 added in TP0) | [top-panel.md](neoui-shell/top-panel.md#screen-map) |
| Navigation | all 35 (`nav-*`, `nav2-spec-*`) | [navigation.md](neoui-shell/navigation.md) |
| Keyboard | `kb2-*` (7), `pad-*` (22) | [keyboard.md](neoui-shell/keyboard.md#canvas-the-keyboard-page-29-boards) |

## Decisions

| Question | Decision | Why |
|---|---|---|
| Who draws a widget | **Data first:** the app sends content, the shell draws it with a few built-in layouts. The protocol reserves a `Surface` kind so app-drawn widgets can come later | Costs no process or memory per widget (at most 4 apps run at once, and a surface is ~7 MB on the phone). The app need not be running, and every widget matches the house style |
| Home layout | **Belle style:** home pages hold widgets and shortcuts; every app stays in the Menu; pinning adds a shortcut or a dock slot | Keeps the "Belle, modernized" direction of `neoui/design/DESIGN.md` |
| What a new notification does | Always a status bar icon, a badge on the app's icon and a row in the shade. **Urgent** ones (call, alarm, SMS) also slide down a banner | Visible without being noisy |
| Where an app's own settings live | **One store.** The Settings app shows global settings and per-app notification switches. An app's own options stay inside the app but are saved in the same store | One file, one format, one change event |

The 2026-11-16/17 decisions K01–K04 (kit), D12–D20 (navigation) and the top panel's TPD1–TPD7 and P01–P06 are in
[kit.md](neoui-shell/kit.md), [navigation.md](neoui-shell/navigation.md) and
[top-panel.md](neoui-shell/top-panel.md#decisions).

## Where the code goes

No new crates; this follows the existing split.

| Layer | Path | New |
|---|---|---|
| Pure logic: `no_std`, Apache-2.0, host-tested | `neoui/crates/neoui-proto/src/` | `settings.rs`, `notify.rs`, `home.rs`, `widget.rs`; new opcodes and events in `ipc.rs` |
| UI server (GPL-3.0) | `neoui/symbian/src/` | `settings.rs` (store and file, after `clock.rs`), `notify.rs`; opcodes in `host.rs` (`impl Service for Host`) |
| Shell UI | `neoui/ui/` | `screens/home.slint` reworked; `components/widgets.slint`, `components/banner.slint`; the shade list, badges and settings wiring |
| App helper | `neoui/symbian/neoapp/src/lib.rs` | `setting()`, `set_setting()`, `notify()`, `cancel()`, `widget()` over the app's session |
| e32 | `e32-rs/crates/e32/src/server.rs` | `Message::client_sid()` (step 0) |

Processes outside neoui (Apache-2.0, for example in `neohw`) must not link the GPL `neoapp`. They encode with
`neoui-proto` and call through `e32::ipc::Session` themselves.

## Step 0: know who is calling

**Problem.** `Host::connect` (`symbian/src/host.rs`) binds each new session to "the newest launched app without a
session" (marked `shortcut:` there). Two things follow:
- a process the shell didn't launch (a background service) is refused;
- the server can't verify which app a message comes from, so per-app rights (settings namespaces, notification keys)
  can't be enforced.

**Design.**
- Add `Message::client_sid() -> Result<u32, i32>` to `e32::server`. Use the `MessageClient` exec call (number from
  `execs.rs`) to open the client thread, then read its process's secure ID, and close the handle.
- Extend `APPS` to `(key, exe, uid3)`. The UID3 is the SID; take it from `symbian/exes.txt`.
- On `connect`, look up the app by SID.
  - A launched app gets its app record, as today.
  - A SID listed in a new table `SERVICES: &[(sid, &[keys])]` gets a **service session**: no surface or events, but it
    may post notifications and widget content under the keys listed for it.
  - Any other SID is refused with `KErrPermissionDenied`.
- Keep "the newest app without a session" only as the fallback when `client_sid` fails.
- Bump `ipc::VERSION` to (1, 1). The new opcodes and events are additive, so apps built for 1.0 still connect (only
  the major version is checked).

**Not needed at first for phone notifications.** The shell already talks to `NeoModem`, so it can post missed-call
and SMS notifications itself from modem events. Step 0 is needed for third-party apps and other background services.


## Not in this design (later)

- App-drawn (`Surface`) widgets: a small surface chunk per widget, drawn by a running app.
- Waking an app on a schedule to refresh its widget.
- Apps that describe their own settings pages to the Settings app.
- An installed-apps registry. `APPS` and the catalogue stay fixed tables until app installation exists; the registry
  is NeoStore ST4 ([store.md](store.md), opcodes 38/39 in [protocol.md](neoui-shell/protocol.md)).
- The notification items that were here (reboot survival, sounds, lock screen) are now phases of
  [top-panel.md](neoui-shell/top-panel.md).

## Gates for every part
- `neoui`: `cargo fmt --check && cargo clippy --all-targets -- -D warnings && cargo test`, plus
  `cargo build -p neoui-proto -p neoui-render --target thumbv7em-none-eabihf`.
- `neoui/symbian`: `cargo fmt --all --check && cargo arm --workspace`. The `syborg` CI drives the new steps through
  `symbian/taps.sh`.
- `e32-rs` (step 0): its gate, and the `syborg` CI.
- Phone, after part 1 and part 3: install via the ROFS installer path (CLAUDE.md "The phone"). Check that brightness
  changes the backlight and that the home layout survives a power cycle.

When a part lands, mark it **Done** in the table at the top, and update [roadmap.md](roadmap.md) U3 and the org
profile's status list.
