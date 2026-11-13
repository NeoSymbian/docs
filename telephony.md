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
| C4 | Modem services | Modem stays up; DMS returns the revision (**done** 2026-11-08) |
| C5 | QMI + modemsrv + dialer | Calls ring and can be answered, with no audio yet (**done** 2026-11-09) |
| C5b | IPA (the first half of C10, moved earlier) | The modem stays up on LTE while packet data arrives |
| C6 | Call audio | **Two-way call audio on the earpiece: the first win** (**done** 2026-11-09) |
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
  happened". (Since C4 it comes about 0.55 s after ready; since C6 the proxy votes are released then, as Linux.)
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

### C5: QMI + modemsrv + dialer (no audio) (done 2026-11-09)

**What was built:**
- **MODEMD.EXE is the `modemsrv`.** A separate server process would need a QRTR socket API between processes, so the
  QMI clients live in MODEMD. It serves the IPC server **`NeoModem`** (v1.0; the contract is the `no_std` crate
  `modem-ipc` in the telephony repo):
  - `STATUS` returns a fixed 74-byte snapshot: modem state, SIM, registration, technology, bars 0–4, operator, and
    one call `{id, state, incoming, number}`;
  - `DIAL(number)`, `ANSWER` and `HANGUP` complete with `KErrNone`, `KErrNotReady`, `KErrArgument` or
    `KErrInUse`.
- **Auto-start.** neoui's SYSSTART spawns MODEMD at boot (`symbian/src/phone.rs`); in NeoSymbian it holds the system
  starter's role. A second MODEMD finds the server name taken and exits. A ROM without MODEMD (QEMU, CI) gets a
  phone-less shell.
- **The shell:**
  - it polls `STATUS` once a second;
  - the status bar shows the operator (where the title is empty), "LTE"/"3G"/"2G" and the bars;
  - the Phone screen dials, answers and ends calls;
  - an incoming call opens the call view.
  - `shortcut:` a 1 s poll instead of an async notify (C7).
- **QMI clients** (`modem-proto`): one client per service, each with its own port, a transaction counter and its
  pending requests. Responses are matched by transaction, and indications are routed.
- **Dial safety:** numbers with fewer than 5 digits are refused, so tests can't reach 112/911/101–104. **Don't rely on
  this phone for emergency calls.**

**QMI facts used.** Ids come from libqmi's JSON. † marks a fact checked against the C1 capture or the phone.

| Service | Message | Layout |
|---|---|---|
| DMS 2 | Set Operating Mode 0x2E† | TLV 0x01 = 0 (online). Answers error 52 when the modem is already online. |
| UIM 11 | Card Status 0x2F† | TLV 0x10: 4 × u16 session indexes, a card count, then per card the state first (1 = present) |
| NAS 3 | Register Indications 0x03 | 0x13 serving system, 0x19 signal info |
| NAS 3 | Serving System 0x24† | Response and indication. TLV 0x01 `{reg, cs, ps, net, n, radio[n]}` (radio 4 GSM, 5 UMTS, 8 LTE); 0x10 roaming (0 = on); 0x12 PLMN `{u16 mcc, u16 mnc, len, name}` |
| NAS 3 | PLMN Name 0x44† | Request `{u16 mcc, u16 mnc}`. Answer: 0x10 SPN, then the short and long names `{enc, ci, spare, len, str}` |
| NAS 3 | Signal Info 0x4F / indication 0x51† | LTE 0x14 `{i8 rssi, i8 rsrq, i16 rsrp, i16 snr}`; WCDMA 0x13 `{i8 rssi, i16 ecio}`; GSM 0x12 `{i8 rssi}`. **On 3G an invalid LTE TLV still comes**, so read only the current technology's TLV |
| NAS 3 | System Selection 0x33 / 0x34† | Mode 0x11 (u16 mask), service domain 0x18 (u32, 0 = CS only), duration 0x17 (0 = until power cycle) |
| VOICE 9 | Indication Register 0x03† | 0x13 call notifications |
| VOICE 9 | All Call Status indication 0x2E† | TLV 0x01 `n × {id, state, type, dir, mode, multipart, als}`; 0x10 numbers `{id, pi, len, digits}`. States 1 origination, 2 incoming, 3 conversation, 4 cc-in-progress, 5 alerting, 8 disconnecting, 9 end, 10 setup |
| VOICE 9 | Dial 0x20†, End 0x21†, Answer 0x22† | Dial TLV 0x01 = the number in ASCII; the answer's TLV 0x10 is the call id. End/Answer TLV 0x01 = the call id. Answer is refused during setup. |

