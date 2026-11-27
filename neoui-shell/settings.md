<!-- SPDX-License-Identifier: Apache-2.0 -->
# Settings: the store and the Settings app

**Status: the store is done 2026-11-09 (neoui `22af6ac`); the Settings app (NEOSET) SE0–SE4a are built and merged 2026-11-26; board parity V2 is done, and the Settings run of 2026-11-27 built the data stages D1–D11 and D18 with TP2b and TP4 (the [Status](#status-2026-11-26) table lists each). Left: TP7, V3 (the canvas sync) and the hardware stages D12–D17, D19.** One store for the shell and every app (`neoui-proto::settings`,
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

What is built is in the [Status](#status-2026-11-26) table. [The app today](#the-app-today) describes the shell's Settings screen that NEOSET replaced.

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
  - kinds: 1 battery history, 2 Wi-Fi IP/portal, 3 clock sync, 4 app catalogue (SE1, 1.14), 5 battery usage (SE3a,
    1.16), 6 running apps (SE4a, 1.17);
  - later: the notification channels (TP4, a new kind).
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
- **Taps during a sheet's opening animation hit the row under the finger** (seen on SE2b's Pixel run, 2026-11-26:
  "Two beeps" was tapped while the sheet slid up, and Beep was picked). This is the kit's or the shell's behaviour, not
  SE2b's. It may deserve an input lock while a sheet animates; that's the owner's call.

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

**SE1c-1 plan (Saved networks, Forget; `set2-wifi-saved`):**
- **NeoWifi 1.1** (neohw `crates/wifi/src/ipc.rs`, `VERSION` (1, 1, 0)):
  - `op::SAVED = 6`, arg 0 = writable des8 of `SAVED_SIZE` (1 + 8 × 33 = 265 bytes). WIFID writes
    `{count u8, {ssid length u8, ssid}*}`, newest first, at most `Saved::MAX` (8); the PMKs never leave WIFID. It
    completes with the count, or `KErrOverflow` if the buffer is short.
  - `op::FORGET = 7`, arg 0 = des8 SSID (1..=32 bytes, else `KErrArgument`). Removes it from `wifi.dat`; if it is the
    network joined or being joined, WIFID leaves first, as `LEAVE 1` does, so it isn't rejoined. An SSID not saved
    gives `KErrNotFound`, and nothing changes.
  - `Saved::forget` returns whether it found the network. A `SavedNames` encode/decode lives in the host crate,
    shared by WIFID and NEOSET.
- **Versions:** WIFID checks only the major. An old NEOSET against a new WIFID works unchanged. A new NEOSET against
  an old WIFID gets `KErrNotSupported` for SAVED and hides the Saved networks row. In a ROM both come from one build.
- **NEOSET:**
  - page `WifiSaved` = 17 (parent Wi-Fi), with a "Saved networks" row on the Wi-Fi page and a search row;
  - one row per saved name. The subtitle is "Connected" (from LINK), or "Secured", plus "not in range" when the
    latest scan lacks it. The board's "Open" rows don't exist: WIFID remembers only networks with a key (D4);
  - Forget asks for confirmation first (a kit sheet, as the old pads' Reset does), then FORGET, then reloads the list;
  - the footer reads "Stored in C:\private\e0004002\wifi.dat" (the board's path is the old one).
- **Tests:**
  - neohw host: SAVED encoding round trip, at most 8 networks, damaged input refused, `forget` found / not found;
  - neoui: snapshot `set2-wifi-saved`, the act log for Forget and its confirmation, the row table's drift test;
  - phone: first back up `C:\private\e0004002\wifi.dat` with `phone.py pull` (read only). Then the list shows
    the home network as Connected, Forget is cancelled at its confirmation, and FORGET of an unknown SSID gives
    `KErrNotFound`.
- **Approved 2026-11-26** (coordinator), with two deviations from `set2-wifi-saved`: no "Open" rows, since WIFID keeps
  only networks with a key (D4), and the footer shows the real path (`e0004002`, not the board's `e0002001`).
  - The night's phone run skips forgetting the real home network: FORGET is tried on an unknown SSID, and the UI is
    taken up to the confirmation sheet and cancelled.
  - **For the owner:** forget the home network, check it stays off, rejoin, and check a reboot rejoins it. Then
    Disconnect and reconnect with the password (this times WIFID's new `stop()`; Disconnect writes `left.dat`, so it
    waits for someone who has the password).
  - **Known gap, left for the owner (not new):** after a WIFID restart, Disconnect (`LEAVE`) leaves the network joined,
    because `stop()` leaves only when WIFID started the join. FORGET and RADIO off also call `hal::leave`.
    Fixing LEAVE the same way would make `start()` leave first too, which changes how joins work.
  - **Older WIFID gaps found in review (left for the owner):**
    - CONNECT against a link WIFID didn't start (after a restart) can fail its first join with KErrInUse, then drop
      the old link;
    - `LEAVE 1` (forget from the details sheet) ignores a failed save;
    - the supplicant's `sleep()` panics if it can't create its timer;
    - e32's `JoinHandle::join` waits for a fresh signal, so a thread whose exit signal was already used hangs the
      joiner. WIFID works around it (EXITED); a timed join, or one that knows the thread has finished, belongs in
      e32.
    - switch to `sys::replace_private`: the other `save_private` users (WIFID's `left.dat`, MODEMD's `calls.db`,
      `sms.db` and `block.db`, GNSSD's `xtra.*`) still write in place, so a crash mid-save can leave them empty.
- **Pins:**
  - neohw PR first, then neoui's `wifi` pin (both lines in `symbian/Cargo.toml`) at the new neohw rev, rebuilding
    SYSSTART and NEOSET together;
  - phone and files pin neohw through neoui, so their repins wait with phone#10 and files#15 (boot size, the owner).

**SE1d plan (the Apps catalogue, `set2-apps`):**
- **Where the lists come from:**
  - ROM apps: the shell's `host::APPS` (key, EXE). The names and icons are in the shell's `menu.slint`, so neither
    list is complete on its own. `APPS`' keys and names move to `neoui-proto` `apps.rs` (`APPS: &[(key, exe, name)]`):
    the shell starts from it, NEOSET lists from it, and a test checks that every menu.slint app with an EXE is in it.
    Icons stay with each UI (`@neoui/icons/apps/<key>.svg`).
  - Old apps: LEGACY already sends each one to the shell as a launcher entry (`ENTRY`: id = the app's UID, a
    caption of at most 48 bytes, a 128 px icon), and the shell keeps them by app key (`host.entries("legacy")`).
    **No legacy PR is needed.** The entries exist only once LEGACY has run this boot (the user opened Old apps).
- **`SETTINGS_INFO` kind 4 = `INFO_APPS`** (protocol **1.14**):
  - `{count u8, {id u32 LE, caption length u8, caption}*}`, at most `ENTRIES_MAX` (64) × 53 bytes + 1 = 3393 bytes,
    so one call, and `cursor` stays 0. Icons are left out: 64 × 128 px ARGB is 4 MB. The hub shows the generic
    old-app icon (shortcut: real icons need a cache or a smaller ENTRY icon).
  - An empty list means LEGACY hasn't run.
- **`SETTINGS_ACTION` kind 2 = `ACTION_OPEN_ENTRY`** (1.14), `req = id u32 LE`: the shell's `open_entry("legacy",
  id)`, the same as a tap in the Old apps grid. Only `Caller::Settings` (NEOSET's SID) may use it; any other caller
  gets `KErrPermissionDenied`. Back from the old app goes where it does from the grid (`open_entry` doesn't record
  who opened it).
- **NEOSET Apps page:**
  - "Apps": every ROM app (icon, name; Open → `app.open(key, 0, "")`). Apps with a page of their own also offer
    "App settings": Phone → `open phone 3`, Messages → `open phone 3 "messages"`, Dev tools; this is the table
    `settings_app::apps::SETTINGS_PAGE`.
  - "Old apps": the kind 4 list; Open → `ACTION_OPEN_ENTRY`. With none: "Old apps are listed once Old apps has been
    opened since the phone started" and an Open Old apps row. NEOSET doesn't start LEGACY itself (a guest window
    server is costly to start from a settings page).
  - **Versions:** a 1.13 shell answers kind 4 and action 2 with `KErrArgument`; NEOSET then hides the Old apps
    section. The search table gets `apps.*` rows for the static parts.
- **Pin ripple:** inside neoui only (the shell, neoui-proto, settings-ui, NEOSET). phone and files pin neoui, so their
  repins wait with phone#10/files#15. legacy and neohw don't change.
- **Tests:**
  - neoui-proto: the kind 4 round trip, 64 entries fit, damaged input refused, 48-byte captions; the action
    request's encoding;
  - the shell: `apps.rs` against menu.slint; `ACTION_OPEN_ENTRY` refused for a non-Settings caller (a host
    unit test on the access helper);
  - settings-ui: snapshot `set2-apps` with ROM and old apps and with none, and the act log for Open and App
    settings;
  - virt-taps: Settings → Apps → Clock opens Clock;
  - phone (`SIS=xplore,frozenbubble`): open Old apps once, then Settings → Apps lists X-plore and Frozen Bubble, and
    Open starts X-plore.

**SE1d as built** (neoui#44):
- Decided by the coordinator, for the owner to overrule: old apps get the generic icon (`shortcut:`: a kind 5 that
  returns one small icon by id is the upgrade), and NEOSET never starts LEGACY itself.
- **Approved addition:** `total` counts the entries the shell refused (it keeps 64), so the page says "64 of N".
- **App settings:** Dev tools goes to its own settings view; Contacts goes to Phone's settings at Contacts.
- **For the owner:**
  - an image with `SIS=xplore,frozenbubble` comes to 29.0 MB, past the bootloader's RAM-boot limit (see [Board parity](#board-parity-owner-2026-11-26)), so old apps must
    be installed on C: (or go into the ROFS) for test images;
  - on a no-SIS image X-plore won't start (`legacy: start app a0000bcd: -1`, from the grid too). It's probably
    missing files on Z:; check again on an image that has the SIS.

**SE2 plan (Sounds & profiles: `set2-sounds`, `set2-profile`, `set2-ringtone`, S05):**

*What exists today:*
- Three store keys reach MODEMD: `sound.silent`, `sound.vibrate`, `sound.ring_volume` (the shell's
  `phone.rs sync_settings` → modem-ipc `RING_SETTINGS`).
- MODEMD rings with AUDIOD's one synthesized ringtone (`apr::ring_pcm`). A message gets two buzzes plus the first
  0.8 s of the ringtone.
- The shade's Silent tile writes `sound.silent`. The power menu has Power off / Restart / Cancel.
- Nothing has keypad tones or touch vibration.

*Split into three stages, each its own PR cycle:*
- **SE2a: profiles over today's ring (neoui only, protocol 1.15, no neohw change).**
  - neoui-proto `sound_profile.rs` (Apache, host-tested): the built-ins General 0 / Silent 1 / Meeting 2 /
    Outdoor 3 / Offline 4, added ones from 5; the `sound.profiles` blob (versioned, ≤ 1024 B, overrides of the
    built-ins + added records, the last audible profile, the radios Offline turned off); and one pure reducer
    `choose(state, id) -> (state, mirrors)`.
  - The shell runs the reducer. It sets `sound.profile`, the blob, the three mirrors and `radio.airplane` in one
    synchronous call, so watchers and MODEMD see only the final state. Callers:
    - NEOSET through `SETTINGS_ACTION` kind 3 `ACTION_PROFILE` (Settings only);
    - the shade's Silent tile (on: Silent, remembering the last audible profile; off: back to it);
    - the power menu's new profile rows (`powermenu.slint`, Nokia style: the profiles above Power off).
  - Offline = airplane: entering it remembers which radios were on; leaving (another profile, or airplane off
    anywhere) restores them and the previous profile.
  - Upgrade: no `sound.profile` yet → General takes today's volume and vibrate. If `sound.silent` was on, the active
    profile is Silent with General as the last audible one. Nothing sounds different.
  - Pages:
    - Sounds & profiles: the active profile, the list, Add profile;
    - a profile's page: ring volume, Quieter/Louder, vibrate, Rename/Delete for added ones;
    - media volume, route, mic and the tests stay below, as today.
  - Ringtone and message tone show as "Built-in ringtone" / "Two buzzes + the first 0.8 s", read-only until SE2b.
    Keypad tones and Vibrate on touch are left out (D4) until H6.
- **SE2b: tones per profile (neohw + neoui; pins).**
  - modem-ipc `RING_SETTINGS` gains a ringtone id and a message tone id (Built-in, Beep once, Two beeps, None =
    vibrate only), a minor bump with old clients defaulting to Built-in.
  - AUDIOD synthesizes them next to `ring_pcm`; MODEMD plays Beep once / Two beeps once, not looped.
  - The Ringtone page with ▶ preview (a NeoAudio test-style play at the profile's volume, stopped on Back, a call or
    leaving the page).
  - Pins: neohw → neoui. phone pins neohw (modem-ipc), so its repin waits with phone#10 for the owner's boot-size
    decision.
- **SE2c: Your sounds (WAV import).**
  - Files' picker (`OPEN_FILE` pick) → NEOSET checks and converts the WAV to AUDIOD's format into
    `C:\private\e0002007\tones\`, and AUDIOD plays a file tone.
  - The largest part, and it needs AUDIOD's file path; planned after SE2b.

*For the owner (these change how the phone rings or vibrates, so they're not decided here):*
- the built-ins' values: General = today's; Silent = no ring, vibrate on; Meeting = volume 2 and vibrate (Beep once
  needs SE2b); Outdoor = volume 10 and vibrate; Offline = General's sound with the radios off;
- whether Meeting's ring plays once (SE2b changes MODEMD's loop);
- whether Silent also silences the message tone and buzz (today `silent` stops the tone; the buzz stays).

**SE2c plan (Your sounds, WAV import; proposed 2026-11-26, stacked on SE2b, no code until SE2b merges):**

*What exists (research, 2026-11-26):*
- **Picking a file works end to end.** `open(files::KEY, files::PICK, "wav")` opens Files' picker; Files returns a
  read-only handle (`DONE_FILE`); the caller adopts it with `result_file()` (neoapp; the kit app is the example).
  NEOSET doesn't use it yet.
- **The ring buffer holds 2 s.** AUDIOD copies one 192,000-byte period (48 kHz mono s16, `apr::RING_BYTES`) into the
  kernel's audio memory, and the ADSP loops it. That memory is `KAudioBytes = 0x40000` (kernel `qcom_telhal.cpp`),
  shared with media (`MEDIA_OFFSET 0x30000`) and recording. So a file tone longer than ~2 s needs a kernel change.
- **A WAV decoder exists, but in files** (`neo-format-media` `wav.rs`; files pins neoui, so neoui can't pin it back).
  NeoAudio's linear resampler is private.
- **AUDIOD can read another app's `\private`:** ROM EXEs get every capability (KRN-001). neohw's
  `sys::load_private` reads a file and falls back to its `.new`.

*Split into two stages:*
- **SE2c-1: short sounds within today's buffer (neohw + neoui; pins).**
  - **neoaudio** (Apache, host-tested) gains `tones::from_wav(bytes) -> Result<[u8; BYTES], WavError>`. It reads PCM
    8/16/24-bit mono or stereo at 8–48 kHz, mixes to mono, resamples to 48 kHz (the resampler made public), trims
    leading silence, cuts at 2 s with a 50 ms fade, and pads with silence. Float, A-law and µ-law are refused with a
    clear error ("Use a 16-bit PCM WAV"). Tests: each format, rates, too short, too long, damaged headers.
  - **Tone ids 4–15 are your sounds** (the tones byte has 4 bits each). modem-ipc 2.8: `tone::apply` accepts them;
    an older MODEMD treats them as Unknown → Built-in, so it keeps ringing.
  - **NEOSET:** Ringtone sheet → "Add from Files…" → the picker (filter `wav`), then `result_file()`. The file is
    read up to 16 MB, converted with `from_wav`, and written to `C:\private\e0002007\tones\<id>.pcm` (exactly
    192,000 bytes, through `.new` + rename). The name comes from the WAV's INFO name, else the file name, else
    "Sound N". It's kept in a new Bytes key `sound.your_tones` (`[id][len][name]`*, ≤ 512 B, Settings-owned).
    Preview plays the converted file. Rename and Delete are on a long-press. Deleting a sound in use moves those
    profiles back to Built-in in the same store call (the SE2a reducer).
  - **AUDIOD:** for a tone ≥ 4, `prepare_ring` loads that file (exactly `RING_BYTES`, else Built-in; a missing or
    damaged file must still ring). It scales it to the ring volume, as for the synthesized tones. `prepared` is keyed
    by (tone, volume, the file's modified time), so a replaced file is picked up.
  - **MODEMD:** no change beyond the pin; it passes the ids through.
  - **Gates:** host tests; a Pixel run imports a WAV from E: (pushed for the test, deleted after), previews it, sets
    it as ringtone, deletes it, and checks the profile is back on Built-in. MODEMD's `settings.bin` is checked
    byte-identical at the end. A real call with a file tone is for the owner, like SE2b's.
- **SE2c-2: long ringtones (kernel + neohw; the owner's call).** Either grow `KAudioBytes` (a 30 s loop is
  2.88 MB of contiguous physical RAM) and move media and recording past it, or stream the ring through the media path.
  Not planned until the owner picks.

*For the owner:* is a 2 s looped clip acceptable as a first "your sounds", or should SE2c wait for SE2c-2?

**SE2b's file rules (coordinator and review, 2026-11-26):**
- MODEMD's `C:\private\e0003001\settings.bin` stays C8: the old writer's 9 bytes while both tones are Built-in, and
  the same 9 bytes plus a 10th, the tones, once a tone is chosen. An older MODEMD reads the file into 9 bytes, so it
  keeps reading it and loses only the tones.
- The profiles' tones live in `sound.tones`, a key beside `sound.profiles` (which stays version 1). A shell from
  before SE2b drops the unknown key and keeps every profile and edit, losing only the tones.
**Also for the owner:** is a fully silent ring (ringtone None with vibrate off)
ever allowed? For now a ringing profile with ringtone None keeps vibrate on.

**Owner's call, defaults until answered** (approved for SE2a by the coordinator, 2026-11-26): SE2a ships the
proposed values as defaults, each editable per profile. The upgrade keeps today's behaviour exactly, and the other
profiles change nothing until someone picks one. SE2b keeps MODEMD's ring loop as it is today until question 2 is
answered.
- **Morning list (verbatim):**
  1. the built-ins' values: General = today's; Silent = no ring, vibrate on; Meeting = volume 2 and vibrate (Beep
     once needs SE2b); Outdoor = volume 10 and vibrate; Offline = General's sound with the radios off;
  2. whether Meeting's ring plays once (SE2b changes MODEMD's loop);
  3. whether Silent also silences the message tone and buzz (today `silent` stops the tone; the buzz stays).
- **Not selected on the phone at night:** Offline (it drops LTE and Wi-Fi). Host tests and virt cover it.
- **Also for the owner (from SE2a's review):** turning airplane mode *on* elsewhere doesn't enter Offline (D3 only
  says turning it off leaves Offline). If Offline is then chosen and left, airplane mode stays on, because that is
  what the user had. Should airplane on elsewhere make Offline the profile?

*Tests:*
- proto: the blob round trip and its limits, the upgrade mapping, the reducer (Silent remembers and restores; Offline
  restores the radios; deleting the active added profile falls back to General);
- settings-ui: snapshots `set2-sounds` and `set2-profile`, the act log;
- shell: the reducer's callers (host-tested parts);
- virt-taps: the shade's Silent tile → `sound.profile` 1 → back;
- phone: switch General → Meeting → back and read MODEMD's ring settings in the log. No call is made; ringing a call
  needs the owner. The original profile and values are restored at the end.

**What the night's phone runs (2026-11-26) changed on the Pixel's C: (owner's morning list):** all were RAM boots
with `EMMC_C=1`, so the eMMC C: is the real one.
- `C:\private\e0002001\settings.dat` (the shell's store):
  - it now holds `sound.profile` (0, General) and `sound.profiles` (General's volume 1 as an override), written by
    SE2a's upgrade. The installed build drops unknown keys on load, so they're inert there.
  - `display.brightness` is 205/206 after the shade check. The earlier value wasn't logged; it's within a step.
  - `settings.root_grid`: set to grid in the SE1a run, set back to list at the end of the SE2a run.
  - `time.zone` / `time.auto_zone`: set to Sydney and Dublin in the SE1b run, back to Tbilisi with automatic on.
  - `clock.cities`: two cities added and removed in the SE1b run; it is now an empty list (2 bytes).
  - `sound.silent/vibrate/ring_volume`: back to volume 1, not silent, vibrate on (as at boot).
  - `nav.mode`: switched Buttons ↔ Gestures by NEOSET in the SE0 runs (before these notes); not re-checked tonight.
- `C:\private\e0004002\wifi.dat` and `left.dat`: byte-identical before and after SE1c-1's run (`63af15d5…`, empty).
  A rejoin re-saved `wifi.dat` through the new `replace_private`, with the same bytes and no `.new` left over.
- No files were added to `C:\sys\bin` or `C:\Data` by these runs (fa12's test files were deleted by fa12).
- SE2b's run (image 20): `C:\private\e0003001\settings.bin` (MODEMD) was 9 bytes `4338 0100 0100 0100 1e`
  (`a8543b7d…`); it took a 10th tones byte while a tone was chosen, and is byte-identical again after both tones went
  back to Built-in (no `.new` left). `settings.dat` gained `sound.tones`, now empty (0 bytes, every tone Built-in);
  the installed build drops it on load.

- SE3a's runs (images 21–23): `settings.dat` was `07e10b2c…` (656 bytes) at the start of the run and byte-identical
  at the end, every new key back at its default. Image 21's shell (no SE2b) dropped SE2b's empty `sound.tones` key
  from `settings.dat` on its first save; that key was inert there.

- SE3b's runs (images 24–26) wrote nothing: `settings.dat` `07e10b2c…` throughout.
- **fshell note:** on image 24 (flags `ROFS=1 ROFS_CORE='\.dll$' EMMC_C=1 USBDEBUG=1 AUTOFASTBOOT=1500`),
  `phone.py sh "ls -h"` and `sh "ls --help"` printed `sh: serial read timed out; remote completion is unknown; no
  replay`. On images 25 and 26 (same flags) `echo`, `ls` and `ls -l -r` answered, and `pull` worked on all three. So
  it's fshell's `ls` help option, not those boots or tonight's changes.

**SE2b merged 2026-11-26 at the owner's word** (neohw#19 `5964dfb`, neoui#46 `fa84c0f`; the owner tested calls). The test that was asked for: on image 20, a real incoming call, an SMS that
arrives just before a call, and a call during media playback; then merge. PRs neohw#19 (`1430041`) and neoui#46
(`02ff31a`, pins neohw `1430041`). Image: `boot20.img` (27,402,240 bytes, sha256 `8e6b6861…`), on the Mac at
`kernel/out/ekern-bonito/se2b-boot20.img` (gitignored); rebuild from those two heads if it's gone. The night's Pixel run checked: the Ringtone and
Message tone sheets and their previews, MODEMD's tones (`0x02`, `0x01`, `0x03`, `0x13`, `0x20`, back to `0x00`),
None keeping Vibrate on (with its note), the 10th byte only while a tone isn't Built-in, and the file back
byte-identical. No call was made.

**Proposed order:** SE1a, then SE1b; SE1c after a research spike (does the firmware take a directed scan?); SE1d.

**Questions for the owner:** none for SE1a or SE1b. SE1c-2: (a) and (b) above.

**Order:** SE0 comes first and alone, because it fixes Open apps and the dead rows. SE1–SE4 can follow in any order.
SE5 and SE6 follow their platform stages.

#### SE3 plan (proposed 2026-11-26, for review)

*From the boards:* `set2-battery` (Battery saver "Dims the screen", Show percentage "In the status bar", Battery
usage), `set2-battery-usage`, `set2-developer` (Show touches "A dot under each finger"), `set2-language` (Keypress
vibration), `set2-fontsize` (87.5 / 100 / 112.5 / 125 %), `set2-display` and `set2-wallpaper` (eight colours, From
Files, From Photos), `set2-storage`.

*What exists (research, 2026-11-26):*
- **Battery:** the status bar draws the percent inside the battery icon while on battery (`frame.slint`). The shell
  sets the panel brightness from `display.brightness` in one place (`symbian/src/lib.rs` `panel_level` →
  `set_brightness`), with the battery level at hand in the same loop. The recorder keeps 24 h of one-minute
  `Snapshot`s (level, voltage, charge state), but `SETTINGS_INFO` kind 1 sends only the levels. Screen-on time isn't
  recorded.
- **Touches:** every pointer event passes through the shell loop before it's routed. The gesture hint
  (`draw_hint`) is the pattern for drawing over app surfaces. Nothing draws touches today.
- **Vibration:** the shell has `haptic(ms, amp)` (HAL 0x4e27, the old apps' pads use it through `HAPTIC`). The
  on-screen keyboard doesn't use it. `keyboard.vibrate` isn't registered.
- **Fonts:** Theme has five text tokens (`font-status 13`, `font-label 13.5`, `font-body 16`, `font-title 19`,
  `font-clock-large 56`). Literal sizes: about 38 in neoui `ui/`, 12 in neoui's apps, 0 in settings-ui, about 90 in
  phone and about 165 in files.
- **Wallpaper:** home's background is a fixed gradient (`home.slint`). The ROM has no runtime image decoder (Slint
  is built without decoders); files' `neo-format-image` has one.
- **Storage:** e32 `Fs::drives`/`volume` give totals. Files keeps a per-kind index (`files-ops` `Index::groups`),
  but neoui can't pin files.

*Split into four slices, each its own PR cycle; neoui only unless noted:*
- **SE3a: battery and input (proposed first, tonight).**
  - New keys (shell-owned, Settings-writable, `registry.rs`):
    - `battery.show_percent` (Bool, default on = today's icon). Off draws the icon with no number.
    - `battery.saver` (Bool, default off). On caps the effective panel level at 40 % of the panel's max, without
      moving the slider (`min(level, cap)` at the one `panel_level` call). The shade's brightness slider keeps
      showing the setting.
    - `developer.show_touches` (Bool, default off). On, the shell draws a 24 dp ring under each finger over
      whatever is on screen (the `draw_hint` path, erased on up), for touches it routes and ones it keeps.
    - `keyboard.vibrate` (Bool, default off). On, every key press of the shell's keyboard gives a 12 ms pulse through
      `haptic`, like the pads.
  - **Battery usage** (no per-app shares, D4): neoui-proto `battery::usage(&History) -> Usage` (host-tested) gives
    the window (since the last full charge seen, else the history's start), start and end level, time on battery,
    and the gaps ("Off for 6 h, not counted"). The shell sends it as `SETTINGS_INFO` kind 5 `INFO_BATTERY_USAGE`
    (protocol 1.16). The page shows those lines and a note: "Per-app use needs accounting that doesn't exist yet."
  - Pages: Battery gains Saving (two switches) and the Battery usage row; Developer gains Show touches; Language &
    keyboard gains Keypress vibration. Snapshots `set2-battery`, `set2-battery-usage`, `set2-developer`,
    `set2-language`.
  - **Pixel run:** toggle each, check the panel level in the log with the saver on and off, read the status bar in
    a screenshot, take a screenshot with a finger down (show touches), and type in Settings' search (vibration in
    the log). At the end every key goes back to its value at boot.
- **SE3b: Storage.** Drive rows from `drives`/`volume` (E:, C:, D:, Z: with read-only notes), at once. "C: and E: by
  kind" comes from NEOSET's own cancellable worker scan (Images, Video, Audio, Documents, Apps = `\sys\bin` + the
  SIS store, Other), skipping `\private`, `\sys`, `\resource`. "Open in Files" goes to that drive. App data by owner
  moves to SE4, next to Clear data, so nothing sizes `\private\<uid>` blindly. Share E: stays FS6.
- **SE3c: Font size.** `display.font_size` 0–3. The kit's Theme gets `font-scale`, and its four text tokens multiply
  by it (`font-status` and the clock stay fixed). One neoapp helper sets it at start, on change and on resume; SYSSTART
  mirrors it for shell screens. Literal sizes in neoui's `ui/` and apps move to tokens. phone and files follow in
  their own PRs after their neoui repin, which waits with phone#10 and files#15 for the owner's boot-size decision.
  Gate: switch sizes with Phone and Files open.
- **SE3d: Wallpaper colours.** `display.wallpaper` is a palette name (Night = today's gradient, the default; Black,
  Graphite, Blue, Green, Plum, Amber, Dusk as gradients on the kit's tokens). Home reads it. A tap applies it.
  **Pictures (From Files)** need a runtime JPEG/PNG decoder in the ROM (about +300–500 KB). That waits for the
  owner's boot-size decision, then decodes with `zune-jpeg`/`zune-png` on a worker to a 540 × 1080 cache. "From
  Photos" waits for Photos.

*For the owner:* the saver's cap (40 %) and whether it switches on by itself at 15 %; the colours' exact gradients
(from the board); picture wallpapers and the decoder's ROM cost.

**SE3b plan (Storage, `set2-storage`; proposed 2026-11-26, neoui only):**
- **What exists:** e32 `Fs::drives`/`volume` (total, free, media, attributes) and `read_dir`. Files keeps a per-kind
  index, but neoui can't pin files (files pins neoui). Files' `OPEN` pages are Pick and Save only: "Open in Files at
  E:" needs a Files page (`files::BROWSE`, the arg a folder), so it waits for Files' repin (the boot-size decision).
- **Drives** (shown at once, no worker): one row per drive `drives()` lists, as `used of total` with the board's line:
  C: Phone ("Settings, installed apps, app data"), D: RAM ("Temporary files", total only), E: Mass memory ("Media and
  documents"), Z: System ("Read-only", no free space shown). A drive that fails `volume` shows "Not available".
- **C: and E: by kind** (the board's bar and list): a worker thread walks C: and E:, skipping `\private`, `\sys`,
  `\resource` and `\system`. It sums file sizes by extension into Images, Video, Audio, Documents and Other files,
  with the table in neoui-proto (`settings_app::storage::kind_of`, host-tested; the same families as Files' viewers).
  Apps = the sizes in `\sys\bin` on C: and E: (installed EXEs and DLLs). Other = used − files − apps (app data,
  system files). Free = free. The bar shows Apps / Files / Other / Free like the board.
  - The scan is cancellable: leaving the page stops it at the next directory. It shows "Counting…" with the running
    totals, at most 64 directory levels deep, and the result is kept for the app's life. It never opens files, only
    lists them, so nothing is written.
- **Not in SE3b:** app data by owner (SE4, with Clear data); Share E: over USB (FS6); "Open in Files" at a drive (after
  Files' repin; a plain "Open Files" row opens Files at its start).
- **Tests:** `kind_of` and the sums (proto), snapshots `set2-storage` (scanned, counting, an E:-less phone).
  **Pixel run:** the drive rows against fshell's `drive` output and the scan's totals against `du`-style sums of a
  folder, with nothing written (C: hashed before and after: `settings.dat` and the scanned folders' listings).

**SE3b as built** (neoui#48, merged 2026-11-26 as `3f5927c`; coordinator's notes: low priority, only on the page and shown, a kept
count with Recount, Other clamped, unreadable folders counted, Files' units):
- The scan lists 32 folders on the Pixel in 24–39 ms. That is too short to see in the monitor's `cpus`, so it's
  measured by its own log line.
- Codex xhigh review: leaving mid-scan stuck on "Counting…"; a superseded scan writing over a newer one; a wide tree's
  memory (now 4096 folders waiting at most); scanning while hidden; a file-server failure kept as a count; the bar
  mixing the kept count with live totals. All fixed. The Pixel run found a drive without `\sys\bin` counted as
  unreadable and the ROFS Z: shown as "0 B". Both fixed.
- Read-only on the Pixel: `ls -l -r` of E:\ and C:\Data and `settings.dat` byte-identical before and after; the
  drives' free bytes unchanged (a cluster-granularity check only).
- **For the owner:** Storage isn't in the root grid (the board's 12 tiles are full); "Open in Files" at a drive
  waits for a Files page and Files' repin.

**SE3a as built** (neoui#47, merged 2026-11-26 as `85364a1`; coordinator's conditions: every default as before, the saver by hand only
with a named cap, show touches drawing only and measured, usage only from what the history holds):
- `neoui_proto::effects` holds the saver's cap (`SAVER_CAP_PERCENT` 40, a `shortcut:`) and the key pulse (12 ms at
  70, the pads' tick). A host test checks that a fresh store gives today's panel level, no pulse, the percent shown
  and no rings.
- Battery usage (`SETTINGS_INFO` kind 5, protocol 1.16, page 19): the window starts at the last full charge the
  phone then ran down from, else covers the whole history; minutes without a reading count as gaps.
- Codex xhigh review: rings over the shade, square rings over neighbours and the Back hint, hover fingers, pulses per
  code point instead of per press, a refused brightness write taken as done, the usage window and its gaps. All fixed.
- Pixel run (image 23, neohw main): saver on `panel 409 of 1023 (setting 206)`, off `826` at once; `key pulse 12 ms
  amplitude 70 -> 0`; show touches costs about 0.2 ms of the shell's app time per frame while scrolling (3.2–3.5
  against 3.0–3.3 ms at 33 fps); `settings.dat` byte-identical after every key went back.
- **For the owner (left open):**
  - a found row below the fold isn't scrolled to (every long page; Battery's Saving rows are one);
  - the rings pause during a home-page swipe;
  - the first minute after a reboot can count up to 60 s too much as a gap;
  - the show-touches ring hasn't been seen on a screenshot (the debug monitor can't hold a finger down); the owner
    should look: Developer options → Show touches.

#### SE4 plan (proposed 2026-11-26, owner-approved order)
The owner's order: **SE4a** (Stop, Clear data, the two resets) first, then the panel and notifications of
[top-panel.md](top-panel.md) in this push: **TP1 → TP2 → TP4 → TP7**, SE4's notification pages landing with TP4
(Device → Notifications = `tp-settings`; Apps → an app → Notifications = `nt-settings`). TP3 stays with Files
(FA9 M1b); TP5, TP6, TP8 and TP9 come later. Each stage gets its own plan here or in top-panel.md before code.
The per-app notification keys are top-panel.md's `n.<app>` (it replaces this file's `notify.<id>.on/.banner`).

**SE4a plan (neoui 1.17, neohw NeoWifi 1.2):**
- **Protocol (Settings-only by SID, like kinds 2 and 3):**
  - `SETTINGS_INFO` kind 6 `INFO_RUNNING`: the running apps' keys, each with a resident flag.
  - `SETTINGS_ACTION` 4 `ACTION_STOP {key}`: the shell's switcher close (quit, 3 s grace, then a kill).
    `KErrPermissionDenied` for the residents (Phone, Messages: they would respawn) and Settings itself.
  - `SETTINGS_ACTION` 5 `ACTION_RESET {0 network | 1 settings}`: a typed shell job, then the POWER restart path (the
    shell flushes `settings.dat` and the battery log first).
  - `SETTINGS_ACTION` 6 `ACTION_CLEAR {key}`: the shell sends **`AppEvent::ClearData` (kind 28)** to the app,
    starting it hidden if it isn't running. The app clears its own data and quits.
- **Stop** (Apps → an app): "Running" or "Not running" from kind 6; no Stop row for the residents or Settings.
- **Clear data, only where the data's owner can do it (D4, no dead rows):**
  - **Clock** clears its own keys (every key the registry gives to `clock`: alarms, timer, stopwatch, cities, its
    preferences) on `ClearData`.
  - **Messages:** NEOSET asks MODEMD, the SMS owner: `SMS_EDIT` `EDIT_DELETE_ALL` (blocked senders' messages stay).
  - **Phone:** MODEMD `CLEAR_LOG 0`, the call history. Contacts stay (NEOCONT has no clear path yet); the
    question says so.
  - Browser, Files, Terminal and the rest get the row when they handle `ClearData` (with their repins).
- **Reset network settings:** WIFID's new `RESET` (op 8): leave, write `wifi.dat` as a valid empty file (so the old
  `\private\e0002001\wifi.dat` migration can't bring networks back), clear `left.dat`; then the restart. Bluetooth
  bonds and the APN join when their owners exist; the question names only Wi-Fi networks.
- **Reset settings:** every registered key no app owns back to its default, except `registry::RESET_KEEPS`: the
  sound profiles with their live values (a mirror reset alone would be folded into the active profile), the radio
  switches, `legacy.pad.epoch` and `open.always` (the apps chosen per file type). App-owned keys (Clock's alarms,
  Phone's speed dial, `contacts.migrated`) are never touched, and neither is Clock's 24-hour time (Clock's key,
  which Date & time shows): it survives both Reset settings and Clock's Clear data. A host test lists every key as
  reset, kept or an app's. `settings.dat` is saved before the restart, or the action fails and nothing restarts.
- **Pages:** 21 `AppDetail` (the per-app hub, S06) replaces the app sheet: Open, App settings, Stop, Clear data
  (notifications join in TP4). 22 `Reset` under About in both roots: Reset network settings, Reset settings. Every
  destructive row asks first, naming what goes, what stays and "The phone restarts".
- **Checks:** host tests (records, the reset list, the empty `wifi.dat`); virt runs the resets on a scratch C:
  (a changed key back to default, alarms kept; a fabricated `wifi.dat` emptied); the Pixel run stops Clock, clears
  Clock's data with a test alarm (`settings.dat` restored to its hash), and opens and **cancels** both resets and
  the Messages/Phone Clear data questions. The owner's Wi-Fi, SMS and call log are never touched on the phone.

**SE4a Pixel run (2026-11-26, image 29 `se4a-boot29.img`, 27,557,888 bytes):** Apps → Clock showed "Not running",
then "Running" after Open; Stop → "Stop Clock?" → Stop: `neoui: settings stops app clock`, `clock: quit`, a clean
exit. Clear data → Delete: Clock removed its 5 stored keys (`clock: data cleared (8 keys, 0 refused)`), `settings.dat`
saved. Messages and Phone (no Stop row: residents) and both resets: question shown, Cancel (`nav Answer(1)`), nothing
deleted or reset in the log. `settings.dat` pushed back; it and `clock.dat`, both `wifi.dat` and `left.dat` matched
their hashes from before. Seen there and fixed: "Messages's data" → "Delete Messages data?" (neoui `e33c77c`).

#### Board parity (owner, 2026-11-26)
The owner saw that the app and the `set2-*` boards differ. An audit set every board beside its snapshot (neoui
`tools/board_check.py`): the pages, rows, switches and sheets are there and do the real thing, but the look is behind
and many boards show data nothing produces yet. Each stage had been checked for what it does, never against its board.
The owner's decisions:
- **Visual first**, before TP2b: the kit's shared parts, then every existing page to its board.
- **Keep NeoSans**: match the canvas's sizes, weights, colours, icons and copy, not Inter's letter shapes.
- **Build to the board with real data**: what a board shows that the phone can't produce yet gets a data stage,
  D1–D19 in [settings-data.md](settings-data.md). A row whose data doesn't exist stays out until its stage passes;
  where the hardware can't give it, the board is changed to the honest substitute.
- **The board check is a gate** for every stage from now on: the PR lists its pairs and any accepted difference.

What differs in the shared parts (V1):

| # | Board | App today |
|---|---|---|
| A1 | row titles medium (500) | the root's `SettingRow` at regular |
| A2 | a trailing value 14 dp in `text-secondary` | `text-dim` at 13.5 dp |
| A3 | a root row with a switch shows its value as a subtitle (Wi-Fi "Home-5G") | the value on the right |
| A4 | choice sheets: title at the start, radio first, a description line per option | title centred, radio last, no description |
| A5 | detail sheets: title at the start | centred |
| A6 | destructive rows in red (Clear data, Stop app, Erase C:, Reset remembered pads) | white |
| A7 | pill buttons in rows (Forget) | plain dim text |
| A8 | a leading icon or tile on drive, profile, saved-network, search and app rows | missing on many |
| A9 | a section header with text beside its action ("Searching… ⟳") | the icon only |

Richer parts per page (V2), with data that exists: the active-profile card (`set2-sounds`), the three mode cards
with phone drawings (`set2-navigation`), drive tiles with bars (`set2-storage`), the result count, path, highlighted
match and icon (`set2-search`), the app header with icon and EXE line and red actions (`set2-app-browser`), Ringtone
and Time zone as pages rather than sheets, the grid's Notifications/Storage/Security tiles and the root's names and
order (`set2-root-*`), the brightness slider's sun icons, status icons on saved networks.

**The RAM-boot limit (measured 2026-11-26).** A test image (`ROFS=1`) carries Z: inside the kernel, and the
Pixel's bootloader refuses `fastboot boot` when the unpacked kernel passes about 71.6–72.2 MB ("Error verifying the
received boot.img: Volume Corrupt"): 71,608,864 bytes boot, 72,186,784 don't. boot.img's size (about 27.8 MB) is only
a stand-in for it. Installed phones read Z: from `system_x` and aren't limited. Until Z: rides as the boot.img's
ramdisk (a kernel/build change, to plan with the kernel stream), Settings test images leave `NEOFILES` out.

Boards that are wrong about what is built get fixed on the canvas (V3): the `wifi.dat` path (`e0004002`), the user
side (ARMv8-A, not ARMv5TE), Reset under About. Boards still without a page: `bt-device`, `bt-pair`, `fontsize`,
`lock`, `lock-pin`, `notifications`, `notify-app`, `sim-lock`, `storage-drive`, `wallpaper`, `wifi-hidden` (their D
stages), `reset-query` (the shell's QUERY dialog, already built).

| Stage | What |
|---|---|
| V0 | `tools/board_check.py` in neoui (Chromium draws each board at 360×720, set beside the snapshot); this section; [settings-data.md](settings-data.md) |
| V1 | the kit parts A1–A9 as opt-in properties (other apps keep their look), Settings opts in; kit snapshots re-shot |
| V2 | every existing page to its board, in four batches: root + search; Wi-Fi + Connectivity + Mobile + Bluetooth; Display, Navigation, Sounds, Profile, Ringtone, Time zone, formats; Battery, Storage, Apps, App detail, Reset, About, Developer, Privacy, Language, Old apps |
| V3 | the canvas: fixes above, AS BUILT marks where a board now matches |
| D1–D8 | the data available now, in the order D1 → D2 → D3 → D5 → D4 → D6 → D7 → D8 |
| then | TP2b → TP4 with D9 → TP7; D10 → D11 → D18; the large ones (D12–D17, D19) one by one, the owner choosing the order |

### Status (2026-11-26)

| Part | State |
|---|---|
| The design (48 boards, prototype, spec) | done, on the canvas, approved |
| This plan | written 2026-11-25 |
| SE0 | built and merged 2026-11-26: neoui#38 (`b19d597`), e32-rs#16 (`Message::client_sid`), neohw#17 (e32 pin). QEMU walk and three Pixel RAM-boot runs: Open apps card, Wi-Fi list and join (keyboard, wrong password, no double join), Buttons/Gestures by NEOSET's SID, the connect and reap races, keyboard resume. Two Codex reviews, findings fixed |
| SE1 | SE1a (find) merged 2026-11-26: neoui#39 (`5055cdb`); two Codex reviews; Pixel RAM-boot run: grid, search → selected row, Back along the path, Kernel log → Dev tools Console. SE1b (zones) merged 2026-11-26: neoui#40 (`32b032a`); Codex review, findings fixed; Pixel RAM-boot run: Sydney UTC+11:00 (summer time), Dublin UTC+00:00 (no summer time), World clock Yesterday −4 h / Today +7 h. SE1c spike done. SE1c-1 (Saved networks, Forget) merged 2026-11-26: neohw#18 (`5a4f8f2`, NeoWifi 1.1), neoui#43 (`2b222c8`); two Codex reviews (WIFID's stop/save fixes); Pixel run: list, Forget→Cancel, Wi-Fi off/on (stop 121 ms), wifi.dat/left.dat byte-identical. SE1c-2 waits for the owner. SE1d (Apps catalogue) merged 2026-11-26: neoui#44 (`eedb063`, protocol 1.14 INFO_APPS + ACTION_OPEN_ENTRY, neoui-proto `apps.rs`); Codex review, findings fixed; virt-taps walks search → Apps → Clock; Pixel run: ROM apps, the empty state, old apps listed after Old apps ran, eshell opened through Settings |
| SE2 | SE2a (profiles) merged 2026-11-26: neoui#45 (`079ce68`, protocol 1.15 ACTION_PROFILE); two Codex passes (UiMirror's stale edits, writes in one frame, ring before airplane), virt walks Offline and back, Pixel run: Meeting, the shade's Silent, brightness and Wi-Fi checks, all restored. SE2b (tones) merged 2026-11-26: neohw#19 (`5964dfb`, modem-ipc 2.7), neoui#46 (`fa84c0f`, main merged in, CI green); two Codex passes, findings fixed; Pixel run without a call passed and restored; the owner tested calls and asked for the merge. SE2c (Your sounds) is next |
| SE3 | planned 2026-11-26 (SE3a–SE3d). SE3a (battery saver, show percentage, battery usage, show touches, keypress vibration) merged 2026-11-26: neoui#47 (`85364a1`, protocol 1.16), Codex xhigh review fixed, Pixel run on the final head passed and restored. SE3b (Storage) merged 2026-11-26: neoui#48 (`3f5927c`), Codex review fixed, Pixel run on the final head passed (read-only). SE3c waits for the phone/files repins; SE3d colours not started |
| SE4 | SE4a (Stop, Clear data, Reset network settings, Reset settings) merged 2026-11-26: neohw#20 (`4163f92`, NeoWifi 1.2 `RESET`, MODEMD's bulk deletes by SID), neoui#49 (`fca5a1b`, protocol 1.17), docs#68; Codex xhigh review, findings fixed; virt ran both resets; Pixel run on image 29 passed and restored (below). Then the top panel: TP1 merged (neoui#50), TP2a merged (neoui#51, protocol 1.18); next TP2b → TP4 (with SE4's notification pages) → TP7 ([top-panel.md](top-panel.md#phases)) |
| Board parity | decided 2026-11-26 ([above](#board-parity-owner-2026-11-26)). V0 merged (neoui#53, docs#74); V1 kit parts merged (neoui#54 `a2e4d37`); V2 batches 1–4 merged (neoui#55, #56, #57/#58, #60 `96610d5`: root, grid, search; Wi-Fi, Connectivity, Mobile, Bluetooth; Display, Navigation, Sounds, Profile, Ringtone and Time zone pages; Storage, Apps, App detail, Reset, About, Developer, Language). Each with the board check, a Codex xhigh review and a Pixel run on the final head. Batch 4 also baked the keyboard's alphabets into Settings (Cyrillic and Armenian drew as blanks). V3 (canvas sync) is left |
| Settings run (2026-11-27) | the owner asked for everything at once: Codex (xhigh) wrote the specs, parallel agents built them in worktrees, the integrator merged them on neoui `set2-int`, two Codex reviews (findings fixed), Pixel RAM boots on each integration. Built: **D1** one row model (pages, search, root; search keeps its query on Back); **D2** Wi-Fi link fields, Console overlay switch, the active slot; **D3** per-drive counts, C:'s bar, file systems, root C: free; **D4** app identity and sizes (INFO 8), owners, confirmed Clear data; **D5** screen-on time since full charge (INFO 9); **D6** message-tone line, keypad tones and vibrate on touch, preview pause, your own ringtones; **D7** wallpaper colours and font size; **D8** clipboard-read toast, diagnostics; **D9 + TP4** notifications (protocol 1.21); **D10** switcher columns, swipe down closes apps, Lanes, the home editor; **D11** SIM card lock; **D18** update status; honest "Not yet (Dxx)" rows for D12–D17, D19. Protocol 1.20/1.21 ([protocol.md](protocol.md)). PRs: neoui#61, neohw#21 (modem-ipc 2.8/2.9), e32-rs#18, phone#12, docs (this). Not run on the phone: call/SMS-driven cards and banners (no network at the test spot), WAV import, Lanes. Deferred: inline reply (REPLY_TEXT), Contacts/Messages touch feedback, display language strings, wallpaper pictures, read-only app permissions |
| SE5–SE7 | not started |

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

