<!-- SPDX-License-Identifier: Apache-2.0 -->
# Settings data: what the boards show and who produces it

Part of [neoui shell](README.md) · Status: active · Updated: 2026-11-27

**Status: plan 2026-11-26; D1–D11 and D18 built 2026-11-27 (the Settings run, table below), D12–D17 and D19 show honest "Not yet (Dxx)" rows until their hardware stages.** The owner decided that NEOSET matches the design canvas's `set2-*` boards and that every value a board shows is real ([settings.md](settings.md#board-parity-owner-2026-11-26)). This file is the data side: the stages D1–D19, each with its producer, protocol, gate and feasibility. It was written by Codex (xhigh, read-only, from the `origin/main` trees named below); the order the owner approved is in settings.md. The visual side (V0–V3) is in settings.md too.


Four board values already have producers worth reusing. WIFID supplies **all four** requested Wi-Fi detail fields. F32 supplies free bytes for **C:**, although Settings currently prefers E: for the root summary. The kernel exposes both the console-overlay state and the booted A/B slot. The largest gaps are cellular packet data, Bluetooth, and calibrated battery attribution.

Codex inspected the local `origin/main` trees, including `docs b1e2d91`, `neoui 56f4775`, `neohw 4163f92`, `kernel 73111a3d`, `e32-rs b525e9f`, `build dc684b5`, `phone 8165f58`, `files 39ab88a` and `browser ddf32c9`. The hardware roadmaps are in the **docs** repository at these revisions. It read source only: no builds, tests or phone runs. The checks below are implementation acceptance criteria. [Settings status](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/settings.md#status-2026-11-26) · [Hardware ownership](https://github.com/NeoSymbian/docs/blob/b1e2d91/hardware.md)

## Built (2026-11-27)

<!-- stages -->
| Stage | What | State | Updated | Next / evidence |
|---|---|---|---|---|
| D1 | Shared row values, search, both roots | done | 2026-11-27 | neoui#61: one row model; left: dynamic instances, scroll to a hit |
| D2 | Wi-Fi details, console overlay, slot | done | 2026-11-27 | neoui#61: WIFID link record, HAL 0x4e02/03, active slot |
| D3 | Drive totals, per-drive kinds, C: free | done | 2026-11-27 | neoui#61; left: the per-drive kinds page, shell work (finishing plan W1), not FS6 (that is USB sharing, D17) |
| D4 | App identity, size by owner, Clear data | done | 2026-11-27 | neoui#61 (INFO 8, OWNER_REPORT, INFO 13); owners in other apps left |
| D5 | Screen-on time since full charge | done | 2026-11-27 | neoui#61: charge-cycle recorder, INFO 9 |
| D6 | Profile feedback, previews, your own ringtones | done | 2026-11-27 | neoui#61, neohw#21 (modem-ipc 2.8, NeoAudio 1.1); WAV import not run on the phone |
| D7 | Wallpaper, font scale, display language | active | 2026-11-27 | colours and font size built; left: pictures (INSTALL_WALLPAPER, protocol 1.22), language strings (settings.md L0–L2), other apps' font scale |
| D8 | Clipboard notice, permissions, diagnostics | done | 2026-11-27 | toast and diagnostics built; read-only app permissions deferred |
| D9 | Notification policy and pages | done | 2026-11-27 | with TP4, protocol 1.21; left: MODEMD's alert policy, inline reply |
| D10 | Navigation settings and Edit home | done | 2026-11-27 | G3–G5 and the home editor; left: Add to home from the menu, 2×2 widgets |
| D11 | SIM lock and attempts left | active | 2026-11-27 | page reads the card; PIN changes held back until the review's fixes (below) |
| D12 | Hidden Wi-Fi join | open | 2026-11-27 | "Not yet" row; needs the kernel's directed scan (SE1c-2) |
| D13 | Mobile bearer, mode, APNs, traffic | open | 2026-11-27 | "Not yet" row; waits for C10 |
| D14 | Bluetooth discovery, pairing, profiles | open | 2026-11-27 | "Not yet" row; waits for B0–B8 |
| D15 | Lock policy, device PIN, double-tap wake | open | 2026-11-27 | "Not yet" row; TP8/TP9 are shell software (finishing plan W2); only double-tap wake needs the kernel |
| D16 | Attributed battery estimates | open | 2026-11-27 | "Not yet" row; after D5 and radio instrumentation |
| D17 | Eject E: and share over USB | open | 2026-11-27 | "Not yet" row; waits for FS6 |
| D18 | Check for OS updates | active | 2026-11-27 | status row built ("Update service unavailable"); a signed feed is open |
| D19 | Network reset extensions, Erase C: | open | 2026-11-27 | "Not yet" row; after D13/D14, then recovery (SE7) |
<!-- /stages -->

What each built and what it left:

| Stage | As built | Left |
|---|---|---|
| D1 | `settings_app/row_model.rs`: stable row ids, instances, one provider for page, search and root; search keeps its query, scroll and selection on Back | visible APs / saved SSIDs as instances; a hit below the fold isn't scrolled into view |
| D2 | Wi-Fi details from WIFID's link record; Console overlay (HAL 0x4e02/03, `REPAINT` 45 after off); About's active slot (HAL 0x4e09) | — |
| D3 | C: and E: counted apart, C:'s Apps/Files/Other bar, file system per drive (e32 `file_system_name`/`sub_type`), mount generation, root "C: … free" | the per-drive kinds page (NEOSET only; it doesn't need FS6) |
| D4 | INFO 8 from SYSSTART (catalogue, EXE found, measurements), owners Dev tools and Terminal (`OWNER_REPORT` 42), confirmed Clear data with tickets (INFO 13), the shell's own measurement on a worker | owners in datetime, Files, Browser, Phone/Messages; full-colour app icons |
| D5 | the charge-cycle recorder (discharge + display-on only, gaps counted), A/B checkpoints, INFO 9, Battery usage's card and Screen-on time | per-app shares (D16) |
| D6 | message-tone line; keypad tones and vibrate on touch per profile (`CONTROL_FEEDBACK` 44); preview pause/elapsed; your own ringtones (WAV import, modem-ipc 2.8, NeoAudio 1.1) | Contacts/Messages feedback; picking your sound as a message tone; ring-gain preview |
| D7 | wallpaper colours (`display.wallpaper`), font size (`display.font_size`: Settings, home and the shade) | pictures (needs INSTALL_WALLPAPER), display language strings, the other apps' font scale at their repins |
| D8 | clipboard-read toast (`privacy.clip_notice`), diagnostics = Dev tools' local log | read-only app permissions (needs the capability words) |
| D9 | with TP4, protocol 1.21: `CHANNEL` 34, INFO 7, `n.<app>`, DND, banners, the Notifications pages | MODEMD's alert policy (DND for calls/SMS, favourites); inline reply |
| D10 | switcher columns and thumbnails, swipe down closes apps, Lanes, `home.layout` and the home editor (ACTION 9) | "Add to home" from the menu; 2×2 widgets |
| D11 | modem-ipc 2.9: protection state, SET_PIN_PROTECTION, CHANGE_PIN; the SIM card lock page; one-attempt rule; PINs never stored or logged | a spare-SIM run for the mutating paths; PUK |
| D18 | About: "Slot a · Update service unavailable" | a signed feed (INFO 11, CHECK_UPDATE) |
| D12–D17, D19 | honest "Not yet (Dxx)" rows on Wi-Fi, Mobile, Bluetooth, root, Notifications, Reset | their stages |

