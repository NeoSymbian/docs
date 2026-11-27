<!-- SPDX-License-Identifier: Apache-2.0 -->
# WB4: Servo in the Browser app

Part of [Apps](../README.md) · Status: done · Updated: 2026-11-20 · Neighbours: [the browser hub](README.md)

**Status:** ✅ done 2026-11-20 · [browser#8](https://github.com/NeoSymbian/browser/pull/8), [build#40](https://github.com/NeoSymbian/build/pull/40), [kernel#31](https://github.com/NeoSymbian/kernel/pull/31), [ossrv#3](https://github.com/NeoSymbian/oss.FCL.sf.os.ossrv/pull/3), [mozjs#2](https://github.com/NeoSymbian/mozjs/pull/2) · the protocol: [protocol.md](protocol.md)

## Scope

| Stage | Work | Gate | Estimate (PM) |
|---|---|---|---:|
| WB4 Servo → neoui | servo/surfman forks, SWGL, fonts, presentation. **The rustls crypto provider and entropy come here, not in WB6:** `Servo::new` always calls `prewarm_tls` | Local HTML/CSS/JS pages and images draw in `NEOWEB.EXE`; the memory is measured again | 6–12 |

## Result (2026-11-20): done

Merged in browser#8, build#40, kernel#31, ossrv#3 and mozjs#2. The heap crash that followed was fixed by US0/US1
([user-side-smp.md](../../user-side/user-side-smp.md)).
- **Two processes:** NEOWEB.EXE (the neoui app, the Slint chrome) and NEOWEBE.EXE (Servo 0.8 with SWGL on C:, the
  engine). They talk over the Symbian server `NeoWebEngine` (`app/neoweb-proto`); frames arrive in a global chunk
  with two RGBA buffers, and a buffer is reused only after NEOWEB shows it.
- **On the Pixel:** local pages render in about 8 s and Wikipedia over https in about 30 s; touch scrolling works.
- **Open after WB4:**
  - 🟡 scrolling at about 10 fps: 15–18 fps since [WB5](wb5-input-chrome.md), 30 fps still open;
  - ⬜ CSS mask icons render black;
  - ⬜ GitHub's module scripts fail their CORS check.
