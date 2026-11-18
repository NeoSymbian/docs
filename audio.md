<!-- SPDX-License-Identifier: Apache-2.0 -->
# Audio: NeoAudio, media on the ADSP, and the old apps' DevSound

Started 2026-11-17 (research: `private/audio/codex-audio-report-20261117.md`, a Codex review with line-level
references into the 2010 sources). Continues [driver-support.md](driver-support.md) D3 and
[legacy.md](legacy.md) L2.

## What there was

Call audio (telephony C6/C7) and the ringtone work on the Pixel:

| Part | Chip | Before this work |
|---|---|---|
| Earpiece (top) | Cirrus CS35L36 at I2C10 0x40 ("Top") | calls, Dev tools loopback |
| Loudspeaker (bottom) | CS35L36 at 0x41 ("Bottom") | call Speaker, ringtone, loopback; "speaker" drives **both** amps with the same mono slot |
| Main mic | a DMIC through a Realtek RT5514 (I2C 0x57) | calls, loopback; DMIC1 left only (C1's mixer) |
| Second mic | the RT5514's other DMIC inputs | unused; which one is the top mic is not known |
| RT5514 on SPI | the always-on voice-wake DSP | unused, not needed |
| 3.5 mm jack | PM660L analog codec + the SDM660 digital codec | only MIC BIAS 1 (the DMIC's supply); no output, detection or buttons |
| Amp protection | CS35L36 IRQs (TLMM 79/80) | ignored; faults logged at start |
| Calibration | ACDB | none: the ADSP's built-in topologies |

MODEMD's APR ([telephony.md](telephony.md) C6) ran three things: the call's voice path, the loopback test and a
2-second ringtone looped from one 256 KB DMA region. No app could play or record sound; the old apps' DevSound had
no server (Frozen Bubble ran silent, [legacy.md](legacy.md)).

## Design

```mermaid
flowchart LR
  subgraph apps
    N[native apps: Dev tools, media, alerts]
    L[old apps: CMdaAudioOutputStream ...]
  end
  L --> DS[DevSound client + audio server<br/>2010 sources]
  DS --> SH[mmfdevsoundadaptor.dll<br/>our replacement, legacy repo]
  N --> NA
  SH --> NA[NeoAudio server<br/>in MODEMD]
  NA --> MX[mixer + resampler<br/>48 kHz mono]
  MX -->|media runs| ASM[ADSP ASM/ADM periods] --> AMP[CS35L36 amps]
  MX -->|call, ringtone, QEMU| CLK[clock sink: consumed in real time]
```

- **NeoAudio lives in MODEMD** because MODEMD owns the ADSP's APR channel (one receive owner per kernel ring). The
  logic is its own crate (`telephony/crates/neoaudio`), so a later AUDIOD (or the `neohw` split) takes it as is.
- **One session = one stream.** Any rate 8–96 kHz, mono or stereo, S16LE. Each stream has a 250 ms queue; WRITE
  waits while it is full (flow control); an underrun is counted once per dry spell (DevSound reports the end of
  data that way).
- **Software mixing first:** every stream is resampled (linear) to 48 kHz, mixed to mono with its volume, and
  saturated. One ADSP stream plays the mix. ADSP-side mixing (several ASM sessions) is a later option once proven.
- **Media on the ADSP:** `apr::Mode::Media` runs the ringtone's ASM/ADM path without the loop: eight 20 ms periods
  (1920 bytes each) after the ringtone in the same region, each published to the ADSP with its own kernel ticket
  and released by its own WRITE_DONE. Leaving media waits for the periods in flight (at most 1 s).
- **Priority:** call > ringtone > loopback test > media. While preempted, streams keep running on the clock sink
  (unheard) and INFO reports `PREEMPTED`, so players keep their pace and native players can pause.
- **The clock sink** consumes the mix in real time whenever the ADSP does not play it: no audio DSP (QEMU), a call,
  the ringtone, or a media start that has not reached the ADSP within 3 s. While media is starting the streams wait
  instead, so the start of a sound is not lost.
- **QEMU:** MODEMD no longer exits without a modem: it serves NeoAudio on the clock sink and refuses NeoModem
  connections (KErrNotFound), as if NeoModem were absent. `syborg-virtio-audio` is an unimplemented device in our
  QEMU board, so nothing is audible there.

### Kernel

- **AudioMem** (HAL 0x4e26) publishes **ranges**: up to 16 at once, each with a ticket and the ADSP generation;
  copies refuse a published range; publishing length 0 is the whole region (the ringtone). Op 4 copies out
  (recording). A successful ADSP stop frees every range.
- **Routes** (HAL Audio op 3): 0 earpiece (Top), 1 both amps, 2 bottom only (new).

### NeoAudio protocol (v1.0)

| Op | Args | Result |
|---|---|---|
| 1 OPEN | rate, channels, flags (1 = record) | 0; KErrInUse if the session has a stream |
| 2 WRITE | des8 PCM (whole frames) | bytes, once all are queued; waits while full |
| 3 READ | writable des8 | bytes, once full (or at STOP) |
| 4 VOLUME | 0..=100 | stream gain |
| 5 PAUSE | 1 / 0 | the queue is kept |
| 6 STOP | — | drops the queue; a waiting WRITE gets KErrCancel |
| 7 INFO | writable des8 (24 bytes) | state, sink, queued bytes, frames, underruns, overruns |
| 8 ROUTE | 0 both speakers, 1 earpiece, 2 bottom | media's route |
| 9 MASTER | 0..=10 | media's amp volume |

## Stages

| Stage | What | Check |
|---|---|---|
| **A0** | This page; the protocol | — |
| **A1** | NeoAudio in MODEMD with the clock sink; Dev tools tests | QEMU: Dev tools → Audio → "NeoAudio: play a tone" logs `done in ~3000 ms`, sink clock |
| **A2** | Media periods on the ADSP; per-range AudioMem; preemption | Pixel: the tone is heard on the loudspeaker; "two tones mixed"; routes (both / bottom / earpiece); a call or the ringtone during a tone; `sink dsp`, no underruns before the end |
| **A3** | Old apps: our `mmfdevsoundadaptor.dll` over NeoAudio, the audio server and its launcher | Frozen Bubble plays its sounds; exits and restarts cleanly |
| **A4** | Tones and DTMF (DevSound tone mode), WAV through the MMF controller | tone utility and a WAV file play |
| **A5** | Recording: ASM read from the mic port, the input stream | record 60 s, play it back; find the top mic |
| **A6** | Volume keys and settings for media, routes in Settings, focus rules | media → call → media |
| **A7** | Amp fault IRQs (mute and report), bottom/earpiece use, optional ADSP mixing, optional QEMU audio device | |
| **A8** | 3.5 mm jack (output, detection, headset mic, buttons), ACDB calibration investigation | |

## Status (2026-11-18)

All of A0–A8 is implemented on the `audio` branches (telephony, kernel, neoui, legacy, docs); host tests, ARM builds
and clippy pass. Results on the Pixel (RAM boots, nothing flashed) and on QEMU:

| Stage | Result |
|---|---|
| A1 | QEMU: MODEMD finds no modem, serves NeoAudio only (clock sink); SYSSTART's media settings reach it |
| A2 | Pixel: the test sound plays through the ADSP (`38808 frames, 1 underrun` = the end, `sink 1` = DSP); routes both / bottom / earpiece reach the amps; volume changes apply live |
| A3 | Pixel: Frozen Bubble starts `MMFAudioServerStart.exe`, opens a NeoAudio stream (16 kHz mono) through our DevSound adaptor, media runs on the ADSP while it plays; no panics. Audible level not yet confirmed by ear |
| A4 | Built into the ROM: tones and DTMF (synthesized in the adaptor), the WAV controller, format, source/sink and codecs; not exercised yet (no app on the phone plays a WAV) |
| A5 | Pixel: 5 s recording = 480000 bytes, played back with 0 underruns. The READ opcode is ASM_DATA_CMD_READ_V2 `0x10dac` (`0x10db5` is refused with status 3). The full-scale samples are the mic's start (its first 7–12 ms), not clipping: a quiet room after 0.5 s reads RMS 7–11, peak 29–52 |
| A6 | Pixel: Settings → Sounds → Media works; the volume keys step the media volume outside a call |
| A7 | Amp protection polling runs (no event seen). Mics (Dev tools → "find the microphones", a 1 kHz tone on one speaker recorded by each mic): earpiece → DMIC1 5031 / DMIC2 5730 RMS; bottom speaker → DMIC1 5862 / DMIC2 5983. DMIC1, the call mic, is the bottom mic; DMIC2 is most likely the top one (the body couples both strongly, so the margin is small) |
| A8 | Pixel: the jack driver comes up (`jack ok: unplugged`, no faults); headphones and the headset mic are untested (nothing plugged in) |

**Gaps:**
- QEMU has no audible device: our board's `syborg-virtio-audio` is unimplemented and VNC carries no sound.
- No ACDB calibration: the format is proprietary, and the ADSP's built-in topologies stay.
- Headphones and the headset mic are implemented end to end, but untried: no headset has been plugged in yet.
  - Media on headphones: INT0 MI2S RX, the codec's MCLK, the kernel's op 9.
  - Recording from a headset: INT3 MI2S TX, the kernel's op 10.

**Open:**
- One kernel fault on the Pixel (2026-11-18, kernel `9d4011e6`): a data abort in `exc_common` (ExcCode 1, system
  exception).
  - It came about 2 s after media stopped, while you scrolled Dev tools; no action had reached Dev tools.
  - It was not seen again with the same tests.
  - Kernel `6d9fb78a` now prints every kernel-mode abort's pc, far, esr, lr, sp and thread, so the next one names its
    cause: read it with `phone.py cmd lastlog`.

**Fixed on the way:** "Action failed (-2)" on Settings → Sounds. It was MODEMD's stale result from the modem
refusing "online" (QMI 52, invalid transition) about 20 s into every boot; it no longer counts as a failed action.
