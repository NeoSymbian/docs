<!-- SPDX-License-Identifier: Apache-2.0 -->
# Files: the file manager (NEOFILES v2)

Written 2026-11-17. This is the implementation proposal for the Files app: a new `NeoSymbian/files` repo, every screen
of the design canvas's Files page, the platform work it needs, and the phases FA0–FA13. Today's app (R8) is built and,
since FA0, lives in [NeoSymbian/files](https://github.com/NeoSymbian/files). FA1–FA8 are built (2026-11-18/20, see
[Status](#status-2026-11-21)); FA9 M0–M1 and FA10 are built (FA10 tried on the Pixel, not merged); the rest of FA9 and
FA11–FA13 are not.

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
- **CI:** neoui's Syborg job (retired in US5, kept as the US6b spec `symbian/us6b/syborg-taps.yml`) cloned NeoSymbian/files, built `libneofiles.a`, then tapped through drives,
  `Z:\Sys\Bin`, `estart.txt`, makes and deletes `C:\neo\` and makes `C:\дом\`. The files repo's own CI runs the
  model's tests and snapshots today's five screens (`snapshots/files-*.png`).
- **Speed:** the open animation averages 20.5 ms a frame, over the 16.7 ms budget ([smooth-ui.md](neoui-shell/smooth-ui.md)).

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
  session (a session is bound to its thread) and talk through e32 mutex queues (native atomics exist since US4, but a thread-owned session needs none).
- **CI:** host: `cargo fmt --check`, `clippy -D warnings`, `cargo test --locked`, every board's snapshot compared
  with its baseline (diffs uploaded); arm: `cargo arm --locked`, the EXE size and heap budget. The Files taps of neoui's
  retired Syborg job move to QEMU virt with US6b.
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
- **Speed:** the kernel saves FP/NEON for apps since WB1 (2026-11-17, KRN-019), but our Rust built for
  ARMv5TE soft-float until US4 (2026-11-25; now ARMv8 softfp): codecs can use NEON (smooth-ui S4's user-side part). Each media phase
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
| Open a vCard in Contacts | done (FA7): Contacts' IMPORT page (`contacts::IMPORT`, its arg a .vcf path) | — | phone | FA7 |
| Add an event to a calendar | Calendar is a shell mock | a calendar store (and app) | neoui or a new repo | FA7 |
| Fonts at run time (the font viewer) | done (FA7): our rasteriser over `ttf-parser` in `neo-format-inspect` | installing a font for other apps | files | FA7 |
| Open with, file types | done (FA8): neoui protocol 1.12 (`OPEN_FILE`, `DONE_FILE`), the handler table `neoui_proto::open`, Files' PICK/SAVE pages, e32's `SharedFile` (`EFsFileAdopt`) | a registry of installed apps' types (store ST) | neoui, e32-rs | FA8 |
| Copy and paste files | done (FA8): CLIP's kind (paths to copy or move) | — | neoui | FA8 |
| Audio out | done: NeoAudio in AUDIOD.EXE ([hardware/audio.md](hardware/audio.md) A0–A8): S16LE streams at 8–96 kHz, mixed to mono; FA9's player is a client | events (no end-of-stream or call notice: the player polls INFO), a media session for the shade (M1b) | neohw, neoui | FA9 |
| FP/NEON for apps | the kernel part done (WB1, 2026-11-17: Q0–Q15 saved per thread); Files builds for ARMv7 since FA9 (`cargo arm7`) | the rest of the Rust user side on ARMv8 AArch32 ([user-side-smp.md](user-side-smp.md) US4); Syborg's kernel switches no VFP (US6) | e32-rs, neoui, build | FA9–FA12 |
| Video | the FA12 player: pure-Rust decoders on the A75s, conversion on its own thread (2026-11-26) | A/V after key frames, VP9 720p and 1080p (FA12b, [video-sync.md](video-sync.md)) | files | FA12 |
| Share E: over USB, Eject | FS6 researched, not started | E: removable (`a64_medblk.cpp`), a DWC3 PSL, mass storage in the ROM, USB power on cold boot, dismount in e32 | kernel, build, e32-rs | FA13 |
| Send via Bluetooth | — | OBEX, hardware/bluetooth.md B5 | neohw | FA13 |
| Send by MMS | SMS only | MMS, hardware/modem.md C10 | neohw, phone | FA13 |
| Install .sis / .sisx / .npk | unpacked at build time (`legacy/tools/sis.py`) | NEOINST on the device, store.md ST6 + ST10 (was SWI, legacy.md L4) | store, legacy | FA13 |
| Install .jar | no Java runtime | a runtime | — (not planned) | — |
| Files over 4 GB | FAT32 | exFAT ([filesystem.md](filesystem.md), Later) | kernel | — |
| Trusted certificates | not built | a certificate store ([browser WB6](browser/wb6-services.md)) | browser, build | FA7 (view only) |

## Phases

Each phase ends with a gate: host tests and board snapshots in the files repo, then the Pixel (and, from US6b, the UI taps on QEMU virt).

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
| **FA9** audio | stages M0–M6: M0 the ARMv7 build; M1 the player + WAV; M1b now playing in the shade (the media session, [top-panel.md](neoui-shell/top-panel.md) TP3); M2 MP3; M3 FLAC, Ogg Vorbis, Opus; M4 AAC/M4A, AMR; M5 MIDI; M6 docs. `neo-format-media` over NeoAudio (AUDIOD); "Open in Music" disabled until a Music app | files, neoui | an MP3 plays on the Pixel without gaps; a call interrupts it | [`view-audio`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-84826f21b3aa) |
| **FA10** documents I | EPUB (zip + XHTML, reflow, chapters, position), docx / odt / rtf reflowed, xlsx as a read-only grid (`xmlparser`) | files | a 300-page EPUB pages smoothly; the docx with Armenian text from the board renders | [`view-epub`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-a7f9e4db02c8), [`view-docx`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-eb23122f75d9), [`view-xlsx`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-636480de5643) |
| **FA11** documents II | PDF: parse (`hayro-syntax`), our renderer (paths, text with embedded fonts, images), pages, thumbnails | files | the boarding pass from the board renders; a 100-page PDF scrolls | [`view-pdf`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-7c18c7fd6f77) |
| **FA12** video | the ARMv7/NEON build (smooth-ui S4; the kernel part is done) first; then a decoder for MP4/3GP (H.264 baseline) and WebM (VP8), with the audio service | kernel, files | a 720p clip plays on the Pixel | [`view-video`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-0a854b5f4d99) |
| **FA13** outside Files | Share E: over USB and Eject (FS6); Send via Bluetooth (B5); MMS (C10); install .sis on the device (L4); heic, mkv, 7z, rar, pptx | kernel, build, neohw, legacy | each in its own repo's stages; Files only wires the buttons | [`share`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-3db79c4164d1), [`view-app`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-093a96e8c80a), [`spec-types`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-addb580badcb) |

The replacement map (old boards → new) is [`spec-replace`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-79a68f1005f5).

**Order:** FA0 → FA1 → FA2 are the base, in that order. FA3–FA8 can follow in any order (FA8 changes neoui's
protocol, so it goes with a neoui release). FA9–FA12 depend on platform work and run beside it. *Estimate:* FA0–FA2
about 1 month, FA3–FA8 about 2–3 months, FA9–FA12 several months each, mostly platform work.

## Status (2026-11-21)

| Part | State |
|---|---|
| R8 (drives, folders, text, rename, delete) | built; replaced by FA1–FA4 |
| The design (60 boards, prototype, spec) | done, on the canvas |
| FA0 move | built 2026-11-17: files `624fb01` (CI green), neoui PR #14 (the cutover; Syborg passes every Files step); Pixel RAM boot: `NEOFILES.EXE[e0006001]`, the R8 walk passes |
| FA1 + FA2 | built 2026-11-18: files `4ed71d4`, e32-rs `0489694` (drive info, `set_entry`, volume label, a `NotifyChange` future), neoui `2047404` (protocol 1.11: the shade's progress bar). Syborg passes the v2 taps (browse, copy through the paste bar, trash) |
| FA3 | built 2026-11-18: files `559c508` + `f00af5f` (Pixel fixes), neoui `e0cfe28` (taps: Recent, Restore, search). Pixel: the bin survives a reboot, search, Types, Favourites, Details, Empty bin (2 GB) |
| FA4 | built 2026-11-18: files `e42811c`, neoui `ae720c6` (taps: New file → editor → type → save, 2 bytes exact). Pixel: a 5 MB log opens in about a second and scrolls; saves are byte-exact |
| FA5 | built 2026-11-19: files#6 (with NeoSymbian/image-webp `neosymbian`, the decoder made no_std). Pixel: a 12 MP JPEG decodes in 310 ms and shows in about a second; thumbnails come from a worker and a cache; swipe; rotate / crop / resize and Save as copy, on a 12 MP photo too. Syborg passes every Files step (its C: has no images) |
| FA6 | built 2026-11-19: files#7. Pixel: a 1 GB zip (made on the phone by our writer in 36 s) extracts in 70 s, as fast as a plain copy of it (68 s), with the extract sheet open or closed (before progress changed once a second, the open sheet made it 396 s); browse a zip with Armenian and Cyrillic names, open a member read-only, list a tar.gz on the worker, compress to tar.gz on E: through the folder picker. Syborg passes every Files step (no archive taps: its C: has none) |
| FA7 | built 2026-11-20: files#8, phone#7 (Contacts' IMPORT page). Pixel: Add to Contacts imports the ticked cards through NEOCONT, and Files then marks them "In Contacts" (a vCard 2.1 copy too); a saved edit changes only the edited line (PHOTO, X- properties, groups and CRLFs stay byte-exact); each of 9 corrupt fixtures shows its typed error and the hex view, with no panic; the DejaVu Sans samples (Latin, Cyrillic, Armenian, 12–32 px) draw in under about 2 s; X-plore's real SIS shows its platform, signer, UID and 4 capabilities |
| FA8 | built 2026-11-20: e32-rs#7 (file handles between processes; Syborg `fs_share`), neohw#11 (pin), neoui#27 (protocol 1.12, the kit's Files page; Syborg: the kit saves through Files), files#9. Pixel: the kit picks `big.log` and saves `note.txt` through Files' picker; Open with sends a 298-byte path and a file in Files' private folder (a zip member) to the kit by handle; Always routes a .txt tap to the kit and is undone from the sheet; Copy to clipboard pastes the text; a Copy survives Files being killed (the paste bar comes back) |
| FA9 M0 + M1 | built 2026-11-21: files#10. Files builds for ARMv7 on the phone (`cargo arm7`: VFPv3 + NEON, softfp; Syborg keeps `cargo arm`). The player plays WAV (8/16/24/32-bit PCM, float, A-law, µ-law, extensible). Pixel (muted): ARMv7 Files runs; 44.1/48/22.05/8 kHz WAVs play; next, previous, end-of-track advance, seek and pause work; one underrun per track (the end); a broken file is skipped; music goes on with the screen off. **Not done yet:** the incoming-call test on the Pixel, Syborg CI with the branch, the decoder choices (before M2), M1b |
| FA10 | built 2026-11-21, merged (files#11): docx, odt and rtf in Reflow and Page; the EPUB reader; xlsx as a grid. Host: every reader on its fixtures and on broken copies (no panic), the layout's widths equal Slint's, snapshots `files2-view-docx(-page)`, `files2-view-epub(-controls, -contents)`, `files2-view-xlsx(-chart)`. **Pixel** (RAM boot): the board's Armenian docx in Reflow and Page; the 311-page EPUB (a page turn is one ~3.4 ms app frame plus ≤ 7.3 ms of rendering; 12 chapters counted in ~250 ms; the place, size and theme kept over a reboot); the xlsx grid (E7's formula and sum, a row's sum, sideways scroll, the chartsheet); a docx with three 12 MP photos: each decoded on the worker only as it scrolls in (4000×3000 → 800×600 in 1.2–1.4 s); every broken copy in `C:\Data\fa10\` opens as hex (or, a cut rtf, partly), no crash. The run found pages laid out 264 px short (measured before the reader's frame): the viewers now lay out again when their area changes size. **Not tried:** the pinch (the debug monitor injects one finger) |
| FA11 | merged 2026-11-25 (files `fa11`; Pixel-tested except pinch): PDFs open in a viewer like the board (`files2-view-pdf`): pages at the screen's width on grey, the "Page 1 / 2" pill (a tap goes to a page), the strip of thumbnails with the size and page count, pinch zoom 1–4× (the pages stretch, then a sharp tile of the view is drawn), Contents from the outline, Go to page, a password ask, the place kept per file. Host: the board's boarding pass (our fixture, `make_pdf.py`) draws every QR module where it belongs, its embedded subset fonts (Armenian too) and its JPEG; a 100-page book (unembedded Helvetica, object streams, an outline); RC4 with a password; macOS Quartz's own PDF; forms 200 deep, a page tree that loops, a broken xref, a 3e9-wide tiling cell, 40 nested soft masks, cuts and bit flips: errors or partial pages, no panic. Snapshots `files2-view-pdf(-zoom, -page, -password, -book, -contents)`. **Pixel (2026-11-25, ARMv8 image from us5c + `test-files`):** the boarding pass sharp (opened in 3 ms, pages in 78/95 ms); book-100 opens in 19 ms, pages 200–360 ms (about 270) at 984 px, placeholders fill in about 3 s after a fast flick; the pill, thumbnails, Contents (current chapter marked), Go to page, the password (wrong one said, 1234 opens) and the place (page 77 kept) work; deep/loop/tiling/masks draw partial pages, broken-xref is repaired, the broken copies open as hex with the reason; quartz.pdf and a downloaded `dummy.pdf` draw. Fixed from the run: enlarged photos are smoothed (only 1-bit images keep hard pixels), the keyboard goes with the ask card, a jump moves the view at once. Not checked: pinch (two fingers, by hand), the worker's stack high-water mark (1 MB holds the deepest fixture) |
| FA12 | merged as it stands (2026-11-26: neoui#52, files#16 and this docs PR; the open issues below go to FA12b, the A/V research in [video-sync.md](video-sync.md)): videos play in a player like the board (`files2-view-video`): MP4, MOV, 3GP and Matroska/WebM; H.264 (Baseline to High), VP8 and VP9 pictures; AAC, Vorbis and Opus sound; ±10 s, the seek bar, pause, speed 0.5–2×, mute, rotate, full screen, the place kept per clip, the controls hiding after 3 s. All pure Rust and no_std (NeoSymbian forks of rust_h264, vp8-decoder, rusty_vp9 and symphonia; `shiguredo_mp4`; our Matroska reader); every fixture's pictures equal ffmpeg's bit for bit on the host. **Pixel (720p30 H.264 High + AAC, 2026-11-26):** portrait 28.5–30 fps shown with the conversion on its own thread (CPU 6; the UI thread 0–2 ms a picture), controls up 29.7 fps, landscape 23–27 fps (conversion 21–22 ms, split with a helper on an A55), the clip's end and rotating after it right, over 720p refused with a plain card; from the earlier runs MKV H.264, VP8+Vorbis and VP9 480p + Opus play and H.263 shows the error card. **Open (FA12b):** see *Known issues* under the FA12 decisions |
| FA9 M1b–M6, FA13 | proposed; next: the decoder choices, then M2 (MP3); M1b with the top panel's media session ([top-panel.md](neoui-shell/top-panel.md) TP3: Files posts MEDIA and keeps playing in the background, owner 2026-11-21) |

**Decided while building FA1–FA8:**
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
- **Archives** (`neo-format-archive`): zip, gzip and tar readers and writers of our own (the crates.io ones need std)
  over `miniz_oxide` and `crc32fast`, streamed (a 1 GB archive is never in memory). Zip reads Zip64, CP437 and UTF-8
  names (flag, 0x7075, or plain UTF-8), stored and deflated members; it writes UTF-8 names and no Zip64 (over 4 GB or
  65,535 entries it says to use tar.gz). 7z and rar are recognised only; encrypted members are listed, not opened.
- **Safety:** one function (`name::safe`) decides a member's name: `..`, absolute paths, drives and control
  characters are refused, FAT's forbidden characters become `_`; every target is checked again to stay inside the
  destination. A member never gives more than it declares (and its CRC is checked); the declared total must fit the
  free space first; a gzip or tar.gz stops at the free space; nested archives are never opened; at most 200,000
  members are listed.
- **Extract here** makes `<folder>\<name>\` (a new name when that is taken); **Extract to…** and Compress's **Save
  in** use a folder-picker page. A tar.gz is listed on the job worker (it has no index); a member opened from an
  archive is unpacked into `C:\private\e0006001\open\` and shown read-only. Already-compressed files (audio, video,
  photos, archives) are stored, not deflated. Extracted files get today's date (neo-fs has no set-modified).
- **Progress** of an archive job changes once a second: redrawn every 250 ms poll, the open extract sheet slowed a
  1 GB extract from 70 s to 396 s on the Pixel; once a second, it takes 71 s.
- **vCard and iCal** (`neo-format-pim`, our own, no_std): a file is a list of content lines that keep their raw
  bytes; an edit rewrites only the lines it changes, in the file's own version (2.1 quoted-printable, 3.0/4.0
  escapes, folded at 75 octets) and line ends. Text that isn't valid UTF-8 opens read-only. A save edits a copy and
  swaps it in only after the write succeeds. iCal reads VEVENT, VTODO, VALARM (shown as "1 hour before") and
  VTIMEZONE (the offset for a TZID); a Repeat the form can't show (an RRULE beyond FREQ) stays untouched unless the
  user changes it. datetime's `pim-ics` reuses this crate.
- **Add to Contacts** writes the ticked cards' original bytes to `C:\private\e0006001\open\add.vcf` and opens
  Contacts on its IMPORT page; NEOCONT stays the only writer of the book. "In Contacts" is phone's own duplicate
  rule (`Book::has_same`: same name and first number), run by Files over a read of `contacts.dat`.
- **Add to Calendar** and "Your week" are left out until datetime DT6 (a calendar store).
- **Inspectors** (`neo-format-inspect`): fonts through `ttf-parser` and our own coverage rasteriser (no shaping;
  one cmap subtable; at most 1024 glyphs or 8 MB cached); certificates through `x509-cert` (PEM bundles, DER),
  shown, never verified; SIS v2 reads only the header and the controller (SIS v1 says so); .jad and a .jar's
  manifest; any other file, or a file a viewer can't read, opens as hex (pages read with `read_at`).
- **Disabled until later phases:** Install font (needs a font store), Install as trusted (a certificate store,
  browser WB6), Install for .sis/.sisx (NEOINST, FA13). Each says why in its footer.
- **Files go by handle** (FA8, owner decision): Open with and the picker's answer pass an open file (e32
  `SharedFile`: the 2010 `RFile` transfer and adopt), so a long path or a file in Files' private folder (an archive
  member) reaches another app. Files' file-server session is shared (`Fs::share_protected`) at start.
- **Protocol 1.12:** `OPEN_FILE` / `ARG_FILE` open an app with a file; `DONE_FILE` / `RESULT_FILE` answer the opener
  with one (Files' `PICK` and `SAVE` pages); the clipboard has a kind, and copied files are their paths, one per
  line. neoui holds a passed file between the two apps.
- **Who opens what** is `neoui_proto::open::HANDLERS` (owner decision: in neoui-proto, not Files): Contacts' IMPORT
  takes a .vcf by name (it reads a path), the kit's file viewer anything by handle. Files' own viewer always comes
  first. **Always** is the system setting `open.always` (`ext=key;`, any app may write it); undo it by picking Files
  with Always on (the selection ⋮ has Open with… for one file).
- **No Photos app yet** (owner decision): the gate is the kit's Files page (Pick a file, Save a file, and a view page
  Open with targets), which is also the template for apps that pick or save files.
- **The picker** is FA6's folder picker: files after the folders (filtered by extensions or a family) for PICK, a
  name field for SAVE and the editor's Save as. A name clash keeps both (`name (1).txt`); ✕ answers with plain `DONE`.
- **Share:** Copy path; Copy to clipboard (a text file up to 2 KB as text, any other file as a paths clip with the
  paste bar); Open with…; Bluetooth and MMS drawn disabled (FA13).
- **Copied files on the system clipboard** (owner: the typed clip): Copy and Move also set a paths clip, and Files
  restores the paste bar from it on start and when shown again; Paste and Cancel clear it.
- **Pixel test images** are built with `--features test-files` (a 5 MB `C:\Data\big.log`, `C:\Data\photos\`,
  `C:\Data\zips\` with a 1 GB zip, `C:\Data\fa7\` with each FA7 fixture and a broken copy of it, and `C:\Data\fa8\` with
  a note, contact cards and a 298-byte path); the shipped
  app has no such hook.

**Decided while building FA9 (M0, M1):**
- **ARMv7 now** (owner decision): the phone's NEOFILES is built with `cargo arm7` (`symbian/targets/armv7a-neosymbian-eabi.json`, a copy of e32-rs's: VFPv3 + NEON, the softfp calling convention, so Symbian calls are unchanged). Moving to ARMv8 AArch32 later (US4) swaps the target only. Syborg's 2010 kernel switches no VFP for user threads (GCCE), so the Syborg CI builds Files with `cargo arm`; the files CI builds and lints both. (Superseded by US4, 2026-11-25: one ARMv8 `cargo arm` build, `arm7` gone.)
- **Duplicates hash with xxh64:** xxhash-rust's xxh3 doesn't build for 32-bit ARM with NEON (its NEON code names `core::arch::aarch64` types; the 32-bit intrinsics are unstable). The hashes are only kept in memory.
- **The player is an FA7 viewer** (`Kind::Audio`): FA7's header (Share, ⋮ Show as hex… / Open with… / Details), Back, and the hex view with the reason for a file the decoders can't read. The folder's audio files are Next and Previous (the image viewer's folder list, now shared); shuffle and repeat (the folder, the track) stay while the player is open.
- **Playback runs on a worker** with its own NeoAudio session per track. Each WRITE carries about 50 ms of the track (WRITE blocks while the 250 ms queue is full, so the worker keeps pace with the speaker). After each WRITE it reads INFO, because NeoAudio sends no events. PREEMPTED (a call or the ringtone has the speaker) pauses the stream; it resumes where it was after the call (owner decision). The end of a track is the queue running empty after the decoder's last frame.
- **Leaving Files pauses** ("Stops when you leave Files."), unless a call has the speaker: then the track is held and resumes after the call. The screen going off doesn't hide an app, so music keeps playing with the screen off. With M1b (top panel TP3) leaving Files no longer stops it: the owner chose background playback (2026-11-21), and the footer text changes then.
- **What a file is** comes from its first bytes (`neo_format_media::probe`), not its name; `.aac` is an alias of the M4A row (the board's 55 types stay).
- **Accented tags draw:** Slint bakes only the glyphs its literals use (plus ASCII and the keyboard's alphabets), so the player carries the Latin-1 and Latin Extended-A letters ("Café", "Tunç").
- **Test images play muted** (`test-files`: the stream's own gain at 0, the media volume untouched); generated WAVs go to `C:\Data\fa9\`.

**Decided while building FA12 (2026-11-25/26):**
- **Decoders, all pure Rust and no_std** (owner: rust_h264, FFmpeg only as the fallback): our forks
  [rust_h264](https://github.com/NeoSymbian/rust_h264) (a no_std leak fixed: the boxed OnceLock never freed, about 1 MB a
  frame; NEON motion compensation on 32-bit ARM, checked bit-exact on the Pixel against the Mac with Baseline, Main/High
  and deblocked 1080p clips), [vp8](https://github.com/NeoSymbian/vp8) and
  [rusty_vp9](https://github.com/NeoSymbian/rusty_vp9) (no_std), and [Symphonia](https://github.com/NeoSymbian/Symphonia)
  (PR #553's no_std branch, hashbrown 0.16 for build-std) for AAC and Vorbis; `opus-rs` (built in place: 175 KB);
  `shiguredo_mp4` (the canary, for its edit list: B-frame delay and AAC priming); our own Matroska reader.
- **Speed on the Pixel (one A75 at 2 GHz):** H.264 720p 48–64 fps on typical clips, 21 fps on a noisy 8 Mbps one; 1080p
  about 23; VP8 720p 65; VP9 720p 18.5. The gold cluster sits at 300 MHz unless touched, so the kernel got a media boost
  (HAL `ENeoHalCpuBoost` 0x4e29, kernel#44; the player asks every second) and the decoder runs pinned to CPU 7.
- **Frames go straight into the app's surface** (owner): neoapp `App::raw` and `App::set_landscape` (neoui `fa12-raw`);
  Slint draws the frame only while the controls show. The sound is the clock (NeoAudio's frames less 160 ms); the sound
  and the clock wait until 4 pictures are decoded; a picture is dropped when a newer one is due already; the decoded queue is bounded (8).
- **The screen stays on while a clip plays:** a page flag (`Page.awake`, neoui `fa12-raw`) the server honours as for a call.
- **Test-only layout (2026-11-26):** with the decoders NEOFILES is about 17.5 MB and a core-ROM test image passes the
  Pixel's RAM-boot limit (about 28 MB), so test images left NEOFILES out and it was pushed to `C:\sys\bin` (all
  capabilities), removed after each run. Not a release layout: big Rust EXEs need the ROFS or a bigger core (owner).
- **Conversion off the UI thread** (owner, 2026-11-26): a converter thread pinned to CPU 6 writes each picture
  straight into the surface (neoapp `App::raw_target`), and the UI thread only sends the DAMAGE at the picture's time
  (`App::damage`); with the controls up it fills a Slint image (two buffers reused: a new 2–6 MB one per picture
  fragmented the first-fit heap until one failed). Landscape (2 MP) is split with a helper thread on CPU 5 (owner:
  split across cores; `yuv::draw_rows`, the same bytes). The turned conversion works in bands of 32 rows so the
  compiler vectorizes it (37 → 28 ms on one A75). Watchdogs: a converter or worker silent for 2 s shows the error card.
- **Over 720p is refused for now** ("Files can't play videos over 720p yet"): 1080p ran the worker out of the 64 MB heap.
  It comes back with e32-rs#17 (256 MB) and rust_h264's threaded decoder.
- **1 ms waits:** `RTimer::After` rounds to the 1/64 s tick on this kernel (`stimer.cpp`), so the player's 2 ms waits were
  15–31 ms; Files has its own `TimerHighRes` delay until e32 gets `time::delay_high_res`.
- **Known issues (FA12b, measured on the Pixel 2026-11-26):**
  - **Pictures late after each key frame:** rust_h264's `OrderedDecoder::new()` holds up to 16 pictures until the next
    key frame: no picture for ~780 ms every 2 s, then 50–100 ms late (worst A/V ~100 ms, 1–5 % dropped). The fix (the
    depth from the SPS's `max_num_reorder_frames`, files `fb90512`) passes on the host and is not yet run on the Pixel.
    How other players keep sync, and the FA12b plan: [video-sync.md](video-sync.md).
  - **Landscape 23–27 fps,** not 30: the split conversion takes 21–22 ms, on the edge of the 33 ms a picture has.
  - **VP9 720p 18.5 fps** (single thread); 480p plays at 30.
  - **Memory not measured** (step 3); a thread that panics leaves what it held allocated (no unwinding).
  - **Without kernel#44** (the media boost) the A75s sit at 300 MHz and decoding is slower; kernel#44 and e32-rs#17 are
    still open.
  - **Not done:** V5 thumbnails, the review (V6), the 206 ms jump after resume, and the release layout (NEOFILES is
    17.5 MB: the ROFS, owner's decision).

**Decided while building FA11 (2026-11-25):**
- **The engine is hayro, made no_std in our fork** (owner): [NeoSymbian/hayro](https://github.com/NeoSymbian/hayro),
  branch `neosymbian` from v0.9.0. hayro-syntax was already no_std; hayro-interpret and hayro-font got a `std` feature
  (default on, so upstream behaviour is unchanged: its whole regression suite passes, 1785 tests): hashbrown maps,
  spin locks, libm maths behind a trait with the std names. hayro's own renderer (vello_cpu, std) isn't used: our
  `Device` draws with tiny-skia, which Files already had (SVG). Without std hayro-syntax shares its parts with `Rc`,
  so a document lives on the thread that opened it: the worker.
- **No colour management** (owner): moxcms needs std, so the fork's `icc` feature is off; an ICC-based space uses its
  `/Alternate` (or the device space of its component count), CMYK converts naively and Lab by formula. The predefined
  CJK CMaps (brotli, std) are left out too: Identity-H/V work, CJK PDFs that name another CMap lose their text.
- **The whole file in its own chunk, at most 48 MB** (owner): hayro wants the bytes as one slice. The chunk is never
  the heap (which only grows) and goes when the PDF closes; bigger files open as hex.
- **One memory budget a drawing** (review): tiny-skia can't fail an allocation softly, and a failed one ends the
  worker, so a page's layers, masks, pattern cells and images share 24 MB; what would go over is left out and the
  page marked partial. A drawing is at most 4 MP, a whole page 3 MP (taller pages drawn smaller and stretched).
- **What the view wants, the worker draws:** whole pages at the screen's width near the view, one tile of the view
  while zoomed, thumbnails near the current page; pictures are dropped as they scroll away. A worker that doesn't
  answer for 60 s is taken as dead (a panic ends only its thread) and the file shows as hex.
- **Passwords, Contents, Go to page, the place** (owner): a masked field asks (a wrong password asks again);
  Contents is the book's list (now `ContentsList`, shared); the place (page, zoom) is in `pdfs.dat`.
- **Not in FA11:** text selection, search and copy; links; forms; printing; a night mode; reflow; hinting.

**Decided while building FA10 (2026-11-21):**
- **Slint draws the text, Rust lays it out** (owner). Slint's software renderer keeps each glyph's advance at one SDF
  size T (26.6 fixed point; rounded for glyphs with an outline, truncated for blank ones; T comes from every font size
  in the UI, 16 in Files) and draws it at P px as `(P·adv/T + 32)/64`, P truncated to whole pixels. files-ui's build
  script writes the faces' advances for the glyph set, and `doc::Fonts::calibrate` finds T once from a hidden probe
  run (it needs many sizes: three sizes fit 9, 14 and 16). A host test checks Rust's widths equal Slint's for 100+
  runs. Slint has no underline: underlines and strikes are drawn as rectangles.
- **The document faces are a family of their own, NeoDoc** (owner): DejaVu Sans, Bold and Oblique 2.37 renamed (the
  Bitstream Vera licence asks a changed font to be renamed; `ui/fonts/NeoDoc.license`). Adding a "DejaVu Sans" Bold
  had turned every weight-600 DejaVu title in Files bold. Markdown Preview's italic now draws italic (Slint finds the
  Oblique for NeoSans). Slint bakes every literal character into every embedded font, so the documents' set (Latin-1,
  Latin Extended-A, Greek, Cyrillic, Armenian, punctuation, currency, □) took the baked glyphs from 0.45 to 1.35 MB;
  a character outside it is drawn as □.
- **Documents stream** (owner: big photos must not load all at once). A docx, odt, EPUB or xlsx is read through the
  open file a part at a time; a picture's size comes from its member's first 64 KB (512 KB for a JPEG with a large
  EXIF); pictures are decoded on the picture worker only when the window shows them, at the size they are drawn
  (into a chunk when they can), and let go when they leave it; a quiet box stands in meanwhile. An rtf is read whole
  (at most 32 MB): its pictures are in its text.
- **Content is checked, not only the name:** `neo_format_document::detect` reads `{\rtf`, a zip's `mimetype` (EPUB,
  ODF text) and its parts (`[Content_Types].xml` with `word/` or `xl/`); the viewer is still chosen by extension
  (`.csv` is in the Excel family and keeps its table editor).
- **docx / odt / rtf:** styles (with `basedOn`), headings, lists (bullets and numbers), tables (spans; a column is at
  least its longest word), pictures, page breaks and the page setup. Not shown: headers, footers, footnotes,
  comments, deleted text, text boxes' frames. Left-aligned, centred or end-aligned; no justification, hyphenation or
  right-to-left text.
- **Page mode** (owner: now, not later): the file's page size and margins (A4 when it has none), scaled to the
  screen on grey; a pinch zooms 1–4× and the pages are laid out again when the fingers lift (the footer says the
  zoom meanwhile); a zoomed page scrolls sideways.
- **EPUB:** a chapter at a time; the contents from EPUB 3's nav, else EPUB 2's NCX; DRM refused (obfuscated fonts
  are fine: unused); stylesheets aren't read (an element's inline style is). The reader (owner: Contents, Text size,
  Themes, pictures): taps on the left and right quarters or swipes turn pages, the middle shows Contents · A− · A+ ·
  the theme (Sepia, Light, Dark); Contents is an overlay (a kit sheet doesn't scroll a long list). Sizes 13–30 dp,
  books start at 17. A worker lays every chapter out to number the pages ("Page n of N in the chapter" until it is
  done; a newer size stops an older count). The place in each book is kept in `C:\private\e0006001\books.dat`
  (path, size, date → chapter and position), the size and theme in `files.reader.size` / `files.reader.theme`.
- **xlsx:** cached values only (nothing is calculated); shared formulas shifted from their master for the formula
  bar; number formats: General, decimals, grouping (a no-break space, as the board), percent, thousands, literals,
  currencies, dates and times (1900 and 1904); bold from the cell's font; merged cells; at most 200,000 cells a
  sheet; a chartsheet says "Charts aren't shown". A tap selects a cell (or its merge); a column letter or a row number
  selects the column or row, and the footer sums its numbers (no drag selection). Columns are 6 dp a character
  (Excel's width), rows 29 dp.
- **Syborg is no longer a target** (owner, 2026-11-21, user-side-smp.md): FA10 is not checked there.

## Not doing

- **Java (.jar, .jad):** no runtime is planned; Files shows the package details only.
- **Files over 4 GB:** FAT32 can't hold them; exFAT is in [filesystem.md](filesystem.md)'s Later list.
- **MTP:** E: is shared as mass storage (FS6), not MTP ([debug-access.md](debug-access.md)).
- **Copying the 2010 file manager:** its source (`oss.FCL.sf.app.files`, EPL, deleted, see
  [retired-repos.md](retired-repos.md)) is prior art for wording only; no code is copied.
