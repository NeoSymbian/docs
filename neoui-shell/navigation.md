<!-- SPDX-License-Identifier: Apache-2.0 -->
# Gesture navigation: Navigation v2 (and the N9 mix before it)

Part of [neoui shell](README.md) · Status: active · Updated: 2026-11-27

**Status: Navigation v2 built 2026-11-17** on neoui `ui-v2`: three modes, the app-drawn header, the 639 / 679 dp
surfaces; installed on slot a the same day ([filesystem.md](../storage/filesystem.md) FS5's install record). Open
apps with thumbnails (G3), swipe down to close (G4) and Lanes home (G5) were built on 2026-11-27 with Settings' D10
(neoui#61). Peek (G2) is open. The design is the canvas's Navigation page
(https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ), decisions D12–D20, approved 2026-11-16.

The model is the Nokia N9's Swipe UI (MeeGo Harmattan, 2011), not Android's or iOS's. Gestures sit beside a key row of
system buttons, and the user picks in Settings.

How apps build their part (the kit, the app API, protocol 1.8) is in [kit.md](kit.md).

After "Navigation v2" come the N9 map (which v2 keeps as "N9 gestures"), then pointers to v1: the recognizer as
designed for G1 and Five places, whose strip and shell-drawn page actions v2 replaced, are in
[history/navigation-v1.md](history/navigation-v1.md).

It builds on [README.md](README.md) (the settings store, notifications, home pages) and [smooth-ui.md](smooth-ui.md)
(the server's layers and slides).

<!-- stages -->
| Stage | What | State | Updated | Next / evidence |
|---|---|---|---|---|
| G1 | Edge recognizer and gesture mode | done | 2026-11-16 | Back, Open apps, Home, Apps menu by edge swipe; an edge hint |
| P | v1 Five places: strip and Page API | done | 2026-11-17 | built 2026-11-16, replaced by Navigation v2 on 2026-11-17 |
| NV1–NV12 | Navigation v2, Gestures the default | done | 2026-11-17 | protocol 1.8, kit header, key row and band, both maps; installed on slot a |
| G2 | N9 peek: the screen follows the finger | open | — | design below; not started |
| G3 | Open apps thumbnails, columns, close mode | done | 2026-11-27 | neoui#61 (D10): `nav.switcher_cols`, a 500 ms hold shows × on every card |
| G4 | Swipe down from the top closes the app | done | 2026-11-27 | neoui#61 (D10): `nav.swipe_close`; virt-taps closes Settings with it |
| G5 | Lanes home: Events, Home, Open apps | done | 2026-11-27 | neoui#61 (D10): `home.style`; not run on the phone yet |
<!-- /stages -->

G6, the N9 lock screen, moved to [top-panel.md](top-panel.md#lock-screen-tp8) TP8 on 2026-11-21.

## Navigation v2

**The decisions D12–D20** (owner, 2026-11-16):
- **D12.** Classic becomes Buttons: a key row with system keys only (← ⌂ ▢).
- **D13.** App actions live in an app-drawn header: root `[Name · ≤ 3 icons]`, sub-page `[← Name · ≤ 3]`.
- **D14.** A form is `[✕ Title ✓]`. Big actions (Call, Send, Shutter, Answer) stay in the content.
- **D15.** One shared header component, the kit's `Header`.
- **D16.** The title is in the header only. The status bar shows the clock and indicators.
- **D17.** A mode switch may resize apps (639 ↔ 679 dp).
- **D18.** Buttons has no edge gestures.
- **D19.** Two gesture maps: Gestures (the Thumb map, the default) and N9 gestures.
- **D20.** The live Back arrow, the last-app flick, home's long press, and a swipe down on the keyboard.

### The rules (v2; they replace v1's eleven)
1. **Status bar.** 25 dp in every mode except full screen: the clock at the left, the network's name, signal, Wi-Fi
   and battery at the right. No title.
2. **Apps draw their header** (48 dp, the kit): Header, SubHeader, FormHeader, SearchHeader, SelectionHeader. Icon
   targets are 48 × 48 with 24 dp glyphs.
3. **⋮ is one of the three header actions.** It opens the kit's Menu, a dropdown under it. It shows only when there are
   items; a tap outside or Back closes it.
4. **Big task actions stay in the content.** NEOPHONE's dialer has Call in a band under the keypad.
5. **Three modes.** `nav.mode`: 0 Buttons, 1 Gestures (the default), 2 N9 gestures.
6. **Buttons: system keys only.** A 56 dp key row, ← ⌂ ▢ in thirds. ← dims on home and becomes ˅ with the keyboard.
   There are no edge gestures.
7. **The Thumb map.**
   - Either side edge, inward: Back.
   - Up from the bottom: Home; on home, the Apps menu.
   - Up and held still for about 300 ms: Open apps.
   - Along the bottom band, past 72 dp: the previous (rightwards) or next (leftwards) running app.
   - On home, only the bottom edge is live.
8. **The N9 map.**
   - The left edge: Back.
   - A drag from the right edge: Open apps. A quick flick (≥ 24 dp at ≥ 0.5 dp/ms): the last app.
   - Up from the bottom: Home; past half the screen, the Apps menu.
9. **The live Back arrow.** A 36 dp bubble with ← follows the finger in from a Back edge. It is grey, and turns accent
   at the 72 dp commit point.
10. **Back, in order.**
    - Close a menu, sheet or dialog: the kit's layers (`neoapp::kit_back!`) and the shell's QUERY.
    - Hide the keyboard.
    - Go up one page; the header's ← takes the same path.
    - At the app's top page, go back to where it was opened from.
11. **Home and Open apps keep everything.** Only × on an Open apps card closes an app.
12. **Home.** No ⋮ in any mode, and Apps is always in the dock. A long press opens Edit home · Wallpaper.
13. **Full screen.** A call or the camera hides the status bar and the bottom. In Buttons a tap shows the key row for
    3 s; in Gestures the edges keep working.
14. **Keyboard.** It sits above the key row or the band at its full height. A swipe down on its top band hides it. The
    band also has Select all · Copy · Paste for an app's field.
15. **Dialogs stay with the shell.** QUERY is a centred card with up to 3 buttons, a destructive one in red. Back (or
    the key row's ←, which stays usable under it) answers the last button.
16. **A mode switch resizes apps once.** Buttons gives 639 dp, Gestures and N9 679 dp, full screen 720
    (`AppEvent::Area`).

### Thresholds (dp; `neoui-proto/src/gesture.rs`)
| | Value |
|---|---|
| Edge zone, slop | 16, 8 |
| Side commit (Back, N9's Open apps), along-the-band commit | 72 |
| Home | 80, no flings from the bottom |
| N9 Apps menu | half the screen's height |
| Fling | ≥ 24 dp at ≥ 0.5 dp/ms |
| Thumb up-and-hold | 300 ms still (`Recognizer::tick`, called each frame; the server wakes every 50 ms while a gesture is held) |

### Where the code is
- `neoui-proto`: `gesture.rs` (`Map`, the recognizer, `tick`), `page.rs` (Page 1.8, Note, Notification),
  `ipc.rs` (opcodes and events).
- `ui/components/frame.slint`: StatusBar, KeyRow, Band.
- `ui/shell.slint`: the bottom, the kit header on the shell's screens, the toast, dialogs, the keyboard.
- `crates/neoui-render`: `Renderer::gesture` (last / previous / next app from the running list) and
  `back_bubble_pixel`.
- `symbian/src/lib.rs`: live edges per map, `tick`, the bubble and bar hints. `host.rs`: NOTE, NOTIFY, BADGE, CLIP,
  `Area` on a body change.
- Tests: neoui-proto's gesture tests, including the Thumb and N9 maps; neoui-render's `nav.rs` (the v2 chrome),
  `gestures.rs`, `pads.rs` (keyboard, edit bar, swipe down).

## The N9 Swipe UI, as it worked
This is written from memory of using the phone. No Nokia material is copied.

- **Three home views** sit side by side, and a sideways swipe moves between them:
  - **Events:** notifications and feeds;
  - **Applications:** the app grid;
  - **Open applications:** live thumbnails of the running apps. A pinch switches between 2×2 and 3×3. A long press
    shows a × on every card.
- **There is no home key.** In an app, a swipe in from the left or right edge puts the app away to the home view used
  last.
  - **Peek:** the app follows the finger and the home view shows underneath. Letting go early returns to the app.
  - Pausing halfway shows the status bar and the time without leaving.
- **Swipe down from the top edge** closes the app. It was an option ("Swipe to close app").
- **A tap on the status bar** opens the status menu: profile, volume and connections.
- **Lock screen:** double-tap to wake. Swipe in from any edge to unlock; the lock screen slides away in that direction.
  A swipe up from the bottom shows a quick-launch bar of four apps.
- **Back** is not a gesture. Each app has a back arrow in its own bottom toolbar.

**What Sailfish OS added, and why we don't take it.** The N9's designers went on to Sailfish OS.
- **Back:** a swipe right anywhere on a page goes back. That clashes with apps that scroll sideways (maps, tabs,
  photos), so each app has to opt in. Our apps already claim Back explicitly (`NAV`), and an edge gesture needs no
  opt-in.
- **Pulley menus:** pulling a list past its top opens a menu. That would take over every list's overscroll; our
  Options sheet already does the job.
- **Cover actions:** buttons on the running-app cards. That is a later idea for G3, not a navigation gesture.

## The map
The owner chose this map on 2026-11-16. It is the N9's with two changes:
- **The left edge is Back.** The N9 kept Back in its toolbar, but a phone without one needs it as a gesture. At an
  app's root, Back returns to where the app was opened from (home or the Apps menu), as the toolbar's Back does.
  So the N9's "put away" feel stays.
- **The bottom edge is Home, then the Apps menu.** It is one continuous swipe up: Home first, the Apps menu past half
  the screen. This is the N9's quick-launch swipe turned into a way home.

```text
            top ↓  shade (G4 option: close the app)
          ┌───────────────────┐
     →    │                   │    ←
   Back   │        app        │  Open apps
          │                   │  (N9 peek, G2)
          └───────────────────┘
            bottom ↑  Home ── keep going ↑ ── Apps menu
```

### Every gesture
"Classic" and "Gestures" are the values of `nav.mode`. "—" means the gesture does nothing there.

| Gesture | App | Home | Apps menu | Open apps | Lock | Mode | Stage |
|---|---|---|---|---|---|---|---|
| Left edge, swipe right | Back: the app's Back if it claimed it, else the shell's `back()` | — (the left edge stays with the home pages' slide) | Back (home) | Back | — | Gestures | G1 |
| Right edge, swipe left | Open apps | Open apps | Open apps | — | — | Gestures | G1 (fade), G2 (peek) |
| Bottom edge, short swipe up | Home | Apps menu | Home | Home | — | Gestures | G1 |
| Bottom edge, long swipe up (past half) | Apps menu | Apps menu | — | Apps menu | — | Gestures | G1 |
| Top edge (status bar), swipe down | Shade | Shade | Shade | Shade | — | Both | Exists (`StatusBar.pulled`) |
| Top edge, swipe down, `nav.swipe_close` on | Close the app (it quits) | Shade | Shade | Shade | — | Gestures | G4 |
| Tap on the status bar | Shade | Shade | Shade | Shade | — | Both | Exists |
| Swipe sideways on the home pages | — | Next page (Pages) or lane (Lanes) | — | — | — | Both | Exists (S2c); lanes G5 |
| Long press on an Open apps card | — | — | — | × on every card (N9 close mode) | — | Both | G3 |
| Tap × on an Open apps card | — | — | — | Close that app | — | Both | Exists |
| Swipe in from any edge | — | — | — | — | Unlock | Both | G6 |
| Double-tap on the dark screen | — | — | — | — | Wake | Both | G6 (needs the driver) |
| Toolbar Back button | Back | — | Back | Back | — | Classic only | Exists |
| Toolbar Action, Options | the app's | — | Open apps (Action) | — | — | Both | Exists |
| Pinch on Open apps | — | — | — | 2 ↔ 3 columns | — | Both | Later (multi-touch) |

Not taken from Android or iOS: no swipe-up-and-hold for recents, no sideways swipe along the bottom between apps,
no back from both side edges.

## Five places: one strip, every app, two modes (v1, replaced by Navigation v2)

v1 (decided and built 2026-11-16: a shell-drawn bottom strip, the Page API of protocol 1.7), replaced on 2026-11-17 by
[Navigation v2](#navigation-v2). The design as written: [history/navigation-v1.md](history/navigation-v1.md#five-places-one-strip-every-app-two-modes-v1-replaced-by-navigation-v2).

## The recognizer (G1)

A pure state machine in `neoui-proto::gesture` (`no_std`, host-tested): edge zones, hold and replay, tracking, commit.
G1's design of it (states, sizes, edges per screen, ownership) is in [history/navigation-v1.md](history/navigation-v1.md#the-recognizer-g1); v2's
thresholds are [above](#thresholds-dp-neoui-protosrcgesturers).

## Where the code goes (G1)

G1's file table is in [history/navigation-v1.md](history/navigation-v1.md#where-the-code-goes-g1); v2's is [Where the code is](#where-the-code-is).

### Settings
| Key | Type | Default | Meaning | Stage |
|---|---|---|---|---|
| `nav.mode` | Int 0..=2 | 1 | 0 Buttons, 1 Gestures (Thumb map), 2 N9 gestures (Navigation v2; G1 had 0 Classic, 1 Gestures) | G1, NV |
| `nav.swipe_close` | Bool | off | Top edge on an app closes it; the shade then opens by tap only | G4 |
| `nav.switcher_cols` | Int 2..=3 | 2 | Open apps columns | G3 |
| `home.style` | Int 0..=1 | 0 | 0 Pages (Belle), 1 Lanes (N9) | G5 |

All are `Owner::Shell`; `nav.swipe_close`, `nav.switcher_cols` and `home.style` were registered on 2026-11-27 (D10).
Gestures (Thumb map) is the default since Navigation v2 (2026-11-17). The Settings page for
these is `set2-navigation` in the Settings app ([settings.md](settings.md#the-settings-app-neoset)).

### Classic and Gestures (G1; replaced by [Five places](#five-places-one-strip-every-app-two-modes-v1-replaced-by-navigation-v2))
G1's two modes, replaced twice: [history/navigation-v1.md](history/navigation-v1.md#classic-and-gestures-g1-replaced-by-five-places).

### The server (G1)
How G1's server fed the recognizer and drew the hint: [history/navigation-v1.md](history/navigation-v1.md#the-server-g1).

### Checks (G1)
G1's host tests and Syborg CI walk (2026-11-16): [history/navigation-v1.md](history/navigation-v1.md#checks-g1).

## G2: peek
- When a gesture locks, the screen as it is becomes a layer: the S2b snapshot, with the front app's surface folded
  in. Slint draws the target once into the frame: Open apps for the right edge, home for the bottom edge.
- Each frame then copies the layer at the finger's offset over the target. This is `layer::Slide`, extended to
  vertical movement for the bottom edge.
- Letting go before the commit point settles back in 250 ms; letting go past it settles onto the target.
- **Memory:** the same single 9.3 MB snapshot the fades use, reserved with `try_reserve_exact`. Without memory, G1's
  hint-and-fade runs instead.
- Back gets no peek: what the app shows after Back is drawn by the app only after it gets the event. It keeps G1's
  hint.
- **A preview is not a screen change** (from the Codex review). Today a screen change replaces `old`, starts a fade
  and hides the app (`host.set_screen`), which would destroy the layer being slid.
  - While a peek runs, the shell's `screen`, `view` and `origin` are saved, and the fade and the app lifecycle are
    held back.
  - Letting go short restores them. Committing applies the change once, with no fade, because the slide was the
    animation.
  - The bottom edge's target switches from home to the Apps menu at the half-height point, and back if the finger
    returns.

## G3: Open apps with thumbnails
**Built 2026-11-27** (neoui#61, Settings D10): the thumbnail is the app's last frame, taken before its frame is
released; close mode in Gestures and N9 (Buttons keeps its ×). The design as written:

- When an app is hidden (`Visible(false)` in `host.set_front`), the server downscales its surface into a thumbnail at
  the card's size. That is about 0.3 MB for a 2-column card on the Pixel, at most 4 apps (`MAX_RUNNING`).
- The cards show the thumbnail instead of the icon (`switcher.slint`'s `shortcut:`).
- `nav.switcher_cols` picks 2 or 3 columns. A pinch is the N9's way, but needs multi-touch (below).
- **Close mode (N9):** a long press (500 ms) on a card shows × on all of them; a tap outside the cards leaves.

## G4: swipe down to close
**Built 2026-11-27** (neoui#61, Settings D10): it closes strictly past half the height, with no fling; a resident goes
home still running. The design as written:

- With `nav.swipe_close` on, a press on the status bar while an app is in front is tracked by the recognizer (a
  `Top` edge).
- The app follows the finger down. Past half the height it closes through `host.close` (`AppEvent::Quit`, killed
  after 3 s); a shorter swipe returns.
- The shade then opens only by a tap on the status bar.
- A resident app (NEOPHONE) is hidden, not closed, as the switcher's × does today.

## G5: Lanes home
**Built 2026-11-27** (neoui#61, Settings D10): Events holds the agenda and the shade's cards; Home shows every page
in one column. Not run on the phone yet. The design as written:

- With `home.style` = 1, home becomes three lanes, swiped sideways with the S2c slide:
  - **Events:** neoui-shell Part 2's notifications and the agenda;
  - **Home:** the widget pages, merged into one page;
  - **Open apps:** the switcher's cards.
- The Apps menu stays on the bottom edge rather than becoming a lane. The bottom swipe is how every mode reaches it.
- The right edge opens the Open apps lane, and Home the lane used last (the N9's behaviour).

## G6: lock screen
**Moved (2026-11-21):** the lock screen is now [top-panel.md](top-panel.md#lock-screen-tp8) TP8; its any-edge
unlock and double-tap wake are kept there. The notes below are the original G6 sketch.

- There is no lock screen today: `now.slint` only names it.
- G6 adds one: the time, the date and notification counts.
  - Unlock by swiping in from any edge. The screen slides away in that direction, using G2's layer.
  - The N9's quick-launch bar comes on a bottom swipe that stops short.
- **Double-tap to wake** needs the touchscreen to report taps while the display is dark. Today the kernel's
  touchscreen sleeps with the screen (`symbian/src/lib.rs`: "a dark screen takes no touches"). This needs work in the
  kernel's `sdm670_assp` touch driver, so it is a kernel item.

## Later
- **Multi-touch:** since neoui `93a02a3` (2026-11-17) fingers after the first reach the app they pressed in (an old
  app's Gamepad moves and fires at once); gestures and the shell's widgets still follow finger 0. A pinch on Open apps
  (2 ↔ 3 columns) needs the shell to follow a second finger.
- **A slimmer toolbar** in gesture mode (above).
- **Haptics** on commit, once there is a vibrator driver.

## Gates for every stage
- `neoui`: `cargo fmt --check && cargo clippy --all-targets -- -D warnings && cargo test`, plus
  `cargo build -p neoui-proto -p neoui-render --target thumbv7em-none-eabihf`.
- `neoui/symbian`: `cargo fmt --all --check && cargo arm --workspace`.
- CI: neoui's `virt-taps` drives the gestures with `symbian/taps.sh`'s `swipe` on QEMU `virt` (US6b; before
  2026-11-25 this was the Syborg CI).
- By hand: the phone (RAM boot; `neo live` was removed in US5, a `virt` view is US6b). Check the edges with a thumb, and that taps on the toolbar and
  the dock never trigger a gesture.

When a stage lands, mark it in the stages block at the top (`tools/roadmap.py` rebuilds
[roadmap.md](../roadmap.md)'s board) and update the org profile's status list.
