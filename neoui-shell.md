# neoui shell services: settings, notifications, home pages and widgets

**Status: Part 1 (settings) done 2026-11-09 on neoui branch `shell-services`; the rest planned.** This is the design for four shell services
in neoui, written so that a later session can build any one part from this page alone. The parts are:
- step 0: knowing who is calling;
- part 1: one settings store;
- part 2: a notification service;
- part 3: home pages with pin and unpin;
- part 4: widgets.

It belongs to roadmap stage U3 ("system apps in Rust", [roadmap.md](roadmap.md)).

| Part | What | Status |
|---|---|---|
| 0 | Know who is calling: the client's secure ID, service sessions | Planned |
| 1 | One settings store for the shell and every app | **Done** (2026-11-09, neoui `shell-services`) |
| 2 | Notification service: status bar icons, badges, shade list, urgent banner | Planned |
| 3 | Home pages of widgets and shortcuts (Belle style), pin and unpin, dock, edit mode | Planned |
| 4 | Widgets: drawn by the shell from data the app sends | Planned |

Build them in this order. Each later part saves its state through the settings store, and each part ships on its own
with its tests and a Syborg boot check.

## Where things are today (2026-11-09)

neoui is the Rust UI server `SYSSTART.EXE` (`neoui/symbian`) plus the Slint shell (`neoui/ui`). The parts this design
touches are mock-ups:
- **Home:** `ui/screens/home.slint` hard-codes `BigClock`, an `AgendaCard`, the favourites card and a `MusicCard` on
  fixed pages. The UI server already drives the swipe between pages (smooth-ui S2c: `home-page`, `home-strip-h` in
  `ui/shell.slint`).
- **Shade:** `ui/components/shade.slint` has quick toggles and nothing else.
- **Settings:** `ui/screens/settings.slint` holds `in-out` properties (`wifi`, `bluetooth`, `data`, `airplane`,
  `dark`, `brightness`) that nothing saves or reads.
- **Status bar:** `StatusBar` in `ui/components/frame.slint` shows the clock, signal bars, operator and RAT. The icon
  set in `ui/icons/sys/` already has message, missed call, alarm, bell, silent and vibrate.
- **IPC:** the app ↔ server protocol `NeoUi` (`crates/neoui-proto/src/ipc.rs`, version 1.0) has opcodes 1–7:
  - `GEOMETRY`, `SURFACE`, `DAMAGE`, `NEXT_EVENT`, `KEYBOARD`, `NAV`, `POWER`;
  - the events are `AppEvent::{Input, Quit, Back, Options, Visible}`, 16 bytes each.
- **Apps:** a fixed table `APPS` (`symbian/src/host.rs`) maps screen keys to EXEs:
  - `clock` → `NEOCLOCK.EXE`, `terminal` → `NEOTERM.EXE`, `files` → `NEOFILES.EXE`, `devtools` → `NEODEV.EXE`;
  - UIDs `0xE0002002`–`0xE0002005` in `symbian/exes.txt`, with `SYSSTART` at `0xE0002001`;
  - other screens (phone, messages, calendar, settings…) are drawn by the shell itself.
- **Saving files:** the only pattern so far is Clock's `C:\private\e0002001\clock.dat` (`symbian/src/clock.rs`,
  `neoui-proto/src/clock.rs`). It uses `File::replace` and `read_at` from `e32::fs`. `Fs::rename` exists too.
- **Modem:** the shell is already a client of the modem server `NeoModem` (`MODEMD.EXE`, started by SYSSTART,
  `symbian/src/phone.rs`). It gets call state and signal from it.

## Decisions

| Question | Decision | Why |
|---|---|---|
| Who draws a widget | **Data first:** the app sends content, the shell draws it with a few built-in layouts. The protocol reserves a `Surface` kind so app-drawn widgets can come later | Costs no process or memory per widget (at most 4 apps run at once, and a surface is ~7 MB on the phone). The app need not be running, and every widget matches the house style |
| Home layout | **Belle style:** home pages hold widgets and shortcuts; every app stays in the Menu; pinning adds a shortcut or a dock slot | Keeps the "Belle, modernized" direction of `neoui/design/DESIGN.md` |
| What a new notification does | Always a status bar icon, a badge on the app's icon and a row in the shade. **Urgent** ones (call, alarm, SMS) also slide down a banner | Visible without being noisy |
| Where an app's own settings live | **One store.** The Settings app shows global settings and per-app notification switches. An app's own options stay inside the app but are saved in the same store | One file, one format, one change event |

