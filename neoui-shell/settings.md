<!-- SPDX-License-Identifier: Apache-2.0 -->
# Shell settings store

**Status: done 2026-11-09 (neoui `22af6ac`).** One store for the shell and every app (`neoui-proto::settings`,
`SETTING_GET`/`SET`/`WATCH`). Moved here from `neoui-shell.md` Part 1 on 2026-11-21; the hub is [../neoui-shell.md](../neoui-shell.md).
The keys the top panel adds (`shell.*`, `notify.*`, `island.*`, `lock.*`) are listed in [top-panel.md](top-panel.md#settings-keys).

## Part 1: settings store (done 2026-11-09)

As built. It changes the first sketch: typed keys, a registry, change subscriptions per prefix, and the pure logic
in `neoui-proto`.

### Where it is
| Path | What |
|---|---|
| `neoui-proto/src/settings/value.rs` | `Value` (`Bool`, `Int(i32)`, `Str` ≤ 64 B, `Bytes` ≤ 2 KB), `ValueType`; one encoding (tag byte + payload) for IPC and the file |
| `…/key.rs` | Key names (`ns.name`, `[a-z0-9_]`, ≤ 32 B), typed `Key<T>` (checked at compile time; invalid names don't compile), the sealed `Setting` trait for `bool`/`i32`/`String`/`Bytes` |
| `…/registry.rs` | **The registry:** one `registry!` row per system setting (type, default, limit, owner). It generates `keys::*` and `REGISTRY` and checks at compile time that each default has the key's type |
| `…/store.rs` | `Store`: get (stored, else the default), set with validation; a value equal to its default is removed; a change journal (64 entries) for notifications |
| `…/file.rs` | File format v1: `NSET`, version, count, then records (key length, key, value length, value). Decode keeps every valid record and skips damaged or retyped ones; `migrate()` is the hook for later versions |
| `…/access.rs` | `Caller::{Shell, App(key)}`: the shell writes everything; an app writes registered keys it owns and unregistered keys in its own namespace. Step 0 extends it here |
| `…/service.rs` | `Service<B: Backend>`: store + backend + a 1 s save delay (each change restarts it; a failed save retries a delay later) + `flush()` + watches per session (≤ 8 prefixes) |
| `neoui/symbian/src/settings.rs` | `FileBackend`: `C:\private\e0002001\settings.dat`, atomic replace (write `settings.new`, delete, rename; load falls back to `.new`). `UiMirror` keeps the shell's view in step |
| `neoui/ui/system-settings.slint`, `neoui-render/src/settings.rs` | The `SystemSettings` Slint global (the shade and Settings bind to it two-way) and the binding table to registry keys |
| `neoui/symbian/neoapp` | `App::setting(key)`, `set_setting`, `setting_raw`/`set_setting_raw`, `watch_settings(prefix)` |

### Protocol (`NeoUi` 1.1, additive)
| Opcode | Arguments | Result |
|---|---|---|
| `SETTING_GET = 8` | `[Des8 key, Des8 out value]` | the value's length; `KErrNotFound`, `KErrArgument`, `KErrOverflow` (short buffer) |
| `SETTING_SET = 9` | `[Des8 key, Des8 value]` | 0; `KErrPermissionDenied`, `KErrArgument`, `KErrTooBig` |
| `SETTING_WATCH = 10` | `[Des8 prefix]` (empty = every key) | 0; `KErrArgument`, `KErrOverflow` (more than 8) |

`AppEvent::Settings { seq }` (kind 7) is sent at most once per frame to a session whose prefix matches a changed
key. The app reads its keys again.

### Registered keys
| Key | Type | Default | Shown in |
|---|---|---|---|
| `radio.wifi`, `radio.bt`, `radio.data`, `radio.airplane` | Bool | true, false, true, false | Shade toggles, Settings → Connectivity (UI only until there are drivers) |
| `sound.silent`, `sound.vibrate` | Bool | false, true | Shade (Silent) |
| `display.dark` | Bool | true | Settings → Display (stored; there is no light palette yet) |
| `display.brightness` | Int 0–255 | 160 | Shade slider, Settings → Display; sent to the panel (display HAL, scaled to 0–1023) |
| `display.timeout` | Int 0–600 (s) | 60 | Settings → Display → Screen timeout (15 s … 10 min, Never = 0); off after that long without a touch or key |
| `clock.24h` | Bool | true | Settings → Display; the status bar clock and the Clock app follow it |
| `keyboard.en`, `keyboard.hy`, `keyboard.ru` | Bool | true, true, true | Settings → Language & keyboard: the system keyboard's languages |
| `keyboard.layout` | Int 0–15 | 0 | The current language (an index into `layouts.slint`); the globe key and Settings change it |
| `keyboard.same_height` | Bool | true | Settings → Language & keyboard: every language as tall as the tallest one on |

### Adding a setting
1. Add a row to `registry!` in `registry.rs`.
2. If the shell shows it, add a property and a `changed` handler in `system-settings.slint`, and a row in
   `BINDINGS` in `neoui-render/src/settings.rs`. Tests check every binding against the registry.

An app's private settings need neither step: it writes `<its key>.*` through `App::set_setting`.

### Log lines (for CI)
- `neoui: settings loaded N keys (vV, D dropped)`, or `neoui: settings: none saved yet, using defaults`.
- `neoui: setting KEY = VALUE (by WHO)`.
- `neoui: settings saved (N bytes)` and `neoui: settings save failed (E)`.
- In the Clock app: `clock: settings changed (SEQ): 24-hour B`.

### Tests
- **Host:** 37 settings tests in `neoui-proto`: codec, names, registry, store, journal, file (truncated, corrupt,
  retyped, oversize, newer version), access, and the service (save delay, retry, flush, watches).
- **Renderer** (`neoui-render/tests/settings.rs`): the binding table against the registry; values from the store
  show in the shade; a tap on the shade's Wi-Fi tile comes back as `("radio.wifi", true)`.
- **Still to do:** a boot check in `symbian/taps.sh` (QEMU virt, US6b): toggle Wi-Fi, reboot, the tile stays off; 24-hour off,
  the Clock app shows 12-hour time.

### Deferred to later parts
- `notify.<app>.*` and Settings → Notifications: Part 2.
- Capability-checked writes to global keys by ROM EXEs: step 0.

## Apps rebuilt on Part 1 (2026-11-09/10)

Two apps were rebuilt before Part 2 (neoui `main`, 2026-11-10). Each follows one pattern: pure models in
`neoui-proto` (host-tested), one `State` global in Slint, and one module per page in Rust and in Slint
(`src/pages/*.rs` with `bind` and `show`, `ui/pages/*.slint`).

### Clock (`NEOCLOCK.EXE`, neoui `872e6dc`)
- **Pages:** Clock (face, Set time), Alarms (editor: days, label, snooze), World (a catalogue of 21 cities with fixed
  offsets; shortcut: no DST), Timer, Stopwatch.
- **Kept state:** every page's state is kept in settings rows owned by `App("clock")`: `clock.tab`, `clock.alarms`,
  `clock.cities`, `clock.timer`, `clock.stopwatch`. The timer and stopwatch count from wall-clock UTC, so they keep
  running across app restarts and reboots.
- **Time without an RTC:** the UI server's keeper falls back to the boot clock (the kernel's UTC at boot plus elapsed
  time) when a board has no RTC, such as Syborg. It saves within 5 s of a set.
- **Alarms:** the server checks once a minute and rings even while the app is closed. It brings Clock to the front
  and sends `AppEvent::Alarm` (kind 8, `NeoUi` 1.2).
- **Home widget:** the `ClockWidget` on home is the first widget of Part 4. It is live, fed through the `Now` global,
  and opens Clock on a tap.
- **Open:** a two-boot check of every page's saved state (on the phone, or QEMU virt from US6b).

### Dev tools (`NEODEV.EXE`, neoui `ed9202f`)
- **Tabs:** Home · Devices · Console · Procs · More. More opens Settings, Tools and About. Sub-views replace the
  tabs rather than covering them, because a cover lets taps through to the page underneath. Back closes a sub-view.
- **Home:** cards for uptime, memory and CPU (both with 30-second bar graphs), storage, processes and threads, a
  device summary, the modem, and the kernel and slot. Below them, a list of every page.
- **Devices:** every component a phone has (`neoui-proto::devtools::device::CATALOGUE`, in sections). Each state
  comes from the best of three sources:
  1. the kernel's device registry: HAL `ENeoHalDeviceList` 0x4e19, with one `A64_DEVICE` per driver in the arm64
     baseport (kernel branch `device-registry`, `090bb5e`);
  2. the app's probes: memory, display, drives, RTC, NeoModem `STATUS`, ModemState, AdspState, slots;
  3. the log's tags.

  Without a registry (the 2010 kernel on Syborg), parts that some board's driver reports show "Unknown" rather than
  "No driver". "Run checks" runs every check without side effects; the only write is a 4 KB file on C:.
- **A device's view:** the driver, source, state, live values, its check, its log lines, and its tests:
  - Touch: a grid that lights each cell a finger crosses;
  - Display: R/G/B/white/black/grey fills, and the kernel console on or off;
  - Storage: a 1 MB speed test on C:;
  - Audio and ADSP: the mic looped back to the loudspeaker or the earpiece (NeoModem `AUDIO_TEST`);
  - Modem: refresh the status.
- **Console:** the live log, or the last boot's. Only the rows that fit go to Slint. Drag scrolls by whole rows; there
  are Follow, tag chips (All plus the 8 commonest tags), Clear and Save.
- **Procs:** processes (exec `ObjectNext`, `FindHandleOpen`, `ProcessGetMemoryInfo`), sorted by CPU time, then
  memory. A process's view lists its threads with their priority and CPU time. CPU time needs a kernel built with
  `MONITOR_THREAD_CPU_TIME`; the arm64 kernel is not, so it shows "-".
- **More:**
  - Settings: every registered key with its value, owner, type, limit and default; read-only, and live.
  - Tools: save both logs to `E:\logs` (or `C:\logs` without E:), the kernel console overlay, and power, each power
    action behind an inline confirm.
  - About: the builds, slots, display, CPUs, RAM and uptime.
- **Code:** `neoui-proto::devtools` (device, log, stats), `neoapp::hal` (the variant HAL calls, typed), `neoapp::sys`
  (memory, CPUs, processes and threads; shortcut: raw exec calls until e32 wraps them), and
  `symbian/apps/devtools/src/{state,probe,pages/*}.rs`.
- **Log lines (for CI):**
  - `devtools: devices N (kernel K, probe P, log L); procs N threads M; …`;
  - `devtools: kernel registry Listed { devices, bad } | Missing(e)`;
  - `devtools: tab N`, `devtools: view X`;
  - `devtools: check <key> pass|fail|skip <why>`, `devtools: checks P pass, F fail, S skipped`;
  - `devtools: touch test cell c,r (n of 72)`;
  - `devtools: saved …`.
- **Verified:**
  - Syborg on the Mac: every tab and sub-view, Run checks (3 pass, 20 skipped), the colour and touch tests, Back.
  - QEMU arm64 with the registry kernel: `drivers` lists display ok, kbd ok and blk absent (no disk), and Dev tools
    reports `devices 23 (kernel 3, probe 3, log 0)`.
  - Not yet on the phone.
- **Open:**
  - the modem (`qcom_mss`) and USB (`qcom_dwc3_acm`) registry entries, which wait for the kernel stream's edits to
    those files;
  - per-thread CPU time;
  - the battery and other parts with no driver at all.

