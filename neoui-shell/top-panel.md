<!-- SPDX-License-Identifier: Apache-2.0 -->
# Top panel: status bar, shade, notifications, media, calls and messages, live island, control centre, lock screen

**Status: designed 2026-11-21; TP0 done (docs + canvas); TP1 built 2026-11-26 (neoui#50); TP2–TP9 not built.** The design comes from the canvas page **Top panel &
notifications** (18 boards) plus the related boards on the Shell, Navigation, Phone, Messages, Clock, Files, Store,
Browser and Settings pages. The screen map is at the [end](#screen-map). It replaces `neoui-shell.md` Part 2 (the
2026-11-09 notification sketch, whose opcode numbers are void) and Navigation's G6 lock screen. The hub is
[../neoui-shell.md](../neoui-shell.md); the wire numbers are in [protocol.md](protocol.md).

Canvas: https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ (page "Top panel & notifications").

## Decisions

**The owner's decisions (2026-11-21):**

| # | Decision |
|---|---|
| TPD1 | All shell docs live in `docs/neoui-shell/` with `neoui-shell.md` as the hub |
| TPD2 | Lock screen: swipe to unlock first; the screen-lock PIN is a later phase (TP9) |
| TPD3 | An incoming call while the phone is in use is a **heads-up banner** (Answer · Reject · Reply). With the screen off or locked it stays full screen |
| TPD4 | **Background playback:** audio keeps playing when the user leaves the player; the panel, the island, the lock screen and the home Media card control it |
| TPD5 | Build order: **media early** (TP3 right after the cards), so Files FA9 M1b can land |
| TPD6 | The boards still missing are drawn in TP0 |
| TPD7 | **NEOPHONE posts its own call cards, banners and activities** through the same model; the shell's hard-coded call, missed-call and unread rows go |

**The canvas's proposals (`api-notify-model`):** these were not approved separately. They are approved with this
document.

| # | Proposal |
|---|---|
| P01 | **One panel, two stops.** A tap or pull opens the tile row plus the notifications; a second pull, or a drag past the tiles, opens the full control centre. There is no left/right split pull |
| P02 | **The shell draws every notification.** Apps describe cards; there are no app-drawn notification views (K01 keeps the shade in the shell) |
| P03 | **Channels with four importances:** Urgent, Default, Low, Min. The app declares them; the user can override each |
| P04 | **The live island is drawn in the status bar.** The Pixel has no cut-out, so it is a drawn pill with at most 2 activities, and the shell ticks the times |
| P05 | **One media session system-wide:** the last app that played owns the shade, lock-screen and island player |
| P06 | **App tiles are placed by the user:** TILE only offers a tile, and nothing appears in the control centre until the user adds it |

## What exists today (2026-11-21)

**Status bar** (`neoui/ui/components/frame.slint` `StatusBar`, fed by `symbian/src/{phone,wifi,battery}.rs`):
- the clock at the left, then the operator, the RAT and signal bars (R when roaming), the unread-SMS envelope,
  Wi-Fi with its band label ("2.4"/"5"), and one battery widget;
- **Battery:** red at or below 15 %, orange at or below 30 %. A bolt when plugged (dim while the charger idles), a
  check when full on USB, "--" when unknown;
- `status.seconds` (off by default) makes the loop wake every second.
- There are no app glyphs, no mode icons (silent, alarm, DND, headset) and no island.
- Board `sh-statusbar-states` draws the built states. It marks No SIM, SOS only and roaming as proposed.

**Shade** (`ui/components/shade.slint`): the big time (and the date if `shade.date`), 4 toggles (Wi-Fi, Bluetooth
(drawn only), Mobile data, Silent), brightness. Then the cards:
- the newest app card expanded (avatar, time, two lines, up to 2 action pills, the progress bar), the rest as 72 dp rows;
- then the shell's own rows: **call in progress**, **N missed calls** (from MODEMD's log vs `phone.missed_seen`),
  **N new messages** (hidden while Messages posts its own).
- There is no swipe to dismiss, no Clear all and no groups. Cards live in RAM only, at most 16 per app (`NOTIFICATIONS_MAX`).
- It opens with a tap on the status bar or a drag of more than 24 dp on it; there is no top-edge gesture.

**The wire today** (`page::Notification`, NOTIFY 18): `id`, `title` ≤ 48 B, `text` ≤ 160 B (a newline gives two
lines), `page`, `actions` ≤ 2 × 16 B, `initials` + `tint` (the avatar), `time` (≤ 16 B, text the app writes),
`progress` 0–100 (1.11). An empty title removes the card. A tap sends `Page { page }` and then `Notified { id, 0 }`;
action `i` sends `Notified { id, i + 1 }`.

**Who posts:**
- **NEOMSG:** one card per unread conversation (Reply, plus Call for a real number); there is no Mark read.
- **NEOFILES:** the copy/move job (progress + Cancel, re-posted every second).
- **Nobody else.**
  - Alarms ring through `clockwork.rs` → `ui.show("clock")`. They don't wake the screen.
  - The shell pulls NEOPHONE full screen when a call rings (`phone.rs:269-287`).

