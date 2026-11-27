<!-- SPDX-License-Identifier: Apache-2.0 -->
# Navigation v1: Five places and the G1 build

Part of [neoui shell](../README.md) · Status: record · Updated: 2026-11-27

Moved out of [navigation.md](../navigation.md) on 2026-11-27 and kept as written: v1's Five places design (built
2026-11-16, replaced by Navigation v2 on 2026-11-17) and the G1 chapters (the recognizer as designed, where its code
went, the shell's G1 Settings page, Classic and Gestures, the server, the checks). The live design is
[Navigation v2](../navigation.md#navigation-v2).

## Five places: one strip, every app, two modes (v1, replaced by Navigation v2)

**v1. Replaced 2026-11-17 by [Navigation v2](../navigation.md#navigation-v2):** apps draw their header, and the strip is now a key
row or a band. **Decided 2026-11-16** by the owner, after a first idea (apps drawing their own bars, a system bar under an app bar in
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
  [legacy.md](../../user-side/legacy.md)).
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
| Setting | `neoui-proto/src/settings/registry.rs`, `neoui-render/src/settings.rs`, `ui/system-settings.slint` | `nav.mode`, following "Adding a setting" in [README.md](../README.md) |
| Settings page | `ui/screens/settings.slint` | Root row "Home screen & navigation" → view `navigation` |
| Shell | `ui/shell.slint`, `ui/components/frame.slint` | Back arrow hidden in gesture mode (`Toolbar.no-back`; its place stays empty); `nav-back()` is the toolbar Back's path, shared with the gesture |
| Renderer | `neoui-render/src/lib.rs` | `Renderer::gesture(Gesture)` |
| Server | `neoui/symbian/src/lib.rs` | The recognizer before `coalesce_moves`; the hint bar (`hint_rect`, `draw_hint`) |
| Driver | `neoui/symbian/taps.sh`, `neoui/symbian/us6b/syborg-taps.yml` (was `.github/workflows/syborg.yml`) | A `swipe` helper and a gesture flow |

### Settings (the shell's page in G1)

**Settings → Home screen & navigation** (view `navigation`, a root row after Display):
- Navigation: Classic / Gestures. A tap steps to the other, like Screen timeout.
- Under it, one line saying what the edges do in the chosen mode.
- Later stages add their rows here: Swipe down closes apps (G4), Open apps columns (G3), Home style (G5).

### Classic and Gestures (G1; replaced by [Five places](#five-places-one-strip-every-app-two-modes-v1-replaced-by-navigation-v2))
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
