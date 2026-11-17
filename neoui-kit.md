# The neoui kit and the app API (UI v2)

The kit is how every NeoSymbian app looks and behaves the same. It has three parts:
- a shared Slint component library;
- a Rust API for the app's side of the shell protocol;
- a template app to copy.

It implements the design canvas's three approved pages:
- **Design system:** tokens and layout.
- **Shell & system UI:** the UI kit, the shell services, the Shell API.
- **Navigation:** v2, decisions D12–D20.

The canvas is https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ. It was built on 2026-11-17 on branches `ui-v2` (neoui, docs) and `kit` (phone).

## Who draws what

| Part | Drawn by | Where |
|---|---|---|
| Status bar (clock left, network name, signal, Wi-Fi, battery; no title, D16) | shell | `neoui/ui/components/frame.slint` `StatusBar` |
| Header: Header, SubHeader, FormHeader, SearchHeader, SelectionHeader, with ⋮ | **app**, with the kit | `ui/components/header.slint` |
| Content, big actions (Call, Send, Shutter, Answer: D14) | **app** | the app's `.slint` |
| Footer tabs (icon-only, 2–5) | **app**, with the kit | `ui/components/footer.slint` |
| Key row (Buttons: ← ⌂ ▢) or gesture band (Gestures, N9: 16 dp) | shell | `frame.slint` `KeyRow`, `Band` |
| Dialogs (`QUERY`), toasts (`NOTE`), the shade (`NOTIFY`), the keyboard, Open apps, the Apps menu, home | shell | `ui/shell.slint` |

On the Pixel (360 × 720 dp), the app's surface is:
- Buttons: 720 − 25 − 56 = **639 dp**;
- Gestures and N9: 720 − 25 − 16 = **679 dp**;
- a full-screen page: 720.

A mode switch resizes running apps once, with `AppEvent::Area` (rule 16).

## Using the kit from any repo

**Build helper.** Add `neoui-kit` as a build-dependency (a git rev of NeoSymbian/neoui), and compile the UI with it:

```toml
[build-dependencies]
neoui-kit = { git = "https://github.com/NeoSymbian/neoui", rev = "<rev>" }
```

```rust
// build.rs
fn main() {
    neoui_kit::compile("ui/app.slint");
}
```

`neoui_kit::compile` maps `@neoui` to neoui's `ui/` folder, embeds images and glyphs for the software renderer, and turns on SDF text. `neoui_kit::config()` gives the same setup for custom builds.

**One import.** The app's Slint takes everything from one file:

```slint
import "@neoui/fonts/NeoSans-Regular.ttf";
import "@neoui/fonts/NeoSans-Medium.ttf";
import "@neoui/fonts/NeoSans-SemiBold.ttf";
import { Theme, Kit, Scroll, Header, Footer, TabPages, NeoList, ListRow } from "@neoui/kit.slint";
export { Theme, Kit, Scroll }   // Rust sets Theme.dp, reads Scroll, drives Kit (Back)
```

Glyphs are `@image-url("@neoui/icons/sys/<name>.svg")`. There are 84 of them, from `tools/make_icons.py`; the v2 additions are:
- clock, timer, recents, contacts;
- select_all, archive, share, sort, filter;
- chevron_left.

**Fonts.** The UI's font is **NeoSans** (`default-font-family: "NeoSans"`): Inter merged with Noto Sans Armenian at 400, 500 and 600, both OFL, made by `neoui/tools/make_fonts.py`. Slint draws a Text in one font with no fallback, and the design draws Inter with Noto Sans Armenian after it, so one family carries both. Text a user types in a field stays DejaVu Sans (every keyboard language). The three subset faces are smaller than the variable Inter they replace.

**The runtime.** On the device, the app's crate depends on `neoapp`, the app API. `neoapp` lives in the neoui repo at `symbian/neoapp` and is GPL because it links Slint.

## The kit, component by component

The signatures follow the canvas's *Shell API · Kit reference*. The table gives the main properties; the sources hold the full list.

