<!-- SPDX-License-Identifier: Apache-2.0 -->
# Settings: the Settings app (NEOSET)

Part of [neoui shell](README.md) · Status: active · Updated: 2026-11-27

**Status:** SE0–SE4a and board parity V0–V2 were built and merged on 2026-11-26. The Settings run of 2026-11-27 built
the data stages D1–D11 and D18 with TP2b and TP4 (docs#81), with D11's SIM PIN changes held back. Left: TP7, V3 (the
canvas sync), SE5–SE7 and the hardware stages D12–D17, D19. Each stage is in the [Status](#status) block.

This page is the Settings app, `NEOSET.EXE`: its design, stages and status. The settings store it reads and writes
(`neoui-proto::settings`, `SETTING_GET`/`SET`/`WATCH`, done 2026-11-09) is in [settings-store.md](settings-store.md);
the data every board shows, and who produces it, is in [settings-data.md](settings-data.md). The keys the top panel
adds (`shell.*`, `notify.*`, `island.*`, `lock.*`) are listed in [top-panel.md](top-panel.md#settings-keys). The
registry (`registry.rs`) holds every key; the canvas's `set2-spec-keys` lists them with the ones the v2 pages add.

## The Settings app (NEOSET)

Written 2026-11-25. This is the implementation plan for the Settings app:
- a real app, `NEOSET.EXE`, inside neoui, replacing the shell's Settings screen;
- every screen of the design canvas's Settings page;
- the platform work it needs;
- the stages SE0–SE7.

What is built is in the [Status](#status) block. [The app today](#the-app-today) describes the shell's Settings screen that NEOSET replaced.

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
and every missing part with file:line evidence. Its findings are folded into [The platform work](#the-platform-work)
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
    [C](#c-per-app-keys-and-who-is-calling-m-se0--se1).
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
    ([settings-store.md](settings-store.md)).
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
- Every input of today's screen gets a new source; see the [Architecture](#architecture) table.
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
  SID check refuses them). The fix is binding by SID at `connect`: [Step 0](history/step-0.md)'s second half, done in protocol 1.20
  (sessions are bound by SID and the spawned process id; [protocol.md](protocol.md)).
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
- **SE0:** `Message::client_sid()` and `Caller::Settings` with its allowlist (see [Architecture](#architecture)).
- **SE1:** the registry resolves typed patterns after exact rows: `notify.<id>.on/.banner` (Bool, default true) and
  `<id>.default_page` (Int 0–7). The same resolver runs for GET, SET, file load and reset.
- **SE4:** `NOTIFY` and `BADGE` return `KErrPermissionDenied` for an app whose notifications are off, and existing
  cards go. This needs the caller check too ([Step 0](history/step-0.md); TP2a added it for NOTIFY and BADGE).

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
- **SE6, Share E: = FS6** ([filesystem.md](../storage/filesystem.md)):
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

#### O. Display language (LG, SE5)
- **The key:** `ui.language` (≤ 8, default `en`), independent of the keyboard.
- **Translations:** Slint 1.18's bundled translations (`@tr`, `.po` catalogues compiled in, no gettext on the
  device), in the shell, the kit and each app. Rust-made strings (dates, statuses) are translated too.
- **The choice** offers a language only when its catalogue and glyphs are complete.
- **The owner's decision O2 (2026-11-27):** build the mechanism (Slint `@tr`, the `ui.language` key, a Rust string
  catalogue) plus **Armenian and Russian** for SYSSTART, NEOSET and the kit. The other apps adopt it at their next
  repin. Stages LG0–LG2 below:
  - **LG0:** prove `@tr` with bundled translations and a runtime switch in our `no_std` Slint build, through
    `neoui_kit::compile`. If it doesn't work, stop and ask the owner.
  - **LG1:** `ui.language`; wrap the SYSSTART, NEOSET and kit strings; a Rust-side catalogue (about 600 strings:
    rows, dates, plurals).
  - **LG2:** hy and ru translations; the Display language row goes live; NeoSans covers every glyph.

#### P. Panel, notifications, old apps (S, SE0; L, SE4/SE5)
- **Panel & notifications** (`tp-settings`) sits at Device → Notifications in both roots. Apps → an app →
  Notifications opens the same per-app page (`nt-settings`).
- **The rows follow their stages:** each row appears as its TP stage of
  [neoui-shell/top-panel.md](top-panel.md) ships (tiles TP7, channels and DND TP4, the island TP6). DND
  must also hold MODEMD's SMS tone, not only the banner.
- **Old apps' pads** are ported whole in SE0, under Apps: vibration, strength, default pad, directions, A, **B**,
  handedness, console, and Reset (behind a QUERY).

#### Q. Speed and memory (S, SE0)
See [Architecture](#architecture). If a cold start is slow, the fix is the app's first frame (fewer live pages,
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
| **SE5** language, SIM, panel | Display language (O2: LG0–LG2); SIM PIN lock and change; Panel & notifications as TP1–TP7 land; G3/G4/G5 rows | neoui, neohw, apps | Armenian UI through a reboot; SIM PIN on a spare SIM |
| **SE6** hardware pages and lock | Lock (TP8, TP9 PIN); Bluetooth B3/B6–B8; C10 mobile data; FS6 Share E:; Check for updates | neoui, neohw, kernel, build | each owner's own device gate |
| **SE7** erase | Erase C: through recovery | kernel, build, neoui | on a disposable C: image first |

**Order:** SE0 comes first and alone, because it fixes Open apps and the dead rows. SE1–SE4 can follow in any order.
SE5 and SE6 follow their platform stages.

#### SE1 plan (proposed 2026-11-26, for review)
Built. The SE1a–SE1d and SE2a–SE2c plans, their as-built notes, reviews and Pixel runs (2026-11-26), with the night's
record of what the runs changed on the Pixel's C:, are in
[history/settings-plans.md](history/settings-plans.md#se1-plan-proposed-2026-11-26-for-review). SE1c-2 (hidden
networks) continues as [D12](settings-data.md#d12--hidden-wi-fi-join--ml--se1c-2-kernel-and-band-gate).

#### SE3 plan (proposed 2026-11-26, for review)
Built. The SE3a–SE3d plans and the SE3a/SE3b as-built notes are in
[history/settings-plans.md](history/settings-plans.md#se3-plan-proposed-2026-11-26-for-review); SE3c and SE3d were
built as D7 on 2026-11-27.

#### SE4 plan (proposed 2026-11-26, owner-approved order)
The owner's order: SE4a first, then the top panel's TP1 → TP2 → TP4 → TP7, with SE4's notification pages landing
with TP4. The SE4a plan and its Pixel run are in
[history/settings-plans.md](history/settings-plans.md#se4-plan-proposed-2026-11-26-owner-approved-order).

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
side (ARMv8-A, not ARMv5TE), Reset under About. Boards still without a page (no `set2-*`
snapshot in neoui `snapshots/`, 2026-11-27): `bt-device`, `bt-pair`, `lock`, `lock-pin`, `storage-drive`,
`wifi-hidden` (their D stages), `reset-query` (the shell's QUERY dialog, already built). `fontsize`, `notifications`,
`notify-app`, `sim-lock` and `wallpaper` got theirs in the Settings run.

| Stage | What |
|---|---|
| V0 | `tools/board_check.py` in neoui (Chromium draws each board at 360×720, set beside the snapshot); this section; [settings-data.md](settings-data.md) |
| V1 | the kit parts A1–A9 as opt-in properties (other apps keep their look), Settings opts in; kit snapshots re-shot |
| V2 | every existing page to its board, in four batches: root + search; Wi-Fi + Connectivity + Mobile + Bluetooth; Display, Navigation, Sounds, Profile, Ringtone, Time zone, formats; Battery, Storage, Apps, App detail, Reset, About, Developer, Privacy, Language, Old apps |
| V3 | the canvas: fixes above, AS BUILT marks where a board now matches |
| D1–D8 | the data available now, in the order D1 → D2 → D3 → D5 → D4 → D6 → D7 → D8 |
| then | TP2b → TP4 with D9 → TP7; D10 → D11 → D18; the large ones (D12–D17, D19) one by one, the owner choosing the order |

### Status

<!-- stages -->
| Stage | What | State | Updated | Next / evidence |
|---|---|---|---|---|
| SE0 | NEOSET app, out of the shell | done | 2026-11-26 | neoui#38, e32-rs#16, neohw#17; three Pixel runs |
| SE1 | Grid, search, zones, saved Wi-Fi, apps catalogue | done | 2026-11-26 | neoui#39 #40 #43 #44, neohw#18; SE1c-2 (hidden networks) continues as D12 |
| SE2 | Sound profiles, tones, your sounds | done | 2026-11-27 | neoui#45 #46, neohw#19; WAV import built as D6 (neoui#61) |
| SE2c-2 | Ringtones longer than 2 s | parked | 2026-11-26 | needs a kernel audio-buffer change; the owner's call |
| SE3 | Battery, input, storage, font size, wallpaper | done | 2026-11-27 | neoui#47 #48; font size and colours as D7 (neoui#61); pictures wait (D7) |
| SE4 | Stop, Clear data, resets, notification pages | active | 2026-11-27 | SE4a neoui#49 neohw#20; TP4 + D9 neoui#61; left: TP7, the capabilities view |
| SE5 | Language, SIM PIN, panel, navigation rows | active | 2026-11-27 | G3–G5 rows (D10), SIM lock page read-only (D11); left: display language (LG0–LG2), PIN changes |
| LG0 | Prove Slint `@tr` in our `no_std` build | open | 2026-11-27 | O2; bundled translations and a runtime switch through `neoui_kit::compile` |
| LG1 | `ui.language` and the string catalogue | open | 2026-11-27 | O2; SYSSTART, NEOSET and kit strings; a Rust catalogue (~600 strings) |
| LG2 | Armenian and Russian | open | 2026-11-27 | O2; hy + ru; the Display language row goes live; NeoSans glyph check |
| SE6 | Hardware pages and lock | open | 2026-11-27 | update status row only (D18); waits for TP8/TP9, B3, C10, FS6 |
| SE7 | Erase C: through recovery | open | — | waits for recovery support (D19) |
| V0 | Board check tool | done | 2026-11-26 | neoui#53, docs#74 |
| V1 | Kit parts A1–A9 | done | 2026-11-26 | neoui#54 |
| V2 | Every page to its board | done | 2026-11-26 | neoui#55 #56 #57 #58 #60; board check, Codex review, Pixel run each |
| V3 | Canvas sync | open | 2026-11-27 | the fixes listed under Board parity; AS BUILT marks |
<!-- /stages -->

The data stages D1–D19 have their own block in [settings-data.md](settings-data.md#built-2026-11-27).

**Evidence per stage:**
- **SE0** (neoui#38 `b19d597`, e32-rs#16 `Message::client_sid`, neohw#17 e32 pin): a QEMU walk and three Pixel RAM-boot
  runs: the Open apps card, the Wi-Fi list and join (keyboard, wrong password, no double join), Buttons/Gestures by
  NEOSET's SID, the connect and reap races, keyboard resume. Two Codex reviews, findings fixed.
- **SE1:** SE1a find (neoui#39 `5055cdb`): grid, search → selected row, Back along the path, Kernel log → Dev tools
  Console. SE1b zones (neoui#40 `32b032a`): Sydney UTC+11:00 (summer time), Dublin UTC+00:00, World clock. SE1c-1
  Saved networks and Forget (neohw#18 `5a4f8f2`, NeoWifi 1.1; neoui#43 `2b222c8`): `wifi.dat`/`left.dat`
  byte-identical. SE1d Apps catalogue (neoui#44 `eedb063`): ROM apps, the empty state, old apps listed after Old apps
  ran. Codex reviews on each, findings fixed.
- **SE2:** SE2a profiles (neoui#45 `079ce68`): virt walks Offline and back; Pixel run with Meeting and the shade's
  Silent, all restored. SE2b tones (neohw#19 `5964dfb`, modem-ipc 2.7; neoui#46 `fa84c0f`): the owner tested calls
  and asked for the merge. SE2c-1 (your own ringtones, WAV import) was built in the 2026-11-27 run as D6 (not run on
  the phone).
- **SE3:** SE3a battery saver, show percentage, battery usage, show touches, keypress vibration (neoui#47 `85364a1`)
  and SE3b Storage (neoui#48 `3f5927c`, read-only Pixel run): Codex xhigh reviews fixed, Pixel runs on the final
  heads. SE3c font size and SE3d wallpaper colours: D7 (2026-11-27).
- **SE4:** SE4a Stop, Clear data, Reset network settings, Reset settings (neohw#20 `4163f92`, NeoWifi 1.2 `RESET`;
  neoui#49 `fca5a1b`; docs#68): virt ran both resets, Pixel run on image 29 passed and restored. Then the top panel:
  TP1 (neoui#50), TP2a (neoui#51), TP2b and TP4 with SE4's notification pages (neoui#61, phone#12;
  [top-panel.md](top-panel.md#phases)). The clipboard-read toast is D8.
- **Board parity** (decided 2026-11-26, [above](#board-parity-owner-2026-11-26)): V1 `a2e4d37`; V2 batches 1–4 (root,
  grid, search; Wi-Fi, Connectivity, Mobile, Bluetooth; Display, Navigation, Sounds, Profile, Ringtone and Time zone
  pages; Storage, Apps, App detail, Reset, About, Developer, Language; `96610d5`). Batch 4 also baked the keyboard's
  alphabets into Settings (Cyrillic and Armenian drew as blanks).
- **The Settings run (2026-11-27):** the owner asked for everything at once. Codex (xhigh) wrote the specs, parallel
  agents built them in worktrees, the integrator merged them on neoui `set2-int`, two Codex reviews (findings fixed),
  Pixel RAM boots on each integration. It built D1–D11 and D18 with TP2b and TP4, and honest "Not yet (Dxx)" rows for
  D12–D17 and D19 (what each built: [settings-data.md](settings-data.md#built-2026-11-27)). Protocol 1.20/1.21
  ([protocol.md](protocol.md)). PRs: neoui#61, neohw#21 (modem-ipc 2.8/2.9), e32-rs#18, phone#12, docs#81.
  - **Held back:** D11's PIN changes (MODEMD answers `SET_PIN_PROTECTION`/`CHANGE_PIN` with `KErrNotSupported`; the
    SIM lock page only reads the card), until the review's findings are fixed
    ([settings-data.md](settings-data.md#open-after-the-run-codex-review-2026-11-27)).
  - **Not run on the phone:** call/SMS-driven cards and banners (no network at the test spot), WAV import, Lanes.
  - **Deferred:** inline reply (`REPLY_TEXT`), Contacts/Messages touch feedback, display language strings, wallpaper
    pictures, read-only app permissions.

## Part 1: settings store (done 2026-11-09)

Moved to [settings-store.md](settings-store.md) on 2026-11-27: the store's code, protocol (`SETTING_GET`/`SET`/`WATCH`),
the first registered keys, how to add a setting, log lines and tests.

## Apps rebuilt on Part 1 (2026-11-09/10)

Clock and Dev tools as first rebuilt on the store (2026-11-09/10): in
[settings-store.md](settings-store.md#apps-rebuilt-on-part-1-2026-11-0910).
