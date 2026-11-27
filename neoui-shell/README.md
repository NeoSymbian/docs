<!-- SPDX-License-Identifier: Apache-2.0 -->
# neoui shell

Part of [NeoSymbian docs](../README.md) · Status: reference · Updated: 2026-11-27

Everything the shell (`SYSSTART.EXE`, NeoSymbian/neoui) draws and serves, and how apps talk to it: the protocol, the
kit and app API, navigation, the keyboard, the top panel, home, the settings store and the Settings app, system time,
the design system and smoothness. One document per area, each with its own status and stages; the stage board across
all areas is in [../roadmap.md](../roadmap.md). Reorganised 2026-11-21 (this page was the "shell services" design:
settings, notifications, home pages, widgets) and 2026-11-27 (finished plans moved to [history/](history/)).

## Documents

| Document | What | Status |
|---|---|---|
| [protocol.md](protocol.md) | Every NeoUi opcode and event, the versions built, and the numbers reserved for designed work | reference |
| [kit.md](kit.md) | The kit (shared Slint components), the app API `neoapp`, creating an app | done |
| [navigation.md](navigation.md) | Navigation v2: Buttons, Gestures (Thumb map), N9; the recognizer; Open apps, peek, Lanes | active |
| [keyboard.md](keyboard.md) | The system keyboard (en, hy, ru, pads, terminal) and the old apps' key pads | done |
| [top-panel.md](top-panel.md) | Status bar, shade, notifications, banners, media session, calls and messages from the panel, live island, control centre, lock screen | active |
| [home.md](home.md) | Home pages, pin and unpin, the dock, the home editor, widgets | active |
| [settings.md](settings.md) | The Settings app `NEOSET.EXE`: pages, `SETTINGS_INFO`/`ACTION`, who may write what, board parity | active |
| [settings-data.md](settings-data.md) | The data every Settings board shows: who produces it, the protocol, gates and feasibility | active |
| [settings-store.md](settings-store.md) | The settings store: typed keys, the registry, the file, `SETTING_GET`/`SET`/`WATCH` | done |
| [system-time.md](system-time.md) | The shell's system time: Date & time, network time, time zones with summer time | done |
| [design-system.md](design-system.md) | Tokens, layout, glyphs, digits, app tiles, components | done |
| [smooth-ui.md](smooth-ui.md) | 60 fps: input pacing, layers, CPU placement, FP/NEON, DPU, GPU | active |
| [history/](history/) | Finished plans kept as written: [step-0.md](history/step-0.md) (who is calling), [settings-plans.md](history/settings-plans.md) (SE1–SE4), [navigation-v1.md](history/navigation-v1.md) (Five places and G1) | record |

Elsewhere: [../user-side/legacy.md](../user-side/legacy.md) (old S60 apps through LEGACY.EXE; their key pads are drawn
there; their launcher becomes **Classic apps**, below) and the apps built on the kit: [../apps/files/README.md](../apps/files/README.md),
[../apps/phone.md](../apps/phone.md), [../apps/datetime.md](../apps/datetime.md), [../apps/store.md](../apps/store.md),
[../apps/browser/ui.md](../apps/browser/ui.md).

## Who draws what (K01)