**What does not exist:**
- the lock screen, a device PIN, banners, the island, a media session and audio focus;
- headset or media keys, a volume HUD, `notify.*`/`shell.*`/`lock.*` keys;
- `Visible(false)` on screen-off: apps can't tell the screen went off.
- Home's Music and Agenda cards are static mock-ups.

## Who draws what

| Surface | Drawn by | Fed by | Phase |
|---|---|---|---|
| Status bar: clock, app glyphs, system icons | shell | MODEMD, Wi-Fi, battery, settings; NOTIFY (Default and above) for the app glyphs | TP1 |
| Shade, first stop: date, 4 tiles, media, cards | shell | system tiles, MEDIA, NOTIFY, ACTIVITY (Live) | TP1–TP3 |
| Cards (shade, banner, lock screen) | shell | NOTIFY | TP2, TP4 |
| Heads-up banner | shell | NOTIFY on an Urgent channel; NEOPHONE's incoming call | TP4, TP5 |
| Media player (shade, island, lock, home) | shell | MEDIA | TP3 |
| Live island | shell | ACTIVITY; transient system alerts | TP6 |
| Control centre and tile details | shell | system tiles + TILE; `shell.tiles` | TP7 |
| Lock screen | shell | NOTIFY (with privacy), ACTIVITY, MEDIA | TP8 |
| Volume HUD | shell | volume keys, `sound.*` | TP3 |
| Settings pages (Panel & notifications, per-app channels, Lock screen) | Settings app | the shell's keys below | TP4, TP8 |
| The full-screen call, the alarm ringing | the app (NEOPHONE, Clock / DTSRV) | MODEMD, DTSRV | as today |

**The flow (`api-notify-model`):**
1. An app sends NOTIFY, ACTIVITY, MEDIA or TILE; NEOPHONE and NEOMSG post the call and SMS cards.
2. The shell keeps one list per app: cards, activities, the media session, tiles.
3. Filters apply: is the app allowed, the channel's importance, Do not disturb, the rate limit, the lock-screen
   privacy.
4. The surfaces draw it: status glyph, banner, shade, lock screen, island, tone and vibration.
5. The user taps a card, an action, a reply, a swipe, a tile or a media key.
6. That goes back to the app as an AppEvent. A stopped app is started at its page first, as Clock is woken for an
   alarm today.

## The model

### Cards (NOTIFY grows in TP2, compatible with 1.12's record)
One card model for the shade, the banner and the lock screen (`nt-anatomy`):
1. App glyph and name (from the launcher entry), tinted by the channel.
2. When: `when` (unix ms; 0 = now). The shell writes "now", "2 min", then the clock time; the app's own `time`
   text stays for old records.
3. Group count and expand: the same app and `group` make one stack; ▾ shows the rest. A collapsed group shows a
   summary ("4 new messages · Ava (2), Ben, +374…").
4. Large icon: a BLOB id (avatar, album art, file type; ≤ 128 × 128 in the ENTRY icon encoding), or 1.9's initials
   on a tint.
5. Title ≤ 48 B, one line.
6. Text ≤ 160 B, two lines; BigText shows up to 480 B expanded.
7. Progress: value/max or indeterminate; updates are silent.
8. Actions: ≤ 3 (up from 2), each ≤ 16 B, kind Button · Reply { hint } · Danger.
9. Gestures: a tap opens the app at `page`. A swipe dismisses (not an ongoing card). A slow swipe offers Snooze
   15 min / 1 h and the channel's settings. A hold opens the channel's importance sheet.

**Styles:** Basic, BigText, Picture { blob }, Progress { value, max }, Conversation { person, blob }, Call,
Chrono { since or until }.

