<!-- SPDX-License-Identifier: Apache-2.0 -->
# Bluetooth on the Pixel 3a XL

Written 2026-11-15. This is the Bluetooth part of [driver-support.md](driver-support.md) D6 (roadmap P4), next to
[wifi.md](wifi.md): from a silent WCN3990 Bluetooth core to BLE devices, file transfer, headsets and old S60 apps that
use Bluetooth. It is a design and an estimate; nothing here is built yet.

Sources: a read of our kernel, neolink, telephony and build trees; the 2010 Symbian Bluetooth sources on GitHub
(`SymbianSource/oss.FCL.sf.os.bt` at `ba9e7d24a7`, `oss.FCL.sf.mw.remoteconn`, `oss.FCL.sf.mw.btservices`); the
phone's DTB; mainline Linux `drivers/bluetooth/hci_qca.c` and `btqca.c`; a Codex (gpt-6-astra) architecture review.

## Decisions (owner, 2026-11-14/15)

- **All four uses:** BLE devices (GATT: keyboards, watches), OBEX file transfer, real Bluetooth APIs for old .sis
  apps, and headset audio (A2DP music, HFP calls).
- **A new Rust host stack** in NeoSymbian/neolink, with a Symbian-compatible layer on top for old apps. The 2010 stack
  (`bt_v2.prt`, HCI v2, link manager, L2CAP, RFCOMM, security manager) is **not** ported; its client DLLs are.
- **BLE first:** after the chip comes up (B0/B1), BLE/GATT through the TrouBLE crate (B2), then pairing, Classic,
  OBEX and old apps, A2DP, HFP.
