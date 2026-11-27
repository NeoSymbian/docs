<!-- SPDX-License-Identifier: Apache-2.0 -->
# WB7: media

Part of the [browser docs](../browser.md).

**Status:** ⬜ not started.

## Scope

| Stage | Work | Gate | Estimate (PM) |
|---|---|---|---:|
| WB7 media | The custom media backend (FFmpeg/dav1d, DevSound/MMF) | Video with sound, seeking, A/V sync, a thermal soak | 6–12+ |

## What it covers

| Item | Status | Where |
|---|---|---|
| A servo-media backend: `dummy` today; FFmpeg/dav1d software decode and colour conversion next | ⬜ | [architecture.md](architecture.md#architecture) |
| Sound through NeoAudio (the phone's audio works since A0–A8) | ⬜ | [audio.md](../hardware/audio.md) |
| Full-screen video: `PAGE` full, controls for 3 s | ⬜ | `br2-video` |
| Video with sound, seeking, A/V sync, a thermal soak | ⬜ | the gate |

The screen is UI6's: [ui-screens.md](ui-screens.md#ui6-media).
