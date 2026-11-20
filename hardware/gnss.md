<!-- SPDX-License-Identifier: Apache-2.0 -->
# GNSS: GNSSD.EXE, QMI LOC on the modem, XTRA over Wi-Fi

Part of [hardware.md](../hardware.md), the hardware and drivers hub (status of every driver, the neohw processes). Neighbours: [modem](modem.md), [audio](audio.md), [wifi](wifi.md), [bluetooth](bluetooth.md), [battery](battery.md).

Started 2026-11-20. D6's GNSS part ([hardware.md](../hardware.md#milestones-and-gates)): the gate is an outdoor
standalone fix. Decisions (owner, 2026-11-20): a **separate GNSSD.EXE**, not a module in MODEMD; **XTRA over Wi-Fi**
in the first version.

## What we know

- **The modem serves LOC.** Our own HWHUB logs show `qrtr: server 16 v2 i0 at 0:7x` on every boot since C7. The
  port moves (71–75 seen), so the client always uses the lookup. QMI-SLIM (55) is announced too (not used).
- **It answers.** In the C1 Linux reference run (`private/c1/`), LOC answered Set Engine Lock, Get Server (a SUPL
  server is already set in the modem's EFS), Get Predicted Orbits Data Source (three XTRA URLs on
  `xtrapath{1,2,3}.izatcloud.net`) and Register Events. Nobody tried a fix.
- **No new kernel or locator work.** GNSS runs in the modem's root PD (the firmware has no `gps_pd`), so HWHUB's
  locator is unchanged. Its NV items live in the modem EFS that rmtfs already serves. EFS writes stay in RAM until
  [modem.md](modem.md) G4, so every boot is a cold start.
- **Not known:** the RF path. The DTB has no GNSS LNA or antenna nodes; the first fix is the only test.

## Design

```
 neoui Dev tools ("Location (GNSS)")
   | NeoLocation
 GNSSD.EXE --- XTRA download (HTTP) ---> NEONET.EXE (Wi-Fi)
   | NeoHub (BIND LOC, client port 0x28)
 HWHUB --- QRTR ---> modem: LOC (service 16, v2)
```

**GNSSD.EXE** (UID 0xE0003004) is a NeoHub client of LOC and serves NeoLocation. MODEMD starts it once its own
NeoHub session is up, the way it starts AUDIOD. HWHUB's port allow-list (0x20–0x27, all used) gains 0x28.

**Host crate `neohw/crates/loc`** (Apache, `no_std` + alloc), the same shape as `wlfw` + `wifi`:
- `proto`: the LOC messages, with `qrtr::qmi`'s builder and parser.
- `Engine`, sans-I/O:
  - LOC up: Register Events (position report, satellite info, inject time request, predicted orbits request,
    engine state). Get Engine Lock; if mobile-initiated fixes are locked (MI or ALL), set NONE and log it.
    Set Operation Mode standalone. Get Predicted Orbits Data Source (URLs, max file and part sizes).
  - START (the first client): Get Predicted Orbits Data Validity; XTRA stale or missing → ask the EXE for it.
    Start session 1: periodic, intermediate reports on, 1 s.
  - Inject Time Request → Inject UTC Time from our clock, uncertainty 5 s, only once the clock was set (NITZ or
    the HTTP `Date:`).
  - XTRA data → Inject Predicted Orbits Data (0x35, format XTRA) in parts of at most the modem's part size
    (≤ 1024 bytes), the next part after each acknowledgement.
  - Position reports → the last fix and the time to first fix. Stop after 15 min without a fix, and when the last
    client stops. A modem reset clears everything until LOC is up again.
- `http`: the response parser for one plain-HTTP GET: status 200, `Content-Length`, at most 512 KB. Only URLs
  from the modem's own list whose host ends in `.izatcloud.net` are fetched. The modem checks the file itself.
