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
| SMMU stream | `0x640`, mask `0x1` (`iommus = <&apps_smmu 0x40 0x1>`) | DTB |
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
| **W2** (1–2 wk) | Kernel `sdm670_assp/qcom_wcn3990*.cpp`: CE rings, SNOC setup, interrupts, SMMU stream `0x640` (`Smmu_IdentityMap`); HTC connect (WMI control, HTT data); WMI init/ready | Monitor `wifi` prints the firmware version and MAC |
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

**Next, W0d:** MODEMD logs the modem's NEW_LOOKUPs and data sent to ports we don't serve (until now both were dropped
silently), to see what the modem's root domain asks for before it would start `wlan_pd`.
