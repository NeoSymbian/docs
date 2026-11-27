<!-- SPDX-License-Identifier: Apache-2.0 -->
# GNSS research: zero C/N0 on bonito and the first-fix plan

Part of [Hardware](README.md) · Status: research · Updated: 2026-11-20

The long version of [gnss.md](gnss.md)'s "Getting a first fix" section; its G0–G5 are gnss.md's GR0–GR5 (G4a and G4b are GR4). Written by a
Codex research run on 2026-11-20, from Android, Linux and our own logs; reviewed and published unchanged in substance.
Paths: `neohw/` = NeoSymbian/neohw at `208b878` (branch `gnss/gn1`), `kernel/` = NeoSymbian/kernel at `6d34d8da`,
`docs/` = this repository, `private/` = the owner's unpublished captures (not in any repository). Line numbers are
those revisions'.

Research date: **2026-11-20**. Target: **NeoSymbian EKA2/AArch64 on Pixel 3a XL**, not Android/Linux.

**Root cause remains unproven.** The research ran without phone access, builds or code changes.

## Finding

**There is no verified missing Bonito “GPS LNA enable” GPIO, voltage, or mandatory extra LOC RF-enable command in the reviewed public sources.**

First validate the observation and perform a genuine outdoor acquisition; then use Linux on this same handset to separate LOC policy from kernel/RF/firmware differences. An unpowered or misconfigured receiver remains plausible if **valid C/N0 stays zero outdoors**. A window test and a satellite list alone do not establish that diagnosis. Qualcomm’s Android implementation explicitly retains ephemeris/almanac entries with zero SNR after tracking stops. [A1, source lines 2082–2125]

Labels below:

- **Observed:** supplied evidence or inspected local code/log.
- **Sourced:** external implementation/documentation.
- **Hypothesis:** proposed explanation, not verified on this phone.

Gates and thresholds are proposed acceptance criteria.

## What is established

- **Observed:** engine unlock, standalone mode, engine-on, IN_PROGRESS and TIMEOUT are reported. The saved `xtra-test-ring.txt:616–619,803–809` shows Start at 72.3 seconds and timeout at 327.3 seconds while MSS remains up. All-zero SVs near a window are owner-reported and recorded in the design; the inspected saved logs do not contain raw SV records establishing validity/status for every entry. [L1,L2]

- **Observed:** packed SV decoding uses TLV `0x10`, a `u8` count, 28-byte entries, float SNR at offset 24 and validity bit 7. That agrees with libqmi. However, truncated arrays can still return `listed=n, heard=0`; absent/malformed TLVs become zero through `unwrap_or_default()`. Initial all-zero statistics may not log because only changed heard/best buckets log. **“No valid positive C/N0 reported” is currently better supported than “every satellite measured zero.”** [L3,L4,Q1]

- **Observed:** startup is not a completion-gated sequence: service discovery queues Register/Get Lock/Set Mode/Source, and Start can run before the later unlock indication. Send failures are ignored and requests lack pending-transaction tracking. This deserves correction, although subsequent engine-on/SV indications make a permanent startup failure less likely. [L4]

- **Observed:** rmtfs starts from real `modemst1/2,fsg,fsc` reads. Writes update RAM images and are readable within that run, but are lost when those images are rebuilt. `persist` and `modemcal` are not in this HAL partition allow-list. This does **not** establish that their GNSS data is missing or must be exposed. [L5,L6]

- **Observed correction:** `mcfg.tmp` WRQ is **accepted**: one byte is retained, then RRQ is refused. Hardware/software digest RRQs are refused. The same digest failures occur in C1, but C1 never attempted GPS, so C1 cannot exonerate them. [L7,L8]

- **Observed:** C1 enabled cell-location sources, with GPS RAW/NMEA and AGPS disabled. Its successful LOC queries prove transport/configuration access, not RF reception. It used C0 backup EFS copies in RAM, whereas current HWHUB reads current partitions; these are not controlled equivalent inputs. [L8,L9]

## Ranked causes and cheap discriminating tests

Ranking is **investigation priority**, not a quantified probability.

