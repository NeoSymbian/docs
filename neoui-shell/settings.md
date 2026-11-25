<!-- SPDX-License-Identifier: Apache-2.0 -->
# Settings: the store and the Settings app

**Status: the store is done 2026-11-09 (neoui `22af6ac`); the Settings app (NEOSET) SE0 is built and merged 2026-11-26 (neoui#38 `b19d597`, e32-rs#16, neohw#17), SE1 in progress.** One store for the shell and every app (`neoui-proto::settings`,
`SETTING_GET`/`SET`/`WATCH`). Moved here from `neoui-shell.md` Part 1 on 2026-11-21; the hub is [../neoui-shell.md](../neoui-shell.md).
The keys the top panel adds (`shell.*`, `notify.*`, `island.*`, `lock.*`) are listed in [top-panel.md](top-panel.md#settings-keys).

**The Settings app:** the screen that shows these keys moves out of the shell into `NEOSET.EXE`
([below](#the-settings-app-neoset), 2026-11-25). The "Shown in" column below names today's shell pages; the
table lists the Part 1 keys only, the registry (`registry.rs`) has 43 today and the canvas's `set2-spec-keys` lists
them all with the 32 the v2 pages add.

## The Settings app (NEOSET)

Written 2026-11-25. This is the implementation plan for the Settings app:
- a real app, `NEOSET.EXE`, inside neoui, replacing the shell's Settings screen;
- every screen of the design canvas's Settings page;
- the platform work it needs;
- the stages SE0–SE7.

Nothing of it is built yet. Today's Settings is a screen inside the UI server; see [The app today]](#the-app-today).

**The design:** the canvas's Settings page, https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#page-009b5da44490
- 48 `set2-*` boards, decisions S01–S07, published 2026-11-17;
- the owner approved every board and every "Proposed" item on 2026-11-25;
- the prototype is the board `set2-prototype`;
- the spec boards are `set2-spec-map` (board → keys), `set2-spec-keys` (the registry and 32 new keys),
  `set2-spec-decisions` and `set2-replacement-map`.

Related boards on other pages are part of this plan too:
- `tp-settings` (Panel & notifications) and `nt-settings` (per-app channels) on the Top panel page;
- `pad-settings*` (Old apps key pads) on the Keyboard page;
- `pat-settings-top` (tap the header to scroll to top) on the Shell page;
- `nav-settings-nav` on the Navigation page.

The canvas is private: the links open for the owner and whoever it is shared with.

**Research:** Codex (gpt-6.2-astra, highest effort, read-only, 2026-11-25) traced every dependency of today's screen
and every missing part with file:line evidence. Its findings are folded into [The platform work]](#the-platform-work)
below.

### Decisions

**From the canvas (owner, 2026-11-17):**
- **S01 Two roots, shared sub-pages:**
  - a List: Connections · Device · Personal · Apps · System, with colour tiles and live values;
  - a Nokia grid: 14 category tiles, 3 columns.
- **S02** The Wi-Fi and Bluetooth rows carry a switch. The switch toggles the radio; the rest of the row opens the
  page.
- **S03** A status chip on every board: As built / Planned + stage / Proposed.
- **S04** The 14 old boards are replaced (`set2-replacement-map`).
- **S05 Nokia sound profiles:**
  - General, Silent, Meeting, Outdoor, Offline (= airplane mode), and Add profile;
  - each has ringtone, ring volume 0–10, vibrate, message tone, keypad tones and touch vibration;
  - the shade and the power menu switch them.
- **S06** Apps is the per-app hub: notifications, storage, Open app settings, default page, Stop.
- **S07** v2 chrome everywhere:
  - header `[Title · ≤3]`, sub-pages `[← Title · ≤3]`;
  - a 16 dp Gestures band, a 56 dp Buttons key row;
  - kit choice sheets, QUERY dialogs and toasts.

**For the implementation (2026-11-25; the owner approved every proposal and asked for these to be decided):**
- **D1 A real app, inside neoui.**
  - `NEOSET.EXE`, UID **0xE0002007**, app key `settings`;
  - device glue in `neoui/symbian/apps/settings` (GPL);
  - Slint screens in `neoui/crates/settings-ui` (GPL, host snapshot tests);
  - pure models in `neoui-proto/src/settings_app/` (Apache).
  - **Why neoui and not a repo of its own:** Settings is welded to the shell. The settings store and registry, the
    shade, the SIM prompt, the battery recorder, the captive portal and the page table all live there. A repo would
    add four pins (neoui, neohw, e32, Slint) and a ROM copy step for no gain. Files moved out because it is large and
    standalone; Settings is the opposite.
- **D2 On demand.** It is not resident and not started at boot. Like any app it shows in Open apps, and the shell
  closes it for room. It keeps the page and scroll position for a resume.
- **D3 The open questions on `set2-spec-decisions`:**
  - **Root:** the List is the default. ⋮ → View as grid stores `settings.root_grid`. The grid puts Reset under About.
  - **Sound keys:** `sound.silent`, `sound.vibrate` and `sound.ring_volume` stay. They are the active profile's
    live values (MODEMD reads them); the profiles live in a `sound.profiles` blob.
  - **Leaving Offline:** Offline remembers the previous profile. Turning airplane mode off, anywhere, restores it.
    Choosing another profile leaves Offline.
  - **Phone:** it moves to Apps → Phone & Contacts. There is no root shortcut.
  - **Stop:** hidden for NEOPHONE, NEOMSG and Settings itself.
  - **Banner time:** 5 s by default (`notify.bannert`); the boards said 4 s in one place and 5 s in another.
  - **Share E::** a QUERY first. It suspends USB debugging while E: is shared, then restores it.
  - **Lock PIN vs SIM PIN:** two separate things. The phone PIN's verifier lives in the UI server's `\private\`,
    never in the store. The SIM PIN stays on the SIM (MODEMD).
  - **Per-app keys:** typed pattern rows in the registry (`notify.<app>.on`, `.banner`, `<app>.default_page`), see
    [C]](#c-per-app-keys-and-who-is-calling).
  - **Network mode:** offered only for the modes the modem confirms. The page shows MODEMD's technology (3G/LTE),
    never a fixed "4G".
- **D4 Honest values only.** A row shows a real reading or is left out until its stage ships:
  - no per-app battery percentages: the arm64 kernel has no thread CPU time, and CPU time isn't energy anyway.
    Battery usage shows the observed discharge instead;
  - no "Visible to nearby devices" before B3;
  - no data usage before C10.

  The boards keep their S03 chips; the product shows what really works.
- **D5 Nothing that works today is lost,** even where a board leaves it out:
  - the media test and record-and-play-back on the Sounds page;
  - the old-app pads' B key and their reset;
  - the 87 cities with summer time.

### The app today

- **Where it is:** a screen inside `SYSSTART.EXE`:
  - `neoui/ui/screens/settings.slint`, 1044 lines and 12 views: root, connectivity, developer, sounds, display,
    navigation, about, oldapps, wifi, datetime, keyboard, battery;
  - hosted at `neoui/ui/shell.slint:419-447`, bound two-way to the `SystemSettings` global
    ([neoui-shell/settings.md](settings.md)).
- **What that costs:**
  - **It never shows in Open apps.** The switcher lists app processes that have been shown (`host.rs:589-621`);
    Settings is not one.
  - **Dead or made-up rows:**
    - Apps shows a fixed "12" and Privacy does nothing;
    - Font size is a fixed "Medium";
    - Mobile network says "4G" and "1.2 GB this month" whatever the SIM does;
    - Bluetooth opens the shared Connectivity view;
    - Time zone, Screen timeout and Date format step to the next value on each tap;
    - the root Sounds row always says "Ringing".
  - **It is welded to the shell:** Wi-Fi, battery, sound, modem and build info reach it as shell properties (below),
    so it can't move or grow without touching the UI server.
- **Entry points:**
  - Home and the Apps menu;
  - home's long-press menu (Edit home → Navigation, Wallpaper → Display: `home.slint:425-435`);
  - the browser's Check Wi-Fi (UI5: `OPEN("settings", 0, "wifi")`, special-cased at `host.rs:1124-1142` and
    `lib.rs:581-588`).
- **CI:** neoui's `virt-taps` reaches Navigation through it (`virt-taps.yml:111-178, 318-359`). The renderer tests
  in `neoui-render/tests/` drive it too.

### Architecture

```
 NEOSET.EXE (on demand)                       SYSSTART.EXE (UI server)
 ┌──────────────────────────────┐   NeoUi     ┌──────────────────────────────────────┐
 │ settings-ui pages (Slint)     │◄──────────►│ store + registry (SETTING_GET/SET/   │
 │ neoapp: page, Back, QUERY,    │  8/9/10    │   WATCH), allowlist for NEOSET's SID │
 │   OPEN, clipboard             │  40/41     │ SETTINGS_INFO / SETTINGS_ACTION      │
 │ workers: Wi-Fi poll, audio    │            │ status bar, shade, power, SIM prompt │
 └───┬──────────┬──────────┬────┘            │ battery recorder, portal, clockwork  │
     │NeoWifi   │NeoModem  │NeoAudio         └──────────────────────────────────────┘
     ▼          ▼          ▼
   WIFID      MODEMD     AUDIOD          (neoapp::hal: battery now; neoapp::build: build lines)
```

**Who owns what:**

| Thing | Owner | NEOSET's part |
|---|---|---|
| Settings store, registry, file | SYSSTART (`neoui-proto/src/settings/*`, `symbian/src/settings.rs`) | reads, watches, writes the allowlisted keys |
| Saved Wi-Fi networks (`C:\private\e0004002\wifi.dat`), joins | WIFID | its own NeoWifi session: `SCAN(false)` reads, `SCAN(true)` rescans (5 s guard kept), `CONNECT`, `LINK`, `LEAVE(0/1)`. WIFID takes several sessions but pushes nothing, so NEOSET polls only while a Wi-Fi page is visible |
| IP, the internet check, captive portal, the shade's sign-in entry | SYSSTART (`symbian/src/wifi.rs:155-225`) | reads them through `SETTINGS_INFO`; "Sign in" is `SETTINGS_ACTION` with the BSSID it shows, so SYSSTART rechecks before opening the browser's portal page |
| Modem, SIM unlock, emergency calls, the ringer replay | MODEMD + SYSSTART (`symbian/src/phone.rs`) | its own NeoModem session (`STATUS`, `NOTIFY`) for operator, SIM state and the real technology |
| Media test, record and play back | today SYSSTART (`symbian/src/sound.rs:58-131`) | moves into a NEOSET worker on NeoAudio and stops when the page closes. Master volume, route and the volume keys stay in SYSSTART |
| Battery now | HAL | `neoapp::hal::battery()` and the `neoui-proto/src/battery.rs` formatters |
| Battery history (24 h, gaps, save state) | SYSSTART (`symbian/src/battery.rs`) | `SETTINGS_INFO` snapshot, refreshed when its revision changes |
| Clock sync source and offset | SYSSTART (`clockwork.rs`, `netclock.rs`) | `SETTINGS_INFO` |
| Build lines | kernel and ROM stamps | `neoapp::build::lines()` |
| Lock PIN verifier (SE6) | SYSSTART `\private\e0002001\` | starts the shell-owned enrol/change dialog; sees only `lock.pin_set` |

**Protocol** ([neoui-shell/protocol.md](protocol.md); numbers reserved by this document):
- **`SETTINGS_INFO = 40`** `[kind, cursor, Des8 out]` returns a bounded, versioned, revisioned snapshot of something
  only the shell knows:
  - kinds: 1 battery history, 2 Wi-Fi IP/portal, 3 clock sync;
  - later: 4 app catalogue (SE1), 5 notification channels (SE5).
- **`SETTINGS_ACTION = 41`** `[kind, Des8 request]` asks the shell to act:
  - kind 1 signs in to the current network;
  - later: profile switch (SE2), reset jobs (SE4), share E: (SE6).
  - The shell checks every request against its own state.
- **Event 27 `SettingsInfo { kind, rev }`** is reserved for when polling a visible page isn't enough. It isn't used
  in SE0.
- **No secret goes over either:** no passwords, PINs or history arrays in events.

**Who may write what.** An app writes only its own namespace today (`settings/access.rs`), and a session is bound to
"the newest app waiting for one" (`host.rs:589-596`). So a launcher key is not an identity. NEOSET needs to write
shell-owned keys, so SE0 adds:
- **`Message::client_sid()` in e32** (`e32/src/server.rs`), from the kernel's message security info. The kernel
  already has it; the Rust side doesn't expose it yet.
- **`Caller::Settings` in `access.rs`,** with an allowlist of user-editable keys. It includes `clock.24h` and the
  `legacy.pad.*` keys; it excludes the internal records (alarms, timers, speed dial, migration markers).
- **The check in `setting_set`:** SYSSTART grants `Caller::Settings` only when the message's SID is 0xE0002007.
  ROM EXEs get all capabilities, so the SID (one per ROM image) is what is checked, not a capability.

**Pages and entry points.**
- Stable page IDs live in `neoui-proto/src/settings_app/page.rs`: root 0, Wi-Fi 1, Mobile 2, Bluetooth 3,
  Connectivity 4, Display 5, Navigation 6, Sounds 7, Battery 8, Date & time 9, Keyboard 10, Developer 11, About 12,
  Apps 13, Old apps 14, Privacy 15; later pages append.
- The shell's `PAGES` table maps view names to them. Home, the menu, home's long-press menu and the browser open Settings with a
  normal `OPEN`. The browser's `OPEN("settings", 0, "wifi")` stays as an alias: NEOSET decodes it, so the browser
  needs no change now.
- **Back** closes the keyboard, sheet or menu first, then pops a page, then returns to whoever opened Settings.
- **New entry points with later stages:**
  - a hold on a shade tile opens its page (TP7);
  - the power menu opens the profile chooser (SE2);
  - the SIM prompt gets a "SIM settings" action (SE5).

**What leaves SYSSTART in SE0:**
- the `SettingsScreen` slot and its title routing (`shell.slint:43,296-305,419-447`);
- `screens/settings.slint`;
- the Settings-only properties and callbacks;
- `requested_settings` and its `OPEN` branch.

What stays: the store and the bindings the shell itself uses (shade, status bar, keyboard, navigation), the power and
SIM overlays, the battery recorder, Wi-Fi status and the portal, the clock.

**Memory and speed.**
- An app surface on bonito is 1080 × 2160 × 4 = 8.9 MiB, allocated on its first visible draw.
- One page subtree is live at a time; sheets are transient; workers stop when their page hides.
- SE0 measures four times on the phone: tap → first frame, spawn → connect, connect → first draw, and warm resume.
  It also records free RAM before, at peak and after close.

### Screen map

Each board, the page that builds it, the keys it reads or adds, and its stage. "SE0" means it ships in the first app.
"↑" means SE0 ships the as-built rows and the stage adds the rest.

| Board(s) | Page | Keys (new in **bold**) | Stage |
|---|---|---|---|
| `set2-root-list`, `set2-root-buttons` | Root, List; Buttons mode | radio.*, display.dark, nav.mode, sound.ring_volume/silent, developer.usb_debugging | SE0 |
| `set2-root-grid` | Root, grid | **settings.root_grid** | SE1 |
| `set2-search` | Search | — | SE1 |
| `set2-wifi`, `-wifi-off`, `-wifi-join`, `-wifi-details` | Wi-Fi | radio.wifi | SE0 |
| `set2-wifi-saved`, `-wifi-hidden` | Saved networks, Add hidden network | — (WIFID) | SE1 |
| `set2-airplane` | Connectivity | radio.* | SE0 |
| `set2-mobile` | Mobile network | radio.data; **data.network_mode**, **data.roaming**, **data.apn** | SE0 (real status) ↑ SE6 (C10) |
| `set2-sim-lock` | SIM card lock | — (MODEMD) | SE5 |
| `set2-bluetooth`, `-bt-pair`, `-bt-device` | Bluetooth | radio.bt; **bt.visible**, **bt.name** | SE0 (switch, "No driver yet") ↑ SE6 (B3, B6–B8) |
| `set2-display`, `-timeout` | Display, Screen timeout sheet | display.* | SE0 |
| `set2-fontsize` | Font size | **display.font_size** | SE3 |
| `set2-wallpaper` | Wallpaper | **display.wallpaper** | SE3 |
| `set2-navigation`, `nav-settings-nav` | Home & navigation | nav.mode; **nav.swipe_close**, **nav.switcher_cols**, **home.style** | SE0 ↑ SE5 (G3/G4/G5) |
| `set2-sounds`, `-profile`, `-ringtone` | Sounds & profiles | sound.*; **sound.profile**, **sound.profiles**, **sound.ringtone**, **sound.message_tone**, **sound.keypad_tones**, **keyboard.vibrate** | SE0 (today's controls + media test) ↑ SE2 |
| `set2-notifications`, `-notify-app`, `tp-settings`, `nt-settings` | Notifications, per app, Panel & notifications | **notify.<app>.on/.banner**, **notify.dnd**, **lock.notify**, top-panel keys | SE4 (masters) ↑ SE5 (with TP1–TP7) |
| `set2-battery` | Battery | **battery.saver**, **battery.show_percent** | SE0 (chart) ↑ SE3 |
| `set2-battery-usage` | Battery usage (observed discharge, D4) | — | SE3 |
| `set2-storage`, `-storage-drive` | Storage, a drive | **usb.share** | SE3 (totals, scan) ↑ SE6 (FS6) |
| `set2-lock`, `-lock-pin` | Lock screen & security, PIN | **lock.style**, **lock.double_tap**, **lock.pin_set** | SE6 (TP8, TP9) |
| `set2-datetime`, `-timezone`, `-dateformat` | Date & time, city sheet, format sheet | time.*, clock.24h, status.seconds, shade.date | SE0 |
| `set2-language` | Language & keyboard | keyboard.*; **ui.language** | SE0 ↑ SE5 |
| `set2-privacy` | Privacy | **privacy.clip_notice**, **privacy.diagnostics** | SE0 (Clear clipboard) ↑ SE4 |
| `set2-apps`, `-app-browser` | Apps, an app | **<app>.default_page** | SE0 (list → app settings, Old apps) ↑ SE1, SE4 |
| `pad-settings*` | Apps → Old apps | legacy.* (as built) | SE0 |
| `set2-developer` | Developer options | developer.usb_debugging; **developer.show_touches** | SE0 ↑ SE3 |
| `set2-about` | About phone | — | SE0 ↑ SE1 (Licences), SE6 (updates) |
| `set2-reset`, `-reset-query` | Reset | — | SE4 (network, settings) ↑ SE7 (Erase C:) |

### The platform work

Topics A–Q follow the research. **S**, **M** and **L** are the size: a bounded UI or model change; work across a
process or a shared component; or coordinated services, hardware or recovery work.

#### A. Out of the shell (L, SE0)
- Every input of today's screen gets a new source; see the [Architecture]](#architecture) table.
- The Wi-Fi presentation code moves from `symbian/src/wifi.rs` to `neoui-proto/src/wifi.rs`: signal words, security,
  failure reasons. The shade and Settings then say the same thing. Raw SSID bytes are kept apart from their display
  text.
- **The SE0 phone gate:**
  - open Settings from Home, see its card in Open apps in all three navigation modes, come back to the same page and
    scroll, close it and see the card go;
  - browser → Check Wi-Fi → portal → Back;
  - home long-press → Wallpaper opens Display;
  - four apps already running;
  - an incoming call while Settings is open;
  - two apps launched at once;
  - a non-Settings app's write to `display.dark` is refused.

**Known shell risks SE0 leaves open** (they predate NEOSET and hit every app, but an on-demand Settings app hits them
more often; Codex review of neoui#38, 2026-11-26). The SE0 phone run checks the first two: open Settings right after
boot, and close and reopen it fast.
- **The connect race:** a session binds to "the newest launched app without one" (`host.rs` `connect`). If NEOSET starts
  while a resident app is still connecting, the two can swap surfaces and input. NEOSET's writes then fail safe (the
  SID check refuses them). The fix is binding by SID at `connect`: Step 0's second half (`neoui-shell.md`).
- **The reap race:** `reap()` can report the old process's key while a fresh NEOSET is live, so a close-then-reopen
  can jump to Home.
- **A failed spawn** leaves a blank screen, and the `OPEN` caller still gets success.
- **Two queued `OPEN`s** of one app share its argument slot: the second can land on the root page.

#### B. Sound profiles (M, SE2)
- **One reducer in SYSSTART** serves Settings, the shade's Silent tile and the power menu.
- **The keys:**
  - `sound.profile` is a stable id: 0 General, 1 Silent, 2 Meeting, 3 Outdoor, 4 Offline, then added profiles;
  - `sound.profiles` is a versioned blob of at most 1024 bytes. It holds a header, the previous audible profile and
    length-prefixed records (id, name, two tone ids, volume, flags), and stores only overrides of the built-ins.
- **One store transaction:** the profile, the blob, the live mirrors (`sound.silent/vibrate/ring_volume/ringtone/
  message_tone/keypad_tones`, `keyboard.vibrate`) and the radio intent commit together, before any watch fires or
  MODEMD is told.
- **Silent and Offline:**
  - Silent on remembers the last audible profile, and off restores it;
  - Offline remembers the radios. Wi-Fi and BT may be turned back on inside it. Leaving it restores what the user had.
- **Upgrade:** today's silent/volume settings become General without an audible change.
- **Previews** play at the profile's volume and stop on Back, a call, or leaving the app.
- **Custom tones:** a WAV is picked through Files (file handle) and converted. MODEMD's ring policy and NeoAudio then
  choose separate call and message tones.

#### C. Per-app keys and who is calling (M, SE0 + SE1)
- **SE0:** `Message::client_sid()` and `Caller::Settings` with its allowlist (see [Architecture]](#architecture)).
- **SE1:** the registry resolves typed patterns after exact rows: `notify.<id>.on/.banner` (Bool, default true) and
  `<id>.default_page` (Int 0–7). The same resolver runs for GET, SET, file load and reset.
- **SE4:** `NOTIFY` and `BADGE` return `KErrPermissionDenied` for an app whose notifications are off, and existing
  cards go. This needs the caller check too: [neoui-shell.md](../neoui-shell.md) Part 0.

#### D. Device lock and SIM PIN (L lock, M SIM; SE5/SE6)
- **The lock is TP8** (swipe), **then TP9** (PIN) of [neoui-shell/top-panel.md](top-panel.md).
- **The keys:**
  - `lock.style` (0 none, 1 swipe, 2 PIN);
  - `lock.double_tap` (stays false until the touch driver can wake);
  - `lock.notify` (0 off, 1 counts, 2 content);
  - `lock.pin_set`, which only SYSSTART sets.
- **The PIN dialog is SYSSTART's own,** above apps, the switcher and the shade. It asks for the old PIN, then the new
  one twice. It stores a salted, versioned verifier from a reviewed password KDF tuned on the Pixel, plus the attempt
  count and back-off, in `\private\e0002001\`. The PIN never enters the store, the logs, the clipboard or IPC.
  Emergency calls stay possible.
- **SIM:** modem-ipc 2.6 has `VERIFY_PIN` only. SE5 adds:
  - `SET_PIN_PROTECTION` and `CHANGE_PIN`, with the protection state and attempts left in `STATUS`, answered to the
    session that asked;
  - PINs zeroed and never logged, and no retry after a timeout or a modem restart.

#### E. Time zone (S, SE0; M, SE1)
- **The data already exists:** `neoui-proto/src/clock/world.rs` has 87 cities with POSIX rules, and `clock/tz.rs`
  evaluates summer time without std.
- **SE0:** a searchable city sheet replaces the stepper.
  - The clock recomputes as soon as the city or Automatic time zone changes.
  - Automatic time zone keeps working with Automatic time off; `netclock.rs:27-50` returns early today, which is a
    bug.
- **SE1:** zone data is generated at build time from a pinned IANA release. The release and the year range are
  recorded, and saved city names stay valid. Vancouver and Havana have already changed since the table was written.

#### F. Font size (M, SE3)
- **The key:** `display.font_size` 0–3 scales Theme's text tokens by 0.875 / 1 / 1.125 / 1.25.
- **One neoapp helper** sets it at start, on change and on resume. Each app's Theme gets a small adapter, and
  SYSSTART mirrors it.
- **What stays fixed:** the status bar, key faces, hit targets and the dp unit.
- **Every kit app** is audited for literal font sizes.
- Dark theme stays a read-out until there is a light palette.

#### G. Wallpaper (S colours, M pictures; SE3)
- **The key:** `display.wallpaper` is a palette name or a private asset token. Today's home look stays the default.
- **Pictures:**
  - NEOSET picks a JPEG or PNG through Files' picker (file handle), decodes it on a worker, then crops and scales it
    to the screen (a 540 × 1080 RGB cache is about 1.7 MiB);
  - SYSSTART checks the raster, installs it in its `\private\` and redraws home. The old wallpaper stays until the
    new one is in place.
- **From Photos** comes when Photos offers the same picker.

#### H. Storage and USB (M, SE3; L, SE6)
- **SE3:**
  - drive totals at once (e32 `drives`/`volume`); a cancellable worker scan of C: and E: by kind;
  - app data by owner through the app catalogue. It never deletes or sizes `\private\<uid>` blindly: the contacts
    book lives under Phone's UID and the SMS in MODEMD;
  - "Open in Files" goes to a drive page.
- **SE6, Share E: = FS6** ([filesystem.md](../filesystem.md)):
  - one SYSSTART operation that QUERYs first, suspends USB debugging, refuses a busy E:, flushes and dismounts, and
    exports E: only;
  - after the host ejects, it remounts and restores debugging;
  - `usb.share` is the request; the page shows the acknowledged state. Nothing is exported on boot.

#### I. Battery (S, SE0; M, SE3)
- **SE0** ports the real chart: 24 h of minute samples with gaps, from SYSSTART's recorder.
- **SE3:**
  - `battery.saver` caps the effective brightness without changing the slider;
  - `battery.show_percent`;
  - Battery usage shows observed start/end, time on battery and gaps ("since full charge" only once a full charge was
    seen), and screen-on time if measured. There are no per-app shares (D4).

#### J. Search (M, SE1)
- **One source:** each row has metadata shared with its page: a stable id, the page, the label, aliases, an
  availability check and a value formatter.
- **Generated at build time:** a generator emits the page row tables and the search index from it. The build fails on
  a duplicate id or a dead destination.
- **Dynamic entries:** installed apps, profiles and channels.
- **A result** opens the page, scrolls to the row and keeps the query for Back. Credentials never enter the index.

#### K. Apps hub (S, SE0; M, SE1/SE4)
- **SE0:** a list of the apps with their own settings: Phone & Contacts (Phone's page 3) and Old apps (the pads).
  Each opens with `OPEN`.
- **SE1:** the app catalogue through `SETTINGS_INFO` kind 4. It merges ROM apps (`host::APPS`), the legacy guests
  (when LEGACY has started) and later the store's installs. It offers Open app settings for apps that publish a page,
  and `default_page`, which applies to a plain launch only.
- **SE4:**
  - **Stop:** quit, a grace period, then a kill. Hidden for residents and Settings itself.
  - **Clear data:** a QUERY that names what goes. It is done by the owner of the data, never as a recursive delete of
    a private folder.

#### L. Mobile network (S, SE0; L, SE6)
- **SE0:** the operator, SIM state, home or roaming, and 2G/3G/LTE from MODEMD, shown only while registered. Otherwise
  "No service" or "Recovering". `radio.data` reads as a preference until there is a data bearer.
- **SE6, with C10** ([hardware/modem.md](../hardware/modem.md)):
  - network mode, only after the modem reports its capabilities and the change reads back;
  - `data.roaming` enforced before a bearer starts;
  - `data.apn` applied by MODEMD;
  - data usage counted at the interface.

#### M. Bluetooth (S, SE0; L, SE6)
- **SE0:** the `radio.bt` switch on its own page with "No driver yet".
- **SE6 with B3** ([hardware/bluetooth.md](../hardware/bluetooth.md)): BTSRV owns the radio, bonds and scans; NEOSET
  shows snapshots and asks for actions.
  - SYSSTART can show an incoming pairing request when Settings is closed.
  - Audio, Calls and Input wait for B6, B7 and B8.

#### N. Reset (M, SE4; L, SE7)
- **Each reset is a typed SYSSTART job** behind a shell QUERY, then a restart once its owners have saved.
- **Reset network settings:** WIFID empties `wifi.dat` (a valid empty file, so an old migration source can't bring
  the keys back), plus BT bonds and the APN through their owners.
- **Reset settings:** registry defaults for the preference keys only. Alarms, timers, speed dial, contacts, messages
  and files stay. The PIN has its own flow.
- **Erase C: (SE7):** a recovery-only formatter for the C: window. It runs after the phone PIN is confirmed (if
  set), keeps E:, the ROM and the slots, and survives a power cut.

#### O. Display language (L, SE5)
- **The key:** `ui.language` (≤ 8, default `en`), independent of the keyboard.
- **Translations:** Slint 1.18's bundled translations (`@tr`, `.po` catalogues compiled in, no gettext on the
  device), in the shell, the kit and each app. Rust-made strings (dates, statuses) are translated too.
- **The choice** offers a language only when its catalogue and glyphs are complete.

#### P. Panel, notifications, old apps (S, SE0; L, SE4/SE5)
- **Panel & notifications** (`tp-settings`) sits at Device → Notifications in both roots. Apps → an app →
  Notifications opens the same per-app page (`nt-settings`).
- **The rows follow their stages:** each row appears as its TP stage of
  [neoui-shell/top-panel.md](top-panel.md) ships (tiles TP7, channels and DND TP4, the island TP6). DND
  must also hold MODEMD's SMS tone, not only the banner.
- **Old apps' pads** are ported whole in SE0, under Apps: vibration, strength, default pad, directions, A, **B**,
  handedness, console, and Reset (behind a QUERY).

#### Q. Speed and memory (S, SE0)
See [Architecture]](#architecture). If a cold start is slow, the fix is the app's first frame (fewer live pages,
deferred models), not making Settings resident.

### Stages

Each stage ends with a gate:
- **host:** neoui's checks plus the `settings-ui` snapshots against the boards;
- **build:** `neo fetch && neo rom`, `neo kernel bonito` on atlas;
- **CI:** `virt-taps` green;
- **phone:** a RAM boot on the Pixel.

| Stage | Work | Repos | Gate |
|---|---|---|---|
| **SE0** the app | NEOSET 0xE0002007 in neoui (`symbian/apps/settings`, `crates/settings-ui`, `neoui-proto/src/settings_app`); e32 `Message::client_sid()` + `Caller::Settings`; `SETTINGS_INFO`/`SETTINGS_ACTION` (battery history, Wi-Fi IP/portal, clock sync, sign-in); page IDs, `PAGES`, the browser alias; the shell screen removed. Pages in v2 chrome: root List, Wi-Fi (every state and sheet), Connectivity, Mobile (real status), Bluetooth (switch), Display (choice sheets), Home & navigation, Sounds (today's controls, media test, record and play back), Battery (chart), Date & time (city sheet, format sheet), Language & keyboard, Developer, About, Apps (→ Phone settings, Old apps pads), Privacy (Clear clipboard). Repin e32 in phone and files | neoui, e32-rs, phone, files, docs | the A gate above; parity with today's controls |
| **SE1** find and catalogue | Grid root; generated search; pattern keys; app catalogue + default page; Saved networks, hidden network (WIFID: list, forget, directed scan, join by raw SSID); About → Licences; IANA zone data; Dev tools links | neoui, neohw | search finds "time" and a live value; a hidden network joins |
| **SE2** profiles | Profiles end to end, shade and power menu, Offline, ringtone and message tone, WAV import | neoui, neohw | real call and SMS tones per profile; Offline through a reboot |
| **SE3** appearance and device data | Font size, wallpaper, storage, battery saver, show %, battery usage, Show touches, keyboard vibration | neoui, files (picker) | sizes switched with Phone and Files open; a bad picture leaves the old wallpaper |
| **SE4** management | Stop, Clear data, Reset network / settings, notification masters, clipboard-read toast, capabilities view | neoui, neohw, phone | a reset keeps contacts, SMS and files; a disabled app's NOTIFY is refused |
| **SE5** language, SIM, panel | Display language; SIM PIN lock and change; Panel & notifications as TP1–TP7 land; G3/G4/G5 rows | neoui, neohw, apps | Armenian UI through a reboot; SIM PIN on a spare SIM |
| **SE6** hardware pages and lock | Lock (TP8, TP9 PIN); Bluetooth B3/B6–B8; C10 mobile data; FS6 Share E:; Check for updates | neoui, neohw, kernel, build | each owner's own device gate |
| **SE7** erase | Erase C: through recovery | kernel, build, neoui | on a disposable C: image first |

#### SE1 plan (proposed 2026-11-26, for review)

SE1 is split into four parts. Each ships on its own and gets its own phone run.

| Part | Scope (boards) | Touches | Real data / placeholders | Gates |
|---|---|---|---|---|
| **SE1a Find** | Root grid (`set2-root-grid`): 3 x 14 tiles, ⋮ → View as grid / View as list, stored in `settings.root_grid` (the app's own namespace, no registry row); the grid has no Reset tile until SE4. Search (`set2-search`): the root header's 🔍 searches every row's title, its page's title and the row's live value; a result opens its page. About → Licences (the `set2-about` row): Apache-2.0 (NeoSymbian), EPL-1.0/2.0 (Symbian, changed files), GPL-3.0 (Slint and the code linking it). Developer → Kernel log / Save logs open Dev tools on its own pages (it already opens "settings", "tools", "about" by name) | neoui only: `neoui-proto/src/settings_app/rows.rs` (the row table: id, page, title, aliases), `crates/settings-ui` (grid, search results, licences), `symbian/apps/settings`, devtools (`AppEvent::Open` by page) | all real; the search index is the row table. A host test fails when a table title is missing from the `.slint` pages, so the two can't drift | host snapshots `set2-root-grid`, `set2-search`, `set2-licences`; tests: every row found by its title, the grid's tiles open their pages; virt-taps: 🔍 "time" → Date & time; phone: grid ↔ list survives a restart, search and open |
| **SE1b Zones** | Time zone data generated at build time from a pinned IANA release (2025b) for the 87 cities: rules, the release and the years covered recorded; saved city names keep working | neoui-proto `clock/` (a generated table + its generator in `tools/`) | real | host: every city's transitions for 2026–2030 against the IANA reference; the ROM grows by under 8 KB; phone: a city on each hemisphere |
| **SE1c Wi-Fi lists** | Saved networks (`set2-wifi-saved`: list, Forget by name), Add hidden network (`set2-wifi-hidden`) | neohw NeoWifi 1.1 (`SAVED`, `FORGET`, `CONNECT` with no BSSID = by name), WIFID; maybe the kernel (a directed probe scan) | real; Add hidden ships only if the directed scan works | neohw host tests; phone: forget a saved network, join a hidden test network |
| **SE1d Apps catalogue** | The Apps hub lists every app (ROM apps and the old apps LEGACY lists) with Open and, where an app has its own settings page, Open app settings | `SETTINGS_INFO` kind 4 (the shell's apps and launcher entries), settings-ui, NEOSET | real. Default page and per-app notifications wait for SE4, where the shell enforces them (D4: no switch that does nothing) | host: the catalogue's encoding; phone: an old app listed and opened |

**SE1a as built** (neoui#39): search matches a row's title, other names, page and live value; a result opens its page
with the row **selected**, not scrolled to (a deviation from J, approved 2026-11-26: every page is about one screen tall,
so the selected row is in view; scroll-to-row becomes required once a page grows past one screen). A row that
leads to another page (Old apps, Licences, the root's rows) opens that page with nothing selected. Back follows the
pages the user went through (grid → Connectivity → Bluetooth → Back → Connectivity). The row table
covers model-drawn rows too (navigation modes, keyboards), and the drift test compares (page, title) pairs.

**SE1b as built** (neoui#40): the rules are generated **by hand and checked in**, not at build time (a deviation,
accepted by the coordinator 2026-11-26: nothing in the build needs zic). `tools/tzdata` vendors IANA 2025b;
`tools/gen_zones.py` compiles it with `zic -b fat` and writes `clock/zones.rs` (`TZDATA`, `YEARS_CHECKED` 2026–2030,
each city's POSIX footer) and `clock/zones_ref.rs` (zic's transitions, for tests). neoui's `ci` runs
`gen_zones.py --check`, so the table can't drift from the vendored data. Same 87 names in the same order. The only
rule that changed is Dublin's, now IANA's negative-DST `IST-1GMT0,...`: summer time and the west-to-east order use
the zone's winter offset (`tz::Rule::is_summer`/`winter`), not the rule's "standard". The table is 3.4 KB. To update:
replace `tools/tzdata` with a new release, run `tools/gen_zones.py`, and check the test diff.

**SE1c spike (2026-11-26): can the firmware send a directed probe?** Yes. WMI `START_SCAN` (0x3001) takes an SSID
array (TLV 19, `{len u32, ssid[32]}` each, `num_ssids` in the fixed part), as ath10k uses for directed probes. Our
`ScanStart` (kernel `baseport/arm64/sdm670_assp/qcom_wcn3990.cpp:1114`) already builds the TLV, with the wildcard
only, and every scan is passive (`:2141`; [wifi.md](../hardware/wifi.md) W3c: active scans missed 2.4 GHz here).
A hidden network therefore needs the **kernel**:
1. a HAL WlanScan (0x4e1e) request carrying an SSID, which runs `ScanStart(active, ssid)`; on 2.4 GHz it may miss
   like the active scans did (a phone test decides; fallback: 2.4 GHz with longer dwell and more probes);
2. a join that knows the SSID. The Association Request copies the scan entry's SSID (`:1720`, `:1813`), which is
   empty for a hidden AP (`:609` logs "(hidden)"). Either the directed probe response fills it in (`:588` takes the
   first SSID IE when none is stored), or WlanLink op 1 takes `{bssid, ssid, rsn}`.

Then NeoWifi 1.1 gets a directed scan and join by raw SSID, and WIFID keeps `hidden` per saved network. So SE1c splits:
- **SE1c-1** (Saved networks, Forget): user side only (WIFID already keeps `C:\private\e0004002\wifi.dat`). Go.
- **SE1c-2** (Add hidden network): waits for the owner on (a) a kernel change to WlanScan/WlanLink, and (b) whether
  5 GHz-only hidden networks are acceptable if 2.4 GHz directed scans miss.

**Proposed order:** SE1a, then SE1b; SE1c after a research spike (does the firmware take a directed scan?); SE1d.

**Questions for the owner:** none for SE1a or SE1b. SE1c-2: (a) and (b) above.

**Order:** SE0 comes first and alone, because it fixes Open apps and the dead rows. SE1–SE4 can follow in any order.
SE5 and SE6 follow their platform stages.

### Status (2026-11-26)

| Part | State |
|---|---|
| The design (48 boards, prototype, spec) | done, on the canvas, approved |
| This plan | written 2026-11-25 |
| SE0 | built and merged 2026-11-26: neoui#38 (`b19d597`), e32-rs#16 (`Message::client_sid`), neohw#17 (e32 pin). QEMU walk and three Pixel RAM-boot runs: Open apps card, Wi-Fi list and join (keyboard, wrong password, no double join), Buttons/Gestures by NEOSET's SID, the connect and reap races, keyboard resume. Two Codex reviews, findings fixed |
| SE1 | SE1a (find) merged 2026-11-26: neoui#39 (`5055cdb`); two Codex reviews; Pixel RAM-boot run: grid, search → selected row, Back along the path, Kernel log → Dev tools Console. SE1b (zones) next; SE1c spike; SE1d after its plan additions |
| SE2–SE7 | not started |

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
| `display.brightness` | Int 0–255 | 160 | Shade slider, Settings → Display; sent to the panel (display HAL, scaled to 0–1023) |
| `display.timeout` | Int 0–600 (s) | 60 | Settings → Display → Screen timeout (15 s … 10 min, Never = 0); off after that long without a touch or key |
| `clock.24h` | Bool | true | Settings → Display; the status bar clock and the Clock app follow it |
| `keyboard.en`, `keyboard.hy`, `keyboard.ru` | Bool | true, true, true | Settings → Language & keyboard: the system keyboard's languages |
| `keyboard.layout` | Int 0–15 | 0 | The current language (an index into `layouts.slint`); the globe key and Settings change it |
| `keyboard.same_height` | Bool | true | Settings → Language & keyboard: every language as tall as the tallest one on |

### Adding a setting
1. Add a row to `registry!` in `registry.rs`.
2. If the shell shows it, add a property and a `changed` handler in `system-settings.slint`, and a row in
   `BINDINGS` in `neoui-render/src/settings.rs`. Tests check every binding against the registry.
3. If the user edits it in Settings, add it to the `Caller::Settings` allowlist in `access.rs`
   ([below](#architecture)) and give it a row on its page.

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
- **Still to do:** a boot check in `symbian/taps.sh` (QEMU virt, US6b): toggle Wi-Fi, reboot, the tile stays off; 24-hour off,
  the Clock app shows 12-hour time.

### Deferred to later parts
- `notify.<app>.*` and Settings → Notifications: Part 2.
- Capability-checked writes to global keys by ROM EXEs: step 0.

## Apps rebuilt on Part 1 (2026-11-09/10)

Two apps were rebuilt before Part 2 (neoui `main`, 2026-11-10). Each follows one pattern: pure models in
`neoui-proto` (host-tested), one `State` global in Slint, and one module per page in Rust and in Slint
(`src/pages/*.rs` with `bind` and `show`, `ui/pages/*.slint`).

### Clock (`NEOCLOCK.EXE`, neoui `872e6dc`)
- **Pages:** Clock (face, Set time), Alarms (editor: days, label, snooze), World (then 21 cities with fixed offsets;
  since replaced by 87 cities with summer-time rules: `clock/world.rs`, `clock/tz.rs`), Timer, Stopwatch.
- **Kept state:** every page's state is kept in settings rows owned by `App("clock")`: `clock.tab`, `clock.alarms`,
  `clock.cities`, `clock.timer`, `clock.stopwatch`. The timer and stopwatch count from wall-clock UTC, so they keep
  running across app restarts and reboots.
- **Time without an RTC:** the UI server's keeper falls back to the boot clock (the kernel's UTC at boot plus elapsed
  time) when a board has no RTC, such as Syborg. It saves within 5 s of a set.
- **Alarms:** the server checks once a minute and rings even while the app is closed. It brings Clock to the front
  and sends `AppEvent::Alarm` (kind 8, `NeoUi` 1.2).
- **Home widget:** the `ClockWidget` on home is the first widget of Part 4. It is live, fed through the `Now` global,
  and opens Clock on a tap.
- **Open:** a two-boot check of every page's saved state (on the phone, or QEMU virt from US6b).

### Dev tools (`NEODEV.EXE`, neoui `ed9202f`)
- **Tabs:** Home · Devices · Console · Procs · More. More opens Settings, Tools and About. Sub-views replace the
  tabs rather than covering them, because a cover lets taps through to the page underneath. Back closes a sub-view.
- **Home:** cards for uptime, memory and CPU (both with 30-second bar graphs), storage, processes and threads, a
  device summary, the modem, and the kernel and slot. Below them, a list of every page.
- **Devices:** every component a phone has (`neoui-proto::devtools::device::CATALOGUE`, in sections). Each state
  comes from the best of three sources:
  1. the kernel's device registry: HAL `ENeoHalDeviceList` 0x4e19, with one `A64_DEVICE` per driver in the arm64
     baseport (kernel branch `device-registry`, `090bb5e`);
  2. the app's probes: memory, display, drives, RTC, NeoModem `STATUS`, ModemState, AdspState, slots;
  3. the log's tags.

  Without a registry (the 2010 kernel on Syborg), parts that some board's driver reports show "Unknown" rather than
  "No driver". "Run checks" runs every check without side effects; the only write is a 4 KB file on C:.
- **A device's view:** the driver, source, state, live values, its check, its log lines, and its tests:
  - Touch: a grid that lights each cell a finger crosses;
  - Display: R/G/B/white/black/grey fills, and the kernel console on or off;
  - Storage: a 1 MB speed test on C:;
  - Audio and ADSP: the mic looped back to the loudspeaker or the earpiece (NeoModem `AUDIO_TEST`);
  - Modem: refresh the status.
- **Console:** the live log, or the last boot's. Only the rows that fit go to Slint. Drag scrolls by whole rows; there
  are Follow, tag chips (All plus the 8 commonest tags), Clear and Save.
- **Procs:** processes (exec `ObjectNext`, `FindHandleOpen`, `ProcessGetMemoryInfo`), sorted by CPU time, then
  memory. A process's view lists its threads with their priority and CPU time. CPU time needs a kernel built with
  `MONITOR_THREAD_CPU_TIME`; the arm64 kernel is not, so it shows "-".
- **More:**
  - Settings: every registered key with its value, owner, type, limit and default; read-only, and live.
  - Tools: save both logs to `E:\logs` (or `C:\logs` without E:), the kernel console overlay, and power, each power
    action behind an inline confirm.
  - About: the builds, slots, display, CPUs, RAM and uptime.
- **Code:** `neoui-proto::devtools` (device, log, stats), `neoapp::hal` (the variant HAL calls, typed), `neoapp::sys`
  (memory, CPUs, processes and threads; shortcut: raw exec calls until e32 wraps them), and
  `symbian/apps/devtools/src/{state,probe,pages/*}.rs`.
- **Log lines (for CI):**
  - `devtools: devices N (kernel K, probe P, log L); procs N threads M; …`;
  - `devtools: kernel registry Listed { devices, bad } | Missing(e)`;
  - `devtools: tab N`, `devtools: view X`;
  - `devtools: check <key> pass|fail|skip <why>`, `devtools: checks P pass, F fail, S skipped`;
  - `devtools: touch test cell c,r (n of 72)`;
  - `devtools: saved …`.
- **Verified:**
  - Syborg on the Mac: every tab and sub-view, Run checks (3 pass, 20 skipped), the colour and touch tests, Back.
  - QEMU arm64 with the registry kernel: `drivers` lists display ok, kbd ok and blk absent (no disk), and Dev tools
    reports `devices 23 (kernel 3, probe 3, log 0)`.
  - Not yet on the phone.
- **Open:**
  - the modem (`qcom_mss`) and USB (`qcom_dwc3_acm`) registry entries, which wait for the kernel stream's edits to
    those files;
  - per-thread CPU time;
  - the battery and other parts with no driver at all.

