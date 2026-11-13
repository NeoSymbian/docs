# Symbian phone and contacts sources: what C8 can reuse

Research for [telephony.md C8](telephony.md#c8-call-log-and-contacts) (Phone, Recents, Contacts, speed dial, call
settings), done 2026-11-13. It reads the Symbian^3 code of the three 2010 packages that held the phone and contacts
apps. **This file holds facts only:** constants, tables, algorithms in our own words, and short English UI phrases as
wording reference. No code and no `.loc`/`.rss` files are copied; they are Nokia EPL-1.0 and must not enter our
Apache-2.0/GPL-3.0 repos.

| Repo | Revision read | What it is |
|---|---|---|
| [NeoSymbian/oss.FCL.sf.app.contacts](https://github.com/NeoSymbian/oss.FCL.sf.app.contacts) | `22bf872e` (= upstream `BRANCH_RCL_3`, kit 201050); pinned in `build/sources.lock` | Phonebook2, Speeddial, Logs, PCS predictive search, the contacts model |
| [NeoSymbian/oss.FCL.sf.mw.phonesrv](https://github.com/NeoSymbian/oss.FCL.sf.mw.phonesrv) | `44089abe` (201045); pinned | dial-string parser, SS settings, voicemail, emergency numbers, USSD |
| [NeoSymbian/oss.FCL.sf.app.phone](https://github.com/NeoSymbian/oss.FCL.sf.app.phone) | `BRANCH_RCL_3` @ `17f1eec5`; forked 2026-11-13, not pinned | phone app: dialer, easydialing, call UI, DTMF |

The `master` branch of all three is the later Qt/Orbit (Symbian^4) rewrite; use the revisions above. Paths in each
section are relative to the repo named in its heading.

Tags: **[a]** fact, table or algorithm we re-express in our own code · **[b]** English UI wording we can reuse ·
**[c]** usable only by building the original binary.

## Verdict
- **[c] binaries: nothing is worth building into the ROM.**
  - Phonebook2, Speeddial, Logs and the phone UI need Avkon.
  - The parser, Pset, vmbx and phoneserver need ETel/ETelMM, which we don't have; MODEMD replaces it.
  - The PCS server needs PtiEngine and Virtual Phonebook.
  - The only buildable piece is the contacts model (`cntsrv`, `cntplsql`, `cntmatchlog`: euser, estor, ecom, sqlite, versit). It matters only if unchanged 2010 apps need `contacts.cdb` (C12). For C8 we keep our own Rust store.
- **[a] facts:** many; listed below, ready to turn into Rust code and host-test vectors.
- **[b] wording:** about 400 clean English strings. **Licence note:** they are Nokia EPL text. Reusing short UI phrases as wording is fine. Never copy the `.loc` files or code into our Apache/GPL repos.
- **Not in any repo:**
  - the GS call-settings plugin: soft-reject default text, auto-redial, any-key answer, the one-key-dialling default;
  - the platform log engine: recent-list cap (believed 20), the "Incoming/Outgoing" strings;
  - `avkon.loc` shared notes ("Not done", "Done", "Request not confirmed", …);
  - operator-name display rules;
  - status-bar texts ("No network coverage", "Offline").

  These are ours to specify.

---

## 1. Dialer (app.phone RCL_3 `phoneuis/dialer`, `phoneapp/phoneuicontrol`) [a]
- **Keypad:** a 3×4 grid `1 2 3 / 4 5 6 / 7 8 9 / * 0 #`.
  - Key 1 shows the voicemail icon.
  - Labels: `*+`; 2 abc, 3 def, 4 ghi, 5 jkl, 6 mno, 7 pqrs, 8 tuv, 9 wxyz (`dialerkeypad.rh:23-34`).
  - There is a Cyrillic second row: 2 = "абвг" (`dialerkeypad_cyrillic.rss:40-60`).
  - Dragging off a pressed key cancels its long press.
- **Long press:** 0.6 s (`phoneconstants.h:73`). It applies only when the field holds exactly that one digit.
  - 1 calls voicemail. If no number is set, ask to define it.
  - 2 calls the video mailbox only if configured; otherwise it acts as speed dial.
  - 3–9 speed dial. An empty slot asks "Speed dial not assigned. Assign it now?"
  - Pressing Call with a single digit 1–9 in the field also speed-dials.
  - 0 opens the browser (configurable app launch).
  - `#` toggles silent mode, or asks "Change outgoing phone line?" with ALS.
- **`*` multi-tap:** a second `*` within 1 s cycles `* → + → p → w`; any other key resets the cycle (`cphonekeyeventforwarder.cpp:334-366`). The Qt version uses 800 ms and allows `+` only at position 0.
- **Number entry:**
  - no digit grouping; at most 100 characters;
  - large font with 4 lines, falling back to small font with 5 lines; overflow truncated with "…";
  - paste accepts only `0-9*#+pwPW`.
- **Toolbar:**

  | Button | Field empty | Field not empty |
  |---|---|---|
  | Call | "Recent calls" | "Call" |
  | Contacts | "Contacts" | "Add to contacts" |
  | Clear | dimmed | backspace |

  Clear auto-repeats: first after 300 ms, then every 75 ms.
- **Call on an empty field** opens Recent calls; it does not redial.
- **Options menu**, in order:
  - Send *(service codes only)*
  - Call *(non-empty)*
  - Send message
  - Call Handling
  - Touch input
  - Recent calls, Contacts, Speed Dial *(empty field only)*
  - Add to contacts *(non-empty)*
  - Call settings
  - Contact search › On/Off
  - Help, Exit

## 2. Smart dialling, "Enter number or name" (app.phone `phoneuis/easydialing`; matching in contacts PCS `Algorithm1`) [a]
- **Fields searched:** first name, last name and company only. Numbers are **not** searched.
- **Query characters:** digits, `#`, `*` and `+` match by key; any other character matches literally.
- **Matching:**
  - every query word must match the **start** of a different word in some field;
  - comparison is case-insensitive with accent-folding collation;
  - the query is split into words on spaces.
- **0 as a space:** search the query as typed, then search again with every 0 after the leading zeros turned into a space, and merge the results.
  - "Abc0" also searches "Abc";
  - "00" does not search again;
  - "00Zxc" also searches "Zxc".
- **Results:**
  - at most 100;
  - sorted alphabetically in the name-order setting; on a tie, fewer fields sorts first ("Smith" before "Smith Donald");
  - favourites last;
  - the list is anchored at the **bottom**, next to the number field, with nothing selected.
- **Empty or whitespace query:** no search, and the placeholder "Enter number or name" shows.
- **Row:**
  - thumbnail;
  - the name line (first and last name in name order, or company if both are empty);
  - a company line, shown only when the name line is a real name;
  - a favourite star.

  Matched prefixes are highlighted, except in Arabic, Indic and other complex scripts and in mixed-direction text.
- **Interaction:** tap a row to call; long-tap to open the contact. Menu: Open / Call › Voice / Send message / Contact search On-Off.
- **Setting:** "Contact search", default **On** (cenrep `0x200212A0` key 1); thumbnails default on.
- **Key map:**
  - S^3 builds it at runtime from PtiEngine, ordered: the UI language, English, then the other installed languages;
  - when a character sits on two keys, key 1 is dropped;
  - after that, the leftmost position on a key wins;
  - Chinese, Japanese and Korean use a different algorithm.

  **Ours:** static maps for en, ru (E.161: 2 абвг …) and hy (our own; `shortcut:` alphabetical over keys 2–9).

## 3. Call screens and states (app.phone RCL_3) [a][b]
- **States:** Idle, CallSetup, Single, Incoming, Emergency, Alerting, WaitingInSingle, TwoSingles, Conference, plus the combination states (`phonestatedefinitions.h`, `…gsm.h`). Limits: 5 conference participants, 2 active calls.
- **Buttons per state** (`callhandlingui.rss`):

  | State | Buttons |
  |---|---|
  | In call | Hold/Unhold, End call |
  | Two calls | Conference, End active call |
  | Conference | Participants, End call |
  | Conference + single | Join, End active call |
  | Emergency | Loudspeaker/Handset, End call |
  | Incoming | Answer, Reject (or Answer, Silence) |
  | Dialling | Hold, End call |
  | Waiting | Answer, End active call |

  In-call toolbar: Mute/Unmute, Loudspeaker/Handset, Contacts.
- **Single-call menu** (`phoneui.rss:1515`): Unmute, Unhold, Dialer, loudspeaker on/off, Handset, End active call, Hold, Mute, New call, Go to idle, Send DTMF.
- **Active + held menu** adds Swap, Conference, Transfer, End all calls; **active + held + waiting** adds Replace.
- **"End all calls"** is shown with 2 calls when none is ringing, dialling or disconnecting, and always with 3 calls.
- **Caller line**, first that applies (`tphonecallheaderparam.cpp:654-775`):
  1. "Emergency call".
  2. A number with no contact name or company: the number, truncated from the left.
  3. "Private number" or "Payphone".
  4. Otherwise: contact name → network name (CNAP) → company → **"Call"** for a ringing call with unknown identity (S^3 wording) → "Call %N".

  The second line shows the number when there is a name and the number isn't private. A name is shown only when **exactly one** contact matches.
- **Labels:** "Calling", "calling", "waiting", "on hold", "disconnected", "Conference", "Diverted call", "Video call", "on line 2".
- **Call end:** there is **no timer**.
  - The bubble says "disconnected" until the network releases the call.
  - Then the bubble is removed, and the dialer is shown again if it was open; otherwise the idle screen or the previous app.
  - Then the optional summary note: "Call Terminated" / "Time" / the duration (`KSettingsSummaryAfterCall`).
- **Incoming call:**
  - End key short press rejects; long press ends all calls.
  - Silence mutes ring and vibration, then the buttons become Answer/Reject.
  - Soft reject opens an SMS to the caller (needs C9).
  - Any-key answer and auto-redial: not in the source.
- **Emergency** (Qt dialpad notes): the Call key checks the emergency list and dials directly, bypassing the lock and the SIM. Ordinary calls are refused with "Emergency calls only" when not registered or offline.
- **Ringing:**
  - 1 s gap between repeats;
  - 3 s ascending ramp;
  - repeats forever;
  - wait at most 3 s for the tone to start, then play the default tone, then a built-in backup tone;
  - silent mode still vibrates;
  - answering mutes at once;
  - volume 0–10, default 4.

## 4. DTMF postfix (app.phone `cpemessagehandler.cpp:430-660`, `cpeparserphonenumberhandler.cpp`) [a]
- **Allowed characters:** `+0123456789*#pwPW`. Each chunk stops at `+pPwW`.
- **At dial time:** the postfix up to the first `w` or `+` goes to the network with the number. Implement the intended behaviour: RCL_3's loop never advances.
- **After the outgoing call connects,** replay the stored postfix:
  - drop invalid characters;
  - a leading `w`: stop and ask "Send string:\n%U" (Send/Cancel); after Send, continue 0.1 s later;
  - a leading `+`: replace it with the speed-dial entry 2–9. The prompt is "Speed dial number:"; the errors are "Invalid speed dial location" and "Speed dial not assigned";
  - a leading `p`: pause, then continue. The modem layer times the pause; 2.5 s is the GSM convention, not verified here;
  - otherwise: send up to the next stop character.
- **Answering another call** aborts the replay.

## 5. Dial-string classification (phonesrv `telutils/phoneparser`) [a]
**Inputs:** the string, plus Send (Call pressed), InCall and VoipCall. The first parser that matches wins:
1. **IMEI:** exactly `*#06#`, *without* Send.
2. **Emergency** (Send): see §8. It wins in a call too.
3. **Network service code** (Send): see §6. **In-call commands** need InCall and Send:
   - `0`: release held, or reject the waiting call;
   - `1`: end the active call and accept the other;
   - `2`: swap;
   - `3`: join a conference;
   - `4`: explicit transfer;
   - `1X`: end call X;
   - `2X`: hold all calls except X.
4. **SIM code** (no Send):
   - `**04*old*new*new#` PIN change, `**042*` PIN2;
   - `**05*PUK*new*new#` unblock, `**052*` PIN2;
   - PIN length 4–8, PUK exactly 8.
5. **Maker codes** (no Send, ending in `#`):
   - `*#0000#` version;
   - `*#7780#` reset, `*#7370#` deep reset;
   - `*#2820#` BT address, `*#62209526#` WLAN MAC, `*#92702689#` life timer.
6. **Number** (Send):
   - a string containing `p` or `w` is always a number;
   - otherwise, a string of 2+ characters ending in `#` is not a number;
   - a 1–2 character string is not a number, except `1X` out of a call (zero-dial and two-digit dial are off by default);
   - an optional `*31#` prefix shows our number for this call; `#31#` hides it;
   - then an optional `+`, then `0-9*#`, at most 80 characters (81 with `+`);
   - the rest is the DTMF postfix, not validated.
7. **USSD:** anything else with Send. Without Send there is no match.

**Test vectors** (default flags):

| # | Input | Flags | Expected |
|---|---|---|---|
| 1 | `*#06#` | no Send | IMEI |
| 2 | `*#06#` | Send | USSD |
| 3 | `112` | Send, in call | Emergency `112` |
| 4 | `+112` | Send | Emergency `112` |
| 5 | `*31#0401234567` | Send | Number, CLIR suppressed |
| 6 | `#31#+358401234567p123` | Send | Number `+358401234567`, CLIR invoked, DTMF `p123` |
| 7 | `*21*+358401234567#` | Send | SS 21 **register** [num, ""] |
| 8 | `**61*0401234567*11*20#` | Send | SS 61 register [num, 11, 20] |
| 9 | `**61*0401234567**25#` | Send | SS 61 register [num, "", 25] |
| 10 | `**61*0401234567*11*35#` | Send | USSD (bad timer) |
| 11 | `*43#` | Send | SS 43 activate |
| 12 | `*#43#` | Send | SS 43 interrogate |
| 13 | `##002#` | Send | SS 002 erase |
| 14 | `*33*1234#` | Send | SS 33 activate [1234, ""] |
| 15 | `*33*123#` | Send | USSD |
| 16 | `**03*330*1111*2222*2222#` | Send | SS 03 password change |
| 17 | `**04*1234*5678*5678#` | no Send | SIM PIN change |
| 18 | `**04*12*5678*5678#` | no Send | bad PIN code (maker) |
| 19 | `*#7370#` | no Send | maker deep reset |
| 20 | `1` | Send, in call | in-call 1 |
| 21 | `12` | Send, in call | in-call 1X (end call 2) |
| 22 | `12` | Send, idle | Number `12` |
| 23 | `5` | Send, in call | USSD |
| 24 | `0` | Send, idle | USSD |
| 25 | `*100#` | Send | USSD |
| 26 | `*30#` | Send | USSD |

**Quirks:** RCL_3 accepts an empty forward-to number (`**21*#`), leaves the DTMF postfix unvalidated, and in normal-mode emergency matching checks only the first occurrence. For each, decide whether to keep it or follow 3GPP 22.030.

## 6. Network service codes (`CPhoneGsmSsParser.cpp:120-224`) [a]
**Action prefix:**

| Prefix | Action |
|---|---|
| `*` | activate |
| `#` | deactivate |
| `*#` | interrogate |
| `**` | register |
| `##` | erase |

The service code follows, at most 5 digits. An activation that fails to parse is retried as a registration.

**Syntax kinds:**

| id | Name | Accepted |
|---|---|---|
| 1 | no params | `#` |
| 2 | empty or BS | `#`, `**BS#` |
| 3 | number, BS, timer | `*N#`, `*N*BS#`, `*N*BS*T#`, `*N**T#` |
| 4 | number, BS | `*N#`, `*N*BS#` |
| 5 | password, BS | `*PW#`, `*PW*BS#` |
| 6 | group + 3 passwords | `*330*PW*PW*PW#`, `**PW*PW*PW#` |
| 7 | empty or BS | `#`, `*BS#` |

**Codes** (allowed syntax for activate / deactivate / interrogate / register / erase; 0 = not allowed):

| Code | Service | Syntax |
|---|---|---|
| 002 | all forwarding | 2/2/0/3/2 |
| 004 | all conditional forwarding | 2/2/0/3/2 |
| 21 | forward unconditional | 2/2/2/4/2 |
| 61 | forward on no reply | 2/2/2/3/2 |
| 62 | forward when not reachable | 2/2/2/4/2 |
| 67 | forward when busy | 2/2/2/4/2 |
| 33, 331, 332, 35, 351 | barring | 5/5/1/0/0 |
| 330, 333, 353 | barring | deactivate only (5) |
| 43 | call waiting | 7/7/7/0/0 |
| 30, 31, 76, 77, 300 | CLIP, CLIR, COLP, COLR, CNAP | interrogate only (1) |
| 03 | barring password | 6/0/0/6/0 |

**Parameter checks:**
- **Number:** an optional `+`, digits only, at most 38.
- **Basic service:** exactly 2 digits from:
  - 10 all teleservices, 11 voice, 12 data teleservices, 13 fax, 16 SMS, 19 all except SMS;
  - 20 bearer services, 21 async, 22 sync, 24 sync data, 25 async data, 26 packet, 27 PAD;
  - 50–65 and 70–85 PLMN-specific;
  - 89 ALS.
- **Timer:** 5/10/15/20/25/30 s. The default is 30, and a value must be divisible by 5.
- **Password:** exactly 4 digits.
- **Group code:** 330 only.

## 7. Call waiting, caller ID and forwarding behaviour (phonesrv `cellular/telephonysettings`, `PsetNotesUi`) [a][b]
- **Call waiting:**
  - never stored locally; always queried from and set on the network;
  - the basic service defaults to 11 (voice);
  - status is "active" if any entry in the list is active;
  - notes: "Call waiting activated", "Call waiting cancelled", "Call waiting active", "Call waiting not active", "Call waiting not provisioned", "Active for:" with a list.
- **Caller ID setting:**
  - stored values: 0 network default, 1 always hide, 2 always show (`0x101F87E3` key 2);
  - applied per call through the `*31#`/`#31#` prefix;
  - the network's CLIR status maps to ON for "active permanent" or "default restricted", and OFF for "default allowed" or "not provisioned";
  - notes: "Own No. not sent on calling" / "Own No. sent on calling"; CLIP "Number of caller is shown" / "…not shown".
- **Forwarding:**
  - a number starting with `+` has international type;
  - after a query, only the active entries are shown;
  - the 3 most recent forward-to numbers are kept;
  - notes: "Divert activated", "Diverts activated", "Divert cancelled", "Divert not active", "To number: ", "Delay time: ", "%N seconds", "Voice mailbox", "Check network services", "Note: all incoming calls diverted", "Note: you have active diverts".
- **Network errors to notes:**

  | Network error | Note |
  |---|---|
  | subscription violation | "Barring operation not successful. Contact your service provider" |
  | illegal or barred | not allowed |
  | system failure | result unknown |
  | resources or bad data | request rejected |
  | wrong password | "Password error" |
  | password attempts exceeded | "Password blocked" |
  | no service | no service |
  | activation data lost | "Check network services" |
  | anything else | not done |

  The texts for "not allowed", "result unknown", "request rejected", "no service" and "not done" are in `avkon.loc`; we write our own.
- **Basic-service names:** 11 "Voice calls", 13 "Fax", 16 "Messages", 19 "Voice calls and fax", 20 "Data services", 26 "Packet data", 89 "Alternate line services".

## 8. Emergency numbers (phonesrv `phoneclientserver/EnPolicy/Src/SosEnPolicy/CSosEmergencyNumberPolicyHandler.cpp`, `CSosEnPolicyENListHandler.cpp`, `phoneclient/Src/EmergencyNumber/EmergencyNumber_Aiw/RPhCltEmergencyCall.cpp`) [a]
- **The list:**
  1. 112 and 911, always present.
  2. The SIM's EF_ECC list when the SIM can be read; otherwise the fallback 999, 000, 08, 110, 118, 119.
  3. The product's own numbers from cenrep.

  Edge case: a non-empty product list wipes the fallback.
- **Before matching:**
  - strip a `*31#` or `#31#` prefix;
  - cut the string at the first `p` or `w`;
  - strip one `+`;
  - a non-digit means not emergency;
  - more than 6 digits is an error.
  
  So `+112`, `*31#112` and `112p1` all match; `112#` doesn't.
- **Normal mode** (used by the dialer): exact match, bounded by spaces in the list.
- **Advanced mode:** the dialled string *ends with* an entry; the longest entry wins and replaces the dialled string.
- **Empty input:** dials 112.

## 9. Voicemail number (phonesrv `engines/vmbxengine`) [a][b]
- **Lookup:**
  1. the SIM: MBI, then MBDN, falling back to the CPHS VMBX file;
  2. else the phone's own value (cenrep `0x101F874F` key 1);
  3. an emergency number is rejected from either source;
  4. the number found is synced to the other store.
- **Save:** with a writable SIM, ask "Save number to:" with the choices "SIM card" and "Phone Memory". The SIM length limit is 20, 40 or 48.
- **Validation:**
  - at least 3 characters;
  - skip any leading `#`, `*` or space, then an optional `+`;
  - 2–40 digits;
  - no spaces after the `+`.
  
  The dialog takes at most 48 characters.
- **Strings:**
  - "Define voice mailbox number:"
  - "Invalid phone number."
  - "Voice mailbox number not defined."
  - "Call to:"
  - "Voice mailbox"
  - "Voice mailbox number from SIM taken into use"
  - "Voicemail number not provisioned"
  - "Calling voicemail" (speeddial)

## 10. USSD (phonesrv `phoneclient/…/UssdWrapper`, `phoneserver/…/Ussd`) [a]
For later (C9 or C11). We can carry this out with QMI VOICE `ORIG_USSD` 0x3a.
- **Sending:**
  - DCS defaults to 0x0F (0x00 also means 0x0F);
  - at most 182 characters, 160 octets once packed;
  - packed as GSM 7-bit, least-significant bit first;
  - if 7 bits are left free in the last octet, append CR padding.
- **Message types:** MO Request normally; MO Reply while the network's reply timer runs. The timer is 5 min and starts on an MT Request.
- **Notifications:** an MT Notify is acked with an empty MO-Ack.
- **Decoding:**
  - 0x10: 7-bit with a 2–3 octet language prefix;
  - 0x11: UCS2;
  - `01xxxxxx`: 8-bit or UCS2 by the class bits; SIM-specific messages are dropped;
  - `1111x1xx`: 8-bit;
  - anything else: 7-bit.
- **Display:** an empty text means "Done". Show the query 0.5 s after it arrives. The softkeys are Answer/Exit for a request and Exit for a notify.
- **Closing** sends a release. A release from the network shows "Done" if a send was pending.

## 11. Call log / Recents (contacts `logsui`) [a][b]
- **Lists:**
  - recent lists: Received = 1, Dialled = 2, Missed = 3;
  - Log view filters: all, outgoing, incoming, voice, messages, packet, data, WLAN, one person;
  - directions: In, Out, Missed, plus the alternate-line variants.
- **Duplicates:** the log engine merges repeated calls from one number into a single row. The missed list shows "(N)" when there are N unread duplicates.
- **Marking missed calls read:**
  - opening the Missed view marks the call and its duplicates read and resets the new-missed counter;
  - sending a message from a missed row also marks it read;
  - switching logging on or off resets the counter too.
- **A row:**
  - icon: the number type (mobile, landline, fax, video, …);
  - line 1, first available: "Emergency call", the contact name, "Private number", "Payphone call", "Operator Service", the number truncated from the left, or "Unknown caller";
  - line 2: the date and the time.
  
  Received and dialled calls are always treated as read.
- **Detail view rows:**
  - Direction (In/Out/Missed);
  - Type (Voice/Video/…);
  - Duration: shown for outgoing calls even when zero, never for missed;
  - Tel no: hidden for emergency calls.
- **Menus:**
  - Recent: Call, Send message, Open phonebook, Save to Contacts, Use number › Prepend/Copy, Delete, Clear list, Settings;
  - Detail: the same without Delete.
- **Settings:**
  - Log length: No log / 1 day / 10 days / 30 days (0, 86400, 864000, 2592000 s), default **30 days**.
  - Choosing No log asks "The log will not be kept - continue?"
  - Show call duration defaults to **off**.
  - Total log size 1000 events. The per-list cap belongs to the log engine; believed to be 20, not verified.
- **Missed-call indicator:** "1 missed call" / "%N missed calls"; tapping it opens Missed.
- **Timers:**
  - Last, Dialled, Received, All (= Dialled + Received), as hh:mm:ss;
  - "Clear Timers" asks for the security code and is refused during a call.
- **Strings** (`logs.loc`, `stm.loc`):
  - "Recent calls", "Missed calls", "Received calls", "Dialled calls";
  - "No Missed calls" / "No Received calls" / "No Dialled calls";
  - "Erase number\nfrom list?", "Erase all missed\ncalls?" (and received, dialled);
  - "Clear list", "Use number", "Prepend", "Copy", "Number copied\nto clipboard!", "Save to Contacts";
  - "Direction", "Type", "Duration", "Tel no", "In", "Out", "Missed", "Voice";
  - "Log length", "No log", "1 day", "10 days", "30 days", "Show call duration";
  - "Private number", "Unknown caller", "Payphone call", "Emergency call", "%N New calls" / "1 New call";
  - "Call timers", "Last Call Timer", "Dialled Calls Timer", "Received Calls Timer", "All Calls Timer", "Clear Timers".

## 12. Speed dial (contacts `phonebookui/Speeddial`, `cntsrv`) [a][b]
- **Storage:** slots 1–9, a number of at most 64 characters, stored as (contact id, number). Key 1 is always voicemail. Key 2 holds the video mailbox only if one is configured.
- **Cell menus:**
  - assigned: Call, Change, Remove, View number, Write message;
  - empty: Assign;
  - voicemail: Call.
- **Assign flow:** pick a contact and number; any previous assignment is replaced silently; the note says "Number assigned for key %N". Remove has no confirmation in practice.
- **Cell content:**
  - first name and last name on two lines;
  - else the company;
  - else the number;
  - plus the thumbnail and a number-type icon.
- **Strings:**
  - "Assign", "Change", "Remove", "View number", "Key %N:", "Voice mail", "Speed dial", "Calling voicemail";
  - "No Speed dial assigned. Assign now?", "Number assigned for key %N";
  - "Remove speed dial %0U from key %1N?", "%U already assigned for this key. Replace?";
  - "One-Key-Calling from Idle is set off. Would you like to turn it on?"

## 13. Contacts (contacts `Phonebook2`, `VirtualPhonebook`) [a][b]
- **New-contact template:** last name, first name, job title, company, general phone, mobile, video number, email, ringing tone, image. The N8 screenshot shows First, Last, Mobile, Telephone, Mail, Address, Image, Ringtone, Video call.
- **Display order:**
  1. prefix, first or last name, middle name, suffix, nickname;
  2. mobile, mobile (home), mobile (work), general, home, work;
  3. email, email (home), email (work);
  4. addresses;
  5. company, job;
  6. URL, date, note.
- **Max lengths:** names 50; prefix and suffix 10; phone 48; email 150; SIP 100; URL 1000; note 1000; postal code 20.
- **Field counts:** names, company and date appear once per contact; phones, emails and notes can repeat. Names, ringing tone and image cannot be removed.
- **List:**
  - My Card at the top: "Create My Card" until one exists, then "My Card";
  - favourites sort first;
  - "Add Favorities" item: 0 never, 1 until the first favourite exists, 2 always (default).
  
  Empty-list texts: "No contacts", "(Select new contact from Options to add contacts)".
- **Name and sort:**
  - sort by favourite, then last+first or first+last (setting), then company;
  - the title uses the first two non-empty name fields, else the company, else "Unnamed";
  - names are separated by a space;
  - non-printing characters become spaces;
  - the setting "Display Names" offers "Last name First name" / "First name Last name". The English default is **First Last**.
- **Contact card actions:**
  - Voice call, Message, E-mail, Video call, Edit, Delete;
  - Use number › Prepend/Copy, "Copy number";
  - Defaults (call, SMS, email; "Set as default", "(no default)");
  - Assign or Remove speed dial;
  - Send as business card ("Without picture" / "With picture");
  - Ringing tone ("According to profile"), Add image.
  
  Several numbers show "%N numbers".
- **Delete confirmations:**
  - one contact: "Delete?\n%U";
  - several: "Delete?\n%N marked entries", with the progress note "Deleting entries";
  - one field: "Delete\ndetail %U?";
  - My Card: "Delete all data stored in My Card?"
- **Editor strings:**
  - field actions: "Add field", "Delete field", "Edit Label", "Label:";
  - after saving: "New contact created", "Contact updated", "Contact exists. Save duplicate? %U";
  - limits: "Number too long", "Name too long".
- **Labels:**
  - "last name", "first name", "Middle name", "prefix", "suffix";
  - "general", "home", "work", "mobile", "mobile (home)", "mobile (work)";
  - "fax", "fax (home)", "fax (work)", "pager", "video no.";
  - "email", "email (home)", "email (work)", "address", "URL";
  - "job", "company", "Department", "date", "Anniversary", "note", "tone", "Image".
- **Settings:**
  - "Contacts shown from" and "Default saving memory": Phone or SIM, default phone;
  - "Display Names";
  - "Predictive search" On/Off.
  
  We offer Phone memory only until a SIM phonebook (QMI PBM) exists.
- **Number matching for the caller's name** (`cpplcommaddrtable.cpp`, `cntmatchlog`):
  - strip every non-digit, including `+`;
  - compare the last 7 digits, plus up to 8 more when both numbers have them (best-match mode: compare up to the shorter length, skipping leading zeros);
  - the name is used only when **exactly one** contact matches;
  - match length 7 (`KTelMatchDigits`).
- **First-boot contacts** (predefinedcontacts): import every `*.vcf` (and XML) from a configured folder once, and keep the ids so they can be replaced later. We could use this for an "import from E:" on first boot.

## 14. vCard mapping (`VPbkEngFieldTypes.rss`, `Vpbkvcardeng.rss`) [a]
- **Names:**
  - `N` = family;given;middle;prefix;suffix; family is also written as `FN`;
  - `X-NICKNAME`;
  - `SOUND` for Japanese name readings.
- **Phones:**

  | Our field | vCard |
  |---|---|
  | general | `TEL` with none of WORK, HOME, FAX, PAGER, CELL, VIDEO, CAR |
  | home / work | `TEL;HOME` / `TEL;WORK` |
  | mobile | `TEL;CELL[;HOME\|;WORK]` |
  | video | `TEL;VIDEO[…]` |
  | fax | `TEL;FAX[…]` |
  | pager | `TEL;PAGER` |
  | car | `TEL;CAR` |
  | assistant | `X-ASSISTANT-TEL` |
- **Internet:**
  - `X-SIP;VOIP|POC|SWIS`;
  - `EMAIL;INTERNET[;HOME|;WORK]`;
  - `URL[…]`.
- **Addresses:** `ADR` with 7 parts (PO box, extended, street, city, region, postal code, country); `LABEL`.
- **Other properties:**
  - `TITLE`, `ORG` (company;department);
  - `BDAY`, `X-ANNIVERSARY`, `NOTE`;
  - `PHOTO` (`ENCODING=BASE64`);
  - `X-ASSISTANT`, `X-SPOUSE`, `X-CHILDREN`, `X-WV-ID`, `X-IMPP`, `X-CLASS`;
  - `X-FAVORITE` (dropped when sending by Bluetooth or IR);
  - `REV` (the modification time in UTC).
- **Never exported:** DTMF, ringtone, the caller image and text.
- **Export order:** N, SOUND, ORG, TITLE, nickname, then `TEL;CELL` before plain `TEL`.
- **Encoding:** vCard 2.1. The charset and quoted-printable handling is in the platform's versit library, not here; N8 files use `CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE`.

## 15. Not found, to specify ourselves
- **Call settings items and defaults.** The GS plugin is missing. Use the N8 screenshots as the spec:

  | Item | Default |
  |---|---|
  | Send my caller ID | Set by network |
  | Call waiting | network |
  | Message text | "Sorry, I'll call later" (from the N8) |
  | Show call duration | No |
  | Summary after call | Off |
  | Speed dialling | — |
  | Contact search | On |
  | Log duration | 30 days |
  | Name display | First Last |

- **Missing values:** the one-key-dialling default, the auto-redial and any-key-answer behaviour, and the recent-list cap (we pick 20 per list).
- **Missing text:** the shared `avkon.loc` notes ("Done", "Not done", "Request not confirmed", "Not allowed") and the status-bar network texts.
