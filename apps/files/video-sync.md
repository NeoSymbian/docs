# Video sync: how players keep picture and sound together, and what Files does next

**Status:** research, 2026-11-26. It feeds FA12b of [README.md](README.md) (the video player, FA12). Two
researchers read the sources: Codex for Android (Media3/ExoPlayer, AOSP NuPlayer, libavc, SurfaceFlinger) and a Claude
agent for the Linux players (FFmpeg/ffplay, GStreamer, mpv, VLC, libyuv). The claims that drive a change below were
checked again against the source; the versions are under [Sources](#sources). This page describes mechanisms and links
them: no code is copied from GPL or LGPL projects.

## Our player today

```
file ─► worker (CPU 7): demux, decode H.264/VP8/VP9 ─► queue of decoded pictures (4, at most 8)
                         └► sound decoded ─► AUDIOD (NeoAudio) ─► DSP
UI thread: picks the next picture ─► converter (CPU 6, + helper on CPU 5 in landscape): YUV → XRGB, scale, turn,
           straight into the app's surface ─► at the picture's time the UI sends DAMAGE, the server copies it out
clock: NeoAudio's played frames − 160 ms, published when the count moves, interpolated with the fast counter
```

Code: `files/symbian/app/src/video.rs` (`Worker`, `poll`, `Converter`), `files/crates/neo-format-media/src/av/`
(`video.rs` decoders, `yuv.rs` conversion). Constants: `AHEAD` 4, `AHEAD_MAX` 8, `LATENCY_US` 160 ms, `TICK_US` 4 ms,
`FAST_CPU` 7, `CONVERT_CPU` 6, `HELPER_CPU` 5 with 25 % of the rows, over-720p refused (`HEAP_PIXELS`).

**Measured on the Pixel (720p30 H.264 High + AAC, 2026-11-26):**

| What | Value |
|---|---|
| Portrait | 28.5–30 fps, 1–5 % dropped, worst A/V ~100 ms |
| Controls up (Slint path) | 29.7 fps |
| Landscape | 23–27 fps; conversion 21–22 ms split over two cores (28 ms on one A75, 12 ms portrait) |
| Decode | 20 ms average, 30 ms worst a picture (one A75) |
| Clock | steps of ~20 ms between NeoAudio's position reports |
| After every key frame (2 s GOP) | ~780 ms with no picture out of the decoder, then pictures 50–100 ms late |

The last row was the decoder's reorder buffer: rust_h264's `OrderedDecoder::new()` holds up to 16 pictures until the
next key frame. Files now sets the depth from the stream (files `fb90512`); host-tested, not yet run on the Pixel.

## 1. The clock

**Android.**
- **Media3.** `AudioTrackPositionTracker` reads `AudioTrack.getTimestamp()`, a frame count and the time it was
  played, together.
  - It extrapolates from that pair at the playback speed.
  - Without a timestamp, it uses the head position and averages up to 10 offsets sampled at least 30 ms apart.
  - It rejects a timestamp more than 5 s off, and blends a change of method over 1 s.
  - `DefaultMediaClock` never lets the position go backwards when the clock source changes.
- **NuPlayer.** It anchors "the buffer's time − what is written but unplayed" to now. `MediaClock::updateAnchor`
  keeps the old projection when the new one differs by less than 10 ms.

**Linux players.**
- **ffplay.** It has the same shape as ours.
  - The clock is `pts_drift + now`.
  - Each update is set at the time the SDL audio callback *started*.
  - The output latency is a fixed guess of two hardware buffers plus what is not yet handed over.
- **mpv and GStreamer** ask the device every time: `snd_pcm_delay` for ALSA, the PipeWire stream time.
  - GStreamer's `GstAudioClock` never returns a smaller value than before.
- **VLC** fits a line through the last 10 updates. It resets when the slope leaves 1 ± 0.2.

**Ours.** The clock is the played count minus a fixed 160 ms. It is stamped when the *worker* sees the count change,
not when NeoAudio played it. Nobody has measured the 160 ms.

**What we change.**
- **NeoAudio reports frames and time together.** It returns *(frames played, frames still in the DSP, counter time of
  that reading)* in one answer, as `getTimestamp` and PipeWire do. This is a NeoAudio protocol addition in neohw. The
  published clock never goes backwards.
- **Measure the real output latency once.** Play a flash-and-beep clip and film the phone at 240 fps, then replace
  the fixed 160 ms with what was measured.
- **Pixel check.** The clock's step at each report stays at or under 2 ms; the click and the flash line up within one
  frame.

## 2. When a picture is shown or dropped

**Android.**
- **ExoPlayer (Media3 1.5.1).** Below, *early* is how long before its time the picture is ready.

  | Picture is | ExoPlayer | Constant |
  |---|---|---|
  | more than 50 ms early | holds it and asks again later | `MAX_EARLY_US_THRESHOLD = 50_000` |
  | more than 30 ms late | drops it (not the last one) | `MIN_EARLY_US_LATE_THRESHOLD = -30_000L` |
  | more than 500 ms late | skips to the next key frame | `MIN_EARLY_US_VERY_LATE_THRESHOLD = -500_000L` |
  | late, with no picture shown for 100 ms | shows it anyway, to break a freeze | `elapsedSinceLastRenderUs > 100_000` |

  - A picture is handed to the display with a timestamp, aimed at a vsync about two refreshes ahead
    (`VideoFrameReleaseHelper`).
- **NuPlayer** drops a picture more than 40 ms late. When over 100 ms behind, it doesn't even decode non-reference AVC
  pictures (`NuPlayerDecoder::fetchInputData`).

**Linux players.**
- **ffplay** has two drop points.
  - When showing (`video_refresh`): it drops a picture when the next one is already due, the same as our rule.
  - Before filtering and scaling (`get_video_frame`): it drops a picture that is already behind the clock.
  - When more than 100 ms behind, it moves its frame timer to now instead of rushing to catch up.
- **GStreamer.** The video sink allows 5 ms of lateness plus a 15 ms processing deadline. Its QoS events make the
  decoder skip non-reference frames (`skip_frame = AVDISCARD_NONREF`) until it catches up.
- **VLC** drops a picture before rendering when its measured render time (the high of the last 5) can't make it.
  After 11 late pictures it throws away everything up to the next I-frame.
- **mpv** drops at the display (but never below 10 fps) or in the decoder (`--framedrop=decoder`).

**Ours.** A converted picture is dropped when a newer one is due. Every picture is converted first (12–22 ms), even
one that will be dropped. DAMAGE goes at the picture's time, with no lead.

**What we change.**
- **Drop before converting.** A picture is not converted when `pts + one frame < now + convert estimate`, where the
  estimate is the highest of the last 5 conversions (as VLC and ffplay do). In landscape this gives the cores back.
- **ExoPlayer's thresholds for the rest:**
  - drop a picture more than 30 ms late;
  - hold one more than 50 ms early;
  - show one anyway when nothing has been shown for 100 ms.
- **Catching up.**
  - More than 500 ms behind: skip to the next key frame.
  - More than 100 ms behind: skip non-reference H.264 pictures (`nal_ref_idc == 0`) in the decoder.
- **A lead for DAMAGE.** Send it early by the measured DAMAGE→scanout time, which is GStreamer's render delay and
  ExoPlayer's release timestamp.
- **Pixel check.** Drops are counted by where they happen: before converting, after converting, or skipped in the
  decoder. A−V is measured at presentation (section 6).

## 3. Reordering and look-ahead

**Android and Linux.** Every decoder lets a picture out as soon as it holds more pictures than the stream reorders.
- **FFmpeg** (`h264_select_output_frame`) outputs when `pics > has_b_frames`.
  - `has_b_frames` is the VUI's `num_reorder_frames` when `bitstream_restriction_flag` is set, or in strict mode.
  - Otherwise it starts low and grows when a picture comes out of order.
- **libavc** (Android's H.264 decoder) waits for `num_reorder_frames + 1`, so a stream without B-frames shows its
  first picture at once.
- **Without the VUI value,** the bound comes from the level (MaxDpbMbs ÷ the picture's macroblocks): 720p is 5 at
  level 3.1 and 9 at level 4.x.
- **Neither ever reorders across a key frame;** both drain at an IDR.

**How far ahead they decode**, in time rather than pictures:

| Player | Look-ahead |
|---|---|
| ffplay | 3 decoded pictures, and at least 1 s of packets |
| mpv | at least 2 pictures at the display, 1 s of demuxed data |
| Android Codec2 | output slots = the decoder's delay + 4 |

**Ours.** The depth is now the VUI's `max_num_reorder_frames`, and 16 when the stream has none. The queue counts
pictures (4, at most 8), not time.

**What we change.**
- **Verify `fb90512` on the Pixel.** Log each picture's decode index, POC, PTS and the count held, from each IDR on.
- **Without the VUI value,** use 0 for Baseline and POC type 2 (output order is decode order), otherwise the level
  bound, never 16. This goes in the H264 wrapper in `neo-format-media`.
- **Size the decoded queue by time:** at least the worst I-picture decode minus one frame, about 100–150 ms. Log the
  queue's lead in ms at each IDR.
- **Pixel check.** No "late picture" lines after key frames; the queue's lead never reaches 0.

## 4. Converting, scaling and turning

**Android and Linux.** Players hand YUV to a display plane or the GPU, which scales, turns and converts on the way to
the screen:
- **Android:** SurfaceFlinger gives the hardware composer the crop, the rectangle and the transform.
- **ffplay:** `SDL_UpdateYUVTexture`.

Software fallbacks (libyuv and libswscale, both with NEON) work like this:
- they scale and turn on the YUV planes, at 1.5 bytes a pixel, then convert row by row;
- libyuv turns after converting only where it has no one-pass path;
- RGB565 output (`I422ToRGB565Row_NEON`) halves the bytes written.

**Ours.** Each output pixel is converted, scaled and turned in one software pass (`yuv::draw`, bands of 32 rows,
vectorized by the compiler). Landscape writes 2 MP; our decoder and converter already run on different cores. Writing
2 MP is the cost; the Pixel has no GPU path in our OS.

**What we change.**
- **First: landscape at the clip's own size** (1280×720, 0.92 MP, no upscale on the CPU), centred on black. Or scale
  and turn on the planes, then convert.
- **RGB565** if the app surface can take it. That is a neoui surface-format question.
- **Long term: the display controller's plane scaler** (SDM670 MDSS), as the phones' own players do. That is a kernel
  and neoui project.
- **Pixel check.** Landscape conversion under 15 ms; 29.5 fps or more with at most 1 % dropped.

## 5. Threads

**Android.**
- The playback thread runs at `THREAD_PRIORITY_AUDIO` (−16).
- AudioFlinger runs at urgent-audio priority.
- SurfaceFlinger runs at urgent display priority and asks for FIFO scheduling.
- Codec callbacks and input run on their own threads.

**Linux players.**
- They split work into demux, decode, display and audio threads.
- They don't raise priorities themselves; the sound server (PipeWire through RTKit) does.

**Ours.** The decoder is pinned to CPU 7, the converter to CPU 6 and its helper to CPU 5. AUDIOD and the UI thread are
left to the scheduler, with no priorities set.

**What we change.**
- **Priorities:** the audio server first, then the UI thread that presents, then the converter, then the decoder.
- **Pixel check.** Measure each thread's wake-up delay, and the two converter halves separately.

## 6. Measuring sync

**What each player reports:**

| Player | What it reports |
|---|---|
| ExoPlayer | each picture's offset (positive early, negative late) and dropped counts by cause (`DecoderCounters`) |
| ffplay | `A-V` = audio clock − video clock at display, and `fd` = early + late drops |
| mpv | A−V when the picture is due on screen, and `Dropped: vo/decoder` |
| GStreamer | `proportion` = processing time ÷ frame time (above 1, drops are certain), with rendered and dropped counts |

**Ours.**
- "Worst A/V" is the largest |clock − pts| when DAMAGE is sent, unsigned.
- Drops are one number.
- The queue is counted in pictures.

**What we change.** The 5 s line reports:
- **A−V at presentation:** signed mean, p95 and max.
- **Drops by stage:** before converting, after converting, skipped in the decoder.
- **The queue's lead in ms.**
- **The slowest stage's proportion.**

One frame id runs through decode, conversion and DAMAGE. The flash-and-beep film is the end-to-end truth.

## FA12b plan

Ranked; each step ends with its Pixel check from the sections above.

| # | Step | Where | Pixel check |
|---|---|---|---|
| 1 | Verify the reorder fix; the new A−V metric and logs at IDRs | files | no late pictures after key frames; A−V p95 ≤ 40 ms portrait |
| 2 | Drop before converting; ExoPlayer's 30/50/100 ms rules | files | drops by stage; ≤ 1 % dropped portrait |
| 3 | Landscape at the clip's size (or planes-first conversion) | files | landscape ≥ 29.5 fps, ≤ 1 % dropped |
| 4 | NeoAudio position with its time; measure the real latency | neohw, files | clock steps ≤ 2 ms; flash and beep within a frame |
| 5 | Skip non-reference pictures when behind, key frame when far behind | neo-format-media, files | recovers after a forced stall without a freeze |
| 6 | DAMAGE lead | files | A−V mean near 0 |
| 7 | Thread priorities | files, neoui, neohw | wake-up delays |

**Not copied:**
- **Resampling the sound to follow the picture** (ffplay, mpv display-sync, VLC). We are audio-master with no
  display sync, so none of them would resample in our setup.
- **GPU or overlay composition** until our display stack has it.

## Sources

| Project | Version | Where |
|---|---|---|
| Media3 / ExoPlayer | 1.5.1 | [MediaCodecVideoRenderer](https://github.com/androidx/media/blob/1.5.1/libraries/exoplayer/src/main/java/androidx/media3/exoplayer/video/MediaCodecVideoRenderer.java) (drop, key frame, force), [VideoFrameReleaseControl](https://github.com/androidx/media/blob/1.5.1/libraries/exoplayer/src/main/java/androidx/media3/exoplayer/video/VideoFrameReleaseControl.java) (50 ms hold), [VideoFrameReleaseHelper](https://github.com/androidx/media/blob/1.5.1/libraries/exoplayer/src/main/java/androidx/media3/exoplayer/video/VideoFrameReleaseHelper.java), [AudioTrackPositionTracker](https://github.com/androidx/media/blob/1.5.1/libraries/exoplayer/src/main/java/androidx/media3/exoplayer/audio/AudioTrackPositionTracker.java), [AudioTimestampPoller](https://github.com/androidx/media/blob/1.5.1/libraries/exoplayer/src/main/java/androidx/media3/exoplayer/audio/AudioTimestampPoller.java), [DefaultMediaClock](https://github.com/androidx/media/blob/1.5.1/libraries/exoplayer/src/main/java/androidx/media3/exoplayer/DefaultMediaClock.java), [DecoderCounters](https://github.com/androidx/media/blob/1.5.1/libraries/exoplayer/src/main/java/androidx/media3/exoplayer/DecoderCounters.java) |
| AOSP frameworks/av | main | [NuPlayerRenderer.cpp](https://android.googlesource.com/platform/frameworks/av/+/master/media/libmediaplayerservice/nuplayer/NuPlayerRenderer.cpp), [NuPlayerDecoder.cpp](https://android.googlesource.com/platform/frameworks/av/+/master/media/libmediaplayerservice/nuplayer/NuPlayerDecoder.cpp), [MediaClock.cpp](https://android.googlesource.com/platform/frameworks/av/+/refs/heads/main/media/libstagefright/MediaClock.cpp), [CCodecBufferChannel.cpp](https://android.googlesource.com/platform/frameworks/av/+/refs/heads/main/media/codec2/sfplugin/CCodecBufferChannel.cpp) |
| AOSP frameworks/native | main | [OutputLayer.cpp](https://android.googlesource.com/platform/frameworks/native/+/refs/heads/main/services/surfaceflinger/CompositionEngine/src/OutputLayer.cpp), [TimeStats.cpp](https://android.googlesource.com/platform/frameworks/native/+/master/services/surfaceflinger/TimeStats/TimeStats.cpp) |
| libavc | 5863b2e | [ih264d_utils.c](https://android.googlesource.com/platform/external/libavc/+/5863b2e39357d82d53b3163afd38ad3bb0a07042/decoder/ih264d_utils.c) (`ih264d_assign_display_seq`) |
| FFmpeg | master 288839e8 | `fftools/ffplay.c` (`compute_target_delay`, `video_refresh`, `get_video_frame`, `sdl_audio_callback`), `libavcodec/h264_slice.c` (`h264_select_output_frame`), `libavcodec/h264_ps.c` (`decode_vui_parameters`) |
| GStreamer | main 72bccde1 | `libs/gst/base/gstbasesink.c` (QoS, `max-lateness`), `gst-libs/gst/video/gstvideodecoder.c`, `gst-libs/gst/audio/gstaudiobasesink.c`, `gstaudioclock.c`; gst-libav `gstavviddec.c` |
| mpv | master 1eab28e7 | `player/video.c`, `player/audio.c`, `video/out/vo.c`, `audio/out/buffer.c`, `ao_pipewire.c` |
| VLC | master 80323b37 | `src/clock/clock.c`, `src/video_output/video_output.c`, `src/audio_output/dec.c`, `modules/codec/avcodec/video.c` |
| libyuv | main 03f119c0 | `row.h`, `rotate_row.h`, `convert_argb.cc` (`ConvertToARGB`) |
