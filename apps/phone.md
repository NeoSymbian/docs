<!-- SPDX-License-Identifier: Apache-2.0 -->
# Phone, Contacts and Messages: three apps (NEOPHONE v2)

Part of [Apps](README.md) · Status: done · Updated: 2026-11-17

NeoSymbian/phone builds three apps on the neoui kit ([kit.md](../neoui-shell/kit.md)), from the design canvas's NEOPHONE v2 pages (`p2-*`
boards: Phone, Contacts, Messages). They used to be one process behind three icons (C8/C9, [modem.md](../hardware/modem.md)).

**The owner's decisions (2026-11-17):**
- **Three separate EXEs.** Each has its own card in Open apps; they open each other. This replaces the canvas's P01 ("one app with three tabs").
- **The footer stays as an app switcher.** Phone · Contacts · Messages: a tab opens the other app; the app drawing it keeps its own tab selected.
- **Every "Proposed" item on the boards is built.** What the platform can't do yet is listed under [Missing platform functions](#missing-platform-functions).

## The apps

| EXE | UID | Key | What | Resident |
|---|---|---|---|---|
| `NEOPHONE.EXE` | 0xE0005001 | `phone` | Recents with the keypad sheet, call details, speed dial, the call screens, the shared Settings page (Settings → Apps → **Phone & Contacts**, [../neoui-shell/settings.md](../neoui-shell/settings.md#the-settings-app-neoset); it was the root **Calls & Messages** row: calls, log, contacts, messages), blocked numbers, quick replies | yes: an incoming call shows at once |
| `NEOCONT.EXE` | 0xE0005002 | `contacts` | the list (search, favourites, the three-script letter strip), the card, the editor, selection; the only writer of the book | no |
| `NEOMSG.EXE` | 0xE0005003 | `messages` | the conversations (search, swipe Archive/Delete with Undo, Archived, selection), a thread (the bubble menu at the finger), a new message, blocked messages, one shade entry per conversation | yes: it posts the shade's entries |

Phone keeps UID 0xE0005001 and its private directory, so the book stays at `C:\private\e0005001\contacts.dat` with no
migration (ROM EXEs have AllFiles).

## How they work together

**Opening each other (neoui protocol 1.9, `OPEN`/`ARG`/`DONE`).** Each page belongs to one app
(`phone_core::page::Page::app`) and has a number there (`Page::number`). A move to another app's page opens that app
with an argument:

| From | Action | Opens |
|---|---|---|
| Contacts card, Messages thread | Call | Phone, CALL, the number. When the call ends, Phone sends DONE: back to the caller |
| Contacts card, Phone details, call screens | Message, Reply | Messages, THREAD (or WRITE: the composer takes the focus), the number |
| Phone details, Messages thread | Open contact, Add to contacts | Contacts, CARD (a new contact when none matches) or NEW, the number |
| Contacts card | Speed dial | Phone, SPEED, the number to put on a key |
| Contacts and Messages ⋮ | Settings | Phone, SETTINGS, `contacts` or `messages` (scrolled to that section) |
| the footer | a tab | that app's root |

Back at a page another app opened (a card, a thread, the editor's ✕) returns to that app (DONE); Back at an app's
root returns to the app that opened it (the shell's origin), else home.

**Shared data.**
- **The book:** Contacts writes it (`contacts.new`, then a rename) and bumps the `contacts.rev` setting; Phone and Messages watch `contacts.` and read it again.
- **Settings:** `phone.*` and `contacts.*`. Phone's Settings page and a contact card both write `phone.speed` and the `contacts.*` keys (`Owner::Apps`).
- **The blocklist:** in MODEMD (`BLOCK_GET/SET`), edited from any of the three (`phone_common::block`).
- **Quick replies:** Phone's `replies.txt`.

**The repo.**
- `ui-shared` (`@phone-shared`, compiled with `neoui_kit::compile_with`):
  - the frame: the kit header from `Nav` (actions, search, selection, ⋮), the content, the footer;
  - the shared parts and the `Icons` global.
- `crates/{phone,contacts,messages}-ui`: the screens, and the snapshot tests named after their boards (`snapshots/p2-*.png`).
- `symbian/common`: MODEMD's client, the files, the prefs reader, blocking, opening the other apps.
- `symbian/{phone,contacts,messages}`: each app's event loop and areas.

**MODEMD.** The apps use these modem-ipc additions ([modem.md](../hardware/modem.md)):
- **2.4:** Messages' Archive (`EDIT_ARCHIVE_THREAD` 8, `EDIT_UNARCHIVE_THREAD` 9). A new message brings the thread back.
- **2.5:** Unblock sender, Delete all, and the reason a message failed.
- **2.6:** a call's conference flag and connect time, the IMEI, and `SILENCE`.

**Return to call.** While a call goes on and its screen isn't showing, all three apps draw a green bar under the
header ("Ava Lindqvist · 04:12 · Return to call", the prototype's hidden call).
- Its timer counts from MODEMD's connect time (`Call::since`), so it matches the call screen in every app.
- Back on the call screen hides it.

**Calls.** Known contacts, unknown numbers and private numbers each have their own incoming screen:
- an unknown number shows the # avatar and Reply with message;
- a private number shows no Reply.

The other call screens:
- Silence quietens only this call (MODEMD's `SILENCE`); the ring settings stay as they are.
- After Merge, every connected call is multiparty, so the Conference screen shows (`p2-call-conference`): "Conference", the callers' names, a group glyph. End ends them all.
- `*#06#` shows the IMEI.

**Launcher badges.** Both resident apps keep their icon's badge (BADGE) current, hidden or not:
- Phone shows its new missed calls;
- Messages shows its unread messages.

**Contacts.**
- Send as vCard asks: **Message** opens Messages' New message with the card as text (name, then label and number), or **Save as vCard file** writes `C:\Data\<name>.vcf`.
- Speed dial on a card with several numbers asks which number to use.

## Missing platform functions

What the boards show that the platform can't do yet. Both are drawn as on the boards; a tap says what is missing
(the owner's decision, 2026-11-17).

| Board | Missing | Meanwhile |
|---|---|---|
| Contacts editor: Photo | a Photos app or picker, and photos in the book | the slot shows; a tap: "Needs the Photos app" |
| Contacts card: Email | an Email app | the button shows; a tap: "Needs an Email app" |

Done this round (they were gaps): the shade's entry with an avatar, a time, two lines and a main Reply button (NOTIFY);
an app reading the clipboard (`app.clipboard()`); unblocking a sender's messages and deleting all conversations in
MODEMD (modem-ipc 2.5); why a message failed.

## Status (2026-11-17)

| Part | State |
|---|---|
| neoui 1.9: OPEN / ARG / DONE, notification actions, two residents, the kit parts | on main |
| the split into three EXEs, the shared frame | on main; RAM-booted on the Pixel |
| Phone, Contacts, Messages v2 (every `p2-*` board, `snapshots/p2-*.png`) | on main |
| the board audit (2026-11-17): every board reached with real data; fixes for the bar timer, badges, Conference, Silence, IMEI, Send as vCard, the speed-dial number; boards `p2-call-conference`, `p2-msg-archived` | on main (modem-ipc 2.6, neohw) |
| a Pixel install | installed into slot a, 2026-11-17 ([filesystem.md](../storage/filesystem.md)) |