| Rank | Hypothesis and evidence | Cheap future phone test; interpretation |
|---|---|---|
| **1** | **Indoor attenuation plus acquisition without confirmed fresh assistance.** Only the window condition is established; no outdoor result exists. Android permits listed zero-SNR entries. [L1,A1] | Same baseline, stationary open sky for the full 15-minute daemon limit; known-good receiver nearby, fixed orientation, Wi-Fi/BT idle and no deliberate LTE upload. Log valid C/N0 periodically. Positive C/N0 moves the problem toward acquisition/assistance; persistent valid zeros justify RF/config isolation. Do not promise a fix by a specific minute. |
| **2** | **Observability hides invalid/truncated reports.** Concrete parser/logging weaknesses exist, but no stride/offset bug was demonstrated. [L3,L4,Q1] | Capture raw LOC SV payloads and independently decode using libqmi/matching IDL. Separate invalid, malformed, valid-zero and positive values. Resolve any decoder disagreement before hardware work. |
| **3** | **LOC policy/race:** mode or unlock incomplete; inherited constellation acquisition restrictions or low-power setting. The race exists; inherited settings remain unknown. [L4,A1,Q2] | Serialize and verify lock/mode, then read supported constellation/acquisition and low-power state. One supported setting change per run, followed by read-back. Require C/N0/tracking improvement, not increased listed count. |
| **4** | **Firmware/EFS/MCFG mismatch or incomplete TFTP semantics.** A real read-after-write defect exists; Android provisions MCFG files. GNSS causality is unverified. [L5,L7,L8,D3,T1] | First repair RAM-only `mcfg.tmp` read-back in one future image. Separately compare current-versus-C0 EFS inputs while holding other inputs constant, then exact matching stock MCFG files if requests require them. Record requests, bytes, status and C/N0. No NV guessing or persistent writes. |
| **5** | **Missing AP-owned rail/clock/pin state or wrong modem RF-board selection.** Android MSS resources are known; no GNSS-specific control was found. NeoSymbian already supplies board SMEM and MSS votes. [K1,L10] | Compare Linux/Android against NeoSymbian resource and pin states before/after LOC Start, plus SMEM134/firmware provenance. Implement only a demonstrated AP-owned difference, one RAM image per variable. |
| **6** | **Antenna/contact failure or radio desense/coexistence.** Bonito antenna sharing and WCI2 prerequisites were not verified. | Same outdoor test under known-good Android/Linux; separately idle Wi-Fi/BT, then test cellular traffic. Failure under all OSes elevates antenna/hardware; failure tied to a transmitter elevates coexistence. Working LTE/Wi-Fi alone does not validate the GNSS antenna branch. |

## Android RF ownership: what to port and what remains unknown

**Sourced:** downstream MSS DT declares XO/GCC clocks, CX/MX/MSS proxy power, AOP and SMP2P; `mss.lvl` maps to PM660 S5/VDD_MODEM. This identifies modem-subsystem power, **not the GNSS LNA or SDR/WTR supplies**. [K1]

The bounded search covered Google `sdm670-b4-pvt.dts`, `b4-common`, `b4s4-common/pinctrl`, Qualcomm `sdm670.dtsi`, its regulator/pinctrl/PMIC overlay, `pm660.dtsi`, `pm660l.dtsi` and `pm660-rpm-regulator.dtsi` at K1’s pinned kernel revision. No GNSS/GPS/LNA/RFFE/WTR/SDR/COEX-named board enable was identified. This cannot exclude anonymously named resources or controls inside signed firmware. [K1]

An in-memory traversal of the private DTB’s **818 nodes** likewise found no GNSS/GPS/LNA/RFFE/COEX/WCI match in node/property names; the DTB was not copied. The supplied inspector only emits an allow-list of peripheral compatibles, so its normal output alone cannot prove GNSS-node absence. [L11]

**Ownership boundary:** Android explicitly disallows APSS configuration of these **one-based hardware GPIO numbers**:

- PM660: **1, 5, 7, 8, 10**
- PM660L: **1, 10, 11, 12**

Their actual function is unverified. Do not experiment with them as guessed LNA enables. SoC GPS_TX/NAV_PPS mux alternatives are capabilities, not evidence of a board RF-enable connection. [K2,K3]

**Inference:** modem-controlled RF/RFFE and PMIC votes are plausible, but public DT/init evidence does not prove whether every external RF supply is MSS-controlled, AP-voted or always powered. No exact Bonito SDR/WTR supply mapping or antenna-sharing schematic was verified.

Android’s `modemPowerVote(true)` precedes unlock. A Qualcomm-source mirror implements that through peripheral manager/modem powerup, without LNA GPIO/voltage operations. Its exact Bonito binary provenance is unverified. [A2,V1]