### Open after the run (Codex review, 2026-11-27)

- **D11 PIN changes are held back.** MODEMD answers `SET_PIN_PROTECTION` / `CHANGE_PIN` with `KErrNotSupported`, and
  the SIM lock page only reads the card. They come back once these are fixed:
  - Settings and MODEMD authenticate their NeoModem and NeoHub servers by SID.
  - HWHUB restricts destinations to the owning daemon.
  - The sheet freezes the target card and the selected application.
  - The observed try count is checked at dispatch.
  - PIN fields use wipeable fixed storage, and the kernel HAL scrubs its copy.
- **Partial fixes to finish:**
  - **Settings store:** treat a partial decode (records dropped) as unresolved.
  - **Dev tools Clear data:** keep the verified file's identity through deletion, using a private quarantine instead
    of a public `.del` name.
  - **Tone import:** reserve durably and never overwrite an occupied PCM; one staging path per import.
  - **MODEMD `settings.bin`:** start unresolved on a file-server connect failure; invalid bytes are not absence.
  - **Cycle checkpoints:** keep replay through late resolution.
  - **`channels.dat`:** a decode failure refuses writes.
  - **Owner FINISH:** keep the receipt until it is acknowledged; a dead D4 worker must fail its ticket.
  - **INFO 8 / INFO 13:** publish them together after a save.
  - **Badge exclusions at boot:** apply them before the modem's counts.
  - **Banner overlay:** apply it on fade and drag frames too.
  - **Old `sound.tones` pairs:** convert them on the next save.
  - **Phone card actions:** bind them to a posting token.
  - **Storage rescan:** keep it pending until the new tally lands.
  - **virt-taps:** pin Phone's branch.
  - **Notifications:** controls stay disabled while a policy can't be read.
  - **Accessibility:** keyboard focus for the secondary actions.

## Protocol and delivery order

The D-numbers order the data work. The SE, TP, G, B, C, H and FS numbers retain their existing owners and gates. Independent stages can proceed once their stated dependencies are met. **S** means an existing producer can be exposed directly, **M** means a new bounded feature in known components, and **L** means a substantial cross-repo, hardware or recovery effort.

