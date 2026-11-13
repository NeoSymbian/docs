<!-- SPDX-License-Identifier: Apache-2.0 -->
# Wi-Fi on the Pixel 3a XL

Written 2026-11-12. This is the Wi-Fi part of [driver-support.md](driver-support.md) D6 (roadmap P4): from a silent
WCN3990 to a WPA2 network with IP traffic, then a Settings page.

## Decision (owner, 2026-11-12)

Use **Symbian's 2010 WLAN stack on top** and **a chip driver ported from Linux ath10k beneath it**.

- **Reused, unchanged where possible (EPL):**
  - `oss.FCL.sf.os.wlan`:
    - `wlanldd`, the kernel-side LDD with Nokia's 802.11 layer (UMAC: scan, join, power save);
    - `wlanengine`, connections, WPA/RSN information elements, roaming;
    - `wlannwif`, the ESOCK network interface.
  - `oss.FCL.sf.mw.accesssec`: `eapol`, WPA/WPA2 key handshake and EAP.
  - `oss.FCL.sf.os.commsfw` + `oss.FCL.sf.os.networkingsrv`: ESOCK, TCPIP6, DHCP, DNS.
- **New:**
  - a WHA chip driver (PDD) for the WCN3990, in kernel C++;
  - the firmware control (QMI WLFW) in MODEMD, in Rust.
- **It also decides C10:** mobile data uses ESOCK/TCPIP6 too ([telephony.md](telephony.md) C10 asked the owner).

The seam is `wlan_plat/wlan_hal_api/inc/wlanpddiface.h`: the PDD's `MWlanPddIface::Extract()` returns a `WHA::Wha`
(`wha.h`).
- **Control calls:** Initialize, Configure, Scan/StopScan, Join, SetBssParameters, SetPsMode, AddKey/RemoveKey,
  ReadMib/WriteMib, ConfigureQueue/ConfigureAC, Reset, Release.
- **Data:** SendPacket.
- **Callbacks** (`MWhaCb`): CommandResponse, CommandComplete, Indication, ReceivePacket, RequestForBuffer.

### What comes from Linux, and how

Only ath10k is ported. It is ISC-licensed (checked 2026-11-12: `snoc.c`, `ce.c`, `qmi_wlfw_v01.c`, `wmi-tlv.h`).
Ported files keep the ISC copyright and permission notice, with a NeoSymbian line added.