NeoSymbian already releases proxy MX/MSS/XO votes at handover and retains CX for eMMC; it separately enables four WCN3990 supplies and RF_CLK2. **Those Wi-Fi rails are not established GNSS supplies.** Retaining maximum proxy votes is not a justified GNSS fix; kernel comments record earlier modem assertions from doing that. [L10]

Kernel work should first add bounded read-only diagnostics: resource identity, AP vote versus actual accessible rail status, pin configuration/ownership, SMEM board record and modem generation. An eventual verified AP-owned enable needs declared voltage constraints, reference ownership, bounded failure cleanup and release on stop/reset. Respect the existing RPMh mutex/shared-holder model. [L12]

## LOC additions: baseline versus optional Android policy

Android references are protocol evidence, not a transcript of this phone’s proprietary HAL.

| Category | Verified behavior and priority |
|---|---|
| **Startup / client / engine** | Android registers tracking events, waits for Set Operation Mode completion, then starts session 1. No mandatory client-type or extra position-engine setup was found in that baseline. Add response/indication correlation, deadlines, lock/mode read-back and reset-generation handling first. [A1:396–530,L4] |
| **Constellation / GNSS_SV_TYPE** | Distinguish acquisition control and blacklists from `SET_GNSS_CONSTELL_REPORT_CONFIG`, which configures measurement/polynomial reports. Query capabilities/current supported controls; change a demonstrated restrictive acquisition setting. No evidence establishes that omitting report configuration disables RF. [A2:1327–1380,Q2:12486–12523] |
| **Sensors / SLIM service 55** | Android applies sensor control/performance; IDL describes inertial aiding and sensor provider. No standalone reception dependency was verified. Test supported sensor-disabled operation if needed; implementing SLIM first is unsupported. [A2:629–702,Q2:7613–7678] |
| **UTC / coarse position** | Android ages UTC using monotonic elapsed time and includes uncertainty; coarse position includes uncertainty/confidence. Validate NITZ milliseconds, UTC conversion and age. Add optional honest coarse-location injection and inject-position-request handling. Never count an injected location as a GNSS fix. [A1:585–656,L3,L4] |
| **XTRA / XTRA T** | Existing upload is multipart and completion-driven. Add deadlines and matching returned part number; require final success and validity read-back. Test an exact requested file with current UTC. URLs may arrive later in an unsolicited request. A required Bonito XTRA T session-control order was not verified. [A1:1044–1106,L3,L4] |
| **SUPL / server / LPP/LPPE** | Android configures assistance policy; C1 already has `supl.google.com:7275`. Keep standalone for first isolation. No sourced evidence establishes that these omissions alone produce all-zero C/N0. [A2:629–702,L8] |
| **NMEA** | Add the NMEA event and GGA/GSA/GSV types as another diagnostic output. MM uses these; Bonito Android uses AP-generated NMEA. This is not an evidenced RF power command. [M1,D2] |
| **Low power / premium / position-engine config** | Read supported low-power state; A/B explicit disable if available. Premium-service IDL concerns terrestrial/sensor positioning. No universal “enable premium/position engine first” requirement was verified; unknown vendor defaults need a matching trace. [Q2:5073–5081,5158–5163,12360–12384] |

**IDL caution:** libqmi labels SV status idle/search/track as `0/1/2`, while the reviewed Qualcomm header uses `1/2/3`. Preserve raw values and use modem-matched definitions before labeling states. SNR validity bit 7 agrees. [Q1,Q2:1291–1313]

## Linux, firmware and NV

**Sourced:** ModemManager implements periodic LOC Start and NMEA/time/position-request registration without initializing SLIM, premium services or XTRA T first. Maemo Leste’s sargo/bonito Linux 6.12 device page marks GPS/A-GPS working through MM and supplies a LOC/MM recipe, while calling Geoclue integration WIP. This is maintainer-reported support, not acceptance of our handset. [M1,W1]

A future **RAM-only C1 reference** should use one persistent MM LOC client:

```sh
mmcli -m 0 --location-enable-gps-raw --location-enable-gps-nmea
mmcli -m 0 --location-get
```

Confirm the modem index first and enable MM debug/raw LOC capture. MM should configure its own NMEA/session; avoid competing qmicli sessions. NMEA syntax/no-fix sentences are not a fix gate. [M1]

