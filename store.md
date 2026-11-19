<!-- SPDX-License-Identifier: Apache-2.0 -->
# NeoStore: apps for NeoSymbian (NEOSTORE, NEOINST, the store server)

Written 2026-11-18. This is the proposal for a new repo, `NeoSymbian/store`. NeoStore brings two kinds of app to the
phone and installs them there, with no ROM build:
- **classic S60 apps** (`.sis`, `.sisx`), which run in Old apps ([legacy.md](legacy.md));
- **new NeoSymbian apps**: Rust neoui apps in a new package format, `.npk`.

It has three parts:
- **a Go server** with Postgres and MinIO. It holds the apps, their texts, icons, banners and screenshots, the
  releases, the 5-star ratings and the reviews;
- **the phone app** `NEOSTORE.EXE`;
- **a trusted installer server** `NEOINST.EXE`, which installs both formats.

Nothing here is built yet.

**The design** is on the canvas's Store page (https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#page-af8ae2719594):
- 33 phone boards (`store-*`), drawn in Gestures, plus a Buttons row;
- 6 developer and admin web pages (`store-web-*`);
- the interactive prototype [`prototype`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-4bcd5e160a59);
- five spec sheets: [`spec-decisions`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-608e5fabb2da), [`spec-map`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-0e862b7a5e00), [`spec-npk`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-9abf29cffae0),
  [`spec-install`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-25c1f1c37a6d), [`spec-api`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-b65de07881be).

All of it was published 2026-11-18. Each board carries its phase tag (`PLANNED STn` or `PROPOSED`). The canvas is
private.

**Not the N8 store.** `~/WS/Symbian/NeoStore` serves the stock Nokia N8 at `store.notallow.cc` (Go stdlib, files on
disk, no database) and stays as it is (NS01). The new server shares no code with it. It does borrow three ideas:
pre-sized raw icons (`icon.565`), ETag + gzip on the index, and the category vocabulary.

## Decisions

From the console (owner, 2026-11-18):

- **NS01 A new backend.** The N8 NeoStore stays separate and untouched.
- **NS02 Postgres 17 + MinIO** on the Prod Infra (the `prod-infra` skill), with the app's own credentials. Dev uses
  the shared zdev Postgres; tests use testcontainers.
- **NS03 Ratings: an anonymous device key.**
  - The phone makes an Ed25519 key on first run.
  - One signed rating per app per phone: 1–5 stars plus optional text. Posting again replaces it.
  - Admins can hide reviews.
  - There are no user accounts on the phone.
- **NS04 Developers publish with review.**
  - Developers have accounts and upload releases and listings.
  - Everything waits in a review queue until an admin approves it.
