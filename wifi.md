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
| **W5a** (parallel, 1–2 wk) | ESOCK/TCPIP6 + CommsDat (default database), the C32/ESOCK configs and ECom comms plugins, through `build/emitter/components.py`; Syborg first | A loopback TCP test EXE passes on Syborg CI |
| **W3** (1–2 wk) | The UMAC LDD built into ekern (as `locmedia` is); WHA Initialize/Configure → WMI vdev create; Scan → WMI start scan; beacons from WMI management RX → `ReceivePacket`; wlanengine + management client in the ROM | A test EXE lists nearby networks |
| **W4** (1–2 wk) | Join/SetBssParameters → vdev start, peer create/assoc, vdev up; management TX over WMI, data and EAPOL over HTT (802.11 headers rebuilt on RX); AddKey → WMI install key; accesssec EAPOL in the ROM | Joins an open network, then WPA2-PSK |
| **W5** (1–2 wk) | `wlannwif` + DHCP/DNS on the phone, a CommsDat WLAN access point | Ping and an HTTP fetch over Wi-Fi |
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
