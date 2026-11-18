<!-- SPDX-License-Identifier: Apache-2.0 -->
# Read-only battery telemetry

Target: Pixel 3a XL (bonito), PM660 on SPMI SID 0. This extends the thermal
telemetry work on `feat/pixel-driver-support`. Hardware control remains owned by
firmware: this driver does not configure charging, kick its watchdog, load a
battery profile, access gauge SRAM or trigger ADC conversions.

## Readings and confidence

The accepted policy is to display the PMIC-reported charge estimate when its
hardware readiness checks pass. It is not Android's smoothed UI percentage.
Profile integrity and measurement age cannot be proven through these direct
register reads; Dev tools must state that the profile is unverified. Matching
shadow copies demonstrate coherent observations, not independent calibration.
Missing, inconsistent or failed readings remain unknown, never synthetic zero.

| SID 0 address | Interpretation |
|---|---|
| `0x0104/0105` | PMIC type `0x51`, PM660 subtype `0x1b` |
| `0x4005/4105` | SOC/info peripheral subtypes `0x10/0x11` |
| `0x4009/400a` | Monotonic SOC and redundant shadow; bounded equality retries |
| `0x4010` bit 1 | SOC ready |
| `0x4046` bit 7, `0x4048` bit 0 | Algorithm enabled, restart active |
| `0x4110` bit 3, `0x1210` bits 5/4 | Battery-detection/missing flags |
| `0x4109` bit 7 | Gauge watchdog reset diagnostic |
| `0x41a0/a1`, `0x41a6/a7` | Little-endian voltage and shadow copy |
| `0x1310` bit 4 | USB present; bit 3 is overvoltage, not presence |
| `0x160b` bits 4 and 0 | USB selected and input source valid |
| `0x1006` bits 2:0, `0x1007` bit 5 | Charger phase and battery overvoltage |

Voltage conversion promotes before multiplication:
`TUint64(raw) * 122070 / 1000` gives microvolts. PM660 uses the v2 byte ordering;
do not use the PMI8998-v1 swapped-byte workaround. MSOC maps raw 0 to 0%, 255 to
100%, and intermediate values to `round((raw - 1) * 98 / 253) + 1`.

USB plugged-in, usable input power and charging are separate facts. With valid
battery/charger state, offline means discharging; overvoltage suppresses charging;
phases 0..4 mean charging, 5/6 full and 7 disabled/not charging. Unknown fields
remain independent so, for example, USB state can be available without gauge SOC.

## Interface and user surfaces

HAL `EHalGroupVariant/0x4e1a` requires `ReadDeviceData`; a1 is an output descriptor.
Version 1 is exactly 32 bytes, eight little-endian unsigned 32-bit words:

`version, valid_mask, present, percent, voltage_uV, usb_present, usb_online, charge_state`

Valid-mask bits 0..5 correspond to the six data fields in order. Charge states:
0 unknown, 1 discharging, 2 charging, 3 not charging, 4 full. Partial snapshots
are successful; callers must consult validity. Unsupported boards/kernels return
`KErrNotSupported`. No existing IPC layouts are changed. The monitor's `battery`
command and device registry expose diagnostics; the registry state is `partial`
for available telemetry without a charging policy.

The UI server polls every five seconds, sharing its latest observation with the
status bar and Settings. Unknown percentage is neutral/`--%`; the charging mark
requires a decoded charging state. A separate plug shows valid USB presence;
a full check requires valid full state and usable USB power. Discharging stays
neutral. Settings' old fixed 82% value is replaced with
a live Battery page: percentage, voltage, connection/charging state and history.
Dev tools' Battery and charger row maps the kernel entry and explains unavailable
fields/profile confidence.

## History across reboots

Collect real, timestamped minute observations, capped at 1,440 entries / 24 hours.
The graph uses a 0..100% axis; invalid values, shutdown intervals and clock changes
are gaps. Genuine 0% is a point, not a gap. No padded zeros or invented past data.

Two alternating versioned/checksummed files live in the UI server's existing
private directory on C:. Load the newest valid bounded copy, preserving the older
copy while replacing its peer. Save every five minutes and before every normal
restart, fastboot restart or shutdown, before `clockwork.power()` finalizes drives.
A crash may lose the unsaved interval; this is not a claim of full power-cut
filesystem durability. A history I/O failure must not stop live telemetry.

Persistent history writes application files on C:; “read-only” applies to the
PMIC and charger. Preserve existing settings, clock and other user files. Ignore
corrupt history rather than formatting or repairing the drive. Prune future-dated
and expired records and break graph segments across restarts/time adjustments.

## Acceptance

- Actual-source fake-SPMI tests cover identity, readiness, shadow mismatch, error
  propagation, retry bounds, SOC endpoints, high-voltage arithmetic and no writes.
- Host UI/model tests cover invalid fields, real zero, chart gaps, retention,
  checksums, torn/corrupt newest copy and clock changes. Actual file-I/O fault
  injection remains separate target acceptance.
- Build matching kernel, SYSSTART and Dev tools. RAM-boot first; no boot/system
  partition flashing is needed. Capture monitor/HAL data and actual phone screens.
- User-assisted USB unplug/replug checks must distinguish connection from charging
  and update within one polling interval. Store transition logs for later USB readback.
- Demonstrate restoration across two boots using the existing persistent C:
  drive. Corruption tests use disposable emulator images/host fixtures, not phone
  userdata. Record commands, exits, hashes, screenshots and remaining gaps under
  `private/driver-support/battery-20261111/`.

Implementation and runtime acceptance are recorded separately in the
[verification record](verification/battery-2026-11-11.md). Host/build success does
not establish phone battery readings or persistent-C restoration.

## Primary references

- [Linux PM660/PMI8998 charger](https://raw.githubusercontent.com/torvalds/linux/v6.16/drivers/power/supply/qcom_pmi8998_charger.c).
- [AOSP PM660 gauge and voltage conversion](https://android.googlesource.com/kernel/msm/+/0f5f44a2e74ce7f335a2432e3e51155419ccc42d/drivers/power/qpnp-fg-gen3.c).
- [AOSP SOC conversion/readiness](https://android.googlesource.com/kernel/msm/+/6289dd9905d07b82140a93f31229e967a75e595f/drivers/power/supply/qcom/qpnp-fg-gen3.c).
- [AOSP coherent voltage reader](https://android.googlesource.com/kernel/msm/+/60e67638d95e7fd48f602b15729ea13c13c478d5/drivers/power/supply/qcom/fg-util.c).
