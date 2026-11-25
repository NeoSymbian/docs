<!-- SPDX-License-Identifier: Apache-2.0 -->
# neoweb-proto: the Browser app ↔ the engine

Part of the [browser docs](../browser.md). **Version 1.5** (2026-11-21, UI5). The source is
[`app/neoweb-proto/src/lib.rs`](https://github.com/NeoSymbian/browser/blob/main/app/neoweb-proto/src/lib.rs); this page
lists it, and the code wins where they differ.

## Two processes

| Process | What | Built for |
|---|---|---|
| `NEOWEB.EXE` (ROM) | The neoui app: the Slint chrome, every screen of [ui-screens.md](ui-screens.md), the library on C: | `armv8a-neosymbian-eabi`, `no_std` (`armv5te-none-eabi` until US4, 2026-11-25) |
| `NEOWEBE.EXE` (C:, `drive=c`) | The engine: Servo 0.8 with SWGL, downloads (ureq + rustls) | `armv7a-symbian-eabi`, `std` |

- **Transport:** NEOWEBE runs the Symbian server `NeoWebEngine`; NEOWEB starts it (`neowebe.exe --serve`) when it
  can't connect. Each message is a tag byte and little-endian fields; strings are a `u32` length and UTF-8; lists a
  `u32` count.

| Function | Number | Use |
|---|---:|---|
| `COMMAND` | 1 | Argument 0: one encoded `Command` |
| `NEXT_EVENT` | 2 | Kept outstanding; argument 0 is a buffer of `EVENT_MAX` (4096) bytes; completes with an `Event`'s length |
| `FRAMES` | 3 | Completes with a handle to the frame chunk |
| `CANCEL` | 4 | Completes the held `NEXT_EVENT` with `KErrCancel`, before NEOWEB drops it |

- **Frames:** an unnamed global chunk holds a `FrameHeader` (magic `NWF1`, width, height, stride, two buffer offsets;
  4096 bytes) and two RGBA8 buffers. `Event::Frame` names the buffer just written; the engine writes into it again
  only after `Command::FrameShown` (WB0's rule: never paint faster than frames are shown). NEOWEB copies the frame
  into an opaque RGB image (WB5b).
- **Tabs:** NEOWEB numbers its tabs; a tab a page opens itself gets an engine id ≥ `0x8000_0000` (`ENGINE_TABS`).
  Load, Url, Title and History are the shown tab's; the other tabs report `TabInfo`.
- **Error pages (1.5):** the engine serves its own certificate and network error pages in place of Servo's; they
  only report to NEOWEB (`PageError`, through a console line with a token per engine run), and NEOWEB draws
  `br2-cert-error` or `br2-offline`. A tab keeps its error until its next load or a Reload.
- **The engine dies:** the held request fails with `KErrServerTerminated`; NEOWEB starts the engine again on the
  next Load, Open, Reload or Activate.

## Commands (NEOWEB → engine)

| Tag | Command | Fields | Since |
|---:|---|---|---|
| 0 | `Load` | url | 1.0 (WB4) |
| 1–4 | `Reload`, `Stop`, `Back`, `Forward` | — | 1.0 |
| 5 | `Resize` | w, h (page px), dpr × 1000 | 1.0 |
| 6 | `Touch` | kind (Down, Move, Up, Cancel), id, x, y | 1.0 |
| 7 | `Scroll` | dx, dy, x, y | 1.0 |
| 8 | `Key` | code (a Unicode scalar; Backspace 8, Enter 13; Ctrl 0x11 before a/c/v), down | 1.0, used from 1.1 |
| 9 | `Text` | text | 1.0 |
| 10 | `FrameShown` | seq | 1.0 |
| 11 | `ImeDismissed` | — (the user hid the page's keyboard) | 1.1 (WB5a) |
| 12 | `Answer` | id, ok, text (a dialog; a prompt's text) | 1.1 |
| 13 | `Choose` | id, cancel, picked ids (a `<select>`) | 1.1 |
| 14 | `Files` | id, paths (an upload; none = cancelled) | 1.1 |
| 15 | `Clipboard` | id, text (answers `ClipboardGet`) | 1.1 |
| 16 | `Open` | tab, url (make or reload the tab's page and show it) | 1.2 (WB5c) |
| 17 | `Activate` | tab | 1.2 |
| 18 | `Close` | tab (closed or evicted) | 1.2 |
| 19 | `Press` | x, y (a long-press; answered by `Pressed`) | 1.2 |
| 20 | `Select` | op (Copy, SelectAll, Clear, DragStart, DragEnd), x, y | 1.2 |
| 21 | `Find` | text, dir (0 from the top, 1 next, −1 previous; empty text stops) | 1.2 |
| 22 | `DesktopSite` | on | 1.2 |
| 23 | `Download` | url (the link menu's Download link) | 1.3 (WB5d) |
| 24 | `DownloadOp` | id, op (Pause, Resume, Cancel) | 1.3 |
| 25 | `Zoom` | percent (Settings' text size) | 1.4 |
| 26 | `ClearData` | — (cookies, every site's storage, the cache) | 1.4 |
| 27 | `AllowCert` | — (open the shown certificate error's site anyway; sent only with B10's switch on) | 1.5 (UI5) |
| 28 | `SiteInfo` | — (the shown page's connection and certificate: answered by `SiteInfo`) | 1.5 |
| 29 | `ClearSite` | — (the shown page's site: its cookies and stored data) | 1.5 |

## Events (engine → NEOWEB)

| Tag | Event | Fields | Since |
|---:|---|---|---|
| 0 | `Load` | Started, HeadParsed, Complete | 1.0 (WB4) |
| 1 | `Frame` | seq, buffer (0/1), width, height, dirty rect | 1.0 |
| 2 | `Url` | url | 1.0 |
| 3 | `Title` | title | 1.0 |
| 4 | `History` | back, forward | 1.0 |
| 5 | `Crashed` | reason ("page crashed" with Reload) | 1.0 |
| 6 | `Keyboard` | mode (neoui `KEYBOARD`: 0 none, 1 text, 3 number, 4 phone) | 1.1 (WB5a) |
| 7 | `Dialog` | id, kind (Alert, Confirm, Prompt, Unload), text, value | 1.1 |
| 8 | `Select` | id, multiple, items (id, label, disabled, selected; group rows have id `u32::MAX`), cut to fit 4096 bytes | 1.1 |
| 9 | `FilePick` | id, multiple, accept (extensions) | 1.1 |
| 10 | `ClipboardSet` | text (the page copied) | 1.1 |
| 11 | `ClipboardGet` | id | 1.1 |
| 12 | `Login` | user (a password form was sent: offer Save password) | 1.1 |
| 13 | `TabInfo` | tab, url, title (a hidden tab changed) | 1.2 (WB5c) |
| 14 | `Created` | tab (engine id), opener (`target=_blank`, `window.open`) | 1.2 |
| 15 | `Pressed` | kind (Nothing, Link, Image, Text), title, url, y | 1.2 |
| 16 | `Selection` | ends (start left/top, end right/top, line height; empty = none) | 1.2 |
| 17 | `Found` | index (1-based, 0 = none), count | 1.2 |
| 18 | `Download` | id, name, url, path, received, total, state (Downloading, Paused, Done, Failed, Cancelled) | 1.3 (WB5d) |
| 19 | `PageError` | kind (Cert, Net), reason, host, issued to, issued by, valid from, valid until (the cert fields empty for Net) | 1.5 (UI5) |
| 20 | `SiteInfo` | host (the site asked about), tls ("TLS 1.3"), issued to, issued by, valid until, cookies, error | 1.5 |

## Open

- Page events and frames carry no tab id, so a fast tab switch or a popup can mix them up for a moment (WB5
  review). A tab id and generation on every message is the planned fix.
- `Select` lists over one event lose rows; long link URLs are cut at about 2 KiB.