**Lessons from the phone:**
- **QRTR flow control covers control packets too.** The modem marks packets `confirm_rx` and waits for RESUME_TX.
  MODEMD at first confirmed only data packets, so the modem's NEW_SERVER announcements stalled and DMS or UIM went
  missing at random. Now every packet type is confirmed, as Linux does.
- **The modem asserts in its IPA path once LTE packet data flows:**
  `ipa_dl_opt_lte.c:431:[lte_rlc_dl]IPA Assert: new_free_space > 0`. Nothing on the AP runs IPA yet.
  - **Interim, `VOICE_ONLY` in `modem-proto`:** once the modem has registered, MODEMD asks NAS for GSM/UMTS with CS
    only, until a power cycle (nothing is persisted). Calls work on 3G, and packet data stays detached.
  - Sending that request as soon as NAS appeared was refused (error 25), and the modem never brought up UIM.
  - C5b removes the interim mode.
- Calls on LTE drop to 3G (CSFB) and come back afterwards, as under Linux. VoLTE is C11.

**Result on the phone:**
- MODEMD started by SYSSTART;
- registered with "Ucom AM" (LTE, then 3G voice-only), with bars;
- an outgoing call rang the owner's phone;
- an incoming call showed the number, was answered and hung up;
- the calls were silent, as expected until C6.

### C5b: IPA (the first half of C10, moved earlier) (done 2026-11-09, kernel `d003355`)

The modem needs the AP to run IPA, the hardware that moves packets between it and the AP, even with no data call:
on LTE, an idle IPA makes the modem assert (C5). The facts come from Linux `drivers/net/ipa` (GPL, reference only).
On sdm670 that is IPA v3.5.1, the sdm845 data.

What runs now:
- **Firmware:** `vendor_a` holds the factory `/vendor/firmware` as an ext4 (written by NeoSymbian's `blk put`,
  verified by readback). MODEMD reads `ipa_fws.*` with the `ext4ro` crate and passes it to HAL `IpaStart` 0x4e13.
  The kernel's `qcom_pas.cpp` loads it into ipa-fw `0x97a00000` as **PAS id 15**. The `.mdt` is used as is: the
  hash segment's `.b01` must not be placed over it.
- **Kernel** (`qcom_ipa.cpp`, `qcom_smmu.cpp`), in Linux's order, before MODEMD boots the modem:
  - RPMh votes: SN10 and SN1 only, plus IP0 = 1875 (75 MHz / (unit 40 × 1000)). Voting the shared DDR/NoC BCMs
    from the AP's DRV replaces the whole AP's vote (a data abort);
  - an identity SMMU context for streams 0x720 and 0x722;
  - ipa_config;
  - GSI event rings 0/1 and channels 4 (AP_COMMAND_TX→ep5) and 5 (AP_LAN_RX→ep9);
  - the immediate commands (header, processing-context and modem SRAM init; route/filter tables);
  - LAN_RX buffers and the default route;
  - a 1 ms poll that recycles LAN_RX and answers the modem's SMP2P clock query.
- **MODEMD:** with IPA up, it serves the IPA QMI service (0x31, instance 1), sends INIT_DRIVER to the modem's
  instance 2, and doesn't set voice-only. The modem attaches on LTE.

The bugs that held it up, all fixed:
- **RPMh:** the TCS message length was 4, not 8; every vote was acked and none applied.
- **SCM:**
  - the resume path must pass `x6` back;
  - `x7 = 0`;
  - one call at a time.
- **SMMU, under the hypervisor:**
  - **only exact stream matches are used** (one SMR per stream, mask 0); a masked SMR was ignored, and IPA's reads
    never reached our context;
  - **the table must start at level 0** (T0SZ 16, a table descriptor → level-1 1 GB blocks). A T0SZ 32 table with
    blocks at the top faulted at level 0;
  - both were found by diffing against Linux's live context bank (C1, `/dev/mem` after pinning IPA's runtime PM
    on: reading GSI or IPA with IPA suspended stalls the CPU, and the GSI global area always stalls).

