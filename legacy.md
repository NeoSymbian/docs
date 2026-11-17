# Legacy apps: old S60 apps inside neoui

**Goal:** old, unmodified Symbian S60 apps run inside neoui. These are 3rd and 5th edition `.sis` packages: first X-plore 1.64 and Frozen Bubble, later a wider corpus.

**What unmodified means:** the app's executables, DLLs and resources stay byte for byte the same. Compatibility comes only from the system's implementations, configuration and documented screen/input profiles.

The design was reviewed on 2026-11-14 with Codex (gpt-6-astra) and adopted by the owner.

## Architecture

```
unmodified S60 app processes
  -> stock Avkon / Uikon / CONE / WS32
  -> one shared stock window server (guest mode) -> the guest screen (a global chunk)
  -> LEGACY.EXE (supervisor + presentation) <-> neoui (display, input, launcher)
```

- **One shared guest environment.** There is one window-server instance, and each app keeps its own process, windows and `RWsSession`.
  - Notes and dialogs from other processes (EIKSRV, AknCapServer) appear on the same desktop.
  - Task switching works as it did on a 2010 phone.
  - The guest stays up while any legacy app runs; closing an app never ends the window server.
- **Not chosen:**
  - A neoui-served window server ("NeoWserv") would reimplement buffered drawing, redraw, plugins and direct screen access. It is deferred.
  - A window server per app would break the shared named servers that clients expect.
- **neoui** owns the physical display, input, the system keyboard, the launcher and the switcher.
- **LEGACY.EXE** is the supervisor:
  - starts the guest;
  - lists the installed apps through AppArc;
  - launches apps by UID;
  - presents the guest screen and turns touches and keys into raw window-server events.
- **Guest mode** lives in the graphics fork:
  - `scnew.cpp` draws into the `NeoUiLegacy` chunk with the geometry from its header;
  - `WSTOP.CPP` and `EVENT.CPP` take no display or event-hook ownership.
  - Mode is currently detected from the chunk's existence; an explicit handshake comes later.

## Where things live