- `ipc`: the NeoLocation contract (`NAME = "NeoLocation"`, version 1.0.0): STATUS fills a fixed record (state:
  off, searching, fix, failed, locked; latitude and longitude ×10⁷; horizontal accuracy and altitude in dm;
  satellites used and seen; UTC ms; time to first fix; XTRA age), START and STOP are counted per session and
  released when a session closes.

**The EXE (`neohw/symbian/gnssd`):** the NeoHub client moves from WIFID into `symbian/sys` (WIFID's copy was
marked to be shared at the third client), a server and hub loop like WIFID's, and the XTRA download on a worker
thread through `net::client` (its calls block). The file is cached in GNSSD's private folder with its download
time and fetched again only when older than 24 h or when the modem calls it invalid. Without Wi-Fi, GNSS runs
standalone with no XTRA.

**First consumer:** neoui Dev tools' `gnss` row (Connectivity), today "No driver": live facts from STATUS and the
actions "Start a fix" and "Stop".

## Message facts

libqmi `data/qmi-service-loc.json`, `qmi-enums-loc.h`, `qmi-flags64-loc.h`. Requests are answered twice: a
response with the QMI result, then (for most) an indication with the same id carrying the real answer (TLV 0x01
status, 0 = success).

| Id | Name | TLVs used |
|---|---|---|
| 0x21 | Register Events | 0x01 mask u64: bit 0 position, 1 satellites, 4 time request, 5 orbits request, 7 engine state |
| 0x22 / 0x23 | Start / Stop | 0x01 session u8; 0x10 recurrence u32 (1 periodic); 0x12 intermediate u32 (1 on); 0x13 interval ms |
| 0x24 ind | Position Report | 0x01 status u32 (0 ok, 1 in progress, 3 timeout, 6 locked); 0x10/0x11 lat/lon f64; 0x12 h-unc f32 m; 0x1B alt MSL f32; 0x25 UTC ms u64; 0x2C satellites used |
| 0x25 ind | GNSS SV Info | 0x10 list (count = satellites seen) |
| 0x28 ind → 0x38 | Inject Time Request → Inject UTC Time | 0x01 UTC ms u64, 0x02 uncertainty ms u32 |
| 0x29 ind | Predicted Orbits Request | 0x01 max file / part size |
| 0x35 | Inject Predicted Orbits Data | 0x01 total size u32, 0x02 parts u16, 0x03 part u16, 0x04 data (u16 length, ≤ 1024), 0x10 format 0 (XTRA) |
| 0x36 / 0x37 | Get Orbits Source / Validity | ind 0x10 sizes, 0x11 URLs / ind 0x10 start UTC u64 + hours u16 |
| 0x3A / 0x3B | Set / Get Engine Lock | 0x01 (ind 0x10) u32: 1 none, 2 MI, 3 MT, 4 all |
| 0x4A | Set Operation Mode | 0x01 u32: 4 standalone |

## Stages

| Stage | Work | Gate | Status |
|---|---|---|---|
| GN0 | This design | the owner reads it | 2026-11-20 |
| GN1 | `crates/loc`; hub port 0x28 | host tests: replies built with the QMI builder, a hand-built position report, XTRA parts, the 15-min bound, reset | |
| GN2 | GNSSD.EXE, the shared NeoHub client in `sys`, `exes.txt`, MODEMD starts it | phone RAM boot: bind, Register / Lock / Mode answered; WIFID still joins | |
| GN3 | XTRA download, cache, inject | phone: validity after the inject; the cache reused after a reboot | |
| GN4 | Dev tools row and actions | Syborg ("no modem") and the phone | |
| GN5 | Outdoor fix | horizontal accuracy < 50 m; time to first fix with and without XTRA | |

## Not in scope

SUPL and MS-based modes, Settings → Location and a status-bar icon, the browser's Geolocation, a legacy
`RPositionServer` adapter (D8), GNSS as a time source, NMEA, persistent EFS writes (G4).
