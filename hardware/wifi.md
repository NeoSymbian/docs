<!-- SPDX-License-Identifier: Apache-2.0 -->
# Wi-Fi on the Pixel 3a XL

Part of [Hardware](README.md) · Status: done · Updated: 2026-11-21 · Neighbours: [modem](modem.md), [audio](audio.md), [gnss](gnss.md), [bluetooth](bluetooth.md), [battery](battery.md)

Written 2026-11-12. This is the Wi-Fi part of the hardware hub's [D6](README.md#milestones-and-gates) (roadmap P4): from
a silent WCN3990 to a WPA2 network with IP traffic, then a Settings page. W0–W7 are done; the bring-up log is in
[history/wifi-bringup.md](history/wifi-bringup.md), and each stage below keeps a short summary.

**Who does what now (neohw S5, 2026-11-18).** MODEMD ran the firmware start and SYSSTART the supplicant until S5.
- **`WIFID.EXE`** (neohw `symbian/wifid`, 0xE0004002) owns the user side:
  - WLFW over NeoHub (crates `wlfw`, `wifi`);
  - the MSA and the board data;
  - scans, joins and the WPA2 supplicant (crate `wpa`);
  - the remembered networks (`C:\private\e0004002\wifi.dat`).
- **`NEONET.EXE`** is the IP stack, and WIFID starts it.
- **neoui's SYSSTART** starts WIFID and is a NeoWifi client.
- **The kernel side** is `qcom_wcn3990.cpp`. The [audit](#audit-2026-11-18) lists what is built.

## Decision (owner, 2026-11-12)

The owner chose Symbian's 2010 WLAN stack (UMAC, wlanengine, ESOCK) over a WHA chip driver ported from ath10k. W4 then
took a direct WMI path in the kernel driver and W5 a smoltcp stack (NEONET), so nothing builds from the WLAN forks;
UMAC/WHA stays the long-term option. The decision also put C10 on ESOCK/TCPIP6 ([modem.md](modem.md#c10-mobile-data)).
Log: [history/wifi-bringup.md](history/wifi-bringup.md#decision-owner-2026-11-12).

## What comes from Linux, and how

Only ath10k is ported. It is ISC-licensed (checked 2026-11-12: `snoc.c`, `ce.c`, `qmi_wlfw_v01.c`, `wmi-tlv.h`).
Ported files keep the ISC copyright and permission notice, with a NeoSymbian line added.

| Linux file (ISC) | Becomes |
|---|---|
| `qmi_wlfw_v01.c`, `qmi.c` | `neohw/crates/wlfw` (was `modem-proto/src/wlfw.rs`): the messages and the start-up order |
| `snoc.c` | the PDD's register, interrupt and pipe setup; the CE pipe and service tables sent in WLAN cfg |
| `ce.c` | the PDD's copy-engine rings |
| `htc.c`, `wmi-tlv.*`, `wmi.h`, `htt*` | the PDD's HTC, WMI and HTT messages |

GPL-licensed code is read for facts only, never copied: `mac80211`/`cfg80211`, `qmi_interface.c`, the Linux IP stack.

## Hardware facts

| Fact | Value | Source |
|---|---|---|
| Wi-Fi block | `qcom,wcn3990-wifi` at `0x18800000`, size `0x800000` | DTB |
| Interrupts | 12 SPIs, `0x19e`–`0x1a9` (one per copy engine) | DTB |
| SMMU stream | `0x40`, mask `0x1` (`iommus = <&apps_smmu 0x40 0x1>`; mainline sdm845 uses the same) | DTB |
| Supplies | PM660 (RPMh `a`) LDO5 0.8 V (cx-mx), LDO9 1.8 V (xo), LDO6 1.3 V (rfa), LDO19 3.3 V (ch0) | DTB |
| Clock | `cxo_ref_clk_pin` = RPMh clock 8 (RF_CLK2) | DTB, Linux `clk-rpmh` |
| Quirk | `qcom,snoc-host-cap-8bit-quirk` (the host-cap message uses 8-bit fields) | DTB, ath10k |
| MSA memory | carve-out `wlan-msa` at `0x94d00000` | [modem.md](modem.md) |
| Firmware | the WLAN protection domain `msm/modem/wlan_pd` runs inside the modem; its image is `wlanmdsp.mbn` (in pmOS's `qcom/sdm670/sargo/`) | C1 image listing |
| Board data | `bdwlan.bin` (vendor) or linux-firmware `ath10k/WCN3990/hw1.0/board-2.bin`; read at runtime, never stored | ath10k |
| MAC address | none stored (ztOS FIXES #10): derive a stable one | ztOS |

## Stages

<!-- stages -->
| Stage | What | State | Updated | Next / evidence |
|---|---|---|---|---|
| W0 | The firmware's WLFW service appears | done | 2026-11-12 | cause: the locator's message id (0x21) |
| W1 | Firmware control (WLFW) | done | 2026-11-12 | firmware-ready indication on the phone |
| W2 | Copy engines, HTC, WMI | done | 2026-11-12 | WMI READY on the phone |
| W3 | Scan | done | 2026-11-12 | direct WMI path, not UMAC/WHA; networks on both bands |
| W4 | Join a WPA2-PSK network | done | 2026-11-12 | connected from Settings by touch |
| W5 | An IP address (smoltcp, NEONET) | done | 2026-11-12 | DHCP, ping, internet check over NeoNet |
| W5a | ESOCK over NeoNet | done | 2026-11-13 | NEOSOCK passed on Syborg and on the phone; no CI run on virt |
| W6 | Wi-Fi in Settings | done | 2026-11-12 | W3c and W4: list, password, connect, details |
| W7 | Interrupts, handshake guard, modem restart | done | 2026-11-21 | interrupts 2026-11-13; re-init after a restart proven (kernel#38, neohw#14) |
<!-- /stages -->

The first plan (work, exits and size guesses per stage) and its design gates are in the
[log](history/wifi-bringup.md#stages-the-plan-of-2026-11-12). What is built and what is still open: the
[audit](#audit-2026-11-18).

## Where the code goes

As built (the plan had UMAC in ekern; W4's direct path dropped it):
- **kernel:** the driver `baseport/arm64/sdm670_assp/qcom_wcn3990.cpp`, plus the `variant.conf` `ekc` lines.
- **neohw:**
  - the crates `wlfw`, `wifi` (+ `wifi::ipc`, NeoWifi), `wpa` and `net` (NeoNet);
  - `symbian/wifid` and `symbian/neonet`.
- **build:**
  - ESOCK and the comms components in `emitter/comms_components.py` (commsfw and networkingsrv pinned in `sources.lock`);
  - `apps/esock` (NEOTIER, NEONET.PRT, NEOCDB, NEOSOCK);
  - `apps/neonet` (NEONET.DLL, NEONETT).
- **No wlan/accesssec forks:** nothing builds from `oss.FCL.sf.os.wlan` or `oss.FCL.sf.mw.accesssec` since W4. They come
  back only with the UMAC/WHA option.
- **neoui:** the Settings page (W6).

## Interfaces

- **Kernel HALs** (`EHalGroupVariant`): FwRead `0x4e1b`, WlanMsa `0x4e1c`, WlanStart `0x4e1d`, WlanScan `0x4e1e`,
  WlanLink `0x4e1f` (ops 1–11; op 8 takes the next received Ethernet frame, op 9 queues one, op 10 completes a
  `TRequestStatus` on a frame or a link change, op 11 cancels it), Prng `0x4e23` (the SoC PRNG).
- **NeoWifi** (`wifi::ipc`): WIFID's server; SYSSTART and the Settings app are its clients.
- **NeoNet** (`net::proto`): NEONET's server, for apps (in Rust `net::client`, in C++ NEONET.DLL).

**The NeoNet API 1.0:**

| Function | Arguments | Completes with |
|---|---|---|
| STATUS 1 | out des | `{1, state, prefix, 0, ip, gateway, dns1, dns2}` |
| RESOLVE 2 | name, out des (4) | 0 + the IPv4 address (waits for DNS) |
| CONNECT 3 | IPv4 (big-endian u32), port | the socket id once established |
| SEND 4 | id, data (<= 8 KB) | bytes taken (waits while the buffer is full) |
| RECV 5 | id, out des | bytes read, 0 = closed (waits for data) |
| CLOSE 6 | id | 0 |

- A socket belongs to the session that opened it.
- A session that closes cancels its waiting requests (`KErrCancel`) and closes its sockets.
- In Rust: `net::client::{Net, TcpStream}`.

**NeoNet API 1.1 (UDP and listening sockets).** NEONET and the `net` crate share one socket id space, 24 sockets
in all.

| Op | Arguments | Completes with |
|---|---|---|
| 7 `UDP_OPEN` | a port (0: any) | the id |
| 8 `SEND_TO` | id, data, a 6-byte endpoint `{ip, port big-endian}` | the length |
| 9 `RECV_FROM` | id, out data, out endpoint | the length (`KErrOverflow`: the datagram didn't fit and is gone) |
| 10 `LISTEN` | a port | the id |
| 11 `ACCEPT` | the listener's id, out endpoint | the connection's id |

- Host tests run UDP and listen/accept over smoltcp's loopback device.
- Shortcut: one waiting connection per listener (smoltcp has no backlog).

**NEONET.DLL (C++)** (`build/apps/neonet/`): `RNeoNet` on `RSessionBase`. Each method is one NeoNet op, and the
waiting ones complete a `TRequestStatus`. Its 12 exports are frozen in `eabi/neonetu.def`. `NEONETT.EXE` is the
phone test: it waits for an address, resolves a name, fetches `generate_204` over TCP, and sends a DNS query to the
gateway over UDP. It prints `neonett: PASS`.

## W0: the firmware service

Done 2026-11-12: the modem's WLFW service (QMI 69) never appeared because our locator answered GET_DOMAIN_LIST with the
wrong message id (0x20, not 0x21). With that fixed, the modem fetches `wlanmdsp.mbn` over TFTP from `vendor_a`.
Log: [history/wifi-bringup.md](history/wifi-bringup.md#w0-the-firmware-service).

## W1: firmware control (done 2026-11-12, phone RAM boot)

WLFW in ath10k's order (host capability, MSA, board data `bdwlan-bonito.bin`, calibration) up to the firmware-ready
indication; HALs FwRead `0x4e1b` and WlanMsa `0x4e1c`. Picking the regional board data is an owner question before any
release. Log: [history/wifi-bringup.md](history/wifi-bringup.md#w1-firmware-control-done-2026-11-12-phone-ram-boot).

## W3 design gate: WHA → WMI mapping (written 2026-11-12)

The WHA → WMI mapping, call by call, for the UMAC/WHA option. Not built: W4 took the direct path. The table is kept as
reference in the log. Log: [history/wifi-bringup.md](history/wifi-bringup.md#w3-design-gate-wha--wmi-mapping-written-2026-11-12).

## W2: copy engines, HTC, WMI (done 2026-11-12, phone RAM boot)

`qcom_wcn3990.cpp` brings up the copy engines, HTC and WMI up to WMI READY. The DMA pool is device memory: aligned
32-bit accesses only. Log: [history/wifi-bringup.md](history/wifi-bringup.md#w2-copy-engines-htc-wmi-done-2026-11-12-phone-ram-boot).

## W3a: first scan (in progress, 2026-11-12)

2026-11-12: the firmware accepted the scan commands, but no beacon reached the host until W3b set up the HTT rx ring.
Log: [history/wifi-bringup.md](history/wifi-bringup.md#w3a-first-scan-in-progress-2026-11-12).

## W3b: the first scan works (2026-11-12, phone RAM boot)

With the HTT rx ring configured, passive and active scans list the networks on both bands.
Log: [history/wifi-bringup.md](history/wifi-bringup.md#w3b-the-first-scan-works-2026-11-12-phone-ram-boot).

## W3c: Wi-Fi in Settings (2026-11-12, phone RAM boot)

The driver stays up as a service; HAL WlanScan `0x4e1e` returns the list; the station MAC is `02:4e` + the SoC serial.
Settings → Wi-Fi lists the networks and takes a password (Settings is now its own app, a NeoWifi client:
[settings.md](../neoui-shell/settings.md#the-settings-app-neoset)). Log: [history/wifi-bringup.md](history/wifi-bringup.md#w3c-wi-fi-in-settings-2026-11-12-phone-ram-boot).

## W4: joining a WPA2-PSK network (connected 2026-11-12)

The kernel joins over WMI (authentication, association, keys; EAPOL over HTT) and a user-side WPA2-PSK supplicant
(crate `wpa`) runs the 4-way handshake; a remembered network keeps the SSID and the PMK, never the password. The
shortcuts still open (legacy rates, no PMF) are in the [audit](#audit-2026-11-18). Log: [history/wifi-bringup.md](history/wifi-bringup.md#w4-joining-a-wpa2-psk-network-connected-2026-11-12).

## W5: an IP address (smoltcp, 2026-11-12)

NEONET.EXE (smoltcp) gets an address by DHCP and reaches the internet over the kernel's Ethernet frame queues
(WlanLink ops 8 and 9); apps use the NeoNet API ([interfaces](#interfaces)). IPv4 only. Log: [history/wifi-bringup.md](history/wifi-bringup.md#w5-an-ip-address-smoltcp-2026-11-12).

## After W5: background rejoin, handshake timeout (2026-11-13)

Background rejoin with Settings closed; the supplicant gives up after 10 s in the handshake, because an AP that
resent message 1 for a minute made the firmware assert and take the modem down. Log: [history/wifi-bringup.md](history/wifi-bringup.md#after-w5-background-rejoin-handshake-timeout-2026-11-13).

## W7: interrupts, the handshake guard, a modem restart (design, 2026-11-13)

Done on the phone 2026-11-13 (kernel `6bac85c6`): copy-engine interrupts instead of polling, WlanLink op 10 (notify,
so NEONET no longer polls), a 15 s handshake guard, NeoNet 1.1 (UDP, listening sockets) and NEONET.DLL for C++. The
re-init after a modem restart was proven on 2026-11-21
([modem.md](modem.md#modem-restart-and-the-adsp-fixed-2026-11-21-kernel38-neohw14)). Log: [history/wifi-bringup.md](history/wifi-bringup.md#w7-interrupts-the-handshake-guard-a-modem-restart-design-2026-11-13).

## W5a: ESOCK over NeoNet (2026-11-13)

**Goal:** 2010 programs work unchanged through the real socket API: `RSocketServ`, `RSocket` (TCP and UDP),
`RHostResolver` and `RConnection`.

**One IP stack: NEONET.** There is no TCPIP6 and no NIF; a second stack on the same MAC would fight smoltcp for DHCP
and the frames.

**The gate (read in the 2010 sources):**
- **Every implicit socket or resolver needs a connection stack, but never a started one.** `RSocket::Open` without
  an `RConnection` asks the tier manager plane for an implicit flow (`ss_roles.cpp`). That looks up the CommsDat tier
  tagged with the address family (KAfInet = 2048), selects its MCPR, and creates the CPR, the SCPR and the flow. With
  the transport flow shim (`0x101F7482`) as the flow, the shim loads our protocol module. No step starts a bearer
  unless the protocol asks for one (`NoBearer`).
- **`RConnection::Start` on a bottom-layer vanilla stack** runs start → no bearer → MCPR finds no next layer → start
  self → started. No agent, IAP or NIF is involved. commsfw's own test configuration runs exactly this
  ("DummyVanillaWithNoNextLayer").

**The pieces:**

| Piece | What |
|---|---|
| ESOCK and the comms framework, from the 2010 sources | About 50 binaries in `build/emitter/comms_components.py`, all built by our MMP builder: c32start, c32exe and the root server, the commselements, commsbufs, esock/esocksvr with their params and messages, the core, mobility and UPS providers, CommsDat with the commdb shim, insock, and edbms/dial/upsclient/logwrap. mbufmgrimpl needs two include shims (its headers' names clash with commsbufs/version1's under casefix), and edbms needs `foff_dynamic` |
| `.cmi`/`.ini` (stock) | c32start's `esock.cmi` (the dealer), `esock_tr`, `esock_mip` (ESock_IP: TM/MCPR/CPR/SCPR), `esock_dip` (ESock_DIP: data, `IP.*.ESK`), `c32start.ini` |
| `NEOTIER.DLL` (`build/apps/esock/neotier`) | ECom: a tier manager whose selector always picks the tier's default access point, whatever the preferences (an IAP, a SNAP, none), and the core MCPR. CommsDat holds these UIDs as signed fields, so they are `0x0E004005`/`0x0E004006`. **Since browser WB2d (build#37), a link layer under it:** the link tier's manager (`0x0E00400B`) and `CNeoLinkFlow` (`0x0E00400C`), which binds under the transport shim and answers `KSoConnectionInfo`, so sockets opened on an `RConnection` (P.I.P.S. opens all of them so) get a bearer |
| `NEONET.PRT` (`build/apps/esock/neonetprt`) | The KAfInet protocol module: TCP (connect, listen/accept, stream data) and UDP (bind, send-to, receive-from, "connected" datagrams), and the host resolver, all over `NEONET.DLL`. It runs in ESock_DIP and never blocks: each waiting NeoNet call is an active object. Cancelling closes the NeoNet socket (or, for a connect, the session), and NEONET then answers the waiting call with KErrCancel |
| `ip.neonet.esk` | `protocols= tcp,udp` from `neonet.prt` |
| CommsDat | The ROM repository is the 2010 empty one (`defaultcommdb/src/empty.txt`, policies only). `NEOCDB.EXE` writes our records at boot through the CommsDat API, so they always match this schema: the MCPR, the vanilla CPR/SCPR, the flow shim, access point 10000 "NeoNet", tier 2048 (ESock_IP, neotier's tier manager), and GlobalSettings' default tier; since WB2d also the link tier `0x0E00400D` and access point 10001 "NeoNetLink" under 10000 (a database from before gains them at boot; older images then need `C:\private\10202be9\persists\cccccc00.cre` deleted). It does this once; NEONET starts it |
| `NEOSOCK.EXE` | The test, through the 2010 API: the protocol list, `RConnection` Start/Stop, resolving `localhost`, TCP listen/accept/connect and both directions, and a UDP datagram, all on 127.0.0.1. With `net`, it also fetches `generate_204` |

**NEONET on a board without Wi-Fi** (QEMU `virt`; Syborg until 2026-11-21): the HAL has no WlanLink, so NEONET runs a
loopback interface at 127.0.0.1/8 (a static address, no DHCP; `localhost` resolves). This makes the whole path
testable on QEMU.

The 2026-11-13 result (NEOSOCK passed on Syborg's loopback and over Wi-Fi on the phone) and why the 2009 Linux `ced`
was not used: [log](history/wifi-bringup.md#w5a-esock-over-neonet-2026-11-13).

**Shortcuts:**
- socket options are accepted and ignored;
- one waiting connection per listener;
- no reverse lookups;
- the UPS prompt stubs (upsclient) are never reached, because the vanilla access point carries no UPS extension;
- no IAP records yet, so apps that list IAPs see none.

## Audit 2026-11-18

This section checks the code against the doc (kernel `dc4a7b34`, neohw `815e25b`, neoui `e06e8f4`, build `2cf5454`).

**Built as the doc describes:**
- W0–W2, W3a–c, W4, W5, W7 and W5a;
- every HAL (0x4e1b–0x4e1f, 0x4e23);
- WlanLink ops 1–11, the CE interrupts with the polled fallback, the 15 s handshake guard and the modem-restart path;
- WLFW in ath10k's order, the WPA2 supplicant, NeoNet 1.1 and ESOCK over NeoNet.

**Not built, by decision or still open:**
- the UMAC/WHA PDD (W4 took the direct path);
- HT/VHT and WMM (legacy rates only);
- PMF;
- the regional board data (`bdwlan-bonito.bin` for every country);
- IPv6;
- a check of the CCMP packet numbers on receive. ath10k leaves replay detection to the host; we do none yet, so the
  install-key RSC is 0, as ath10k's.
- a phone test of the re-init after a modem restart (**done since 2026-11-21**: Wi-Fi reconnects about 25 s after a forced
  modem fault, [modem.md](modem.md#modem-restart-and-the-adsp-fixed-2026-11-21-kernel38-neohw14));
- a CI run of NEOSOCK (it was a manual Syborg run; Syborg is retired since 2026-11-21, and no `virt` CI job runs it).

**Fixed in this audit:**

| Bug | Fix | Where |
|---|---|---|
| **The "reason 4" drops after 2–5 minutes** ([known-issues](../known-issues.md)). Not the AP: after ~150 receive records the firmware stopped receiving for good, then reported a beacon miss, logged as reason 4 | **1024 HTT receive buffers instead of 128** (ath10k keeps 2047). The beacon miss also probes the AP first, and its log line carries the receive counters | kernel `wifi/bmiss` |
| A handshake with no EAPOL at all (a dead data path) was retried until the firmware asserted and crashed the modem | `fail::NO_DATA`: no automatic rejoins until the modem restarts or the user connects | WIFID |
| A restarted modem looked running at once: its SMP2P item still held the old READY\|HANDOVER\|FATAL | SMP2P reports a stopped remote's old bits as 0 until its next boot writes them; MSS boot fails on FATAL | kernel `mss/fatal-stale` |
| A PTK rekey (a second 4-way on the same association) installed nothing, so data stopped after an AP's rekey | Its msg3 installs the new PTK. A resent msg3, or a group message 1 carrying the key already installed, still installs nothing (KRACK). Host tests for both | neohw `wpa` |
| The Wi-Fi switch off only stopped rejoining; the link and IP stayed up | Off leaves the network (the radio itself stays powered) | WIFID |
| Disconnect was forgotten on a reboot | The left SSID is kept in `C:\private\e0004002\left.dat` | WIFID |
| A join the kernel kept in Joining could block WIFID's leave and its reset answer | The supplicant gives up after 30 s | WIFID |
| WIFID asked for a 128 KB stack, over the 2010 kernel's 80 KB on Syborg, so neither WIFID nor NEONET could start there | `stack=0x10000` | neohw `exes.txt` |
| After a modem stop, link requests waited 3 s for a driver thread that had let go | They fail at once (`KErrNotReady`) | kernel |
| NEONET.DLL had WIFID's UID3 0xE0004002 | 0xE000400A | build |
| The device registry showed READY's zero MAC | It shows the station MAC | kernel |

