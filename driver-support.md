<!-- SPDX-License-Identifier: Apache-2.0 -->
# Pixel 3a XL driver support

Accepted program: 2026-11-10. Target: **bonito / SDM670**. Native Rust apps first,
legacy Symbian adapters later. This continues the hardware track without changing
EKA2's AArch64 ILP32 kernel or ARMv5TE soft-float user ABI.

## Evidence and current inventory

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

| Subsystem | Evidence / existing implementation | Remaining work |
|---|---|---|
| CPU, interrupt, timer | Eight-core boot recorded; GICv3, virtual timer | Focused timer/wake correctness before deep suspend |
| Storage | eMMC, persistent C:/E:, ROFS and A/B recorded | Preserve partition allow-list and recovery gates |
| Display/input | Bootloader OLED framebuffer, Synaptics RMI4 touch, PMIC keys | Independent panel initialization, brightness/blanking, IRQ/wake |
| PMIC/power | SPMI, RPMh, RTC and reboot code | Fuel gauge (`qcom,pmi8998-fg`), PM660 RRADC, charger, TSENS, policy |
| USB | DWC3 debug console on RAM boots | Cold/installed-boot power remains open; see known-issues |
| Audio | ADSP, dual CS35L36 amps, RT5514 mic; C6 two-way calls recorded | Independent audio lifecycle, amplifier protection, ASM/ADM PCM, native jack |
| Haptics | DTB TI DRV2624, I2C10 `0x5a`, reset GPIO24 | Driver, verified supplies/actuator configuration, bounded pulse; PM660 haptics disabled |
| Sensors | ADSP FastRPC transport described; sensor GPIO ownership reserved | Discover exact chips, firmware sensor protocol and calibration requirements |
| Front camera | DTB Sony IMX355, CCI1 `0x1a`, MCLK2 19.2 MHz, reset GPIO9 | CCI/CAMSS/DMA and software image processing |
| Rear camera | DTB Sony IMX363, CCI0 `0x1a`, MCLK0 24 MHz, reset GPIO127; LC898219XI focus actuator | Separately pinned downstream mode/calibration evidence, capture and focus |
| Wi-Fi | DTB WCN3990 enabled at `0x18800000` | QMI firmware control plus SNOC copy engines and full packet/protocol path |
| Bluetooth | DTB WCN3990 UART transport | GENI UART/HCI, firmware, IBS sleep, BLE and audio profiles |
| GNSS | Qualcomm modem; QMI LOC is a protocol reference | Discover live service, standalone fixes and typed location API |
| NFC | DTB NXP NCI I2C `0x28`; AOSP NXP configuration | Verify chip/firmware, NCI and tag reading |
| Fingerprint | Google FPC service configuration | Verify exact sensor and secure enrollment/matching interface; PIN fallback |

Prior feature results above remain historical implementation-note evidence;
checks repeated in this change are identified in the verification record. Sensor and camera entries in Dev tools were catalogue
placeholders, not linked working drivers.

## Integration contracts

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
- MODEMD initially owns APR and ADSP QRTR exclusively. Independent ADSP/radio
  state machines must pump even after radio failure; support-only routing must
  never advertise dummy RMTFS memory. Use fixed deadlines and bounded work under
  IPC load. Defer AUDIOD extraction until this passes phone regressions.
- Versioned native IPC: audio configure/queue/reclaim/start/stop/route/focus;
  sensors enumerate/subscribe/timestamped samples/calibration/drops; camera
  exclusive session/modes/queue/dequeue/controls/capture; power/network/location
  subscriptions. Enforce capabilities at the service and kernel boundaries.
- Report actual readiness through the existing device registry: absent, off,
  starting, ok, partial or error. DSP boot or driver linkage alone is not readiness.

## Milestones and gates

| Stage | Work | Acceptance |
|---|---|---|
| D0 inventory | Sanitized DTB inspection, reconcile roadmap, pin reference/firmware provenance; probe exact silicon before using it | Reproducible report plus explicit unknowns; no public firmware/calibration |
| D1 foundations | Explicit bus startup, validated bus requests; resource votes, async streams and per-device DMA follow | Existing call/storage/input regressions pass; cancellation and OOM bounded |
| D2 power | Fuel gauge/RRADC, charging telemetry, TSENS, conservative policy; OLED brightness/blanking and input wake; cold USB | Compared telemetry, thermal shutdown and cold-boot logs; power baseline |
| D3 audio/haptics | Independent audio lifecycle; conservative amplifier gain and fault mute; ASM/ADM 48 kHz S16 playback and mono capture; typed audio service; DRV2624; 3.5 mm jack later | Tone/WAV playback, recorded WAV, ringtone→call, volume/mute/routes; audio with no SIM/radio off and radio failures; bounded vibration |
| D4 sensors | Sensor PD/FastRPC/reverse file service; discover actual sensor protocol; proximity/light→accel/gyro→compass/barometer→batching/fusion | Six-orientation gravity, gyro zero/motion, call proximity/light transitions, calibrated units/timestamps and wake |
| D5 cameras | CAMCC/power/CCI/CAMSS/isolated DMA; ID→testgen→sensor pattern→scene; IMX355 first, IMX363/focus next | Reduced preview >=10 fps and recognizable persistent JPEG, correct format/orientation, bounded RAM/latency, no SMMU faults |
| D6 connectivity | WCN3990 SNOC/CE DMA, QMI and HTC/WMI/HTT, WPA2-PSK and ESOCK/TCPIP6 NIF coordinated with C10; BT UART/HCI/IBS and BLE→A2DP/HFP; QMI LOC | Wi-Fi scan/auth/IP/traffic, BT pairing/GATT/audio routing, outdoor standalone fix; coexistence and idle-power evidence |
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

## Verification and implementation record

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
[the implementation verification record](verification/driver-support-2026-11-10.md)
for this change's actual commands and limitations.

## Primary hardware references

Read for register/protocol facts; preserve the project's licence boundaries:

- [Linux Google SDM670 device tree](https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/sdm670-google-common.dtsi): front camera and supplies; does not establish rear support.
- [IMX355 reference](https://raw.githubusercontent.com/torvalds/linux/master/drivers/media/i2c/imx355.c).
- [Google camera wiring](https://android.googlesource.com/kernel/msm/+/b9d5f1970a0e0a6482250f2e076dd7f6c192e566/arch/arm64/boot/dts/google/sdm670-camera-sensor-v2.dtsi).
- [HexagonRPC](https://github.com/linux-msm/hexagonrpc): FastRPC/reverse file service.
- [WCN3990 SNOC](https://raw.githubusercontent.com/torvalds/linux/master/drivers/net/wireless/ath/ath10k/snoc.c), [Bluetooth HCI/IBS](https://raw.githubusercontent.com/torvalds/linux/master/drivers/bluetooth/hci_qca.c).
- [QMI LOC definitions](https://raw.githubusercontent.com/linux-mobile-broadband/libqmi/main/data/qmi-service-loc.json).
- [Google device configuration](https://android.googlesource.com/device/google/bonito/+/refs/heads/main/device.mk), [hardware diagram](https://support.google.com/pixelphone/answer/7157629?hl=en).