## Where the code goes

No new crates; this follows the existing split.

| Layer | Path | New |
|---|---|---|
| Pure logic: `no_std`, Apache-2.0, host-tested | `neoui/crates/neoui-proto/src/` | `settings.rs`, `notify.rs`, `home.rs`, `widget.rs`; new opcodes and events in `ipc.rs` |
| UI server (GPL-3.0) | `neoui/symbian/src/` | `settings.rs` (store and file, after `clock.rs`), `notify.rs`; opcodes in `host.rs` (`impl Service for Host`) |
| Shell UI | `neoui/ui/` | `screens/home.slint` reworked; `components/widgets.slint`, `components/banner.slint`; the shade list, badges and settings wiring |
| App helper | `neoui/symbian/neoapp/src/lib.rs` | `setting()`, `set_setting()`, `notify()`, `cancel()`, `widget()` over the app's session |
| e32 | `e32-rs/crates/e32/src/server.rs` | `Message::client_sid()` (step 0) |

Processes outside neoui (Apache-2.0, for example in `telephony`) must not link the GPL `neoapp`. They encode with
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

## Part 1: settings store (done 2026-11-09)

As built. It changes the first sketch: typed keys, a registry, change subscriptions per prefix, and the pure logic
in `neoui-proto`.

### Where it is
| Path | What |
|---|---|
| `neoui-proto/src/settings/value.rs` | `Value` (`Bool`, `Int(i32)`, `Str` ≤ 64 B, `Bytes` ≤ 2 KB), `ValueType`; one encoding (tag byte + payload) for IPC and the file |
| `…/key.rs` | Key names (`ns.name`, `[a-z0-9_]`, ≤ 32 B), typed `Key<T>` (checked at compile time; invalid names don't compile), the sealed `Setting` trait for `bool`/`i32`/`String`/`Bytes` |
| `…/registry.rs` | **The registry:** one `registry!` row per system setting (type, default, limit, owner). It generates `keys::*` and `REGISTRY` and checks at compile time that each default has the key's type |
| `…/store.rs` | `Store`: get (stored, else the default), set with validation; a value equal to its default is removed; a change journal (64 entries) for notifications |
| `…/file.rs` | File format v1: `NSET`, version, count, then records (key length, key, value length, value). Decode keeps every valid record and skips damaged or retyped ones; `migrate()` is the hook for later versions |
| `…/access.rs` | `Caller::{Shell, App(key)}`: the shell writes everything; an app writes registered keys it owns and unregistered keys in its own namespace. Step 0 extends it here |
| `…/service.rs` | `Service<B: Backend>`: store + backend + a 1 s save delay (each change restarts it; a failed save retries a delay later) + `flush()` + watches per session (≤ 8 prefixes) |
| `neoui/symbian/src/settings.rs` | `FileBackend`: `C:\private\e0002001\settings.dat`, atomic replace (write `settings.new`, delete, rename; load falls back to `.new`). `UiMirror` keeps the shell's view in step |
| `neoui/ui/system-settings.slint`, `neoui-render/src/settings.rs` | The `SystemSettings` Slint global (the shade and Settings bind to it two-way) and the binding table to registry keys |
| `neoui/symbian/neoapp` | `App::setting(key)`, `set_setting`, `setting_raw`/`set_setting_raw`, `watch_settings(prefix)` |

### Protocol (`NeoUi` 1.1, additive)
| Opcode | Arguments | Result |
|---|---|---|
| `SETTING_GET = 8` | `[Des8 key, Des8 out value]` | the value's length; `KErrNotFound`, `KErrArgument`, `KErrOverflow` (short buffer) |
| `SETTING_SET = 9` | `[Des8 key, Des8 value]` | 0; `KErrPermissionDenied`, `KErrArgument`, `KErrTooBig` |
| `SETTING_WATCH = 10` | `[Des8 prefix]` (empty = every key) | 0; `KErrArgument`, `KErrOverflow` (more than 8) |

`AppEvent::Settings { seq }` (kind 7) is sent at most once per frame to a session whose prefix matches a changed
key. The app reads its keys again.

### Registered keys
| Key | Type | Default | Shown in |
|---|---|---|---|
| `radio.wifi`, `radio.bt`, `radio.data`, `radio.airplane` | Bool | true, false, true, false | Shade toggles, Settings → Connectivity (UI only until there are drivers) |
| `sound.silent`, `sound.vibrate` | Bool | false, true | Shade (Silent) |
| `display.dark` | Bool | true | Settings → Display (stored; there is no light palette yet) |
| `display.brightness` | Int 0–255 | 160 | Shade slider, Settings → Display (not applied to the backlight until there's a HAL call, H4) |
| `clock.24h` | Bool | true | Settings → Display; the status bar clock and the Clock app follow it |

### Adding a setting
1. Add a row to `registry!` in `registry.rs`.
2. If the shell shows it, add a property and a `changed` handler in `system-settings.slint`, and a row in
   `BINDINGS` in `neoui-render/src/settings.rs`. Tests check every binding against the registry.

An app's private settings need neither step: it writes `<its key>.*` through `App::set_setting`.

### Log lines (for CI)
- `neoui: settings loaded N keys (vV, D dropped)`, or `neoui: settings: none saved yet, using defaults`.
- `neoui: setting KEY = VALUE (by WHO)`.
- `neoui: settings saved (N bytes)` and `neoui: settings save failed (E)`.
- In the Clock app: `clock: settings changed (SEQ): 24-hour B`.

### Tests
- **Host:** 37 settings tests in `neoui-proto`: codec, names, registry, store, journal, file (truncated, corrupt,
  retyped, oversize, newer version), access, and the service (save delay, retry, flush, watches).
- **Renderer** (`neoui-render/tests/settings.rs`): the binding table against the registry; values from the store
  show in the shade; a tap on the shade's Wi-Fi tile comes back as `("radio.wifi", true)`.
- **Still to do:** a Syborg boot check in `symbian/taps.sh`: toggle Wi-Fi, reboot, the tile stays off; 24-hour off,
  the Clock app shows 12-hour time.

### Deferred to later parts
- `notify.<app>.*` and Settings → Notifications: Part 2.
- Capability-checked writes to global keys by ROM EXEs: step 0.

## Part 2: notification service

### Model (`neoui-proto::notify`)
```text
Notification {
    app: AppKey,          // the poster's app key (checked against the session, step 0)
    id: u16,              // chosen by the app; (app, id) is unique
    priority: Low | Normal | Urgent,
    category: Message | MissedCall | Alarm | Bell | Generic,   // maps to ui/icons/sys/
    title: ≤ 48 B UTF-8,
    text: ≤ 128 B UTF-8,
    utc: i64,             // when; the shade shows "now", "5 min", "10:24"
}
```
- Posting the same `(app, id)` again **replaces** the notification and moves it to the top.
- The list is capped at 64. When it is full, drop the oldest `Low` first, then the oldest `Normal`. Never drop an
  `Urgent` to make room.
- A pure `List` type in `neoui-proto` does post, cancel, `count(app)` and an iterator of categories present, so the
  rules are host-tested.

### Protocol
| Opcode | Arguments | Result |
|---|---|---|
| `NOTIFY = 10` | `[Des8 encoded notification without app]` | 0; `KErrPermissionDenied` if `notify.<app>.on` is false (the app may ignore it) |
| `NOTIFY_CANCEL = 11` | `[id]` (or `-1` = all of the app's) | 0 |

- **`AppEvent::Opened(id)`, kind 8:** the user tapped the notification. If the app isn't running, the server starts it
  first (`Host::launch`) and queues the event for when it connects.
- **Service sessions** (step 0) post with an explicit app key out of their allowed list: `NOTIFY` takes the key as
  `Des8` argument 1.

### UI
- **Status bar** (`StatusBar`): one icon per category present, newest first, up to 3, then a "+". The silent and
  vibrate icons come from settings.
- **Badges:** a count dot on the app's icon in the Menu, on home shortcuts and in the dock. It shows "9+" above 9.
- **Shade:** a list under the toggles, newest first, grouped by app when an app has more than 3.
  - Tap opens the app (`Opened`).
  - Swipe left or right dismisses one notification.
  - "Clear all" clears every one except ongoing calls.
- **Banner** (`components/banner.slint`):
  - Shown only for `Urgent`, when `notify.<app>.banner` is on.
  - Slides down from the status bar over the current screen for 4 s, using the `popup` timing (250 ms out-quad).
  - Tap opens the app; a swipe up dismisses it.
  - Composite it as a server layer, as the S2 fades are ([smooth-ui.md](smooth-ui.md)), so the screen under it isn't
    redrawn.
  - Banners queue one at a time.
- **Opening an app doesn't clear its notifications.** The app cancels them when they are dealt with (a conversation
  marks itself read). The user can also dismiss them in the shade.

### First posters
- Dev tools (`NEODEV.EXE`): "Post notification" for low, normal and urgent. This is the test hook for CI.
- Clock: an `Urgent` alarm notification when an alarm fires.
- The shell, from `NeoModem` events: a missed call (`MissedCall`, Normal) and an incoming SMS once telephony P3 has
  SMS.

### Tests
- Host: replace, cancel, cancel-all, the cap and drop order, counts per app, encode/decode.
- Snapshot (neoui): the shade with notifications, the banner, a badge, at the Pixel and Syborg sizes.
- Syborg (`symbian/taps.sh` + MONITOR):
  1. Open Dev tools and post an urgent notification. Expect `neoui: notify devtools 1 urgent` in the serial log, and
     the banner and badge on screen.
  2. Tap the banner. Expect Dev tools in front and `Opened(1)` logged.

## Part 3: home pages, pin and unpin, dock

### Model (`neoui-proto::home`)
```text
Layout { pages: Vec<Page> /* 1..=5 */, dock: [Option<AppKey>; 4] }
Page   { items: Vec<Item> }
Item   = Shortcut(AppKey)                                   // 1×1
       | Widget { app: AppKey, name: WidgetName, size: Size }  // 4×1 | 4×2 | 2×2
```
- A page is a **4-column grid**. Items are packed in their stored order, row by row, top to bottom: a 2×2 next to
  another 2×2 or next to two shortcuts, and a 4×n on its own rows.
  - Packing order means there are no gaps to manage.
  - The same layout fits Syborg, the Pixel and odd CI sizes.
  - In landscape (360 dp tall) a page that doesn't fit scrolls vertically.
- **Operations:** `pin(app, page)`, `unpin(app)`, `pin_dock(app, slot)`, `move_to(item, page, index)`,
  `add_widget(app, name, size, page)`, `remove(item)`, `add_page`, `drop_empty_pages`.
  - All of them are pure and return an error rather than panic: full page (more than 6 rows of cells), unknown size,
    5 pages already.
- **Encoding:** `encode`/`decode` into the `home.layout` setting (Bytes, format version byte first). A layout that
  fails to decode falls back to the default and is logged.
- **The default layout** reproduces today's page 0 and dock:
  - page 0: Clock widget 4×2, Agenda 4×2, Favourites 4×1, Music 4×1;
  - dock: phone, messages, browser, camera;
  - pages 1–2 start empty.

### Pin and unpin
- In the Menu, a long-press on an app opens the Options sheet (the existing `OptionsMenu`). It offers:
  - "Add to home" (to the current home page, or the first page with room);
  - "Add to dock" (the first free slot, or replace one);
  - "Remove from home" when the app is already pinned.
- In edit mode, an item's × unpins or removes it.
- Uninstalling an app (later) removes its items.

### Edit mode
- **Enter:** a long-press on an empty spot or an item on home. A long-press is a Slint `Timer` (500 ms) started on
  `pointer-event` down and cancelled by a move beyond the touch slop or by the finger lifting. There is no new input
  type in `neoui-proto`.
- **While editing:**
  - items get an outline and a × button;
  - dragging an item reorders it, and the others reflow live;
  - holding an item at the left or right screen edge for 400 ms moves it to that page, adding a page at the end if
    needed;
  - a "+" button in the toolbar opens a sheet with two tabs: **Widgets** (the catalogue, part 4) and **Apps**.
- **Leave:** "Done" in the toolbar, or Back. The layout is saved to `home.layout`, and empty pages beyond the first
  are dropped.

### Rendering
- `HomeScreen` takes a Rust-fed model `[HomeItem { kind, app, name, col, row, w, h, badge }]` per page, with the
  positions computed by the packer in `neoui-proto::home`. It no longer hard-codes the cards.
- The swipe between pages stays server-driven (S2c). Edit mode can turn that off and use plain Slint movement, since
  it is not performance-critical.
- Check with `perf.rs` that the home swipe still meets the S2 budget before and after.

### Tests
- Host: packing (shortcut rows, 2×2 pairs, 4×n), pin and unpin, dock, move across pages, page limits, encode/decode,
  a corrupt blob falling back to the default, and the default layout itself.
- Snapshot: home with the default layout, a page with shortcuts and a 2×2, edit mode.
- Syborg: long-press Clock in the Menu → "Add to home". Reboot without `SNAPSHOT` and check that the shortcut is still
  on page 0.

## Part 4: widgets

### Templates (`neoui-proto::widget`, drawn in `ui/components/widgets.slint`)
| Template | Content | From today's code |
|---|---|---|
| `Clock` | none; the shell feeds the time and `clock.24h` | `BigClock` + date line on home |
| `Agenda` | up to 3 rows of (time, title, place, tint) | `AgendaCard` |
| `Media` | title, artist, playing, position | `MusicCard` |
| `People` | up to 5 (initials, tint, name) | the favourites card |
| `Text` | icon (a `sys/` or app icon id), title, up to 3 lines | new |
| `Count` | big number, label, icon | new |
| `Surface` | reserved for app-drawn widgets; not built | — |

- Each template draws at every size it allows. For example, `Text` at 2×2 shows the title and 2 lines, and at 4×1
  the title and 1 line.
- Each widget is a `Card` with radius 14 dp (`DESIGN.md` tokens).

### Catalogue
A table beside `APPS` in the server: `(app, name, template, sizes, label)`.
- **Built-in, fed by the shell:**
  - `shell.clock` (Clock 4×2, 2×2);
  - `calendar.agenda` (Agenda 4×2, 2×2);
  - `music.now` (Media 4×1, 4×2);
  - `contacts.favourites` (People 4×1).
- **App widgets:** declared in the same table. The first is `clock.next` ("Next alarm / world clock", Text 2×2, 4×1).

### Protocol
| Opcode | Arguments | Result |
|---|---|---|
| `WIDGET = 12` | `[Des8 name, Des8 encoded content]` | 0; `KErrNotFound` for a name not in the app's catalogue; `KErrArgument` for content that doesn't match the template |

- The server keeps the latest content per `(app, name)` and redraws only the cards that show it. The damage covers
  just those cards.
- The content is saved under `widget.<app>.<name>` (Bytes, through part 1), so widgets show the last content after a
  reboot without the app running.
- Before any content arrives, a widget shows its label greyed out.
- An app sends content when its data changes. Waking an app on a schedule to refresh is a later feature.

### Tests
- Host: the content encode/decode per template, template/size checks.
- Snapshot: each template at each of its sizes.
- Syborg: add `clock.next` to home in edit mode, set an alarm in Clock, and check the widget's text in the serial log
  and on screen.

## Not in this design (later)

- App-drawn (`Surface`) widgets: a small surface chunk per widget, drawn by a running app.
- Notifications that survive a reboot (they are kept in RAM only for now).
- Notification sounds and vibration (they need audio and haptics).
- Lock-screen notifications.
- Waking an app on a schedule to refresh its widget.
- Apps that describe their own settings pages to the Settings app.
- An installed-apps registry. `APPS` and the catalogue stay fixed tables until app installation exists.

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