| Piece | Repo |
|---|---|
| LEGACY.EXE, the legacy component list, the `.sis`/icon/skin tools, `sis.lock` | [legacy](https://github.com/NeoSymbian/legacy). `build` pins it as `src/legacy` and merges its `components.py`. |
| Fixes to Symbian code | The fork that owns the file, on `main`: graphics (guest wserv), classicui (Avkon/Uikon), appsupport (AppArc, view server), uiresources (icons, skins), cellularsrv (ETel), svgt (SVG icons). |
| C++ run time of RVCT-built binaries (`drtaeabi`, `dfpaeabi`) | kernel `kernel/eka/compsupp/gcce` |
| The launcher protocol (1.6 `ENTRY`, `FRONT`, `Entry` event) and the Old apps grid | neoui |
| Telephony for old apps (ETel TSY over MODEMD) | telephony |
| ELF/E32 emission, unwind tables, ROM/ROFS, the component loader | build |

## Compatibility contract

- **A missing library gets a typed implementation with a specified contract,** never a blanket success. It:
  - initializes its outputs;
  - completes or cancels each asynchronous request exactly once;
  - returns documented errors for what it can't do.

  It never reports "alarm scheduled", "audio played" or "position obtained" when nothing happened.
- **Panic stubs are a stop-gap.** The generated EUSRNIMP stubs in the legacy component list only get apps past start-up. Each one is replaced by:
  - the real 2010 source, where the release has it (`estlib` does);
  - or a typed provider;
  - or a bridge to a native service (MODEMD, NeoNet, neoui).
- **Finding what's missing is static first.** `romcheck` and `sis.py check` report:
  - missing DLLs;
  - ordinals past an export table;
  - imports that land on panic stubs;
  - opaque payloads, reported as "unknown".

  Runtime loader and ECom traces cover what the static scan can't see.

## The Old apps launcher (protocol 1.6)

1. **Listing:**
   - neoui starts LEGACY in the background when the Old apps screen opens.
   - LEGACY lists AppArc's apps, skipping hidden ones.
   - Avkon's icon server rasterizes each app's icon from its MIF (SVG) or MBM.
   - LEGACY sends each app as `ENTRY {uid, caption, icon}`. With no icon, neoui shows a generic tile.
2. **Launching:**
   - A tap sends `Entry(uid)`.
   - LEGACY starts the app through AppArc, claims Back and calls `FRONT(1)`.
   - Back or the app's exit closes that app and calls `FRONT(0)`, which shows the grid again.

## Finding the failing call (the failure trace)

An old app usually dies with a bare reason (`Killed -1`), and RVCT apps may ship encrypted code (X-plore loads its
program from an encrypted `app.bin`), so the failing call is found at run time:
- **The switch** is debug-mask word 3 bit 31 (`KNEOLEGACYTRACE`). LEGACY.EXE sets it when the old-app runtime starts,
  so boot stays quiet.
- **What it logs:** every process except ours (SID 0xE…) writes `neotrace:` lines to the debug log:
  - leaves (`User::Leave`, `LeaveIfError`, `LeaveIfNull`, `LeaveNoMemory`), with the caller's address;
  - `User::Exit` with an error, and failed `RLibrary::Lookup` calls (DLL and ordinal) (euser `us_trp.cpp`);
  - failed file-server requests, with the function number and file name, and failed loader requests, with the file
    name (F32 `sf_request.cpp`, `sf_ldr.cpp`).
- **Mapping an address:** the core ROM has fixed addresses (`ROFS_CORE='\.dll$'`), so a caller maps to an image and
  function through the ROM map plus `addr2line` on the image's ELF.
- **Reading it:** the last leaves before the exit name the failing call.

It opened up both test apps:

| Exit | Traced to | Fix |
|---|---|---|
| `Killed -1` | `CTelephonyFunctions::ConstructL`: `RTelServer::Connect`, no ETel server | cellularsrv: a phone-less `CTelephony` (the phone identity is answered; everything else is `KErrNotSupported`) |
| `-20` | `CPtiDefaultCore::InitializeL`: no key-map data plugin | legacy: `PtiKeymappings_ITUT_01` (English) |
| "System error." note | every app loading AknFep, the default FEP in `EIKPRIV.RSS`, not built | classicui: no default FEP until AknFep is built |
| Frozen Bubble: `KERN-EXEC 3` in `CActive::Cancel` | foreground lost before its first idle callback had made its game timer: the first app started AknCapServer, EikSrv and the skin server, whose windows took the focus | legacy: LEGACY.EXE starts AknCapServer first (`RAknUiServer::StartAknCapserverL`, as the starter does) |
| Frozen Bubble: not loadable, then `EUSRNIMP` and `E32USER-CBase 47` in its mixer thread | `mediaclientaudiostream.dll` missing; then DevSound's proxy on panic stubs; then `CMMFDevSound::NewL` leaving `KErrNotFound` (no audio server) | legacy: the MMF audio clients; os.mmaudio: `CMdaAudioOutputStream` constructs without a server, and its open reports `KErrNotSupported` |

A RAM-loaded EXE also gets 64 KB of stack at least (the F32 loader). RVCT's default is 8 KB, and our GCC-built Avkon
needs more than that: Frozen Bubble overflowed in `CEikStatusPaneLayoutTree::AknLayoutRect`.

**Two runtime rules came from the phone:**
- **The guest desktop is persistent.** The guest window server and Avkon's system servers (AknCapServer, EikSrv,
  skins) stay up when LEGACY closes, and a later LEGACY reuses them.
  - Taken down, the system-critical AknCapServer panicked CONE 9 and faulted the kernel: the phone reset when Old
    apps was closed from Open apps.
  - Killed first, AknCapServer could not start again (`KErrAlreadyExists`).
- **Old apps run SMP-unsafe.** Every image we build carries `KImageSMPSafe`, and the kernel runs
  `EKernelConfigSMPUnsafeCompat`, as Symbian^3 did, so a process that loads an image without the flag (an old `.sis`
  app) runs one CPU at a time.
  - Frozen Bubble's realtime mixer thread publishes a pointer its creator uses right after `Resume`, with no
    handshake.
  - On a single-core phone the mixer always ran first; on the Pixel's 8 cores the creator read NULL.

## Key pads (S60 apps take keys, not touch)

