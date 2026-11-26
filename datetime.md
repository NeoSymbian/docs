<!-- SPDX-License-Identifier: Apache-2.0 -->
# datetime: Clock + Calendar v2 (NEOCLOCK, NEOCAL, DTSRV)

Written 2026-11-17. This is the proposal for a new repo, `NeoSymbian/datetime`. It ships two apps from one codebase:
- **Clock** (`NEOCLOCK.EXE`), moved out of neoui and redesigned;
- **Calendar** (`NEOCAL.EXE`), new.

They share a resident server, **DTSRV**, that owns every alarm, timer, event and to-do and rings them. **Built
2026-11-26** in [NeoSymbian/datetime](https://github.com/NeoSymbian/datetime) (DT0–DT7 in one go; see
[Status](#status-2026-11-26)).

**The design** is on the canvas's Clock page (https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#page-9cf533b1dc6b) and
Calendar page (https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#page-b458b7e9b909):
- 55 screen boards (`clk2-*`, `cal2-*`, `dt2-*`), published 2026-11-17;
- one interactive prototype per app (`clk2-prototype`, `cal2-prototype`);
- six spec sheets (`dt2-spec-*`).

Each board title carries its tag (As built, Planned DTn or Proposed). The canvas is private.

## Decisions

From the canvas (owner, 2026-11-17, console questions):
- **DT01 Style: Hero + cards.**
  - Every root tab starts with a shared **TimeHero** band, then kit cards and rows.
  - Clock's hero: digits, date, next alarm and next event.
  - Calendar's hero: the month grid, or the week strip on Day.
  - The home clock and agenda widgets use the same parts.
- **DT02 Clock has 3 footer tabs: Clock · Alarms · Timers.**
  - World is merged into the Clock tab: city cards under the hero.
  - Timer and Stopwatch share the Timers tab behind a segmented switch.
  - The header title is the tab name, as built.
- **DT03 Calendar has 4 footer tabs: Month · Week · Day · To-do.**
  - Month is the grid plus the chosen day's agenda.
  - Week and Day are timelines with a now line.
  - The root header is `[Calendar · today · + · ⋮]`.
- **DT04 Two apps plus a server.**
  - `NEOCLOCK` 0xE0008001, `NEOCAL` 0xE0008002 and `DTSRV` 0xE0008003, resident.
  - DTSRV owns the alarm, timer, event and to-do stores, and fires all of them.
  - The shell's `clockwork.rs` loses its alarm code.
- **DT05 Numerals:** the display-digit glyphs (`ui/icons/digits`, the canvas's `ds-digits`) for every big time:
  heroes, alarm cards, timer, stopwatch, event times. Inter tabular for small times.
- **DT06 Entry types:**
  - timed events;
  - all-day and multi-day events;
  - anniversaries and birthdays (birthdays read live from NEOCONT's book);
  - to-dos with a due date and priority.
- **DT07 Links:**
  - the hero shows the next alarm and the next event;
  - reminders ring with the same full-screen Ringing UI as alarms, plus a shade entry;
  - `.ics` opens from Files (FA7) and Messages, and events share as `.ics`;
  - the home ClockWidget and AgendaCard are redrawn.
- **DT08 The board set:**
  - the 5 old boards are removed;
  - everything is drawn in Gestures, plus a Buttons row per app, the prototypes and the spec sheets.

**DT09 DTSRV is a headless app** (owner, 2026-11-26, console). Since protocol 1.18 only an app's own EXE may post
shade cards, so "DTSRV sends OPEN + NOTIFY" needed a shell change. The owner chose protocol **1.19 services**
(an `APPS` entry with no screen: started at boot, kept alive, OPEN with `OPEN_WAKE`, card taps delivered in place)
over relaying the rings through the shell. Details: [neoui-shell/protocol.md](neoui-shell/protocol.md#services-119).

## The apps before (2026-11-17)

**Clock, NEOCLOCK.EXE 0xE0002002**, in `neoui/symbian/apps/clock`, on the kit since 2026-11-17:
- **Tabs:** Clock (digital or analog face, seconds, date, next alarm), Alarms, World, Timer and Stopwatch.
- **Sub-views:**
  - alarm editor (time stepper, day chips, label presets);
  - city picker;
  - Set time (date, time, zone; needs WriteDeviceData);
  - Settings (face, seconds, date, 24 h);
  - Ringing (Snooze 5 min, Dismiss).
- **Model:** `neoui-proto/src/clock/` (`alarm`, `timer`, `stopwatch`, `world`, `tz`, `local`, `datetime`, `face`,
  `analog`, `saved`, `wire`), with host tests. There are no app snapshots.
- **State:** `clock.*` settings keys, including the byte blobs `clock.alarms`, `clock.cities`, `clock.timer` and
  `clock.stopwatch`.
- **Alarms:** `neoui/symbian/src/clockwork.rs` checks `clock.alarms` once a minute. When one is due, it calls
  `ui.show("clock")` and posts `AppEvent::Alarm` (IPC kind 8). The app then opens Ringing. Alarms ring only while the
  phone is on, and there is no shade entry.

**Calendar** is not an app:
- `neoui/ui/screens/calendar.slint` is a hard-coded November 2026 month and day, with mock events in `ui/data.slint`.
- The home `AgendaCard` shows the same mock events.

## The repo

The layout of `phone` (several EXEs, shared code) and `files` (host and device workspaces). The UID block is
**0xE0008xxx** (the next free one).

```
datetime/
  crates/
    datetime-core/   Apache, no_std: alarm, timer, stopwatch, world (moved from neoui-proto/src/clock),
                     next-due planning, snooze; the dt-ipc 1.0 codec
    pim-ics/         Apache, no_std + alloc: reuses files' neo-format-pim (ical: VEVENT/VTODO/VALARM/
                     VTIMEZONE parse and write, unknown properties kept, built in FA7) and adds what the
                     calendar needs on top (RRULE expansion lives in calendar-core)
    calendar-core/   Apache: events, recurrence (an RRULE subset: daily, weekly by day, monthly by date,
                     yearly, COUNT/UNTIL, EXDATE), to-dos, the agenda and range queries, birthdays
    clock-ui/        GPL (Slint): Clock screens, host snapshots snapshots/clk2-*.png
    calendar-ui/     GPL (Slint): Calendar screens, host snapshots snapshots/cal2-*.png
  ui-shared/         @dt-shared: TimeHero, WeekStrip, MonthGrid, EventRow, TimeCard, ProgressRing, Ringing
  symbian/
    common/          device glue: the DTSRV client, settings, OPEN/NOTIFY helpers
    server/          DTSRV.EXE   0xE0008003  (e32::server)
    clock/           NEOCLOCK.EXE 0xE0008001
    calendar/        NEOCAL.EXE   0xE0008002
    exes.txt
```

**Shared code:**
- `-ui` crates compile `ui-shared` with `neoui_kit::compile_with(…, &[("dt-shared", …)])`, as phone does with
  `@phone-shared`.
- `datetime-core` is pinned by neoui. `tz`, `datetime` and `local` stay in `neoui-proto`, because the shell's status
  bar and `clock.dat` need them.

**Pins:**
- e32, neoui (`neoui-proto`, `neoapp`, `neoui-kit`) and Slint, by git rev. They must match neoui's
  `symbian/Cargo.toml` (the files and phone repos already drift: `e6aa05e` vs `27a90f7`).
- Nightly as in neoui.

**Licences:** Apache for the `*-core` crates, `pim-ics`, DTSRV and its client; GPL-3.0 for everything that links Slint (`-ui`,
`symbian/*`). DTSRV links no Slint, so it is Apache.

**CI:**
- host: `cargo fmt/clippy/test` and the snapshots;
- device: `cargo arm`;
- from US6b, UI taps on QEMU virt through the tabs (neoui's Syborg job, which cloned files this way, was retired in US5).

## How it works

**DTSRV** (`symbian/server`, Apache-2.0) is a Rust CServer2 (`e32::server`, name `DtSrv`) and a **service** of the UI
server (protocol 1.19): the shell starts it at boot (`RESIDENT`, first) and keeps it running. It links no Slint, so
it talks to the UI server through a thin client on `neoui-proto` (`ui.rs`), not `neoapp`.
- **Stores** in `C:\private\e0008003\`, DTSRV the only writer, each saved as `x.new` + replace:
  - `alarms.dat`, `timers.dat` (`datetime-core` blobs), `rings.dat` (each alarm's last rung occurrence, the rings
    not yet acted on, the snoozes left: no double ring after a restart or a clock set back);
  - `calendar.ics` (one VCALENDAR per calendar, `X-NEO-COLOR`, `X-WR-CALNAME`) and `todo.ics`;
  - only "not found" means "no file": any other read error keeps the store unread (writes answer KErrNotReady)
    and it is read again every 10 s.
  - First run: `clock.alarms` / `clock.timer` (the old Clock's settings) are imported, then emptied.
- **Planning:** one plan over alarms (local minute of week), the timer and the reminders of the next two days
  (`datetime-core::plan`), against UTC and the local zone (the `time.zone` city's `tz::Rule` with automatic zone
  off, else the kernel offset). It sleeps `min(due − now, 60 s)`; `time.*` and `clock.*` changes re-plan at once.
  `shortcut:` a clock jump without a settings change is seen within 60 s (upgrade: an e32 `TIMER_AT` wrapper).
- **Firing:** `OPEN(clock | calendar, page RING, arg ring id, OPEN_WAKE)` (screen on, shade closed) plus DTSRV's
  own card (Snooze / Dismiss, in place; the running timer has an ongoing card with Pause). A card tap reopens the
  page. Ring ids are `(kind << 24) | item` (1 alarm, 2 timer, 3 reminder).
- **`dtsrv.next`:** the next alarm and the next event as a settings blob (`neoui_proto::clock::next`), which the
  shell shows in the home ClockWidget and AgendaCard. There is no shell→DTSRV IPC.
- **dt-ipc 1.0** (`datetime-core::ipc`; large replies return the full length and are asked for again):

  | Op | Name | Op | Name |
  |---|---|---|---|
  | 1 | NEXT | 12 | TODO_PUT |
  | 2 | WATCH (async, mask: alarms 1, timers 2, events 4, todos 8, rings 16) | 13 | TODO_DEL |
  | 3 / 4 / 5 | ALARM_LIST / PUT (id 0 creates) / DEL | 14 | IMPORT_ICS (text ≤ 256 KB) |
  | 6 | TIMER (get, start, pause, resume, reset, add) | 15 | EXPORT_ICS |
  | 7 | RING_ACTION (snooze, dismiss, stop, +1 min) | 16 | CLEAR (mask) |
  | 8 | EVENT_QUERY (days, hidden calendars) | 17 | WATCH_CANCEL |
  | 9 / 10 | EVENT_PUT / EVENT_DEL (this or all) | 18 / 19 | CALENDARS / CALENDAR_PUT |
  | 11 | TODO_LIST | 20 / 21 | RING_INFO / EVENT_GET |
- **Birthdays:** read from NEOCONT's book (`contacts.dat`, NCT2 since phone#birthdays) through phone's `contacts`
  crate, again on every `contacts.rev` change, never copied.

**The apps** keep no alarm or event state. They read through DTSRV and redraw on `WATCH`. Only the Stopwatch stays
local, because it never rings. The Ringing screen lives in `ui-shared`:
- NEOCLOCK shows it for alarms and timers;
- NEOCAL shows it for reminders ("Ring like an alarm" is on by default).

**The shell** keeps from `clockwork.rs`: the status-bar clock, the summer-time rule and the home widget text. The
widget text now comes from `NEXT`. The shell drops the alarm check (`due()`, `AppEvent::Alarm`).

**Settings keys** (registry changes in neoui, `Owner::App`):
- `clock.24h`, `clock.face`, `clock.seconds`, `clock.date`, `clock.tab`, `clock.cities` and `clock.stopwatch` stay.
- `clock.alarms` and `clock.timer` are imported into DTSRV once, then removed.
- New: `clock.snooze`, `clock.snooze_count`, `clock.sound`, `clock.rise`, `clock.shade_next`.
- New: `calendar.view`, `calendar.week_start`, `calendar.week_numbers`, `calendar.reminder`, `calendar.length`,
  `calendar.ring`, `calendar.birthdays`, `calendar.hidden`.
- The app key stays `clock`, so `APPS` and the settings owner don't change when the UID does. Calendar adds the key
  `calendar` (and replaces the shell mock's menu entry).

**Page links** (protocol 1.7 PAGE / 1.9 OPEN; the full table is on `dt2-spec-map`):
- `clock:/alarms`, `clock:/alarm?id=`, `clock:/timer`, `clock:/stopwatch`, `clock:/ring?id=`;
- `calendar:/day?d=`, `calendar:/event?uid=`, `calendar:/new?d=`, `calendar:/import?path=`, `calendar:/ring?uid=`.

## Platform gaps

| Need | Today | Needs | Where |
|---|---|---|---|
| Alarms with the phone off | none | a PMIC RTC alarm + power-on reason in the kernel (sdm670) | kernel |
| Ring while silent | sound profiles don't exist yet | profiles (settings S-boards) and an audio path for tones | neoui, telephony |
| Alarm sounds | a beep | the audio service of files FA9 (MP3/AAC), or built-in tones first | telephony, files |
| OPEN a page with arguments from a server | done: protocol 1.19 services (DT09) | — | neoui |
| .ics in Messages | SMS only | MMS (modem C10) | neohw |
| Share by Bluetooth | none | hardware/bluetooth.md B5 | neohw |

## Phases

Each phase ends with host tests and board snapshots in the datetime repo, then the Pixel (and, from US6b, the UI taps on QEMU virt).

| Phase | Work | Repos | Gate | Boards |
|---|---|---|---|---|
| **DT0** move | Create `NeoSymbian/datetime`; NEOCLOCK → `symbian/clock` + `crates/clock-ui`, model → `datetime-core`; UID 0xE0008001. neoui drops `symbian/apps/clock` and its exes line, and clones datetime in `syborg.yml`. No behaviour change. | datetime, neoui, docs | today's Clock taps pass on Syborg from the new repo | — |
| **DT1** DTSRV for alarms and timers | The server, `alarms.dat`/`timers.dat`, one-time import of `clock.alarms`/`clock.timer`, `RTimer::At`, OPEN + NOTIFY on fire, snooze; clockwork's alarm code removed; NEXT for the home widget | datetime, neoui | an alarm rings with Clock closed and after a reboot; a time-zone change moves it | `dt2-ring-alarm`, `dt2-ring-timer`, `dt2-shade` |
| **DT2** Clock v2 | 3 tabs, TimeHero, world cards, alarm cards with digit glyphs, free-text label, sound and snooze settings, Timer/Stopwatch switch, Buttons mode | datetime | every `clk2-*` board matches its snapshot; Back order of `dt2-spec-map` | `clk2-*` |
| **DT3** the calendar model | `pim-ics` (round trip, unknown properties kept), `calendar-core` (RRULE subset, ranges, to-dos), DTSRV event and to-do stores | datetime | fuzzed parser; recurrence tests across DST changes | — |
| **DT4** NEOCAL views | Month, Week, Day, To-do, event view and edit, sheets, Calendars, Settings, Search; delete the shell mock | datetime, neoui | every `cal2-*` view board matches its snapshot; 1 000 events scroll smoothly | `cal2-month*`, `cal2-week*`, `cal2-day*`, `cal2-todo*`, `cal2-event-*`, `cal2-*-sheet`, `cal2-search`, `cal2-settings` |
| **DT5** reminders | Event reminders through DTSRV, Ringing for events, shade entries with Snooze | datetime | a reminder rings with both apps closed | `dt2-ring-event`, `cal2-reminder-sheet` |
| **DT6** links | Birthdays from NEOCONT, anniversaries, `.ics` import from Files/Messages and export/share, OPEN to NEOPHONE/NEOMSG/NEOCONT | datetime, files, phone | `concert.ics` from the Files board imports; a birthday shows the day it's added in Contacts | `cal2-birthday-view`, `cal2-anniversary-edit`, `cal2-ics-import`, `cal2-share` |
| **DT7** home widgets | ClockWidget = TimeHero (next alarm + next event), AgendaCard = EventRow, both from NEXT | neoui | the home boards match | `sh-home-clock-24h`, `sh-home-clock-12h` |

**Order:**
- DT0 → DT1 → DT2 is the Clock line. DT3 → DT4 → DT5 is the Calendar line; it can start after DT1.
- DT6 and DT7 come last.
- Proposed boards (`clk2-world-edit` reorder, `clk2-timer-multi`, `cal2-week-list`, Holidays calendar, Bluetooth
  share) wait for the owner's go.

## Status (2026-11-26)

Built in one go on 2026-11-26, by parallel agents with a Codex review: datetime#1, neoui#59 (protocol 1.19),
phone#11 (birthdays), files#18 (Add to Calendar), this doc.

| Phase | State |
|---|---|
| DT0 move | done: NEOCLOCK is datetime's (0xE0008001); neoui dropped `apps/clock` and the clock model |
| DT1 DTSRV | done: service (1.19), stores, plan, OPEN WAKE + cards, snooze, import of `clock.alarms`/`clock.timer`, `dtsrv.next` |
| DT2 Clock v2 | done: every non-Proposed `clk2-*` board (23 snapshots), Ringing with a NeoAudio tone |
| DT3 model | done: `pim-ics`, `calendar-core` (RRULE subset with DST, fuzzed), DTSRV's event and to-do stores |
| DT4 NEOCAL | done: every non-Proposed `cal2-*` board (27 snapshots); the shell mock is gone |
| DT5 reminders | done: Calendar's Ringing (`calendar.ring`) and cards, snooze |
| DT6 links | done: birthdays from NEOCONT (NCT2), anniversaries, `.ics` import from Files, share/export |
| DT7 home widgets | done: ClockWidget's next alarm and AgendaCard from `dtsrv.next` |

**Pixel (RAM boots, 2026-11-26, `ROFS=ramdisk EMMC_C=1`, two images):**
- **UI and connectivity:** UI, LTE and Wi-Fi up; DTSRV starts first and imports.
- **Alarm:**
  - a 21:19 alarm rang over Files: screen on, Clock's Ringing, tone on the speaker;
  - Snooze ×2 and Dismiss by hand;
  - a tap on DTSRV's shade card brought Ringing back.
- **Calendar:**
  - Files → Add to Calendar → NEOCAL's import → `dtsrv: import 1 0`;
  - the event's 1-minute reminder rang in Calendar.
- **After a second boot:** the alarm, the events and a running 10-min timer came back, and the timer rang on time.
- **Birthdays:** set in NEOCONT's editor, the birthday showed at once in Calendar's agenda.
- **Found and fixed:** two rings at the same minute (the alarm and the reminder): ending one went Home with the other
  still ringing. DTSRV now reopens the other's Ringing page.

**Open:**
- **Rings and alarms:**
  - a ring screen hides the shade; Back = Snooze;
  - reminder snoozes are in memory only (lost on restart);
  - the 60 s re-plan for a clock jump without a settings change (upgrade: an e32 `TIMER_AT` wrapper);
  - power-off alarms (PMIC RTC).
- **Clock:**
  - one timer;
  - three NeoAudio tones;
  - no Vibrate per alarm;
  - the time sheet has no ±5 min chips.
- **Calendar:**
  - forms don't ask before discarding;
  - Phone's pages can't open on a contact id (the birthday view opens the dialer).
- **Shade:** DTSRV's cards are headed "Clock & Calendar", not per app.

## System time (shell, built 2026-11-13)

The shell owns the clock, the Date & time settings page, network time and the time zones (`time.*` keys);
DTSRV and the apps read them. Moved here from `neoui-shell.md` Parts 5 and 6 on 2026-11-21. The status bar and the
shade's header are in [neoui-shell/top-panel.md](neoui-shell/top-panel.md).

**Settings → Date & time** (view `datetime`; the date and zone helpers are in `neoui-proto::clock::datetime`, which
is host-tested):

| Row | Key | Notes |
|---|---|---|
| Automatic time | `time.auto` (on) | NITZ from MODEMD's status, else the HTTP `Date:` of the internet check |
| Automatic time zone | `time.auto_zone` (on) | NITZ's zone (quarter hours, daylight saving included) |
| Time zone | `time.zone` ("") | A World catalogue city (Part 6). A tap steps to the next city. The offset in force stays in the kernel and `clock.dat` |
| 24-hour time | `clock.24h` | Moved here from Display |
| Seconds in the status bar | `status.seconds` (off) | |
| Date in the shade | `shade.date` (on) | |
| Date format | `time.date_format` 0..=3 | "Friday, 13 November", "13.11.2026", "2026-11-13", "11/13/2026" |

**Network time** (`symbian/src/netclock.rs`):
- A new NITZ value, or a fresh HTTP Date, corrects the clock when it is more than 2 s off or the zone differs
  (`datetime::correction`). `clock::Keeper` saves it.
- "Last set" shows the source and the time.
- **Phone, 2026-11-13:** the clock was booted wrong (00:00). Ucom's NITZ (UTC+4) set it 21 s after boot, matching the
  Mac to within seconds.

**Shortcuts:**
- the NITZ age inside MODEMD's status is not counted;
- the Wi-Fi switch stops scanning and rejoining but leaves the radio up.


### Time zones with daylight saving (Part 6, 2026-11-13)

**Rules:** each World catalogue city (`neoui-proto::clock::world`, 87 cities west to east) carries its zone's rule
as a POSIX `TZ` string from IANA tzdata, e.g. Berlin `CET-1CEST,M3.5.0,M10.5.0/3`.
- `clock::tz::Rule` parses and evaluates the string: the standard offset, the daylight saving offset, and the
  `Mm.w.d`, `Jn` and `n` dates with POSIX's extended times (Israel's `/26`, Greenland's `/-1`).
- Southern zones, whose summer spans the new year, and Lord Howe's 30-minute change are covered.
- Host tests check the 2026 changes for Berlin, London, New York, Sydney, Lord Howe and Jerusalem.

**The zone in force:**
- `time.zone` (Owner::Shell) names the city. With "Automatic time zone" off, the shell applies the city's offset
  once a minute (`symbian/src/clockwork.rs`), so the clock enters and leaves summer time by itself. `clock::Keeper`
  saves the offset as before.
- With automatic zone on, NITZ sets the offset (its zone includes daylight saving), and the city rule stays out of
  the way.
- **Time zone row:** shows "UTC+02:00 · Berlin (summer time)": the chosen city when its rule agrees with the clock,
  else the first city on that offset.
- **World page:** the catalogue lists each city's offset in force now.

**Shortcuts:**
- today's rules only, no history (tzdata 2025): the table needs an update when a country changes its rules;
- the Time zone row steps through the cities one tap at a time; there is no picker yet.

## Not doing

- **Sync (CalDAV, Exchange):** not planned. `.ics` import/export only; a sync service would be its own repo.
- **Other calendar systems (lunar, Armenian church calendar):** only as an imported read-only `.ics`.
- **Copying the 2010 Clock or Calendar:** the S60 apps (EPL) are prior art for wording only; no code is copied.
