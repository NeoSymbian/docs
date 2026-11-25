<!-- SPDX-License-Identifier: Apache-2.0 -->
# The browser app (NEOWEB): UI spec

Part of the [browser docs](../browser.md). Written 2026-11-17: every screen of `NEOWEB.EXE`, the rules its chrome
follows, how it talks to the shell and to the engine. The phases that build the screens, and each screen's status, are
in [ui-screens.md](ui-screens.md); the engine side is the WB stages.

**Status (2026-11-21):** ✅ UI0–UI4 built, and on Servo on the Pixel since WB5; ⬜ UI5 (WB6) and UI6 (WB7). The
counts per screen are in [ui-screens.md](ui-screens.md).

**The design is the canvas.** The Browser page of the design canvas is the source of truth:
https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#page-9cb33ae9a178
- 30 screens, a prototype and 3 spec sheets, all `br2-*`;
- one more board on the Settings page, `set2-app-browser`.

Board names below are the canvas's file names; open the page and find the board by its title. The spec sheets are:
- `br2-spec-chrome` (Chrome & rules);
- `br2-spec-screens` (Screen map);
- `br2-spec-shell` (Shell & engine).

**Every screen is approved (owner, 2026-11-17), including those the canvas tags PROPOSED.** A board's stage tag
(WB4–WB7) now tells only when the engine side of that screen arrives. The UI itself is built in the phases below.

**What this replaces:**
- the mock browser screen inside the neoui shell (`neoui/ui/screens/browser.slint`, wired in `ui/shell.slint`);
- the engine plan's one-line chrome plan ("URL bar, tabs, menu, downloads, certificate errors").

## Decisions

| # | Decision | Board |
|---|---|---|
| B01 | **The header is the address bar:** the security icon + domain (path hidden), ☆ bookmark, and ⟳ reload (✕ stop while loading). No app name | `br2-spec-chrome`, `br2-footer-states` |
| B02 | Header and footer **hide while scrolling down**, show on scroll up | `br2-reading` |
| B03 | **Opened pages is a full-screen grid**; up to 6 pages stay loaded | `br2-tabs` |
| B04 | **Options** (the 4-squares `g-apps` icon) opens a full-width bottom panel of icon tiles: Page (New tab, Find in page, Share, Copy link, Desktop site) and Pages (Bookmarks, History, Downloads, Settings) | `br2-menu` |
| B05 | The full screen set, each with its engine stage | `br2-spec-screens` |
| B06 | **Start page:** search field, Shortcuts (4 × 2, editable), Recently visited | `br2-start` |
| B07 | **The footer has five icons:** ← → Search, Opened pages (with the count), Options. They are actions, not tabs (no pill) | `br2-footer-states` |
| B08 | **The UI comes first, on a stand-in engine.** NEOWEB and all its screens are built now, in parallel with WB2–WB4; Servo replaces the stand-in at WB4 | — |
| B09 | **The default search engine is DuckDuckGo**; it can be changed in Settings | `br2-settings` |
| B10 | **Certificate errors:** a Settings switch allows "Open the site anyway (unsafe)". It is **off by default**, so the error page offers only Back to safety | `br2-cert-error`, `br2-settings` |
| B11 | **Passwords:** the Save password sheet is built now; storing passwords waits for a secure store (WB6 or later). Until then, a sign-in keeps its cookies only | `br2-login-save` |

B01–B07 were the owner's decisions of 2026-11-17 on the canvas; B08–B11 were the owner's answers the same day.

**Defaults taken from `br2-spec-shell`'s open questions** (the owner can change them):
- Bookmarks, history and settings are kept on the phone only, with no sync.
- Downloads go to `C:\Data\Downloads`. That Files shows the folder is unverified.
- 6 pages stay loaded and at most 30 are open. There is also a heap budget of about 512 MiB.
- When the chrome shows, it overlays the page; the page is never resized on hide.
- **Back uses `can_back`.** Protocol 1.8 removed NAV, so the old design's `claim_nav` is gone.
- **The Wi-Fi portal hand-off is protocol 1.9 `OPEN`.** Wi-Fi opens `browser` with the portal URL as its argument, and
  NEOWEB reads it with `ARG` ([kit.md](../neoui-shell/kit.md), protocol 1.9).

