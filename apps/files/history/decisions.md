<!-- SPDX-License-Identifier: Apache-2.0 -->
# Files: build records and decisions, FA0–FA12

Part of [Apps](../../README.md) · Status: record · Updated: 2026-11-26

Moved out of [the Files plan](../README.md) on 2026-11-27: what each finished phase was checked with, and the
decisions taken while building FA1–FA11. The stage states live in the README's [Status](../README.md#status); FA12's
decisions stay there while FA12 is open.

## Build and test records (to 2026-11-26)

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
| FA12 | merged as it stands (2026-11-26: neoui#52, files#16 and this docs PR; the open issues go to FA12b, the A/V research in [video-sync.md](../video-sync.md)): videos play in a player like the board (`files2-view-video`): MP4, MOV, 3GP and Matroska/WebM; H.264 (Baseline to High), VP8 and VP9 pictures; AAC, Vorbis and Opus sound; ±10 s, the seek bar, pause, speed 0.5–2×, mute, rotate, full screen, the place kept per clip, the controls hiding after 3 s. All pure Rust and no_std (NeoSymbian forks of rust_h264, vp8-decoder, rusty_vp9 and symphonia; `shiguredo_mp4`; our Matroska reader); every fixture's pictures equal ffmpeg's bit for bit on the host. **Pixel (720p30 H.264 High + AAC, 2026-11-26):** portrait 28.5–30 fps shown with the conversion on its own thread (CPU 6; the UI thread 0–2 ms a picture), controls up 29.7 fps, landscape 23–27 fps (conversion 21–22 ms, split with a helper on an A55), the clip's end and rotating after it right, over 720p refused with a plain card; from the earlier runs MKV H.264, VP8+Vorbis and VP9 480p + Opus play and H.263 shows the error card. **Open (FA12b):** see *Known issues* under the FA12 decisions in [the README](../README.md#status) |
| FA9 M1b–M6, FA13 | proposed; next: the decoder choices, then M2 (MP3); M1b with the top panel's media session ([top-panel.md](../../../neoui-shell/top-panel.md) TP3: Files posts MEDIA and keeps playing in the background, owner 2026-11-21) |

## Decided while building FA1–FA8

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

## Decided while building FA9 (M0, M1)

- **ARMv7 now** (owner decision): the phone's NEOFILES is built with `cargo arm7` (`symbian/targets/armv7a-neosymbian-eabi.json`, a copy of e32-rs's: VFPv3 + NEON, the softfp calling convention, so Symbian calls are unchanged). Moving to ARMv8 AArch32 later (US4) swaps the target only. Syborg's 2010 kernel switches no VFP for user threads (GCCE), so the Syborg CI builds Files with `cargo arm`; the files CI builds and lints both. (Superseded by US4, 2026-11-25: one ARMv8 `cargo arm` build, `arm7` gone.)
- **Duplicates hash with xxh64:** xxhash-rust's xxh3 doesn't build for 32-bit ARM with NEON (its NEON code names `core::arch::aarch64` types; the 32-bit intrinsics are unstable). The hashes are only kept in memory.
- **The player is an FA7 viewer** (`Kind::Audio`): FA7's header (Share, ⋮ Show as hex… / Open with… / Details), Back, and the hex view with the reason for a file the decoders can't read. The folder's audio files are Next and Previous (the image viewer's folder list, now shared); shuffle and repeat (the folder, the track) stay while the player is open.
- **Playback runs on a worker** with its own NeoAudio session per track. Each WRITE carries about 50 ms of the track (WRITE blocks while the 250 ms queue is full, so the worker keeps pace with the speaker). After each WRITE it reads INFO, because NeoAudio sends no events. PREEMPTED (a call or the ringtone has the speaker) pauses the stream; it resumes where it was after the call (owner decision). The end of a track is the queue running empty after the decoder's last frame.
- **Leaving Files pauses** ("Stops when you leave Files."), unless a call has the speaker: then the track is held and resumes after the call. The screen going off doesn't hide an app, so music keeps playing with the screen off. With M1b (top panel TP3) leaving Files no longer stops it: the owner chose background playback (2026-11-21), and the footer text changes then.
- **What a file is** comes from its first bytes (`neo_format_media::probe`), not its name; `.aac` is an alias of the M4A row (the board's 55 types stay).
- **Accented tags draw:** Slint bakes only the glyphs its literals use (plus ASCII and the keyboard's alphabets), so the player carries the Latin-1 and Latin Extended-A letters ("Café", "Tunç").
- **Test images play muted** (`test-files`: the stream's own gain at 0, the media volume untouched); generated WAVs go to `C:\Data\fa9\`.

## Decided while building FA11 (2026-11-25)

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

## Decided while building FA10 (2026-11-21)

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
