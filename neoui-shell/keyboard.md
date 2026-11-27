<!-- SPDX-License-Identifier: Apache-2.0 -->
# System keyboard and old-app key pads

**Status: languages built 2026-11-12; Keyboard v2 boards (`kb2-*`) and the old-app key pads (`pad-*`) are on the
canvas's Keyboard page.** Moved here from `neoui-shell.md` on 2026-11-21; the hub is [README.md](README.md).
The keyboard's place in each navigation mode (above the key row or the band, swipe down to hide) is in
[navigation.md](navigation.md).

## System keyboard: languages (2026-11-12)

One on-screen keyboard for every screen. The shell draws it, so no app links a copy. It types English (QWERTY),
Armenian (Eastern, phonetic) and Russian (ЙЦУКЕН), and more languages can be added as data. Settings → Language &
keyboard turns languages on and off; there is no launcher entry. It replaces the US-only R6c keyboard and the
Terminal's own Esc/Tab/arrows bar.

### Where it is (`neoui/ui/components/keyboard/`)
| File | What |
|---|---|
| `types.slint` | `struct Layout { code, name, hint, font, cols, rows: [[string]], abc, comma, stop }` |
| `layouts/en.slint`, `hy.slint`, `ru.slint` | One global per language. Its rows are strings, one per key. `⇧` and `⌫` may only start or end a row and share the width the letters leave; a row without them is centred. |
| `layouts/common.slint` | The symbols layer, the digit row, and the terminal row (Esc, Tab, ← ↑ ↓ →) |
| `layouts.slint` | `Layouts`: the list (append only), which are on, the current one, and `next()` for the globe key. Two pure callbacks are answered in Rust (`neoui-render::keyboard::{pick, tallest}`), because Slint has no loops. |
| `glyphs.slint` | `Alphabets`: every letter, upper and lower case, as a string literal (see Fonts) |
| `keyboard.slint` | Draws the current layout: letter rows, one-shot shift, the symbols layer, the bottom row (symbols, globe when 2+ languages are on, comma, space, stop, Enter), and in terminal mode the terminal row on top |

### Protocol (`NeoUi` 1.3, additive)
- **`KEYBOARD [mode]`:** 0 hidden, 1 text, 2 terminal. 1.2's `show = 1` is the text mode. The reply is the height
  covered.
- **`AppEvent::Keyboard { h }`:** sent when that height changes while the keyboard is open. This happens when the
  language changes and the same-height setting is off, or when the settings change. The server reads both heights
  from the renderer every frame (`Host::set_keyboard_heights`).
- **The terminal row's keys** arrive as key codes 27, 9 and 0xF807–0xF80A (Symbian's arrows). `neoapp::dispatch_key`
  maps them to Slint keys for text fields.

### Shell text fields (2026-11-12)
- **`TextField` and `SearchField`** (`ui/components/controls.slint`) hold a real `TextInput` drawn in DejaVu Sans.
  Focusing one sets `KeyboardFocus.open` (`keyboard/focus.slint`), so the shell shows the text keyboard over the
  body.
- **Typed keys go into the field:** `Renderer::dispatch` sends them to the shell window as Slint key events
  (`keyboard::key_text`), not to an app.
- **Hiding:** changing screen or view, or closing the Wi-Fi sheet, hides the keyboard.
- **Used by:** the Wi-Fi network sheet's password field (masked, focused when the sheet opens, the card above the
  keyboard) and the Contacts and Messages search bars.
- **An app's own field:** the app calls `App::keyboard(KEYBOARD_TEXT)` when the field takes focus and
  `KEYBOARD_HIDDEN` when it loses it, as Files' name dialog does.

### Height
- **Same height on (the default):** every language has the row count of the tallest one that is on (Armenian: 4
  letter rows). Shorter ones get the digit row on top.