S60 3rd-edition apps ignore taps: Frozen Bubble and X-plore's dialogs want the phone's keys. LEGACY draws an
on-screen key pad under the old app (legacy `host/pad.cpp`), designed on the owner's canvas (Old apps · key pads,
pad states, console, settings; the spec sheets "Pad keys", "Touch & hold", "Pad memory" and "Pad stages").
- **Pads:** a strip of Nav · Game · 123 · Abc · Hide · ⟳ over the pad.
  - **Navigator:** the softkeys, the arrows, OK, Call, End, C and Edit (the S60 layout).
  - **Gamepad:** a d-pad with diagonals, A and B (Settings: arrows or the number keys; A = OK or 5; B = the right
    softkey, 0 or #).
  - **Number:** 0-9, `*` and `#` with their letters.
  - **Abc:** neoui's system keyboard (every language) types into the app's editor as character key events
    (`RWsSession::SimulateKeyEvent`), so no FEP is needed.
  - **Hidden:** the app on the whole area; a keyboard button brings the pad back.
  - **The console:** the Gamepad on its side (⟳): a full-screen page, the canvas turned a quarter, the app in the
    middle, the d-pad and A/B either side (left-handed swaps them).
- **Keys:** raw scan codes (`e32keys.h`: the softkeys `EStdKeyDevice0/1`, OK `EStdKeyDevice3`, Call/End
  `EStdKeyYes/No`, C `EStdKeyBackspace`, Edit `EStdKeyLeftShift`, the arrows, the digits, `*` and `#`), held while the
  finger is down so the guest window server repeats them. A one-shot key (a softkey, Call, End, C, Edit) fires on a
  lift inside, so sliding off it presses nothing.
- **Fingers:** each contact has one owner, chosen at the press (the guest, the d-pad, a button, the strip). Sliding
  on the d-pad changes direction; a count per scan code means two fingers on one key send one down and one up.
  Everything held is released when the app goes to the background, closes, the pad changes, the screen goes off
  (neoui `InputReset`), and once at LEGACY's start (the guest desktop outlives a crashed LEGACY).
- **Multi-touch:** the bonito touch driver reports up to five fingers, each its pointer number; neoui gives finger 0
  to the shell and the gestures, and another finger to the app it presses in, so a game can move and fire at once.
- **Memory and Settings:** each app's pad is the setting `legacy.<uid>.pad` (mode, last pad, orientation, its own A
  and B, the reset epoch). A first open takes Settings' default pad, else a UID table (Frozen Bubble: the Gamepad),
  else AppArc's "Games" group (the Gamepad), else the Navigator, and says so in a toast. Settings → Old apps holds
  key vibration and its strength (neoui `HAPTIC`), the default pad, the Gamepad's directions, A, B, left-handed,
  games in the console, and Reset remembered pads (`legacy.pad.*`).
- **The page:** while an old app is in front LEGACY declares a page (neoui protocol 1.10), so the shell draws no
  header over it: the pad's softkeys replace ⋮.

## Milestones

| | Work | Done when |
|---|---|---|
| **L0** | Ownership and inventory: the legacy repo, the run time in compsupp, the manifest loading, honest audit reports. | The same ROM before and after; build owns no legacy runtime. |
| **L0.5** | The AppArc launcher: protocol 1.6, the Old apps grid, real icons (SVG-T engine). | Old apps shows X-plore and Frozen Bubble with their icons; a tap starts the app in the guest. |
| **L1** | A stable runtime and desktop: guest handshake, persistent supervisor, AknCapServer CONE 9 found from evidence, the Avkon service closure. | A minimal Avkon app starts again and again; notes and menus work; a guest failure leaves neoui usable. |
| **L2** | Two usable apps: Frozen Bubble's `mediaclientaudiostream`, X-plore's dynamic loads, typed providers, controls, basic text. | **X-plore:** lists, copies and renames files, and keeps its settings. **Frozen Bubble:** a full game with held controls. Whether audio works is recorded either way. |
| **L3** | Shell integration: damage instead of the 10 Hz full copy, frame ownership, a task protocol, several apps at once. | Two apps keep running while switching; no idle full-frame copies. |
| **L4** | Runtime SIS install: the SWI engine from mw.appinstall and a neoui install screen. | Install from C: without a ROM build; the launcher updates; uninstall and upgrade work. |
| **L5** | Breadth: screen modes and rotation, a FEP bridge to the neoui keyboard, media, a corpus of apps. | Per-app feature results published. |

Each step is tested on QEMU (Syborg, watched over VNC with `neo live`), then on the Pixel.

**Status (2026-11-17):**
- L0 and L0.5 are done.
- L2 has started, on QEMU and on the Pixel:
  - X-plore 1.64 opens its file browser, with C: and E: on the phone, and browses with the Navigator pad.
  - Frozen Bubble is played with the Gamepad (QEMU: its key setup, a game, held aiming, firing), in portrait and in
    the console; silent: there is no audio server yet.
  - Closing and reopening Old apps is stable.
- Next:
  - AknFep (multi-tap and T9 on the Number pad);
  - an audio server.

## Open decisions (owner)

- **Audio:** is audible sound required for L2?
- **Unsigned packages:** how to treat unsigned, expired and privileged packages (a permissive development policy is the default).
- **PIM data:** do legacy contacts, calendar and messages share the native stores or keep their own?
- **Guest failure:** after a guest failure, the user chooses whether to restart; unsaved work is never silently relaunched.
