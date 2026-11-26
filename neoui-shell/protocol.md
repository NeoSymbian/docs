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
| 18 | `NOTIFY` | 1.8 (actions 1.9, progress 1.11) | built; grows in TP2 |
| 19 | `BADGE` | 1.8 | built |
| 20 / 21 | `CLIP_SET` / `CLIP_GET` | 1.8 (kind 1.12) | built |
| 22 / 23 / 24 | `OPEN` / `ARG` / `DONE` | 1.9 | built |
| 25 | `HAPTIC` | 1.10 | built |
| 26 / 27 / 28 / 29 | `OPEN_FILE` / `ARG_FILE` / `DONE_FILE` / `RESULT_FILE` | 1.12 | built |
| 30 | `CLIP_KIND` | 1.12 | built |
| 31 | `BLOB` | — | **reserved:** [top-panel.md](top-panel.md) TP2 |
| 32 | `NOTIFY_CLEAR` | — | **reserved:** TP2 |
| 33 | `MEDIA` | — | **reserved:** TP3 |
| 34 | `CHANNEL` | — | **reserved:** TP4 |
| 35 | `REPLY_TEXT` | — | **reserved:** TP4 |
| 36 | `ACTIVITY` | — | **reserved:** TP6 |
| 37 | `TILE` | — | **reserved:** TP7 |
| 38 / 39 | `REGISTER` / `UNREGISTER` | — | **reserved:** [../store.md](../store.md) ST4 (store.md said "1.12", which Files FA8 took) |
| 40 | `SETTINGS_INFO` | 1.13 | built (neoui#38): [settings.md](settings.md#the-settings-app-neoset) SE0 (`[kind, cursor, Des8 out]`: a bounded, revisioned snapshot only the shell has; kinds 1 battery history, 2 Wi-Fi IP/portal, 3 clock sync, 4 old apps (1.14), 5 battery usage (1.16), 6 running apps (1.17, Settings only); TP4's channels take the next kind) |
| 41 | `SETTINGS_ACTION` | 1.13 | built (neoui#38): settings.md SE0 (`[kind, Des8 request]`: 1 sign in to the current network, 2 open an old app (1.14), 3 sound profile (1.15), 4 stop an app, 5 reset (0 network, 1 settings), 6 clear an app's data (1.17); later share E:) |
| 42 | — | — | next free |

## AppEvent kinds (shell → app)

| Kind | Event | Since | State |
|---|---|---|---|
| 1 / 2 | `Input(Touch)` / `Input(Key)` | 1.0 | built |
| 3 | `Quit` | 1.0 | built |
| 4 | `Back` | 1.0 | built |
| 5 | `Options` | 1.0 | kept for LEGACY.EXE only |
| 6 | `Visible(bool)` | 1.0 | built; TP1 also sends `Visible(false)` when the screen goes off |
| 7 | `Settings { seq }` | 1.1 | built |
| 8 | `Alarm { id }` | 1.2 | built |
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
| 22 | `NotifyGone { id, why }` | — | **reserved:** TP2 (why: 0 swiped, 1 cleared all, 2 channel off, 3 expired) |
| 23 | `Media { cmd, arg }` | — | **reserved:** TP3 (PLAY 1, PAUSE 2, NEXT 3, PREV 4, SEEK 5 = arg ms, SHUFFLE 6, REPEAT 7) |
| 24 | `NotifyReply { id }` | — | **reserved:** TP4 (the text through `REPLY_TEXT`) |
| 25 | `ActivityTap { id, i }` | — | **reserved:** TP6 (0 = the island, 1.. = a button) |
| 26 | `Tile { id, hold }` | — | **reserved:** TP7 |
| 27 | `SettingsInfo { kind, rev }` | — | **reserved:** settings.md (a snapshot of `SETTINGS_INFO` kind changed; not used in SE0) |
| 28 | `ClearData` | 1.17 | built: Settings → Apps → an app → Clear data; the app deletes its own data and quits (SE4a) |
| 29 | — | — | next free |

## Older numbering, now void

These designs drew numbers before the table existed. They are void; use the table above.
- `neoui-shell.md` Part 2 (2026-11-09): `NOTIFY = 10`, `NOTIFY_CANCEL = 11`, `AppEvent::Opened` kind 8. Replaced by
  [top-panel.md](top-panel.md).
- The canvas's `api-notify-protocol` (the "proposed 1.9" notifications, live island and tiles): opcodes 18–25 and
  kinds 19–25. They are renumbered above as 31–37 and 22–26; 18 (`NOTIFY`) grows in place.
- The key pads plan: `HAPTIC = 15/19`, `VIEWPORT = 16/20`, `InputReset` kind 19. HAPTIC became 25 and InputReset
  kind 21 in 1.10; VIEWPORT was not needed (`PAGE.full`).
- [../store.md](../store.md) ST4: `REGISTER` as "protocol 1.12". Now opcodes 38/39.
