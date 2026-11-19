<!-- SPDX-License-Identifier: Apache-2.0 -->
# Hardware and drivers

The hub for everything that drives the phone's hardware. Target: **Pixel 3a XL (bonito, SDM670)**; the Pixel 3a
(sargo) shares the SoC ([devices](#devices-where-neosymbian-can-go-next)). Each driver has two halves:
- **kernel** (C++, `kernel/baseport/arm64`: `sdm670_assp/` for the SoC, `bonito_variant/` for the board): MMIO,
  interrupts, DMA and buffer lifetime, exposed to the user side through HAL functions (`EHalGroupVariant`, 0x4exx);
- **user side** (Rust, [NeoSymbian/neohw](https://github.com/NeoSymbian/neohw)): the protocols and the policy, as
  daemons with IPC servers that apps and neoui talk to.

`neohw` was `telephony` until 2026-11-18, when it was renamed and `neolink` (Wi-Fi, Bluetooth) was merged into it.

**Details:**

| Document | Covers | Stages |
|---|---|---|
| [hardware/modem.md](hardware/modem.md) | The cellular modem: QRTR, QMI, rmtfs, calls, SMS, data | C0–C12 |
| [hardware/audio.md](hardware/audio.md) | NeoAudio, media/recording on the ADSP, the jack, the old apps' DevSound | A0–A8 |
| [hardware/wifi.md](hardware/wifi.md) | WCN3990 Wi-Fi: firmware, copy engines, WPA2, NEONET (IP) | W0–W7 |
| [hardware/bluetooth.md](hardware/bluetooth.md) | Bluetooth: the Rust host stack and the 2010 facade (design) | B0– |
| [hardware/battery.md](hardware/battery.md) | PM660 battery and thermal telemetry | D2 |
| [hardware/verification/](hardware/verification/) | Run records: [driver support](hardware/verification/driver-support-2026-11-10.md), [TSENS](hardware/verification/tsens-2026-11-10.md), [battery](hardware/verification/battery-2026-11-11.md) | |

Also: [debug-access.md](debug-access.md) (USB console and monitor), [filesystem.md](filesystem.md) (eMMC, A/B),
[known-issues.md](known-issues.md), [roadmap.md](roadmap.md) track H.

## Driver status

"Phone" = last verified on the Pixel. HAL numbers are `EHalGroupVariant` functions; `telhal` =
`sdm670_assp/qcom_telhal.cpp`, `bv/` = `bonito_variant/specific/`.

| Driver | Kernel | HAL | User side (neohw unless named) | Status | Phone |
|---|---|---|---|---|---|
| CPU, GIC, timer, cpufreq | `arm64` port, `qcom_cpufreq.cpp` | 0x4e19 device list | — | 8 cores, GICv3, virtual timer | 2026-11-10 |
| Storage | `qcom_sdhci.cpp`, `qcom_fat16.cpp`, `qcom_bootctrl.cpp` | 0x4e09 slot info | — | eMMC, C:/E:, ROFS, A/B slots | installed |
| Display | `qcom_dsi.cpp`, `bv/panel_sofef00.cpp` | display HAL | neoui (`screen.rs`) | ABL framebuffer; brightness, on/off ([below](#d2-display-brightness-screen-off-wake-done-2026-11-11)) | 2026-11-11 |
| Touch, keys | `bv/a64_touch.cpp` (RMI4), `bv/a64_keys.cpp` (PMIC) | — | neoui | 5 fingers; power/volume keys | 2026-11-17 |
| Battery, TSENS | `qcom_battery.cpp`, `qcom_tsens.cpp`, `qcom_spmi.cpp` | 0x4e1a | neoui (status bar, Settings, Dev tools) | read-only telemetry; no charger control | 2026-11-11 |
| Haptics | `bv/a64_haptics.cpp` | 0x4e27 | MODEMD (ring, SMS), neoui | bounded pulses | yes |
| USB debug | `qcom_dwc3.cpp`, `qcom_usbpower.cpp` | 0x4e04/05 | neoui (`usb_debug.rs`) | console on RAM boots; cold-boot power open | RAM boots |
| Modem (MSS) | `qcom_mss.cpp`, `qcom_pas.cpp`, `qcom_glink.cpp`, `qcom_smp2p.cpp`, `qcom_ipa.cpp`, telhal | 0x4e0d–0x4e13, 0x4e24/25 | HWHUB (boot, QRTR, recovery) + MODEMD (cellular) ([modem.md](hardware/modem.md)) | calls, SMS, call log, recovery | 2026-11-18 |
| ADSP, audio | `qcom_adsp.cpp`, `bv/a64_audio.cpp` (CS35L36 ×2, RT5514), telhal AudioMem | 0x4e14–0x4e18, 0x4e26 | AUDIOD: NeoAudio (MODEMD drives calls/ring over op::CONTROL) ([audio.md](hardware/audio.md)) | call audio, media, recording, routes, amp protection | 2026-11-18 |
| 3.5 mm jack | `bv/a64_jack.cpp` (PM660L/SDM660 codec) | 0x4e18 ops 8–10 | AUDIOD | driver idle-tested; headphones/headset mic untested with a plug | 2026-11-18 |
| Wi-Fi | `qcom_wcn3990.cpp` (SNOC copy engines, HTC/WMI/HTT) | 0x4e1b–0x4e1f, 0x4e23 PRNG | WIFID (firmware over NeoHub, joining, WPA2, remembered networks) + NEONET (IP) ([wifi.md](hardware/wifi.md)) | scan, WPA2, DHCP, TCP/UDP | 2026-11-18 |
| Bluetooth | — (GENI UART + HCI LDD planned) | — | BTSRV planned ([bluetooth.md](hardware/bluetooth.md)) | design | — |
| Sensors | — (ADSP sensor PD via FastRPC) | — | — | not started (D4) | — |
| Cameras | — (IMX355 front, IMX363 rear; CCI/CAMSS) | — | — | not started (D5) | — |
| GNSS | — (QMI LOC on the modem) | — | MODEMD later | not started (D6) | — |
| NFC, fingerprint | — (NXP NCI I2C 0x28; FPC) | — | — | not started (D7) | — |

## neohw: the processes and their IPC

The user side of the hardware is a set of daemons, one per driver area, built from host-tested crates (`no_std`
+ `alloc`, Apache-2.0) in `neohw/crates/` and composed into EXEs in `neohw/symbian/`.

| EXE | UID3 | Owns | Serves |
|---|---|---|---|
| `HWHUB.EXE` | 0xE0003002 | the QRTR receive rings (MSS, ADSP ring 1) and the router; rmtfs, TFTP, the locator, SSCTL, IPA; MSS + ADSP boot and recovery; starts the others | NeoHub |
| `MODEMD.EXE` | 0xE0003001 | the cellular QMI clients: calls, SMS, call log, blocklist; haptic alerts | NeoModem (`modem-ipc`) |
| `AUDIOD.EXE` | 0xE0003003 | APR (ADSP ring 2), AudioMem, the mixer, routes, amps, the jack, the call voice path | NeoAudio (`neoaudio`) |
| `WIFID.EXE` | 0xE0004002 | the Wi-Fi firmware (WLFW over NeoHub), MSA, board data, scan, join, the WPA2 supplicant, saved networks | NeoWifi (`wifi-ipc`) |
| `NEONET.EXE` | 0xE0004001 | the IP stack (smoltcp) on the Wi-Fi link | NeoNet (`net`) |

```
 neoui / apps / legacy DevSound
   |NeoModem      |NeoAudio        |NeoWifi        |NeoNet
 MODEMD ----call, ring, DTMF----> AUDIOD          WIFID ---starts---> NEONET
   |NeoHub                         | APR ring 2     |NeoHub             | WlanLink frames
 HWHUB (QRTR router, MSS/ADSP boot, recovery) <------+                   |
   | MSS + ADSP QRTR rings, rmtfs, PAS                                   |
 kernel: qcom_telhal, qcom_mss, qcom_adsp, qcom_glink, a64_audio, qcom_wcn3990
```

**Rules:**
- **One reader per kernel ring.** The kernel's receive rings pop packets for whoever reads first
  (`qcom_telhal.cpp`), so HWHUB alone reads the QRTR rings and AUDIOD alone reads APR.
- **NeoHub** is QRTR over IPC: a client BINDs the services it wants and gets ports; SEND; an asynchronous RECV
  delivers its packets, NEW/DEL_SERVER and `RESET{subsystem, generation}`; a client answers a reset with QUIESCED.
  Each client's queue is bounded (64 packets; the oldest goes, logged), so a slow client cannot stall the hub.
- **Recovery** is coordinated by HWHUB: RESET to every client, QUIESCED (or 2 s), stop/restart, BIND again.
  An MSS stop invalidates the Wi-Fi firmware; an ADSP stop clears AudioMem.
- **PCM never crosses IPC:** it stays in AUDIOD (APR + AudioMem). MODEMD sends AUDIOD intents (call state, ring,
  DTMF, SMS chime) and mirrors AUDIOD's status into NeoModem.
- **Boot:** SYSSTART starts MODEMD and WIFID. MODEMD starts HWHUB and AUDIOD; WIFID starts NEONET. HWHUB probes: no
  modem (Syborg) → "no hardware", AUDIOD plays on its clock sink. On the phone HWHUB loads the ADSP, then boots the
  MSS once IPA and the EFS are ready; MODEMD and WIFID connect to NeoHub and wait for their services.
- **Contracts keep their names:** `modem-ipc`, `neoaudio`, `phone-rules`, `sms`, `net`, `wpa` are pinned by neoui
  and phone; their package names stay.

Stages (neohw PRs; S4/S5 with neoui #21):

| Stage | Work | Status |
|---|---|---|
| S0 | `telephony` renamed `neohw`; these docs centralised | done 2026-11-18 |
| S1 | `neolink` merged into neohw with its history; one host and one Symbian workspace | done 2026-11-18 (neohw#4) |
| S2 | modem-proto split into `qrtr`, `hub`, `modem`, `apr` crates and `symbian/sys`; a `Bus` between router and cellular (still one MODEMD.EXE) | done 2026-11-18 (neohw#5), phone: registers, Wi-Fi |
| S3 | HWHUB.EXE and NeoHub; MODEMD a NeoHub client | done 2026-11-18 (neohw#6), phone: boot, registration over NeoHub, Wi-Fi |
| S4 | AUDIOD.EXE; MODEMD → AUDIOD over NeoAudio op::CONTROL | 2026-11-18 (neohw#7), phone: media on the DSP; a call's voice path not exercised yet |
| S5 | WIFID.EXE; the supplicant moves out of neoui's SYSSTART (NeoWifi) | 2026-11-18 (neohw#8, neoui#21), phone: firmware, auto-join of the remembered network, DHCP, internet |
| S6 | ROM recipe (`neohw/symbian/exes.txt`: MODEMD, HWHUB, AUDIOD, NEONET, WIFID), results here | 2026-11-18 |

## Program D0–D8 (accepted 2026-11-10)

Native Rust apps first, legacy Symbian adapters later, without changing EKA2's AArch64 ILP32 kernel or the ARMv5TE
soft-float user ABI.

### Evidence

Reviewed baseline: kernel `326fffcd`, telephony `54a8114`, neoui `ed9202f`, docs
`7f926e7`. The build lock still names kernel `2692bea`: a source checkout and an
installed image are separate baselines. Re-pin only the deliberately selected,
validated candidate, preserving other sessions' changes.

The private DTB SHA-256 is
`131c8d50af0aef16be883038198e94502261af1769f0dccab58e8105d473825f`.
It is configuration evidence, not physical chip identification. Generate a
sanitized report without dumping firmware, calibration or device identifiers:

```sh
python3 docs/tools/inspect-bonito.py private/bonito.dtb
```

Run that command from the workspace root. The report lists only selected public
compatible strings and effective enabled state (including disabled ancestors).
An enabled node does **not** establish a working NeoSymbian driver. Missing nodes
do not prove hardware absence. Keep full DTBs and firmware under `private/`.

The inventory as reviewed on 2026-11-10 (DTB evidence for the hardware not started yet):

| Subsystem | Evidence / existing implementation | Remaining work |
|---|---|---|
| CPU, interrupt, timer | Eight-core boot recorded; GICv3, virtual timer | Focused timer/wake correctness before deep suspend |
| Storage | eMMC, persistent C:/E:, ROFS and A/B recorded | Preserve partition allow-list and recovery gates |
| Display/input | Bootloader OLED framebuffer, Synaptics RMI4 touch, PMIC keys; panel brightness and on/off, touch sleep, screen timeout and power key (2026-11-11, below) | Independent panel initialization, IRQ/wake from suspend |
| PMIC/power | SPMI, RPMh, RTC and reboot code | Fuel gauge (`qcom,pmi8998-fg`), PM660 RRADC, charger, TSENS, policy |
| USB | DWC3 debug console on RAM boots | Cold/installed-boot power remains open; see known-issues |
| Audio | ADSP, dual CS35L36 amps, RT5514 mic; C6 two-way calls; NeoAudio (2026-11-18, [audio.md](hardware/audio.md)): ASM/ADM PCM playback and recording, routes, amp protection polling, the 3.5 mm jack driver | ACDB calibration, headset-mic recording path, audible QEMU |
| Haptics | DTB TI DRV2624, I2C10 `0x5a`, reset GPIO24 | Driver, verified supplies/actuator configuration, bounded pulse; PM660 haptics disabled |
| Sensors | ADSP FastRPC transport described; sensor GPIO ownership reserved | Discover exact chips, firmware sensor protocol and calibration requirements |
| Front camera | DTB Sony IMX355, CCI1 `0x1a`, MCLK2 19.2 MHz, reset GPIO9 | CCI/CAMSS/DMA and software image processing |
| Rear camera | DTB Sony IMX363, CCI0 `0x1a`, MCLK0 24 MHz, reset GPIO127; LC898219XI focus actuator | Separately pinned downstream mode/calibration evidence, capture and focus |
| Wi-Fi | DTB WCN3990 enabled at `0x18800000` | QMI firmware control plus SNOC copy engines and full packet/protocol path |
| Bluetooth | DTB WCN3990 UART transport; design in [bluetooth.md](hardware/bluetooth.md) | GENI UART/HCI, firmware, IBS sleep, BLE and audio profiles |
| GNSS | Qualcomm modem; QMI LOC is a protocol reference | Discover live service, standalone fixes and typed location API |
| NFC | DTB NXP NCI I2C `0x28`; AOSP NXP configuration | Verify chip/firmware, NCI and tag reading |
| Fingerprint | Google FPC service configuration | Verify exact sensor and secure enrollment/matching interface; PIN fallback |

Prior feature results above remain historical implementation-note evidence;
checks repeated in this change are identified in the verification record. Sensor and camera entries in Dev tools were catalogue
placeholders, not linked working drivers.

### Integration contracts

- Kernel C++ owns MMIO, interrupt/DFC execution, DMA mappings and buffer lifetime.
  Rust owns protocols and policy. Retain static linking and SoC/board ownership;
  avoid a tree-wide framework rewrite as a prerequisite.
- Initialize buses explicitly before their consumers. Aggregate clock/regulator
  and bandwidth votes; a consumer must not power off a resource another needs.
- Use bounded lifecycle operations: probe, initialize, run, stop, failed/retry.
  Partial initialization unwinds; optional-device failures leave shell/storage usable.
- Streaming uses asynchronous logical channels and shared chunks. Fixed-width
  fields, chunk handles/offsets and checked stride/length arithmetic cross the ABI;
  arbitrary physical addresses do not. Complete requests on cancel/client death/fault.
- Add separate device DMA/SMMU contexts and cache/barrier contracts. Existing IPA
  low-4-GiB identity mapping is **not** a camera or FastRPC buffer API. Do not reuse
  memory until DMA has stopped or completion is acknowledged.
- The allocator currently exposes one bank ending at `0x85700000`, not all 4 GB.
  Budget DMA rings, RAW conversion, preview and JPEG together against measured
  free/contiguous RAM. Cleanly reject OOM; never increase RAM_END across carve-outs.
- The ring owners are in [neohw: the processes](#neohw-the-processes-and-their-ipc). Originally MODEMD owned APR and ADSP QRTR exclusively. Independent ADSP/radio
  state machines must pump even after radio failure; support-only routing must
  never advertise dummy RMTFS memory. Use fixed deadlines and bounded work under
  IPC load. AUDIOD extraction (S4) waits until this passes phone regressions.
- Versioned native IPC: audio configure/queue/reclaim/start/stop/route/focus;
  sensors enumerate/subscribe/timestamped samples/calibration/drops; camera
  exclusive session/modes/queue/dequeue/controls/capture; power/network/location
  subscriptions. Enforce capabilities at the service and kernel boundaries.
- Report actual readiness through the existing device registry: absent, off,
  starting, ok, partial or error. DSP boot or driver linkage alone is not readiness.

### Milestones and gates

| Stage | Work | Acceptance |
|---|---|---|
| D0 inventory | Sanitized DTB inspection, reconcile roadmap, pin reference/firmware provenance; probe exact silicon before using it | Reproducible report plus explicit unknowns; no public firmware/calibration |
| D1 foundations | Explicit bus startup, validated bus requests; resource votes, async streams and per-device DMA follow | Existing call/storage/input regressions pass; cancellation and OOM bounded |
| D2 power | Read-only TSENS telemetry phone-tested (21/21 valid; Dev tools display and check verified); fuel gauge/RRADC, charging telemetry and conservative policy; OLED brightness/blanking and input wake; cold USB | Compared telemetry, thermal shutdown and cold-boot logs; power baseline |
| D3 audio/haptics | Independent audio lifecycle; conservative amplifier gain and fault mute; ASM/ADM 48 kHz S16 playback and mono capture; typed audio service; DRV2624; 3.5 mm jack later | Tone/WAV playback, recorded WAV, ringtone→call, volume/mute/routes; audio with no SIM/radio off and radio failures; bounded vibration |
| D4 sensors | Sensor PD/FastRPC/reverse file service; discover actual sensor protocol; proximity/light→accel/gyro→compass/barometer→batching/fusion | Six-orientation gravity, gyro zero/motion, call proximity/light transitions, calibrated units/timestamps and wake |
| D5 cameras | CAMCC/power/CCI/CAMSS/isolated DMA; ID→testgen→sensor pattern→scene; IMX355 first, IMX363/focus next | Reduced preview >=10 fps and recognizable persistent JPEG, correct format/orientation, bounded RAM/latency, no SMMU faults |
| D6 connectivity | Wi-Fi: [wifi.md](hardware/wifi.md) (Symbian WLAN stack over an ath10k-derived WHA driver, decided 2026-11-12); WCN3990 SNOC/CE DMA, QMI and HTC/WMI/HTT, WPA2-PSK and ESOCK/TCPIP6 NIF coordinated with C10; Bluetooth: [bluetooth.md](hardware/bluetooth.md) (a new Rust host stack + a 2010-compatible facade, decided 2026-11-15); BT UART/HCI/IBS and BLE→A2DP/HFP; QMI LOC | Wi-Fi scan/auth/IP/traffic, BT pairing/GATT/audio routing, outdoor standalone fix; coexistence and idle-power evidence |
| D7 remaining hardware | NXP NCI/tag read; secure fingerprint feasibility→enrollment/matching; bounded torch | Tag events and thermal limits; fingerprint remains unsupported if secure path unavailable |
| D8 system acceptance | Coordinated quiescence, timer accounting, wake sources/resume; legacy framework adapters after native acceptance | Repeated suspend/resume, overnight idle and recorded 24-hour mixed-use run; measured results, not a battery-life promise |

D0 precedes hardware programming; D1's required contracts precede each consumer.
Power telemetry/haptics can overlap audio after shared-bus ownership is established.
Cameras and connectivity can proceed independently after their DMA foundations.
Hardware-specific discoveries are gates, not guesses delegated to driver authors.

First camera processing is software: RAW unpacking, black level, Bayer demosaic,
white balance/exposure, orientation and JPEG. Select a documented reduced sensor
mode against the D1 memory budget, and record its dimensions, stride, buffers and
latency before implementation. RAW/test patterns alone do not close D5. Full
resolution, video, HDR, OIS, GPU acceleration and payments are follow-up programs.

### Verification and implementation record

Keep run records under `private/driver-support/<run-id>/`: exact commands/status,
source/diff identity, toolchain/image digest, DTB/firmware hashes, image and ELF,
serial logs, test counts and measured data. Never publish private identifiers.

Host tests cover malformed protocols, deadlines/backpressure, ownership, radio
failure, cancellation and late responses. Kernel/QEMU checks cover bounds,
permissions, cache/lifetime contracts, OOM and process death. Require completion
markers and zero failure counts. QEMU cannot validate Qualcomm registers or DMA.

Phone gates use recoverable RAM boots before installed images. Regress C6's mic
before voice / speaker after START_VOICE sequencing and teardown at END. Exercise
media→call→media, recording→call, camera during calls, haptics sharing I2C, DSP
failure and late completions. Preserve working debug/recovery paths and update
source pins only for a selected tested candidate.

The first implementation tranche adds explicit SPMI startup/readiness and bus
argument validation, a support-only ADSP router with later radio-storage attachment,
independent daemon servicing after radio failure, and fixed polling deadlines.
`radio-disabled` is a MODEMD build feature for startup testing, not a runtime
airplane-mode setting. There is no new PCM service or sensor/camera driver yet.
Synchronous firmware/storage HAL calls can still delay polling: the deadline helper
fixes starvation by unrelated IPC, not hard real-time behavior.

Implementation status is intentionally split: documentation/inventory tooling can
be complete while hardware probes and the later milestones remain pending. See
[the implementation verification record](hardware/verification/driver-support-2026-11-10.md)
for the initial foundation commands and limitations. The subsequent read-only
TSENS addition has a [separate verification record](hardware/verification/tsens-2026-11-10.md).

The subsequent [battery telemetry implementation](hardware/battery.md) includes
live status-bar/Settings/Dev tools and retained history; physical acceptance is
tracked separately in its verification record.

### D2 display: brightness, screen off, wake (done 2026-11-11)

Phone-tested in RAM boots (kernel #13, neoui #6; evidence in `private/display/`):
- **What ABL leaves:** DSI0 (`0xae94000`, 6G v2.2; controller registers at +4) in **command mode**, 4 lanes, with
  the DPU pushing the splash framebuffer and command DMA from memory, low power, a software trigger.
- **Panel commands:** `qcom_dsi.cpp` sends DCS writes through that DMA from **ABL's own packet page `0x9a027000`**.
  The DMA reads through the SMMU (stream 0x880); a page in the framebuffer region (`0x9c8f0000`) was not reachable:
  the commands completed with no effect.
- **Panel:** `panel_sofef00.cpp` (DTB `samsung,sofef00-bonito`): brightness DCS `0x51`, 16 bits, 0..1023; off
  `0x28` + `0x10`; on `0x11` + `0x29`. The supplies and reset stay ABL's.
- **Kernel interface:** Symbian's display HAL: `EDisplayHalMax/Set/DisplayBrightness` and `EDisplayHalSetState`
  (a mutex serialises them). The monitor's `panel on|off|bright N`. While off, the touchscreen sleeps (RMI4 F01
  sensor sleep, no polling).
- **neoui:**
  - `display.brightness` (0..255) is scaled to the panel;
  - `display.timeout` (default 60 s, 0 = never; no timeout without a panel);
  - a short Power press toggles the screen, and a 1-s hold is the Power menu;
  - Power or a ringing call wakes it, and a tap doesn't;
  - nothing is drawn while dark.
- **Never read the SMMU's S2CR table (`0x15000c00`) from the monitor:** it hangs the phone.
- **Not done:** wake on a call not phone-tested; no suspend (H3); tearing (no TE/vsync; smooth-ui S5).

### Primary hardware references

Read for register/protocol facts; preserve the project's licence boundaries:

- [Linux Google SDM670 device tree](https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/sdm670-google-common.dtsi): front camera and supplies; does not establish rear support.
- [IMX355 reference](https://raw.githubusercontent.com/torvalds/linux/master/drivers/media/i2c/imx355.c).
- [Google camera wiring](https://android.googlesource.com/kernel/msm/+/b9d5f1970a0e0a6482250f2e076dd7f6c192e566/arch/arm64/boot/dts/google/sdm670-camera-sensor-v2.dtsi).
- [HexagonRPC](https://github.com/linux-msm/hexagonrpc): FastRPC/reverse file service.
- [WCN3990 SNOC](https://raw.githubusercontent.com/torvalds/linux/master/drivers/net/wireless/ath/ath10k/snoc.c), [Bluetooth HCI/IBS](https://raw.githubusercontent.com/torvalds/linux/master/drivers/bluetooth/hci_qca.c).
- [QMI LOC definitions](https://raw.githubusercontent.com/linux-mobile-broadband/libqmi/main/data/qmi-service-loc.json).
- [Google device configuration](https://android.googlesource.com/device/google/bonito/+/refs/heads/main/device.mk), [hardware diagram](https://support.google.com/pixelphone/answer/7157629?hl=en).

## Devices: where NeoSymbian can go next

(Moved here from `devices.md`, 2026-11-19.)

**Status: shortlist (2026-11-09). Ported: the Pixel 3a XL (bonito), and since 2026-11-16 the Pixel 3a (sargo), contributed by idkmaybedeveloper (kernel #18, build #28).** This page lists phones from the mobile
Linux device lists that NeoSymbian could boot on. They are phones with an unlockable (or no) bootloader, and with
mainline Linux support to read for register layouts. Each entry says what our port already covers and what would be
new.

### What a NeoSymbian phone needs

These come from the port's fixed decisions ([roadmap.md](roadmap.md), [port-map.md](port-map.md)):

| Need | Why | Effect on the list |
|---|---|---|
| **AArch64 cores that also run 32-bit code at EL0** | The 2010 user side runs unchanged as ARMv5TE code at AArch32 EL0 | Cortex-A53/A55/A72–A78 qualify. **Cortex-X2 and later, A715/A720 and A520 are AArch64-only** (most SoCs from 2022 on), so they are out |
| **A bootloader we can unlock**, or none at all | We boot our own `boot.img` (`fastboot boot` / `flash boot_x`) | Carrier-locked models are out (Verizon Pixels). Xiaomi makes you wait; Fairphone may need a code |
| **Mainline Linux support** | Mainline drivers and device trees are our register reference (read only, never copied) | The phone should be in Nura's `community` category, or in `testing` with a working device tree |
| GICv3 interrupt controller | `nkernsmp/arm64` implements GICv3 only | GICv2 phones (Allwinner A64) need a new interrupt back end first |
| Storage we can drive | `sdm670_assp` has SDHCI-msm (eMMC) | UFS phones need a new UFS host driver (UFSHC + its PHY) before `C:` and `Z:` work |
| A modem we can talk to | `neohw` speaks QMI over QRTR/GLINK (Qualcomm) | Qualcomm phones reuse it; a Quectel EG25 phone needs an AT-command path instead |

### Sources and how this was checked (2026-11-09)

- **Nura**, formerly postmarketOS: the project renamed itself in September 2026 ([announcement](https://nura.eco/blog/2026/09/27/nura-rename/)); `wiki.postmarketos.org` and `gitlab.postmarketos.org` now redirect to `*.nura.eco`.
  - The **category** and the **device tree name** (which names the SoC) of each phone below are taken from `pmaports`
    (`device/<category>/device-<codename>/deviceinfo`), read through the GitLab API at `gitlab.nura.eco` on
    2026-11-09.
  - The wiki pages (`wiki.nura.eco`) block automated readers, so per-device feature tables (calls, SMS, data, Wi-Fi)
    have **not** been read. Check them in a browser before choosing a device.
- **Ubuntu Touch** progress figures are from https://devices.ubuntu-touch.io on 2026-11-09. Most Ubuntu Touch ports
  run on Android kernels (Halium), not mainline, so a high figure says the hardware is well understood, not that
  mainline drivers exist. The PinePhones are the exception: they run native.
- **Fairphone unlock rules:** from https://www.fairphone.com/bootloader-unlocking-code-for-fairphone, which disagrees
  with the shop version of that page (details in the FP5 row).
- **Unverified:** CPU core types, storage type (UFS or eMMC), RAM and the modem are taken from public spec sheets as
  remembered, not checked today. Check each against the device tree (`ufshc@`/`sdhci@`, `cpu@` `compatible`)
  before porting.

### The shortlist

#### Same SoC as ours

| Phone (codename) | SoC, cores | Nura | UT | Bootloader | Reuse | New work |
|---|---|---|---|---|---|---|
| **Google Pixel 3a (sargo)** | SDM670 (`qcom/sdm670-google-sargo`), Kryo 360 = A75 + A55 | community | 97.3% | Unlockable (`fastboot flashing unlock`), except Verizon | `sdm670_assp` entirely, the modem firmware layout and the whole `neohw` stack | **Ported 2026-11-16** (kernel #18): `sargo_variant` = its board file (1080 x 2220 framebuffer, I/O map) and the Samsung S6E3FA7 OLED panel; every other driver is bonito's (touch, keys, haptics with sargo's clamp 0x5d, audio, eMMC, USB, modem). Builds with `neo kernel sargo` and the phone's own DTB. Not yet run on a sargo by the main streams: what works there is unconfirmed |

#### SDM845 family (2018–2020): our closest relatives

Our docs already use the Linux sdm845 drivers as a reference (`gcc-sdm845.c`, the `sdm845_mss` modem flow, IPA
v3.5.1). All of these have **UFS** storage (unverified), so a UFS driver is the main cost of the whole family.

| Phone (codename) | SoC | Nura | UT | Bootloader | Notes |
|---|---|---|---|---|---|
| **OnePlus 6 (enchilada)** | SDM845 (`qcom/sdm845-oneplus-enchilada`), A75 + A55 | community | 93.8% | `fastboot oem unlock`, no wait | Best-supported SDM845 phone in mainline Linux. Cheap used |
| **OnePlus 6T (fajita)** | SDM845 (`qcom/sdm845-oneplus-fajita`) | community | 93.8% | As OnePlus 6 | Same board as the 6 with a different panel and an optical fingerprint reader. One port covers both |
| **Xiaomi Poco F1 (beryllium)** | SDM845 | community | 91.2% | Xiaomi Mi Unlock: account binding and a waiting period | Two panel variants (Tianma, EBBG) |
| **SHIFT6mq (axolotl)** | SDM845 (`qcom/sdm845-shift-axolotl`) | community | 82.1% | Unlockable | Small maker, fewer units around |
| **Google Pixel 3 (blueline)** | SDM845 (`qcom/sdm845-google-blueline`) | testing | — | Unlockable, except Verizon | Mainline support behind the OnePlus 6 |

#### Newer Qualcomm (2020–2024): still AArch32-capable

| Phone (codename) | SoC | Nura | UT | Bootloader | Notes |
|---|---|---|---|---|---|
| **Fairphone 4 (fp4)** | SM7225 (`qcom/sm7225-fairphone-fp4`), A76 + A55 | community | 97.3% | Official; may need a Fairphone code (see FP5) | Repairable, long support. UFS; newer clock and power blocks |
| **Fairphone 5 (fp5)** | QCM6490 (`qcom/qcm6490-fairphone-fp5`), A78 + A55 | testing | 97.4% | Official. Fairphone is dropping the unlock code ("enable it in Developer options"), but the shop page still offers codes for FP4/FP5 and says the change so far covers the FP3 only. **Has anti-rollback: never relock with our image** | The best long-term daily phone. UFS. Shares QCM6490 with the SHIFTphone 8 |
| **SHIFTphone 8 (otter)** | QCM6490 (`qcom/qcm6490-shift-otter`) | testing | — | Unlockable | Same SoC as the FP5: one `qcm6490_assp` would serve both |
| **Nothing Phone (1) (spacewar)** | SM7325 (`qcom/sm7325-nothing-spacewar`), A78 + A55 | testing | 95.6% | Unlockable | A close relative of the QCM6490 (both are Kodiak/SC7280 family) |
| **OnePlus 8T (kebab), 8 Pro (instantnoodlep)** | SM8250, A77 + A55 | testing | — | Unlockable | Flagship-class SoC; more blocks to bring up |

#### Open by default (no bootloader lock at all)

| Phone (codename) | SoC | Nura | UT | Reuse | New work |
|---|---|---|---|---|---|
| **PinePhone Pro (pinephonepro)** | RK3399 (`rockchip/rk3399-pinephone-pro`), A72 + A53 | community | 69% (native) | GICv3 (GIC-500); eMMC on a standard SDHCI (Arasan), so the generic parts of our SDHCI code carry over | A new `rk3399_assp` (clocks, I2C, display). The **Quectel EG25-G** modem is driven by AT commands (unverified: over UART and USB), not QMI |
| **PinePhone (pinephone)** | Allwinner A64 (`allwinner/sun50i-a64-pinephone-1.x`), A53 | **testing** (was main) | 67.3% (native) | Phorepoc already has an A64 board bootstrap (`os/src/phorepoc-arm/a64/bootstrap`, [sources.md](sources.md)) | **GICv2 (GIC-400)**: a new interrupt back end; a slow CPU; 2–3 GB RAM; EG25-G modem |
| **Purism Librem 5 (librem5)** | i.MX8MQ (`freescale/imx8mq-librem5-r2..r4`), A53 | community | — | GICv3; eMMC (uSDHC) | A new SoC; slow; expensive; the modem is a plug-in M.2 card |

### Out, and why

- **Fairphone (Gen. 6)** (`qcom/milos-fairphone-fp6`, Nura testing): its Snapdragon 7s Gen 3 has Cortex-A720 + A520
  cores, which are AArch64-only (unverified), so the 32-bit user side can't run.
- **Most phones from 2022 on** (Snapdragon 8 Gen 1 and later, Dimensity 9000 and later): the big cores, and often all
  cores, are AArch64-only. A big.LITTLE phone with some 32-bit-capable cores would need the scheduler to keep every
  user thread on them; that isn't worth it.
- **MediaTek and Exynos phones:** mainline Linux support is thin, so there is little register reference to read.
  Ubuntu Touch runs them on Android kernels.
- **Carrier-locked models** (Verizon Pixels, many US OnePlus carrier units): the bootloader can't be unlocked.

### Recommendation

1. **Pixel 3a (sargo):** a second board for almost no work. It proves that the board/SoC split in
   `kernel/baseport/arm64` holds and gives us a cheap spare test phone.
2. **OnePlus 6 / 6T:** the second SoC (`sdm845_assp`). Build the **UFS driver** here; it then serves every later
   Qualcomm phone. `neohw` carries over mostly unchanged.
3. **Fairphone 5** (or SHIFTphone 8, same SoC): the long-term daily phone. It reuses the UFS driver and the QMI stack.
4. **PinePhone Pro:** only if "open hardware, no bootloader lock" matters more than reuse. It means a new SoC and an
   AT-command modem path.

### Adding a device

- **Kernel:** a new `kernel/baseport/arm64/<board>_variant` (+ `<soc>_assp` for a new SoC), as in the baseport
  README. Keep the phone's DTB out of git, like `private/bonito.dtb`.
- **Before buying:** check the Nura wiki page's feature table in a browser, and the exact model number (carrier lock,
  regional variant).
- **When a port lands:** move its row to a "Ported" table in this section, and update [roadmap.md](roadmap.md) and the org
  profile.