- **Same height off:** each language has its own height, and apps relayout on `AppEvent::Keyboard`. The Terminal
  keeps its grid and lifts the rows so the cursor stays visible.
- **Geometry is counted from the keyboard's bottom:** row k is centred 27 + 48 k dp above it. So taps
  (`symbian/taps.sh`, `tests/keyboard.rs`) don't depend on the rows above.

### Fonts
Slint's software renderer draws a `Text` in one embedded font, with no per-glyph fallback. At build time it bakes
in only the glyphs that appear in that crate's string literals, and fills missing ones from the build host's fonts.
- **DejaVu Sans** (Latin, Cyrillic and Armenian in one face) draws the Armenian keys, and the typed text in Files
  (the name field and the list).
- **DejaVu Sans Mono** draws the Terminal.
- **`Alphabets {}`** goes in every window that shows typed text, so that its letters are baked in.

### Adding a language
1. Add `layouts/<code>.slint`.
2. Add a line to `all`, `on` and `set-on` in `layouts.slint`. Append only.
3. Add its letters, upper and lower case, to `glyphs.slint`.
4. Add `keyboard.<code>` to `registry!`, a property and `changed` handler in `system-settings.slint`, and a
   `bool_binding!` in `neoui-render/src/settings.rs`.
5. In `tests/keyboard.rs`, add its letters to `layouts_have_every_letter` and a snapshot.

If the language's font is not DejaVu Sans, import it in `shell.slint` and in each app that shows typed text.

### Tests
- **`neoui-render` `tests/keyboard.rs`:** typing in each language, the globe and its stored choice, a language
  turned off, both height modes, the terminal row, and every letter of each alphabet on a key.
- **Snapshots:** `keyboard-{en,hy,ru,term}`, and `settings-keyboard-pixel`.
- **Syborg CI:** types `dir` in the Terminal and `neo` in Files. Then it presses the globe twice and makes a folder
  named дом.

### Not yet
Key repeat, long-press (accents, ё/ъ for Russian), Ctrl, suggestions, Western Armenian, layouts for hardware keys,
and translating the UI itself.


## Canvas: the Keyboard page (29 boards)

**Keyboards (`kb2-*`, Keyboard v2, 2026-11-17):**

| Board | What | Status |
|---|---|---|
| `kb2-en`, `kb2-hy`, `kb2-ru` | English, Armenian, Russian letters | built (languages, 2026-11-12); v2 look on the canvas |
| `kb2-number`, `kb2-phone` | number pad, phone pad (1.5) | built |
| `kb2-term` | the Terminal row (Esc, Tab, arrows; 1.3) | built |
| `kb2-buttons` | English in Buttons mode (above the 56 dp key row) | built (NV9) |
| `sh-form-keyboard` (Shell page) | a form with the keyboard up, Gestures | built |

**Old-app key pads (`pad-*`):** drawn by LEGACY.EXE in C++, not by the shell; the design and its stages live in
[../user-side/legacy.md](../user-side/legacy.md#key-pads-s60-apps-take-keys-not-touch).

| Row | Boards |
|---|---|
| Pads | `pad-navigator`, `pad-gamepad`, `pad-number`, `pad-hidden`, `pad-buttons` |
| States | `pad-state-press`, `pad-state-diagonal`, `pad-state-twofinger`, `pad-state-slide`, `pad-state-firstopen` |
| Console (landscape) | `pad-console`, `pad-console-lefthanded`, `pad-console-twofinger` |
| Settings | `pad-settings`, `pad-settings-default`, `pad-settings-reset`, `pad-settings-entry` |
| Spec | `pad-spec-keys`, `pad-spec-touch`, `pad-spec-memory`, `pad-spec-stages` (its HAPTIC 19 / VIEWPORT 20 proposal predates 1.10: HAPTIC became 25, see [protocol.md](protocol.md)) |
| Prototype | `pad-prototype` (Play) |

`pad-spec-anatomy` is held back (its positions don't match the boards).