| Component | Main properties and callbacks | Notes |
|---|---|---|
| `Header` | `title`, `dots`/`dot`, `actions: [Act]` (≤ 3 with ⋮), `menu: [string]`, `menu-destructive`, `search` (on), `tap-to-top` (on), `alt`, `has-back`, `selected` + `selection-actions`, `query`, `searching`; `action(i)`, `menu-picked(i)`, `searched(text)`, `top()`, `back()`, `selection-action(i)`, `selection-closed()` | 48 dp, title 19/600. Search and selection are built in; both are Back layers |
| `SubHeader` | a `Header` with `has-back: true` | ← takes the same path as Back |
| `FormHeader` | `title`, `can-save`; `cancel()`, `save()` | [✕ Title ✓]. The app asks (QUERY) before it discards edits (D14) |
| `SearchHeader`, `SelectionHeader` | as Header's modes | also usable alone |
| `Footer` | `tabs: [Tab]` (`icon`, `label`, `badge`: −1 a dot, n a count, `disabled`), `current`; `picked(i)` | 48 dp, the active tab on a 56 × 32 accent pill |
| `TabPages` | `count`, `current`, `swipe-tabs` (on); `tab-changed(i)`; one child per tab | commits past 60 dp. The callback is `tab-changed` because `changed` is a Slint keyword |
| `Menu` | `items`, `destructive`, `at-x`, `at-y`, `right-aligned`; `picked(i)`; `show()`, `close()` | a PopupWindow: under ⋮, or at the finger for a long-press menu. A Back layer |
| `Sheet`, `ChoiceSheet`, `DatePicker`, `TimePicker` | `open`, `title`; `chosen(i)` / `set(...)`, `dismissed()` | full-size overlays the app places **last** in its window. Back layers |
| `NeoList` | the Flickable's `content-*` forwarded; `pull-refresh` (**off**), `refreshing`, `refresh()`; `selection`, `selected`; `to-top()` | see "Defaults" below |
| `ListRow` | as before, plus `selecting`, `checked`, `long-pressed()`, `long-x`/`long-y` | long-press is 500 ms (a Slint Timer) |
| `RowActions` | `actions: [Act]`, `destructive-last`, `revealed`; `action(i)`; the row as its child | swipe left. A full swipe runs the last action |
| `FastScroll` | `letters`; `jump(letter)` | a 24 dp A–Z strip |
| `FormRow`, `Chip`, `TextField.error`, `Button.flat`/`enabled` | Chip: `text`, `on`, `count`, `count-danger`; `toggled(on)` | form rows, chips (picked: a 16 % accent fill and an accent border; a count after the text, red for missed calls), validation, text buttons |
| `Keypad` (1.9) | `voicemail`; `typed(key)`, `held(key)`, `pressed(key)`, `released(key)` | the phone keypad: digits over letters, voicemail on 1, + on 0. Holding a key 500 ms sends `held` (speed dial) instead of `typed`; `pressed`/`released` follow the finger for call tones |
| `Fab` (1.9) | `icon`, `label`; `clicked()` | 56 dp, accent; the app places it 16 dp from the content's bottom right |
| `Bubble`, `Composer` (1.9) | Bubble: `text`, `meta`, `mine`, `failed`; `tapped()`, `long-pressed(x, y)`. Composer: `text`, `placeholder`, `counter`, `enabled`; `send(text)`, `edited(text)`, `focus-field()` | a message (theirs left, mine right, failed with a red border) and the field, Send and counter line under a thread |
| `Toast`, `Spinner`, `ProgressBar`, `EmptyState`, `ErrorState`, `Skeleton`, `PullIndicator` | | the toast's look (the shell draws NOTE with it), states in place of a list |
| `Badge` | `count` (−1 a dot) | footer tabs, launcher icons |
| Header extras | `selecting` (the selection header with 0 ticked), `selection-menu` + `selection-menu-picked(i)` (⋮ in selection), `title-font`, `search-first`; `Act.tint` | `SearchHeader` (field 12 dp in, ✕ beside it) and `SelectionHeader` follow `alt` (#0b0c0e) |
| `ListRow.trailing-room`, `Button.icon`/`has-icon`, `Bubble.held`, `ChoiceSheet.radio-left`, `Menu.bound`, `FormHeader.has-save`/`alt`, `Footer.alt` | | room for a letter strip, pills with a glyph, a held bubble's ring, the phone's pickers, a menu at the finger that opens upwards near the bottom, a form whose action is in its content |

**Defaults (K03).** The kit turns these on, and each has an opt-out:
- `Header.search` and `Header.tap-to-top`;
- `TabPages.swipe-tabs`;
- `NeoList.selection`.

`NeoList.pull-refresh` is the exception: it is **opt-in**. A swipe handler holds every press back for 100 ms (Slint's forward delay). Wrapping every list in one would slow the first frames of every scroll, and neoui-render's smooth-scroll test failed. Lists whose data comes from outside (network, modem, files) turn it on.

**Back through the kit (rule 10).** These are layers:
- a Menu, a Sheet or picker;
- the Header's search;
- selection.

The `Kit` global counts them. With one open, the app's page must keep `can_back` true. On `AppEvent::Back`, `neoapp::kit_back!(ui)` closes the top layer and returns true; otherwise the app does its own Back.

Slint has no destroy hook, so a layer whose component goes away while open isn't counted down. `kit_back!` heals that: when no layer answers, it resets the count.

## The app API (`neoapp`)

| Call | What it does |
|---|---|
| `App::connect()` | Connects the `NeoUi` session, gets the geometry and the surface chunk, and sets Slint's platform. The clipboard is the server's |
| `app.next_event(ticker).await` | Keeps one `NEXT_EVENT` outstanding. While it waits it runs Slint's timers and animations and an optional `Ticker` (Clock's seconds). It dispatches input, resizes for `Area`, draws, then returns the event |
| `app.run(\|e\| ...)` | The whole loop, for an app with nothing else to wait for. Quit ends it |
| `app.redraw()` / `draw()` / `set_scrolled(f)` | Draws what changed; `set_scrolled` lets lists move pixels instead of redrawing |
| `app.page(&Page { title, can_back, full })` | The page: its name (Open apps), whether Back stays inside the app, full screen |
| `app.query(&Query)` / `close_query()` | A shell dialog. `AppEvent::Answer { i }` comes back; Back answers the last button |
| `app.note(text, action)` / `close_note()` | A toast for 3 s. `AppEvent::NoteAction` comes back |
| `app.notify(&Notification)` / `cancel_notify(id)` | An entry in the shade, with up to 2 actions (1.9). A tap brings the app to the front with `AppEvent::Page { page }` and `AppEvent::Notified { id, action: 0 }`; action `i` sends `Notified { id, action: i + 1 }` |
| `app.open(key, page, arg)` / `app.arg()` (1.9) | Open another app on one of its pages with an argument (a number). The target gets `AppEvent::Open { page }` and reads the argument with `arg()`; Back at its root returns to the caller |
| `app.done()` (1.9) | The task the app was opened for is finished (a call ended): the shell shows where the user came from |
| `app.clipboard()` / `set_clipboard(text)` | The shared clipboard (≤ 2048 B), for Copy text and Paste outside a text field |
| `app.wake_us()` | When Slint needs the app's loop again (its next timer; 16 ms while animating). A loop that also waits on something else (MODEMD) sleeps no longer than this and then draws: otherwise switches don't redraw and long-presses never fire |
| `app.badge(id, count)` | A counter on the launcher icon. The counters are summed; 0 removes one |
| `app.entry(id, caption, icon)` / `app.front(bool)` | Launcher entries, and showing the app's surface or its shell screen |
| `app.keyboard(mode)` | The system keyboard. `AppEvent::Keyboard { h }` reports later height changes |
| `app.setting` / `set_setting` / `watch_settings` | The settings store (an app writes only its own namespace) |
| `neoapp::kit_back!(ui)` | Back through the kit's layers |

Saving state on Quit needs no new call. The app writes its own `<namespace>.state` value with `set_setting_raw` (≤ 2048 B) and reads it back at start, as Clock does with its `clock.*` keys.

## Protocol 1.8 (`neoui-proto`)

`VERSION = (1, 8)`. A 1.7 app still connects, since the major version is the same.

| # | Opcode | Arguments → result |
|---|---|---|
| 15 | `PAGE` | `[flags (CAN_BACK 1, FULL 4), 0, 0, 0, 0] + title` → the area's height. A 1.7 page still decodes; its primary action, options and dots are ignored |
| 16 | `QUERY` | unchanged |
| 17 | `NOTE` | `[len, text ≤ 80 B, len, action ≤ 32 B]` → 0. Empty text takes the toast away |
| 18 | `NOTIFY` | `[id u32, page u16] + title ≤ 48 B + text ≤ 160 B` → 0. An empty title removes the entry; ≤ 16 per app |
| 19 | `BADGE` | `[id, count]` → 0 |
| 20 / 21 | `CLIP_SET` / `CLIP_GET` | the clipboard, ≤ 2048 B |

| Kind | Event |
|---|---|
| 17 | `AppEvent::NoteAction` |
| 18 | `AppEvent::Area { h }`: the area's new height after a navigation mode switch |

**Removed.** `TITLE` (11) and `TOOLBAR` (12) now answer `KErrNotSupported`. The 1.7 events Action, Primary, Cancel and Option are gone. Their numbers stay reserved.

**Kept for the legacy bridge.** `NAV` (6) and `AppEvent::Options` (5) stay for LEGACY.EXE, the C++ bridge for old S60 apps, which draws no kit header. This answers the canvas's open question on old apps with its compatibility-header option:
- the shell draws a kit-style header over the bridge: ← while Back is claimed, ⋮ sending Options;
- the server gives the bridge a body 48 dp shorter, and places its surface under the header.

## Navigation v2 (`nav.mode`)

The modes:
- **0 Buttons** (D12, D18): a 56 dp key row with ← ⌂ ▢, and no edge gestures. ← dims on home and becomes ˅ while the keyboard is up. Over a full-screen page, a tap shows the key row for 3 s.
- **1 Gestures, the Thumb map:** the default (D19). A stored 1 from v1 becomes the Thumb map.
  - Either side edge: Back.
  - Up from the bottom: Home; up and held still for 300 ms: Open apps.
  - Along the band (72 dp): the previous or next running app.
  - On home, only the bottom edge is live.
- **2 N9 gestures:**
  - The left edge: Back.
  - The right edge: a drag is Open apps, a quick flick the last app.
  - Up from the bottom: Home, and past half the screen the Apps menu.

`nav.strip` is gone.

**What every mode shares:**
- **Back bubble.** A 36 dp bubble with ← follows the finger in from a Back edge; it turns accent at 72 dp (rule 09).
- **Keyboard.** It sits above the key row or the band at its full height. A swipe down on its top band hides it (D20). For an app's field, the band also has Select all · Copy · Paste, sent as Control (0x11) then the letter; `neoapp` turns that pair into Slint's Ctrl chord.
- **Home.** It has no ⋮ in any mode, and Apps is always in the dock (D10). A long press opens Edit home · Wallpaper.

**Where the code is:**
- `neoui-proto/src/gesture.rs`: `Map` and `Recognizer::tick`.
- `symbian/src/lib.rs`: the live edges, the bubble, the toast, notifications, badges.
- `ui/shell.slint` and `frame.slint`.

## Protocol 1.9: apps open each other

`VERSION = (1, 9)`. Phone, Contacts and Messages are three apps (NeoSymbian/phone `phone-apps.md`) that open each other's pages: a contact's Call opens Phone on its call page with the number.

| # | Opcode | Arguments → result |
|---|---|---|
| 22 | `OPEN` | `[key ≤ 16 B, page u16, arg ≤ 256 B]` → 0. The server starts the app `key` or brings it to the front, keeps `arg`, sends `AppEvent::Open { page }`, and shows it with the caller as where Back returns (the shell's origin). `KErrNotFound` for an unknown key |
| 23 | `ARG` | `[out arg]` → its length; reading takes it |
| 24 | `DONE` | → 0. From the app in front: the shell's Back past it (to the app that opened it, or home) |
| 18 | `NOTIFY` | 1.8's record, then optionally `[n ≤ 2]` and the action labels (≤ 16 B), then optionally the avatar's initials (≤ 8 B) and tint (u32 0xRRGGBB) and a time (≤ 16 B). A newline in the text gives two lines. The shade draws the newest entry expanded (avatar, time, two lines, the first action as the main button) and the others as rows. A 1.8 record still decodes |

| Kind | Event |
|---|---|
| 19 | `AppEvent::Open { page }` |
| 20 | `AppEvent::Notified { id, action }`: 0 the entry, `i + 1` its action `i` |

**The server's side (`symbian/src/host.rs`):**
- `APPS` has `phone` (NEOPHONE), `contacts` (NEOCONT), `messages` (NEOMSG); 1.7's `ALIASES` (one process behind three icons) are gone. Open apps lists one card per app.
- `RESIDENT` is Phone and Messages (an incoming call shows at once; Messages posts the shade's entries). They start one at a time, and only while no other app is still connecting, because `connect` binds the newest app without a session. A resident app that was never shown holds no `MAX_RUNNING` slot.
- `neoapp` asks for the surface on the first frame drawn while the app is on screen, so a hidden resident costs no ~7 MB surface until it is first shown.
- The shade's "new messages" summary row hides while Messages posts its own entries.

**Settings shared by apps.** A registered key's owner can be several apps (`Owner::Apps`): Phone's Settings page and a contact card both write `phone.speed` and the `contacts.*` keys. An unregistered key in an app's own namespace (`contacts.rev`) stays writable by that app alone.

**The kit Menu fix.** An item's tap reports its pick before the popup closes: closing tears the item down, and before the fix no ⋮ item ran (`neoui-gallery`'s test now taps one).

**Back to Settings.** An app opened from the Settings app (its Calls & Messages row) returns there on Back.

**Libraries beside `@neoui`.** `neoui_kit::compile_with("ui/app.slint", &[("phone-shared", dir)])` maps an app repo's own Slint library (`@phone-shared/...`), for parts several apps of one repo share.

## Create an app

1. Copy `neoui/symbian/apps/kit` (NEOKIT.EXE: the kit gallery). It is about 70 lines of Rust and 40 of Slint.
2. Rename the package and the EXE:
   - Cargo.toml;
   - `exes.txt` (a new UID);
   - the server's `APPS` table (`symbian/src/host.rs`);
   - the `Apps` list (`ui/screens/menu.slint`), so it shows in the Apps menu.
3. Replace `ui/app.slint` with the app's screens, built from `@neoui/kit.slint`.
4. In `src/lib.rs`, the loop is `app.run`. Handle Back (`kit_back!` first), Answer and NoteAction, and describe the page whenever `can_back` changes.

The app can live in another repo, as NEOPHONE does (NeoSymbian/phone). It pins neoui's rev for `neoui-kit` and `neoapp`, and the same `e32` and Slint as neoui.

## Status (2026-11-17)

| Stage | What | State |
|---|---|---|
| A1 + extras | the kit, tokens, glyphs, gallery (`snapshots/kit-*.png`) | built |
| A5 / NV1 | protocol 1.8, `nav.mode` 0..=2 | built |
| NV3, NV4, NV7, NV8 | key row, band, 639/679 resize, Back bubble, home long press, the shell services | built |
| NV5, NV6, NV9 | Thumb and N9 maps, keyboard swipe-down | built |
| A2, A3, NV10 | Clock, Files, Dev tools, Terminal, NEOKIT, the shell's screens on the kit; NEOPHONE ported (the p2 redesign is its own session) | built |
| copy/paste | the keyboard's edit bar (apps' fields) | built |
| 1.9 | OPEN / ARG / DONE, notification actions, two residents, Keypad / Fab / Bubble / Composer | built (neoui `apps-split`) |
| NV11, NV12 | this doc, `gestures.md`, the roadmap; Gestures is the default | docs written; install pending |

**Not done yet:**
- A Pixel install and the Syborg CI tap paths for v2: `neoui/.github/workflows/syborg.yml` still taps the v1 strip.
- An editor for home and a wallpaper picker: the long-press menu opens their Settings pages.
- Flipping a long-press menu near the bottom.
- The edit bar for the shell's own fields.
- G2–G6, from v1's plan.
