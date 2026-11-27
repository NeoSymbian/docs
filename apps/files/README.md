<!-- SPDX-License-Identifier: Apache-2.0 -->
# Files: the file manager (NEOFILES v2)

Part of [Apps](../README.md) · Status: active · Updated: 2026-11-26

Written 2026-11-17. This is the implementation proposal for the Files app: a new `NeoSymbian/files` repo, every screen
of the design canvas's Files page, the platform work it needs, and the phases FA0–FA13. Since FA0 the app lives in
[NeoSymbian/files](https://github.com/NeoSymbian/files). What is built is in [Status](#status).

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
- **CI:** neoui's Syborg job (retired in US5) cloned NeoSymbian/files, built `libneofiles.a`, then tapped through drives,
  `Z:\Sys\Bin`, `estart.txt`, makes and deletes `C:\neo\` and makes `C:\дом\`; since US6b neoui's `virt-taps`
  workflow does this on QEMU `virt`. The files repo's own CI ran the model's tests and snapshotted R8's five screens
  (`snapshots/files-*.png`).
- **Speed:** the open animation averages 20.5 ms a frame, over the 16.7 ms budget ([smooth-ui.md](../../neoui-shell/smooth-ui.md)).

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
  with its baseline (diffs uploaded); arm: `cargo arm --locked`, the EXE size and heap budget. The Files taps run in
  neoui's `virt-taps` workflow on QEMU `virt` (US6b; Syborg's job was retired in US5).
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
| Add an event to a calendar | done (2026-11-26, files#18): an .ics opens NEOCAL's import page ([datetime.md](../datetime.md) DT6) | — | datetime | FA7 |
| Fonts at run time (the font viewer) | done (FA7): our rasteriser over `ttf-parser` in `neo-format-inspect` | installing a font for other apps | files | FA7 |
| Open with, file types | done (FA8): neoui protocol 1.12 (`OPEN_FILE`, `DONE_FILE`), the handler table `neoui_proto::open`, Files' PICK/SAVE pages, e32's `SharedFile` (`EFsFileAdopt`) | a registry of installed apps' types (store ST) | neoui, e32-rs | FA8 |
| Copy and paste files | done (FA8): CLIP's kind (paths to copy or move) | — | neoui | FA8 |
| Audio out | done: NeoAudio in AUDIOD.EXE ([../../hardware/audio.md](../../hardware/audio.md) A0–A8): S16LE streams at 8–96 kHz, mixed to mono; FA9's player is a client | events (no end-of-stream or call notice: the player polls INFO), a media session for the shade (M1b) | neohw, neoui | FA9 |
| FP/NEON for apps | done: the kernel saves Q0–Q15 per thread (WB1, 2026-11-17); all Rust builds for ARMv8 AArch32 with NEON (`cargo arm`, [US4](../../user-side/user-side-smp.md), 2026-11-25; FA9's `cargo arm7` is gone) | — | e32-rs, neoui, build | FA9–FA12 |
| Video | the FA12 player: pure-Rust decoders on the A75s, conversion on its own thread (2026-11-26) | A/V after key frames, VP9 720p and 1080p (FA12b, [video-sync.md](video-sync.md)) | files | FA12 |
| Share E: over USB, Eject | FS6 researched, not started | E: removable (`a64_medblk.cpp`), a DWC3 PSL, mass storage in the ROM, USB power on cold boot, dismount in e32 | kernel, build, e32-rs | FA13 |
| Send via Bluetooth | — | OBEX, hardware/bluetooth.md B5 | neohw | FA13 |
| Send by MMS | SMS only | MMS, hardware/modem.md C10 | neohw, phone | FA13 |
| Install .sis / .sisx / .npk | unpacked at build time (`legacy/tools/sis.py`) | NEOINST on the device, store.md ST6 + ST10 (was SWI, legacy.md L4) | store, legacy | FA13 |
| Install .jar | no Java runtime | a runtime | — (not planned) | — |
| Files over 4 GB | FAT32 | exFAT ([../../storage/filesystem.md](../../storage/filesystem.md), Later) | kernel | — |
| Trusted certificates | not built | a certificate store ([browser WB6](../browser/wb6-services.md)) | browser, build | FA7 (view only) |

## Phases

Each phase ends with a gate: host tests and board snapshots in the files repo, then the Pixel (and, from US6b, the UI taps on QEMU virt).

| Phase | Work | Repos | Gate | Screens |
|---|---|---|---|---|
| **FA0** move | Create `NeoSymbian/files`; `neoui-files` → `files-core`, the app → `symbian/app` + `crates/files-ui`; UID 0xE0006001; CI. neoui drops `crates/neoui-files`, `symbian/apps/files`, the NEOFILES line, the shell mock and its snapshots, and clones the files repo in its CI (`syborg.yml` then; `virt-taps.yml` since US6b). No behaviour change. | files, neoui, docs | the R8 taps pass on Syborg from the new repo; host snapshots of today's screens | today's app: [`pat-files-refresh`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-bc9bc3e4da54), [`pat-files-select`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-b403f3b83e97) |
| **FA1** v2 browsing | The footer tabs, the Browse tab, folder list and grid, breadcrumb, folder ⋮, Sort sheet, empty folder, New folder, Z: read-only, Buttons mode; `ftile` icons for all 55 types; `files.*` settings keys; `EFsDrive` | files, neoui, e32-rs | every board below matches its snapshot; Back order of the spec | [`browse`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-3b00261f7f9d), [`folder-list`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-093a3d3f2dcf), [`folder-grid`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-f0cdc90d8458), [`folder-menu`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-e17e53bf193d), [`sort`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-47b52b42f241), [`folder-empty`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-ba0077b3f140), [`new-folder`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-09c4d3dc5e89), [`rom`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-9ada2c720ef0), [`browse-buttons`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-ae34e51279fc), [`folder-buttons`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-2d6172009655), icons [`spec-icons`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-93754f2cea38), headers [`spec-headers`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-c80d46adfa71) |
| **FA2** file operations | `neo-fs` + `files-ops`; selection header and ⋮, copy/move with the paste bar, progress (toast + shade entry, Cancel), clash, rename, delete into `.trash` with Undo; folder refresh by change notification; attributes | files, e32-rs | host tests with the fake (full disk, drive removed, power cut mid-move); a 2 GB copy C:→E: on the Pixel | [`select`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-9bedc9d6d4ab), [`select-menu`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-c972e3173d2c), [`paste-bar`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-ebac5e347da8), [`progress`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-1c8b970f65c6), [`clash`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-1726a0c853b3), [`delete`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-3f1185a0b7d9), [`rename`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-cb84232c1485), pattern [`pat-files-select`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-b403f3b83e97) |
| **FA3** find and tidy | Recent (Files' own list), Types (an index built by a worker, kept in `C:\private\e0006001\`), search with filters, Recycle bin (restore, empty, 30 days), Free up space (large files, old downloads, duplicates by size then hash), Details | files | search of E: under a set time on the Pixel; bin survives a reboot | [`recent`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-d48ee7f12f4e), [`types`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-b25e04de395a), [`type-images`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-f223378dc344), [`type-docs`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-f0772ec49764), [`search`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-fed7da8f354a), [`search-filters`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-3fc3efedcca3), [`bin`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-cde87383eb63), [`cleanup`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-08374822da0c), [`details`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-0428c730f1ce), pattern [`pat-files-search`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-d1f71b42fbde) |
| **FA4** text and code | `neo-format-text`: the text viewer (wrap, line numbers), the editor (19 text types; highlighting with our own lexers on `logos`; undo; find and replace; the code-key row), Markdown Preview, CSV/TSV table editing (`csv-core`), New file, the unsaved-changes dialog | files | edits round-trip byte-exact (encodings, line ends); a 5 MB log opens | [`view-text`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-4279a4f341e5), [`edit-code`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-4db6131c88c3), [`edit-find`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-7f8fb0ab48f6), [`edit-md`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-2e0af6ea745a), [`edit-csv`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-5d514d4e7945), [`new-file`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-428e95273bb3), [`edit-unsaved`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-538e2a9100d7), [`edit-buttons`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-e87d42c5045a) |
| **FA5** images | `neo-format-image`: JPEG, PNG, GIF, WebP, BMP, a bounded SVG subset; thumbnails in the grid and the Types tab (a worker, a cache); the image viewer (zoom, swipe, strip); the image editor (rotate, crop, resize, save a copy as JPEG/PNG) | files | a 12 MP JPEG opens within the heap; thumbnails don't block scrolling | [`view-image`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-58724838c247), [`edit-image`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-babc1c91e924), [`folder-grid`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-f0cdc90d8458), [`type-images`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-f223378dc344) |
| **FA6** archives | `neo-format-archive`: zip (read, write, deflate with `miniz_oxide`), gzip, tar; browse inside an archive read-only, Extract here / to…, Compress the selection | files | zip-slip and bomb tests; a 1 GB zip extracts on the Pixel | [`zip-browse`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-125122954e14), [`extract`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-9ed03d5b90ed), [`compress`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-70a253041365) |
| **FA7** cards and inspectors | vCard and iCal viewers and forms (`neo-format-pim`, unknown properties kept); "Add to Contacts" through a new Contacts OPEN page; "Add to Calendar" once a calendar store exists; font viewer (`ttf-parser` + our rasteriser); certificate viewer (`x509-cert`, view only); app package info (.sis header, .jad); unknown type with hex | files, phone, (calendar) | vCard round trip with phone's `vcard.rs`; each viewer on a corrupt fixture shows an error, not a panic | [`view-vcf`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-0be7ab9b0592), [`edit-vcf`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-11eec67bbda5), [`view-ics`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-b0c7d55e26eb), [`edit-ics`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-eb6a23e083f9), [`view-font`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-ea84c2ddd0f6), [`view-cert`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-9a9f15522173), [`view-app`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-093a96e8c80a), [`view-unknown`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-676d4c8645cf) |
| **FA8** open with, share, pick | Protocol 1.10 in neoui: a handler table (file type → app keys, with "Always"), a file clip, file handles past 256-byte paths; Files as the system file picker (an OPEN page that returns a path with DONE, for Save as and attachments); the Open with and Share sheets (Copy path, Copy to clipboard; Bluetooth and MMS wait for FA13) | neoui, e32-rs, files | an image opens from Files in Photos (once Photos exists) and Photos' "attach" picks through Files | [`open-with`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-758bbdc3cb11), [`share`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-3db79c4164d1) |
| **FA9** audio | stages M0–M6: M0 the ARMv7 build (replaced by US4's ARMv8 build); M1 the player + WAV; M1b now playing in the shade (the media session, [top-panel.md](../../neoui-shell/top-panel.md) TP3); M2 MP3; M3 FLAC, Ogg Vorbis, Opus; M4 AAC/M4A, AMR; M5 MIDI; M6 docs. `neo-format-media` over NeoAudio (AUDIOD); "Open in Music" disabled until a Music app | files, neoui | an MP3 plays on the Pixel without gaps; a call interrupts it | [`view-audio`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-84826f21b3aa) |
| **FA10** documents I | EPUB (zip + XHTML, reflow, chapters, position), docx / odt / rtf reflowed, xlsx as a read-only grid (`xmlparser`) | files | a 300-page EPUB pages smoothly; the docx with Armenian text from the board renders | [`view-epub`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-a7f9e4db02c8), [`view-docx`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-eb23122f75d9), [`view-xlsx`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-636480de5643) |
| **FA11** documents II | PDF: parse (`hayro-syntax`), our renderer (paths, text with embedded fonts, images), pages, thumbnails | files | the boarding pass from the board renders; a 100-page PDF scrolls | [`view-pdf`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-7c18c7fd6f77) |
| **FA12** video | the NEON build (smooth-ui S4; ARMv8 since US4) first; then a decoder for MP4/3GP (H.264 baseline) and WebM (VP8), with the audio service | kernel, files | a 720p clip plays on the Pixel | [`view-video`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-0a854b5f4d99) |
| **FA13** outside Files | Share E: over USB and Eject (FS6); Send via Bluetooth (B5); MMS (C10); install .sis on the device (L4); heic, mkv, 7z, rar, pptx | kernel, build, neohw, legacy | each in its own repo's stages; Files only wires the buttons | [`share`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-3db79c4164d1), [`view-app`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-093a96e8c80a), [`spec-types`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-addb580badcb) |

The replacement map (old boards → new) is [`spec-replace`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-79a68f1005f5).

**Order:** FA0 → FA1 → FA2 are the base, in that order. FA3–FA8 can follow in any order (FA8 changes neoui's
protocol, so it goes with a neoui release). FA9–FA12 depend on platform work and run beside it. *Estimate:* FA0–FA2
about 1 month, FA3–FA8 about 2–3 months, FA9–FA12 several months each, mostly platform work.

## Status

<!-- stages -->
| Stage | What | State | Updated | Next / evidence |
|---|---|---|---|---|
| FA0 | Move Files to its own repo | done | 2026-11-17 | files `624fb01`, neoui#14; Pixel RAM boot |
| FA1 | v2 browsing, footer tabs, icons | done | 2026-11-18 | files `4ed71d4`, e32-rs `0489694`, neoui `2047404` |
| FA2 | Copy, move, trash, paste bar | done | 2026-11-18 | same PRs as FA1; protocol 1.11 progress in the shade |
| FA3 | Recent, Types, search, bin, cleanup | done | 2026-11-18 | files `559c508` + `f00af5f`; Pixel: bin survives a reboot |
| FA4 | Text and code viewer and editor | done | 2026-11-18 | files `e42811c`; Pixel: 5 MB log opens, byte-exact saves |
| FA5 | Images: decoders, thumbnails, editor | done | 2026-11-19 | files#6; Pixel: 12 MP JPEG in 310 ms |
| FA6 | Archives: zip, gzip, tar | done | 2026-11-19 | files#7; Pixel: 1 GB zip extracts in 70 s |
| FA7 | vCard, iCal, fonts, certificates, hex | done | 2026-11-20 | files#8, phone#7; Add to Calendar later in files#18 (DT6) |
| FA8 | Open with, share, file picker | done | 2026-11-20 | e32-rs#7, neohw#11, neoui#27, files#9 |
| FA9 M0–M1 | Audio player and WAV | done | 2026-11-21 | files#10; the incoming-call test not run |
| FA9 M1b–M6 | Background play, MP3 to MIDI | open | 2026-11-21 | next: decoder choices, then M2 (MP3); M1b needs top panel TP3 |
| FA10 | EPUB, docx, odt, rtf, xlsx | done | 2026-11-21 | files#11; Pixel-tested except pinch |
| FA11 | PDF viewer (hayro fork) | done | 2026-11-25 | files#14, docs#64; Pixel-tested except pinch |
| FA12 | Video player: H.264, VP8, VP9 | active | 2026-11-26 | neoui#52, files#16; 720p30 plays on the Pixel; V5, V6, release layout open |
| FA12b | A/V sync and speed fixes | open | 2026-11-26 | seven steps in video-sync.md (FA12b plan); step 1 verifies files `fb90512` on the Pixel |
| FA13 | Outside Files: USB, Bluetooth, MMS, .sis | open | — | each in its owner's stages (FS6, B5, C10, ST10) |
<!-- /stages -->

What each finished phase was checked with (commits, Pixel numbers) and the decisions taken while building FA1–FA11
(settings, jobs, decoders, archives, safety, PDF, documents) moved to [history/decisions.md](history/decisions.md) on
2026-11-27. FA12's decisions stay here while FA12 is open; FA12b's ranked steps are the
[FA12b plan](video-sync.md#fa12b-plan).

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
  - **Without kernel#44** (the media boost) the A75s sit at 300 MHz and decoding is slower; kernel#44 and e32-rs#17
    were merged on 2026-11-26.
  - **Not done:** V5 thumbnails, the review (V6), the 206 ms jump after resume, and the release layout (NEOFILES is
    17.5 MB: the ROFS, owner's decision).

## Not doing

- **Java (.jar, .jad):** no runtime is planned; Files shows the package details only.
- **Files over 4 GB:** FAT32 can't hold them; exFAT is in [../../storage/filesystem.md](../../storage/filesystem.md)'s Later list.
- **MTP:** E: is shared as mass storage (FS6), not MTP ([../../developer-tools/debug-access.md](../../developer-tools/debug-access.md)).
- **Copying the 2010 file manager:** its source (`oss.FCL.sf.app.files`, EPL, deleted, see
  [../../history/retired-repos.md](../../history/retired-repos.md)) is prior art for wording only; no code is copied.
