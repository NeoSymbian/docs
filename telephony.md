# Telephony: cellular calls, SMS and data on the Pixel 3a XL

Written 2026-11-08. This file is the end-to-end runbook for roadmap Track P: from a silent modem to a phone that
places and takes calls, sends SMS and uses mobile data. It replaces the outline in `roadmap.md` Track P.

Each stage gives its goal, the work, the exit test, and the failure modes we know of. It gets updated at the end of
every stage with what really happened.

- Facts marked **DTB** come from the mainline bonito device tree (the ztOS boot.img, `~/WS/ztOS/…/sdc/boot.img`).
  Dump it with `dtc -I dtb -O dts` after the `d00dfeed` magic.
- **Linux** facts are taken from the mainline drivers named next to them. They describe protocol behaviour and are
  used as reference ([Sources and licences](#sources-and-licences)).
- **unverified** means not checked yet. Stage C1 is meant to check most of them.

## Decisions

| Decision | Made by | Choice |
|---|---|---|
| Networks | user | The SIM's network has 3G and 4G/VoLTE. |
| First milestone | user | A full voice call: dial and answer, two-way audio through the earpiece and the mic. |
| Calls on 4G | **my call** | The modem registers on LTE and uses **CSFB** for calls: it drops to 3G for the call by itself, with no IMS needed. VoLTE is a separate stretch stage (C11). |
| Symbian stack | **my call** (user: "you decide") | A Rust `modemsrv` server plus neoui apps, **no ETel at first**. The 2010 Phone app needs the classic Avkon UI, which neoui replaced. A thin ETel TSY over `modemsrv` comes in C12, only if old apps need it. |
| Language split | roadmap | Transport (SCM, SMEM, SMP2P, GLINK, remote-processor boot, IPA rings) is kernel C++. Protocols (QRTR, QMI, rmtfs, pd-mapper, tqftp, APR, call logic) are user-side Rust. |
| Sources | user: "any option, prefer our own" | Our own code first. The BSD-3 linux-msm tools can be ported closely, with attribution. GPL Linux drivers are reference only. If a piece stalls, porting the GPL driver directly is allowed: that file then carries a GPL-2.0 header and is listed in [Sources](#sources-and-licences). |
| Firmware | **my call** | Qualcomm's signed firmware is read at runtime from the phone's own `modem_a` and `dsp_a` partitions. It never goes into a repo or a ROM. |

## Safety rules

- **Gate G4** (new; the other gates are in `filesystem.md`): any write to `modemst1`, `modemst2`, `fsg`, `fsc`,
  `modemcal`, `persist` or `modem_a/b` needs the owner's OK at the time. Until G4, rmtfs keeps the modem's EFS writes in
  RAM.
- Back up the radio partitions (C0) before the first modem boot of any OS.
- Never put the IMEI, ICCID, IMSI, phone numbers or the DTB in a repo or a committed log. Monitor commands print
  them masked (`35xxxxxxxxxxx12`).
- Don't rely on this phone for emergency calls.

## Hardware facts (DTB)

| Block | Facts |
|---|---|
| **MSS (modem)** | `qcom,sdm670-mss-pil`. QDSP6 registers at `0x4080000`, RMB at `0x4180000`. Watchdog = SPI 266. fatal / ready / handover / stop-ack / shutdown-ack = smp2p-mpss inbound bits 0 / 1 / 2 / 3 / 7. The stop request is outbound bit 0. |
| MSS clocks | GCC: iface, bus, mem, gpll0_mss, snoc_axi, mnoc_axi, prng; plus RPMh xo |
| MSS power and reset | Power domains rpmhpd cx, mx, mss. Resets: AOSS `0xc2a0000` `mss_restart`, PDC `0xb2e0000` reset 9. Halt registers in TCSR `0x1f60000` at +0x3000 (q6), +0x5000 (modem), +0x4000 (nc). Needs an AOP QMP message (`qcom,qmp`) |
| MSS memory | mba `0x95600000` + 2 MB, mpss `0x8b000000` + 0x9800000 (152 MB) |
| Firmware | `modem_a` (FAT16, 4096-byte sectors) holds only the modem: `IMAGE/MBA.MBN`, `MODEM.MDT` + `MODEM.B00`–`B30`, `MODEMR.JSN` (root PD, QMI instance 180), `QDSP6M.QDB`. Build MPSS.AT.4.0.2.c4.1-00120, radio `g670-00145-220106-B-8048689` (2022-01-06). **There is no `dsp_a`**: the ADSP firmware, the `mcfg` carrier profiles and `ipa_fws` sit on `vendor_a` (`/vendor/firmware`, **unverified**), taken from Google's factory image of that radio build. Linux names: `qcom/sdm670/sargo/{mba,modem,adsp,ipa_fws}.mbn` |
| **SMEM** | `0x86000000` + 2 MB, hwlock = TCSR mutex 3 |
| **APCS IPC** | `0x17990000`; doorbell register +0xc. Bits: AOP QMP 0, modem GLINK 12, modem SMP2P 14, ADSP GLINK 24, ADSP SMP2P 26 |
| GLINK edges | modem: SPI 449, remote pid 1. lpass (ADSP): SPI 170, remote pid 2 |
| SMP2P | mpss: SMEM items 435 (**in**, the modem's) / 428 (**out**, ours), SPI 451. lpass: in 443 / out 429, SPI 172. Our out entries "master-kernel" (bit 0 = stop), "ipa"; the modem's in entries "smp2p", "slave-kernel" (fatal 0, ready 1, handover 2, stop-ack 3, shutdown-ack 7) |
| **AOP QMP** | `0xc300000`, SPI 389, mbox bit 0 |
| **rmtfs** | `0xfc201000` + 2 MB (guard pages on both sides), client-id 1, VMID 15 (MSS_MSA) |
| **ADSP** | `qcom,sdm670-adsp-pas` at `0x62400000`, memory `0x95800000` + 0x2200000. Watchdog SPI 162; fatal/ready/handover/stop-ack = smp2p-lpass bits 0–3. APR on GLINK channel `apr_audio_svc`, protection domain `avs/audio` (`msm/adsp/audio_pd`). ACDB name `Global_cal.acdb` |
| **Audio** (C1, from the pmOS UCM + the live mixer) | **Earpiece and loudspeaker** = two Cirrus Logic **CS35L36** amps ("Top", "Bottom") on I2C bus 2 at 0x40/0x41, fed by the ADSP's `SEC_TDM_RX_0`. **Built-in mic** = DMIC through `PRIMARY_TDM_TX_0` ("Sto1/Sto2 ADC MIXL DMIC"). The PM660L analog codec (`qcom,pm660l-wcd-analog-codec`, SPMI 0xf000) + the digital codec (`0x62ec0000`, mclk 9.6 MHz) serve only the 3.5 mm jack (`LPI_MI2S_RX_0` / `LPI_MI2S_TX_3`). Voice = ADSP `VoiceMMode1` (ALSA card 0 device 4), RX topology 268504967, TX 268500988 |
| **IPA** | `0x1e40000` (+gsi `0x1e04000`), IRQs SPI 311 / 432 and smp2p ipa bits. SMMU stream IDs 0x720/0x722. Carve-outs ipa-fw `0x97a00000`, ipa-gsi `0x97a10000` |
| Other carve-outs | hyp `0x85700000`, tz `0x86200000`, cdsp `0x94e00000`, wlan-msa `0x94d00000`, spss `0x97b00000`, qseecom `0x9e400000` |

## The bring-up chain

```mermaid
graph LR
  SCM[SCM calls] --> MSS[MSS boot]
  SMEM --> SMP2P --> MSS
  SMEM --> GLINK --> QRTR
  QMP[AOP QMP] --> MSS
  MSS --> GLINK
  QRTR --> NS[nameserver]
  NS --> RMTFS[rmtfs] & PDM[pd-mapper] & TFTP[tqftp]
  RMTFS & PDM & TFTP --> QMI[QMI DMS/NAS/UIM/VOICE]
  QMI --> MSRV[modemsrv] --> UI[neoui dialer]
  SCM --> ADSP[ADSP boot] --> APR --> VOICE[voice path] --> UI
  QMI --> WMS[SMS]
  QMI --> WDS[data] --> IPA --> NIF[ESOCK NIF]
```

## Stages

| Stage | What | Exit |
|---|---|---|
| C0 | Recon and backups | Radio partitions backed up and hashed; carve-outs safe |
| C1 | Linux reference run | A call on this phone and SIM under mainline Linux; traces captured |
| C2 | Kernel transport | SMEM, SMP2P, GLINK working on the phone (**done** 2026-11-08) |
| C3 | Modem boot | The modem reports ready and talks QRTR (**done** 2026-11-08) |
| C4 | Modem services | Modem stays up; DMS returns the revision |
| C5 | QMI + modemsrv + dialer | Calls ring and can be answered, with no audio yet |
| C6 | Call audio | **Two-way call audio on the earpiece: the first win** |
| C7 | Complete calls | Ringtone, speaker, in-call controls, crash recovery |
| C8 | Call log and contacts | Names on incoming calls |
| C9 | SMS | SMS round-trip, Unicode |
| C10 | Mobile data | HTTP over LTE |
| C11 | VoLTE (stretch) | A VoLTE call, or a recorded no-go |
| C12 | Persistence, power, compatibility | EFS persists (G4); idles overnight and still rings |

Sizes are a **GUESS**: C0–C1 2–4 days, C2–C3 1–2 weeks, C4–C5 1–2 weeks, C6 2–4 weeks, C7–C8 2–3 weeks, C9 1 week,
C10 2–3 weeks, C11 open, C12 1–2 weeks.

### C0: recon and backups

1. **Look for older backups first.** ztOS and Droidian ran on this phone before. If a dump of the radio partitions
   exists, compare hashes.
2. **Dump the radio partitions read-only:**
   - Partitions: `modemst1`, `modemst2`, `fsg`, `fsc`, `persist`, `modem_a`, `dsp_a`, plus `vendor_a` for audio facts.
   - How: a new monitor command `blk dump <part> <offset> <len>` streams the bytes over the USB console to
     `phone.py`, with a SHA-256 per partition (the CPU SHA-256 from kernel `fc4ab26`).
   - Where: `private/radio-backup/` on the Mac, never a repo.
   - Partition names and LBAs come from the GPT the driver already reads.
3. **List the firmware on the Mac:**
   - `modem_a` is FAT. With mtools, list `image/`: mba, the modem mdt/bNN files, `*.jsn`, `mcfg`, `qdsp6m.qdb`.
   - `dsp_a` the same way.
   - `vendor_a` is ext4: use `debugfs` to pull `etc/mixer_paths*.xml`, `etc/audio_platform_info*.xml` and
     `etc/acdbdata/*`.
4. **Check the carve-outs.** The table above lists them. Check that the Symbian RAM allocator never hands any of them
   out: the RAM banks in `bonito_variant/specific/pixel_bonito.cpp`, and the lastlog ring at `0x9e3e0000`, which sits
   just below qseecom.

Exit: hashes recorded in `private/radio-backup/SHA256SUMS`. The firmware file list and the carve-out check go into
this file.

**Done 2026-11-08** (kernel `1253e70` + `5c65051`):
- `blk dump <lba> <n>` (monitor) and `phone.py dump <partition> <file>`: 2.0 MB/s over the USB console, SHA-256 checked
  on the phone and on the Mac.
- No older backup existed.
- Backed up, hashes matching: `modemst1`, `modemst2`, `fsg`, `fsc`, `modemcal` (radio calibration, not in the first
  list), `persist`, `modem_a`, `bluetooth_a`.
  - `vendor_a` is not dumped: it comes from Google's factory image instead.
  - Test image: `USERSIDE=0 AUTOFASTBOOT=3600`, kernel only, eMMC read-only.
- GPT sectors:

  | Partition | Sectors |
  |---|---|
  | fsg | 27432..31527 |
  | modem_a | 299816..525095 |
  | modem_b | 525096..750375 |
  | fsc | 996480..996735 |
  | modemst1 | 1029632..1033727 |
  | modemst2 | 1033728..1037823 |
  | persist | 1037824..1119743 |
  | modemcal | 1123584..1127679 |
  | vendor_a | 14214144..15787007 |
  | bluetooth_a | 992384..994431 |

- Carve-outs: safe. Symbian's only RAM bank ends at `0x85700000` (`A64_BOOT_RAM_END`, hyp-mem), below every
  modem/DSP region. The lastlog ring ends exactly where qseecom starts. Any later growth of the bank must skip the
  carve-outs.
- Gate G4 now also covers `modemcal`.

### C1: Linux reference run (throwaway)

Why: it proves the network, the SIM and the firmware work on this phone before we write our own code. It also gives
us the exact sequences to reproduce.

- **Image:** a RAM-boot image with the ztOS mainline kernel and an initramfs-only root. It must not touch userdata,
  which holds NeoSymbian's C: and E:.
  - qrtr-ns and pd-mapper are in-kernel (ztOS `FIXES.md` #9).
  - Userland: tqftpserv, `rmtfs -o /run/rmtfs` on **copies** of the C0 dumps (the eMMC stays untouched),
    ModemManager + `qmicli` + `mmcli`, and the pmOS `ucm2/Google/sargo` VoiceCall profile.
  - Firmware: `modem_a` and `dsp_a` mounted read-only at the paths the kernel expects.
- **Tests:**
  1. register on 3G and LTE;
  2. outgoing and incoming calls (`mmcli -m 0 --voice-create-call`);
  3. SMS both ways;
  4. a data session;
  5. check whether call audio works on mainline sdm670 (**unverified**: voice needs a q6voice driver, which may be
     missing).
- **Capture, as facts for later stages:**
  - `dmesg` with `dyndbg` on `qcom_q6v5_mss`, `qcom_q6v5_pas`, `qcom_glink_smem`, `qcom_smp2p`: the order of the
    steps and the RMB status values;
  - `qrtr-lookup` (service, version, instance, node, port);
  - `qmicli -v` hex dumps for DMS/NAS/UIM/VOICE/WMS/WDS, saved as test vectors;
  - the APR traffic and the codec register writes (debugfs regmap), if audio works.
- **Go/no-go:** if Linux can't place a call with this SIM, find the cause first (network, firmware, provisioning).
  Don't write C2+ against an unknown.

**Result 2026-11-08: GO.** The recipe is in [telephony/c1-linux](https://github.com/NeoSymbian/telephony/tree/main/c1-linux)
(`build.sh`); the logs are in `private/c1/captures-*`.
- **Image:** pmOS `linux-postmarketos-qcom-sdm670` 7.2.3 + `firmware-google-sargo` 220505.008 (the same firmware as
  `modem_a`: no phone dump needed), Alpine userland, 105 MB boot.img, RAM disk only. Boot to an ssh shell takes about
  30 s.
- **Modem:**
  - MBA boot, MPSS load and handover in about 3 s; "up" at 9.8 s.
  - About 40 QMI services on QRTR node 0, among them VOICE 9 (v2), NAS 3, UIM 11, WMS 5, DMS 2, WDS 1, IMS 33/77
    and PDC 36.
  - Firmware MPSS.AT.4.0.2.c4.1-00145.
- **SIM (UCOM, Armenia):**
  - USIM ready, PIN1 off, plus an ISIM (the SIM can do IMS/VoLTE).
  - Registered on **LTE**, MCC 283 MNC 10, CS + PS attached.
  - The voice domain preference is `cs-only`, so calls use CSFB.
  - Signal RSRP -96 dBm (96 %).
- **Incoming call:** ModemManager answers. **Two-way audio confirmed by the owner** through the earpiece/speaker amps
  and the built-in mic (call 2: 41 s).
- **Still to do in C1:** an outgoing call, SMS both ways, mobile data, and the q6v5 dyndbg boot trace (that run's
  dmesg was cleared by mistake).
- **What it took:**
  - `/lib/modules` and `/lib/firmware` links plus `depmod` (the packages' scripts were skipped);
  - `root`/`messagebus`/`polkitd` users;
  - **polkitd** (ModemManager refuses `enable` without it: "authority not found");
  - `q6voiced hw:0,4`;
  - the VoiceCall mixer path set with `amixer` (`voice-route`), because `alsaucm` did not keep it.
  - On the Mac, the ECM interface needed a static 172.16.42.2 (udhcpd did not answer).
  - `qmicli` 1.39 has no voice dial or answer; ModemManager does.
- **The sequence to copy in C6** (from the UCM; register-level facts are in the captured `amixer contents`):
  1. VoiceMMode1 RX topology, then `SEC_TDM_RX_0 Voice Mixer VoiceMMode1` = 1;
  2. both CS35L36 amps enabled (gain/ramp settings in the UCM BootSequence);
  3. VoiceMMode1 TX topology, then `VoiceMMode1 Capture Mixer PRIMARY_TDM_TX_0` = 1 + the DMIC switches;
  4. open the VoiceMMode1 PCM both ways while the call is active (`q6voiced`).

### C2: kernel transport (done 2026-11-08, kernel `a5283de`)

All files are in `kernel/baseport/arm64/sdm670_assp/`: our own C++, with Apache-2.0 headers and "written from the
protocol as described by Linux `<file>`" comments. Everything is polled. GIC lines come later (C12), because
`A64_BindSpi` stops at INTID 255 (SPI 449 = INTID 481) and nothing sets edge triggering yet.

| File | What it does |
|---|---|
| `qcom_scm.cpp` | TrustZone SIP calls: yielding SMC64, function id `0x42000000 \| svc << 8 \| cmd`, x1 = arg info, x2..x5 args. Beyond 4 args, x5 points at an uncached page (it also holds `assign_mem`'s lists). Resumes interrupted calls (x0 = 1) and retries busy ones. `Scm_AssignMem`, `Scm_IsAvailable`. |
| `qcom_smem.cpp` | SMEM v12: the `$TOC` table, the global partition, and the apps↔remote partitions; item get/alloc under TCSR mutex 3 (`0x1f43000`). First-time init runs under a fast mutex, because the monitor and the boot thread raced and listed a partition twice. |
| `qcom_ipc.h` | The APCS doorbell `0x17990000 + 0xc`: bit 0 AOP, 12 modem GLINK, 14 modem SMP2P, 24/26 ADSP. |
| `qcom_smp2p.cpp` | Our out item (version 2, SSR-ack feature) and its entries; read in entries by name; version negotiation and the restart ack. |
| `qcom_qmp.cpp` | The AOP mailbox: the link/channel handshake, then 64-byte messages; 32-bit accesses only. |
| `qcom_glink.cpp` | GLINK over SMEM (item 478 = the 4 FIFO pointers, 479 = our TX FIFO 16 KB, 480 = the modem's): version, open/open-ack, intents (4 × 2 KB, regrown on request), TX_DATA/CONT, RX_DONE. Its own thread polls every 1 ms. |
| `qcom_telmon.cpp` | Monitor commands: `scm`, `smem`, `fw ls\|sha`, `smp2p [start]`, `qmp [modem on\|off]`, `mss [boot]`, `glink [hello]`. |

Measured on the phone:
- **TrustZone:** `assign_mem` and all the PAS calls are available.
- **SMEM:** partitions for the modem (1), the ADSP (2) and the CDSP (5).
- **SMP2P:** negotiated to version 1 with the SSR-ack feature.
- **QMP:** the handshake works, and `load_state` is acked.
- **Lesson: never read another host pair's SMEM partition** (entry 3 is 7↔5). The apps CPU stalls on the bus and the
  watchdog resets the phone. Check the hosts before touching a partition header.

### C3: modem boot (done 2026-11-08, kernel `a5283de`)

**The kernel reads the firmware itself:** `qcom_fat16.cpp` is a read-only FAT16 reader over the GPT (`modem_a` is FAT16
with 4096-byte sectors). There is no `rprocd` file loading and no `rproc.ldd`. It reads about 17 MB/s; `fw sha`
matches the Mac's hashes.

`qcom_mss.cpp` boots the modem on its own DFC thread, following the `sdm845_mss` flow (Linux `qcom_q6v5_mss.c`):
1. QMP `load_state modem on`. RPMh mx/cx/mss at their highest levels (corners 4/7/8; `Arc_Vote` now falls back to a
   rail's highest level).
2. Clocks (GCC, from `gcc-sdm845.c`):
   - proxy: prng (`0x152004` bit 13);
   - reset: iface `0x18a000`, snoc_axi `0x18a150`;
   - active: bus `0x18a154`, mem (boot ROM, `0x152004` bit 10), gpll0_mss (`0x152004` bit 17), mnoc_axi
     `0x18a004`.
3. The alt reset: PDC `0xb2e0100` bit 9 on → RMB `+0x44` = 1 → AOSS `0xc2b0000` = 1, 300 µs, = 0 → `+0x44` = 0 → PDC
   bit 9 off.
4. `MBA.MBN` into mba `0x95600000`. Then `assign_mem`: mpss and mba to MSS_MSA (VMID 15, RW). `RMB_MBA_IMAGE` = mba.
5. QDSP6 `+0x3c` sleep clock on → `+0x400` = 1 → `+0x404` = 1 → poll RMB `+0x40` bit 0 → PBL status (`+0x04`) 1 →
   MBA status (`+0x0c`) 1 or 2. **Got 2.**
6. `MODEM.MDT` = the 0x414-byte ELF headers + the 0x1d08-byte hash, i.e. the whole 8476-byte file. It goes in a
   contiguous buffer handed to the modem, then `+0x10` = its address and **command 1** (not 3: 3 is the *status*).
   Status 3.
7. 31 segments, all relocatable from `0x8b000000`, filling the 152 MB mpss exactly:
   - mpss is shared HLOS+MSS while loading and copied through 16 MB non-cacheable mappings; `MODEM.Bnn` for
     segment n; zero-fill segments 13/19/30;
   - code start = `0x8b000000` with **command 2** (not 4) on the first segment, then the length grows;
   - mpss goes back to MSS only. Status 4.
   - **158 MB in 5.9 s.**
8. SMP2P `slave-kernel` ready (bit 1). The mba carve-out returns to HLOS.
9. GLINK starts:
   - the modem opens `IPCRTR`, `glink_ssr` and `SSM_RTR_MODEM_APPS`;
   - after our QRTR HELLO (`glink hello`: node 1 → broadcast, control port), it sends `NEW_SERVER` control packets
     (type 4) from node 0.

**Exit met.** The modem boots under our kernel and talks QRTR.

Known gaps:
- **Handover (bit 2) never came within 5 s.** Linux on this phone logged "Handover signaled, but it already
  happened". Our proxy votes and clocks stay on anyway (shortcut).
- **The modem raises fatal (bit 0) about a minute after ready.** Nothing answers rmtfs/tqftp yet; C4 does.
  - No crash reason appeared in SMEM item 421: neither in the global partition nor in the modem's.
- **`mss stop` / crash recovery isn't wired up yet** (C7). `Stop()` exists for the failure paths.

Failure modes seen on the way:
- A data abort in the clocks step: a wrong GCC address doubled the base, `A64_Io` returned 0, and the write went
  through a null pointer.
- `KERN-COMMON 23` in the GLINK thread: `memclr` on a struct holding a `TBuf8` zeroes its max length.

### C4: modem services (Rust, user side) (done 2026-11-08)

One process, `MODEMD.EXE` (uid `0xE0003001`), from the Rust workspace
[NeoSymbian/telephony](https://github.com/NeoSymbian/telephony). The protocol code is the `no_std` crate `modem-proto`, tested on the Mac
with vectors from the C1 captures. The `symbian/modemd` glue talks to the kernel through `EHalGroupVariant`
functions 0x4e0d–0x4e12 (`qcom_telhal.cpp`; table in [rust-integration.md](rust-integration.md)). It doesn't use LDDs.
Started by hand for now: Terminal, `modemd`. Auto-start is decided in C5.

| Part | Work |
|---|---|
| QRTR | Node 1's router and nameserver over GLINK `IPCRTR`: HELLO, NEW_SERVER/NEW_LOOKUP, RESUME_TX for `confirm_rx`. Every service is a local port in the one process. Reference: linux-msm `qrtr` (BSD-3). |
| QMI | Header + TLVs. A small client asks DMS for the revision and the IMEI (masked in the log), and UIM for the card status. |
| rmtfs | QMI service 14: open (`/boot/modem_fs1` = modemst1, `fs2`, `fsg`, `fsc`; `fsg_oem_1/2` refused as under Linux), alloc_buf (`0xfc201000`), rw_iovec. **`phys_offset` is a physical address** (0xfc201200), not an offset into the buffer. The partitions are read once at start through the read-only HAL op `PartRead`. **`shortcut:` writes stay in RAM until gate G4.** Reference: linux-msm `rmtfs` (BSD-3). |
| locator | QMI service 64, v1, instance 1: Linux's sdm670 pd-mapper table (modem root_pd + wlan_pd, ADSP audio_pd, CDSP). The domain list is sent only when the service is known. |
| TFTP | QRTR service 4096: `/readwrite/` writes are kept in RAM and reads refused. Linux refused the same reads (`modem_efs`, `ota_firewall/ruleset`, `mcfg.tmp`, `mbn_*.dig`). |

**What the modem needs from the apps side** besides these services:
- **SMEM item 134** (`SMEM_ID_VENDOR0`, global partition, 32 bytes): the Pixel's board record `{version 0,
  modem_flag 0, major_id, minor_id, subtype, platform, efs_magic 0, ftm_magic 0}`.
  - It comes from socinfo (item 137): `platform` = `hw_plat` (+0x34), `major/minor` = bytes 2 and 0 of `plat_ver`
    (+0x38), `subtype` = `hw_plat_subtype` (+0x40).
  - Without it, the modem's RF task faults 0.5 s after ready, right after COEX (34) registers:
    `:0:[rf]EX:kernel:0:rf:171:PC=d949b6d4`. Handover never comes.
  - The fact comes from the pmOS sdm670 kernel's `google,modemsmem` driver (DTB `modemsmem { qcom,smem = <134>; }`).
    The kernel writes the item before the MBA (`qcom_mss.cpp` `BoardInfo`).
- The LLCC slices, the XO vote, and GLINK started at "ready" all match what Linux does. Voting every BCM to the top
  crashed the SoC and was dropped.

Result on the phone (kernel `tel-c4` 41b8ddb, telephony `be6b566`):
- handover 560 ms after ready;
- 40 modem servers registered, the same set as Linux;
- DMS returns `MPSS.AT.4.0.2.c4.1-00145` and the IMEI (masked);
- UIM reports the card present;
- no fatal after 10 minutes.

Exit:
- the modem stays up 10 minutes with no fatal;
- QMI DMS answers the revision and the IMEI (masked in the log);
- UIM reports the SIM present.

### C5: QMI + modemsrv + dialer (no audio)

- **QMI clients:**
  - DMS: operating mode online / low-power, revision, IMEI.
  - UIM: card status, PIN verify, ICCID.
  - NAS: system selection (auto, LTE preferred, 3G allowed), serving system, operator name, signal info,
    indications.
  - VOICE: indication register, dial, answer, end, all-call-status indication, get-all-call-info, start/stop DTMF.
- **`modemsrv`** (Rust Symbian server): owns the QMI clients. Its IPC API for apps:
  - `Status` → operator, technology (3G/LTE), bars, SIM state;
  - `Dial(number)`, `Answer`, `Hangup`, `SendDtmf`;
  - a notification stream: incoming call with number, call state changes, registration changes.
- **neoui:** the status bar shows the operator and the bars. A dial pad, the incoming-call screen, the in-call screen
  (timer, hang up).

Exit: the status bar shows the operator and the bars; an outgoing call rings the owner's other phone; an incoming call
shows the number and can be answered and hung up. This needs the owner to place and answer test calls.

### C6: call audio (= roadmap H5 for voice)

1. **ADSP boot** (`qcom_pas.cpp`): PAS flow through `qcom_scm.cpp`:
   1. QMP `load_state adsp on`, then PAS `init_image` with the `.mdt` metadata;
   2. `mem_setup`, copy the segments into `0x95800000`, then `auth_and_reset`;
   3. wait for SMP2P lpass ready and handover.
2. **Services:**
   - The GLINK edge "lpass" comes up. QRTR also runs on it, and pd-mapper must serve `avs/audio` or the audio PD
     never starts.
3. **APR client** (Rust crate `apr`) on the GLINK channel `apr_audio_svc`. APR services: CORE 3, AFE 4, ASM 7,
   ADM 8, MVM 9, CVS 10, CVP 11 (Linux `apr.h`).
   - q6core: wait for ready.
   - AFE: set the LPASS clocks (internal codec MCLK 9.6 MHz), start the RX and TX ports used by the internal codec.
     The port IDs come from C1 or the pmOS UCM.
   - Voice (Linux q6voice / Android `msm-voice` as reference):
     1. MVM creates the passive control session "default modem voice", and CVS creates the passive stream session of
        the same name;
     2. CVP creates the full control session on the RX/TX AFE ports;
     3. MVM attaches the vocproc and starts voice. The modem then streams call audio to the ADSP by itself.
4. **Codec and amps** (corrected by C1):
   - Earpiece/speaker: the two **CS35L36** amps over I2C (bus 2, 0x40/0x41) on `SEC_TDM_RX_0`. Reuse the GENI I2C
     driver (`qcom_geni_i2c.cpp`). Linux `cs35l36.c` serves as reference.
   - Mic: the DMIC on `PRIMARY_TDM_TX_0`.
   - The AFE ports to start are the TDM ones, not the internal codec. The PM660L analog codec is only for the jack.
   - Values come from the pmOS UCM VoiceCall profile and C1's `amixer contents` capture, as facts.
5. **Calibration:** ACDB is optional at first. Without it, expect quiet or echoey audio; note it in known-issues.

Fallback if this stalls: port Linux q6afe/q6voice and the msm8916-wcd codec drivers directly (GPL, allowed).

Exit: **a two-way call through the earpiece**, both directions, with the owner on the other phone.

Failure modes:
- q6core never ready: the audio PD did not start (pd-mapper), or the ADSP crashed (SMEM crash reason item for
  lpass).
- The call connects but is silent: AFE port not started, wrong port IDs, codec not powered, or MVM not attached to
  the modem session.

### C7: complete calls

- **Ringing:**
  - a ringtone file played through ASM → ADM → AFE to the loudspeaker;
  - the speaker path follows the pmOS UCM (whether it is the PM660L speaker driver or an external amp is
    **unverified**);
  - vibration through PM660 haptics (roadmap H6);
  - a missed-call notification.
- **In-call:**
  - mute (CVS mute), DTMF;
  - hold/resume, call waiting, swap and merge (QMI VOICE manage-calls);
  - a speakerphone switch (CVP device change).
- **Proximity:** the sensor is served by the ADSP sensor PD over FastRPC (ztOS needed `hexagonrpcd`), which is a large
  piece of work. **Fallback (my call):** turn the screen off when a call is answered and turn it on with the power
  key, until a FastRPC client exists.
- **Wired headset:** USB-C analog audio (the codec MBHC plus the USB PHY mux); last in this stage.
- **Robustness:**
  - On SMP2P fatal or the watchdog, `rprocd` stops the modem, reloads it and restarts the services, and `modemsrv`
    reconnects. The UI shows "no service" meanwhile.
  - Airplane mode = DMS low-power.
  - SIM PIN prompt, SIM removed and inserted.

Exit: a day of normal use with calls and no reboot.

### C8: call log and contacts

- `modemsrv` writes the call history to `C:\private\<modemsrv uid>\calls.db`.
- A small Rust contacts store, plus vCard import from `E:`. The old Symbian contacts model is used only if C12's ETel
  work makes old apps matter.
- neoui Recents and Contacts apps. The dialer and the incoming-call screen look up names.

Exit: an incoming call from a saved number shows the contact's name.

### C9: SMS

- QMI WMS:
  - receive (MT indications, read + delete from modem storage);
  - send (PDU mode, our own GSM-7/UCS-2 encoder);
  - concatenated messages, delivery reports;
  - the SMSC from the SIM.
- Messages are stored in `C:\private\<modemsrv uid>\sms\`. neoui Messages has threads and notifications.
- The Symbian SMS stack is not used.

Exit: an SMS round-trip with the owner's phone, including Armenian and Cyrillic text and a 300-character message.

### C10: mobile data

- **Control:** QMI WDS (start network interface, APN from settings), WDA (QMAP data format), and the IPA QMI
  handshake with the modem (Linux `ipa_qmi.c`).
- **Data path, kernel C++:**
  - the IPA hardware: load `ipa_fws.mbn` through PAS, GSI channels and rings, and the IPA SMMU context (stream IDs
    0x720/0x722);
  - rmnet/QMAP framing.
  - Reference: Linux `drivers/net/ipa`.
  - **Risk:** the first SMMU work in the port.
- **Symbian side:** an ESOCK/TCPIP6 packet interface (NIF) over the rmnet device. It needs `commsfw`,
  `networkingsrv` (ESOCK/TCPIP6) re-forked from `retired-repos.md`; **ask the owner first.**
- **Fallback:** a small Rust IP stack (smoltcp) behind our own socket API, if the 2010 stack costs too much.

Exit: ping and an HTTP fetch over LTE, and over 3G with LTE disabled.

### C11: VoLTE (stretch, go/no-go)

- **Question:** can the modem's internal IMS register when the carrier's MCFG profile is selected (QMI PDC), the IMS
  settings are written (QMI IMSS/IMSA), and an IMS APN data session is up (WDS)?
- **Test** on the C1 Linux setup first: how far postmarketOS sdm845-family ports have got is the reference.
- **Yes:** calls go through the same VOICE service and C6 audio path.
- **No:** record it here. Calls stay on CSFB/3G and stop working when the network turns 3G off.

### C12: persistence, power, compatibility

- **G4 (owner's OK):**
  - rmtfs writes the EFS back the way Android does: alternate between `modemst1` and `modemst2`, sync on the modem's
    request;
  - `fsg` stays read-only;
  - only after a verified C0 backup.
  - Until G4 the modem relearns its network caches every boot. Nothing else breaks.
- **Power** (needs roadmap H3 suspend):
  - drop our RPMh votes when idle;
  - the AP suspends with the modem registered;
  - SMP2P/GLINK interrupts wake it for calls and SMS.
  - Exit: idle overnight with a SIM, and an incoming call still rings.
- **ETel (optional):** if old Symbian apps need telephony, a thin C++ TSY over `modemsrv` after re-forking
  `cellularsrv` (ask first).
- **Out of scope:** eSIM, MMS, Bluetooth call audio (comes with P4 Bluetooth), emergency-call guarantees.

## Code layout

| Where | What |
|---|---|
| `kernel/baseport/arm64/sdm670_assp/` | `qcom_scm`, `qcom_smem`, `qcom_ipc`, `qcom_smp2p`, `qcom_qmp`, `qcom_glink`, `qcom_mss`, `qcom_pas`, IPA (C10), the LDDs `glink`, `rproc`, raw read-only partition op |
| `kernel/.../a64_medblk.cpp` | Read-only drives for `modem_a`/`dsp_a`; G4 write path for `modemst1/2` (C12) |
| `kernel/.../pixel_bonito.cpp` | MMU entries for SMEM, rmtfs, QMP, APCS, codec; RAM bank carve-out check |
| [`telephony`](https://github.com/NeoSymbian/telephony) (Rust) | `qrtr`, `qmi`, `rmtfs`, `pdmapper`, `tqftp`, `rprocd`, `apr`, `modemsrv` |
| `neoui` | status bar, dialer, in-call, Recents, Contacts, Messages |

## Testing

- **Rust protocol crates:** `cargo test` on the Mac, with the C1 captures as vectors (QMI, QRTR, APR, rmtfs
  requests).
- **Kernel:** each stage builds for QEMU too (`neo kernel qemu`, `neo qemu 60`), so nothing regresses. The hardware
  parts are tested on the phone:
  `AUTOFASTBOOT=600 DTB=../private/bonito.dtb neo kernel bonito`, `phone.py run IMG --stay`, then `phone.py cmd …`.
- **Calls need the owner:** the call and SMS exit tests need someone at the other phone.

## Sources and licences

| Source | Licence | Use |
|---|---|---|
| linux-msm `qrtr`, `rmtfs`, `pd-mapper`, `tqftpserv` | BSD-3-Clause | May be ported closely; keep the copyright line in the ported file |
| libqmi `data/qmi-service-*.json` | LGPL-2.1 (data) | Message IDs and TLV layouts, as facts |
| Linux `qcom_scm`, `qcom_q6v5_mss`, `qcom_q6v5_pas`, `qcom_glink_*`, `qcom_smp2p`, `smem`, `qcom_aoss`, `apr`, `q6afe`, `q6asm`, `msm8916-wcd-*`, `drivers/net/ipa` | GPL-2.0 | Reference. A direct port is allowed if a stage stalls; that file is then GPL-2.0 and listed here |
| pmOS/msm8916-mainline `q6voice` | GPL-2.0 | Reference for C6 |
| Android `mixer_paths*.xml` (phone's vendor partition) | proprietary | Register values as facts, read from the phone; never copied into a repo |
| Qualcomm firmware (`modem_a`, `dsp_a`) | proprietary | Loaded from the phone at runtime only |

Direct GPL ports so far: none.

## Status

| Stage | State |
|---|---|
| C0 | **done 2026-11-08**: radio partitions backed up, firmware listed, carve-outs safe |
| C1 | **GO 2026-11-08**: modem up, LTE on UCOM, an incoming call with two-way audio under mainline Linux; outgoing call, SMS, data still to test |
| C2 | **done 2026-11-08** (kernel `a5283de`): SCM, SMEM, SMP2P, QMP, GLINK, monitor commands |
| C3 | **done 2026-11-08**: the kernel boots the modem from `modem_a` and talks QRTR; the modem dies after ~1 min without rmtfs (C4) |
| C4 | **done 2026-11-08**: `MODEMD.EXE` serves rmtfs, the locator and TFTP; the modem reaches handover and stays up (SMEM item 134 was the missing piece); DMS + UIM answer |
| C5–C12 | not started |
