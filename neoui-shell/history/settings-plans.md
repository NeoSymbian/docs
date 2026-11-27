<!-- SPDX-License-Identifier: Apache-2.0 -->
# Settings app: the SE1–SE4 plans as written

Part of [neoui shell](../README.md) · Status: record · Updated: 2026-11-27

The implementation plans for the Settings app's SE1, SE2, SE3 and SE4a stages, with their as-built notes, review findings and Pixel runs (all 2026-11-26), moved out of [settings.md](../settings.md) on 2026-11-27. They are kept as written. What is built now is in settings.md's [Status](../settings.md#status) and [settings-data.md](../settings-data.md).

## SE1 plan (proposed 2026-11-26, for review)

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
only, and every scan is passive (`:2141`; [wifi.md](../../hardware/wifi.md) W3c: active scans missed 2.4 GHz here).
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
  - an image with `SIS=xplore,frozenbubble` comes to 29.0 MB, past the bootloader's RAM-boot limit (see [Board parity](../settings.md#board-parity-owner-2026-11-26)), so old apps must
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


## SE3 plan (proposed 2026-11-26, for review)

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

## SE4 plan (proposed 2026-11-26, owner-approved order)
The owner's order: **SE4a** (Stop, Clear data, the two resets) first, then the panel and notifications of
[top-panel.md](../top-panel.md) in this push: **TP1 → TP2 → TP4 → TP7**, SE4's notification pages landing with TP4
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