## Architecture

**NEOWEB is a normal neoui app**, a separate process like NEOPHONE:
- it draws its own header and footer with the kit (`@neoui/kit.slint`);
- it tells the shell about its page with `PAGE`;
- it gets Back, the area and the keyboard as events ([kit.md](../neoui-shell/kit.md)).

It lives in `NeoSymbian/browser`, laid out like `NeoSymbian/phone`:

| Path | Licence | What |
|---|---|---|
| `app/neoweb-core` | Apache-2.0 | The logic, host-tested: tabs and their caps, history and its grouping by day, bookmarks and folders, the Back order, the chrome's hide-on-scroll state machine, address vs search parsing, settings, and the `Engine` trait with `FakeEngine` |
| `app/neoweb-ui` | GPL-3.0 (Slint) | The screens as Slint, built with `neoui_kit::compile_with`; host snapshots `snapshots/br2-*.png`, one per board |
| `symbian/neoweb` | GPL-3.0 | `NEOWEB.EXE`: the `neoapp` loop, protocol 1.8/1.9, storage in its private folder |
| `crates/neoweb-host` | Apache-2.0 | Today the WB0 Linux embedder. From WB4 it is Servo behind `Engine` |

**Why `app/` is its own workspace:** `crates/` is the Servo cross-build workspace, and its mozjs patch path exists only
inside the build container.

**The `Engine` trait is the seam.** It takes:
- the commands load, reload, stop, back, forward, input (touch, keys, text), resize, find, select and
  zoom/desktop-site;
- a frame request.

It sends back the events below. `FakeEngine` serves bundled pages and covers every event, so all screens work before
Servo does. The event list follows `br2-spec-shell`:

