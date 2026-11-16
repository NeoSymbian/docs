# Gesture navigation: the N9 mix

**Status: designed 2026-11-16 (reviewed by Codex the same day); G1 and the [Five places](#five-places-one-strip-every-app-two-modes) strip and Page API built (neoui, NEOPHONE), checked on the phone from RAM.** This page designs gesture navigation for neoui, the Rust UI shell.
It is written so that a later session can build any stage from this page alone. The model is the Nokia N9's Swipe UI
(MeeGo Harmattan, 2011). It is not Android's or iOS's. Gestures sit beside the classic Belle/N8 toolbar, and the
user picks one or the other in Settings.

It belongs to roadmap stage U3 ("system apps in Rust", [roadmap.md](roadmap.md)) and builds on
[neoui-shell.md](neoui-shell.md) (the settings store, notifications, home pages) and [smooth-ui.md](smooth-ui.md)
(the server's layers and slides).

| Stage | What | Status |
|---|---|---|
| G1 | Edge recognizer; `nav.mode`; Settings → Home screen & navigation; Back, Open apps, Home and Apps menu by edge swipe; an edge hint | Built 2026-11-16 (host tests, CI flow, phone) |
| P | **Five places:** one shell-drawn bottom strip for every app, the Page API (apps declare, the shell draws), window rules | Built 2026-11-16 (P1–P3 below); Gestures as the default still to do |
| G2 | N9 peek: the screen follows the finger, with the target underneath; letting go early cancels | Planned |
| G3 | Open apps with live thumbnails, 2 or 3 columns, N9 long-press close mode | Planned |
| G4 | Swipe down from the top to close an app (N9's option) | Planned |
| G5 | Lanes home: Events · Home · Open apps side by side | Planned |
| G6 | N9 lock screen: swipe in from any edge to unlock; double-tap to wake | Planned |

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

## Five places: one strip, every app, two modes

**Decided 2026-11-16** by the owner, after a first idea (apps drawing their own bars, a system bar under an app bar in
Classic, ⋮ moving between the app bar and the status bar) turned out too complex. Codex and Claude each proposed a
model; both arrived at "apps declare, the shell draws". This chapter is the merged result. It replaces G1's
"Classic and Gestures" section.

### The rules
1. **Apps draw content; the shell draws everything else:** the status bar, the bottom strip, the Options sheet,
   dialogs and the keyboard. They look and behave the same in every app.
2. **One bottom strip, 56 dp, the same height in both modes.**
   - The app body is always 360 × 639 dp (720 − 25 status − 56 strip).
   - Switching modes never resizes an app.
3. **The strip has two groups:**
   - system: `← Back`, `⌂ Home`, `▢ Open apps`;
   - app: `Cancel` (forms only), the **primary** action as a pill, `⋮` Options.
4. **Gestures removes the system group.**
   - The edges do its work: left = Back, bottom = Home (keep going = Apps menu), right = Open apps, top = shade.
   - The app group spreads over the whole strip.
5. **One primary action per page** (Call, Save, New, Send). Everything else is in `⋮`.
   - `⋮` shows only when the page has options; `←` is dimmed when there is nowhere to go back to.
   - A screen never shows a button that does nothing.
6. **Back order:**
   1. close the sheet or dialog;
   2. then hide the keyboard;
   3. then go up one page;
   4. at an app's top page, return to where you came from (home, Apps menu, Open apps). The app keeps running.
7. **Home and Open apps never close or save anything.** Only × on an Open apps card closes an app.
8. **Full screen** (call, camera, video, game) hides the status bar and the strip.
   - In Gestures the edges still work.
   - In Classic a tap shows the strip for 3 s.
9. **The keyboard covers the strip while it is open** and brings its own hide key. The strip returns when it closes.
10. **Classic always shows the strip,** home included. There, the page's main action is Apps (the app menu) and ⋮ holds
    Edit home and Wallpaper. Gestures home has no strip; its dock carries Apps, and the edges do the rest. (Owner,
    2026-11-16.)
11. **One title, in the status bar.** The shell shows the page's title at the left of the 25 dp status bar, as Belle
    did, and the app draws no header or title strip: its content starts right under the status bar.
    - A page switch (Phone | Contacts) is a sideways swipe plus dots that the shell draws beside the title
      (`Phone ● ○`).
    - Icons that sat in a header (the contact card's ★) move into the content or into ⋮.
    - Before this rule, NEOPHONE drew a 52 dp title strip under a status bar that already showed the title, so the
      title appeared twice.

### Arrangement (`nav.strip`, Classic only)
| Value | Strip | Note |
|---|---|---|
| 0 (default) | `│ ← ⌂ ▢ │ Cancel ( Save ) ⋮ │` | System left, app right, under the right thumb. Back stays bottom-left, as on Belle and the N9 |
| 1 | `│ Cancel ( Save ) ⋮ │ ← ⌂ ▢ │` | App left, system right |
| 2 | `│ ← ⌂ │ Cancel ( Save ) ⋮ │ ▢ │` | Split: the system at both ends, matching the edges (left = Back, right = Open apps) |

In Gestures the arrangement doesn't matter. The app group fills the strip: `│  Cancel      ( Save )       ⋮  │`.

### Every state
Each state below is shown in both modes. The arrangement is 0. Every state carries its title in the status bar
(rule 11); the sketches show the strip only.

```text
App root (Contacts)                       Sub-page (contact card)
Classic  │ ← ⌂ ▢ │        ( New )   ⋮ │   Classic  │ ← ⌂ ▢ │       ( Call )   ⋮ │
Gestures │          ( New )          ⋮ │   Gestures │          ( Call )         ⋮ │
         ← dimmed: nothing to go back to

Form (contact editor)                     Page with no actions or options (Settings)
Classic  │ ← ⌂ ▢ │ Cancel ( Save )    │   Classic  │ ← ⌂ ▢ │                    │
Gestures │  Cancel      ( Save )       │   Gestures │                             │  (empty strip, 56 dp kept)

Options open                              Dialog (QUERY)
  the shell's sheet rises above the strip   centred card, buttons from the app (≤ 3),
  Back or a tap outside closes it           destructive one red; Back = the last button

Keyboard open                             Full screen (active call, camera, video)
  keyboard over the strip, own hide key     no status bar, no strip; the call's own buttons
  Back first hides the keyboard             Gestures: edges work; Classic: tap → strip for 3 s

Home                                      Apps menu / Open apps (shell screens, same strip)
Classic  │ ← ⌂ ▢ │       ( Apps )   ⋮ │     Apps:      primary none, ⋮ none
  ← dimmed, ⌂ lit; ⋮ = Edit home, Wallpaper  Open apps: primary Home, ⋮ Close all
  dock: Phone · Messages · Browser · Camera
Gestures: no strip on home; dock:
  Phone · Messages · Browser · Camera · Apps
```

- **Incoming call:** full screen with its own Answer and Reject.
- **Legacy S60 apps:** the app group stays empty. Their softkeys come with the on-screen keypad (docs
  [legacy.md](legacy.md)).
- **Lock screen:** G6.

### Window management
- **Tasks:**
  - One task per app identity.
  - Phone, Contacts and Messages are one task, NEOPHONE (`host.rs` `ALIASES`).
  - Shell screens (Settings, Apps menu, Open apps) are not tasks.
- **Pages:** each app keeps its own page stack and tells the shell whether Back stays inside it (`can_back`).
- **Open apps:** the running tasks, most recent first, the current one included.
- **At most 4 processes**, the resident Phone and a legacy guest included.
  - Before a new launch, the shell closes the least recently used hidden task that isn't resident.
  - That task gets `Quit` and has 3 s to save.
  - Today `host.rs` starts the new app first and then limits (`start` before `limit_running`); the order flips.
- **The resident Phone** is never closed. Its Open apps card offers Dismiss, which hides it.
- **Home, switching apps and a forced screen** (an incoming call, an alarm) keep pages and drafts. Apps save drafts
  as they go.

### The Page API
Apps declare their page. The shell does the drawing, the Options sheet, dialogs and Back. The protocol is `NeoUi`
1.7, additive. The pure logic lives in `neoui-proto::page`, host-tested.

| Opcode | Arguments | What |
|---|---|---|
| `PAGE = 15` | `Des8` encoded `Page` | Sent whenever the page changes |
| `QUERY = 16` | `Des8` encoded `Query` | A shell dialog; the answer comes back as an event |

```rust
Page {
    title: String,               // the status bar shows it (≤ 48 bytes, like TITLE)
    can_back: bool,              // Back goes to the app (else the shell handles it)
    primary: Option<Action>,     // Action { icon: TOOL_*, label }: the pill
    cancel: bool,                // a form: Cancel beside the primary
    options: Vec<String>,        // ≤ 12 labels of ≤ 32 bytes; empty = no ⋮
    full: bool,                  // full screen: no status bar, no strip
    dots: Option<(u8, u8)>,      // a page switch: (count, current); the shell draws the dots beside the title
}
Query { text: String /* ≤ 160 bytes */, buttons: Vec<String> /* 1..=3 */, destructive: bool /* the first is red */ }
```

- **Events** (16 bytes each, as today): `Primary`, `Cancel`, `Option(i)`, `Back` (only while `can_back`) and
  `Answer(i)`. `Visible`, `Keyboard`, `Quit`, `Page` and input are unchanged.
- **`neoapp`:** `app.page(&Page)`, `app.query(&Query)`, `app.close_query()`.
- **The keyboard** stays with `KEYBOARD` (it answers with the height), so the Page has no keyboard field.
- **Old apps:** an app that never sends `PAGE` gets an implied Page:
  - the title from `TITLE`;
  - the primary from `TOOLBAR`;
  - `can_back` from its `NAV` Back claim;
  - an Options claim becomes a bare `⋮` that sends today's `Options` event, so app-drawn sheets keep working.

  Apps move over one at a time.
- **Full screen:** every app surface is allocated at the full screen size (1080 × 2160 on the Pixel, about +1.5 MB
  per app). A normal page uses the 639 dp body. A page with `full` gets the whole screen: `neoapp` resizes the app's
  window when the app sends that Page. The app asked for it, so the resize never comes as a surprise. Mode switches
  never resize anything.

### Build order
All six built on 2026-11-16 except the last: neoui `bf258d9` (1), `47769cc` (2), `949cc6c` (3), `873dc49` (4), and
NEOPHONE `24328b1` (5). On the phone the owner asked for one change: in Gestures, a shell screen with nothing in the
strip (the Apps menu, Settings) has no strip at all, and an app's empty strip is plain black (neoui `28b512f`).

1. **`neoui-proto`:** `page.rs` (Page and Query encode/decode with limits) and its tests; `ipc.rs` 1.7; the registry
   key `nav.strip` 0..=2.
2. **Shell:**
   - a `Strip` (`ui/components/frame.slint`) replaces `Toolbar`, with both groups, the three arrangements and the
     full-width app group in Gestures;
   - the Options sheet (`OptionsMenu`) is filled from the Page;
   - the shell's own screens declare Pages;
   - the keyboard gets a hide key;
   - home's Page (Classic strip with Apps and ⋮); the dock is Phone · Messages · Browser · Camera, plus Apps in
     Gestures.
3. **Server** (`symbian/src/host.rs`, `lib.rs`):
   - store each app's Page and build the implied Page;
   - route Primary, Cancel, Option and Back;
   - full screen;
   - evict before launch.
4. **`neoapp` and the neoui apps:** Clock, Files, Dev tools and Terminal declare honest Pages.
5. **NEOPHONE:**
   - its per-view `Chrome` tables (`ctx.rs`) become Pages;
   - simple dialogs become `query()`;
   - its own Options sheet goes away.
6. **`nav.mode` defaults to Gestures** after the phone check.

## The recognizer (G1)
A pure state machine in `neoui-proto::gesture` (`no_std`, Apache-2.0, host-tested). It knows nothing about
screens. The UI server feeds it touches and acts on what it returns.

**Input:** `feed(phase, x, y, ms, live_edges)`.
- The phase is `TouchPhase`. The coordinates are screen pixels.
- `ms` is `time::millis()` read when the server takes the batch; the kernel's events carry no time.
- The server feeds every touch **before** `coalesce_moves`. A merged move could hide a drag that started along the
  edge. Only what the recognizer lets through is merged and routed.

**Sizes, in dp** (scaled by the server's `dp256`: 1 dp = 3 px on the Pixel, 1.78 px on Syborg):

| Value | dp | Why |
|---|---|---|
| Edge zone | 16 | Wide enough for a thumb on a flat screen. Narrow enough to leave the toolbar's buttons and the dock to taps |
| Slop | 8 | The same as the home slide (S2c) |
| Side commit | 72 | About a fifth of the width: a deliberate swipe, not a brushed edge |
| Bottom Home | 80 | Past the toolbar (61 dp), so a press on the toolbar that slips doesn't go home |
| Bottom Apps menu | half the screen height | One continuous swipe |
| Fling | ≥ 24 dp moved, last segment ≥ 0.5 dp/ms | A short fast flick also counts, from the side edges only. The bottom edge takes no flings, so a press on the toolbar that slips up fast doesn't go home |

**States:**
1. **Idle.** A press outside every edge zone returns `Pass`; the server routes the touch as today. A press inside a
   zone returns `Hold`. The server keeps the press back from the app and from Slint. It keeps at most two touches,
   the press and the latest move.
2. **Held.** Moves stay held until the finger has gone `slop` from the press.
   - If the move is mostly inward (along the gesture's axis, `|along| > |across|`, and toward the screen's middle),
     the gesture **locks**: `Track { edge, progress }`.
   - Otherwise (a move along the edge, or outward), the recognizer returns `Replay`. The server sends the held press
     and the moves after it through the normal path. The app or Slint never knows the touch was held.
   - A release while held (a tap in the zone) also returns `Replay`. The tap reaches the toolbar button, the dock or
     the app.
   - **What a replay costs:** the press reaches the app or Slint only once the touch is known not to be a gesture.
     A button in the zone shows as pressed late, and a long press in the zone starts its timer late.
3. **Tracking.** Each move returns `Track { edge, progress }`. `progress` runs 0..=256 toward the commit distance.
   For the bottom edge, past 256 it grows toward the Apps menu point (512), so the hint can show the second stage.
4. **Release.** The recognizer returns `Commit(gesture)` if the distance or a fling meets the threshold, else
   `Cancel`.

**Edges per screen:**
- The server passes the live edges with each press:
  - home: right and bottom (the left edge stays with the pages' slide, and Back does nothing there);
  - every other screen: left, right and bottom;
  - none on the lock screen (G6).
- The top edge stays with the status bar's own pull in G1.
- No edge is live, and the recognizer only passes touches through, when any of these holds:
  - `nav.mode` is 0;
  - the shade is open;
  - the Power menu or the SIM PIN prompt shows;
  - a fade or the home slide runs.

**Ownership:** while the recognizer holds or tracks a touch, nothing else sees it.
- When the screen changes under it (a call, an alarm, the PIN prompt, an app asking to come to the front), the server
  calls `reset`. The held touches are dropped, and so is the rest of that touch up to the release (`Step::Drop`).
- A replay happens in the same batch as the move that decided it, so the touch goes where it would have gone without
  the hold.

## Where the code goes (G1)

| Layer | Path | What |
|---|---|---|
| Pure logic | `neoui/crates/neoui-proto/src/gesture.rs` | `Edge`, `Gesture`, `Recognizer`, `Step`; unit tests |
| Setting | `neoui-proto/src/settings/registry.rs`, `neoui-render/src/settings.rs`, `ui/system-settings.slint` | `nav.mode`, following "Adding a setting" in [neoui-shell.md](neoui-shell.md) |
| Settings page | `ui/screens/settings.slint` | Root row "Home screen & navigation" → view `navigation` |
| Shell | `ui/shell.slint`, `ui/components/frame.slint` | Back arrow hidden in gesture mode (`Toolbar.no-back`; its place stays empty); `nav-back()` is the toolbar Back's path, shared with the gesture |
| Renderer | `neoui-render/src/lib.rs` | `Renderer::gesture(Gesture)` |
| Server | `neoui/symbian/src/lib.rs` | The recognizer before `coalesce_moves`; the hint bar (`hint_rect`, `draw_hint`) |
| Driver | `neoui/symbian/taps.sh`, `neoui/.github/workflows/syborg.yml` | A `swipe` helper and a gesture flow |

### Settings
| Key | Type | Default | Meaning | Stage |
|---|---|---|---|---|
| `nav.mode` | Int 0..=1 | 0 | 0 Classic (the toolbar's Back), 1 Gestures | G1 |
| `nav.swipe_close` | Bool | off | Top edge on an app closes it; the shade then opens by tap only | G4 |
| `nav.switcher_cols` | Int 2..=3 | 2 | Open apps columns | G3 |
| `home.style` | Int 0..=1 | 0 | 0 Pages (Belle), 1 Lanes (N9) | G5 |

All are `Owner::Shell`. Classic stays the default until gestures have been checked by hand on the phone; then the
default may flip.

**Settings → Home screen & navigation** (view `navigation`, a root row after Display):
- Navigation: Classic / Gestures. A tap steps to the other, like Screen timeout.
- Under it, one line saying what the edges do in the chosen mode.
- Later stages add their rows here: Swipe down closes apps (G4), Open apps columns (G3), Home style (G5).

### Classic and Gestures (G1; replaced by [Five places](#five-places-one-strip-every-app-two-modes))
- **Classic** is exactly today's navigation.
- **Gestures** hides the toolbar's Back button. Action, Options and the keyboard toggle stay, so an app's `NAV`
  claims keep working. Back by gesture runs the same path as the button:
  - the app's `AppEvent::Back` if it claimed Back and no overlay is open;
  - otherwise the shell's `back()`.
- **Later:** a slimmer toolbar in gesture mode. It changes the app body's geometry (`app-body-h`), so apps would need
  to handle a resize; not in G1.

### The server (G1)
In the event loop (`symbian/src/lib.rs`, the `InputEvent::Touch` arm):
- **On a press,** the recognizer is fed when all of these hold:
  - `nav.mode` is 1;
  - no overlay is open (shade, Options, keyboard), no Power menu, no `phone.modal()`;
  - no transition or home slide is running.
- **`Hold`:** the event is kept in a small buffer and the loop moves on.
- **`Replay`:** the buffer goes through the existing routing:
  - the `home_press` slide check;
  - `to_app`, or `ui.dispatch`;
  - `take_nav`, `take_typed`, `take_closed`.

  That code becomes one function so the live and replayed paths can't drift apart.
- **`Track`:** the server draws the hint itself. It is a 4 dp bar along the edge (`hint_rect`):
  - it gets longer as the finger goes in;
  - it is grey before the commit point, in the accent colour past it, and white past the Apps menu point;
  - it is drawn straight to the screen after the app is composed. Each frame, the strip it covered is put back from
    the frame with the app's surface over it.

  It can't be a Slint overlay: any shell damage over an app's area makes the server copy the app's whole surface
  over it again.
- **`Commit`:** `ui.gesture(g)`:
  - **Back:** `nav-back()`, then the usual `take_nav` → `AppEvent::Back`;
  - **OpenApps:** `open("switcher")`, so Back returns to where it was opened from;
  - **Home:** `show("home")`, or the Apps menu when home already shows;
  - **AppsMenu:** `show("menu")`.

  The screen-change fade (smooth-ui S2b) animates the change as for any other screen change.
- **`Cancel`:** the hint is cleared.
- Each commit logs `neoui: gesture back|apps|home|menu` for CI.

**Interactions with what already exists:**
- **The home pages slide** starts only on a press outside the edge zones, so the two never compete. At the home
  screen's left and right edges the slide gives way to the edge gestures.
- **An incoming call or an alarm** forces its screen as today. A gesture already being tracked is cancelled when the
  screen changes under it.
- **The keyboard** sits above the toolbar, so the bottom zone (inside the toolbar) never covers a key. Every edge
  stays live while it shows.
- **During a call,** Back leaves the call screen and the call keeps running, as with the toolbar today
  (`call::back` returns false).

### Checks (G1)
- **Host:**
  - `neoui-proto` `gesture` tests (12): tap and along-edge replay, distance and fling commits, a short slow swipe
    cancels, a fast slip up from the toolbar stays, home and Apps menu from the bottom, corners, reset, scaling with
    dp;
  - `neoui-render` `tests/gestures.rs`: every gesture through the shell's paths, the Back arrow gone in gesture mode;
  - snapshots `settings-navigation-pixel.png` and `settings-navigation-classic-pixel.png`.
- **Syborg CI** (`syborg.yml`, "gesture navigation"), at 539×1079:
  1. turn gestures on in Settings;
  2. Back twice from the left edge;
  3. Home, then the menu, from the bottom;
  4. Clock hidden by Back from the left edge;
  5. Open apps from the right edge;
  6. a long swipe up to the menu;
  7. a tap inside the bottom zone still reaches the toolbar;
  8. back to Classic.
- **Phone:** by hand, with a thumb.

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
- When an app is hidden (`Visible(false)` in `host.set_front`), the server downscales its surface into a thumbnail at
  the card's size. That is about 0.3 MB for a 2-column card on the Pixel, at most 4 apps (`MAX_RUNNING`).
- The cards show the thumbnail instead of the icon (`switcher.slint`'s `shortcut:`).
- `nav.switcher_cols` picks 2 or 3 columns. A pinch is the N9's way, but needs multi-touch (below).
- **Close mode (N9):** a long press (500 ms) on a card shows × on all of them; a tap outside the cards leaves.

## G4: swipe down to close
- With `nav.swipe_close` on, a press on the status bar while an app is in front is tracked by the recognizer (a
  `Top` edge).
- The app follows the finger down. Past half the height it closes through `host.close` (`AppEvent::Quit`, killed
  after 3 s); a shorter swipe returns.
- The shade then opens only by a tap on the status bar.
- A resident app (NEOPHONE) is hidden, not closed, as the switcher's × does today.

## G5: Lanes home
- With `home.style` = 1, home becomes three lanes, swiped sideways with the S2c slide:
  - **Events:** neoui-shell Part 2's notifications and the agenda;
  - **Home:** the widget pages, merged into one page;
  - **Open apps:** the switcher's cards.
- The Apps menu stays on the bottom edge rather than becoming a lane. The bottom swipe is how every mode reaches it.
- The right edge opens the Open apps lane, and Home the lane used last (the N9's behaviour).

## G6: lock screen
- There is no lock screen today: `now.slint` only names it.
- G6 adds one: the time, the date and notification counts.
  - Unlock by swiping in from any edge. The screen slides away in that direction, using G2's layer.
  - The N9's quick-launch bar comes on a bottom swipe that stops short.
- **Double-tap to wake** needs the touchscreen to report taps while the display is dark. Today the kernel's
  touchscreen sleeps with the screen (`symbian/src/lib.rs`: "a dark screen takes no touches"). This needs work in the
  kernel's `sdm670_assp` touch driver, so it is a kernel item.

## Later
- **Multi-touch:** `to_input` (`symbian/src/lib.rs`) reports every touch as id 0, and `Renderer::dispatch` drives one
  Slint pointer. A pinch needs the second finger from the kernel's touch driver, then ids through `InputEvent`.
- **A slimmer toolbar** in gesture mode (above).
- **Haptics** on commit, once there is a vibrator driver.

## Gates for every stage
- `neoui`: `cargo fmt --check && cargo clippy --all-targets -- -D warnings && cargo test`, plus
  `cargo build -p neoui-proto -p neoui-render --target thumbv7em-none-eabihf`.
- `neoui/symbian`: `cargo fmt --all --check && cargo arm --workspace`.
- Syborg: the `syborg` CI drives the gestures with `symbian/taps.sh`'s `swipe`.
- By hand: QEMU over VNC (`neo live`), then the phone. Check the edges with a thumb, and that taps on the toolbar and
  the dock never trigger a gesture.

When a stage lands, mark it in the table at the top, and update [roadmap.md](roadmap.md) U3 and the org profile's
status list.
