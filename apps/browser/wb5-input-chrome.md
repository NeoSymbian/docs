<!-- SPDX-License-Identifier: Apache-2.0 -->
# WB5: input and chrome

Part of [Apps](../README.md) · Status: done · Updated: 2026-11-21 · Neighbours: [the browser hub](README.md)

**Status:** ✅ done 2026-11-21 · [browser#10](https://github.com/NeoSymbian/browser/pull/10), [browser#11](https://github.com/NeoSymbian/browser/pull/11), [ossrv#5](https://github.com/NeoSymbian/oss.FCL.sf.os.ossrv/pull/5), [servo#1](https://github.com/NeoSymbian/servo/pull/1), [webrender#1](https://github.com/NeoSymbian/webrender/pull/1), [build#47](https://github.com/NeoSymbian/build/pull/47), [docs#52](https://github.com/NeoSymbian/docs/pull/52), [docs#53](https://github.com/NeoSymbian/docs/pull/53) · every screen: [ui-screens.md](ui-screens.md) · the protocol: [protocol.md](protocol.md)

## Scope

| Stage | Work | Gate | Estimate (PM) |
|---|---|---|---:|
| WB5 input and chrome | Touch, scrolling, focus, direct Unicode input (a versioned composition/preedit protocol in neoui + its keyboard comes later), selection, forms, keyboard resize, Back, the Slint chrome (already built on FakeEngine by UI0–UI4, [ui.md](ui.md)) | Typing into forms and navigating with Back on the phone | 2–4 |

## Result (2026-11-21): done

Merged in browser#10 and #11 (protocol 1.4), ossrv#5, servo#1 (paint timing), webrender#1 (the scroll root fix),
build#47 (the ossrv pin) and docs#52. The gate flows ran on the Pixel by RAM boot, on a user side from before US2
(ARMv7); US4 rebuilt the Rust binaries for ARMv8 (2026-11-25).

| Part | Works on the Pixel | Notes |
|---|---|---|
| WB5a input and forms | Typing (English and Armenian on the on-screen keyboard) into page fields; the keyboard mode follows the field; the page shrinks above the keyboard (355 dp); confirm through the shell's QUERY; prompt as a sheet; `<select>` sheet; upload through Files' picker; Save password offer | Keys reach Servo as keyboard presses; contenteditable gets no keyboard yet |
| WB5c tabs and menus | Opened pages with thumbnails; a new tab from the link menu; long-press on a link opens the link menu; find in page with its count; a long-press on text selects the word, Copy puts it on the clipboard | Word selection uses Servo's double-click selection; the handles are approximate (Servo's Range rectangles cover a whole text node) |
| WB5d library | Bookmarks (☆), history by day (kept on C: across boots), an https download with its progress and "Download complete" in the shade (a second one of the same name is "dummy (2).pdf"), the Downloads and Settings views, the Clear data QUERY | The shade's Open starts Files on its home page: Files has no page yet that shows a file another app opens it with |
| WB5b speed | Scrolling 15-18 fps (was 8-10): NEOWEB draws an opaque RGB frame (draw 41-56 → 22-34 ms), and WebRender takes the root pipeline's scroll frame as the page's scroll root, so a scroll moves cached tiles (engine paint 95-140 → 43-53 ms; tiles rasterized in 5-9 of 31-37 frames, 9 draws a frame) | 30 fps needs the full-screen SWGL composite (about 45 ms) and the frame copies (engine 6 ms, NEOWEB 8 ms) cut: WebRender's threaded software compositor, and frames drawn straight into the shell's surface |

**Open after WB5 (next):**
- Tabs: page events and frames carry no tab id, so a fast tab switch or a popup can mix them up for a moment
  (Codex review); a hidden tab's dialog shows the visible site's name.
- contenteditable gets no keyboard; `<select>` lists over one event (4 KiB) lose rows; long link URLs are cut at
  about 2 KiB.
- JavaScript on/off and the cookie rule are saved but not applied (Servo 0.8 has no switches for them).
- The Settings app's Browser page (`set2-app-browser`) waits for Settings' Apps list.
- Found while marking the screens (2026-11-21): the chrome doesn't hide on scroll (`ChromeScroll` is unused with
  Servo); the tab list isn't saved on Quit; no heap budget for eviction; no ←/→ history list; eviction and Buttons
  mode were not run on the phone. Each screen: [ui-screens.md](ui-screens.md).
- Re-test on an ARMv8 user side after US4 (these runs used a user side from before US2): done in US4's Pixel run
  (2026-11-25), where the owner browsed with the ARMv8 NEOWEBE ([user-side-smp.md](../../user-side/user-side-smp.md)).

**Fixed on the way:**
- A thread calling `localtime` died with `TzServer 1` (no time zone server in the ROM). P.I.P.S. now uses the
  kernel's UTC offset when `tzserver.exe` is missing.
- `\p{L}` in the page helper needed ICU, which this SpiderMonkey lacks.
- Calling back into the WebView from a script result panicked Servo ("RefCell already borrowed").
- The engine's main thread is now process-critical, and NEOWEB restarts the engine for tabs.
