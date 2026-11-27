<!-- SPDX-License-Identifier: Apache-2.0 -->
# Home pages and widgets

Part of [neoui shell](README.md) · Status: active · Updated: 2026-11-27

**Status:** the home layout and its editor were built on 2026-11-27 with Settings' D10 (neoui#61): `neoui-proto::home`
(4 × 6 packing, 1–5 pages, 4 dock slots, a version-1 `home.layout`, a damaged one falls back to the default), and edit
mode (long press → Edit home, or Settings: ×, drag to a cell, a 400 ms edge hold to the page beside, Add with widgets
and apps, dock slots; Done or Back saves once). The Favourites and Media cards show empty states instead of mock data.
Not built yet: "Add to home" from the Apps menu, 2×2 widgets, and Part 4's app widgets (`WIDGET`). Moved here from
`neoui-shell.md` Parts 3 and 4 on 2026-11-21; the hub is [README.md](README.md).

<!-- stages -->
| Stage | What | State | Updated | Next / evidence |
|---|---|---|---|---|
| Part 3 | Home pages, pin and unpin, dock, edit mode | active | 2026-11-27 | layout and editor built (neoui#61, D10); left: Add to home from the menu |
| Part 4 | Widgets: templates, catalogue, `WIDGET` | active | 2026-11-27 | built-in Clock, Agenda, Favourites, Media in a catalogue; app widgets open |
<!-- /stages -->

The home **Media** card goes live with the media session ([top-panel.md](top-panel.md) TP3); the Agenda card with
DTSRV ([../apps/datetime.md](../apps/datetime.md)).

Canvas (Shell & system UI page): `Main` (home, Gestures), `sh-home-buttons`, `sh-home-clock-24h`, `sh-home-clock-12h`;
`nav-home-longpress` (Navigation page) for Edit home · Wallpaper.

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
  - The same layout fits the Pixel, QEMU `virt` and odd CI sizes.
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
- On `virt` (the Syborg CI when this was written): long-press Clock in the Menu → "Add to home". Reboot without `SNAPSHOT` and check that the shortcut is still
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
- On `virt` (the Syborg CI when this was written): add `clock.next` to home in edit mode, set an alarm in Clock, and check the widget's text in the serial log
  and on screen.