The shell draws the status bar, the key row or the gesture band, dialogs (`QUERY`), toasts, the keyboard, the
shade and everything in [top-panel.md](top-panel.md), Open apps, the Apps menu, home, the power menu and
the SIM PIN. An app draws its header, footer and content with the kit ([kit.md](kit.md#who-draws-what)).

## Canvas map

The five canvas pages the shell owns (https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ) and the document each board
belongs to:

| Page | Boards | Document |
|---|---|---|
| Design system | `ds-tokens`, `ds-layout`, `ds-digits`, `ds-icon-formats`, `ds-app-icons`, `ds-glyphs`, `ds-components` | [design-system.md](design-system.md) |
| Shell & system UI · system screens | `Main`, `sh-home-buttons`, `sh-home-clock-24h`, `sh-home-clock-12h` | [home.md](home.md) |
| | `sh-apps-menu`, `sh-open-apps` | [navigation.md](navigation.md) |
| | `sh-shade`, `sh-shade-quick`, `sh-statusbar-states`, `sh-power-menu`, `sh-power-menu-v2`, `sh-sim-pin` | [top-panel.md](top-panel.md#screen-map) |
| | `sh-dialog` | [kit.md](kit.md) (QUERY) |
| | `sh-form-keyboard` | [keyboard.md](keyboard.md) |
| Shell & system UI · shell services | `sh-toast`, `sh-shade-app-notify`, `sh-badges` | [top-panel.md](top-panel.md#screen-map) |
| Shell & system UI · UI kit, patterns | `kit-header`, `kit-footer`, `kit-lists`, `kit-controls`, `kit-menus`, `kit-feedback`; `pat-prototype`, `pat-clock-buttons`, `pat-clock-gestures`, `pat-tabs-swipe`, `pat-files-select`, `pat-files-search`, `pat-files-refresh`, `pat-settings-top`, `pat-row-actions` | [kit.md](kit.md) |
| Shell & system UI · Shell API | `api-overview`, `api-kit-reference`, `api-recipes`, `api-decisions` | [kit.md](kit.md) |
| | `api-protocol` | [protocol.md](protocol.md) |
| Top panel & notifications | all 26 (`tp-*`, `nt-*`, `di-*`, `api-notify-*`; 8 added in TP0) | [top-panel.md](top-panel.md#screen-map) |
| Navigation | all 35 (`nav-*`, `nav2-spec-*`) | [navigation.md](navigation.md) |
| Keyboard | `kb2-*` (7), `pad-*` (22) | [keyboard.md](keyboard.md#canvas-the-keyboard-page-29-boards) |

## Decisions

| Question | Decision | Why |
|---|---|---|
| Who draws a widget | **Data first:** the app sends content, the shell draws it with a few built-in layouts. The protocol reserves a `Surface` kind so app-drawn widgets can come later | Costs no process or memory per widget (at most 4 apps run at once, and a surface is ~7 MB on the phone). The app need not be running, and every widget matches the house style |
| Home layout | **Belle style:** home pages hold widgets and shortcuts; every app stays in the Menu; pinning adds a shortcut or a dock slot | Keeps the "Belle, modernized" direction of `neoui/design/DESIGN.md` |
| What a new notification does | Always a status bar icon, a badge on the app's icon and a row in the shade. **Urgent** ones (call, alarm, SMS) also slide down a banner | Visible without being noisy |
| Where an app's own settings live | **One store.** The Settings app shows global settings and per-app notification switches. An app's own options stay inside the app but are saved in the same store | One file, one format, one change event |
| Boards or docs (O4, 2026-11-27) | **Boards win** over docs, and the docs are updated to match. Exception: stage and spec boards that are simply stale (`nav2-spec-stages`, `pad-spec-stages`, opcode numbers) are corrected to match the code | The canvas is the approved design; its stage notes went stale as the code moved |
| Terminal (O3, 2026-11-27) | **Moves to a new repo NeoSymbian/neoterm:** `NEOTERM.EXE` 0xE0002003, crate `neoui-term`, GPL because it links Slint | The shell repo keeps only the shell and its own apps |
| Old apps (O3, 2026-11-27) | **Renamed "Classic apps":** a kit app `CLASSIC.EXE` in the `legacy` repo reads INFO kind 4 and opens entries with `ACTION_OPEN_ENTRY`; the shell keeps only the entries (`host.entries("legacy")`) | The old-app launcher lives with the old-app runtime ([../user-side/legacy.md](../user-side/legacy.md)) |

The 2026-11-16/17 decisions K01–K04 (kit), D12–D20 (navigation) and the top panel's TPD1–TPD7 and P01–P06 are in
[kit.md](kit.md), [navigation.md](navigation.md) and
[top-panel.md](top-panel.md#decisions).

## Where the code goes

The layers of the 2026-11-09 shell-services plan (the "New" column is what that plan added; some of it has since
landed under other names, for example `home.rs`). No new crates; this follows the existing split.

| Layer | Path | New |
|---|---|---|
| Pure logic: `no_std`, Apache-2.0, host-tested | `neoui/crates/neoui-proto/src/` | `settings.rs`, `notify.rs`, `home.rs`, `widget.rs`; new opcodes and events in `ipc.rs` |
| UI server (GPL-3.0) | `neoui/symbian/src/` | `settings.rs` (store and file, after `clock.rs`), `notify.rs`; opcodes in `host.rs` (`impl Service for Host`) |
| Shell UI | `neoui/ui/` | `screens/home.slint` reworked; `components/widgets.slint`, `components/banner.slint`; the shade list, badges and settings wiring |
| App helper | `neoui/symbian/neoapp/src/lib.rs` | `setting()`, `set_setting()`, `notify()`, `cancel()`, `widget()` over the app's session |
| e32 | `e32-rs/crates/e32/src/server.rs` | `Message::client_sid()` (step 0; built in SE0) |

Processes outside neoui (Apache-2.0, for example in `neohw`) must not link the GPL `neoapp`. They encode with
`neoui-proto` and call through `e32::ipc::Session` themselves.

## Step 0: know who is calling

The design for binding each session to the app that calls (2026-11-09) is in [history/step-0.md](history/step-0.md).
It was built in parts: `Message::client_sid()` in SE0, the NOTIFY/BADGE caller check in TP2a, services in protocol 1.19
and session binding by SID and process id in 1.20.

## Not in this design (later)

- **Music, Photos and Camera** (O6, 2026-11-27; still being designed): only the protocols they will use are built
  now. Music uses MEDIA (TP3); Camera uses ACTIVITY kind Recording plus the privacy dot; Photos uses OPEN (1.9) plus
  WIDGET. The shell's demo screens stay as they are.
- App-drawn (`Surface`) widgets: a small surface chunk per widget, drawn by a running app.
- Waking an app on a schedule to refresh its widget.
- Apps that describe their own settings pages to the Settings app.
- An installed-apps registry. `APPS` and the catalogue stay fixed tables until app installation exists; the registry
  is NeoStore ST4 ([../apps/store.md](../apps/store.md), opcodes 38/39 in [protocol.md](protocol.md)).
- The notification items that were here (reboot survival, sounds, lock screen) are now phases of
  [top-panel.md](top-panel.md).

## Finishing plan (2026-11-27)

The owner asked for everything left in this folder in one push, built to the canvas (every page; proposals count as
approved), by agents in waves. The decisions O1–O6 are above and in [top-panel.md](top-panel.md#decisions) (O1, O5)
and [settings.md](settings.md#o-display-language-l-se5) (O2).

| Wave | What it builds | Stages |
|---|---|---|
| W0 | Protocol 1.22 (MEDIA, ACTIVITY, TILE, WIDGET, REPLY_TEXT, STICKY, LOCK_DIALOG, INSTALL_WALLPAPER, new keys); the canvas (`sh-power-menu-v2`, V3 sync, Classic apps page); these docs; the repo moves | V3, MV1, MV2 |
| W1 | The shell, part 1 (neoui): media, control centre and the 7 missing glyphs, navigation, home, keyboard, Settings | TP3, TP7, G2, home Part 3/4, keyboard extras, D1/D3/D7, SE4 |
| W2 | The shell, part 2 (neoui): lock screen and PIN; calls, island and inline reply; power menu v2 | TP8, TP9, TP5, TP6, TP4 reply, POWER |
| W3 | Producers and repins (phone, files, datetime, neohw, browser); the D11 fixes and SIM PIN changes | TP2c, TP5, TP6, FA9 M1b, D4, D9, D11 |
| W4 | Display language, then the wrap-up (docs, canvas AS BUILT, a named build and a Pixel run) | L0, L1, L2, SE5 |

**Out of scope** (their "Not yet" rows stay):
- blocked on the kernel or hardware: hidden Wi-Fi (D12), mobile data (D13), Bluetooth (D14), per-app battery shares
  (D16), USB Eject/Share (D17), Erase C: (D19); ringtones over 2 s (SE2c-2), the display processor (S5), double-tap
  wake, pinch on `virt` (one pointer), headset keys (A8), the unbacked tiles (Flashlight, Rotate, Hotspot, Cast;
  Bluetooth tiles hidden);
- blocked on release infrastructure: a signed update feed (D18);
- deferred: AknFep multi-tap/T9 and legacy L3 (several old apps at once), Surface widgets.

## Gates for every part
- `neoui`: `cargo fmt --check && cargo clippy --all-targets -- -D warnings && cargo test`, plus
  `cargo build -p neoui-proto -p neoui-render --target thumbv7em-none-eabihf`.
- `neoui/symbian`: `cargo fmt --all --check && cargo arm --workspace`. UI steps go into `symbian/taps.sh`; neoui's `virt-taps` CI runs them on QEMU
  `virt` (US6b; the kernel's `tools/ui-qemu.py`).
- `e32-rs` (step 0): its gate, and its `virt` CI (named `syborg` until 2026-11-25).
- Phone, after part 1 and part 3: install via the ROFS installer path (CLAUDE.md "The phone"). Check that brightness
  changes the backlight and that the home layout survives a power cycle.

When a stage lands, mark it in its document's stages block (`tools/roadmap.py` rebuilds [../roadmap.md](../roadmap.md)'s
board from them) and update the org profile's status list.