| Linux file (ISC) | Becomes |
|---|---|
| `qmi_wlfw_v01.c`, `qmi.c` | `telephony/crates/modem-proto/src/wlfw.rs`: the messages and the start-up order |
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
| MSA memory | carve-out `wlan-msa` at `0x94d00000` | [telephony.md](telephony.md) |
| Firmware | the WLAN protection domain `msm/modem/wlan_pd` runs inside the modem; its image is `wlanmdsp.mbn` (in pmOS's `qcom/sdm670/sargo/`) | C1 image listing |
| Board data | `bdwlan.bin` (vendor) or linux-firmware `ath10k/WCN3990/hw1.0/board-2.bin`; read at runtime, never stored | ath10k |
| MAC address | none stored (ztOS FIXES #10): derive a stable one | ztOS |

## Stages

Sizes are a **GUESS**.

| Stage | Work | Exit |
|---|---|---|
| **W0** (½ d) | Does the firmware's WLFW service (QMI 69) appear? | Yes, or we know what `wlan_pd` waits for |
| **W1** (1 wk) | `wlfw.rs` + MODEMD in `ath10k/qmi.c`'s order: indication register, host cap, MSA info/ready, cap, BDF download, cal report, mode ON, WLAN cfg. A HAL call tells the kernel the firmware is ready | The firmware reports ready; host tests against ath10k's message tables |
| **W2** (1–2 wk) | Kernel `sdm670_assp/qcom_wcn3990*.cpp`: CE rings, SNOC setup, interrupts, SMMU stream `0x40` mask 1 (`Smmu_IdentityMap`); HTC connect (WMI control, HTT data); WMI init/ready | Monitor `wifi` prints the firmware version and MAC |
| **W5a** (deferred: W5 went smoltcp first) | ESOCK/TCPIP6 + CommsDat (default database), the C32/ESOCK configs and ECom comms plugins, through `build/emitter/components.py`; Syborg first | A loopback TCP test EXE passes on Syborg CI |
| **W3** (1–2 wk) | The UMAC LDD built into ekern (as `locmedia` is); WHA Initialize/Configure → WMI vdev create; Scan → WMI start scan; beacons from WMI management RX → `ReceivePacket`; wlanengine + management client in the ROM | A test EXE lists nearby networks |
| **W4** (1–2 wk) | Join/SetBssParameters → vdev start, peer create/assoc, vdev up; management TX over WMI, data and EAPOL over HTT (802.11 headers rebuilt on RX); AddKey → WMI install key; accesssec EAPOL in the ROM | Joins an open network, then WPA2-PSK |
| **W5** (1–2 wk) | **smoltcp first (owner, 2026-11-12):** NEONET.EXE (neolink) with DHCP, DNS and TCP over the kernel's Ethernet frame queue, and the NeoNet socket API for apps. `wlannwif`/ESOCK stays the long-term option | Ping and an HTTP fetch over Wi-Fi, through the app API |
| **W6** (1 wk) | neoui Settings → Wi-Fi: networks, password by keyboard, connect, status icon (C++ glue like `neocli.cpp`) | On the phone, by touch |

### Design gates

Each is written here before its code.
- **W3, WHA → WMI mapping, call by call.** WHA is softmac-like: UMAC builds the 802.11 frames itself. The ath10k
  firmware keeps vdev and peer state. The PDD must read the AID and rates from the association response UMAC
  receives. This is the main technical risk.
- **W5a, the ESOCK component list.** Which ESOCK, CommsDat and ECom components, and what they cost in the ROM. This
  is the main schedule risk.

## Where the code goes

- **kernel:**
  - the PDD in `baseport/arm64/sdm670_assp/qcom_wcn3990*`, plus `variant.conf` `ekc` lines;
  - `build-ekern.sh` builds the UMAC sources from the wlan fork.
- **telephony:** `wlfw.rs` + MODEMD (it owns the modem's QRTR link).
- **build:**
  - `sources.lock` pins the new forks;
  - `components.py` gets the user-side components;
  - `fetch.sh` fetches them.
- **New NeoSymbian forks:** `oss.FCL.sf.os.wlan`, `oss.FCL.sf.mw.accesssec`. Upstream stays untouched; our work is
  on `main`.
- **neoui:** the Settings page (W6).

## W0: the firmware service

**Result 2026-11-12, from existing logs (no new boot): it never appears under NeoSymbian.**

- **Under Linux** (C1, `private/c1/captures-20261108-1846/qrtr-lookup.txt`), the modem announces
  `69 v1 i0 at 0:83 "ATH10k WLAN firmware service"`, after `51 i3 at 0:82`.
  - ath10k_snoc was loaded.
  - tqftpserv served the modem's reads from `/lib/firmware/qcom/sdm670/sargo/`, which holds `wlanmdsp.mbn`.
- **Under NeoSymbian** (MODEMD logs in `private/c7/`), neither 69 nor `51 i3` ever appears.
  - The modem asks the locator for `kernel/elf_loader` (answered: `msm/modem/wlan_pd`, instance 180).
  - After that there is no TFTP read for a WLAN file. Every read we see is refused (MODEMD's TFTP refuses every read
    and logs it).
- **ztOS on this phone** fixed "WIFI-HW missing" by running rmtfs and **tqftpserv** (ztOS FIXES #9).

**TFTP is not the difference.** C1's tqftpserv logs every read it opens ("opened for reading", checked in its
binary). Its log has none, only refusals and one write, so the Linux modem read no Wi-Fi file either.

**W0b, power (RAM boot 2026-11-12, kernel `670a24fa` + votes, user side of 2026-11-10): not enough.**
- Before the modem boots, `qcom_mss.cpp` voted PM660 LDO5 800 mV, LDO9 1800 mV, LDO6 1304 mV, LDO19 3300 mV and
  RF_CLK2 (`rfclka2` +4 = 1). All five answered `-> 0`.
- After 60 s of modem uptime the same services appear as before: no 69 and no `51 i3`.

**W0c, Linux without host drivers (2026-11-12, C1 image, cmdline patched): 69 still appears.**

| Linux run | Result |
|---|---|
| `modprobe.blacklist=ath10k_snoc,ath10k_core` | `69 v1 i0 at 0:83` and `51 i3 at 0:82` after 100 s |
| The same, then CDSP stopped and the modem restarted | 69 again |
| Cold boot with `ath10k_snoc,ath10k_core,hci_uart,btqca` blacklisted (no Wi-Fi or Bluetooth driver, so nothing powers the chip or sends the UART power pulse) | 69 again |

So **the modem starts its WLAN domain by itself.** The host's Wi-Fi and Bluetooth drivers and the CDSP play no part.
- The difference is in how we start the modem, or in what our side answers it.
- Not the difference: the RPMh supply votes (W0b), the locator table (identical to Linux's sdm670 table), TFTP
  reads (none on either side), rmtfs (the same opens and refusals as Linux's `rmtfs.log`).
- The same result on the latest image (kernel `670a24fa` + votes, build `310ae87`, neoui `e209df0`, telephony
  `37fb4c3`).

**W0 done (2026-11-12): the cause was our locator.**
- A packet trace of Linux, diffed with MODEMD's own, found it. On Linux, kprobes on `qrtr_endpoint_post` and
  `rpmsg_send` were set from tracefs while the modem restarted (`private/wifi/w0/`). MODEMD logs every packet with
  feature `qrtr-trace`.
- **Bug: wrong message id.** The locator's GET_DOMAIN_LIST is message **0x21**. We had 0x20 since C4, so every
  domain lookup got an error, and the modem never learned that `msm/modem/wlan_pd` provides `kernel/elf_loader`.
- **What the modem does next.** With the right answer, it asks TFTP for `/readonly/firmware/image/wlanmdsp.mbn`,
  then `/readonly/vendor/firmware/wlanmdsp.mbn`.
  - Linux served the first from pmOS's firmware folder.
  - On this phone the file is on vendor_a, so MODEMD now serves `/readonly/vendor/firmware/` reads read-only.
  - It uses tqftpserv's options and windows: blksize 7680, tsize, wsize 10, rsize/seek.
- **Result:** `51 i3` and **WLFW 69** appear, and LTE is unaffected.
- tqftpserv's log never showed those reads, which is why W0a ruled TFTP out by mistake.
- What W0b–W0d ruled out still holds.

## W1: firmware control (done 2026-11-12, phone RAM boot)

`modem-proto/src/wlfw.rs` (`Client`, host tests) is driven by MODEMD once 69 appears. The steps, in ath10k's order:

| Step | Result on the phone |
|---|---|
| Indication register (fw ready, MSA ready) | ok |
| Host capability, 8-bit layout | ok |
| MSA info | two regions: `0x94d00000` + 16 KB (secure), `0x94d04000` + 1008 KB |
| MSA assignment (kernel HAL WlanMsa `0x4e1c`: TrustZone assign_mem, HLOS → MSS_MSA + WLAN, + WLAN_CE unless secure) | ok |
| MSA ready | ok |
| Capabilities | chip `0x30214`, family `0x4001`, board `0`, soc `0x40030001`, fw `WLAN.HL.2.2.5-00426-QCAHLSWMTPLZ-1` (2022-03-08) |
| Board data | vendor_a `firmware/bdwlan-bonito.bin`, 19152 bytes in 4 segments |
| Calibration report | ok |
| Firmware-ready indication | **received** |

- **Board data:** the factory image's vendor folder has `bdwlan-bonito{,-ROW,-USA,-JPN,-VZW}.bin` and the `-sargo`
  set. The default file is used for now. **Owner question:** pick the regional file by country before any release.
- **New kernel HALs:**
  - `0x4e1b` FwRead: modem_a files; kept for the `/readonly/firmware/image/` path;
  - `0x4e1c` WlanMsa.
- **Next, W2:** the PDD's copy engines and HTC/WMI, then WLAN cfg + mission mode
  (`wlfw::wlan_cfg`/`wlan_mode`, tables from ath10k `snoc.c`).

## W3 design gate: WHA → WMI mapping (written 2026-11-12)

UMAC (the Symbian WLAN LDD) drives the chip through `WHA::Wha` (`wlan_hal_api/inc/wha.h`). The PDD turns each call
into WMI-TLV commands (ath10k names; ids in `wmi-tlv.h`) and the firmware's events into `MWhaCb` callbacks.

| WHA call | WMI-TLV | Notes |
|---|---|---|
| `Initialize(data)` | — | W2's bring-up (copy engines, HTC, WMI init → READY) has run by then; `data` (UMAC's init blob for its own chips) is ignored |
| `Configure(SConfigureData, SSettings&)` | `VDEV_CREATE` (STA, the READY MAC) | Fill `SSettings` from SERVICE_READY (chains, bands) and READY (MAC). One vdev for life |
| `Scan(rate, band, channels, type, probes, ssids)` | `SCAN_CHAN_LIST` once per channel set, then `START_SCAN` (active/passive, SSIDs, dwell) | Beacons and probe responses arrive as `MGMT_RX` events → `ReceivePacket` (802.11 frames: the firmware hands up the whole management frame). `SCAN_EVENT` completed → `CommandComplete(EScanComplete)` |
| `StopScan()` | `STOP_SCAN` | |
| `Join(mode, BSSID, SSID, band, channel, beacon interval, basic rates, …)` | `PEER_CREATE` (BSSID), `VDEV_START_REQUEST` (channel, beacon interval) | Then UMAC sends Authentication and Association Request itself through `SendPacket` |
| `SendPacket` of a management frame | `MGMT_TX_SEND` (frame by value or DMA) | Completion event → `SendPacketComplete` |
| `SetBssParameters(DTIM, AID)` | `PEER_ASSOC` (rates/HT caps from the beacon UMAC saw), `VDEV_UP` (AID, BSSID), `VDEV_SET_PARAM` DTIM | **The AID comes straight from UMAC**, no frame parsing. Rates and HT caps: the PDD keeps the last beacon/probe response of the BSSID it joined |
| `AddKey(type, key, index)` | `VDEV_INSTALL_KEY` (pairwise/group, CCMP/TKIP, key index, MAC) | The 4-way handshake frames (EAPOL) go as data |
| `RemoveKey(index)` | `VDEV_INSTALL_KEY` with key length 0 | |
| `SetPsMode(mode)` | `STA_POWERSAVE_MODE` | |
| `ReadMib` / `WriteMib` | `PDEV_SET_PARAM` / `VDEV_SET_PARAM` per MIB; the rest answered from PDD state | MIB by MIB in W3/W4; unknown MIBs succeed and log |
| `ConfigureQueue` / `ConfigureAC` | `VDEV_SET_WMM_PARAMS` (later) | Defaults until then |
| `SendPacket` of a data frame | HTT TX on CE4 (native-wifi decap: 802.11 header without QoS) | W4. RX: HTT RX on CE1/5/9/10 → rebuild an 802.11 header for `ReceivePacket` |
| `Reset()` / `Release()` | `VDEV_DOWN`, `VDEV_STOP`, `PEER_DELETE`, then WLFW `wlan_mode(OFF)` | |
| `Measure`, `Plt` | — | Not supported (UMAC has defaults) |

**Main risk, confirmed manageable:** WHA is softmac-like, the firmware offloads. The open items are:
- the rates and HT caps for `PEER_ASSOC`, kept from scan results;
- data-path header translation (HTT native-wifi ↔ 802.11).

Nothing in WHA needs the firmware to accept raw 802.11 data frames.

## W2: copy engines, HTC, WMI (done 2026-11-12, phone RAM boot)

`kernel/baseport/arm64/sdm670_assp/qcom_wcn3990.cpp` (kernel branch `wifi/w0b`) is started by MODEMD after WLAN cfg +
mission mode (HAL WlanStart `0x4e1d`). It is polled, with its own DFC thread. Result:

```
[wifi] SMMU streams 40/1 -> 0; DMA pool 830d0000 + 80000
[wifi] copy engines up (280512 bytes of the pool); waiting for HTC ready
[wifi] HTC ready: 2 credits of 2184 bytes, 22 endpoints, HTC 2.1
[wifi] HTC service 0300 -> status 0, endpoint 1, max 2000
[wifi] HTC service 0100 -> status 0, endpoint 2, max 2040
[wifi] WMI service ready: ABI 1.0.0.1074, 2 RF chains, 0 memory requests (0 allocated), board 0
[wifi] WMI ready: MAC 00:00:00:00:00:00, status 0 (W2 done)
```

- **The MAC is all zero.** The WCN3990 stores none (ztOS FIXES #10). The host must send PDEV_SET_BASE_MACADDR with a
  stable, locally administered address (planned: `02:…` derived from the phone's serial), the first step of W3.
- **Lessons:**
  - The DMA pool is device memory: only aligned 32-bit accesses (a merged 8-byte store faulted).
  - Size tx buffers only for the CEs used (CE4 alone would take 512 KB).
  - A lost USB console is not a crash: check `lastlog` (that run ran 900 s, then AUTOFASTBOOT).
- **Not yet:** IRQs (polled), HTT, the WHA PDD.

## W3a: first scan (in progress, 2026-11-12)

`qcom_wcn3990.cpp` continues after READY. The firmware accepts every command, and the scans start and complete
(reason 0):
1. PDEV_SET_PARAM chain masks;
2. SCAN_CHAN_LIST (2.4 GHz 1–13, 5 GHz UNII-1/3);
3. PDEV_SET_REGDOMAIN (the reg caps' `eeprom_rd` is 0, so US `0x3a`, as ath10k);
4. VDEV_CREATE (station);
5. START_SCAN, passive and active;
6. the HTT version request: reply `00 60 03 00`.

**The radio receives:** CHAN_INFO on 2412 MHz shows 29 % rx clear and a noise floor of −118 dBm.

**No beacon reaches the host.** There is no WMI MGMT_RX and no frame on another endpoint. The likely cause is the
HTT rx ring: ath10k's RX_RING_CFG carries `HTT_RX_RING_FLAGS_MGMT_RX`, and we have not configured it yet. Next
(W3b): HTT setup (frag-desc bank, RX_RING_CFG, aggregation config) and handling the rx indications.

## W3b: the first scan works (2026-11-12, phone RAM boot)

The firmware needed the **HTT rx ring** before it delivers any received frame. Its MAC rx ring is fed from the
host's HTT ring; without one it receives (CHAN_INFO) but drops everything. `qcom_wcn3990.cpp` (kernel `55c78060`):
- After the HTT version reply (3.96) it sends FRAG_DESC_BANK_CFG, RX_RING_CFG and AGGR_CFG:
  - FRAG_DESC_BANK_CFG: 1056 x 72 B bank;
  - RX_RING_CFG: 2048-entry ring with 128 buffers of 2 KB; flags `0xffff`; the WCN3990 rx-descriptor offsets
    74/90/27/37/4/26/7/12/1/2;
  - AGGR_CFG: `05 40 03 00`.
- It then handles `RX_IN_ORD_PADDR_IND`. Sources: `private/wifi/w3b-htt-rx-spec.md` (ath10k, ISC).

**Result:**
- **Passive scan over 22 channels:** 16 networks from 23 beacons, 2.4 and 5 GHz, −46 to −92 dBm. All arrived as WMI
  MGMT_RX; no HTT copies.
- **Active scan (broadcast probe):** 9 networks.

The full log, with the networks' names, stays in `private/wifi/w0/` (they are neighbours' networks).

**Next (W3 proper, then W4):**
- Make the driver a long-lived service: interrupts instead of the fixed polling window; a stable MAC from the phone.
- Then the WHA PDD under Symbian's UMAC, or a direct WMI join path for a first association (W4).

## W3c: Wi-Fi in Settings (2026-11-12, phone RAM boot)

**Kernel** (`qcom_wcn3990.cpp`, branch `wifi/w0b`):
- The driver stays up after bring-up as a polled service.
- **HAL WlanScan `0x4e1e`** (ReadDeviceData) returns the latest list (`{version, state, count, scans}` + 42-byte
  entries) and takes a scan request.
- Scans are passive: active ones missed the 2.4 GHz networks here.
- A network's channel comes from its own beacon (DS IE, else HT operation).
- The station MAC is `02:4e` + the SoC serial (SMEM socinfo).

**neoui** (branch `wifi/settings-scan`):
- Settings → Wi-Fi is its own page:
  - the switch and status;
  - **Available networks**, strongest first, with signal-tinted icons and security/band/dBm;
  - "Searching…" and a refresh button; hidden networks are counted, not listed.
- **Scanning:** opening the page scans unless the list is under 30 s old; it rescans every 30 s while open and never
  while closed.
- **Tapping a network opens a sheet:** signal, security, band, channel, a password field, Cancel/Connect. Connect
  says that joining is the next step (W4).
- **Since 2026-11-12 the password field is real** (neoui `32b783a`):
  - it is masked and focused when a secured network's sheet opens;
  - the system keyboard comes up with the sheet above it;
  - the typed password is kept in the sheet (`wifi-password`), ready for W4 to join with.
- Host-tested (neoui-proto `wifi`), snapshot `settings-wifi-*-pixel.png`; on the phone it lists 15–18 nearby
  networks on both bands.

## W4: joining a WPA2-PSK network (connected 2026-11-12)

**Decision (owner, 2026-11-12): the direct path first.** The scan (W3) already runs straight from
`qcom_wcn3990.cpp` over WMI, without Symbian's UMAC LDD. W4 extends that driver rather than building the UMAC + WHA PDD
now. UMAC/WHA stays the documented long-term option (the W3 gate above stays as reference). The WPA2 handshake is
user-side Rust, so there is no crypto in kernel C++.

| Part | Where | State |
|---|---|---|
| Join: VDEV_START, PEER_CREATE (HTT PEER_MAP), open-system auth, Association Request (legacy rates, our RSN element), PEER_ASSOC, VDEV_UP; teardown PEER_DELETE, VDEV_DOWN, VDEV_STOP | kernel `qcom_wcn3990.cpp` (W4a) | built, QEMU gate passed; not run on the phone yet |
| Management tx: WMI MGMT_TX_SEND by reference if WMI service 76 is on, else HTT TX_FRM type 3 (the log says which) | kernel | as above |
| Data path for EAPOL: HTT TX_FRM native wifi on CE4 (gather send, ext descriptor in the frag-desc bank, NO_ENCRYPT before the PTK), TX_COMPL_IND; native-wifi HTT RX (EAPOL to the user side, ARP/IP counted) | kernel (W4c) | as above |
| Keys: VDEV_INSTALL_KEY CCMP (acked by HTT SEC_IND), PEER_SET_PARAM AUTHORIZE | kernel (W4c) | as above |
| HAL `WlanLink` `0x4e1f` and the monitor's `wifi` / `wifi join N` / `wifi leave` | kernel | as above |
| HAL `Prng` `0x4e23`: the SoC PRNG for the SNonce | kernel `qcom_telhal.cpp` | as above |
| WPA2-PSK supplicant: PBKDF2 PMK, PTK, MIC, GTK unwrap, 4-way + group rekey, sans-I/O | neolink `crates/wpa` (W4b) | **done**, host-tested (IEEE Annex J and RFC 3394 vectors, a full 4-way against a test AP, wrong password, replays, RSN downgrade) |
| Connect on the network sheet: a supplicant thread in SYSSTART drives the HAL; the sheet shows Connecting… / Connected / Wrong password; a connected network is remembered (SSID + PMK in `C:\private\e0002001\wifi.dat`, never the password) and rejoined when seen | neoui `symbian/src/wifi.rs` (W4d) | built, host-tested (`Link`, `Saved`) |

Facts: `private/wifi/w4-join-spec.md` (ath10k, ISC; mac80211 facts only).

**Shortcuts** (in the code as `shortcut:` comments):
- legacy rates only (no HT/WMM): an HT-only AP refuses with status 27 or 18;
- no PMF: an AP that requires it refuses with status 31;
- no scans while joined;
- the supplicant is a thread of SYSSTART until W5's network interface needs a daemon;
- non-UTF-8 SSIDs hash wrongly;
- after a modem stop (C7 recovery) Wi-Fi stays off until a reboot: the WLAN firmware runs inside the modem, and a
  second bring-up would reuse DMA memory still carved for the old rings (`Wcn3990_ModemDown`).

### Result: connected (phone RAM boot, 2026-11-12)

**The phone joined the owner's WPA2-PSK network** (5 GHz channel 44, −50 dBm) from Settings by touch:
- auth and association (AID 4);
- msg1 → msg2 (acked) → msg3 → msg4;
- the pairwise and group CCMP keys installed (the firmware acked both), the peer authorized;
- decrypted ARP/IP broadcasts arriving (58 of 60 data frames in the first minute);
- the status bar shows the Wi-Fi icon. Logs and screenshots: `private/wifi/w4/`.

**Firmware facts learned on the phone** (the spec had them as inferences):
- Management TX goes over WMI: the firmware sets service 76.
- **The firmware holds msg4 until the PTK is installed.** With the driver waiting for msg4's TX report first, no
  report came in 2 s, the AP resent msg3, and the report arrived as DISCARD at teardown.
  - EAPOL sends are therefore only queued (NO_ENCRYPT fixed at queue time), and the PTK follows at once, as Linux's
    supplicant does.
  - The supplicant answers a resent msg3 with msg4 only and never reinstalls a key (KRACK).
- **A WMI credit can be slow to come back after a handshake.** Link commands wait 3 s and fail alone. Before this fix,
  one slow credit marked the whole driver failed. The monitor's `wifi` shows the credits.
- A wrong password looks like this: msg1 over and over, each msg2 acked, no msg3.

**Settings** (neoui `wifi/join`):
- "Current network" above the list, and the Wi-Fi rows say "Connected to …";
- a details sheet: signal, band/channel, security, access point, phone MAC, AID, frames received, IP (none until W5);
- Disconnect (stays saved but is not rejoined on its own until Connect) and Forget.

**Not yet:**
- How long the link holds (the RAM image returns to fastboot after 20 min);
- rejoin after a reboot: the saved network is on C:, which a RAM boot does not keep;
- an IP address: W5.


## W5: an IP address (smoltcp, 2026-11-12)

**Decision (owner, 2026-11-12): smoltcp first.**
- W4 took the direct path, so there is no UMAC LDD for `wlannwif` to sit on, and ESOCK/TCPIP6 (W5a) is not in the
  build at all.
- W5 therefore uses smoltcp (0BSD) in a Rust daemon.
- ESOCK/TCPIP6 stays the long-term option. Its Ethernet NIF could later read the same kernel frame queue, through
  Symbian's `d_ethernet` LDD or the HAL ops below.
- The owner also asked for an app socket API.

```
kernel  DataIn --(Ethernet II)--> rx queue --WlanLink op 8--> NEONET.EXE (smoltcp: DHCP, DNS, TCP, ping replies)
        tx queue <--WlanLink op 9-- NEONET.EXE                     ^ IPC "NeoNet"
        Serve() drains tx -> DataTx (native wifi)            SYSSTART (status, internet check), apps
```

**Kernel** (`qcom_wcn3990.cpp`):
- **Rx:** data frames other than EAPOL go to a 32-frame rx queue as Ethernet II (DA = addr1, SA = addr3). They are
  queued only when all of these hold:
  - the link is connected (keys in);
  - the rx descriptor shows no decrypt, MIC or FCS error (attention bits 29/28/30);
  - the frame is FromDS, addressed to us or a group;
  - its SA is not our own (no echoes of our broadcasts).
- **Tx:** a 16-frame tx queue. The driver thread drains it each pass into HTT TX_FRM: native wifi, addr3 = the
  Ethernet destination, Protected once the PTK is in.
- **Size:** the tx slots grew from 512 bytes to 1536 (a 1514-byte frame is 1532 as native wifi).
- **HAL WlanLink `0x4e1f`:**
  - op 8: the next received frame (`KErrNotReady` if none);
  - op 9: queue a frame (14–1514 bytes, from our MAC; `KErrNotReady` unless connected, `KErrOverflow` if full).

  Neither waits on the driver thread.
- **Monitor:** `wifi` prints a second line with the queue counters.

**neolink:**
- **Crate `net`:** the `Stack` (sans-I/O, host-tested on smoltcp's loopback device), the IPC protocol `proto`, and
  the `client` (feature `client`).
- **`symbian/neonet`, NEONET.EXE** (uid `0xE0004001`):
  - reads the link every 200 ms, and on "connected" brings the interface up with the station MAC;
  - polls frames every 2 ms while linked;
  - serves "NeoNet".

**The NeoNet API** (`net::proto`):

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

**neoui** (SYSSTART):
- starts NEONET.EXE at boot;
- reads its status every second while connected;
- runs one internet check per address. The check uses the client API: resolve
  `connectivitycheck.gstatic.com`, connect to port 80, `GET /generate_204`, expect 204.
- The Wi-Fi details sheet shows IP address, Gateway, DNS and Internet (Checking… / Connected / No access).

**Shortcuts:**
- IPv4 only;
- no UDP or listening sockets in the API;
- frames polled every 2 ms while linked (no interrupts yet);
- one TCP buffer size (8 KB each way, 16 sockets);
- a captive portal shows as "No access";
- the supplicant stays a SYSSTART thread.

### Result: an IP address and the internet (phone RAM boot, 2026-11-12)

- **DHCP:** the saved network rejoined at boot, and NEONET logged `Up: 192.168.3.53/24 gateway 192.168.3.1`
  seconds after `link connected`.
- **Ping from the Mac:**
  - 5/5, then 20/20 at 0.2 s intervals, 11–29 ms;
  - 3/3 with 1472-byte payloads (full 1514-byte frames both ways);
  - the driver's counters showed nothing dropped and no failed sends.
- **Internet check through the app API:**
  - In the first image NEONET dropped requests that had to wait: a dropped `Message` completes with KErrGeneral,
    so the check failed with -2.
  - With that fixed, the owner joined from Settings, and the details sheet showed "Internet: Connected" (DNS,
    TCP to port 80, the `generate_204` reply).
- **Firmware facts:**
  - Data frames get TX_COMPL_IND like EAPOL, so the tx slots free themselves.
  - Received data frames arrive as native wifi with FromDS set.
- Logs: `private/wifi/w5/`.

**Not yet:**
- hours-long link stability and throughput;
- the app API from a second app;
- a C++ client for legacy apps.

## After W5: background rejoin, handshake timeout (2026-11-13)

**Background rejoin** (neoui `symbian/src/wifi.rs`):
- When all of these hold, SYSSTART asks for a scan:
  - the Wi-Fi page is closed;
  - the link is idle, lost or in error;
  - a saved network exists that the user didn't disconnect from;
  - the Wi-Fi switch is on;
  - the list is over 60 s old.
- The existing rejoin then finds the saved network.
- **Phone:** after the monitor's `wifi leave`, the link came back in 50 s with Settings closed, with DHCP and the
  internet check.
- The Wi-Fi switch (`radio.wifi`) now stops scanning and rejoining. The radio itself stays up (shortcut).

**A wrong password crashed the modem** (phone, 2026-11-13; log `private/statusbar/fail1.log`):
- This AP kept resending message 1 for a minute and never deauthenticated us. Each msg2 was acknowledged; no msg3
  came.
- The WCN3990 firmware then asserted in `wlan_powersave_sta.c:wlan_ps_sta_health_monitor_timeout`. That is a FATAL of
  the whole modem: LTE dropped and MODEMD ran its recovery. Wi-Fi stays off until a reboot (the known shortcut).
- **Fix:** the supplicant leaves after 10 s in the handshake and the sheet says "Wrong password". Retyped correctly,
  the same AP connected at once.
- **Open:** a kernel-side guard (tear down a join stuck in the handshake) in case the supplicant thread dies.

## W7: interrupts, the handshake guard, a modem restart (design, 2026-11-13)

**Interrupts instead of polling (battery).** Today the driver thread polls the copy engines every 2 ms while
connected, and NEONET polls HAL op 8 every 2 ms.
- **GIC:** `A64_BindSpi` takes every INTID up to 1019, not only those under 256. The CE lines are SPI 414–425 (INTID
  446–457), level-triggered. New `A64_MaskSpi`/`A64_UnmaskSpi`.
- **Driver (`qcom_wcn3990.cpp`):**
  - Binds the destination copy engines that carry traffic: CE1, CE2, CE5, CE9, CE10, CE11. Their `HOST_IE`
    copy-complete bit is set.
  - **The ISR masks its line at the GIC** (the GIC acknowledges before the ISR runs, so a level line would fire again)
    and adds an IDFC. The IDFC signals the `Serve()` thread's fast semaphore.
  - **`Serve()` waits on that semaphore**, then clears `HOST_IS`, reaps, and unmasks. A timer wakes it too:
    - every 1 ms while scanning or in a join (these stay polled);
    - every 100 ms while connected (housekeeping);
    - every 1 s otherwise.
  - The HAL requests (join, leave, frames to send, scans) also signal the semaphore.
  - **Fallback:** if frames keep arriving while no interrupt has fired, the driver logs it and goes back to the old
    polled sleeps.
- **HAL WlanLink op 10 (notify):** a2 is a `TRequestStatus*`. It completes when a received frame is queued or the
  link state changes, or at once if a frame is already waiting. One request at a time. **Op 11** cancels it with
  `KErrCancel`.
- **NEONET** waits on op 10 together with its server messages and smoltcp's next timer, instead of polling every
  2 ms. If op 10 is refused (an older kernel), it falls back to the 2 ms poll.

**Handshake guard.** If the link stays in the handshake for more than 15 s (the supplicant gives up at 10 s), the
driver tears the join down itself: link error, `KErrTimedOut`.

**A modem restart.** `Wcn3990_ModemDown` only sets a flag. `Serve()` then:
- masks the CE interrupts;
- ends the link (lost);
- resets the bring-up state;
- returns.

`Wcn3990_Start` accepts a new start once the modem is down. `Run()` already reuses the DMA pool and carves the same
layout again from offset 0. MODEMD re-runs WLFW after the modem restarts and calls WlanStart. NEONET and neoui's
rejoin then work as after a boot. **Risk:** the chip may not accept a second WMI init without a reset. The phone test
will tell.

**Result (phone, RAM boot, 2026-11-13; kernel `6bac85c6`):**
- `serving: CE interrupts`. Scans, the join, DHCP and SYSSTART's internet check all ran on interrupts, and the saved
  network was rejoined at boot on its own. Ping from the Mac: 10/10, 15 ms average. NEONET logs `link events on`
  and no longer polls.
- On a weak AP (-75 dBm on 5 GHz) the link dropped on a beacon miss (the firmware's roam event, reason 2) in both
  interrupt and polled mode (`wifi polled` A/B), so not an interrupt problem. On the strong AP it held.
- **After `mss fault`,** the driver let go as designed (`Wi-Fi waits for WlanStart`). The modem restarted (QRTR up
  after 6.4 s), but MODEMD then found the ADSP reporting fatal (its state word `[4, 0, 7, 3]`, bit 0) and restarted
  the modem again, three times, until the modem itself went FATAL. So WlanStart never came, and **the re-init is
  not proven yet.** Cause and fix: [telephony.md](telephony.md), "Modem restart and the ADSP".
- The 15 s handshake guard was not triggered (the supplicant's 10 s timeout acts first).

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
| `NEOTIER.DLL` (`build/apps/esock/neotier`) | ECom: a tier manager whose selector always picks the tier's default access point, whatever the preferences (an IAP, a SNAP, none), and the core MCPR. CommsDat holds these UIDs as signed fields, so they are `0x0E004005`/`0x0E004006` |
| `NEONET.PRT` (`build/apps/esock/neonetprt`) | The KAfInet protocol module: TCP (connect, listen/accept, stream data) and UDP (bind, send-to, receive-from, "connected" datagrams), and the host resolver, all over `NEONET.DLL`. It runs in ESock_DIP and never blocks: each waiting NeoNet call is an active object. Cancelling closes the NeoNet socket (or, for a connect, the session), and NEONET then answers the waiting call with KErrCancel |
| `ip.neonet.esk` | `protocols= tcp,udp` from `neonet.prt` |
| CommsDat | The ROM repository is the 2010 empty one (`defaultcommdb/src/empty.txt`, policies only). `NEOCDB.EXE` writes our records at boot through the CommsDat API, so they always match this schema: the MCPR, the vanilla CPR/SCPR, the flow shim, access point 10000 "NeoNet", tier 2048 (ESock_IP, neotier's tier manager), and GlobalSettings' default tier. It does this once; NEONET starts it |
| `NEOSOCK.EXE` | The test, through the 2010 API: the protocol list, `RConnection` Start/Stop, resolving `localhost`, TCP listen/accept/connect and both directions, and a UDP datagram, all on 127.0.0.1. With `net`, it also fetches `generate_204` |

**NEONET on a board without Wi-Fi (Syborg):** the HAL has no WlanLink, so NEONET runs a loopback interface at
127.0.0.1/8 (a static address, no DHCP; `localhost` resolves). This makes the whole path testable on QEMU.

**Why not the 2009 Linux `ced`:** commsfw ships a prebuilt i386 `ced`, and it runs in an i386 container. But it writes
the pre-Symbian^3 schema: its tier records have no `TierImplUid`, and ESOCK's lookup of tier 2048 needs one. Writing
the records at run time through CommsDat avoids both a host build of `ced` and a hand-made `.cre`.

**Result (2026-11-13; build `61ce5c4`):**
- **Syborg (QEMU):** `NEOSOCK` passes on NEONET's loopback: the protocol list, `RConnection::Start`, `localhost`,
  TCP listen/accept/connect and data both ways, and UDP. This meets the W5a exit test.
- **Phone, over Wi-Fi:** `NEOSOCK` passes (the 2010 API: an HTTP 204 from connectivitycheck.gstatic.com over TCP
  and a DNS answer from the gateway over UDP), and so does `NEONETT` (NEONET.DLL directly). CommsDat persists on C:
  (`neocdb: tier 2048 present` on the next boot).
- **Found on the way:** every Rust EXE had asked for a 128 KB stack since 2026-11-11, and the 2010 kernel on Syborg
  refuses more than 80 KB ("Too Big"). Probably that is also why the neoui Syborg CI is red. `exes.txt` now takes
  `stack=`.

**Shortcuts:**
- socket options are accepted and ignored;
- one waiting connection per listener;
- no reverse lookups;
- the UPS prompt stubs (upsclient) are never reached, because the vanilla access point carries no UPS extension;
- no IAP records yet, so apps that list IAPs see none.