- **NS05 New apps ship as `.npk`.** It is a zip with `manifest.toml`, the files and Ed25519 signatures. The manifest
  carries every fact a SIS package or an app registration carries, plus the facts only neoui needs
  ([the format](#the-package-format-npk)).
- **NS06 A Rust SIS installer: core features plus registry compatibility.**
  - It keeps: SIS v2 parsing, conditions, embedded SIS, SA/SP/PU upgrades, FileRun/FileText/FileNull, `\sys\hash`,
    our own package registry, and a Rust SisRegistry server behind the 2010 client DLL.
  - Certificate chains are shown, not trusted: the Symbian Signed roots expired in 2012.
  - It drops: OCSP (the servers are gone), Java, widgets, DRM and backup/restore.
  - This replaces the SWI port planned for legacy L4.
- **NS07 Capabilities.**
  - The user-grantable set is granted after a consent screen: NetworkServices, LocalServices, ReadUserData,
    WriteUserData, Location, UserEnvironment.
  - System capabilities are granted only when store review approves them.
  - A side-loaded package gets user capabilities only.
- **NS08 Tabs: Discover · Apps · Games · Updates.**
  - The header is `[NeoStore · search · ⋮]`.
  - Classic S60 apps sit in the same lists, with a CLASSIC S60 badge and a filter.
- **NS09 The board set:** the phone app (Gestures and Buttons rows, the prototype, the spec sheets) plus the developer
  and admin web console.
- **NS10 Sign-in: GitHub OAuth** for developers and the admin. No passwords are stored, and the owner's GitHub login is
  the admin.
- **NS11 Host: `store.neosymbian.org`.**
  - The web console uses HTTPS only.
  - The phone uses plain HTTP for `/v1` and `/dl` until it has TLS ([ST11](#phases)). A Cloudflare configuration
    rule turns off Always Use HTTPS for those two paths.
- **NS12 Old apps must be redistributable.**
  - Only freeware and open-source apps whose licence allows redistribution, or apps whose author gave permission.
  - Each release records its licence and the proof.

For the implementation (2026-11-18):
- **The repo:** `NeoSymbian/store`, laid out like `phone` and `files`.
- **UIDs:** the block **0xE0009xxx** (the next free one): `NEOSTORE` 0xE0009001, `NEOINST` 0xE0009002, `SISREGSRV`
  0xE0009003.
- **Third-party UIDs:** the store assigns them from **0xE1000000–0xE1FFFFFF**, one range per developer. Old SIS apps
  keep their own UIDs, and the package registry refuses a UID that another vendor already installed.
- **Protocol:** the store's neoui opcodes take the next free protocol version. 1.10 (HAPTIC) and 1.11 (Files
  FA1/FA2) are taken, so that is **1.12** today.
- **The phase prefix is ST.**

## Today

| Part | State |
|---|---|
| Installing old apps | Build time only. `legacy/tools/sis.py` unpacks `SIS=…` packages into the ROFS (`build/scripts/build-steps.sh`). No signature or hash checks, no E: targets, no conditions, no embedded SIS. |
| Installing new apps | They are compiled into neoui. `APPS`, `LAUNCHERS`, `PAGES` and `RESIDENT` are fixed tables in `neoui/symbian/src/host.rs`. The names are fixed in `shell.slint` and the tiles in `home.slint`/`menu.slint`. `connect` binds only EXEs the shell launched itself. |
| An EXE dropped on C: | It runs from the debug shell, but it's missing from the grid, OPEN refuses its key and `connect` returns `KErrNotSupported`. |
| HTTP on the phone | NEONET (neohw `crates/net`: DHCP, DNS, TCP) and ESOCK over it. No HTTP client library, only hand-written GETs (the Wi-Fi internet check). |
| TLS | none. rustls comes with browser WB4 (crypto provider, entropy) and WB6 (certificates). |
| Capabilities | ROM EXEs get all of them. `drive=c` EXEs get none; `exes.txt` can't set capabilities or VID. Whether PlatSec guards `C:\sys\bin` is unclear: `rust-integration.md` says the ROM doesn't enforce it, `kernel-issues.md` says it does. ST0 settles it. |
| Notifications | `NOTIFY` (1.8): at most 16 per app, with no progress field. |

## The repo

The layout of `phone` and `files` (a host workspace and a Symbian workspace), plus the Go server.

```
store/
  server/              Go (Apache): cmd/neostore {serve, migrate, admin}
    internal/db        pgx/v5, SQL migrations embedded (one table schema_migrations)
    internal/blob      minio-go; content-addressed by sha256
    internal/api       the phone API (/v1, /dl, /img)
    internal/web       html/template: developer console, admin review, GitHub OAuth (x/oauth2)
    internal/sis       a SIS v2 metadata reader (the controller only, for listings and review)
    internal/npk       manifest parse, signature check, store countersignature
  crates/
    npk/               Apache, no_std + alloc: manifest, zip reader (miniz_oxide), Ed25519 verify;
                       bin npk-pack (host)
    sis/               Apache, no_std + alloc: the SIS v2 reader and install planner (a port of
                       legacy/tools/sis.py, plus conditions, embedded SIS, upgrades, file actions)
    neo-http/          Apache: a small HTTP/1.1 client on neohw net::client (GET, Range, chunked)
    store-core/        Apache: catalogue model, API types, install state machine, device key
    store-ui/          GPL (Slint): the screens, host snapshots snapshots/store-*.png
  symbian/
    app/               NEOSTORE.EXE  0xE0009001  (GPL)
    inst/              NEOINST.EXE   0xE0009002  resident installer server (Apache, no Slint)
    sisreg/            SISREGSRV.EXE 0xE0009003  SisRegistry-compatible server (Apache)
    exes.txt
```

**Pins:** e32, neoui (`neoui-proto`, `neoapp`, `neoui-kit`), neohw (`net`) and Slint, by git rev. They must match
neoui's `symbian/Cargo.toml`. Nightly as in neoui. Go as in `server/go.mod`.

**Licences:** Apache-2.0 for the server, the crates, NEOINST and SISREGSRV. GPL-3.0 for `store-ui` and `symbian/app`,
which link Slint.

**CI:**
- server: `go vet`, `gofmt -l`, `go test ./...` (testcontainers Postgres + MinIO);
- host crates: `cargo fmt/clippy/test` and the snapshots; fuzz targets for `npk` and `sis`;
- device: `cargo arm`;
- neoui's `syborg.yml` clones store (as it clones files) and taps through it, with a local server on the runner.

## The package format (.npk)

The owner's rule: the manifest must cover every metadata need, now and later. The section has four parts:
1. a table of every fact a 2010 package, app registration or E32 header can carry, and where each one lands in
   `.npk`;
2. the facts only neoui has;
3. the manifest itself;
4. how a package is packed and signed.

The example is on [`spec-npk`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-9abf29cffae0).

**Not verified yet.** The workspace has no SWI or AppArc headers. These came from the public SIS v2 spec, from memory:
the SIS field-type IDs, the option bits, the expression operators and the reg-rsc field list. ST0 checks them against
`oss.FCL.sf.mw.appinstall` (pinned in `build/sources.lock`) and AppArc's `appinfo.rh` before `crates/sis` depends on
them. What `sis.py` reads today is confirmed.

### Every fact and where it goes

| Fact | Comes from | In `.npk` |
|---|---|---|
| package UID | SISInfo | `[package] uid` |
| vendor unique name, vendor names per language | SISInfo | `[package] vendor`, `[text.<lang>] vendor` |
| names per language, supported languages | SISInfo names[], SupportedLanguages | `[text.<lang>] name` |
| version (major.minor.build), creation time | SISInfo | `[package] version`, `code`, `created` |
| install type SA / SP / PU | SISInfo | `[package] install = new / patch / partial` (`upgrade` = SA over an older version) |
| install type PA / PP (preinstalled) | SISInfo | not used: nothing is preinstalled on removable media |
| ShutdownApps flag | SISInfo install flags | `[package] shutdown_apps` |
| user options, If/ElseIf variants (language, device, option) | SupportedOptions, If/ElseIf + Expression | none: one `.npk` per variant, and the store picks it. NEOINST still evaluates them in SIS. |
| target devices + version ranges | Prerequisites | `[requires] devices` |
| dependencies (UID + version range) | Prerequisites | `[requires] packages` |
| properties (int → int) | SISProperties | `[properties]` |
| installer logo | SISLogo | `[app] icon` (one image for both) |
| per-file target, `!:` drive | FileDescription | `[[file]] target` (`!:` = the drive the user picks) |
| per-file MIME | FileDescription | not needed: `[[handles]]` says what the app opens |
| per-file hash | FileDescription (SHA-1) | `[[file]] sha256` |
| file actions: install, run (RI, RR, RB, RW), text (TC, TS, TA, TE), null | FileDescription op + options | `[[file]] op`, `options` |
| capabilities | FileDescription capabilities, E32 header | `[[exe]] caps`. The header stays authoritative: NEOINST checks they match. |
| SID, VID, stack, heap, flags | E32 header | `[[exe]] sid`, `vid`, `stack`, `heap` |
| signatures + certificate chain | SignatureCertificateChain | `META/SIGNATURE` (developer) and `META/STORE` (store), Ed25519 |
| embedded packages | InstallBlock controllers | none: a dependency on another package instead |
| caption, short caption per language | LOCALISABLE_APP_INFO | `[text.<lang>] name`, `caption` (≤ 48 bytes, the ENTRY limit) |
| group (Games, …) | reg rsc `group_name` | `[text.<lang>] group` (Apps, Games). It also picks the default key pad for classic games. |
| hidden | reg rsc | `[app] hidden` |
| launch in background | reg rsc `launch` | `[app] background` |
| MIME types it opens + priority | reg rsc `datatype_list` | `[[handles]]` |
| views | reg rsc `view_list` | `[app] pages` |
| file ownership list, services, embeddability, newfile, opaque data | reg rsc | not used by neoui; kept under `[x-symbian]` if a tool needs them |

### What only neoui knows

These have no SIS or reg-rsc equivalent.

| Fact | Today | In `.npk` |
|---|---|---|
| app key (≤ 16 bytes): the address for OPEN, settings ownership, `APPS` | `host.rs` `APPS` | `[package] key` |
| named pages + page numbers + URI args | `host.rs` `PAGES`, `datetime.md` URIs | `[app] pages = [{name, page, uri}]` |
| launcher (draws a grid until FRONT) | `host.rs` `LAUNCHERS` | `[app] launcher` |
| resident (started at boot, never evicted) | `host.rs` `RESIDENT` | `[app] resident`: needs store review (it costs RAM at every boot) |
| tile icon (192 px, 72 dp on screen) and ENTRY icon (≤ 128 px ARGB) | `ui/icons/apps/*.svg`, `make_icons.py` | `[app] icon`, `entry_icon` |
| settings keys owned or shared, with type, default and limit | `neoui-proto` settings registry | `[[settings]]` |
| file-type handlers with "Always" | files FA8 (planned) | `[[handles]] types`, `page`, `priority` |
| minimum protocol, platform release | none | `[requires] protocol`, `platform` |

### manifest.toml

TOML, UTF-8, with `manifest.toml` as the zip's first entry. Unknown keys and sections are kept and ignored, so the
format can grow. NEOINST refuses a manifest whose `format` it doesn't know.

```toml
format = 1

[package]
key           = "tasks"          # neoui app key, ≤16 B
uid           = 0xE1000014       # package UID
vendor        = "Hayk Studio"
version       = "1.4.0"          # major.minor.build
code          = 14               # monotonic; updates compare this
created       = 2026-11-18T09:12:00Z
install       = "upgrade"        # new | upgrade | patch | partial
shutdown_apps = true

[text.en]
name    = "Tasks"
caption = "Tasks"
group   = "Apps"                 # Apps | Games
summary = "To-dos with reminders and a home widget"
[text.hy]
name    = "Առաջադրանքներ"

[requires]
protocol = "1.12"
platform = ">=0.9"
devices  = ["bonito", "sargo"]   # empty = all
packages = [{ uid = 0xE1000002, version = ">=1.0" }]

[[exe]]
file  = "sys/bin/TASKS.EXE"
uid3  = 0xE1000014
sid   = 0xE1000014               # = uid3 unless set
vid   = 0
caps  = ["ReadUserData", "NetworkServices", "Location"]
stack = "128K"
heap  = "1M"

[app]
exe        = "TASKS.EXE"
launcher   = false
resident   = false
hidden     = false
background = false
icon       = "icon.svg"          # or a 192 px PNG
entry_icon = "icon-128.png"      # optional
pages = [
  { name = "list",     page = 0, uri = "tasks:/list" },
  { name = "edit",     page = 1, uri = "tasks:/edit?id=" },
  { name = "settings", page = 2, uri = "tasks:/settings" },
]

[[handles]]
types    = ["text/calendar", ".ics"]
page     = "tasks:/import?path="
priority = "normal"              # high | normal | low | last

[[settings]]
key     = "tasks.sort"
type    = "u8"
default = 0

[[file]]
src    = "sys/bin/TASKS.EXE"
target = "!:\\sys\\bin\\TASKS.EXE"
sha256 = "9b1e…44d0"

[[file]]
src     = "private/readme.txt"
target  = "!:\\private\\e1000014\\readme.txt"
op      = "text"                 # install | run | text | null
options = ["continue"]           # run: install, remove, wait · text: continue, skip, abort, exit
sha256  = "51c0…7a2e"

[properties]
1 = 3
```

**The rules NEOINST enforces:**
- Files may only target `\sys\bin\` (names from `[[exe]]`), `\resource\apps\<key>\` and `\private\<sid>\` of the
  package's own EXEs.
- `\sys\bin` names must be unique on the phone unless this package owns them (an upgrade).
- `caps` must equal the E32 header's capabilities and fit NS07.
- `key` and `uid` must be unused, or belong to the same vendor key (an upgrade).

### Packing and signing

| # | Zip entry | Rule |
|---|---|---|
| 1 | `manifest.toml` | stored, never compressed; read before anything else |
| 2…n | the files (`sys/`, `private/`, `resource/`, icons) | stored or deflate (miniz_oxide on the phone) |
| n+1 | `META/SIGNATURE` | the developer's Ed25519 public key + a signature over `sha256(manifest.toml)` followed by every `(path, sha256)` sorted by path |
| n+2 | `META/STORE` | added by the server on approval: the store key's Ed25519 signature over the same digest + the review id |

- **`npk-pack`** (host, `crates/npk`) builds a package from a staticlib build. It takes an `exes.txt` line plus a
  `manifest.toml` and fills in sha256, stack, heap and caps.
- **`build/emitter/build_rust_exe.py`** gains `caps=` and `vid=` on `exes.txt` lines (today it can set neither) and an
  `npk=` output, so the same build makes the ROM image and a store package.
- **Developer keys** are registered in the console (`store-web-dev-release`). The store's key pair lives on the
  server. The phone has the public key built in, with a second slot for rotation.

## How it works

### The server

**Storage (NS02):**
- **Postgres** holds the rows; the schema is on [`spec-api`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-b65de07881be). The tables:
  - `developers`;
  - `apps` (slug, key, uid, platform `neo | s60`, kind `app | game`, category, licence, source, icon, banner, status,
    rating sum and count);
  - `app_texts` (per language);
  - `releases` (version, code, format `npk | sis | sisx`, blob, size, the whole extracted manifest as `jsonb`, caps,
    notes, status `draft | pending | approved | rejected`, reviewer, note, licence proof);
  - `blobs`, `screenshots`, `categories`, `collections`, `devices`, `ratings`, `downloads`, `audit_log`.
- **MinIO** holds packages, icons, banners and screenshots in one bucket, keyed by sha256.
- **Migrations** are numbered `.sql` files embedded in the binary, applied by `neostore migrate`.

**The phone API** (JSON, plain HTTP under NS11):

| Method | Path | What |
|---|---|---|
| GET | `/v1/index` | Every listed app, light: id, key, name, kind, platform, icon, rating, latest version + code, size, sha256. It has an ETag, and the `X-Neo-Sig` header carries the store key's signature over the body. |
| GET | `/v1/apps/{id}` | Texts, screenshots, banner, releases, capabilities, rating histogram, top reviews |
| GET | `/v1/apps/{id}/reviews?sort=&cursor=` | Reviews, paged |
| POST | `/v1/apps/{id}/rating` | `{stars, text, version, ts, pubkey, sig}`, signed by the device key. One per device: a new post replaces the old one. Rate-limited per key and per IP. |
| GET | `/v1/featured`, `/v1/categories`, `/v1/search?q=` | Banners and rows, the vocabulary, search (Postgres full text) |
| POST | `/v1/updates` | Body: installed `(uid, code)` pairs. Returns the available updates. |
| GET | `/dl/{sha256}` | The package, proxied from MinIO, with Range |
| GET | `/img/{sha256}?w=&fmt=png\|argb` | Images pre-sized for the phone. `argb` is raw pixels, so the phone needs no PNG or JPEG decoder for icons. |

**The web console** (NS04, NS10) is HTML from `html/template`. It uses a GitHub OAuth session cookie and CSRF tokens
on every form. The pages:
- **Sign in:** [`web-signin`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-fa9c40f7be3a).
- **My apps:** [`web-dev-apps`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-d86869e10001).
- **The listing editor:** title, short and full description, category, kind, licence, source, the icon (512 px),
  a 1080×480 banner, 2–8 screenshots. [`web-dev-listing`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-95477f374bcd).
- **New release:** an `.npk` or `.sis`/`.sisx` upload. The server reads the manifest or the SIS controller,
  checks the developer signature and flags new capabilities. [`web-dev-release`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-c1db1c79ae63).
- **Admin, the review queue:** releases and reported reviews. [`web-admin-queue`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-e577a9a701a0).
- **Admin, a review:** the extracted metadata, the capability diff, the licence proof (NS12), and Approve, Ask for
  changes or Reject with a note. [`web-admin-review`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-e483852bb49a).

Approve countersigns the package (`META/STORE` for `.npk`; a detached record for SIS) and republishes the signed
index. Listing changes go through the same queue.

**Deploy:** a ZimaOS app per the `zimaos` skill. It uses its own Postgres database and role and its own MinIO bucket
and key on Prod Infra. The tunnel serves `store.neosymbian.org`. ST1 first checks that the `neosymbian.org` zone is
on Cloudflare; the website `neosite` is on Vercel.

### The phone

**Processes:**

| Process | UID | Role |
|---|---|---|
| `NEOSTORE.EXE` | 0xE0009001 | The UI. It fetches the catalogue, downloads packages and posts ratings. It holds no system capability, only NetworkServices. |
| `NEOINST.EXE` | 0xE0009002 | A resident installer server in the ROM, with TCB and AllFiles. The only writer of `\sys\bin`, `\resource` and the package registry. |
| `SISREGSRV.EXE` | 0xE0009003 | Serves `RSisRegistrySession` for old apps that query installed packages, behind the 2010 `sisregistryclient.dll` (ST9). |
| `SYSSTART.EXE` | 0xE0002001 | neoui: the app registry, the Apps grid, OPEN (ST4). |
| `LEGACY.EXE` | 0xE0002006 | The Old apps grid. It re-publishes after an AppArc change. |

**The pipeline** ([`spec-install`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-25c1f1c37a6d)):
1. **Fetch.** NEOSTORE reads `/v1/index` through `neo-http` on NEONET and checks `X-Neo-Sig`. The last good index
   is cached in `C:\private\e0009001\`, so Discover works offline ([`offline`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-a5d6fba0d114)).
2. **Download.** `/dl/{sha256}` goes to `C:\private\e0009001\dl\`, with Range resume. Progress shows in the button
   ([`downloading`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-42cb74e6cc31)) and in the shade ([`shade`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-26e1d76ed174)).
3. **Verify.** NEOINST `VERIFY`:
   - the sha256 matches the index;
   - `META/STORE` and `META/SIGNATURE` are valid (for SIS, the store's detached record);
   - the key and UID belong to this vendor;
   - `[requires]` is met.
4. **Consent.** The capability sheet ([`consent`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-118ab796bc7a), NS07). For a SIS, also its language, drive and option
   choices and its FileText dialogs ([`sis-options`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-04c8824816e0)).
5. **Copy.** NEOINST `INSTALL` writes to a temporary name, then renames. On any error it rolls back, and nothing is
   left half-installed ([`install-error`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-beaa08ab6295)). For E: it also writes `\sys\hash\` entries, as SWI did.
6. **Register.**
   - `.npk`: NEOINST sends `REGISTER` to SYSSTART, and the app joins the grid, OPEN and `connect`.
   - SIS: the `_reg.rsc` goes into AppArc's import folder, and LEGACY re-publishes the Old apps grid.
7. **Record.** One file per package in `C:\private\e0009002\packages\`: uid, key, vendor, version, code, source
   (store or side-load), the granted caps, and every file with its sha256. FileRun-on-uninstall and FileNull entries
   are recorded for uninstall.
8. **Done.** A toast and a shade entry with Open ([`installed`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-338d889e6ca1)). Uninstall replays the record in reverse,
   runs the RR and FN actions and sends `UNREGISTER` ([`uninstall`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-5c5159a21e52)).

**inst-ipc 1.0** (NEOSTORE, Files and Settings → NEOINST):

| Op | Arguments | Returns |
|---|---|---|
| `VERIFY` | path | manifest summary, caps, signer, problems |
| `INSTALL` | path, drive, granted caps, SIS options | job id (async) |
| `WATCH` | job id | progress %, phase, error (async) |
| `UNINSTALL` | package uid | job id |
| `LIST` | — | installed packages: uid, key, version, code, drive, size, source |

**Protocol 1.12 (neoui):**
- `REGISTER {key, exe, uid, caption per language, icon, pages, launcher, resident, hidden, handles}` and
  `UNREGISTER {key}`. Only NEOINST's SID is accepted.
- The registry persists in `C:\private\e0002001\apps\` and is read at boot.
- `APPS`, the names in `shell.slint` and the tiles in `home.slint`/`menu.slint` become the ROM's built-in entries in
  the same registry.
- The Apps grid becomes a model and no longer a fixed Slint list.
- OPEN and `connect` accept registered keys.
- `Notification` gains an optional `progress` (0–100), for the download entry.

**The device key (NS03):**
- An Ed25519 key in `C:\private\e0009001\device.key`, made on first run.
- Reviews show the first four hex digits of the public key ("Device 9C41").
- Settings can reset it: the old ratings stay but can no longer be edited ([`settings`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-2d739b3f8410)).

**Security until TLS:** the index signature, the package sha256 and the package signatures protect integrity over
plain HTTP. Privacy is not protected: anyone on the network can see which apps a phone browses. ST11 moves the
phone to HTTPS.

### The screens

From the canvas (the full table is on [`spec-map`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-0e862b7a5e00)):
- **Discover:** a featured banner carousel, then rows "New for NeoSymbian", "Classic S60 apps" and "Top rated".
  [`discover`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-2ab0bd3ae9ca), [`discover-loading`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-13ef84fd3759), [`offline`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-a5d6fba0d114).
- **Apps and Games:** category chips, sorted lists with stars and size, a filter sheet (platform, rating).
  [`apps`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-9ef244c7a60f), [`games`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-0bcd1b1850a5), [`category`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-01578e09938b), [`filter`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-7fd89bd4aee9).
- **Search:** recent queries and categories, then results with platform chips. [`search`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-74430da5a9a5),
  [`search-results`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-797df93ddbdc).
- **The app page:** icon, name, developer, platform badge; then rating, size, version and category; then Install,
  screenshots, the description, and ratings with a histogram.
  - Classic apps add a "Runs in Old apps" card with licence and signer.
  - Installed apps show Open, Uninstall and Update.
  - [`app`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-2f38a283d1c7), [`app-classic`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-05c811454b3c), [`app-installed`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-1c61fbcaae8c), [`screens`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-6ee5ca7d347d), [`about`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-eedbe11abe2c).
- **Install:** [`consent`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-118ab796bc7a), [`downloading`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-42cb74e6cc31), [`installing`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-8b4a1a4915c5), [`installed`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-338d889e6ca1),
  [`install-error`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-beaa08ab6295), [`sis-options`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-04c8824816e0), [`shade`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-26e1d76ed174).
- **Updates:** the count badge on the tab, Update all, then the installed list. [`updates`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-cde1c41781a7),
  [`updates-empty`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-78a528d3f9f8), [`library`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-413d62f4389a), [`uninstall`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-5c5159a21e52).
- **Ratings:** [`rate`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-614f282e5550), [`reviews`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-b8a64fe52686), [`review-mine`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-f215389ade3e).
- **Menu and settings:** auto-update on Wi-Fi, mobile data, install drive, show Classic apps, server, device key.
  [`menu`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-2b5f6bf2f828), [`settings`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-2d739b3f8410).
- **Side-load:** an `.npk` opened in Files. It shows a "Not from NeoStore" warning and gets user capabilities only.
  [`sideload`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-808545ab7c45).
- **Buttons mode:** [`b-discover`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-8c686ed8651c), [`b-app`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-44be6aa1cef6).

## Platform gaps

| Need | Today | Needs | Where | Phase |
|---|---|---|---|---|
| Know whether PlatSec guards `C:\sys\bin` and checks capabilities at load | the docs disagree | a test EXE with caps on C:, a write from a cap-less process | kernel, build | ST0 |
| An HTTP client | hand-written GETs | `neo-http`: HTTP/1.1, Range, chunked, redirects to the same host | store (later shared with the browser) | ST0, ST7 |
| TLS | none | rustls + a certificate store (browser WB4/WB6) | browser, e32-rs | ST11 |
| Capabilities on built EXEs | `exes.txt` sets none | `caps=`, `vid=` in `build_rust_exe.py` | build | ST3 |
| Apps the shell doesn't know at build time | fixed `APPS`/grid, `connect` only for its own launches | the registry, `REGISTER`, protocol 1.12 | neoui | ST4 |
| A trusted writer of `\sys\bin` | none | NEOINST in the ROM with TCB | store, build | ST5 |
| Install SIS on the phone | build time only | `crates/sis` in NEOINST | store, legacy | ST6 |
| Old apps grid updates live | rebuilt when LEGACY starts | watch AppArc's change notification, or re-publish on a NEOINST event | legacy | ST6 |
| Progress in the shade | `Notification` has none | an optional `progress` field | neoui | ST5 |
| `RSisRegistrySession` for old apps | none | SISREGSRV + the 2010 client DLL in the ROM | store, build | ST9 |
| Open `.npk`/`.sis` from Files | the Package board only | `store:/install?path=` | files, store | ST10 |

## Phases

Each phase ends with host tests, and for the phone, the Syborg CI and the Pixel.

| Phase | Work | Repos | Gate | Boards |
|---|---|---|---|---|
| **ST0** spikes | PlatSec on `C:\sys\bin` and capabilities at load (a test EXE); an HTTP GET over NEONET from a Rust app; the SIS enums, option bits and reg-rsc fields checked against mw.appinstall and AppArc; `neosymbian.org` zone check | kernel, build, store, docs | the answers are written into this doc | — |
| **ST1** the server | Repo, schema and migrations, MinIO blobs, `/v1/index` (signed), `/v1/apps`, `/dl`, `/img`, `neostore admin import` (adds an app from a `.sis` with its texts and images); deploy on ZimaOS at `store.neosymbian.org` | store | `go test` green against testcontainers; the index of 3 imported classic apps verifies with the store key | [`spec-api`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-b65de07881be) |
| **ST2** the console | GitHub OAuth, developers, listing editor, release upload with manifest/SIS extraction, review queue, approve and countersign, hide reviews, audit log | store | a developer uploads, the admin approves, the index changes; CSRF and role tests | [`web-signin`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-fa9c40f7be3a), [`web-dev-apps`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-d86869e10001), [`web-dev-listing`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-95477f374bcd), [`web-dev-release`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-c1db1c79ae63), [`web-admin-queue`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-e577a9a701a0), [`web-admin-review`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-e483852bb49a) |
| **ST3** `.npk` | `crates/npk` (manifest, zip, signatures) + fuzzing; `npk-pack`; `caps=`/`vid=`/`npk=` in build | store, build | NEOKIT packed as `.npk` round-trips; a tampered file or manifest is refused | [`spec-npk`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-9abf29cffae0) |
| **ST4** the app registry | Protocol 1.12 `REGISTER`/`UNREGISTER`; the registry file; the built-in apps moved into it; the grid as a model; OPEN and `connect` for registered keys | neoui | a registered test EXE on C: shows on the grid, opens a page and connects; the ROM apps are unchanged | — |
| **ST5** NEOINST for `.npk` | inst-ipc 1.0, verify, consent, atomic copy and rollback, the package record, uninstall, `Notification.progress` | store, neoui, build | install, upgrade, uninstall of a test app on the Pixel; power cut mid-install leaves the old version | [`consent`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-118ab796bc7a), [`installing`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-8b4a1a4915c5), [`installed`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-338d889e6ca1), [`install-error`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-beaa08ab6295), [`uninstall`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-5c5159a21e52), [`shade`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-26e1d76ed174) |
| **ST6** SIS on the phone | `crates/sis` (conditions, embedded, SA/SP/PU, FR/FT/FN, `\sys\hash`), AppArc registration, LEGACY live re-publish; replaces legacy L4's SWI port | store, legacy | X-plore and Frozen Bubble installed at runtime from C: and E: match the ROM-built ones; uninstall leaves no files | [`app-classic`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-05c811454b3c), [`sis-options`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-04c8824816e0) |
| **ST7** NEOSTORE v1 | `neo-http`, the index cache, the four tabs, search, app page, screenshots, download with resume, updates and Update all, installed apps, settings | store | every phone board matches its host snapshot; a 200-app index scrolls smoothly; Discover works offline | [`discover`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-2ab0bd3ae9ca), [`apps`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-9ef244c7a60f), [`games`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-0bcd1b1850a5), [`category`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-01578e09938b), [`filter`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-7fd89bd4aee9), [`search`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-74430da5a9a5), [`search-results`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-797df93ddbdc), [`app`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-2f38a283d1c7), [`app-installed`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-1c61fbcaae8c), [`screens`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-6ee5ca7d347d), [`about`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-eedbe11abe2c), [`downloading`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-42cb74e6cc31), [`updates`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-cde1c41781a7), [`updates-empty`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-78a528d3f9f8), [`library`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-413d62f4389a), [`menu`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-2b5f6bf2f828), [`settings`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-2d739b3f8410), [`offline`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-a5d6fba0d114), [`discover-loading`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-13ef84fd3759), [`b-discover`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-8c686ed8651c), [`b-app`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-44be6aa1cef6) |
| **ST8** ratings | The device key, signed ratings, reviews list and sort, my review, server rate limits and hiding | store | one rating per device enforced; a forged signature is refused | [`rate`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-614f282e5550), [`reviews`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-b8a64fe52686), [`review-mine`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-f215389ade3e) |
| **ST9** SisRegistry compat | SISREGSRV with the 2010 `sisregistryclient.dll`: installed packages, versions, files | store, build | an old app that queries the registry sees the packages installed in ST6 | — |
| **ST10** links | Files opens `.npk`/`.sis` in `store:/install?path=` (replaces the Install button on files' Package board, FA13); Settings → Apps uninstalls and shows granted caps | files, neoui, store | a side-loaded `.npk` from E: installs with user caps only | [`sideload`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-808545ab7c45) |
| **ST11** HTTPS | `neo-http` over rustls once browser WB4/WB6 land; drop the plain-HTTP rule | store, browser | the phone talks only HTTPS to the store | — |

**Order:**
- ST0 first.
- ST1 → ST2 is the server line, which can start at once.
- ST3 → ST4 → ST5 is the `.npk` line.
- ST6 needs ST5's NEOINST.
- ST7 needs ST1 and ST5. ST8 needs ST7. ST9, ST10 and ST11 come last.
- The prototype ([`prototype`](https://claude.ai/artifact/RsLEm6u3dCW6Q88R7LkhtZ#artboard-4bcd5e160a59)) walks Discover → app → consent → download → installed → rate, and the
  Updates tab.

## Status (2026-11-18)

| Part | State |
|---|---|
| The design (39 screen and web boards, the prototype, 5 spec sheets) | done, on the canvas |
| N8 NeoStore (`store.notallow.cc`) | running, separate (NS01) |
| ST0–ST11 | proposed; the repo isn't created yet |

## Not doing

- **Paid apps, in-app purchases, DRM.**
- **Java (`.jar`/`.jad`), WRT widgets, Qt `.sis` runtimes** as store items. A Qt or Open C runtime is a dependency
  package, if an app needs one.
- **OCSP and the Symbian Signed trust chain:** the servers are gone and the roots expired. The certificate is shown;
  trust comes from store review.
- **User accounts on the phone** and syncing ratings across devices (NS03).
- **Hosting old apps without redistribution rights** (NS12).
- **Copying the 2010 SWI or Ovi Store client code:** the 2010 sources (EPL) are reference for formats and behaviour
  only.