| Engine event | NEOWEB does | Engine stage |
|---|---|---|
| Load status (start, progress, done) | The progress line; ⟳ ↔ ✕; the chrome forced on | WB4 |
| Frame ready | Copy RGBA → XRGB8888 into the surface + DAMAGE | WB4 |
| URL changed | The header's domain and security icon; a history entry | WB5 |
| Title changed | The PAGE title (the Open apps card), the tab card, history | WB5 |
| History changed | ← → on/dim; `can_back` | WB5 |
| New window (`target=_blank`) | A new tab (counts toward 30); the opener is kept for Back | WB5 |
| Dialogs: alert, confirm, beforeunload | Shell `QUERY` | WB5 |
| Dialog: prompt | An app sheet + `KEYBOARD_TEXT` | WB5 |
| Input focus | The KEYBOARD mode from the input type: text, `inputmode=numeric` → NUMBER, `type=tel` → PHONE | WB5 |
| Download | The Downloads page + `NOTIFY` | WB5 |
| Certificate error | A `neo:` error page (proceed only if B10's switch is on) | WB6 |
| Permission request | Deny by default (no location, camera or microphone yet) | WB6 |
| Full-screen request | `PAGE` full | WB7 |
| Crashed | A `neo:` "page crashed" page with Reload | WB4 |

Servo 0.8's exact delegate method names are unverified; `crates/neoweb-host/src/delegate.rs` has the ones WB0 used.

## Chrome and rules

All of this comes from `br2-spec-chrome`; 1 dp = 1 px on the 360 × 720 boards.

**Header, 48 dp (B01).** Its states (`br2-footer-states`):

| State | Left | Right |
|---|---|---|
| Empty | g-search + "Search or type an address" (a tap anywhere edits) | — |
| Secure | g-lock + domain (16/500, path hidden) | ☆, ⟳ |
| Bookmarked | as Secure | ☆ filled in accent |
| Not secure | g-info + "Not secure" + domain (http or mixed content) | ☆, ⟳ |
| Certificate error | as Not secure; the page is a `neo:` error page | ☆, ⟳ |
| Loading | as the page's state, with a 2 dp accent progress line under the header | ☆, ✕ (stop) |
| Edit | A 40 dp field `#1d2025` r20 with the full URL selected, and ✕ to cancel | — |

- A tap on the domain, or on the footer's Search, enters edit mode.
- A tap on the security icon opens Site info.

**Footer, 48 dp (B07).**
- Five equal 72 dp slots, glyphs 24: ← `g-back`, → `g-forward`, Search `g-search`, Opened pages `g-tabs` with the count
  inside, and Options `g-apps`.
- A disabled icon is `#7d838c` at 40 %.
- ← and → move in page history only; they never close a menu or leave the app (the system Back does).
- **The count over 9 shows "9+"** (`br2-footer-states`). `br2-spec-chrome` says 1–99; the board decides.
- Long-press on ← or → shows the history list.

**Geometry per navigation mode:**

| Mode | Status | Header | Page | Footer | Nav | Total |
|---|---:|---:|---:|---:|---:|---:|
| Gestures | 25 | 48 | 583 | 48 | 16 (band) | 720 |
| Buttons | 25 | 48 | 543 | 48 | 56 (keys) | 720 |
| Gestures, chrome hidden | 25 | — | 679 | — | 16 | 720 |
| Buttons, chrome hidden | 25 | — | 639 | — | 56 | 720 |
| Full-screen video | — | — | 720 | — | — | 720 |

- **With the keyboard up**, it covers the footer: the page is 631 − h (Gestures) or 591 − h (Buttons), with h from
  `KEYBOARD` and `AppEvent::Keyboard { h }`. The header stays.
- **A mode switch** arrives as `AppEvent::Area { h }`. The page resizes then, and only then.

**Hide on scroll (B02):**
- **Hide:** after the page scrolls down 24 dp (one gesture, summed since the last change of direction). Header and
  footer slide away together in 150 ms.
- **Show:** after a 24 dp scroll up, or a fling up of any length.
- **Always shown:**
  - near the top (scroll offset under 48 dp);
  - while loading;
  - with the keyboard up or in edit mode;
  - with find, a menu, a sheet or a dialog open;
  - on a page shorter than the view;
  - on error and `neo:` pages;
  - right after ← or →.
- The status bar and the nav belong to the shell and stay.
- **No reflow:** the page keeps one size and the chrome slides over it.
- Scroll input is paced to painted frames. That is the WB0 rule (`browser/wb0/results/2026-11-16/summary.md`): input
  faster than frames piles up WebRender work.

**Back order** (the system Back; `can_back` is true while 1, 3 or 4 applies):

| # | What is open | Back does | Who |
|---|---|---|---|
| 1 | Options panel, a sheet, a dialog | Closes it (a QUERY dialog: answers its last button) | App; QUERY: shell |
| 2 | Keyboard | Hides it; the app gets `Keyboard { h: 0 }` | Shell |
| 3 | Find bar, or edit mode | Closes find / cancels the edit; the old URL comes back | App |
| 4 | Page history | The previous page in this tab | App |
| 5 | Nothing (first page of the tab) | Leaves the app, to where it was opened from (1.9 origin) | Shell |

- A tab opened by a link has no history of its own. Back at its first page closes it and returns to the opener.
- **Buttons mode:** the key row's ← does the same as the footer's ← while the page has history (`br2-page-buttons`).

**Pages, memory and eviction:**
- **Up to 6 pages stay loaded.** A page past that, or one opened once the heap passes its budget (about 512 MiB), is
  unloaded, the least recently used first.
- **An unloaded page keeps** its URL, title, initial letter, thumbnail and history. Script state and form input are
  lost.
- **Opening an unloaded page** reloads it, with the NOTE "Page reloaded to save memory" and the action "Why?"
  (`br2-evicted`).
- **At most 30 pages are open.** At the cap, New tab is dimmed and a NOTE says "30 pages open. Close one first."
- **The shell may quit NEOWEB.** At most 4 apps run (`neoui/symbian/src/host.rs` `MAX_RUNNING`), and Quit gives 3 s
  (`QUIT_GRACE_MS`).
  - On Quit, NEOWEB saves its tab list.
  - Next time it loads only the current tab, with the same NOTE.
- **Measured page sizes:** 37–210 MiB per page in WB0. Six large pages would pass the 1 GiB kill line, hence the
  budget.

## Shell protocol use

From `br2-spec-shell`; the calls are in `neoui-proto/src/ipc.rs`, protocol 1.9.

| Call | Browser use | Limits |
|---|---|---|
| `PAGE` | Every page: title (the Open apps card), `can_back`, full for video | Title ≤ 48 B; resend when anything changes |
| `QUERY` | JS alert and confirm; "Leave this page?"; Clear browsing data; Close all pages | Text ≤ 160 B, 1–3 buttons; destructive = red; Back answers the last button. The first line is the site |
| `NOTE` | "Page reloaded to save memory" · "Page closed" + Undo · "Link copied" · "Added to bookmarks" + Undo · the tab cap | Text ≤ 80 B, action ≤ 32 B, 3 s |
| `NOTIFY` | Downloads: "Downloading …" → "Download complete", with action Open → the Downloads page | Title ≤ 48 B, text ≤ 160 B; the same id replaces; ≤ 16 per app; no progress bar |
| `BADGE` | Not used | — |
| `CLIP_SET` / `CLIP_GET` | Copy link, Copy (selection), Paste in the address bar and in forms, paste-and-go | ≤ 2048 B, shared by all apps; a longer URL is refused with a NOTE, never cut |
| `KEYBOARD` | TEXT for the address bar and inputs, NUMBER, PHONE | Returns h; direct Unicode input, no preedit ([architecture.md](architecture.md)) |
| `OPEN` / `ARG` / `DONE` | Wi-Fi opens the captive portal URL; a download notification opens the Downloads page | Arg ≤ 256 B |

**Events handled:**
- `Back`, while `can_back`;
- `Area { h }`;
- `Keyboard { h }`;
- `Visible(bool)`, which pauses timers and media;
- `Quit`, which saves the tab list;
- `Open { page }`;
- `Notified { id, action }`;
- `Answer`, for QUERY;
- `NoteAction`.

## Storage

| What | Where |
|---|---|
| Cookies, cache, local storage | `C:\private\<NEOWEB SID>\` ([architecture.md](architecture.md)) |
| Bookmarks, history, the tab list (session), settings, shortcuts | The same folder |
| Downloads | `C:\Data\Downloads`; Open hands the file to Files |
| Passwords | Not stored until a secure store exists (B11) |
| `neo:` pages | start, the errors (certificate, network, crashed), served by `load_web_resource` |

## When Servo arrives (marked 2026-11-21)

- ✅ **WB2:** the EXE leaves the ARMv5TE target ([wb2-std.md](wb2-std.md)), with the same code: done in US4 (2026-11-25),
  NEOWEB on `armv8a-neosymbian-eabi` and NEOWEBE on its std twin (until then NEOWEB was ARMv5TE, NEOWEBE ARMv7).
- ✅ **WB4:** `crates/neoweb-host` implements `Engine` over Servo, and `FakeEngine` stays for host tests. Pages are real
  from then on; the screens don't change. As built, Servo runs in its own process, NEOWEBE.EXE
  ([protocol.md](protocol.md)), not behind the `Engine` trait inside NEOWEB.
- 🟡 **WB5–WB7:** each screen's engine column lights up, and the phase gates are re-run against Servo. WB4 is done
  (2026-11-20) and WB5 too (2026-11-21): every WB5 screen above works on Servo.
- **Memory:** a full-screen 1080 × 2160 XRGB surface is 8.9 MiB; the app area in Gestures mode (1080 × 2037) is
  8.4 MiB. `host.rs`'s "~7 MB a surface" predates the 2160-high screen.

## Open items

- ✅ **File upload:** the Files picker hand-off (UI3): `OPEN_FILE` of Files' picker and `RESULT_FILE`, done in WB5a.
- ✅ **Engine hooks:** selection, find in page and downloads, done in WB5c/d with Servo 0.8's API and a page helper
  script; no Servo patch was needed for them. The selection handles are approximate.
- 🟡 **Downloads folder:** downloads land in `C:\Data\Downloads`, but the shade's Open starts Files on its home page:
  Files has no page yet that shows a file another app opens it with.
- ⬜ **Secure store:** a secure store for passwords (B11), shared with Wi-Fi keys later (WB6).
- ⬜ **Session on Quit:** NEOWEB doesn't save its tab list on Quit yet (Pages, memory and eviction, above).
- ⬜ **History list:** long-press on ← or → doesn't show the history list yet.
