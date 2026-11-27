<!-- SPDX-License-Identifier: Apache-2.0 -->
# System time: the clock, network time and time zones

Part of [neoui shell](README.md) · Status: done · Updated: 2026-11-27


The shell owns the clock, the Date & time settings page, network time and the time zones (`time.*` keys);
DTSRV and the apps read them. Moved into [../apps/datetime.md](../apps/datetime.md) from the hub's Parts 5 and 6 on
2026-11-21, and here on 2026-11-27. The status bar and the shade's header are in [top-panel.md](top-panel.md).

**Settings → Date & time** (view `datetime`; the date and zone helpers are in `neoui-proto::clock::datetime`, which
is host-tested):

| Row | Key | Notes |
|---|---|---|
| Automatic time | `time.auto` (on) | NITZ from MODEMD's status, else the HTTP `Date:` of the internet check |
| Automatic time zone | `time.auto_zone` (on) | NITZ's zone (quarter hours, daylight saving included) |
| Time zone | `time.zone` ("") | A World catalogue city (Part 6), picked in a searchable city sheet (SE0, [below](#since-then)). The offset in force stays in the kernel and `clock.dat` |
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


## Time zones with daylight saving (Part 6, 2026-11-13)

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
- the Time zone row stepped through the cities one tap at a time; the city sheet replaced that in SE0 ([below](#since-then)).

## Since then

- **The Date & time page** moved into the Settings app (`NEOSET.EXE`, SE0, 2026-11-26): a searchable city sheet and a
  format sheet replace the steppers, and Automatic time zone works with Automatic time off
  ([settings.md](settings.md#e-time-zone-s-se0-m-se1)).
- **The zone rules** are generated from a vendored IANA release (2025b) since SE1b (neoui#40, 2026-11-26), with the
  years checked recorded ([history/settings-plans.md](history/settings-plans.md#se1-plan-proposed-2026-11-26-for-review)).
- The Clock and Calendar apps and DTSRV are in [../apps/datetime.md](../apps/datetime.md).