- **Bonds** (pairing keys) live in `C:\private\<BTSRV SID>\` so headsets reconnect right after boot. That is
  filesystem isolation only, and we say so. Encryption with an unlock secret comes back when there is a lock screen.
- **Acceptance devices are generic for now:** any A2DP/HFP headset, a BLE keyboard, a PC for OBEX. The old apps that
  use Bluetooth are still to be named.

## How hard is it, compared with Wi-Fi?

**The chip is easier. The whole feature is much bigger.**

Wi-Fi was quick (W0–W7 in about two days of agent sessions) for two reasons. The modem loaded the Wi-Fi firmware and
ran the 802.11 MAC; we only had to drive copy engines and WMI. And above the driver, smoltcp and the 2010 ESOCK did
the networking.

Bluetooth turns that around:

| | Wi-Fi | Bluetooth |
|---|---|---|
| Transport | SNOC copy engines, SMMU, MSA memory, QMI WLFW through the modem | A plain UART (GENI SE6) at 3.2 Mbaud with RTS/CTS: simpler |
| Firmware | The modem fetches it over TFTP from MODEMD | **We push it** over HCI (rampatch + NVM, TLV files) |
| Power | Voted before modem boot | The same rails, already voted; plus an on/off byte pulse on the UART |
| Above the driver | The firmware does the MAC; smoltcp + ESOCK do IP | **We write the host stack**: HCI, L2CAP, RFCOMM, SDP, pairing, GATT, AVDTP, HFP |
| Old apps | `RSocket` over ESOCK came almost free (`neonet.prt`) | A facade with real L2CAP/RFCOMM semantics, SDP queries, a device registry and notifiers |
| Audio | none | A2DP needs a PCM source; HFP needs call audio routed to the headset (SLIMbus via the ADSP) |

Estimate (low confidence; planning ranges, not dates):

- **B0–B1 (chip up, firmware in, inquiry/scan):** about the size of W0–W3, a few days. Easier transport, but the
  firmware download is ours.
- **First useful features** (BLE GATT, or OBEX send/receive): **2–5×** the Wi-Fi effort.
- **Everything asked for:** **10–30×** the Wi-Fi effort, roughly **20–60 agent-session days**. HFP audio routing and
  exact old-app behaviour carry most of the uncertainty.

New or adapted production code, excluding tests and unchanged dependencies:

| Part | Lines |
|---|---:|
| GENI UART + HCI LDD + H4 framing + IBS sleep (kernel C++) | 2–4k |
| Qualcomm bootstrap and firmware download (Rust) | 1–2k |
| Controller core + Classic protocols: L2CAP, RFCOMM, SDP, GAP, security policy | 12–25k |
| BLE integration (TrouBLE adapter), SMP, persistence | 3–8k |
| Legacy facade: `NEOBT.PRT`, compatible servers, notifier plugins | 5–12k |
| A2DP + AVRCP + SBC encoder | 6–12k |
| HFP control + hardware audio integration | 5–15k+ |
| neoui screens, OBEX binding, HID and watch services | 3–7k |

That is **40–85k lines** with overlap. Writing BLE ourselves instead of adopting TrouBLE adds another large protocol
implementation.

## Hardware facts

From the phone's DTB (`private/bonito.dtb`, facts only) and our kernel:

- **UART:** `serial@898000`, `qcom,geni-uart`, QUP wrapper 0 (`0x8c0000`), serial engine 6, interrupt SPI 607
  (INTID 639). Pins gpio45 CTS, gpio46 RTS, gpio47 TX, gpio48 RX (function `qup6`): hardware flow control is wired.
- **Bluetooth node:** `qcom,wcn3990-bt`, `max-speed = 3200000`. No `local-bd-address`, no enable GPIO, no
  `firmware-name`, no btfm (SLIMbus Bluetooth audio) nodes.
- **Supplies:** vddio = `vph_pwr`, vddxo = ldoa9 (1.8 V), vddrf = ldoa6 (~1.3 V), vddch0 = ldoa19 (~3.3 V), shared
  with Wi-Fi. `kernel/baseport/arm64/sdm670_assp/qcom_mss.cpp` (lines ~330–336) votes them, and RF_CLK2, before the
  modem boots, so they are on whenever the modem runs.
- **What the kernel lacks:** a GENI UART driver. GENI I2C exists (`sdm670_assp/qcom_geni_i2c.cpp`, wrapper 1, FIFO,
  polled) as a register template. Wrapper 0 is not in the I/O map
  (`bonito_variant/specific/pixel_bonito.cpp`, which also says "No UART") and its clocks are not voted. Linux votes
  wrapper-0 AHB at GCC `+0x5200c` bits 6/7 and SE6 at bit 16; the serial engine's clock (RCG and divider for
  3.2 Mbaud) needs a facts spec.
- **Firmware:** not checked yet. Look in `vendor_a` (where MODEMD already reads the Wi-Fi files) and the
  `bluetooth_a` partition ([telephony.md](telephony.md) lists it; our backup copy is all zeros). The file names follow
  the chip's ROM version (WCN3990: `crbtfw<ver>.tlv` + `crnv<ver>.bin`); read the version at B0, don't assume `21`.
- **Call audio:** stock Android on bonito routes Bluetooth calls through SLIMbus (`SLIM_7_RX_Voice`,
  `SLIM_7_TX_MMode1`, 16 kHz) between the ADSP and the WCN3990. The missing DTB nodes don't mean the hardware is
  missing.

### What Linux does (facts for a spec, not code to copy)

`hci_qca.c` and `btqca.c` are **GPL-2.0**, unlike ath10k (ISC). We write the facts into `private/bt/` and implement
from that spec, the same way as `qcom_wcn3990.cpp`.

1. **Power on:** flow control off; at 2400 baud send the off byte `0xC0`; at 115200 send the on byte `0xFC`; wait
   ~100 ms; flow control back on.
2. **Version:** vendor command `0xFC00`, sub-command `0x19` (patch version request): product, patch, ROM and SoC ids.
3. **Speed:** vendor command `0xFC48` with a baud index; the chip answers at the new speed (Linux drops that event).
4. **Firmware:** rampatch (TLV type 1) then NVM (type 2), sub-command `0x1E`, segments of at most 243 bytes. Linux
   patches some NVM tags (baud, IBS, deep sleep) on the way and has version-specific ack rules.
5. **Address:** vendor command `0xFC14` with the 6 bytes reversed. The WCN3990 stores no address; the host supplies it.
6. **Reset** (HCI_Reset), then normal setup.
7. **IBS sleep** (in-band sleep): single bytes between H4 packets, `0xFE` sleep, `0xFD` wake, `0xFC` wake-ack, with
   separate TX and RX state machines, a wake-retransmit timer and a TX idle timer.
8. **Off:** the `0xC0` byte, then the rails (here: drop our vote; Wi-Fi may still hold them).

## Architecture

```
  old S60 app (.sis)                  neoui (Settings → Bluetooth, pairing dialogs, Send via Bluetooth)
        │                                   │
  2010 client DLLs, rebuilt unchanged:      │  native IPC (bt-ipc)
  bluetooth.dll  btdevice  btmanclient       │
  sdpagent  sdpdatabase  btextnotifiers      │
  obex.dll (+ irobex alias, BT transport)    │
        │ RSocket / RHostResolver /          │
        │ RNetDatabase                       │
     ESOCK ── NEOBT.PRT (C++ facade) ────────┤
        │ !BTManServer  !SdpServer           │       EIKSRV notifier plugins (select, PIN,
        │ (+ eirclient, hciserverclient)     │       auth, SSP) ──► BTSRV broker ──► neoui dialog
        ▼                                    ▼
  ┌──────────────────────── BTSRV.EXE (Rust, neolink) ────────────────────────┐
  │ bt-core: one HCI command scheduler, handles, ACL credits, reassembly        │
  │ bt-qca: power pulse, version, firmware download, baud, address             │
  │ bt-le: TrouBLE adapter (GATT, SMP)     bt-classic: L2CAP, RFCOMM, SDP, GAP  │
  │ bt-profiles: AVDTP/A2DP, AVCTP/AVRCP, HFP AG, HID    bonds in C:\private\   │
  └─────────────────────────────────────┬───────────────────────────────────────┘
                                        │ RBusLogicalChannel: packets, status, bootstrap controls
                         HCI LDD (kernel C++): H4 framing, IBS sleep, recovery
                                        │
                         GENI UART engine: SE6 FIFO, IRQ, RTS/CTS, 2400 / 115200 / 3.2 Mbaud
                                        │
                                     WCN3990 BT core ── SLIMbus ── ADSP (call audio, owned by MODEMD)