Checked on the phone (2026-11-09):
- about 20 minutes on LTE (the 30-minute run was cut short);
- an incoming and an outgoing call, each CSFB to 3G and back to LTE;
- no modem fatal;
- GSI error log 0, and channels 4/5 started.

Open, needed for data (C10):
- **The IPA QMI handshake is half done.** The modem sends INDICATION_REGISTER, but it hasn't answered INIT_DRIVER
  or sent DRIVER_INIT_COMPLETE, and IPA shows no uC-loaded interrupt.
- The AP_MODEM_TX/RX endpoints (ch3/ch6) aren't set up yet.

### Network time (NITZ) (done 2026-11-13)

MODEMD subscribes to NAS Network Time (Register Indications TLV 0x17; indication 0x4C) and asks for it once on
registration (Get Network Time 0x7D, its 3GPP TLV 0x11). Layouts are from libqmi `qmi-service-nas.json`:
- universal time {u16 year, month, day, hour, minute, second, day of week};
- the zone in quarter hours (daylight saving included);
- the daylight saving hours.

The value goes to clients in the NeoModem status (`modem_ipc::Nitz` in bytes 102..110; `Status::SIZE` is unchanged).
neoui sets the clock from it (docs neoui-shell.md Part 5).

**Phone:** Ucom AM on LTE sends it right after registration: `zone 16 quarter hours` = UTC+4.

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

**Result 2026-11-09: done** (kernel `b12d1ba`, telephony `3f4af12`, neoui `2d55d01`).
- **The result on the phone:**
  - calls connect (CSFB to 3G) with two-way audio on the earpiece and the loudspeaker;
  - Mute, Speaker, the volume keys and in-call DTMF work;
  - Dev tools → Audio loops the mic back to the loudspeaker or the earpiece with no call (an AFE loopback).
- **As built:**
  - the kernel boots the ADSP (PAS 1, streamed from `vendor_a` by MODEMD) **before the modem**, and opens its
    `IPCRTR` and `apr_audio_svc`;
  - APR runs in Rust (`modem-proto/src/apr.rs`), as one state machine (Off / Call / Test) that never cuts a sequence
    short;
  - the codecs are a kernel board driver (`a64_audio.cpp`, HAL 0x4e18).
- **What it took, each found against a kprobe trace of a working Linux call (C1 image + `apr_send_pkt` /
  `apr_callback` kprobes):**
  - **SSCTL events**, as Linux sysmon: the modem hears `{"adsp", after powerup}` and the ADSP `{"modem", …}` (QMI
    service 43 v2, instances 0x12 / 0x14, message 0x23).
  - **Linux's order.** The mic's clock and port start before the voice sessions; the speaker's port starts after
    START_VOICE. With both ports started first, START_VOICE was never answered.
  - **The voice path stops at END**, not at "disconnecting". Stopping earlier overlapped the modem's own teardown
    with the ADSP, and the ADSP stopped answering.
  - **The built-in topologies** 0x10F71 / 0x10F77. C1's UCM ids (0x1000FFFC / 0x10010F87) commit under Linux, but
    here they fail (status 1) even with Linux's exact bytes.
  - **Both amps on TDM slot 0.** The AFE channel map {0, 4} is in byte offsets, so channel 2 lands in slot 2 and
    Bottom on slot 1 was silent. Analog gain 17 and 0 dB digital, Linux's live values (`0x6C04 = 0x633`,
    `0x6000 = 0x8000`).
  - **GLINK** opens our side of a remote-opened channel only when it is used here. A full remote-intent table now
    drops its smallest idle intent.
  - **The modem's proxy votes** (mss/mx/cx at their highest, xo) are released at handover, as Linux's
    `qcom_msa_handover`. Held, they made the modem assert in `rpmh_image_os.c:162` after voice calls.
  - **e32's `sleep`/`delay` take microseconds.** MODEMD passed milliseconds, so its send retry to a busy modem gave
    up after a few ticks and dropped the hangup.
  - The loopback test stops its speaker port before its mic port; the other order jammed the AFE.
- **Open** (`known-issues.md`):
  - after a connected call the modem stays on 3G (Linux: back on LTE 1.7 s after the call). **Fixed 2026-11-12**
    (kernel `69bb4cd3`): the codec's rails were voted on the wrong PMIC (`known-issues.md`);
  - no ACDB calibration.