Linux `drivers/gnss` contains serial/USB receiver drivers, not this LOC stack. SDM670/845 PD-mapper tables use plain modem root PD; other platforms explicitly add `gps/gps_service`. There is no evidenced missing Bonito `gps_pd` to invent. Trace actual locator requests and matching JSNs if that changes. [K4,L6]

**Observed firmware strings, not decoded EFS contents:** the local backup `private/radio-backup/modem_a.img` contains:

| String | Byte offset |
|---|---:|
| `/nv/item_files/gps/cgps/me/gnss_config` | `0xac30a0` |
| `/nv/item_files/gps/cgps/me/gnss_wwan_me_config` | `0xac3130` |
| `/nv/item_files/gps/cgps/agps_cold_start_enable` | `0xef778a` |
| `/nv/item_files/gps/cgps/xtra/cgps_xtra_preferred_max_valid_age` | `0xac2fce` |

Binary offsets replace unavailable line numbers here. These establish names only: no values, required bit masks or GNSS RF calibration defaults were decoded. No `gnss_rf_config` string was found in that image. No verified `cgps_nv_*` numeric-item prescription follows.

**Inference:** losing new EFS writes can discard learned assistance/policy after reboot; it does not erase the baseline EFS read from disk or prove that every boot is a fully cold GNSS start. Android provisions persistent RFS directories and MCFG profiles; our RAM EFS already supports intra-run writes. Diagnose missing NV through read-only matched firmware/config inspection or a known-good OS comparison. C1’s RAM-shadow rmtfs is itself a valid reference behavior, with different starting images. [D1,D3,L5,L9,T2]

TFTP is separate from rmtfs EFS: correct coherent RAM read-back first, then serve only verified existing files with exact path/content provenance. A digest is not interchangeable with an MBN. Do not fabricate missing digest responses or enable arbitrary carrier-profile selection. Persistent partition writes remain outside this plan’s early stages and require the existing G4 decision. [L6]

**Research gaps:**

- The official postmarketOS wiki redirected to an access challenge; pmaports GitLab raw/MR access was unavailable. Current official SDM670/845 GPS status/scripts were therefore not verified.
- CodeLinaro was blocked by robots; primary AOSP and pinned Lineage sources were used instead.
- No verified SDM670/SDM845 primary report tied this exact all-zero-SNR symptom to a specific NV, MCFG, coexistence command or rail.
- Bonito antenna sharing with LTE diversity/Wi-Fi and a mandatory WCI2/AP COEX setup remain unknown.

## Execution stages and gates — future work only

### G0: Make signal evidence trustworthy

Instrument bounded raw SV records, validity/float C/N0/status, session/engine/mode, position technology/source and used-SV fields, transaction results and periodic zero reports. Reject truncated lists.

Host vectors must cover invalid SNR, positive/zero floats, absent/truncated TLVs and delayed/out-of-order completions.

**Gate:** independent decoding agrees, and malformed/unknown never appears as measured zero.

### G1: Reproducible outdoor baseline

Serialize:

```text
Registration completion
→ unlock and read-back
→ standalone completion and read-back
→ Start
```

Record one 15-minute open-sky run and radio activity. Keep assistance unchanged for this comparison.

**Gate:** sustained valid positive C/N0 on multiple SVs. Otherwise, a diagnostic negative requires completed configuration, periodic undropped indications, per-entry SNR-valid bits and raw process states. Invalid/absent C/N0 remains unknown. Even a complete zero trace does not identify an LNA failure.

### G2: Isolate policy and assistance, one variable per run

Query low-power/acquisition configuration. Separately correct one restrictive setting, inject accurate UTC, then optional coarse position, then acknowledged XTRA.

The current downloader downgrades HTTPS to HTTP/80 and cannot handle every HTTP response form. If delivery fails, use an explicitly prepared exact requested file for the experiment rather than treating delivery failure as RF evidence. [L13]

**Gate:** accepted commands and read-backs. Separately record C/N0, satellite-derived fix and TTFF. Stop expanding HAL features once reception works.

### G3: Same-phone Linux comparison

RAM-boot the existing C1 approach with GPS explicitly enabled, current matched firmware and the same initial EFS set. Capture open-sky SV/NMEA/fix, rmtfs/TFTP and firmware/resource state.

**Gate:** Linux reception with NeoSymbian zeros narrows the investigation to OS setup. Zeros on both require known-good Android/hardware/config evidence. Wiki success does not substitute for this gate.