```

MODEMD keeps owning the ADSP and the call-audio route. It also reads the firmware files for BTSRV. BTSRV owns
everything Bluetooth: the controller, connections, security, profiles and stored state. Nothing else talks HCI.

## Design decisions

| Decision | Choice | Why |
|---|---|---|
| Transport | **A dedicated HCI LDD**, not ECOMM | ECOMM works (T7), but a byte stream races with the bootstrap's baud changes, the power pulses and IBS. An HCI channel moves whole packets and owns those controls. |
| H4 + IBS | **In the kernel** | IBS is timing-sensitive (wake/ack within milliseconds). IBS bytes are recognised only **between** H4 packets. UART overruns or corruption trigger a controlled reset, not a guess at resync. |
| UART mode | Interrupt-driven FIFO first | DMA (GPI) only if measurements say so. Keep RX clocks on until wake detection is proven. |
| Channel ABI | Versioned, fixed-width | Send/receive packets, cancel, status, a **generation** number (stale completions after a reset are dropped), privileged bootstrap controls (pulse, baud, flow control). Bounded lengths, explicit queue-full. Reset or client death completes every request exactly once. |
| Firmware download | **Rust**, `bt-qca`, sans-I/O like `wlfw` | Bytes, events and deadlines in, actions out: testable on the host. |
| Firmware files | **MODEMD** reads them with its vendor ext4 reader, allowlisted names, bounded sizes | It already reads `vendor_a` for Wi-Fi. Must work with cellular off. Device-owned files over ROFS copies. |
| BD address | Factory address first; otherwise a provisional persistent one; BLE gets a proper random identity | Wi-Fi's `02:4e:<SoC serial>` is a MAC policy, not a Bluetooth address policy. Never derive anything from the IMEI. |
| BLE | **Adopt TrouBLE** (`trouble-host`, MIT/Apache, `no_std`) behind an adapter, pinned | GATT and SMP are large. Gate: it must run on our executor and must not own the controller (TrouBLE sends HCI Reset and sets event masks; only bt-core may). Fallback: our own BLE. |
| Classic | **Our own** L2CAP, RFCOMM, SDP, GAP | No `no_std` Classic stack fits. Floss (Android) is Rust + C++ on Linux infrastructure; a reference, not a base. `bt-hci` packet types where they fit. |
| Threads | One protocol-owner thread in BTSRV, bounded queues; codec and storage workers when needed | Compatibility servers delegate to the owner. e32 mutexes and semaphores; **no CAS**, no lock-free queues. |
| Rails | One shared WCN3990 vote for Wi-Fi and Bluetooth | Bluetooth must not need a running modem and must not drop Wi-Fi's rails. |

### Crates (neolink)

| Crate | Job |
|---|---|
| `crates/bt-core` | HCI command scheduler, connection handles, ACL credits, reassembly, event masks |
| `crates/bt-qca` | Qualcomm bootstrap and firmware download state machine |
| `crates/bt-classic` | L2CAP, RFCOMM, SDP, GAP and security policy |
| `crates/bt-le` | TrouBLE adapter, GATT, SMP, identity and privacy |
| `crates/bt-profiles` | AVDTP/A2DP, AVCTP/AVRCP, HFP AG, HID |
| `crates/bt-ipc` | The versioned native protocol and its client (neoui, the transfer service) |
| `symbian/btsrv` | `BTSRV.EXE`: e32 glue, compatibility servers, persistence |

### Two gates before TrouBLE (B2)

- **Executor:** `e32-rs/crates/e32/src/rt.rs` polls with `Waker::noop()` and waits for kernel completions. TrouBLE's
  async code needs real software wakes and timers. A build that compiles proves nothing; it must make progress.
- **Atomics:** e32 has a kernel-mutex `critical-section` (`e32-rs/crates/e32/src/cs.rs`). Every transitive atomic in
  TrouBLE and its Embassy dependencies still has to be audited and linked for `armv5te-none-eabi`.

## The compatibility layer for old apps

Rebuilding the 2010 **client** DLLs keeps their C++ layouts, descriptors, leaves, export ordinals and async wrappers.
That is far cheaper and more faithful than rewriting them in Rust. What they talk to is new.

| 2010 part | Plan |
|---|---|
| `bluetooth.dll`, `btdevice.dll`, `btmanclient.dll` | Rebuild from source with frozen exports; provide what they depend on |
| `sdpagent.dll`, `sdpdatabase.dll` | Reuse unchanged |
| `btextnotifiers.dll` | Reuse the parameter types; replace the dialog providers |
| `obex.dll`, `irobex.dll` alias, `obexcommontransport.dll`, the ECom BT transport | Reuse (`mw.remoteconn/obex`) |
| `bt_v2.prt`, HCI v2, link manager, L2CAP, RFCOMM, security manager | **Replace** |
| BTManServer, SdpServer | Rust compatibility servers inside BTSRV, same names, versions and IPC |
| S60 `bteng`, `btaudioman`, `btsac`, RemCon | Keep the client contracts apps need; bridge to BTSRV. Never a second controller or audio owner |

### `NEOBT.PRT`, the ESOCK facade

A thin C++ protocol module, like `neonet.prt` (`build/apps/esock/`), registered with the original address family
(`KBTAddrFamily`) and protocol ids through its `.esk`. It provides:

- socket providers for **BTLinkManager, L2CAP and RFCOMM**;
- **inquiry and name lookup** (`RHostResolver`, a `CHostResolvProvdBase`);
- **remote SDP queries** (`RNetDatabase`, a `CNetDBProvdBase`). Unchanged `CSdpAgent` uses `RNetDatabase`, not the
  SDP server. `RSdp`/`RSdpDatabase` use `!SdpServer` only for local records;
- physical-link options and notifications (`RBTPhysicalLinkAdapter`), security checks, cancellation.

Every pending operation is an active object forwarding to BTSRV. It must keep the real semantics: stream vs datagram,
negotiated MTUs, RFCOMM credits and modem signals, resolver iteration, SDP continuation, per-request cancel.
**Unlike `neonet.prt`**, options are not accepted-and-ignored and `SecurityCheck` is not permissive.

ESOCK worker binding: our ESOCK uses the split layout (Main 0, DIP 1, IP 6, TR 7), so the Bluetooth `.cmi` follows
the 2010 `esock_bt_399.cmi` pattern, not `esock_bt.cmi` (which binds to the wrong worker).

### Servers and start-up

- `!BTManServer`: registry searches, local settings, notifications, serialized results.
- `!SdpServer`: local records, deleted when their subsession closes or the client dies.
- `bluetooth.dll` also imports `eirclient` and `hciserverclient`, and its pairing API uses another server: they are
  in the loader closure and need endpoints.
- `BTManServer` is not an 8.3 ROM name. Use a loader alias (as for `ecomm`, `build/toolchain/efile_exe/ldr_builtin_devices.cpp`)
  or patch the internal launch path while keeping the public ABI.

"Unchanged clients" is a target, not yet a build result. From B0 on, inventory the frozen exports (SDK `.def` files in
`~/WS/Symbian/sdk/proxies`), start-up dependencies and IPC layouts. As each piece lands, remove its panic stub from
`legacy/components.py` (the Bluetooth block, line ~174: `bluetooth`, `btextnotifiers`, `sdpagent`, `sdpdatabase`,
`irobex`, `remconcoreapi`, `remconinterfacebase`).

### Notifiers and the UI

EIKSRV notifier plugins decode the original packages and forward to a BTSRV **interaction broker**, which asks neoui
for a dialog. UIDs: device selection `0x100069D1`, PIN `0x100069C9`, SSP-aware PIN `0x10285D55`, authorisation
`0x100069CF`, passkey display `0x10285AD4`, numeric comparison `0x10285AD5`. Native callers use the broker directly.
The LEGACY supervisor ([legacy.md](legacy.md)) presents; it never owns bond state. Cancel, timeout or UI death means
**reject**.

### OBEX

OBEX is a user-side library over RFCOMM, not part of the host stack. Reuse it. A small Rust transfer service owns
files, consent and progress through a narrow C binding to `CObexClient`/`CObexServer`, so OBEX exists once for both
neoui and old apps.

## Audio

### A2DP (music)

- **A2DP Source**, AVDTP signalling, SBC packetisation, AVRCP controls.
- A **fixed-point Rust SBC encoder**, checked against test vectors and timed under ARMv5TE soft-float.
- PCM comes from the mixer **before** ADSP playback, through a shared routing and focus interface. The ringtone path
  ([telephony.md](telephony.md), 2026-11-14) proves playback only; a general PCM producer is new work.
- A call suspends music; focus policy restores it afterwards.

### HFP (calls)

- **Audio Gateway** role: RFCOMM AT commands, indicators, answer/hang up, volume, codec negotiation. MODEMD stays the
  owner of call state.
- **Route:** investigate **SLIMbus first** (ADSP ↔ WCN3990, as stock Android does). SCO over the UART only if the
  firmware can route it there; it would also need duplex call PCM from the ADSP, which the current passive voice
  session does not give the host.
- **CVSD** (narrowband) first, then **mSBC** (wideband). Find out whether the controller codes CVSD itself before
  writing a codec.
- Route changes are transactional in MODEMD, with rollback to the earpiece if the headset drops, keeping today's
  teardown order.

## Security and capabilities

- **Classic SSP:** the controller does the link crypto; Rust owns policy, the dialogs and the keys.
- **BLE LE Secure Connections:** reviewed Rust AES-CMAC and P-256. Just Works is not MITM protection; enforce the
  negotiated strength.
- **Randomness:** the hardware PRNG HAL `0x4e23` (`sdm670_assp/qcom_telhal.cpp`), failing closed: a partial buffer
  is discarded, never padded with timestamps.
- **Bonds:** `C:\private\<BTSRV SID>\`, crash-safe replace, versioned, keys never logged. Protection is filesystem
  isolation (owner decision above).
- **Capabilities are checked against the original caller**, not ESOCK's ROM capabilities: ESOCK passes the caller's
  identity and BTSRV checks it (e32 needs caller-security helpers). Keep the 2010 per-operation policies:
  LocalServices, NetworkControl where it applies, WriteDeviceData for the registry, ReadDeviceData for key disclosure.
  ROM EXEs get every capability, so test with restricted `drive=c` clients too.

## Milestones

Each has an exit test on the real phone (RAM boots, as for Wi-Fi). QEMU coverage needs a **Syborg virtual HCI** backed
by a host-socket controller simulator; it tests the guest stack and old clients, not GENI, IBS or ADSP routing.

| Stage | What | Exit on the phone | QEMU |
|---|---|---|---|
| **B0** | Wrapper-0 clocks and I/O map, GENI UART engine, HCI LDD, power pulses, H4 | A valid version answer (`0xFC00`/`0x19`) after cold boot and after repeated init | Parsing only |
| **B1** | `bt-qca`: firmware read via MODEMD, download, operational baud, address, reset, recovery; IBS | Repeated LE scan and Classic inquiry without hurting LTE or Wi-Fi; plus an early SLIMbus/UART audio feasibility probe | Firmware and state-machine faults |
| **B2** | Executor and atomics gate; TrouBLE behind bt-core | Discover a BLE device, read GATT, receive notifications | Executor, credits, simulated GATT |
| **B3** | Pairing UI (neoui), SSP and LESC, bonds | Pair, reboot, reconnect; reject, cancel and PRNG-failure paths | Crypto vectors, IPC, storage faults |
| **B4** | L2CAP, RFCOMM, SDP; minimal `NEOBT.PRT` + compatible servers | An unchanged 2010 client discovers, queries SDP, transfers, cancels and closes | Full protocol tests |
| **B5** | OBEX (UI send/receive) and old-app contracts | Files both ways with equal hashes; an old app transfers through the reused OBEX; registry, physical-link and notifier contracts pass | ABI, IPC and transfer tests |
| **B6** | A2DP, SBC, AVRCP | 30 minutes of music, controls, disconnect/reconnect, a call pre-empts | Codec and signalling |
| **B7** | HFP AG | A two-way CVSD call, then mSBC; answer, hang up, mute, route switch, headset loss | AT and call-state tests |
| **B8** | HID over GATT, selected watch services | Keyboard and mouse; reconnect; privacy | HID/GATT fixtures |
| **B9** | Acceptance | Wi-Fi + BT + LTE together, fault recovery, screen-off wake, overnight idle, a 24-hour mixed-use run | Stress and fault models |

"Watches" means named models: generic GATT does not implement a vendor's sync protocol.

## Licences

- **Linux `hci_qca.c`, `btqca.c`, `gcc-sdm845.c`:** GPL-2.0. Facts into `private/bt/` (opcodes, sequences, register
  offsets), then a new implementation. No translated code.
- **Symbian:** unchanged files stay EPL-1.0; files we change follow the workspace EPL-2.0 rule (SPDX on header line 7, a
  Contributors line).
- **Ours:** Apache-2.0. TrouBLE and `bt-hci` are MIT/Apache.
- **SBC/mSBC and SIG:** code licence and patent rights are separate questions. Check the Bluetooth SIG agreements and
  qualification duties before distributing images; don't assume the codecs are patent-free because they are old.

## Corrections to older notes

- ECOMM loading by name works since T7 (loader aliases in `build/toolchain/efile_exe/ldr_builtin_devices.cpp`,
  [debug-access-roadmap.md](debug-access-roadmap.md) T7). The Bluetooth plan doesn't use ECOMM anyway.
- The ringtone result proves ADSP playback, not capture or duplex call PCM.

## Open items

Investigation, answered by milestones:
- where the firmware files are (`vendor_a`, `bluetooth_a`) and the chip's ROM version (B0);
- whether a factory BD address exists anywhere (B1);
- whether the firmware routes SCO over the UART, and how SLIMbus is set up for BT voice (B1 probe, B7).

For the owner, later:
- the acceptance devices (headset, watch, keyboard) and the old .sis apps that use Bluetooth;
- encrypted bonds once there is a lock screen.