### C7: complete calls

**Implementation scope agreed 2026-11-10:** one integrated deliverable on
`feat/c7-complete-calls` in the existing repositories. Implement first, then one
final build/test/independent-review pass, followed by owner-assisted phone testing.
No worktrees, duplicate source trees, or replacement build/phone scripts.

- **Ringing:**
  - one original built-in PCM ringtone through ASM → ADM → AFE to the loudspeaker,
    with ring volume, silent and vibration controls;
  - reuse C6's CS35L36 speaker path and its single APR/audio owner;
  - vibration through **TI DRV2624**, I2C10 at 0x5a, reset GPIO24 (roadmap H6, [driver support D3](driver-support.md));
  - a missed-call notification.
- **In-call:**
  - preserve C6's working mute, DTMF, volume and speaker controls;
  - hold/resume, call waiting, swap and merge (QMI VOICE manage-calls);
  - track all calls by modem call ID; ending one must not end another's audio;
  - asynchronous status notification and visible pending/error results.
- **Proximity:** the sensor is served by the ADSP sensor PD over FastRPC (ztOS needed `hexagonrpcd`), which is a large
  piece of work. **Fallback (my call):** turn the screen off when a call is answered and turn it on with the power
  key, until a FastRPC client exists.
- **Screen:** main's D2 panel driver alone (timeout, Power key). No earpiece blanking until there is a proximity
  sensor (owner, 2026-11-12: the C7 draft blanked the screen in earpiece calls with only Power to wake it).
- **Wired headset:** deferred by the owner for C7. The board's analog jack is
  3.5 mm, as recorded in C1; the earlier USB-C analog requirement was unverified.
- **Robustness:**
  - MODEMD owns modem and ADSP recovery (the logical rprocd/modemsrv roles remain
    in this one process). Keep NeoModem responsive and show recovering/no service.
  - Quiesce GLINK/SMP2P, invalidate stale rings and APR handles by generation,
    confirm shutdown/ownership before memory reuse, then reuse the existing loaders.
    Preserve RAM EFS. Replay retained ADSP services/SSCTL after modem-only recovery.
  - Three automatic recovery attempts, backoff 1/3/10 seconds, then visible failure
    with manual retry. ADSP failure uses coordinated ADSP-before-modem recovery.
  - Airplane mode = DMS low-power; preserve desired state through SIM/recovery events.
  - SIM PIN prompt and retry counts, SIM removed/inserted; never store or auto-retry PINs.
  - Fix the post-connected-call return-to-LTE issue in `known-issues.md`; no forced
    radio cycling presented as a root-cause correction.

**Hardware correction:** the C1 reference image's embedded bonito DTB enables
`samsung,sofef00-bonito` (DSI 0x0ae94000, reset GPIO75) and `ti,drv2624` on
`i2c@a88000`. PM660L WLED and PM660 haptics are disabled. This supersedes the
earlier H4/H6 guesses; derive command/register semantics from primary references.

**Implementation order and source ownership:**

1. Telephony locks IPC v2 in `crates/modem-ipc/src/lib.rs`; update MODEMD,
   SYSSTART and Dev tools together. Keep all shared contracts in the existing crate.
2. Kernel adds lifecycle/reset and safe PCM ownership through the existing
   `qcom_mss`, `qcom_adsp`, `qcom_glink`, `qcom_smp2p`, `qcom_telhal` paths.
   MODEMD builds recovery around them before new audio users are integrated.
3. Telephony extends VOICE/UIM/DMS and existing APR; neoui consumes confirmed
   status in its existing phone client, Phone screen, Settings and shade.
4. Integrate ringtone/vibration and OLED state transitions, preserving every C6
   sequencing constraint above. Persistent call history/contacts remain C8.
5. Final host/ARM builds, QEMU boot evidence, bonito build and fresh independent
   review. Push coordinated feature commits and dependency pins. Phone tests then
   validate behavior; record exact commands, exit codes, artifacts and gaps.

Exit: a day of normal use with calls and no reboot, plus successful recovery,
physical screen-off/wake and LTE return. Code completion alone is not this exit.

**Implementation candidate 2026-11-10 (phone acceptance pending).**

