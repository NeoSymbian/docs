<!-- SPDX-License-Identifier: Apache-2.0 -->
# Files: the file manager (NEOFILES v2)

Written 2026-11-17. This is the implementation proposal for the Files app: a new `NeoSymbian/files` repo, every screen
of the design canvas's Files page, the platform work it needs, and the phases FA0–FA13. Today's app (R8) is built and,
since FA0, lives in [NeoSymbian/files](https://github.com/NeoSymbian/files). FA1–FA5 are built (2026-11-18/19, see
[Status](#status-2026-11-19)); FA6–FA13 are not.

**The design:** the canvas's Files page, https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#page-766d8f9d8c3a
(60 `files2-*` boards, decisions F01–F11, published 2026-11-17). Each phase below links to its boards. The prototype is
[`prototype`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#play-ca89c8d335ba). The canvas is private: the links open for the owner and for whoever it is shared with.

## Decisions

**From the canvas (owner, 2026-11-17):**
- **F01 Footer tabs:** Browse · Recent · Types, icons only; the root header is `[Files · search · ⋮]`.
- **F02 File icons:** a page tile with a coloured type badge, one colour per family; images and videos show
  thumbnails; folders are amber, special folders carry a badge.
- **F03 Built-in viewers** for every family, header `[← name · share · edit (if editable) · ⋮]`; ⋮ → Open with.
- **F04 Editors:** text and code, Markdown with Preview, CSV/TSV as a table, images (rotate, crop, resize, saved as a
  copy), vCard and iCal as forms.
- **F05 Folder page:** `[← Folder · search · ⋮]`, a breadcrumb chip row, list or 3-column grid.
- **F06 Copy and move:** a paste bar above the footer ("2 files to move · Cancel · Move here"); progress as a toast
  and a shade entry; a name clash asks Replace / Keep both / Skip.
- **F07 Extras:** Details, Open with and Share sheets; archives (browse, extract, compress); search with filters;
  Recycle bin; Free up space.
- **F08** The old boards are replaced; the Shell page's Files patterns are redrawn.
- **F09 The types:** 55 extensions in 10 families, 24 editable (the type matrix: [`spec-types`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-addb580badcb)).
- **F10** Every board is tagged As built / Planned / Proposed.
- **F11 Code editor:** syntax colours, line numbers, wrap, find and replace, a code-key row above the keyboard.

**For the implementation (owner, 2026-11-17):**
- **A repo of its own**, `NeoSymbian/files`, and its own UID block: `NEOFILES.EXE` becomes **0xE0006001**. Files keeps
  no private data today, so nothing migrates.
- **Heavy formats are ours.** Audio, documents and video viewers are built on crates.io crates inside Files, each in
  its own phase, the platform work they need included.
- **Decoders are shareable crates** (Apache) in the files repo; Photos and Music pin them by git rev later.
- **The Recycle bin is per drive:** `X:\.trash\` with an index. This corrects F07's `C:\Trash\`: moving a 1 GB file
  from E: to C: would be a full copy and could fill the 8 GB C:.

## The app today (R8)

Built 2026-11-06 in neoui (rust-integration.md R8: `symbian/apps/files`, model `crates/neoui-files`), on the kit since
2026-11-17, moved by FA0 to NeoSymbian/files: `symbian/app` (GPL), `crates/files-ui` (GPL) and `crates/files-core`
(Apache, `no_std`, 9 host tests); `NEOFILES.EXE` is now 0xE0006001 (it was 0xE0002004).
- **Screens:** drive cards with usage bars (ROM drives with a lock); folders, sorted, with size and date; pull to
  refresh; selection by long press with Rename (one row) and Delete; New folder; a text viewer (UTF-8, or UTF-16LE
  with a BOM, first 64 KB). Other types get "No viewer for …".
- **Platform calls:** `e32::fs` (`Fs::connect`, `drives`, `volume`, `read_dir`, `mkdir`, `rmdir`, `delete`, `rename`,
  `File::open`, `read_at`); `neoapp` PAGE, QUERY, NOTE, KEYBOARD, `kit_back!`.
- **Shell:** the key `files` in `neoui/symbian/src/host.rs` `APPS`, the menu and home icons, the title in `shell.slint`.
  The shell resolves the EXE by name, so moving the code changes nothing there.
- **CI:** neoui's `syborg.yml` clones NeoSymbian/files, builds `libneofiles.a`, then taps through drives,
  `Z:\Sys\Bin`, `estart.txt`, makes and deletes `C:\neo\` and makes `C:\дом\`. The files repo's own CI runs the
  model's tests and snapshots today's five screens (`snapshots/files-*.png`).
- **Speed:** the open animation averages 20.5 ms a frame, over the 16.7 ms budget ([smooth-ui.md](smooth-ui.md)).

## The repo

Phone's layout (two workspaces: host and device), with firmer boundaries around the file system, the formats and the
device glue (reviewed with Codex, 2026-11-17).

```
files/                       host workspace, Cargo.lock
├── crates/
│   ├── files-core/          navigation, tabs, selection, paste state: events in, effects out (from neoui-files)
│   ├── neo-fs/              paths, metadata, the Fs and byte-I/O traits; an in-memory fake with failure injection
│   ├── files-ops/           the job engine: copy, move, trash, recursive delete, search, index
│   ├── neo-view/            FileType ids, probing, the viewer and editor registry
│   ├── neo-format-text/     text, code, Markdown, CSV: models, highlighting, layout, edit commands
│   ├── neo-format-image/    image models, thumbnails, crop/rotate/resize
│   ├── neo-format-archive/  zip, gzip, tar
│   ├── neo-format-pim/      vCard, iCalendar
│   ├── neo-format-inspect/  fonts, certificates, app packages, hex
│   ├── neo-format-document/ EPUB, Office, RTF, PDF
│   ├── neo-format-media/    audio and video containers, decoders
│   ├── neo-codec-*/         only where no usable no_std crate exists
│   └── files-ui/            Slint screens, one per canvas board; snapshot tests
├── tests/fixtures/          small licensed sample files, corrupt ones included
├── snapshots/               files2-*.png baselines
└── symbian/                 device workspace, Cargo.lock, rust-toolchain.toml, .cargo/config.toml
    ├── fs-e32/              neo-fs over e32::fs
    ├── app/                 the neofiles staticlib: protocol, workers
    └── exes.txt             NEOFILES.EXE 0xE0006001 libneofiles.a
```

| Path | What | Licence |
|---|---|---|
| `crates/files-core`, `neo-fs`, `files-ops`, `neo-view`, `neo-format-*`, `neo-codec-*` | portable logic, `no_std` + alloc, no e32, no Slint; tested on the host | Apache-2.0 |
| `crates/files-ui` | Slint screens (`neoui_kit::compile`), snapshot tests | GPL-3.0 |
| `symbian/fs-e32`, `symbian/app` | device glue | GPL-3.0 |

- **Pins:** the same as neoui's `symbian/Cargo.toml`, one e32 and one Slint per ROM: e32 by rev (feature
  `critical-section`), `neoui-kit`/`neoui-proto`/`neoapp` from one neoui rev, `slint = "=1.18.1"` (`compat-1-2`,
  `unsafe-single-threaded`, `libm`, `renderer-software`), `nightly-2026-10-20`, the `cargo arm` alias. CI checks the
  parity with neoui.
- **Features** choose what ships, in `symbian/app`: `decode-jpeg`, `encode-png`, `archive-write`, `edit-text`, `pdf`,
  `audio-*`… Portable crates default to little. The registry is static, so a viewer not enabled is not linked.
- **Threads:** only the UI thread touches Slint. Workers (copy, search, thumbnails, decode) each open their own `Fs`
  session (a session is bound to its thread) and talk through e32 mutex queues; no compare-and-swap (ARMv5TE).
- **CI:** host: `cargo fmt --check`, `clippy -D warnings`, `cargo test --locked`, every board's snapshot compared
  with its baseline (diffs uploaded); arm: `cargo arm --locked`, the EXE size and heap budget. neoui's Syborg CI clones
  the repo as it clones phone, and keeps today's Files taps.
- **Data:** `C:\private\e0006001\` holds the recent list, the type index, the thumbnail cache and the settings;
  `X:\.trash\` on each writable drive holds deleted files and `index.dat`.

## How it works

- **The file system contract (`neo-fs`)** sits under everything: directory cursors, `u64` offsets, partial reads and
  writes, flush, replace, drive capabilities (removable, read-only, shared over USB), typed errors. The host fake
  injects failures (full disk, a drive gone mid-copy).
- **Jobs (`files-ops`)** run in bounded, cancellable steps on a worker:
  - **copy** writes to a temporary name in the destination, then renames it into place;
  - **move** on one drive is a rename; across drives it is a copy, and the source is deleted only after the copy
    commits;
  - **delete** moves into the drive's `.trash` with a journal entry (original path, date, state), so a cut power
    leaves nothing half-done; **empty bin** and recursive delete walk depth-first;
  - one place checks path identity, copying into itself, clashes and archive paths that escape their folder.
- **Viewers (`neo-view`):** probe the first bytes (magic numbers), then the members of a zip (EPUB, docx, xlsx, odt
  are zips), then the extension. Each entry says what it offers: metadata, view, edit, encode. Unknown files open
  in the hex view.
- **Memory:** the Rust heap is one 64 MB chunk (`e32/src/heap.rs`), first-fit, and it only grows. A 12 MP photo is
  36 MB as RGB, so a JPEG or WebP decodes at full size into a chunk of its own (created for it, closed after the
  shrink) and never enters the heap; documents lay out a page at a time.
- **Speed:** the kernel saves FP/NEON for apps since WB1 (2026-11-17, KRN-019), but our Rust still builds for
  ARMv5TE soft-float: codecs speed up with the ARMv7/NEON build (smooth-ui S4's user-side part). Each media phase
  measures before it ships.

## Platform gaps

What Files needs that doesn't exist, who owns the fix, and the phase that needs it.

| Capability | Today | Missing | Owner | Phase |
|---|---|---|---|---|
| Change notifications (refresh when a folder changes) | F32 has them (`sf_notify.cpp`) | the client: `EFsNotifyChange`/`Ex` in `e32::fs` | e32-rs | FA2 |
| Attributes on folders and by path | `File::set_att` on open files only | `EFsSetEntry` | e32-rs | FA2 |
| Copy, cross-drive move, recursive delete | `read_at64`, `write_at64`, `set_size64`, `rename` (one drive), `rmdir` (empty) | the engine | files (`files-ops`) | FA2 |
| Drive info without a volume, labels | `drives`, `volume` | `EFsDrive`, `EFsSetVolume` | e32-rs | FA1 |
| Settings keys `files.*` (sort, view, hidden) | the settings store | the keys in `neoui-proto` `settings/registry.rs` | neoui | FA1 |
| Images at run time | `slint::Image::from_rgba8` | decoders (Slint has none on the device; ICL has no codecs) | files (`neo-format-image`) | FA5 |
| Zip, gzip, tar | ezlib in the ROM, C++ only | Rust readers and writers | files (`neo-format-archive`) | FA6 |
| Open a vCard in Contacts | Contacts imports every .vcf it finds (`phone/symbian/common/src/store.rs`) | an OPEN page that takes a path | phone | FA7 |
| Add an event to a calendar | Calendar is a shell mock | a calendar store (and app) | neoui or a new repo | FA7 |
| Fonts at run time (the font viewer) | fonts compiled in as SDF | a rasteriser for a loaded font | files (`neo-format-inspect`) | FA7 |
| Open with, file types | OPEN by key, ARG ≤ 256 bytes; a fixed `APPS` table | a handler table (type → app), a file picker, file handles (`EFsFileAdopt`) for long paths | neoui (protocol 1.10), e32-rs | FA8 |
| Copy and paste files | CLIP: text, ≤ 2048 bytes | a file clip (paths) | neoui | FA8 |
| Audio out | MODEMD's ringtone PCM only (ASM→ADM→AFE); MMF has no server | an audio service (hardware.md D3, roadmap H5) | neohw + kernel | FA9 |
| FP/NEON for apps | the kernel part done (WB1, 2026-11-17: Q0–Q15 saved per thread) | an ARMv7/NEON build of the Rust user side (smooth-ui S4) | e32-rs, neoui, build | FA9–FA12 |
| Video | nothing | a decoder on the NEON build | files | FA12 |
| Share E: over USB, Eject | FS6 researched, not started | E: removable (`a64_medblk.cpp`), a DWC3 PSL, mass storage in the ROM, USB power on cold boot, dismount in e32 | kernel, build, e32-rs | FA13 |
| Send via Bluetooth | — | OBEX, hardware/bluetooth.md B5 | neohw | FA13 |
| Send by MMS | SMS only | MMS, hardware/modem.md C10 | neohw, phone | FA13 |
| Install .sis / .sisx | unpacked at build time (`legacy/tools/sis.py`) | SWI on the device, legacy.md L4 | legacy | FA13 |
| Install .jar | no Java runtime | a runtime | — (not planned) | — |
| Files over 4 GB | FAT32 | exFAT ([filesystem.md](filesystem.md), Later) | kernel | — |
| Trusted certificates | not built | a certificate store (browser.md WB6) | browser, build | FA7 (view only) |

## Phases

Each phase ends with a gate: host tests and board snapshots in the files repo, then the Syborg CI and the Pixel.

| Phase | Work | Repos | Gate | Screens |
|---|---|---|---|---|
| **FA0** move | Create `NeoSymbian/files`; `neoui-files` → `files-core`, the app → `symbian/app` + `crates/files-ui`; UID 0xE0006001; CI. neoui drops `crates/neoui-files`, `symbian/apps/files`, the NEOFILES line, the shell mock and its snapshots, and clones the files repo in `syborg.yml`. No behaviour change. | files, neoui, docs | the R8 taps pass on Syborg from the new repo; host snapshots of today's screens | today's app: [`pat-files-refresh`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-bc9bc3e4da54), [`pat-files-select`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-b403f3b83e97) |
| **FA1** v2 browsing | The footer tabs, the Browse tab, folder list and grid, breadcrumb, folder ⋮, Sort sheet, empty folder, New folder, Z: read-only, Buttons mode; `ftile` icons for all 55 types; `files.*` settings keys; `EFsDrive` | files, neoui, e32-rs | every board below matches its snapshot; Back order of the spec | [`browse`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-3b00261f7f9d), [`folder-list`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-093a3d3f2dcf), [`folder-grid`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-f0cdc90d8458), [`folder-menu`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-e17e53bf193d), [`sort`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-47b52b42f241), [`folder-empty`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-ba0077b3f140), [`new-folder`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-09c4d3dc5e89), [`rom`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-9ada2c720ef0), [`browse-buttons`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-ae34e51279fc), [`folder-buttons`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-2d6172009655), icons [`spec-icons`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-93754f2cea38), headers [`spec-headers`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-c80d46adfa71) |
| **FA2** file operations | `neo-fs` + `files-ops`; selection header and ⋮, copy/move with the paste bar, progress (toast + shade entry, Cancel), clash, rename, delete into `.trash` with Undo; folder refresh by change notification; attributes | files, e32-rs | host tests with the fake (full disk, drive removed, power cut mid-move); a 2 GB copy C:→E: on the Pixel | [`select`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-9bedc9d6d4ab), [`select-menu`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-c972e3173d2c), [`paste-bar`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-ebac5e347da8), [`progress`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-1c8b970f65c6), [`clash`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-1726a0c853b3), [`delete`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-3f1185a0b7d9), [`rename`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-cb84232c1485), pattern [`pat-files-select`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-b403f3b83e97) |
| **FA3** find and tidy | Recent (Files' own list), Types (an index built by a worker, kept in `C:\private\e0006001\`), search with filters, Recycle bin (restore, empty, 30 days), Free up space (large files, old downloads, duplicates by size then hash), Details | files | search of E: under a set time on the Pixel; bin survives a reboot | [`recent`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-d48ee7f12f4e), [`types`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-b25e04de395a), [`type-images`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-f223378dc344), [`type-docs`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-f0772ec49764), [`search`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-fed7da8f354a), [`search-filters`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-3fc3efedcca3), [`bin`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-cde87383eb63), [`cleanup`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-08374822da0c), [`details`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-0428c730f1ce), pattern [`pat-files-search`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-d1f71b42fbde) |
| **FA4** text and code | `neo-format-text`: the text viewer (wrap, line numbers), the editor (19 text types; highlighting with our own lexers on `logos`; undo; find and replace; the code-key row), Markdown Preview, CSV/TSV table editing (`csv-core`), New file, the unsaved-changes dialog | files | edits round-trip byte-exact (encodings, line ends); a 5 MB log opens | [`view-text`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-4279a4f341e5), [`edit-code`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-4db6131c88c3), [`edit-find`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-7f8fb0ab48f6), [`edit-md`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-2e0af6ea745a), [`edit-csv`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-5d514d4e7945), [`new-file`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-428e95273bb3), [`edit-unsaved`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-538e2a9100d7), [`edit-buttons`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-e87d42c5045a) |
| **FA5** images | `neo-format-image`: JPEG, PNG, GIF, WebP, BMP, a bounded SVG subset; thumbnails in the grid and the Types tab (a worker, a cache); the image viewer (zoom, swipe, strip); the image editor (rotate, crop, resize, save a copy as JPEG/PNG) | files | a 12 MP JPEG opens within the heap; thumbnails don't block scrolling | [`view-image`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-58724838c247), [`edit-image`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-babc1c91e924), [`folder-grid`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-f0cdc90d8458), [`type-images`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-f223378dc344) |
| **FA6** archives | `neo-format-archive`: zip (read, write, deflate with `miniz_oxide`), gzip, tar; browse inside an archive read-only, Extract here / to…, Compress the selection | files | zip-slip and bomb tests; a 1 GB zip extracts on the Pixel | [`zip-browse`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-125122954e14), [`extract`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-9ed03d5b90ed), [`compress`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-70a253041365) |
| **FA7** cards and inspectors | vCard and iCal viewers and forms (`neo-format-pim`, unknown properties kept); "Add to Contacts" through a new Contacts OPEN page; "Add to Calendar" once a calendar store exists; font viewer (`ttf-parser` + our rasteriser); certificate viewer (`x509-cert`, view only); app package info (.sis header, .jad); unknown type with hex | files, phone, (calendar) | vCard round trip with phone's `vcard.rs`; each viewer on a corrupt fixture shows an error, not a panic | [`view-vcf`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-0be7ab9b0592), [`edit-vcf`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-11eec67bbda5), [`view-ics`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-b0c7d55e26eb), [`edit-ics`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-eb6a23e083f9), [`view-font`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-ea84c2ddd0f6), [`view-cert`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-9a9f15522173), [`view-app`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-093a96e8c80a), [`view-unknown`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-676d4c8645cf) |
| **FA8** open with, share, pick | Protocol 1.10 in neoui: a handler table (file type → app keys, with "Always"), a file clip, file handles past 256-byte paths; Files as the system file picker (an OPEN page that returns a path with DONE, for Save as and attachments); the Open with and Share sheets (Copy path, Copy to clipboard; Bluetooth and MMS wait for FA13) | neoui, e32-rs, files | an image opens from Files in Photos (once Photos exists) and Photos' "attach" picks through Files | [`open-with`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-758bbdc3cb11), [`share`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-3db79c4164d1) |
| **FA9** audio | `neo-format-media`: MP3, AAC, Vorbis, Opus, FLAC, WAV, AMR, MIDI (crate candidates `nanomp3-core`, `rusty_flac`, `ruopus`, a `symphonia` port, `midly`); an audio service for apps (with telephony: MODEMD owns APR today); the audio viewer and "Open in Music" | files, telephony, kernel | an MP3 plays on the Pixel without gaps; a call interrupts it | [`view-audio`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-84826f21b3aa) |
| **FA10** documents I | EPUB (zip + XHTML, reflow, chapters, position), docx / odt / rtf reflowed, xlsx as a read-only grid (`xmlparser`) | files | a 300-page EPUB pages smoothly; the docx with Armenian text from the board renders | [`view-epub`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-a7f9e4db02c8), [`view-docx`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-eb23122f75d9), [`view-xlsx`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-636480de5643) |
| **FA11** documents II | PDF: parse (`hayro-syntax`), our renderer (paths, text with embedded fonts, images), pages, thumbnails | files | the boarding pass from the board renders; a 100-page PDF scrolls | [`view-pdf`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-7c18c7fd6f77) |
| **FA12** video | the ARMv7/NEON build (smooth-ui S4; the kernel part is done) first; then a decoder for MP4/3GP (H.264 baseline) and WebM (VP8), with the audio service | kernel, files | a 720p clip plays on the Pixel | [`view-video`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-0a854b5f4d99) |
| **FA13** outside Files | Share E: over USB and Eject (FS6); Send via Bluetooth (B5); MMS (C10); install .sis on the device (L4); heic, mkv, 7z, rar, pptx | kernel, build, neohw, legacy | each in its own repo's stages; Files only wires the buttons | [`share`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-3db79c4164d1), [`view-app`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-093a96e8c80a), [`spec-types`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-addb580badcb) |

The replacement map (old boards → new) is [`spec-replace`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-79a68f1005f5).

**Order:** FA0 → FA1 → FA2 are the base, in that order. FA3–FA8 can follow in any order (FA8 changes neoui's
protocol, so it goes with a neoui release). FA9–FA12 depend on platform work and run beside it. *Estimate:* FA0–FA2
about 1 month, FA3–FA8 about 2–3 months, FA9–FA12 several months each, mostly platform work.

## Status (2026-11-19)

| Part | State |
|---|---|
| R8 (drives, folders, text, rename, delete) | built; replaced by FA1–FA4 |
| The design (60 boards, prototype, spec) | done, on the canvas |
| FA0 move | built 2026-11-17: files `624fb01` (CI green), neoui PR #14 (the cutover; Syborg passes every Files step); Pixel RAM boot: `NEOFILES.EXE[e0006001]`, the R8 walk passes |
| FA1 + FA2 | built 2026-11-18: files `4ed71d4`, e32-rs `0489694` (drive info, `set_entry`, volume label, a `NotifyChange` future), neoui `2047404` (protocol 1.11: the shade's progress bar). Syborg passes the v2 taps (browse, copy through the paste bar, trash) |
| FA3 | built 2026-11-18: files `559c508` + `f00af5f` (Pixel fixes), neoui `e0cfe28` (taps: Recent, Restore, search). Pixel: the bin survives a reboot, search, Types, Favourites, Details, Empty bin (2 GB) |
| FA4 | built 2026-11-18: files `e42811c`, neoui `ae720c6` (taps: New file → editor → type → save, 2 bytes exact). Pixel: a 5 MB log opens in about a second and scrolls; saves are byte-exact |
| FA5 | built 2026-11-19: files#6 (with NeoSymbian/image-webp `neosymbian`, the decoder made no_std). Pixel: a 12 MP JPEG decodes in 310 ms and shows in about a second; thumbnails come from a worker and a cache; swipe; rotate / crop / resize and Save as copy, on a 12 MP photo too. Syborg passes every Files step (its C: has no images) |
| FA6–FA13 | proposed; next: FA6 (archives; FA10 needs its zip reader) |

**Decided while building FA1–FA5:**
- **Settings** `files.*` (sort, ascending, folders first, grid, hidden, wrap) are unregistered keys in the app's own
  namespace, not registry rows; rows can come with Settings › Apps › Files.
- **Progress** of a copy goes into the shade through protocol 1.11 (`Notification.progress`, an optional trailing
  byte, so 1.9 and 1.10 apps still decode); the toast is Files' own.
- **Jobs** (copy, move, delete for good) run on a worker thread with its own file-server session; the UI polls a
  shared slot every 250 ms. Only the UI thread writes the bin's journal.
- **The index** (Types, search, Free up space) is walked by a second worker at start and after Files' own jobs,
  saved in `C:\private\e0006001\index.dat`; it skips `\private\`, `\sys\`, `\resource\` and the bins. Z: is
  indexed for search only. No change notifications drive it.
- **Favourites** come from the selection ⋮ ("Add to Favourites", one folder) and are edited on their own page.
- **Details** has no Created date: the 2010 `TEntry` keeps only the modified time.
- **Images** on the Types tab are grouped by folder, eight thumbnails a folder (files2-type-images); videos keep
  the list layout until FA12.
- **Image decoders** (`neo-format-image`): JPEG `zune-jpeg` (full size, then shrunk: it has no DCT scaling), PNG
  `zune-png`, GIF our own over `weezl` (the `gif` crate needs std), WebP NeoSymbian's no_std fork of `image-webp`,
  BMP our own, SVG a bounded subset of our own on `tiny-skia` (shapes, paths, transforms, fill and stroke; no text,
  gradients or filters). A progressive JPEG too big for the heap shows its EXIF preview, with a note.
- **One picture worker** (a 256 KB stack: 64 KB overflowed in `zune-jpeg`) decodes the viewer's picture first, then
  thumbnails for the rows on screen, and runs Save as copy; thumbnails (160 px) are kept as JPEGs in
  `C:\private\e0006001\thumbs\`, at most 4,000. The viewer shows a picture at most 2560 px on its long side.
- **The pinch** is read from raw touches: neoapp gives Slint one pointer, so the second finger is the app's.
- **Image edits** save a copy (`name-edit.jpg`; PNG unless the original is a JPEG) and drop EXIF after applying its
  orientation; the original stays. The JPEG encoder is `jpeg-encoder` (based in part on the work of the IJG).
- **The editor** reads keys raw from the event loop (as Terminal does); the code-key row adds what the system
  keyboard lacks (`{ } [ ] | !` …, arrows), the keyboard's edit bar gives Select all / Copy / Paste (Ctrl chords,
  the clipboard holds 2 KB). Selection is a long press on a word, then two handles.
- **Text** is kept byte-exact: encoding (UTF-8, BOM, UTF-16LE/BE) and each line's end are kept; text that isn't
  valid opens read-only. Files up to 16 MB open; the surface draws only the rows on screen.
- **Markdown Preview** wraps by an estimated glyph width: Slint's `StyledText` needs its `std` feature, which the
  device build lacks.
- **Pixel test images** are built with `--features test-files` (a 5 MB `C:\Data\big.log`); the shipped app has no
  such hook.

## Not doing

- **Java (.jar, .jad):** no runtime is planned; Files shows the package details only.
- **Files over 4 GB:** FAT32 can't hold them; exFAT is in [filesystem.md](filesystem.md)'s Later list.
- **MTP:** E: is shared as mass storage (FS6), not MTP ([debug-access.md](debug-access.md)).
- **Copying the 2010 file manager:** its source (`oss.FCL.sf.app.files`, EPL, deleted, see
  [retired-repos.md](retired-repos.md)) is prior art for wording only; no code is copied.