### G4a: Bounded service/config corrections

A/B RAM TFTP read-back, then independently test exact missing stock files/EFS input differences. Keep flash partitions untouched.

**Gate:** coherent request/read-back plus a reproducible GNSS change. A protocol fix alone is not RF acceptance.

### G4b: Kernel RF comparison

Compare existing MSS/SMEM/power lifetime against the working reference. Only after identifying a board-supported AP-owned rail/pin/clock difference, implement one narrowly scoped regulator/GPIO/PMIC change per RAM boot.

Never sweep rails, touch APSS-disallowed pins, or keep all proxy votes high.

**Gate:** repeatable positive C/N0/tracking, bounded start/stop/reset behavior and intact modem/Wi-Fi operation. If no ownership/mapping is established, this stage remains a research gate.

### G5: First-fix acceptance

Require:

- A fresh active-session/modem-generation LOC SUCCESS.
- Satellite-derived technology/source and validated nonempty used-SV evidence.
- Finite latitude/longitude in legal ranges.
- UTC.
- A **present, finite, nonnegative horizontal-uncertainty TLV below 50 metres**.
- Coordinates plausible against a known location, positive tracking evidence and continuing fixes for five minutes.

Do not gate on displayed accuracy alone: current code maps missing uncertainty to zero. [L3,L14]

Repeat after an OS reboot and record orbit validity, GNSSD cache/reinjection and starting EFS state. Compare TTFF with **injection enabled/withheld**; withholding a new upload is not an unaided cold start unless a documented RAM-only procedure actually removes existing aiding. [L4,L13]

Only then separately decide EFS persistence under the repository’s G4 rules. [L1,L6]

## Source register

Local paths use these prefixes:

| Prefix | Location |
|---|---|
| **N** | `neohw/` (NeoSymbian/neohw `208b878`) |
| **D** | `docs/` (this repository) |
| **K** | `kernel/` (NeoSymbian/kernel `6d34d8da`) |
| **P** | `private/` (unpublished captures) |

Local line numbers are from this research run. References such as `[A1:396–530]` identify source-file lines, not browser-renderer line numbers.

### Local evidence

- **L1:** `D/hardware/gnss.md` (2026-11-20 revision) phone results — owner results; first-fix gate at lines **86–93**.
- **L2:** `P/gnss/xtra-test-ring.txt:616–619,803–809`.
- **L3:** `N/crates/loc/src/proto.rs:58–114,157–191`.
- **L4:** `N/crates/loc/src/lib.rs:121–138,201–205,225–240,261–365`.
- **L5:** `N/symbian/hwhub/src/lib.rs:227–262`; `N/crates/hub/src/rmtfs.rs:25–31,92–145`.
- **L6:** `K/baseport/arm64/sdm670_assp/qcom_telhal.cpp:280–300`; `D/hardware/modem.md:31–35,293–307,855–862`; `N/crates/hub/src/locator.rs:17–23`.
- **L7:** `N/crates/hub/src/tftp.rs:72–113,258–310`; `N/crates/hub/src/lib.rs:568–580`.
- **L8:** `P/gnss/xtra-test-ring.txt:404–410,526–574`; `P/c1/captures-20261108-1846/tqftpserv.log:8–50`; `P/c1/captures-20261108-1846/mm.log:4169–4196,4262–4277,4356–4386,5332–5337`.
- **L9:** `P/c1/captures-20261108-1846/init.sh:2–3,27–35`; `D/hardware/modem.md:154–159`.
- **L10:** `K/baseport/arm64/sdm670_assp/qcom_mss.cpp:18–21,88–99,243–270,322–336`.
- **L11:** `D/hardware/tools/inspect-bonito.py:14–20,82–98`; private DTB node/property traversal described above, with no textual line numbers.
- **L12:** `K/baseport/arm64/sdm670_assp/qcom_rpmh.cpp:71–111,258–295,312–335`.
- **L13:** `N/symbian/gnssd/src/lib.rs:91–138,143–180`; `N/crates/loc/src/http.rs:11–27,48–91`. Cache lifetime/reinjection additionally at `gnssd/src/lib.rs:29–34,117–120,199–206`.
- **L14:** `N/crates/loc/src/lib.rs:370–405` — SUCCESS acceptance and absent-uncertainty default; `N/crates/loc/src/proto.rs:157–167` — position parsing.
- **Firmware strings:** `P/radio-backup/modem_a.img`, byte offsets listed in the NV table above. These are binary-string observations, not decoded NV values.

