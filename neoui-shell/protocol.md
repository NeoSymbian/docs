<!-- SPDX-License-Identifier: Apache-2.0 -->
# The NeoUi protocol: every opcode and event

The protocol between an app and the shell (`SYSSTART.EXE`, server `NeoUi`), in one table. The source of truth is
`neoui/crates/neoui-proto/src/ipc.rs`: its module doc has the version history, and the constants have the wire
details. The app side is `neoapp` ([kit.md](kit.md#the-app-api-neoapp)). This page also **reserves the numbers for
work that has been designed but not built**, so that two designs can't pick the same opcode again.

**Rules**
- **Major and minor versions.** A connect with another major version is refused; minors are additive. A record that
  grows keeps its old bytes as a prefix, so an older app's record still decodes (1.9's NOTIFY, 1.11's progress).
- **Numbers are never reused.** Retired opcodes and event kinds stay reserved.
- **Taking a number.** A design takes the next free opcode and event kind from the table below and records it here
  in the same docs PR. The minor version is assigned when the code merges, in merge order.
- **Events** are 16 bytes: `[kind, a, b, c]` as little-endian u32s.

## Versions (built)

| Version | Date | What came | Where it is described |
|---|---|---|---|
| 1.0 | 2026-11-06 (R6) | geometry, surface, damage, events, keyboard, nav, power | `ipc.rs` |
| 1.1 | 2026-11-09 | the settings store | [settings.md](settings.md) |
| 1.2 | 2026-11-10 | the shell wakes Clock for an alarm | [settings.md](settings.md#clock-neoclockexe-neoui-872e6dc) |
| 1.3 | 2026-11-12 | keyboard modes and height changes | [keyboard.md](keyboard.md) |
| 1.4 | 2026-11-14 | title, toolbar, pages (title and toolbar retired in 1.8) | `ipc.rs` |
| 1.5 | 2026-11-14 | number and phone pads | [keyboard.md](keyboard.md) |
| 1.6 | 2026-11-14 | launcher entries, front | [../legacy.md](../legacy.md#the-old-apps-launcher-protocol-16) |
| 1.7 | 2026-11-16 | PAGE and QUERY (the strip and Options sheet were retired in 1.8) | [navigation.md](navigation.md) |
| 1.8 | 2026-11-17 | Navigation v2 and Shell v2: the app draws header and footer; toasts, shade entries, badges, clipboard, the area event | [kit.md](kit.md#protocol-18-neoui-proto) |
| 1.9 | 2026-11-17 | apps open each other; notification actions | [kit.md](kit.md#protocol-19-apps-open-each-other) |
| 1.10 | 2026-11-17 | haptic pulses; input reset | [../legacy.md](../legacy.md) |
| 1.11 | 2026-11-18 | a progress bar on a shade entry | [kit.md](kit.md#status-2026-11-17) |
| 1.12 | 2026-11-20 | files between apps by handle; the clipboard's kind | [kit.md](kit.md#protocol-19-apps-open-each-other) (its 1.12 part), [../files-app.md](../files-app.md) FA8 |
| 1.13 | 2026-11-26 | Settings is an app (NEOSET): `SETTINGS_INFO`, `SETTINGS_ACTION`; shell keys writable by NEOSET's secure ID | [settings.md](settings.md#the-settings-app-neoset) |
| 1.14 | 2026-11-26 | `INFO_APPS` (the old apps), `ACTION_OPEN_ENTRY` (SE1d) | settings.md |
| 1.15 | 2026-11-26 | `ACTION_PROFILE`: the sound profiles through the shell's reducer (SE2a) | settings.md |
| 1.16 | 2026-11-26 | `INFO_BATTERY_USAGE` (SE3a) | settings.md |
| 1.17 | 2026-11-26 | `INFO_RUNNING`, `ACTION_STOP`, `ACTION_RESET`, `ACTION_CLEAR`, event `ClearData` (SE4a) | settings.md SE4a |
| 1.18 | 2026-11-26 | `NOTIFY` grows (flags, style, channel, group, when, ≤ 3 actions with kinds: button, reply, danger, in place), `NOTIFY_CLEAR`, event `NotifyGone` (only to 1.18 clients); NOTIFY / NOTIFY_CLEAR / BADGE only from the app's own EXE (TP2a) | top-panel.md TP2a |
| 1.19 | 2026-11-26 | services: an `APPS` entry with no screen (`dtsrv` = DTSRV.EXE, datetime DT1) started at boot and kept alive; `OPEN` grows `flags` (slot 3, `OPEN_WAKE` 1: screen on, shade closed; only from a service); a service's card taps and actions all arrive in place; `AppEvent::Alarm` retired (Clock gets `Open { page }` + `arg`) | [services](#services-119) |
| 1.20 | 2026-11-26 | Settings contracts: paged, revisioned `SETTINGS_INFO` kinds 8 `APP_DETAIL`, 9 `BATTERY_CYCLE` (both empty until their producers D4/D5), 13 `JOBS`, 14 `FEATURES`; `SETTINGS_ACTION` 6 confirmed `CLEAR` and 7 `MEASURE_APP` (nonces, tickets); `OWNER_REPORT` = 42 (owner work); `ENTRY_THUMB` = 43; events 27 `SettingsInfo`, 29 `OwnerWork`, 28 with a ticket (`ClearTicket`), only to 1.20 clients. Kinds 1–6 and the 1.17 event 28 are byte-identical | [Settings snapshots](#settings-snapshots-owner-reports-and-panel-policy-120-121-reserved) |

## Opcodes (app → shell)

| # | Opcode | Since | State |
|---|---|---|---|
| 1 | `GEOMETRY` | 1.0 | built |
| 2 | `SURFACE` | 1.0 | built |
| 3 | `DAMAGE` | 1.0 | built |
| 4 | `NEXT_EVENT` | 1.0 | built |
| 5 | `KEYBOARD` | 1.0 (modes 1.3, pads 1.5) | built |
| 6 | `NAV` | 1.0 | kept for LEGACY.EXE only |
| 7 | `POWER` | 1.0 | built |
| 8 / 9 / 10 | `SETTING_GET` / `SETTING_SET` / `SETTING_WATCH` | 1.1 | built |
| 11 / 12 | `TITLE` / `TOOLBAR` | 1.4 | **retired** in 1.8 (`KErrNotSupported`) |
| 13 | `ENTRY` | 1.6 | built |
| 14 | `FRONT` | 1.6 | built |
| 15 | `PAGE` | 1.7 | built (reduced in 1.8) |
| 16 | `QUERY` | 1.7 | built |
| 17 | `NOTE` | 1.8 | built |
| 18 | `NOTIFY` | 1.8 (actions 1.9, progress 1.11, card fields 1.18) | built; 1.18: progress 255 = none when the 1.18 fields follow; 24 per app (the oldest goes) |
| 19 | `BADGE` | 1.8 | built |
| 20 / 21 | `CLIP_SET` / `CLIP_GET` | 1.8 (kind 1.12) | built |
| 22 / 23 / 24 | `OPEN` / `ARG` / `DONE` | 1.9 (flags 1.19) | built |
| 25 | `HAPTIC` | 1.10 | built |
| 26 / 27 / 28 / 29 | `OPEN_FILE` / `ARG_FILE` / `DONE_FILE` / `RESULT_FILE` | 1.12 | built |
| 30 | `CLIP_KIND` | 1.12 | built |
| 31 | `BLOB` | — | **reserved:** [top-panel.md](top-panel.md) (moved out of TP2a: no producer yet) |
| 32 | `NOTIFY_CLEAR` | 1.18 | built: every card of the caller |
| 33 | `MEDIA` | — | **reserved:** TP3 |
| 34 | `CHANNEL` | — | **reserved:** TP4, 1.21 (constant in `ipc.rs`; [policy](#tp4-policy-reserved-121)) |
| 35 | `REPLY_TEXT` | — | **reserved:** TP4, 1.21 (constant in `ipc.rs`) |
| 36 | `ACTIVITY` | — | **reserved:** TP6 |
| 37 | `TILE` | — | **reserved:** TP7, 1.21 (constant in `ipc.rs`; [tiles](#tp7-tiles-reserved-121)) |
| 38 / 39 | `REGISTER` / `UNREGISTER` | — | **reserved:** [../store.md](../store.md) ST4 (store.md said "1.12", which Files FA8 took) |
| 40 | `SETTINGS_INFO` | 1.13 (paged kinds 1.20) | built (neoui#38): [settings.md](settings.md#the-settings-app-neoset) SE0 (`[kind, cursor, Des8 out]`: a bounded snapshot only the shell has; kinds 1 battery history, 2 Wi-Fi IP/portal, 3 clock sync, 4 old apps (1.14), 5 battery usage (1.16), 6 running apps (1.17, Settings only)). 1.20: kinds 7–15 are paged ([below](#paging)) |
| 41 | `SETTINGS_ACTION` | 1.13 | built (neoui#38): settings.md SE0 (`[kind, Des8 request]`: 1 sign in to the current network, 2 open an old app (1.14), 3 sound profile (1.15), 4 stop an app, 5 reset (0 network, 1 settings), 6 clear an app's data (1.17; confirmed form 1.20), 7 measure an app (1.20); 8–14 reserved ([below](#requested-settings-actions))) |
| 42 | `OWNER_REPORT` | 1.20 | built: [owner work](#owner-work) |
| 43 | `ENTRY_THUMB` | 1.20 | built: [thumbnails](#entry_thumb) |
| 44 | — | — | next free |

## AppEvent kinds (shell → app)

| Kind | Event | Since | State |
|---|---|---|---|
| 1 / 2 | `Input(Touch)` / `Input(Key)` | 1.0 | built |
| 3 | `Quit` | 1.0 | built |
| 4 | `Back` | 1.0 | built |
| 5 | `Options` | 1.0 | kept for LEGACY.EXE only |
| 6 | `Visible(bool)` | 1.0 | built; TP1 also sends `Visible(false)` when the screen goes off |
| 7 | `Settings { seq }` | 1.1 | built |
| 8 | `Alarm { id }` | 1.2 | **retired** in 1.19 (DTSRV opens Clock on its ring page instead); the number stays taken |
| 9 | `Keyboard { h }` | 1.3 | built |
| 10 | `Page { page }` | 1.4 | built |
| 11 | `Action` | 1.4 | **retired** |
| 12 | `Entry { id }` | 1.6 | built |
| 13 / 14 / 15 | `Primary` / `Cancel` / `Option { i }` | 1.7 | **retired** in 1.8 |
| 16 | `Answer { i }` | 1.7 | built |
| 17 | `NoteAction` | 1.8 | built |
| 18 | `Area { h }` | 1.8 | built |
| 19 | `Open { page }` | 1.9 | built |
| 20 | `Notified { id, action }` | 1.9 | built: 0 = the card, `i + 1` = its action `i` |
| 21 | `InputReset` | 1.10 | built |
| 22 | `NotifyGone { id, why }` | 1.18 | built: why 0 swiped, 1 cleared all; 2 channel off (TP4), 3 expired (later); only to a running app |
| 23 | `Media { cmd, arg }` | — | **reserved:** TP3 (PLAY 1, PAUSE 2, NEXT 3, PREV 4, SEEK 5 = arg ms, SHUFFLE 6, REPEAT 7) |
| 24 | `NotifyReply { id }` | — | **reserved:** TP4, 1.21 (`[24, card_id]`; the text through `REPLY_TEXT`) |
| 25 | `ActivityTap { id, i }` | — | **reserved:** TP6 (0 = the island, 1.. = a button) |
| 26 | `Tile { id, hold }` | — | **reserved:** TP7, 1.21 (`[26, local_id, hold]`, hold 0 tap, 1 hold) |
| 27 | `SettingsInfo { kind, rev }` | 1.20 | built: `[27, kind, rev, 0]`, to the Settings session that read that paged kind ([below](#paging)) |
| 28 | `ClearData` / `ClearTicket { ticket }` | 1.17 / 1.20 | built: `[28, 0, 0, 0]` is the 1.17 event (Settings → Apps → an app → Clear data; the app deletes its own data and quits, SE4a). `[28, ticket, 0, 0]`, ticket nonzero, is 1.20's acknowledged clear, only to a registered 1.20 owner ([owner work](#owner-work)) |
| 29 | `OwnerWork { ticket }` | 1.20 | built: `[29, ticket, 0, 0]`, to a registered owner: claim a measurement |
| 30 | — | — | next free |

## Services (1.19)

A **service** is an app with no screen: an `APPS` entry with `service: true` (`neoui_proto::apps`). The first is
`dtsrv` (DTSRV.EXE 0xE0008003, NeoSymbian/datetime, [../datetime.md](../datetime.md)). It owns the alarms, timers,
events and to-dos and rings them.
- **Start:** the shell starts it hidden at boot, like a [`RESIDENT`] app, and starts it again when it exits. It is never
  closed for room, never the screen, and never listed in the Apps menu or in Settings → Apps.
- **Connects** like any app (`connect`, then `SETTING_GET` / `SETTING_SET` / `SETTING_WATCH`, `NEXT_EVENT`). It never
  sends `SURFACE`, `GEOMETRY` or `DAMAGE`. `FRONT` from a service answers `KErrNotSupported`.
- **`OPEN` with flags:** `[0] key  [1] page  [2] arg  [3] flags` (int; 0 when an older client leaves it out).
  `OPEN_WAKE` (1) turns the screen on, as an incoming call does, and closes the shade. The opened app's Back at its
  root goes Home: `opened_by` is none, because a service has no screen to return to. The flags count only from a
  service; an app's flags are ignored.
- **Cards** (`NOTIFY`, `NOTIFY_CLEAR`, `BADGE`, the 1.18 SID check by `apps::sid("dtsrv")`): a tap on a service's
  card (action 0), and every action on it, arrive as `Notified { id, action }`, delivered in place. They never bring
  up a screen. The service decides what to open (DTSRV: `OPEN clock` on the alarm's page).
- **Settings keys:** a service writes the keys it owns or shares (`Owner::Apps(&["clock", "dtsrv"])` for
  `clock.alarms` and `clock.timer`, which DTSRV imports once and then deletes). It also writes `dtsrv.*` (`dtsrv.next`:
  the next alarm and the next event, which the shell shows in the home widget and the agenda card).

## Settings snapshots, owner reports and panel policy (1.20; 1.21 reserved)

**1.20** (built, neoui `crates/neoui-proto/src/settings_app/{wire,jobs}.rs`, SYSSTART `symbian/src/settings_info.rs`,
neoapp `symbian/neoapp/src/settings_info.rs`) brings revisioned Settings snapshots and acknowledged owner work.
**1.21** will activate the reserved TP4 and TP7 interfaces. A number may be reserved before its producer ships; the
shell advertises a feature (INFO 14) only when it can answer it. 1.19 services, `OPEN_WAKE` and all page IDs keep
their meanings; DTSRV and the 1.19 phone and files apps keep working against a 1.20 shell.

**Encoding.** Integers are little-endian and packed. `b`, `h`, `w`, `q`, `i`, `t` are `u8`, `u16`, `u32`, `u64`,
`i32`, `i64`. `sN` is a length byte and at most `N` bytes of valid UTF-8 (encoders cut on a character boundary). `key`
is an `s16` holding a key of the app catalogue (`neoui_proto::apps`). `app` is `0:b, key` for a native app or
`1:b, entry_id:w` for an old app. `optional-app` is `present:b`, then `app` when present. A Boolean is 0 or 1. UTC
times are Unix seconds. Reserved bits and bytes are zero. A decoder refuses a truncated field, an impossible count, a
duplicate identity, an invalid enum, a reserved bit, trailing bytes or an overflow before anything changes.

| Minor | Interface | Slots or event words | State |
|---|---|---|---|
| 1.20 | `SETTINGS_INFO=40`, new kinds | `[kind, first_record, Des8 out, expected_rev]`. Kinds 1–6 keep their request and answer | built: 8, 9, 13, 14; 7, 10, 11, 12, 15 reserved (`KErrNotSupported`) |
| 1.20 | `SETTINGS_ACTION=41` | `[subkind, DesC8 request, 0, 0]`. The older subkinds keep their completions | built: 6 confirmed `CLEAR`, 7 `MEASURE_APP`; 8–14 reserved |
| 1.20 | `OWNER_REPORT=42` | `[mode, ticket, descriptor, 0]`: 0 register, 1 claim, 2 finish | built |
| 1.20 | `ENTRY_THUMB=43` | `[entry_id, Des8 out, expected_app_detail_rev, 0]`, Settings only | built |
| 1.20 | `SettingsInfo`, event 27 | `[27, kind, rev, 0]`: a hint to the Settings session that read that kind | built |
| 1.20 | `OwnerWork`, event 29 | `[29, ticket, 0, 0]`: wakes a registered owner to claim a measurement | built |
| 1.20 | `ClearData`, event 28 | `[28, 0, 0, 0]` stays the 1.17 event; `[28, ticket, 0, 0]` (`ClearTicket`, nonzero ticket) wakes a registered owner to claim a confirmed clear | built |
| 1.21 | `CHANNEL=34` | `[DesC8 declaration, 0, 0, 0]`, own publisher only | reserved |
| 1.21 | `REPLY_TEXT=35`, `NotifyReply`, event 24 | `[card_id, Des8 out, 0, 0]` takes the reply text; event `[24, card_id, 0, 0]` tells the owner it is ready | reserved |
| 1.21 | `TILE=37`, `Tile`, event 26 | `[DesC8 offer, 0, 0, 0]`; event `[26, local_id, hold, 0]`, hold 0 tap, 1 hold | reserved |
| — | TP2/3/6, Store | 31 `BLOB`, 33 `MEDIA`/event 23, 36 `ACTIVITY`/event 25, 38/39 `REGISTER`/`UNREGISTER` | reserved. 32 `NOTIFY_CLEAR` is built; event 8 stays retired. Next free: opcode 44, event 30 |

**Never to an older client.** The shell drops an event a client can't decode (`AppEvent::needs_minor`: 20 for 27, 29
and the ticketed 28; 18 for `NotifyGone`) before it queues it, so a 1.19 app never sees one. Owner wakes and hints go
only to the authenticated session they are for: the shell checks the recipient's session when it delivers. 1.20's
event words are exact: reserved words are 0, a revision is never 0, a ticket is `1..=i32::MAX`, and `[28, 0, 0, 0]`
is the only 1.17 clear; anything else is no event.

**A connection is its own process's.** Since the 1.20 fixes a new session is bound to its app at its first message, by
the kernel's word twice: the process that sent it is the one SYSSTART started for the app (e32 `Process::id` against
`Message::client_process_id`, e32-rs `7d6ab96`), and its secure ID fits the app's EXE (`apps::sid_fits`; the legacy
bridge by its shared 0xE0002006). Two hidden starts at once (an owner's cold start and an `OPEN_FILE`) can't swap
sessions, files or settings, and the kit and the bridge, which share a SID, can't take each other's session (so a
`NOTIFY` or `CHANNEL` is never put down to the wrong one). A session that fits no started app is refused
(`KErrNotSupported`).

### Paging

A first read sends `first_record = 0, expected_rev = 0`. For the Settings session (its key and SID) it also
subscribes that session to event 27 for the kind, before the snapshot is taken. A page is at most **4,096 bytes**:
a 16-byte header `schema:b = 1, kind:b, count:h, rev:w, first:w, next:w`, then `count` whole records, each
`length:h, payload[length]`. `rev` is never 0. `first` echoes the request. `next = 0xffffffff` ends the traversal;
otherwise `next = first + count` and `count > 0`. An empty collection is one terminal header with count 0. A kind
the shell doesn't build answers `KErrNotSupported` (the 1.19 shell answered `KErrArgument`); a kind 7+ from anyone
but Settings `KErrPermissionDenied`.

A continuation sends the `next` and `rev` it got (the raw `u32` bits in the integer slots). The shell checks the
revision and the cursor before it writes. A changed revision answers `KErrNotReady` (-18) and writes nothing; so do a
cursor past the end or a continuation without a revision (`KErrArgument`). The page holds as many whole records as fit
in the caller's descriptor (at most 4,096 bytes); a descriptor that can't hold the header and the next record answers
`KErrOverflow` and gets nothing. Success completes with the page's length.

The client (`wire::Traversal`, `App::settings_records`) checks the header, the progress, the counts and that every
byte was read (a `count` its bytes can't hold is refused before anything is reserved; a page without records is only
the first page of an empty collection; `first + count` never reaches or passes `0xffffffff`), keeps the pages to
itself, and hands over one generation when the last page came. On `KErrNotReady` it
drops the traversal and starts again at 0, once; a second change returns `KErrNotReady`, and the app keeps its last
complete result marked stale and reads again from its loop. One traversal is capped at 4,096 records and 1 MiB.

Revisions are per kind, start at 1 and change on every change that matters; they skip 0 when they wrap. Queued event
27s coalesce per kind (the newest revision). A new connection starts with no subscriptions and no cursors. Re-read on
resume even without a hint. Kinds 1–6 get **no wrapper**: INFO 4 still answers its old-apps list and total, INFO 5
`[0]` or its 28-byte record, INFO 6 keeps its Settings-only check (golden vectors in
`crates/neoui-proto/tests/settings_wire.rs`).

### New INFO kinds

All are Settings only (its key and SID).

| Kind | One record's payload, in wire order | State |
|---|---|---|
| **7 `CHANNELS`** · TP4 | App record `0:b, owner:key, caption:s48, requested_flags:b, effective_flags:b, requested_lock:b, effective_lock:b, tone:b`. Channel record `1:b, owner:key, channel:b, declared_importance:b, override:b, effective_importance:b, effective_flags:b, effective_lock:b, name:s32, description:s64`. An app record even with no declarations. Flags, lock and importance as in [TP4 policy](#tp4-policy-reserved-121) | reserved (1.21) |
| **8 `APP_DETAIL`** · D4/D8 | `app, caption:s48, exe:s32, version:s64, identity_source:b, sid:w, cap_source:b, caps_lo:w, caps_hi:w, coverage:b, measured_utc:t, clear_scope:w, drive_count:b`, then `drive_count` tuples `drive:b, valid:b, installed:q, data:q, cache:q, logs:q`. Drives 0 = A: to 25 = Z:, unique, at most 26. Validity bits 0–3 go with the four counts; a count whose bit is clear is unknown and 0 on the wire. Data leaves out cache, logs and installed files. `identity_source` 0 unknown, 1 catalogue, 2 deployed image/manifest, 3 verified running component. `cap_source` 0 unknown, 1 deployed E32 header, 2 kernel security info. Coverage 0 unknown, 1 measuring, 2 partial, 3 complete, 4 failed. A zero SID or time is unavailable. A version is never inferred from a board. One record per app | codec built (`wire::AppDetail`); the shell answers an **empty collection** and doesn't advertise it until D4 produces it. Its revision also moves when the legacy bridge's entries change (the thumbnails' catalogue) |
| **9 `BATTERY_CYCLE`** · D5 | Singleton `flags:b, start_pct:b, end_pct:b, reserved:b, start_utc:t, last_utc:t, on_battery_s:q, screen_on_battery_s:q, gap_s:q`. Bits 0 a full charge then discharge was seen, 1 incomplete coverage, 2 checkpoint failure, 3 screen counter valid. Percent 0–100 or 255 unknown. Empty before the first observation. Durations from monotonic intervals; uncertain intervals go into the gaps | codec built (`wire::BatteryCycle`); **empty collection**, not advertised until D5 |
| **10 `VOLUME_STATE`** · D17 | `drive:b, state:b, supported:b, debug_state:b, mount_generation:w, last_error:i`. State 0 unknown, 1 mounted, 2 busy, 3 dismounting, 4 dismounted, 5 exported, 6 remounting, 7 failed. Support bits 0 dismount, 1 remount, 2 export. Debug state 0 unknown, 1 off, 2 on, 3 suspended for export. The acknowledged owner state | reserved |
| **11 `UPDATE_STATUS`** · D18 | Singleton `state:b, valid:b, reserved:h, last_attempt_utc:t, last_success_utc:t, last_error:i, installed_build:s64, available_build:s64`. State 0 no configured service, 1 idle, 2 checking, 3 current, 4 update available, 5 failed. Valid bits 0 attempt, 1 success. A failed check keeps the previous success; a failed read shows "Unknown" | reserved |
| **12 `TILES`** · TP7 | `global_id:h, owner:s16, local_id:b, kind:b, state_flags:b, glyph:h, page:h, order:h, label:s16, subtitle:s24`. An empty owner is the shell. `order = 0xffff`: offered, not placed. Flags bits 0 on, 1 backed/available, 2 wide. The placed order first, then the offers sorted by `(owner, local_id)` | reserved (1.21) |
| **13 `JOBS`** · D4/D7/D17/D18 | `ticket:w, action:b, state:b, reserved:h, subject:optional-app, requested_scope:w, committed_scope:w, result:i, finished_utc:t`. State 0 queued, 1 running, 2 committed, 3 partial, 4 failed, 5 interrupted. `result` 0 on a committed success, a negative error on failure. The unfinished jobs (at most 16), then the latest 32 receipts in the order they finished. A record agrees with
itself: queued and running have no result, committed scope or time; committed has `result = 0` and all that was asked;
failed `result < 0`; partial and interrupted `result ≤ 0`; `committed_scope ⊆ requested_scope` | built (`wire::Job`, `jobs::Jobs::records`) |
| **14 `FEATURES`** · common | Singleton `server_major:b, server_minor:b, reserved:h, info_bits:q, action_bits:q, opcode_bits:q`. Bit `n` is number `n`, for the caller. It says what is implemented; per-app `clear_scope`, volume support and feed state say what is available now. Probe it once per connection | built: 1.20 advertises INFO 1–6, 13, 14; actions 1–7; opcodes 1–10, 13–30, 32, 40–43 (`wire::Features::SHELL`) |
| **15 `ENERGY_SHARES`** · D16 | `category:b, quality:b, basis_points:h, model_version:w, cycle_start_utc:t`. Categories 0 Screen, 1 Mobile network, 2 Phone & Contacts, 3 Browser, 4 System, 5 Wi-Fi, 6 Messages, 7 Clock, 8 Unassigned. Quality 1 calibrated estimate, 2 partial calibrated estimate. One model and cycle per traversal, the residual included, 10,000 basis points in all. Advertised only after the measurement and calibration gate | reserved |

### Requested settings actions

Each new subkind needs `access::caller(key, client_sid) == Caller::Settings` (`KErrPermissionDenied`). Actions 1–6
and their old payloads stay. `nonce` is a nonzero `u64` the client makes and keeps across retries of the same request.
The shell remembers the latest 32 `(caller SID, nonce)` with their exact request (in RAM, not across a restart): the
same request again answers the same ticket, the nonce with another request `KErrAlreadyExists` (-11). A job's
completion is its ticket, `1..=i32::MAX`; NEOSET reads INFO 13 for the outcome (`App::settings_job`).

| Subkind | Request and completion | State |
|---|---|---|
| **3 `PROFILE`**, D6 extension | Tags 0–5 keep their layout. Adds `[6, profile_id, flags, 0]` (keypad/touch feedback, bits 0/1) and `[7, tone_id, 0, 0]` (remove an imported tone 4–15, references replaced through the reducer). Completion 0 after the store changed | reserved (D6) |
| **5 `RESET`**, D19 | Bytes 0 network, 1 settings stay. Byte 2 (`RESET_ERASE_C`) is the recovery-mediated erase: unsupported until the trusted confirmation, recovery handoff and partition-boundary gates pass | byte 2 reserved |
| **6 `CLEAR`**, D4 extension | The bare app key keeps its 1.17 meaning. The confirmed form `0xff:b, 1:b, nonce:q, app, scope:w` (`wire::ClearRequest`) → a ticket. `scope` is nonzero, exactly the scope the confirmation named, and still offered by the app's INFO 8 `clear_scope` (`KErrNotSupported` otherwise: **until D4 produces INFO 8 offers, every confirmed clear answers `KErrNotSupported`**). An old app, a service, the legacy bridge or Settings itself has no owner (`KErrNotSupported`). Never downgraded to the 1.17 clear | built |
| **7 `MEASURE_APP`** | `1:b, nonce:q, app` (`wire::MeasureRequest`) → a ticket for the app. Measurements of the same app while one is unfinished share its ticket. Ordinary enumeration reads cached receipts and starts no app | built |
| **8 `INSTALL_WALLPAPER`** | Slot 1 `1:b, format:b = 1, width:h = 540, height:h = 1080, stride:h = 1620, bytes:w = 1749600`. Slots 2/3 pass an open RFs/RFile holding exactly that tightly packed RGB888, top-down. Validate the length, the dimensions and the product; adopt the handle, stage privately, install atomically, then publish `display.wallpaper`. A ticket | reserved (D7) |
| **9 `EDIT_HOME`** | Empty. Opens the shell's Home editor; 0 once entered. Saved through the editor's own Done/Back | reserved (D10) |
| **10 `VOLUME`** | `1:b, op:b, drive:b, reserved:b = 0, generation:w, nonce:q`. Ops 0 dismount, 1 remount, 2 export, 3 end export/remount. E: only (`drive = 4`); recheck the generation and busy state, confirm in SYSSTART, a ticket | reserved (D17) |
| **11 `CHECK_UPDATE`** | `1:b, nonce:q`. Checks authenticated release metadata for the deployed board/build. A ticket, or `KErrNotSupported` without a configured verifier/feed. No install | reserved (D18) |
| **12 `EDIT_TILES`**, 1.21 | Empty. Opens the control-centre editor; 0 once entered; Done commits the whole validated order | reserved |
| **13 `OPEN_HISTORY`**, 1.21 | Empty. Opens the shell's bounded 24-hour notification history once built. Search indexes the action's title only | reserved |
| **14 `LOCK_DIALOG`**, TP9 | `1:b, mode:b`, 0 enrol, 1 change, 2 remove. Launches SYSSTART's trusted dialog; digits, verification and backoff stay there | reserved |

`clear_scope` bits (`wire::scope`): **0** owner preferences approved for clearing, **1** cache, **2** owner logs, **3**
Browser history/cookies/site storage, **4** Phone call log, **5** Messages SMS except blocked senders, **6** Clock
alarms/timers/stopwatch/world clocks, **7** Calendar events/to-dos, **8** Files recent/favourites/index metadata;
bits 9–31 reserved. An owner may offer a subset. INFO 8 and the confirmation use the same mask. Public
downloads/documents, contacts, trash contents and imported birthdays have no implicit bit.

### Owner work

`OWNER_REPORT` (`App::register_owner`, `App::claim_owner_work`, `App::finish_owner_work`; the state machine is
`neoui_proto::settings_app::jobs`):
- **Mode 0, register:** `[0, 0, DesC8, 0]` with `1:b, capabilities:b` (bit 0 measure, bit 1 confirmed clear; at
  least one, no other) → 0. Only from a 1.20 client whose kernel SID is its catalogue SID (`apps::sid`); the kit and
  the legacy bridge are refused (they share SID 0xE0002006 until their UIDs are separated). A new registration replaces
  the app's last one: what it was woken for is woken again (on this session, with the capability), and work another
  session of it claimed is **interrupted**. Register again after every connect.
- **Mode 1, claim:** `[1, ticket, Des8 out, 0]` → the length of `1:b, work:b, subject:app, scope:w` (work 0 measure,
  1 clear; `wire::OwnerWork`). The reply is copied to the owner first and only then is the job taken and saved; a
  buffer too short answers `KErrOverflow`, a claim that doesn't save answers its error (the job stays queued, the
  owner does nothing). Claiming again on the same session answers the same work.
- **Mode 2, finish:** `[2, ticket, DesC8, 0]` with `1:b, state:b, committed_scope:w, result:i, coverage:b,
  measured_utc:t, version:s64, drive_count:b, drive_tuple*` (INFO 8's tuple; `wire::OwnerReport`) → 0 once the
  receipt is saved. States 2–5 only. Committed: `result = 0` and, for a clear, `committed_scope` = what was asked.
  Failed: `result < 0`. Partial, interrupted: `result ≤ 0`. `committed_scope` is never more than was asked. The
  owner needs the capability it has **now** (registered again without it: `KErrPermissionDenied`). The same report
  again answers 0 (and retries a save still due), after a restart too: the table keeps a fingerprint of each accepted
  report (`jobs::fingerprint`, FNV-1a 64; `jobs.dat` version 2). The first build's table (version 1, no
  fingerprints) is still read: its receipts and next ticket stay, its unfinished jobs are interrupted, and it is saved
  as version 2. A different one on a finished ticket answers `KErrAlreadyExists`. The owner
  can't name its own SID, capabilities or another app: the shell knows those.

Claim and finish check the owner's key, its kernel SID, its current session, its declared capability and the pending
ticket (`KErrPermissionDenied`; `KErrNotFound` for a ticket that isn't pending; `KErrArgument` for a finish before the
claim). **A wake alone authorises nothing:** the owner deletes only after its claim answered. The flow:
1. Settings asks (6 or 7); the job is queued and the table saved **before** any wake. A save writes
   `C:\private\e0002001\jobs.tmp`, flushes and closes it, then replaces `jobs.dat` with it in one file-server
   operation, so a failed save leaves the last table whole. **A change a request makes stands only once saved:** a
   failed save puts the table back and the request answers the error, with no ticket (and no nonce remembered), no
   claim, no acknowledged report. INFO 13 shows the table as last saved. A change nobody asked for (an owner gone, a
   job expired) is kept and saved again every second until it is. A table that couldn't be read at boot (other than
   "not there") is read again every second, and until then the 1.20 requests and owner reports answer `KErrNotReady`
   and nothing overwrites it.
2. A registered owner with the capability gets `OwnerWork` / `ClearTicket` on its session. A cold owner is started
   hidden, at most one start a second: the first app of a queued job that isn't running (a running app that never
   registers, a 1.19 one, doesn't hold up the others). It is woken when it registers.
3. A job not claimed within 20 s fails (the millisecond counter wraps: a time before the job's start restarts its
   wait): `KErrNotSupported` when its app never registered (a 1.19 app, or not an
   owner), `KErrTimedOut` (-33) when it was woken.
4. The owner claims (running), works, and finishes; the receipt is saved **before** the 0, and INFO 13's revision
   moves on (event 27) after it.
5. An owner that goes away with a claimed job leaves it **interrupted** (`KErrDied`, -13); one only woken is woken
   again once it registers again. After a restart every unfinished job is **interrupted** (and finishes then, after the receipts already
   there): nothing resumes on its own,
   and an ambiguous partial clear needs a new confirmation before newly created data is deleted. The latest
   measurement report per app is kept in RAM for INFO 8's producer (`Jobs::measured`).

### `ENTRY_THUMB`

Answers the old app's launcher icon in the `ENTRY` icon encoding, `width:h, height:h` and one straight-alpha
`0xAARRGGBB` LE word per pixel, cut down (nearest pixel, aspect kept) to at most 32 × 32: at most 4,100 bytes. Zero
bytes for the generic icon. `KErrNotFound` for an entry the bridge doesn't have; `KErrNotReady` when
`expected_app_detail_rev` isn't 0 and isn't INFO 8's revision now (0 skips the check); `KErrOverflow` for a short
buffer. Cached per entry until the bridge's entries change (which moves INFO 8's revision). A 128 × 128 icon never
goes into an INFO page and isn't loaded for every search hit (`App::entry_thumb`).

### TP4 policy (reserved, 1.21)

`CHANNEL` declaration: `1:b, id:b, default_importance:b, name:s32, description:s64`. Channel 0 is the fallback for
legacy cards; 16 explicit declarations per publisher. Importance 1 Min/Silent, 2 Low, 3 Default, 4 Urgent. Override
byte 0 inherits, 1–4 override the importance, 5 turns the channel off. A repeated declaration updates the publisher's
metadata and keeps the user's override. Messages' IDs: 1 Conversations, 2 Failed to send, 3 Delivery reports, 4
Blocked messages. Trusted system exceptions are classified by authenticated publisher and channel. DTSRV can declare
alarm/timer/reminder channels under `dtsrv`; the Settings caption can say "Clock & Calendar".

`n.<app>` is a typed `Bytes` setting: `1:b, flags:b, lock:b, tone:b, count:b, (channel:b, override:b)*`. Flags bits 0
allow, 1 banners, 2 sound, 3 badge. `lock` 0 inherit, 1 show, 2 hide content, 3 counts only, 4 off. `tone` 255 follows
the active profile, 0–15 picks an available tone. Defaults: allow/banner/sound/badge on, inherit lock, follow profile,
no overrides. Duplicate channel entries are refused; validated on load and on write. The pinned baseline has no
shipping `n.<app>` codec. Registered shell-owned keys (or a validated catalogue-backed namespace rule covering access,
validation, reset and load) are needed: `Caller::Settings` can't write arbitrary `n.*` today.

`notify.dnd: Bool = false`, `notify.dndto: Bytes` (empty or an 8-byte LE UTC expiry), `notify.dndfav: Bool = true`,
`notify.bannert: Int = 5` s (1–30). Global `notify.lock` as in TP8: 0 show, 1 private, 2 off. Per-app settings may
tighten global visibility; the board's "Counts" is the stricter counts-only rendering. The effective policy is computed
once for Settings, badge, shade, banner, sound and lock. Off removes the eligible cards and badges and refuses new
posts; shell-owned captive-portal cards stay. DND silences alerting and keeps eligible shade cards. The alarm,
favourite-call and repeated-call exceptions apply, and at most five alerting posts per minute per app; silent updates
are free. A board's sample "4 s" shows the effective `notify.bannert`.

`REPLY_TEXT` answers at most 480 UTF-8 bytes for the authenticated publisher and the exact active card. One pending
reply per `(owner, card_id)`, gone after 60 s, after a successful copy, a cancel, the card's replacement or removal, or
the owner's death. A short buffer leaves the text there. Reply text never enters a Settings snapshot, the search
index or a log.

### TP7 tiles (reserved, 1.21)

`TILE` offer: `1:b, local_id:b, kind:b, on:b, glyph:h, page:h, label:s16, subtitle:s24`. Local IDs 0–3 per publisher.
Kind 0 withdraw, 1 toggle, 2 action, 3 detail; a withdrawal has zero/empty other fields. Glyph 0 is the publisher's
catalogue glyph; 1 stopwatch, 2 terminal, 3 shuffle, 4 phone, a generic fallback for later ones. A declaration alone
never places a tile. `(authenticated publisher SID, local_id)` maps to a persistent shell-wide 15-bit ID: 1–255 for
built-ins, apps from 256. `shell.tiles` is the ordered LE `u16` words, high bit wide, low 15 bits the ID; duplicates
refused, at most 32 placed, the mapping kept across reboots, and a new publisher never inherits a removed one's place.
The first stop shows the first four backed, placed tiles. `shell.tap` 0 shade, 1 control centre becomes actionable at
TP7; `shell.swipehome` as registered.

**Compatibility and authority (1.21).** Events 24/26 only to clients of minor ≥ 21 with the matching subscription or
opt-in. A missing SID mapping fails closed for new owner operations. INFO 4 and the cached legacy thumbnails can still
come from the shell.

## Older numbering, now void

These designs drew numbers before the table existed. They are void; use the table above.
- `neoui-shell.md` Part 2 (2026-11-09): `NOTIFY = 10`, `NOTIFY_CANCEL = 11`, `AppEvent::Opened` kind 8. Replaced by
  [top-panel.md](top-panel.md).
- The canvas's `api-notify-protocol` (the "proposed 1.9" notifications, live island and tiles): opcodes 18–25 and
  kinds 19–25. They are renumbered above as 31–37 and 22–26; 18 (`NOTIFY`) grows in place.
- The key pads plan: `HAPTIC = 15/19`, `VIEWPORT = 16/20`, `InputReset` kind 19. HAPTIC became 25 and InputReset
  kind 21 in 1.10; VIEWPORT was not needed (`PAGE.full`).
- [../store.md](../store.md) ST4: `REGISTER` as "protocol 1.12". Now opcodes 38/39.