| Repository | Commit | Main implementation |
|---|---|---|
| kernel | `8dbcc89f` | [Recovery HAL](https://github.com/NeoSymbian/kernel/blob/8dbcc89f1ddd83871140f818d880e1cdc9731f01/baseport/arm64/sdm670_assp/qcom_telhal.cpp#L439), [OLED](https://github.com/NeoSymbian/kernel/blob/8dbcc89f1ddd83871140f818d880e1cdc9731f01/baseport/arm64/bonito_variant/specific/a64_panel.cpp#L105), [haptics](https://github.com/NeoSymbian/kernel/blob/8dbcc89f1ddd83871140f818d880e1cdc9731f01/baseport/arm64/bonito_variant/specific/a64_haptics.cpp#L92) |
| telephony | `63a2b1f9` | [IPC v2](https://github.com/NeoSymbian/telephony/blob/63a2b1f900bf9b45af42613f5e316ffacd557646/crates/modem-ipc/src/lib.rs#L17), [MODEMD recovery](https://github.com/NeoSymbian/telephony/blob/63a2b1f900bf9b45af42613f5e316ffacd557646/symbian/modemd/src/lib.rs#L230), [APR](https://github.com/NeoSymbian/telephony/blob/63a2b1f900bf9b45af42613f5e316ffacd557646/crates/modem-proto/src/apr.rs#L414) |
| neoui | `bf930514` | [Async modem client](https://github.com/NeoSymbian/neoui/blob/bf9305140eaf004ee041604a0188175aee0004bc/symbian/src/phone.rs#L27); Phone, Settings, shade and Dev tools updated together |
| build | `b52e502a` | Kernel pin and default-off diagnostic option; existing `build.sh`, `neo` and `phone.py` remain the build/run path |

- IPC v2 reports up to eight calls, pending/errors, SIM PIN attempts, desired and
  confirmed radio mode, ring settings and recovery generation. Old IPC major versions
  are rejected; install MODEMD and SYSSTART together. Settings are saved under
  MODEMD's private directory, PINs are not saved or logged.
- Recovery retains RAM EFS and a quiescent healthy ADSP. A fatal during unfinished
  voice/ringtone teardown requires coordinated recovery; `Off` alone does not prove
  the DSP has relinquished resources. SMP2P generations rearm IPA clock replies.
- Review corrected mutex initialization/ordering, DRV2624 identification, stale
  SMP2P writes, both delayed-DIAL cancellation orderings and failed codec controls.
  The final independent source review found no remaining blocking/high/medium issue.
- **Still open:** the connected-call LTE retention has no established root cause or
  corrective change. APR's successful voice teardown is preserved. This candidate
  must return to LTE after ordinary END/acknowledged teardown **without recovery**
  before C7 can be accepted; recovery after every call is not a fix.
- Hardware checks remain pending: ASM/ADM/PCM mapping and audible ringtone, physical
  OLED off/on (unknown DSI revisions fail explicitly), DRV2624 vibration, actual
  modem/ADSP restart and carrier-supported multi-call behavior.

**Integration with main (2026-11-12, review by Claude; phone acceptance still pending).** The six C7 branches
were merged with main (driver support's ADSP-first MODEMD, Wi-Fi W0–W4, display D2, battery, keyboard):

| Repository | Merge commit |
|---|---|
| telephony | `a872947` |
| kernel | `7075c11a` |
| neoui | `a525dee` |
| build | `9c8697d` (pins kernel `7075c11a`; move to kernel main's merge commit when the kernel PR merges) |

- **HAL numbers:** C7's RprocStop/RprocState/AudioMem/Haptic were drafted at 0x4e1a–0x4e1d, already main's
  BatteryRead/FwRead/WlanMsa/WlanStart (in the kernel and inside MODEMD itself): now **0x4e24–0x4e27**.
- **Lifecycle:** main's ADSP-first daemon stays (the ADSP serves audio before and without the radio; an ADSP
  failure never stops the radio); C7's recovery runs only for a running modem, never during a stop, and a modem
  stop keeps the ADSP's servers and queued replies. A modem stop also takes Wi-Fi down until a reboot (its firmware
  runs inside the modem; [wifi.md](wifi.md)).
- **Screen:** main's D2 driver is the only panel owner; C7's `a64_panel.cpp` and earpiece blanking are dropped
  (no proximity sensor yet). The exit item "physical screen-off/wake" is D2's.
- **Bugs fixed** (tests where the logic is host-testable): Set Operating Mode resent every 2 s after a refusal
  (bounded to 3 per intent; NAS registration means online); the airplane intent not saved when the radio could not
  follow yet; SIM PIN attempts read as 0 after a recovery; FATAL acted on every step (rising edge now); an ADSP-only
  restart booting a running modem; ringtone preparation retried every 10 ms; a kernel `kumemget` under a critical
  section and mutex (AudioMem); the modem watcher spinning without MODEMD; "Modem connection lost" at every boot;
  the call view stuck after a reconnect; the SIM prompt with no way out (Emergency call, Not now); CANCEL_NOTIFY
  after every notification; C7's and main's clippy errors (syborg CI).

**Final source checks (all exit 0):**

| Checkout | Commands | Result |
|---|---|---|
| telephony | `cargo fmt --all --check`; `cargo clippy --offline -- -D warnings`; `cargo test --offline` | 79 tests: 4 ext4ro, 3 IPC, 72 modem-proto |
| telephony/symbian | `cargo fmt --all --check`; `cargo arm --workspace --offline` | `libmodemd.a` built |
| neoui | `cargo fmt --check`; `cargo clippy --all-targets --offline -- -D warnings`; `cargo test --offline` | 126 tests |
| neoui/symbian | `cargo fmt --all --check`; `cargo arm --workspace --offline` | All apps built; final build uses the pushed IPC revision, without a local patch |

Raw repair host evidence is local/private at `private/c7/repair-telephony-*.log`,
`private/c7/repair-neoui-*.log` and `private/c7/repair-phone-selftest.log`. Kernel/ROM validation runs only on ZimaOS using the
already-existing clean `kernel-final`, `build-final` and `neosymbian-final` volume;
the unrelated dirty `kernel`/`build` checkouts are preserved. Remote logs are under
`/DATA/AppData/symbian-build/logs/c7/`.

**Repair and installation run (2026-11-10; call acceptance deferred):**

- The first repair-session RAM boot used the hash-checked image containing kernel
  `888b6105`, ROM `2c5d869`, and neoui `5d7d0c8`, including current Clock and Dev tools.
  MSS reached step 8, ADSP step 4, and NAS registered on LTE. `lastlog` was captured
  first with `--no-date`; it belonged to older kernel `090bb5e5`, not the latest freeze.
- The existing phone tool now persists partial data and command replies during capture,
  requires completion markers and exits nonzero on timeout/disconnect. Its selftest
  covers fragmented replies, missing markers, EOF and partial-output preservation.
- Repair code gives kernel stop retries one shared 30-second elapsed wait budget and
  MODEMD a 35-second watchdog. A still-running or unreadable stop remains quarantined;
  timeout alone cannot authorize reload or another stop. MSS-only recovery requires
  positively healthy ADSP state and quiescent APR.
- Default-off `TEL_DIAGNOSTICS=1` adds `mss fault` and `adsp fault` to the existing
  monitor. These synthesize detection only; MODEMD performs actual stop/reload through
  its normal lifecycle. Results must be labelled separately from genuine firmware faults.
- OLED, call/audio, haptic and recovery transitions receive bounded diagnostics.
  Post-final-END NAS queries observe actual LTE return for up to 30 seconds; they do
  not change system selection or cycle radio power. No freeze/LTE root cause is claimed fixed.
- Owner has one other line, keeps SIM PIN disabled, and selected connected 24-hour use.
  Successful call waiting/swap/merge and PIN unlock remain unaccepted until the required
  call legs/test SIM are available. The owner subsequently stopped phone testing and
  requested a persistent latest-ROM install; no calls or 24-hour acceptance were run.
- The final build was installed persistently into `system_a` and `boot_a` with
  diagnostic fault injection disabled. The installer wrote/read-back-verified 21,003 KB;
  a RAM boot of the exact flashed image mounted the matching flash-backed ROFS,
  showed the launcher and LTE, and marked slot a successful. Slot b was preserved.
  A normal reboot was then sent successfully; its final visible boot was not independently
  observed because normal-boot USB debug access remains limited. This is installation
  evidence, not call/recovery acceptance. See [FS5](filesystem.md#fs5-updates-and-integrity).

### C8: call log and contacts

- `modemsrv` writes the call history to `C:\private\<modemsrv uid>\calls.db`.
- A small Rust contacts store, plus vCard import from `E:`. The old Symbian contacts model is used only if C12's ETel
  work makes old apps matter.
- neoui Recents and Contacts apps. The dialer and the incoming-call screen look up names.

Exit: an incoming call from a saved number shows the contact's name.

Reference: [symbian-phone-sources.md](symbian-phone-sources.md), the facts C8 takes from the 2010 Symbian phone and contacts
sources (dial-string rules and test vectors, SS codes, caller-name matching, smart dialling, Logs and Speed dial
behaviour, vCard mapping).

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
  `networkingsrv` (ESOCK/TCPIP6) re-forked from `retired-repos.md`. **Decided 2026-11-12 (owner):** ESOCK/TCPIP6,
  shared with Wi-Fi ([wifi.md](wifi.md)).
- **Fallback:** a small Rust IP stack (smoltcp) behind our own socket API, if the 2010 stack costs too much.
- **Wi-Fi went smoltcp first** (owner, 2026-11-12; [wifi.md](wifi.md) W5): NEONET.EXE and the NeoNet API. C10 picks
  its stack when it starts: an rmnet device under NEONET is the short path.

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
| C5 | **done 2026-11-09**: MODEMD serves NeoModem and is started by SYSSTART; registration, operator and bars in the status bar; calls out and in through the Phone screen (silent); 3G voice-only until C5b (IPA) |
| C5b | **done 2026-11-09** (kernel `d003355`): IPA runs (GSI firmware via PAS 15, SMMU identity context, command and LAN_RX channels); the modem stays on LTE, calls CSFB to 3G and back; the IPA QMI handshake is still half done (needed for data) |
| C6 | **done 2026-11-09** (kernel `b12d1ba`, telephony `3f4af12`, neoui `2d55d01`): the ADSP boots (PAS 1), APR in Rust, CS35L36 x2 + RT5514 board driver; two-way call audio on the earpiece and loudspeaker, Mute / Speaker / volume / DTMF; Dev tools audio loopback test; the modem stayed on 3G after a connected call (fixed 2026-11-12, kernel `69bb4cd3`: the codec's rails were on the wrong PMIC) |
| C7 | **merged 2026-11-12** (C7 PRs merged with main, owner's call to land before the C7 phone acceptance): IPC v2, multi-call, SIM PIN, airplane, ringtone + haptics, modem recovery (never stops the ADSP); phone acceptance of the C7 behaviours pending; wired headset deferred |
| C8–C12 | not started |

## Modem restart and the ADSP (2026-11-13, open)

**Seen on the phone** (`mss fault`, a RAM boot with `TEL_DIAGNOSTICS=1`; log `private/wifi/w7/mss3.log`):
1. MODEMD stops the modem: AXI halt incomplete, forced MSS reset, stop acknowledged after 218 ms.
2. The modem boots again: MBA, MPSS authenticated, QRTR up after 6.4 s.
3. MODEMD then reads the ADSP's state as `[4, 0, 7, 3]`. Word 2 has bit 0 (FATAL) set: **the ADSP has failed too.**
   MODEMD asks for a recovery of both (mask 3).
4. Recovery never stops the ADSP (its TrustZone PAS shutdown froze the phone, 2026-11-12), so it restarts the modem
   only. The ADSP stays failed, the check fires again, and after three attempts the modem goes FATAL ("SFR Init: wdog
   or kernel error").

**Why the ADSP fails:** the modem is stopped without warning its peers. Linux's `qcom_sysmon` sends each other
subsystem an SSCTL event before and after a peer shuts down or powers up (QMI service 43, the "subsystem event"
request). The ADSP then closes its links to the modem in order. Ours drops the modem abruptly, and the ADSP's audio
side asserts when its peer vanishes. This is a likely reading, not yet checked against the ADSP's crash reason.

**Fix (next telephony stage):**
1. Send the ADSP the sysmon/SSCTL events around a modem stop and start, as `qcom_sysmon` does.
2. A failed ADSP after a modem-only restart is no reason to restart the modem again: report "no call audio" instead
   of looping.
3. Understand the PAS-shutdown hang, so that the ADSP can be restarted when it really fails.

Wi-Fi's own restart after a modem stop (wifi.md W7) waits on this: MODEMD only calls WlanStart once the modem
recovery succeeds.
