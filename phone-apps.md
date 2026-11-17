# Phone, Contacts and Messages: three apps (NEOPHONE v2)

NeoSymbian/phone builds three apps on the neoui kit (`neoui-kit.md`), from the design canvas's NEOPHONE v2 pages (`p2-*`
boards: Phone, Contacts, Messages). They used to be one process behind three icons (C8/C9, `telephony.md`).

**The owner's decisions (2026-11-17):**
- **Three separate EXEs.** Each has its own card in Open apps; they open each other. This replaces the canvas's P01 ("one app with three tabs").
- **The footer stays as an app switcher.** Phone · Contacts · Messages: a tab opens the other app; the app drawing it keeps its own tab selected.
- **Every "Proposed" item on the boards is built.** What the platform can't do yet is listed under [Missing platform functions](#missing-platform-functions).

## The apps

| EXE | UID | Key | What | Resident |
|---|---|---|---|---|
| `NEOPHONE.EXE` | 0xE0005001 | `phone` | Recents with the keypad sheet, call details, speed dial, the call screens, the shared Settings page (calls, log, contacts, messages), blocked numbers, quick replies | yes: an incoming call shows at once |
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

**MODEMD.** Messages' Archive uses modem-ipc 2.4 (`EDIT_ARCHIVE_THREAD` 8, `EDIT_UNARCHIVE_THREAD` 9); a new
message brings the thread back.

## Missing platform functions

These are what the boards show that the platform can't do yet, and what each app does meanwhile.

| Board | Missing | Meanwhile |
|---|---|---|
| Contacts editor: Photo | a photo picker (no Photos app, no file picker) | the slot is shown and does nothing |
| Contacts card: Email | an Email app | the mail button is hidden on the device |
| Messages notifications | the shade's entry shows no avatar, no time and only one line of text | the title is the name; the text is the newest message |
| Messages: Paste | an app can't read the clipboard directly (only through a focused text field) | a hidden field pastes; ⋮ always lists Paste |
| Messages: badge | the shell already counts unread messages from MODEMD; an app badge would add to it | Messages posts no badge |

Phone found no gap: every action on its boards maps to a MODEMD call or a setting (the IMEI code `*#06#` still only
shows a note, as before).

**Kit candidates** (built inside the apps; worth moving to the neoui kit when another app needs them): a multi-script
letter strip (lit section, separators, bubble), a dialog with a detail line and check boxes, a ChoiceSheet with the
radio on the left, an icon button with a label (the card's and details' Call / Message pills), a ListRow with a
trailing call button, a press with a 500 ms hold that reports the finger's place, a "menu at the finger" helper,
Chip / Switch / Sheet that follow the app's state instead of keeping their own.

## Status (2026-11-17)

| Part | State |
|---|---|
| neoui 1.9 (`apps-split`): OPEN / ARG / DONE, notification actions, two residents, the kit parts (Keypad, Fab, Bubble, Composer, Chip count, Act tint, title font, `alt`, FormHeader `has-save`) | built |
| the split into three EXEs, the shared frame | built; RAM-booted on the Pixel with the old screens |
| Phone, Contacts, Messages v2 (every `p2-*` board, `snapshots/p2-*.png`) | built (phone `split`) |
| telephony 2.4 (archive) | built (`sms-archive`) |
| a Pixel RAM boot with the v2 screens | next |