### Android and Qualcomm LOC

- **A1:** [AOSP Marlin `LocApiV02.cpp`, revision `2772c7e5d4b1e21dc0aad600d3acc84db0476145`](https://android.googlesource.com/device/google/marlin/+/2772c7e5d4b1e21dc0aad600d3acc84db0476145/location/loc_api/loc_api_v02/LocApiV02.cpp#396). Source lines **396–530, 585–656, 1044–1106, 2082–2125**. Older protocol implementation; exact Bonito binary provenance is not established.
- **A2:** [AOSP SDM710 `GnssAdapter.cpp`, revision `b3a9e8c564206ee2d177da4b4dca61c4a36a231a`](https://android.googlesource.com/platform/hardware/qcom/sdm710/gps/+/b3a9e8c564206ee2d177da4b4dca61c4a36a231a/sdm845/gnss/GnssAdapter.cpp#629). Source lines **629–702, 1327–1380, 2518–2564**.
- **Q1:** [libqmi LOC schema, lines 471–512](https://github.com/linux-mobile-broadband/libqmi/blob/1cad48593c8335b9b18992f97bf5320b110a112a/data/qmi-service-loc.json#L471-L512); [validity enums, lines 270–292](https://github.com/linux-mobile-broadband/libqmi/blob/1cad48593c8335b9b18992f97bf5320b110a112a/src/libqmi-glib/qmi-enums-loc.h#L270-L292); satellite-status enums in the same file, lines **343–356**.
- **Q2:** [Qualcomm LOC IDL in AOSP Marlin](https://android.googlesource.com/device/google/marlin/+/2772c7e5d4b1e21dc0aad600d3acc84db0476145/location/loc_api/loc_api_v02/location_service_v02.h#1291). Source lines **1291–1313** — SV status; **5073–5081, 5158–5163** — low power; **7613–7678** — sensor control; **12360–12384** — premium services; **12486–12523** — constellation reporting.
- **V1:** [Qualcomm-source `LBSProxy.cpp` mirror, lines 233–355](https://github.com/tadiphone-caf/vendor_qcom_proprietary/blob/9a79e3c6b709ced2c53befa46628395989d8892b/gps/framework/native/core/LBSProxy.cpp#L233-L355). Exact Bonito linkage remains unverified.

### Kernel, board and vendor configuration

- **K1:** [Lineage MSM4.9 SDM670 MSS DT, lines 2184–2245](https://github.com/LineageOS/android_kernel_google_msm-4.9/blob/df5cccf77f2a78959014d9b9206241a128691764/arch/arm64/boot/dts/qcom/sdm670.dtsi#L2184-L2245); [regulator DT, lines 55–65](https://github.com/LineageOS/android_kernel_google_msm-4.9/blob/df5cccf77f2a78959014d9b9206241a128691764/arch/arm64/boot/dts/qcom/sdm670-regulator.dtsi#L55-L65). Negative-search files use this same repository and pinned revision.
- **K2:** [Bonito PM660 exclusions, lines 145–160](https://github.com/LineageOS/android_kernel_google_msm-4.9/blob/df5cccf77f2a78959014d9b9206241a128691764/arch/arm64/boot/dts/google/sdm670-b4s4-common.dtsi#L145-L160); PM660L exclusions in the same file, lines **266–286**; [GPIO binding, lines 46–55](https://github.com/LineageOS/android_kernel_google_msm-4.9/blob/df5cccf77f2a78959014d9b9206241a128691764/Documentation/devicetree/bindings/pinctrl/qcom,pmic-gpio.txt#L46-L55).
- **K3:** [SDM670 pinmux, lines 1523–1526](https://github.com/LineageOS/android_kernel_google_msm-4.9/blob/df5cccf77f2a78959014d9b9206241a128691764/drivers/pinctrl/qcom/pinctrl-sdm670.c#L1523-L1526); additionally **1547–1550, 1573–1577**.
- **K4:** [Linux v6.17 PD mapper, lines 452–470](https://github.com/torvalds/linux/blob/v6.17/drivers/soc/qcom/qcom_pd_mapper.c#L452-L470), with root/GPS service definitions at **320–345**; [GNSS Kconfig, lines 15–72](https://github.com/torvalds/linux/blob/v6.17/drivers/gnss/Kconfig#L15-L72).
- **D1:** [Bonito `init.hardware.rc`, lines 171–192](https://github.com/LineageOS/android_device_google_bonito/blob/bde25fa67a06be65cdfac2f2e424fc5e7550f524/init.hardware.rc#L171-L192); additionally **596–605, 623–631**; [RFS init, lines 1–5](https://github.com/LineageOS/android_device_google_bonito/blob/bde25fa67a06be65cdfac2f2e424fc5e7550f524/init.hardware.mpssrfs.rc.user#L1-L5).
- **D2:** [Bonito `gps.conf`, lines 53–54](https://github.com/LineageOS/android_device_google_bonito/blob/bde25fa67a06be65cdfac2f2e424fc5e7550f524/gps.conf#L53-L54); additionally **13–16, 75–91, 99–104**; [AOSP version](https://android.googlesource.com/device/google/bonito/+/4e31cff4d47da6f7e49cd6640b2a516ea42ce32b/gps.conf#53).
- **D3:** [Bonito `init.radio.sh`, lines 17–37](https://github.com/LineageOS/android_device_google_bonito/blob/bde25fa67a06be65cdfac2f2e424fc5e7550f524/init.radio.sh#L17-L37).

### Linux userspace and device evidence

- **M1:** [ModemManager `mm-shared-qmi.c`, revision `2c0ecd73fc024f3f906a38b4490f31bee65b437e`, lines 6120–6213](https://github.com/linux-mobile-broadband/ModemManager/blob/2c0ecd73fc024f3f906a38b4490f31bee65b437e/src/mm-shared-qmi.c#L6120-L6213); additionally **5800–5843, 7044–7073**.
- **W1:** [Maemo Leste Pixel 3a GPS section](https://leste.maemo.org/Google_Pixel_3a#GPS_with_ModemManager_and_Geoclue_(testing,_not_implemented_yet,_WIP)); page identifies revision **3297**, last edited **2026-11-09**. Rendered web lines **16, 36, 54–55, 248–279, 311**. The wiki has no repository source-line addressing.
- **T1:** [linux-msm tqftpserv `translate.c`, revision `eb4b9a04ff92d2753ededf32cc3b6ed287f6e29b`, lines 172–200](https://github.com/linux-msm/tqftpserv/blob/eb4b9a04ff92d2753ededf32cc3b6ed287f6e29b/translate.c#L172-L200); additionally **255–275**.
- **T2:** [linux-msm rmtfs `storage.c`, lines 242–277](https://github.com/linux-msm/rmtfs/blob/master/storage.c#L242-L277), partition mapping at **39–43**. Inspected blob: `ee9d52676295b6b140b69b9c3fd7dbbfe000aa1d`; the linked `master` branch can move.

### Unavailable research endpoints

- [postmarketOS sargo/bonito wiki](https://wiki.postmarketos.org/wiki/Google_Pixel_3a_(google-sargo))
- [postmarketOS OnePlus 6 wiki](https://wiki.postmarketos.org/wiki/OnePlus_6_(oneplus-enchilada))
- [pmaports MR7636](https://gitlab.postmarketos.org/postmarketOS/pmaports/-/merge_requests/7636)

No line-addressable content was obtained from these endpoints; no acceptance claim relies on them. Candidate raw pmaports paths were not verified to exist.

## Verification record

Read-only inspection comprised numbered local source reads and targeted `grep -anE` on named logs, private DTB parsing in memory, firmware-string searches in memory, and public web/GitHub source reads. No private DTB or firmware file was copied or exported; only the configuration facts and path strings above were retained.

Baselines:

- Kernel: `6d34d8dafce78793e680f7fad7287dbe67e6ae20`
- LOC checkout: `208b8780919d89d5380eb305d9cbfbc8f0218322`

Kernel and LOC `git status --short` returned clean, **exit 0**. No runtime/test success is claimed: phone operations, builds and code tests were intentionally not run.

The initial `rg` lookup exited **127** because the tool was unavailable; targeted grep replaced it. A shell web fetch exited **1** because DNS was restricted; connected web/GitHub tools supplied external evidence. Inaccessible sources remain verification gaps.

Independent review covered the supplied draft claims and local evidence. Accepted corrections strengthened C/N0 validity, fix validation and assistance-state gates. No remaining blocking issue was reported within that scope. All external references were not independently rechecked.

