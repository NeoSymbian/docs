<!-- SPDX-License-Identifier: Apache-2.0 -->
# The browser app: phases UI0–UI6 and every screen

Part of the [browser docs](../browser.md). The phases UI0–UI6 build every board of the canvas's Browser page; the spec
they follow is [ui.md](ui.md).

**Status (2026-11-21):** 25 of 31 screens built; on Servo on the Pixel: 19 ✅, 5 🟡, 7 ⬜.
- **Built** ✅: rendered by `app/neoweb-ui`'s tests into `snapshots/br2-*.png` (the shell's QUERY and NOTIFY screens
  have no snapshot: they're the shell's).
- **On Servo:** ✅ the screen works with the real engine on the Pixel (WB5's gate runs, 2026-11-21); 🟡 works with a
  gap; ⬜ not yet.

| Phase | Merged | Screens built | On Servo |
|---|---|---|---|
| UI0 the app and its chrome | ✅ [browser#1](https://github.com/NeoSymbian/browser/pull/1) (2026-11-17) | 5/5 | 3 ✅ 2 🟡 |
| UI1 address, loading, reading | ✅ [browser#2](https://github.com/NeoSymbian/browser/pull/2) (2026-11-17) | 3/3 | 2 ✅ 1 ⬜ |
| UI2 opened pages and Options | ✅ in WB5c ([browser#10](https://github.com/NeoSymbian/browser/pull/10)) | 6/6 | 5 ✅ 1 🟡 |
| UI3 forms and dialogs | ✅ in WB5a (browser#10) | 5/5 | 5 ✅ |
| UI4 library and settings | 🟡 in WB5d (browser#10); `set2-app-browser` waits | 6/7 | 4 ✅ 2 🟡 1 ⬜ |
| UI5 safety and errors | ✅ 2026-11-22 (browser `ui5`, servo `ui5`, neoui `ui5-portal`) | 4/4 | 4 ✅ |
| UI6 media | ⬜ with WB7 | 0/1 | ⬜ |

## Phases

Every phase builds **all of its screens for real on `FakeEngine`**. A screen's engine side lights up when the engine
reaches the stage in its last column. Boards are on the canvas Browser page
(https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#page-9cb33ae9a178).

**The gate of every phase:**
- **Host snapshots:** `app/neoweb-ui` renders each of the phase's boards to `snapshots/br2-*.png`, checked side by
  side with the board.
- **Unit tests:** `neoweb-core` covers the phase's logic.
- **On a device:** NEOWEB runs on the phone (a RAM boot) through the phase's flow. Syborg is no longer a target
  (2026-11-21).

### UI0: the app and its chrome

Gate flow: tap the Browser tile, see the start page, tap a shortcut, and get a page in both navigation modes.

| Screen | Board | Build | Engine | Built | On Servo |
|---|---|---|---|---|---|
| Start page | `br2-start` | Empty header; Shortcuts 4 × 2 with Edit; Recently visited; footer with ← → dim and count 1 | WB5 | ✅ | ✅ |
| Start page, Buttons | `br2-start-buttons` | The same above the key row | WB5 | ✅ | 🟡 not run in Buttons mode |
| Page | `br2-page` | Secure header (lock, domain, ☆, ⟳), page area 583, footer | WB4 draws, WB5 chrome | ✅ | ✅ |
| Page, Buttons | `br2-page-buttons` | Page area 543; key ← = footer ← while there is history | WB5 | ✅ | 🟡 not run in Buttons mode |
| Header and footer states | `br2-footer-states` | Every header and footer state in the tables above | WB5 | ✅ | ✅ |

- ✅ **The app:**
  - `NEOWEB.EXE` with a UID in `exes.txt`, an entry in neoui's `APPS` (`symbian/src/host.rs`) and the Apps list;
  - the Home and Apps tiles open it.
- ✅ **neoui:** the mock `BrowserScreen` (`ui/screens/browser.slint` and its `shell.slint` wiring) is removed.
- ✅ **neoweb-core:** the geometry per mode, `PAGE` and `can_back`.
- ✅ **FakeEngine:** bundled pages that draw static content (the boards' Wikipedia, GitHub and forum pages).

### UI1: address, loading, reading

Gate flow: type an address or a search, watch it load, read with the chrome hiding, and use Back through every level.

| Screen | Board | Build | Engine | Built | On Servo |
|---|---|---|---|---|---|
| Address (edit) | `br2-address` | The full URL selected, ✕ cancel, `KEYBOARD_TEXT`; suggestions: history and bookmark rows, then "Search for …" (DuckDuckGo, B09); paste-and-go | WB5 | ✅ | ✅ |
| Loading | `br2-loading` | A 2 dp progress line, ✕ stops, the chrome forced on | WB4 stages, WB5 | ✅ | ✅ |
| Reading | `br2-reading` | The chrome hidden, page 679; a "scroll up to show" hint | WB5 | ✅ | ⬜ the chrome doesn't hide yet (`ChromeScroll` unused) |

- **neoweb-core:**
  - ✅ address vs search parsing: a scheme, a dot or `localhost` makes an address, else a search;
  - 🟡 the hide-on-scroll state machine with its always-shown cases (host-tested; NEOWEB doesn't use it with Servo yet);
  - ✅ the Back order;
  - ⬜ ← and → long-press history.

### UI2: opened pages and Options

Gate flow: open 7 pages and see the 7th evict the oldest; long-press a link; select text and copy it; find a word.

| Screen | Board | Build | Engine | Built | On Servo |
|---|---|---|---|---|---|
| Opened pages | `br2-tabs` | A full-screen grid (footer hidden), the current page outlined, ✕ on each card, New tab; the note "Up to 6 pages stay loaded; older ones reload when you open them." | WB5 | ✅ | ✅ |
| Options panel | `br2-menu` | The bottom tile panel. **Page:** New tab, Find in page, Share, Copy link, Desktop site. **Pages:** Bookmarks, History, Downloads, Settings | WB5 | ✅ | ✅ |
| Link long-press | `br2-link-menu` | A sheet with the link's title and URL: Open in new tab, Copy link, Download link, Share | WB5 | ✅ | ✅ |
| Text selection | `br2-select` | Handles + a bar: Copy (`CLIP_SET`), Select all, Search | WB5 | ✅ | ✅ handles approximate |
| Find in page | `br2-find` | The header becomes the find field with "2/7", ↑ ↓ and ✕; matches highlighted. Back: keyboard → find bar → page | WB5 | ✅ | ✅ |
| Page reloaded | `br2-evicted` | The NOTE "Page reloaded to save memory" · "Why?" | WB5 | ✅ (a NOTE) | 🟡 not checked on the phone |

- 🟡 **neoweb-core:** ✅ the tab list with the 6 loaded / 30 open caps and LRU eviction; ⬜ the heap budget; ⬜ the
  session save on Quit.
- ✅ **Share:** goes to Messages by protocol 1.9 `OPEN` (the link goes on the clipboard: Messages takes no text yet).
- ✅ **Desktop site:** a user agent switch (for every page loaded after it, not per tab).

### UI3: forms and dialogs

Gate flow: sign in on a form with the keyboard up; answer a JS confirm and a prompt; attach a file.

| Screen | Board | Build | Engine | Built | On Servo |
|---|---|---|---|---|---|
| Login form | `br2-form` | The keyboard covers the footer; the page is 679 − 48 − h (355 dp with the 276 dp keyboard); the focused field scrolls into view | WB5, logins WB6 | ✅ | ✅ contenteditable gets no keyboard |
| JS confirm | `br2-js-alert` | Shell `QUERY`: "site: text", OK · Cancel | WB5 | ✅ (shell QUERY) | ✅ |
| JS prompt | `br2-js-prompt` | An app sheet: "site asks: …", a text field, Cancel · OK, `KEYBOARD_TEXT` (QUERY has no text field) | WB5 | ✅ | ✅ |
| File upload | `br2-upload` | A "Choose a file" sheet: Photos · Files · Memory card E:, then Recent files | WB5 | ✅ | ✅ |
| Save password | `br2-login-save` | A sheet with username and masked password; Never · Not now · Save. Save is disabled until a secure store exists (B11) | WB6 | ✅ | ✅ the offer; Save waits for WB6 |

✅ **Done in WB5a:** Files hands NEOWEB the chosen file through its picker (`OPEN_FILE` files page 1, `RESULT_FILE`);
NEOWEB copies it where the engine can read it.

### UI4: library and settings

Gate flow: bookmark a page, find it in Bookmarks and History, download a file and open it from the shade, change the
search engine, and clear data.

| Screen | Board | Build | Engine | Built | On Servo |
|---|---|---|---|---|---|
| Bookmarks | `br2-bookmarks` | Header `[← Bookmarks · search · new folder · ⋮]`; Folders, then bookmarks. Long-press: Edit · Move · Delete; ☆ in the address bar adds one | — (local) | ✅ | ✅ |
| History | `br2-history` | Grouped by day (Today, Yesterday, …), times; a ✕ per row; Clear browsing data at the top; search | WB5 | ✅ | ✅ |
| Downloads | `br2-downloads` | Downloading: progress, time left, pause, cancel. Done: size, time, Open (hands the file to Files) | WB5, files on C: WB6 | ✅ | ✅ |
| Download complete (shade) | `br2-download-done` | `NOTIFY` "Download complete · Browser · name · size", action Open → `Open { page: Downloads }` | WB5 | ✅ (shell NOTIFY) | 🟡 Open lands on Files' home |
| Settings | `br2-settings` | **General:** Search engine (DuckDuckGo), Text size, Desktop site by default. **Content:** JavaScript (interpreter only, no JIT). **Privacy:** Cookies (allow, block third-party), Clear browsing data, the certificate switch (B10). **About:** NEOWEB, Servo 0.8.0 | WB5 | ✅ | 🟡 the JavaScript and cookie switches aren't applied |
| Clear browsing data | `br2-clear-data` | Shell `QUERY`, destructive: "Clear browsing data? History, cookies and cached files on this phone are deleted." Clear · Cancel | WB5 | ✅ (shell QUERY) | ✅ |
| Settings app → Apps → Browser | `set2-app-browser` | Notifications (allow, banners), Storage used (data + cache), Clear data, Open app settings, Stop app | — (Settings app) | ⬜ (needs the Settings Apps list) | ⬜ |

✅ **neoweb-core:** bookmarks with folders, history grouped by day, settings keys, and the download list. ⬜ `set2-app-browser`
is built in the Settings app, which reads NEOWEB's storage size and opens NEOWEB's Settings page with 1.9 `OPEN`.

### UI5: safety and errors

Gate flow: tap the lock for site info; open an expired certificate, a dead address and a captive portal from Wi-Fi.

| Screen | Board | Build | Engine | Built | On Servo |
|---|---|---|---|---|---|
| Site info | `br2-siteinfo` | A sheet from the lock: the connection (TLS version), the certificate (issuer, valid until), cookies and site data with Clear, Site settings | WB6 | ✅ (no Site settings row: no per-site settings yet) | ✅ TLS 1.3, issuer, validity, Clear |
| Certificate error | `br2-cert-error` | A `neo:` page: "This site's identity can't be confirmed", Back to safety, Details (issued to/by, validity, error code). "Open the site anyway (unsafe)" appears only when B10's switch is on | WB6 | ✅ | ✅ expired.badssl.com: no override with the switch off, opens with it on |
| No connection | `br2-offline` | A `neo:` page: "No internet connection", the cause and code, Retry, Check Wi-Fi (opens Settings › Wi-Fi with 1.9 `OPEN`) | WB6 | ✅ | ✅ Retry, Check Wi-Fi; the cause is generic (Servo says only "client error (Connect)") |
| Wi-Fi sign-in | `br2-captive` | Opened by Wi-Fi: a "Sign in to Wi-Fi network …" banner with Dismiss over the portal page; the header shows Not secure | WB6 | ✅ | ✅ from the shade entry (a test host answering instead of the 204) |

✅ **neoui side (owner, 2026-11-21: Settings and the shade):** the internet check tells a login page from no internet
(`Internet::SignIn`). The current network reads "Connected · Sign in needed"; a tap on it, Sign in in its details,
or the shade's "Sign in to Wi-Fi network" entry opens NEOWEB with `OPEN("browser", 5, "<url>\n<network>")`. The
network is checked again every 30 s until the login is done. `OPEN("settings", 0, "wifi")` shows Settings › Wi-Fi
(the offline page's Check Wi-Fi).

**Phone run (2026-11-22, Pixel, build c6c1fe2 + kernel 3bd11c0):** all four screens work. Found and fixed on the
phone: the error pages' buttons went to the page underneath; Servo names a bad certificate only "client error
(Connect)" (the expiry now comes from the certificate's dates); a site opened anyway showed the lock (now Not secure);
the shade named the network by its MAC; Servo 0.8 refused the override request itself (`chrome:allowcert`, so even its
stock page could never override; fixed in the Servo fork).

**How it's built:**
- **Error pages:** the engine serves its own `BadCertHTML` and `NetErrorHTML` (`std/webengine/src/resources.rs`; the
  fork's default reader registers only with its `register` feature). They have no buttons: a console line with a token
  per engine run tells NEOWEB, which draws the page. Servo's own certificate page offered "Allow certificate
  temporarily" whatever Settings said; that broke B10 until UI5.
- **Site info:** the engine's own TLS handshake to the site (a shortcut: not the page's connection) and Servo's cookie
  count; the certificate is read by `neoweb-core::safety`.
- **Protocol 1.5:** `PageError`, `AllowCert`, `SiteInfo`, `ClearSite` ([protocol.md](protocol.md)).
- **Servo fork (branch `neosymbian`):** the default resource reader registers only with its `register` feature, and
  fetch lets the error page's `chrome:allowcert` through (still guarded by Servo's secret).

### UI6: media

| Screen | Board | Build | Engine | Built | On Servo |
|---|---|---|---|---|---|
| Video full screen | `br2-video` | `PAGE` full (720, no status bar, no nav); a tap shows the controls for 3 s: pause, seek, volume, exit full screen | WB7 | ⬜ | ⬜ |

### The prototype

`br2-prototype` is the clickable flow (start → page → tabs → menu). Each phase's gate flow follows it where they
overlap.