Use `SETTING_GET/SET/WATCH` **8/9/10** for preferences, native daemon IPC for daemon-owned data, and `SETTINGS_INFO/ACTION` **40/41** for shell-owned snapshots and operations. INFO **1–6** already mean battery history, IP/portal, clock sync, legacy app entries, observed battery usage and running apps. Reserve **INFO 7 for TP4 channels**. Proposed later kinds are `APP_DETAIL`, `BATTERY_CYCLE` and `VOLUME_STATE`. Keep existing decoders working. Implement the cursor in `neoapp::settings_info` for new paged records, with a revision so a reader can restart after a change. Event **27** is reserved for snapshot invalidation. Assign new numbers in `protocol.md` in merge order. Privileged actions require both the Settings app key and SID `0xE0002007`. [Protocol allocation](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/protocol.md#opcodes-app--shell) · [Current client](https://github.com/NeoSymbian/neoui/blob/56f4775/symbian/neoapp/src/lib.rs#L748) · [Caller checks](https://github.com/NeoSymbian/neoui/blob/56f4775/crates/neoui-proto/src/settings/access.rs#L23)

## Data stages

### D1 — Shared row values, search and both roots · M · SE1a extension, start first

`settings_app/rows.rs` contains **89 static rows**. `search_with` ranks title, alias, page title and formatted live value. `settings-ui::live_value` reads Slint state, 23 rows are explicitly valueless, and device polling refreshes several values only while their own page is open. Custom profiles, individual drive/category rows, runtime app details, channels and Wi-Fi detail rows have no general instance index. The existing drift test covers selected components, literal titles and selected repeaters. A search hit currently clears the query. [Row index](https://github.com/NeoSymbian/neoui/blob/56f4775/crates/neoui-proto/src/settings_app/rows.rs#L496) · [Value formatter](https://github.com/NeoSymbian/neoui/blob/56f4775/crates/settings-ui/src/lib.rs#L15) · [Device refresh](https://github.com/NeoSymbian/neoui/blob/56f4775/symbian/apps/settings/src/lib.rs#L331)

Extend `settings_app/{rows,page}.rs` with a stable row ID, optional instance ID, destination, availability and value provider. Make the page, search result and root summary use the same formatted value. Enumerate dynamic rows from their owners. Refresh cheap readings on search entry, watch preferences, and refresh expensive measurements asynchronously with a timestamp or counting state. A search must work before the user visits the target page. Index action rows by name and exclude credentials, clipboard contents and PIN entry. Carry the instance into navigation and restore the query on Back. This also gives the UI team one source for list and grid, independent of tile placement.

**Gate:** Extend `settings-ui/tests/rows.rs` to compare every board row and generated instance with its destination and provider. On Pixel, cold-open Settings, search for a measured value, change it outside Settings, and reopen the correct instance from the updated result. Repeat this gate as each producer below lands.

### D2 — Existing Wi-Fi details, console overlay and slot · S · available now

- **Wi-Fi:** `qcom_wcn3990.cpp` → `WlanLink` HAL `0x4e1f` → NeoWifi `LINK=2` → `Wifi::poll` → `LinkView::new` already supplies BSSID, phone MAC, association ID and received data frames, including the ARP/IP subset. The counters are per association. Bind D1 to those records. Keep INFO 2 for IP/portal. [Link fields](https://github.com/NeoSymbian/neoui/blob/56f4775/crates/neoui-proto/src/wifi.rs#L351)
- **Developer:** Reuse Dev tools’ `neoapp::hal::{console_shown,set_console}` in NEOSET. HAL GET `0x4e03` and SET `0x4e02` already exist. Read back after a write and on resume, including changes made from Dev tools. No store key or shell action is needed. [HAL helpers](https://github.com/NeoSymbian/neoui/blob/56f4775/symbian/neoapp/src/hal.rs#L80)
- **About:** Keep `neoapp::build::lines()`. Add `hal::slot_info()` (`0x4e09`) and parse the kernel’s validated `current a|b` result. A GPT-read error or a platform without slots yields an unavailable reading. Update-check history belongs to D18. [Slot producer](https://github.com/NeoSymbian/kernel/blob/73111a3d/baseport/arm64/sdm670_assp/qcom_bootctrl.cpp#L175)

**Gate:** Test disconnected, unsupported and malformed responses. On Pixel, compare the Wi-Fi fields with a controlled AP, generate traffic and rejoin. Toggle the console from both apps and observe the overlay. Compare the slot with `fastboot getvar current-slot`.

### D3 — Drive totals, per-drive categories and C: root summary · M · SE3b extension

`symbian/apps/settings/src/storage.rs::drives` already gets per-drive size/free from `Fs::{drives,volume}`. Change the root provider to select **C: explicitly** and include the letter. Today it chooses E: first. The existing cancellable scanner combines C: and E: in one tally. Retain a separate generation, volume identity, captured used/free and tally for each drive. Group Images + Video, Music, Documents and Other according to the drive board. Reconcile Other with used bytes, including unclassified files, private allocation and filesystem overhead. Preserve the overview’s existing Apps/Files classification. Mark an interrupted or unreadable scan as partial. [Drive selection and tally](https://github.com/NeoSymbian/neoui/blob/56f4775/symbian/apps/settings/src/storage.rs#L63) · [SE3b acceptance](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/settings.md#se3-plan-proposed-2026-11-26-for-review)

Add e32-rs `Fs` bindings for existing F32 `RFs::FileSystemName` and `FileSystemSubType`. Use the mounted result for FAT subtype, RAM or ROM/composite volumes. Drive reads stay local to NEOSET. **Gate:** Fixture trees on two drives with distinct totals, absent E:, cancellation and remount during scan. Compare Pixel bytes with fshell `drive` and a known media directory. Root free space must change when only C: changes.

### D4 — App identity, size by owner and Clear data · L · SE1d + SE4a extension

Use `neoui-proto::apps` for native key, EXE and SID, existing launcher assets for icons, and `legacy/host/legacy.cpp::{PublishL,IconL}` for bridge icons. INFO 4 supplies legacy IDs/captions and a total after the bridge registers them. Fetch one cached thumbnail by ID when needed. Generate the version line from the **deployed** app and engine build metadata. Browser’s `std/Cargo.lock` actually pins Servo 0.8.0, but a ROM stamp alone cannot identify a replacement engine on C:. [Native catalogue](https://github.com/NeoSymbian/neoui/blob/56f4775/crates/neoui-proto/src/apps.rs) · [Legacy record](https://github.com/NeoSymbian/neoui/blob/56f4775/crates/neoui-proto/src/settings_app/info.rs#L184) · [Servo pin](https://github.com/NeoSymbian/browser/blob/ddf32c9/std/Cargo.lock#L5267)

Add a Settings-only `INFO_APP_DETAIL` record with app identity, per-drive `u64` data/cache/log bytes, measurement status and supported clear scope. Owners report their files and shell-owned settings records. For cold apps, use bounded, on-demand owner requests. An additive SID-bound owner report can use the next free app opcode **42** and request event **29** if needed. Reuse `ACTION_CLEAR=6` and `ClearData` event **28**. Record durable owner completion before announcing success or refreshing totals. Current shell dispatch can succeed when the event is merely queued.

| Owner | Data and clear boundary |
|---|---|
| `browser` | `symbian/neoweb/src/library.rs` owns chrome files under `C:\private\e0007001`. Connect the shell event to `std/webengine/src/serve.rs`’s existing `Command::ClearData` for cookies, site storage and cache. Count disk-backed bytes on their actual drive. Name the bookmark/history policy in the confirmation and preserve downloaded user files. |
| `files`, Terminal, Dev tools | Files reports its recent/favourite records, index, thumbnails and caches in `symbian/app/src`. Clear the named app data while preserving documents and trash contents. Terminal has no verified file-backed history/log owner on this baseline. A verified empty owner can report zero. Dev tools can attribute its own named exports under `E:\logs` or the C: fallback. |
| `phone`, `neohw`, Clock | Keep MODEMD’s `SMS_EDIT/EDIT_DELETE_ALL` and `CLEAR_LOG 0` paths. The former preserves blocked-sender messages and the latter preserves contacts. The contacts book belongs to Phone’s private store. Clock clears its owned keys. Attribute each dataset once even where Phone and Contacts share a board label. |
| `legacy`, later Store | Extend the SIS install inventory with owned paths and re-stat installed C: files. Deduplicate shared files, distinguish installed bytes from mutable data, and use ST4/ST5 package records as they arrive. An unstarted bridge or missing inventory yields unknown coverage. |

**Gate:** Exact-sized C:/E: fixtures, a shared file, a missing engine, interrupted clear and legacy inventory absent at launch. On a disposable Pixel profile, compare before/after owner reports and verify unrelated contacts, messages and public downloads by hash. [Current clear contracts](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/settings.md#se4-plan-proposed-2026-11-26-owner-approved-order) · [Browser engine clear](https://github.com/NeoSymbian/browser/blob/ddf32c9/std/webengine/src/serve.rs#L841)

### D5 — Screen-on time since full charge · M · SE3a extension, feasible now

SYSSTART already samples the PM660 and saves the 1,440-minute history in alternating `C:\private\e0002001\battery-{a,b}.dat` files. INFO 5 has a fixed 28-byte populated record. Keep that codec. Add a separately versioned `BATTERY_CYCLE` snapshot and private checkpoint spanning more than 24 hours. In `symbian/src/{battery,screen,lib}.rs`, accumulate monotonic on-battery time while the display HAL acknowledges **on**, reconcile at boot/wake, and preserve gaps. Start a cycle at observed full charge followed by discharge. Until then report the measured interval with its actual start. Feed the same duration into search. [Existing usage codec](https://github.com/NeoSymbian/neoui/blob/56f4775/crates/neoui-proto/src/settings_app/info.rs#L61) · [Display transition](https://github.com/NeoSymbian/neoui/blob/56f4775/symbian/src/lib.rs#L1545) · [Battery HAL contract](https://github.com/NeoSymbian/docs/blob/b1e2d91/hardware/battery.md)

**Gate:** Full while plugged in, 100% while discharging, failed display transition, wall-clock change, reboot, missing sample and a cycle longer than 24 hours. On Pixel, time alternating screen-on/off intervals across lock and reboot. The dark interval must add zero screen-on time.

### D6 — Profile feedback, ringtone preview and imported WAVs · M; long clips L · H6 and SE2c

SE2b already has profile tone IDs, `sound.tones`, `ACTION_PROFILE=3`, built-in previews and MODEMD ring settings. Derive the message-tone description from the selected tone and effective sound/vibration policy. For H6, add keypad-tone and touch-feedback flags to the profile reducer and active mirrors, including `sound.keypad_tones`. Keep the existing `keyboard.vibrate` scope explicit. Route local keypad audio through NeoAudio and accepted-touch feedback through the bounded DRV2624 pulse path (`HAPTIC=25`, HAL `0x4e27`). One accepted gesture gets one pulse. Phone keypad feedback must preserve in-call DTMF. [Profile implementation and SE2c](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/settings.md#stages) · [Hardware support](https://github.com/NeoSymbian/docs/blob/b1e2d91/hardware.md)

In `symbian/apps/settings/src/sound.rs`, retain a preview stream and use NeoAudio `PAUSE=5`, `STOP=6`, `INFO=7`. Derive elapsed time from played frames and sample rate. Stop on replacement, page exit or call preemption. For SE2c-1, use Files PICK and `RESULT_FILE=29`, validate a C:/E: PCM WAV, convert it in `neohw/crates/neoaudio`, and atomically install the documented 192,000-byte, two-second clip at `C:\private\e0002007\tones\<id>.pcm`. Use IDs 4–15, `sound.your_tones`, AUDIOD `prepare_ring` fallback, and the profile reducer when deleting an in-use tone. SE2c-2 needs the documented streaming or kernel audio-buffer decision for longer ringtones. [NeoAudio frame counter](https://github.com/NeoSymbian/neohw/blob/4163f92/crates/neoaudio/src/lib.rs#L388)

**Gate:** Old profiles, corrupt WAVs, pause/resume position, stale preview completion and deletion during use. On Pixel import from E:, remove the source, preview and pause, switch profiles, and verify a real test call/SMS, keypad sound and a single touch pulse.

### D7 — Wallpaper, font scale and display language · S/M/L · SE3d, SE3c, then SE5

| Feature | Producer and implementation | Gate |
|---|---|---|
| Wallpaper colours **S**, pictures **M** | Home currently draws a fixed gradient. Register `display.wallpaper` as the documented palette name or private asset token. SE3d colours can ship now. For pictures, use the Files picker handle, bounded JPEG/PNG decoding on a worker, crop/scale to the 540×1080 cache, then a Settings-only wallpaper-install action. SYSSTART validates and atomically replaces its private raster. Pictures depend on the decoder/ROM-size decision. Photos needs a real picker returning the same contract. | On Pixel apply every palette, then import from E:, remove the source and reboot. A damaged or oversized image must leave the previous wallpaper usable. |
| Font scale **M** | Register `display.font_size` 0–3, default 1, with scales 0.875/1/1.125/1.25. Keep **NeoSans**. Scale the four kit text tokens in `ui/theme.slint`. One `neoapp` adapter reads on launch, watches changes and reapplies on resume. Mirror in SYSSTART and migrate literal sizes across shipped clients. Preserve fixed status/clock text, key faces and hit targets. Full delivery depends on the Phone and Files repins and their boot-size decision. | Test all levels. On Pixel change size with Phone and Files already open, resume both, then cold-open the other shipped apps. |
| Display language **L** | Today `keyboard.en/hy/ru` selects input layouts. Add independent `ui.language`, default `en`, to the registry and shared watcher. Bundle Slint `@tr`/`.po` catalogues in shell, kit and apps. Localize Rust-produced status, plurals, dates and search terms. Publish each locale after catalogue and NeoSans glyph coverage are complete. | Test missing strings, glyphs and plural forms. On Pixel switch to Armenian, search a localized live value and reboot with the keyboard layout independently selected. |

[SE3 dependencies](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/settings.md#se3-plan-proposed-2026-11-26-for-review) · [Display-language contract](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/settings.md#o-display-language-l-se5)

### D8 — Clipboard notice, app permissions and diagnostics · S/M · SE4; installed-app coverage follows D4

- **Clipboard:** Clear already works. Register `privacy.clip_notice`. At `host.rs::clip_get`, emit a shell toast after a successful nonempty `CLIP_GET=21`. Attribute the read using the caller SID, coalesce repeated reads, and exclude failed reads and `CLIP_KIND=30` probes. The toast needs only the app name. [Clipboard dispatch](https://github.com/NeoSymbian/neoui/blob/56f4775/symbian/src/host.rs#L1360)
- **Permissions:** Present effective capabilities from `ProcessSecurityInfo` for running processes and actual deployed E32 headers/build metadata for cold apps, with provenance. ROM EXEs receive all capabilities on this build. C: EXEs can specify `caps=` today. Extend the D4 detail record and later consume installer grants at ST5/ST10. The current platform supports a read-only capabilities view. Runtime revoke switches need an enforcing service or loader contract. [Build capability handling](https://github.com/NeoSymbian/build/blob/dc684b5/emitter/build_rust_exe.py#L119) · [Store integration](https://github.com/NeoSymbian/docs/blob/b1e2d91/store.md)
- **Usage & diagnostics:** There is no verified collection/upload service behind `privacy.diagnostics`. Dev tools already has local logs and explicit export. Use that as the current destination. If local opt-in collection is wanted, wire the key to an actual bounded SYSSTART collector with defined fields, retention and deletion, and describe it as local. A sharing switch needs a real recipient and delivery contract.

**Gate:** On Pixel paste in two apps, probe clipboard type, disable notices and repeat. Compare capabilities of a known C: test EXE and ROM EXE. For local collection, prove that switching it off stops new records and that deletion clears the retained data.

### D9 — Notification policy, per-app summaries and root row · L · SE4 with TP4

TP1 and TP2a are present. Follow the owner’s **TP1 → TP2 → TP4 → TP7** sequence and retain TP3’s Files dependency. Use `NOTIFY=18`, `BADGE=19`, `NOTIFY_CLEAR=32`, reserved `CHANNEL=34`, `REPLY_TEXT=35`, event 24 and **INFO 7** for declared channels/effective policy. In `neoui-proto`, `symbian/src/{host,sound,lib}.rs`, `phone` and `neohw`, implement one policy calculation shared by Settings, shade, banners, MODEMD alerts and later the lock screen. [Panel stage status](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/top-panel.md) · [Channels and importance](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/top-panel.md#channels-and-importance-tp4)

Use typed `n.<app>` records with allow and channel importance. Version the record to carry the board’s independent banner, sound and lock-visibility choices. Add `notify.dnd`, `notify.dndto`, `notify.dndfav` and `notify.bannert`. Compute each app’s summary and the root’s live summary from effective policy. Disabling an app rejects posts/badges and clears existing ones. DND suppresses alerting, including MODEMD’s SMS tone, while eligible cards remain in the shade. Implement alarms/favourite/repeat-call exceptions. Panel rows for media, island and tiles arrive with TP3/TP6/TP7.

**Gate:** Test independent banner/sound combinations, DND expiry, old records and SID isolation. On Pixel receive an SMS over Files, exercise reply, mute only its sound, then enable DND. Compare the audible result, shade, app summary and root summary. Verify lock redaction with D15.

### D10 — Navigation settings and Edit home · M for G3/G4, L for G5/editor · SE5

`nav.mode` exists. Register `nav.switcher_cols` 2–3 for G3 and bind it to the real switcher layout/thumbnails. Register `nav.swipe_close` for G4 and wire the top-edge recognizer to the shell’s existing close/resident handling. Register `home.style` for G5’s Pages/Lanes implementation, fed by actual events and running apps. Edit home currently leads back to Navigation. Add a shell action to enter the real home editor and persist its packed layout in versioned `home.layout` bytes per Home Part 3. G6 lock gestures belong to D15. [G3–G6 contracts](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/navigation.md#modes-and-settings) · [Home layout](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/home.md#part-3-home-pages-pin-and-unpin-dock)

**Gate:** Test gesture cancellation, resident handling, full pages and damaged layout. On Pixel verify two/three columns, close an ordinary app, preserve resident service, switch home styles, reorder an item and reboot.

### D11 — SIM lock and remaining attempts · M · SE5, independent of C10

`neohw/crates/modem/src/uim.rs::card` already receives PIN1/UPIN state and attempts. NeoModem `STATUS=1`/`NOTIFY=10` expose attempts (`255` means unknown), and `VERIFY_PIN=14` exists. Enabled-and-verified and disabled currently collapse to `PRESENT`. NEOSET also loses PIN-required/blocked distinctions in `Modem::poll`. Add a negotiated protection-state result compatible with old fixed-size clients. Implement `SET_PIN_PROTECTION` and `CHANGE_PIN` in `modem-ipc`, the UIM client and MODEMD. Complete the requesting authenticated session, re-read the card, clear PIN buffers and avoid automatic replay after a timeout or modem restart. No settings key or kernel change is required. [UIM decoding](https://github.com/NeoSymbian/neohw/blob/4163f92/crates/modem/src/uim.rs#L18) · [Current Settings client](https://github.com/NeoSymbian/neoui/blob/56f4775/symbian/apps/settings/src/modem.rs#L72)

**Gate:** Test old/new descriptor sizes, UPIN, blocked/unknown attempts, card removal and interrupted commands. On a spare SIM enable protection, change the PIN, reboot, unlock and restore the original configuration. The card supplies every displayed attempt count.

### D12 — Hidden Wi-Fi join · M/L · SE1c-2, kernel and band gate

The firmware accepts a directed SSID. The current driver sends passive wildcard scans, and association ordinarily copies the SSID from the scan entry. Extend `qcom_wcn3990.cpp::ScanStart` and `WlanScan 0x4e1e` with a directed raw SSID. Use the directed response for association or extend the `WlanLink` join payload. In `neohw/crates/wifi` and `symbian/wifid`, extend `SCAN=1` and `CONNECT=3` compatibly, migrate `wifi.dat` to retain the hidden flag, and reconnect by raw SSID bytes. Preserve ordinary passive discovery and existing `SAVED=6`, `FORGET=7`, `RESET=8`. [SE1c-2 spike and owner gate](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/settings.md#se1-plan-proposed-2026-11-26-for-review)

**Gate:** Test migration, non-UTF-8 SSIDs, wrong credentials and reboot reconnect. Verify controlled hidden APs independently on 2.4 and 5 GHz. Active scans previously missed 2.4 GHz. A 5-GHz-only release remains the documented owner decision if that persists.

### D13 — Mobile bearer, network mode, APNs and monthly traffic · L · SE6/C10

MODEMD supplies registered RAT, operator, SIM and roaming status now. `radio.data` is a preference. LTE registration does not establish a packet bearer. Complete the kernel IPA/GSI endpoints and rmnet/QMAP path in `qcom_ipa.cpp`, HWHUB’s IPA handshake/recovery, and MODEMD WDA/WDS bearer control. Use the C10-selected network interface. An rmnet device beneath NEONET is the documented short path. [C10 baseline and exit gate](https://github.com/NeoSymbian/docs/blob/b1e2d91/hardware/modem.md#c10-mobile-data)

Use NAS capabilities and readback for `data.network_mode`. Enforce `data.roaming` before starting a bearer and when registration changes. MODEMD owns the APN list, credentials and applied profile. `data.apn` can hold the selected profile ID. Count accepted cellular IP RX/TX bytes exactly once at the packet interface. Persist bounded `u64` monthly buckets in the owner’s private store, with period start, coverage and restart generation. Expose a native usage snapshot for the Data usage page, mobile summary and search. Define the calendar-month boundary and retain a partial-month marker when collection starts late.

**Gate:** Known-size traffic in both directions, Wi-Fi handover, month rollover, clock correction, daemon/modem restart and denied roaming. On Pixel verify ping/HTTP over LTE and available 3G, RAT/APN readback, and an unchanged cellular count during Wi-Fi-only traffic. Until C10 passes, show the actual RAT/registration and bearer availability.

### D14 — Bluetooth discovery, pairing and per-device profiles · L · SE6/B0–B8

Today `radio.bt` is a preference. Build the WCN3990 GENI UART/HCI LDD and H4 transport at B0, firmware/IBS and recovery at B1, executor/GATT at B2, and SSP/LESC and durable bonds at B3. `neohw` owns `bt-ipc` and BTSRV, `kernel` owns transport/power, and `build` packages the daemon. BTSRV publishes applied name/visibility, discovery results, paired peers and connection state. `bt.name` and `bt.visible` express requested settings. Persist bonds and per-device policy privately. SYSSTART handles incoming pairing with Settings closed, using the controller’s actual six-digit comparison and an expiring peer-specific request. [Bluetooth milestone contracts](https://github.com/NeoSymbian/docs/blob/b1e2d91/hardware/bluetooth.md)

Carry the B4/B5 stack stages forward. Expose Audio after B6 A2DP, Calls after B7 HFP and a verified duplex audio route, and Input after B8 HID. Distinguish a device advertising a service, the user enabling it and a connected route. **Gate:** Independent peer discovery/name/visibility, SSP match/reject/timeout, reboot reconnect, Wi-Fi/LTE coexistence, 30-minute music with call preemption, a two-way headset call, and actual keyboard/mouse events. Use “No driver yet” or the specific unsupported profile until its gate passes.

### D15 — Lock policy, device PIN and double-tap wake · L · SE6/TP8 → TP9, G6

`screen.rs` already handles power, idle and call wake. TP8 adds shell lock state at screen-on, swipe unlock, emergency/ringing/alarm paths and filtered notification rendering from D9. Reconcile the two docs once: use top-panel’s `notify.lock` for global visibility and derive the board’s None/Swipe/PIN style from `lock.on` and shell-owned `lock.pin_set`. If `lock.style` is exposed, make it a derived value. Changing a setting must not bypass an enrolled PIN. Both roots can then show the effective security summary. [Settings lock contract](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/settings.md#d-device-lock-and-sim-pin-l-lock-m-sim-se5se6) · [Panel settings keys](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/top-panel.md#settings-keys)

TP9 adds a Settings action that opens SYSSTART’s trusted enrol/change/remove dialog. Keep the salted, versioned KDF verifier, attempts and backoff under `C:\private\e0002001`; protect the derived keys and reset paths. Device PIN digits stay inside that dialog. Double-tap wake is a separate kernel gate. Bonito’s `a64_touch.cpp::A64Touch_Sleep` puts the sensor asleep. Implement low-power gesture detection, wake IRQ and enable/readback before offering `lock.double_tap`.

**Gate:** Test wake, backoff across reboot, policy downgrade, redaction, emergency access, incoming call and alarm return-to-lock. Measure dark-screen double taps, false wakes and idle drain on Pixel. Power-key wake is the available substitute until that test passes.

### D16 — Attributed battery estimates · L · after D5 and radio instrumentation

ARM64 already accumulates scheduler ticks per thread. The public `ThreadGetCpuTime` executive is gated by `MONITOR_THREAD_CPU_TIME`, which the documented phone build lacks. First enable/probe that path and reuse `neoapp::sys::threads`. Add process/SID totals that survive thread/process exit and PID reuse. Group the browser engine with Browser, and Phone/Contacts together. Measure display on-time/brightness, Wi-Fi active periods, and modem voice/data active and tail periods at their owners. Registration time, association time and packet counts alone are insufficient. [ARM64 scheduler](https://github.com/NeoSymbian/kernel/blob/73111a3d/kernel/eka/nkernsmp/arm64/a64s_ncsched.cpp#L224) · [Existing CPU reader](https://github.com/NeoSymbian/neoui/blob/56f4775/symbian/neoapp/src/sys.rs#L181)

Calibrate a bonito-specific energy model against independently measured energy across screen, CPU, Wi-Fi, mobile, call and idle workloads. Persist the model version, coverage and residual with D5’s charge cycle. Define mutually exclusive accounting for Screen, Mobile network, Phone & Contacts, Browser, System, Wi-Fi, Messages and Clock. Account for shared kernel/radio work once. Publish **estimated share of cycle energy** with an explicit unassigned component. System must represent measured/modelled system work rather than absorb every discrepancy.

**Gate:** Short-lived processes, concurrent workloads, reboot gaps and attribution conservation on host. On Pixel validate against held-out workloads and an independent power measurement with a stated error bound. **Recommendation:** Build the counters and screen-time row. Keep SE3a’s observed discharge, coverage and measured durations until calibration passes. Exact per-app energy is unavailable from the present PM660 interface.

### D17 — Eject E: and share over USB · L · D3, then SE6/FS6

E: is internal mass memory. Implement Eject as an acknowledged logical dismount with a remount path. For Share, use a Settings-only `SETTINGS_ACTION` subkind and `INFO_VOLUME_STATE`. SYSSTART owns confirmation, busy checks, flush/dismount, debug suspension, host ownership, remount and debug restoration. `usb.share` is a request with sharing off at boot. FS6 needs the DWC3 PSL, `usbc`/`usbcc`, `smassstorage`/`MSFS.FSY`, ROM components and correct E: removable reporting. Export only E:. [FS6 implementation and blocker](https://github.com/NeoSymbian/docs/blob/b1e2d91/filesystem.md#fs6-usb-mass-storage)

**Gate:** Busy files, host eject, unplug, failed export and debug restoration. Copy a file through the PC, verify its hash after remount and verify C: remained usable. A fastboot RAM-boot pass is provisional. Installed-phone delivery also requires the documented normal-boot USB power fix.

### D18 — Check for OS updates · S for status, M for a real check · SE6, after D2

The active slot and build are available. There is no configured OS update server. Show the real slot, “last checked never” when there is no completed-check record, and “Update service unavailable” while no feed exists. For an actual check, `build` must publish authenticated bonito release metadata with a comparable build identity. Add a bounded fetch/verification worker and private last-success UTC/result record. Distinguish check failure, current build and available release. An offline attempt must not manufacture a successful timestamp.

**Gate:** Test wrong board, invalid signature, older release, network failure and reboot persistence. On Pixel compare the installed stamp with a controlled signed feed. **Recommendation:** Keep flashing outside this Settings action. Installing an OS update has its own FS5b inactive-slot and rollback gate. [Build identity](https://github.com/NeoSymbian/neoui/blob/56f4775/symbian/neoapp/src/build.rs#L12) · [FS5b](https://github.com/NeoSymbian/docs/blob/b1e2d91/filesystem.md#fs5-rofs-and-ab-updates)

### D19 — Network reset and Erase C: · M / L · SE4a extensions, then SE7

- **Network reset, after D13/D14:** Keep `ACTION_RESET=5` with payload `0`. WIFID `RESET=8` already writes a valid empty `wifi.dat` and clears the leave marker. Add BTSRV forget-all, including controller bond state, and MODEMD bearer teardown/custom-APN reset, including the selected profile. Have `host.rs::reset_action` record per-owner durable results, retry partial completion idempotently and restart after success. The confirmation names the implemented owners. Test owner failure and reboot with disposable Wi-Fi credentials, bonds and APNs. Verify SMS, contacts and files survive. [Existing reset contract](https://github.com/NeoSymbian/docs/blob/b1e2d91/neoui-shell/settings.md#se4-plan-proposed-2026-11-26-owner-approved-order)
- **Erase C:, after D15 and recovery support:** Add a typed erase variant to action 5. SYSSTART confirms the phone PIN if enrolled and hands a single-use intent to recovery. `kernel` and `build` supply the recovery entry, validated FS3 C: partition bounds and a restartable completion record outside C:. Format the C: filesystem only. Refuse ambiguous layouts. Test interrupted formatting at multiple points on a disposable image, verify E:/MBR/GPT/ROM/slot hashes, then repeat on a disposable phone configuration. **Recommendation:** Keep the action unavailable until recovery passes. A filesystem reset provides no forensic secure-erasure guarantee. [Partition bounds](https://github.com/NeoSymbian/kernel/blob/73111a3d/baseport/arm64/common/specific/a64_medblk.cpp#L4)

## Board coverage

| Board | Data stages |
|---|---|
| `set2-battery-usage` | D5 measured cycle and screen time · D16 estimated shares |
| `set2-apps`, `set2-app-browser` | D4 identity, icons, sizes and clear · D9 notification summary |
| `set2-mobile` | D11 SIM protection status · D13 RAT, APNs, policy and usage |
| `set2-sim-lock` | D11 |
| `set2-wifi-details`, `set2-wifi-hidden` | D2 details · D12 directed join |
| `set2-storage`, `set2-storage-drive` | D3 reads and breakdown · D17 dismount/share |
| `set2-bluetooth`, `set2-bt-pair`, `set2-bt-device` | D14 |
| `set2-wallpaper`, `set2-fontsize`, `set2-language` | D7 |
| `set2-lock`, `set2-lock-pin` | D9 notification policy · D15 lock, PIN and wake |
| `set2-notifications`, `set2-notify-app`, `tp-settings`, `nt-settings` | D9 · D15 lock-screen enforcement |
| `set2-privacy` | D8 · D4 installed-app metadata |
| `set2-about` | D2 slot/build · D18 update check |
| `set2-developer` | D2 |
| `set2-profile`, `set2-ringtone` | D6 |
| `set2-navigation` | D10 |
| `set2-reset` | D19, with D11/D15 keeping SIM and phone PIN distinct |
| `set2-root-list`, `set2-root-buttons`, `set2-root-grid` | D1 shared providers · D3 C: free · D9 notifications · D15 security |
| `set2-search` | D1 across every shipped producer · D5 supplies “Screen-on time since charged” |

**Release verification:** The source reads `git -C docs show origin/main:neoui-shell/settings.md`, `git -C docs show origin/main:neoui-shell/protocol.md` and `git -C neoui show origin/main:crates/neoui-proto/src/settings_app/rows.rs` exited **0**. At implementation time, run `cargo test -p neoui-proto -p settings-ui` in `neoui`, the changed owner-crate tests, `virt-taps`, and the documented `neo fetch && neo rom` and `neo kernel bonito` gates. Record the candidate image, source pins and actual phone result per stage. A root or search row is complete when a cold-opened NEOSET shows the same value as its owning page and that value changes when the underlying device or service changes.