**Flags:** ONGOING (can't be swiped; Live section), SILENT_UPDATE (no sound or banner, and no rate cost), PRIVATE
(text hidden on the lock screen).

**Rules:**
- Posting the same `id` again **replaces** the card in place, silently unless asked.
- At most 24 cards per app; older ones fold into the group summary.
- The shade orders cards in sections: **Live** (ongoing and activities), **Conversations**, **Alerts**, then
  **Silent** folded at the bottom ("3 silent · Store, Files, Terminal").
- Opening an app doesn't clear its cards; the app cancels them when they are dealt with.
- A history keeps 24 h of dismissed cards (TP2: RAM only; surviving a reboot is later).

### Channels and importance (TP4)
An app declares channels (`CHANNEL`: id, name ≤ 32 B, importance); the user's choice wins after the first post.

| Importance | Sound / vibrate | Banner | Status glyph | Shade | Lock screen | Island | For |
|---|---|---|---|---|---|---|---|
| Urgent 4 | yes | yes, 5 s | yes | top | yes | 2 s alert | conversations, calls, alarms, timers done |
| Default 3 | yes | — | yes | by time | yes | — | a missed call, an update ready |
| Low 2 | — | — | — | by time | glyph only | — | delivery reports, sync done |
| Min 1 | — | — | — | the Silent fold | — | — | tips, background info |
| Ongoing | — | — | yes | Live, top | yes | the activity | calls, downloads, recording: can't be swiped |

- **Do not disturb** holds sound, vibration and banners for everything except alarms, calls from favourites and
  repeated callers; the cards still reach the shade.
- **Rate limit:** 5 alerting posts per minute per app; SILENT_UPDATE posts are free.
- With an app's notifications turned off, NOTIFY answers `KErrPermissionDenied` (the app may ignore it).

### Media session (TP3)
`MEDIA` carries: title, artist and album (≤ 48 B each), art (BLOB), duration, position at a time `at` (the shell
moves the bar itself), state (Stopped, Playing, Paused, Buffering), and caps (Prev, Next, Seek, Shuffle, Repeat).
An empty record ends the session.
- **One session system-wide (P05):** the last app that sent Playing owns it. A new player takes over and the old
  one gets `Media { PAUSE }`.
- The same session draws the shade's media card (`tp-shade`), the island's media activity (TP6), the lock-screen
  player (TP8) and the **home Media card**. The card was a static mock-up until now.
- Commands come back as `Media { cmd, arg }`: play, pause, next, prev, seek (ms), shuffle, repeat.
- **Background playback (TPD4):** the player keeps playing while it is not in front. The shell does not
  `Quit` the session's owner to make room (`MAX_RUNNING`) while it is Playing.
- **Calls:** NeoAudio preempts media during a call, as today. The player pauses on PREEMPTED and resumes after
  (Files does this already). The session shows Paused.
- **Volume HUD:** the volume keys show a small level bar under the status bar, for the media or the call volume.
- Headset and media keys come with hardware A8 (no key path exists yet).

### Live island (TP6)
A pill in the middle of the status bar (≤ 200 dp compact) for things happening now. `ACTIVITY` carries:
- `kind`: Call, Timer, Media, Progress, Recording, Other;
- `title` ≤ 32 B and `text` ≤ 64 B (the expanded card);
- `tint` (the shell clamps it to readable colours), `lead` (a BLOB or a system glyph);
- `trail`: Text (≤ 8 B), Since (ms), Until (ms) or Ring (value, max);
- up to 2 buttons and a `page`. An empty title ends it.

Behaviour:
- **Compact:** one activity, or two (a pill plus a circle). **Transient system alerts** for 2 s: the ringer to
  Silent, the charger plugged in, a headset connected.
- **Expanded (hold):** opens in place over the status bar. A call has Mute · Keypad · Speaker · End (`di-call`); a
  timer Pause · Cancel; a download Pause · Cancel; media the player (`di-home`).
- **Gestures:** a tap opens the activity's app at its page; a hold expands; a sideways swipe swaps the pill and the
  circle; a swipe up folds; pulling down past it opens the shade with the activity at the top of Live.
- **Order:** Call › Recording › Timer › Media › Progress › other. The two highest show; the rest wait in the
  shade's Live section. Full-screen apps hide the island, except for a call or a recording.
- **Rules:**
  - An app may start an activity only while in front, or from a running call, timer, media session or transfer.
  - At most 1 update a second; the shell ticks Since/Until itself.
  - Progress is a value, never a string.
  - The user can turn apps off (`island.deny`).
- **Same data, three places:** the island, a card at the top of Live, and the lock screen.
- **Media in the island is derived from MEDIA:** a player does not also send an ACTIVITY.

### Tiles and the control centre (TP7)
- **First stop:** the shade's row of 4 tiles (the first 4 of `shell.tiles`).
- **Second stop (`tp-control`):**
  - wide tiles with a sub-line: Wi-Fi (network), Bluetooth (device · battery), Mobile data (operator · RAT), Cast;
  - then the small tiles; brightness; the media player;
  - a ⚙ opens Settings and ✎ edits.
- **Details (`tp-wifi`):** every wide tile opens a detail sheet (Wi-Fi networks, Bluetooth devices, data SIM).
- **Edit (`tp-edit`):** drag to reorder, hold to make a tile wide or small, drag to remove. Labelled tiles come
  from apps.
- **A tile shows only when something backs it.** Flashlight, Auto-rotate, Hotspot, Battery saver, Cast, NFC and
  screen record have no driver or service yet; they are hidden, not drawn dead.
- **App tiles (`TILE`):** label ≤ 16 B, sub ≤ 24 B, glyph, kind Toggle · Action · Detail (opens `page`), on, page;
  at most 4 per app. A tap sends `Tile { id, hold: 0 }`; a hold sends `hold: 1` (its settings page).
  - Examples on the board: Stopwatch (Clock), SSH home (Terminal), Shuffle (Music), Speed dial (Phone).

### Lock screen (TP8)
Shown when the screen comes on after it went off (`nt-lock`):
- the time and date, the island's activity (a timer), the media player, and the cards;
- privacy follows `notify.lock`: show all, hide content ("Messages · 2 · content hidden"), or nothing;
- "+3 more", and Swipe up to unlock. In Gestures and N9 modes any edge also unlocks (Navigation's old G6).

Rules:
- **What wakes the screen:** the power key, an incoming call (as today), a ringing alarm or timer (**new:** the
  alarm wakes the panel), an Urgent card (only with `notify.lock` = show).
- A ringing alarm or call shows full screen **over** the lock screen; ending it returns to the lock screen.
- Double-tap to wake needs the touch controller awake with the panel off (kernel `a64_touch.cpp`); later.
- **The screen-lock PIN (TP9)** is designed but not built first: a PIN pad over the lock screen, attempts with
  back-off, the PIN's salted verifier in the shell's private folder (not a settings key).

## Calls and messages from the panel

**Calls (TP5, NEOPHONE posts; TPD3, TPD7):**

| Moment | What the user sees | Who does it |
|---|---|---|
| A call rings, phone in use | **Heads-up call banner**: avatar, name, number; Answer · Reject · Reply with message. It does not time out; a tap expands it to the full call screen | NEOPHONE posts an Urgent Call-style card with a sticky flag; the shell draws the banner. Answer and Reject come back as `Notified` actions and NEOPHONE calls MODEMD |
| A call rings, screen off, locked or on home | the full-screen incoming call (`p2-call-incoming`), as today | the shell keeps `ui.show("phone","call")` for these cases only |
| In a call, user left the call screen | the **island** (green, time ticking; hold = Mute · Keypad · Speaker · End, `di-call`) and a Live card in the shade (`nt-shade`). The in-app "Return to call" bar stays | NEOPHONE: ACTIVITY (TP6) + an ONGOING Call card (TP2) |
| A missed call | a card "2 missed calls · Ben Okafor, +1 555 0123" with Call back · Message (Default channel) | NEOPHONE posts it (TP2); the shell's row goes |

**Messages (TP2, TP4):**
- Each conversation is one Conversation-style card (avatar, the last 2 lines) with **Reply · Mark read · Call**
  (`nt-shade`, `p2-msg-notify`). Several conversations group under "N new messages".
- **Inline reply (`nt-reply`):** Reply opens a field in the card with the shell's keyboard and quick replies ("OK",
  "On my way", "Call you later"). The counter shows "Unicode · 145 left · 1 SMS". Send gives `NotifyReply { id }`;
  NEOMSG reads the text with `REPLY_TEXT` and sends the SMS. **The user stays in the app they were in.**
- An Urgent conversation also shows as a heads-up banner (`nt-headsup`) with Reply · Mark read · Call; a swipe up
  hides it and a tap opens the thread.
- Mark read clears the card and the badge (NEOMSG marks the thread read in MODEMD).
- Blocked senders never post (as today).

## Settings keys

Owned by the shell; the Settings app writes them (`NEOSET.EXE`, [settings.md](settings.md#the-settings-app-neoset), through its
`Caller::Settings` allowlist). Setting names are at most 32 bytes (`settings::KEY_MAX`); app keys, as in `n.<app>`,
are at most 16 (`ipc::KEY_MAX`).

| Key | Value | Meaning | Phase |
|---|---|---|---|
| `shell.tap` | u8: 0 shade · 1 control centre | what a tap on the status bar opens | TP1 |
| `shell.swipehome` | bool (on) | a swipe down on home opens the shade | TP1 |
| `shell.media` | bool (on) | the media player in the shade | TP3 |
| `shell.tiles` | bytes: tile ids, 2 B each | the control centre's order; the first 4 are the first stop | TP7 |
| `notify.dnd` | bool | Do not disturb | TP4 |
| `notify.dndto` | time | when it ends | TP4 |
| `notify.dndfav` | bool (on) | calls from favourites and repeated callers ring | TP4 |
| `notify.bannert` | u8 seconds (5) | how long a banner stays | TP4 |
| `notify.lock` | u8: 0 show · 1 private · 2 off | cards on the lock screen | TP8 |
| `n.<app>` | bytes: allow + importance per channel | the user's choices; app keys ≤ 14 B | TP4 |
| `island.on` | bool (on) | show live activities | TP6 |
| `island.deny` | bytes: app keys | apps turned off for the island | TP6 |
| `lock.on` | bool (on) | show the lock screen at screen-on | TP8 |
| `lock.pin_set` | bool, set by the shell only | a PIN is set; the PIN's salted verifier lives in the shell's `\private\e0002001\`, never in the store ([settings.md](settings.md#d-device-lock-and-sim-pin-l-lock-m-sim-se5se6)) | TP9 |

The Settings boards (`tp-settings`, `nt-settings`, `set2-notifications`, `set2-notify-app`, `set2-lock`) draw these
rows. `set2-notify-app` names `notify.messages.on`/`.banner`; they become `n.messages` here.

## Protocol

The numbers are reserved in [protocol.md](protocol.md); the minor version is assigned at merge.

| Phase | Opcodes | Events |
|---|---|---|
| TP2 | NOTIFY 18 grows: `channel`, `style`, `group`, `icon`, `when`, `flags`, ≤ 3 actions with kinds; 31 `BLOB` (id, image; ≤ 32 per app); 32 `NOTIFY_CLEAR` (all of the app's cards) | 22 `NotifyGone { id, why }` |
| TP3 | 33 `MEDIA` | 23 `Media { cmd, arg }` |
| TP4 | 34 `CHANNEL`; 35 `REPLY_TEXT` (id → the text, ≤ 480 B) | 24 `NotifyReply { id }` |
| TP6 | 36 `ACTIVITY` (or `KErrPermissionDenied` when the user turned the app off) | 25 `ActivityTap { id, i }` |
| TP7 | 37 `TILE` | 26 `Tile { id, hold }` |

The struct sketch is on the canvas board `api-notify-protocol`, renumbered in TP0. `neoapp` gains `notify` (the
grown record), `clear_notify`, `blob`, `media`, `channel`, `reply_text`, `activity` and `tile`. Processes outside
neoui (Apache, such as neohw) encode with `neoui-proto` and do not link the GPL `neoapp`.

## Phases

Each phase ends on the Pixel, with neoui host snapshots for every new board and a step in `taps.sh` (run on QEMU virt from US6b).
1.12 apps keep working throughout.

| # | Phase | What | Protocol | Repos | Done when |
|---|---|---|---|---|---|
| **TP0** | Docs + canvas | This folder; [protocol.md](protocol.md). On the canvas: renumber `api-notify-protocol`/`api-notify-model`; fix `set2-notifications`/`set2-notify-app` ("neoui-shell Part 2" → TP stages) and `store-shade` ("no progress field": 1.11 has one); **draw the missing boards** ([below](#boards-drawn-in-tp0)) | — | docs, canvas | every board on the five pages is in the screen map; the link check passes |
| **TP1** | Status bar v2 + the first stop | Left: the clock + app glyphs (≤ 3, then +n). Centre: the island slot (empty). Right: silent/vibrate, alarm set, DND, headset, airplane, No SIM / SOS / roaming, charging. The shade's first stop as `tp-shade` (date header, the 4-tile row, the media slot, cards, "Pull for all controls"). A pull down from the status bar anywhere. `Visible(false)` when the screen goes off. `shell.tap`, `shell.swipehome` | — | neoui | the 11 `tp-statusbar` states render on the phone; the shade opens by tap and pull |
| **TP2** | Cards | NOTIFY grows; BLOB, NOTIFY_CLEAR, NotifyGone; sections, swipe to dismiss, Clear all, groups, history; 24 per app. **NEOPHONE** posts missed calls and the ongoing-call card, and the shell's three rows go. **NEOMSG** posts Conversation cards with Mark read. **Files** moves its job to Progress style | 31, 32 / 22 | neoui-proto, neoui, phone, files | a missed call, an SMS and a Files copy show as `nt-shade` cards; a swipe dismisses and the app hears NotifyGone |
| **TP3** | Media session | MEDIA + Media events; the shade's media card; the home Media card goes live; the volume HUD; `Visible(false)` when the screen goes off (moved from TP1). **Files FA9 M1b:** Files posts the session, keeps playing in the background, and its footer "Stops when you leave Files." changes | 33 / 23 | neoui-proto, neoui, files | a WAV started in Files plays on with Files in the background; pause, next and seek work from the shade and from home |
| **TP4** | Channels, banners, reply, DND | CHANNEL, importances, the user's override; the heads-up banner (never over a full-screen call or the keyboard's field); inline reply with the shell keyboard; the rate limit; Do not disturb; tone and vibration per importance (`sound.rs`, haptics); Settings pages and the `notify.*`/`n.<app>` keys. **Messages:** Reply, Mark read and Call from the banner and the shade | 34, 35 / 24 | neoui-proto, neoui, phone | an SMS arrives as a banner while Files is open; Reply sends it and Files stays in front; DND holds the banner |
| **TP5** | Calls in the panel | NEOPHONE posts the incoming call as a sticky banner while the phone is in use; full screen when the screen is off, locked or on home. Answer and Reject from the banner; Reply with message | (uses TP2/TP4) | phone, neoui | a call rings over Files as a banner; Answer connects; a call to a locked phone is full screen |
| **TP6** | Live island | ACTIVITY; compact, two, expanded; transient alerts; the order and permission rules; `island.*`. **Producers:** NEOPHONE (the call, `di-call`), the media session (derived), Files (copies), later Clock/DTSRV timers and Browser downloads | 36 / 25 | neoui-proto, neoui, phone, files | in a call, Files shows the green island; a hold gives Mute/Speaker/End; music shows as the circle |
| **TP7** | Control centre | The second stop; wide tiles; details (Wi-Fi first); edit mode; `shell.tiles`; TILE for apps; only backed tiles show | 37 / 26 | neoui-proto, neoui | `tp-control`, `tp-edit` and `tp-wifi` match on the phone; the order survives a reboot |
| **TP8** | Lock screen | Shown at screen-on; cards by `notify.lock`; the activity and the media player; swipe to unlock (any edge in Gestures/N9); alarm wake; ringing over the lock screen; Settings → Lock screen | — | neoui, datetime (alarm wake) | the phone wakes into `nt-lock`; an alarm wakes the screen and rings over it |
| **TP9** | Screen-lock PIN (later) | PIN pad, back-off, a hashed key; asked on wake | — | neoui | — |

**Order:** TP0 → TP1 → TP2 → TP3 → TP4 → TP5 → TP6 → TP7 → TP8 (→ TP9). TP3 is early so Files FA9 M1b can land;
TP7 and TP8 can swap.

**Who else waits on this:**
- datetime DT1/DT5 (alarm and reminder cards with Snooze: TP2/TP4; timers in the island: TP6);
- NeoStore ST5 (install progress: built in 1.11, Progress style in TP2);
- Browser WB5 (download done: TP2; downloads in the island: TP6);
- Files FA9 M1b (TP3).

### TP1 plan (2026-11-26)

From `tp-statusbar`, `tp-shade` and `tp-shade-buttons`; neoui only, no protocol change. **Only what something
backs is drawn** (D4); the rest of the 11 states come with the phase that feeds them.

**Status bar** (`ui/components/frame.slint` `StatusBar`, 25 dp):
- **Left:** the clock, then up to 3 **app glyphs** (14 dp, `text-secondary`), then "+n". One glyph per app with
  cards in the shade, newest first: a small table by app key (`messages` → message, `phone` → missed_call,
  `files` → folder, `clock` → alarm, anything else → bell). The shell's own rows count too (missed calls → phone,
  unread SMS → messages, while Messages posts no cards of its own). The C9 unread envelope goes: it is this glyph now.
- **Centre:** an empty island slot (TP6).
- **Right, in the boards' order:** the mode icons (ring off: vibrate, or silent when vibration is off too;
  alarm when an alarm is on, from `clock.alarms`), then the network (RAT + bars, R when roaming; **No SIM** when
  the SIM is absent, **No service** otherwise; no "SOS" while emergency calls can't be placed; a plane instead of all
  of it in airplane mode), Wi-Fi,
  the battery (the bolt while charging; **amber fill** while the battery saver is on).
- **The operator's name leaves the bar** (the boards don't show it); Settings → Mobile network keeps it.
- **Not in TP1:** privacy dots and screen recording (no source yet), the island (TP6), DND's moon (TP4), headset
  (no jack detection yet: a gap for AUDIOD).

**The shade's first stop** (`ui/components/shade.slint`), under the status bar, which stays visible:
- **Header:** the time (30 dp, light), the date (if `shade.date`), then ⚙ (opens Settings; Panel & notifications
  once TP4 adds it) and ⏻ (the power menu). ✎ comes with the control centre (TP7).
- **Tiles:** the 4 as today, drawn as the board's 74 dp tiles (radius 14, accent when on, icon over label).
- **Brightness** as today; the **media slot** stays empty until TP3.
- **NOTIFICATIONS** and the cards as today (TP2 brings sections, See all, swipe and Clear all).
- **Shape:** bottom corners 22 dp, the scrim over the rest. "Pull for all controls" comes with TP7.
- **Buttons mode** (`tp-shade-buttons`): the same panel above the key row, whose Back closes it.

**Opening it:**
- a tap, or a pull of more than 24 dp, anywhere on the status bar (as today), over home and over apps;
- **`shell.swipehome`** (bool, on): a swipe down on home opens it too. A press on the home pages that first moves
  steeply down (more than twice as far down as sideways) is a pull: the widget under it gets no click and the page
  doesn't turn, and the shade opens past 48 dp, only while home is still in front. Other drags stay page swipes. Its Settings row arrives with `tp-settings` in TP4. `shell.tap` waits for TP7, where it has a choice.

**`Visible(false)` when the screen goes off moves to TP3.** Files stops its audio on `Visible(false)` ("Stops when
you leave Files"), so sending it at screen-off before background play exists would cut music at every screen
timeout. TP3 sends it together with the media session, once Files keeps playing in the background.

**Checks:**
- **host:** `tp1-statusbar-pixel.png` (idle, apps waiting with +n, ring off with an alarm, silent, charging with
  the saver, airplane, No SIM, No service, roaming) and the shade snapshots (`shade-*`); a test for the glyph table
  and the +n count;
- **virt-taps:** swipe down on home → the shade; ⚙ → Settings;
- **Pixel:** the bar with real Wi-Fi, LTE, battery and charging; ring off and vibrate; an alarm set (then put back);
  the shade by tap, by pull and from home; ⚙ and ⏻ from the shade. Airplane mode is not switched
  on the phone (never Offline); its state is checked on virt.
- **boot.img measured** (27.56 MB now, the limit about 28.6 MB).

**TP1 runs (2026-11-26):**
- **virt (image 32/33):** a swipe down on home → the shade; ⚙ → Settings; ⏻ → the Power menu; a short pull on a
  favourite opens nothing; a sideways swipe still turns the page.
- **Pixel, image 33 (`tp1-boot33.img`, 27,566,080 bytes):**
  - the bar with real LTE (4 bars), 5 GHz Wi-Fi and the battery full on USB, no operator name;
  - the shade's Silent tile → the vibrate glyph in the bar, then back to the Outdoor profile;
  - the shade by a tap on the bar, a pull from the bar and a swipe down on home; ⚙ → Settings; ⏻ → the Power menu
    (Cancel);
  - home's long press still opens Edit home · Wallpaper; a page swipe and the home pull no longer do;
  - `settings.dat`, both `wifi.dat` and `left.dat` byte-identical before and after.
- **Found on the Pixel (image 32) and fixed:** the swipe down opened the shade, and half a second later home's long
  press menu over it. The UI server's takeover (`cancel_touch`) left Slint's press held, so home's 500 ms timer ran
  on; page slides did the same before TP1. `cancel_touch` and the start of a pull now stop it until the next press
  (neoui `8135960`, test `home_hold.rs`).
- Not tried on the phone: the alarm glyph (host snapshot only), airplane mode (never switched on the owner's phone),
  No SIM.

### TP2 plan (2026-11-26)

From `nt-shade` and `nt-anatomy`. Three parts, so the phone repin is measured on its own:

**TP2a: the cards (neoui, protocol 1.18).**
- **NOTIFY grows**, compatible with 1.12's record (the shell still reads old records). After `progress` (now 255 =
  none when more follows) come: `flags` (ONGOING 1, SILENT_UPDATE 2, PRIVATE 4), `style` (Basic 0, BigText 1,
  Progress 2, Conversation 3, Call 4, Chrono 5), `channel` (u8, 0 until TP4's CHANNEL), `group` (≤ 16 B; "" = none),
  `when` (unix ms, 0 = now), and a kind per action (Button 0, Reply 1, Danger 2). Up to **3** actions (from 2).
- **32 `NOTIFY_CLEAR`:** every card of the caller's app goes. **Event 22 `NotifyGone { id, why }`:** 0 the user
  swiped it, 1 Clear all, 2 the app was turned off (TP4).
- **The shell's model:** posting the same id replaces the card in place (it keeps its place: no jump to the top);
  24 cards per app (from 16; older ones beyond go, oldest first, instead of refusing the post); the order is by
  section, then newest first: **Live** (ONGOING), **Conversations** (style Conversation), **Alerts** (the rest).
  The Silent fold comes with importances (TP4).
- **Step 0, the caller check:** NOTIFY, NOTIFY_CLEAR and BADGE answer `KErrPermissionDenied` when the session's
  process isn't its app's EXE (the SID from `exes.txt`, kept in `neoui-proto::apps`); apps outside the table (old
  apps' bridge) keep today's binding. TP4's per-app switch relies on it.
- **The shade (`nt-shade`):**
  - the first stop shows the first 2 cards and "See all N"; See all opens the list: the compact header (time, date,
    ⚙), the sections with their labels, then **Clear all** (ONGOING cards stay);
  - a card: the app's glyph and name, "· now / 2 min / 10:24" from `when` (the app's `time` for old records), the
    group's count and ▾, the avatar (initials on a tint), title, two lines, progress, up to 3 actions (Reply drawn
    as the main one, Danger in red);
  - a **group** (same app and `group`) shows its newest card with the count; ▾ opens the rest under it;
  - **swipe** left or right past a third of the width dismisses a card (not ONGOING ones): the app hears
    `NotifyGone { id, 0 }`.
- **neoapp:** `notify` takes the grown record, `clear_notify()`, `AppEvent::NotifyGone`.
- **A producer for virt:** NEOKIT (the kit gallery and new-app template) gets a Notifications demo row that posts a
  conversation, an ongoing call-style card, a progress card and a 3-card group, so `virt-taps` can check sections,
  a swipe and Clear all.
- **Not in TP2a (they have no producer or no screen yet):** BLOB (31) and Picture style (no app has images to post),
  the 24 h history (no view shows it), slow-swipe Snooze and the hold sheet (channels, TP4), the Silent fold (TP4).

**TP2b: Phone and Messages post their own cards (phone repo, neoui).** NEOPHONE: "N missed calls · names" with Call
back · Message, and an ONGOING Call-style card during a call (End). NEOMSG: one Conversation card per unread
thread with Reply · Mark read · Call, grouped under Messages. The shell's three rows (call in progress, missed
calls, new messages) go in the same change. This needs phone's repin to neoui's TP2a rev (it waits today with
phone#10): **boot.img is measured first; past ~28.6 MB, stop and ask the owner.**

**TP2c: Files' copy job as Progress style** with its Cancel, when files repins (waits with files#15).

**Checks (each part):** host snapshots of the shade (first stop with See all, the list with every section, a group
open, a swipe in progress), round-trip and limit tests for the record and its old form, the section order and the
24-per-app rule; virt-taps with NEOKIT's demo; a Pixel run on the final head; boot.img measured.

## Boards drawn in TP0

Drawn on 2026-11-21 (canvas version 67, the Top panel page's "TP0" row). The same publish renumbered
`api-notify-protocol`/`api-notify-model` and fixed the notes on `set2-notifications`, `set2-notify-app` and `store-shade`.

| New board | Shows | Phase |
|---|---|---|
| `nt-call-banner` | the incoming-call heads-up banner over an app (Answer · Reject · Reply) | TP5 |
| `nt-volume` | the volume HUD under the status bar (media and call) | TP3 |
| `tp-shade-buttons`, `tp-control-buttons`, `nt-headsup-buttons` | the first stop, the control centre and a banner in Buttons mode (56 dp key row) | TP1, TP4, TP7 |
| `nt-lock-pin` | the PIN pad over the lock screen (marked Later) | TP9 |
| `nt-files-player` | the Files player with background play: the new footer, the session in the shade | TP3 |
| `nt-home-media` | the home Media card live, from the session | TP3 |

## Screen map

Every board on the five pages the shell owns, and the related boards elsewhere. "Baseline" means as built and
replaced by the named phase.

**Top panel & notifications page (26):**

| Board | Phase | Notes |
|---|---|---|
| `tp-statusbar` | TP1 | 11 states: idle, apps waiting, privacy dots, island call/music/two, recording, charging, modes, DND, airplane |
| `tp-shade` | TP1, TP3 | the first stop: 4 tiles, media, cards, "Pull for all controls" |
| `tp-control` | TP7 | the second stop |
| `tp-edit` | TP7 | edit tiles |
| `tp-wifi` | TP7 | a tile's detail sheet |
| `tp-settings` | TP4 | Settings → Panel & notifications |
| `tp-prototype` | all | the whole flow (Play) |
| `nt-shade` | TP2 | sections Live / Conversations / Alerts / Silent |
| `nt-headsup` | TP4 | the banner |
| `nt-reply` | TP4 | the inline reply |
| `nt-lock` | TP8 | the lock screen |
| `nt-settings` | TP4 | per-app channels (Messages) |
| `nt-anatomy` | TP2, TP4 | the card, the templates, the importance table |
| `di-states` | TP6 | the island's states and rules |
| `di-home` | TP6, TP3 | media expanded on home |
| `di-call` | TP6, TP5 | the call expanded in an app |
| `api-notify-protocol` | TP2–TP7 | → [protocol.md](protocol.md) (renumbered in TP0) |
| `api-notify-model` | — | the flow, P01–P06 and stages (renumbered as TP in TP0) |
| `nt-call-banner` | TP5 | new in TP0 |
| `nt-volume` | TP3 | new in TP0 |
| `tp-shade-buttons`, `tp-control-buttons`, `nt-headsup-buttons` | TP1, TP7, TP4 | new in TP0: Buttons mode |
| `nt-lock-pin` | TP9 | new in TP0 (later) |
| `nt-files-player` | TP3 | new in TP0: Files with background play |
| `nt-home-media` | TP3 | new in TP0: the live home Media card |

**Shell & system UI page, the boards this design replaces (8):**

| Board | Phase |
|---|---|
| `sh-statusbar-states` | baseline → TP1 (No SIM, SOS and roaming drawn as proposed: TP1) |
| `sh-shade` | baseline → TP1/TP2 |
| `sh-shade-quick` | baseline → TP7 |
| `sh-shade-app-notify` | baseline (1.8 NOTIFY) → TP2 |
| `sh-toast` | built (NOTE 1.8); stays |
| `sh-badges` | built (BADGE 1.8); stays, and the count follows the cards in TP2 |
| `sh-power-menu` | built; stays |
| `sh-sim-pin` | built; stays (the SIM PIN, not the screen lock) |

The rest of the Shell page maps to [kit.md](kit.md), [home.md](home.md), [navigation.md](navigation.md) and
[keyboard.md](keyboard.md) (the hub has the whole list). The Design system page maps to
[design-system.md](design-system.md). Navigation and Keyboard map to their docs.

**Other pages, boards that post into the panel:**

| Board | Page | Phase |
|---|---|---|
| `p2-call-incoming`, `p2-call-active`, `p2-call-summary-missed` | Phone | TP5 (full screen stays for screen off and lock) |
| `nav-btn-call`, `nav-ges-call` | Navigation | TP5 (the full-screen call in each mode) |
| `p2-msg-notify` | Messages | TP2, TP4 |
| `dt2-shade`, `dt2-ring-alarm`, `dt2-ring-timer`, `dt2-ring-event` | Clock | TP2 (cards), TP6 (timers), TP8 (ringing over the lock screen) |
| `store-shade` | Store | TP2 (Progress style; fix its "no progress field" note in TP0) |
| `br2-download-done` | Browser | TP2, TP6 |
| `files2-progress` | Files | TP2, TP6 |
| `set2-notifications`, `set2-notify-app` | Settings | TP4 |
| `set2-lock`, `set2-lock-pin` | Settings | TP8, TP9 |
| `music-playing` | Music | TP3 (a future Music app is just another session owner) |

## Gaps outside neoui

| Gap | Needed by | Owner |
|---|---|---|
| Headset and media buttons (no key path) | TP3 | neohw A8, kernel |
| Privacy dots: camera or mic in use, location | TP1 | AUDIOD (mic), GNSSD (location); no camera yet |
| Flashlight, auto-rotate, hotspot, battery saver | TP7 | kernel and neohw (none exist) |
| Double-tap to wake | TP8 | kernel touch driver |
| Ringtone/notification tones per importance | TP4 | AUDIOD (ringtone stream exists) |
| Clock alarms waking the screen | TP8 | neoui `screen.rs` + datetime DT1 |

## Not in this design (later)
- Notifications that survive a reboot.
- App-drawn notification views (P02 says no).
- Wear or second-screen mirroring.
- Notification sounds per app beyond the channel's tone.
