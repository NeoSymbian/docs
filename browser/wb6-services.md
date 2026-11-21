<!-- SPDX-License-Identifier: Apache-2.0 -->
# WB6: browser services

Part of the [browser docs](../browser.md).

**Status:** ⬜ not started (next after WB5).

## Scope

| Stage | Work | Gate | Estimate (PM) |
|---|---|---|---:|
| WB6 browser services | certificate handling and errors, cookies/storage on C:, redirects, logins; wifi.rs opens portals in NEOWEB | Signing in to a site; a captive portal over Wi-Fi | 2–4 |

## What it covers

| Item | Status | Where |
|---|---|---|
| Certificate errors: a `neo:` error page; "Open the site anyway (unsafe)" only with Settings' switch, off by default (B10) | ⬜ (the switch is saved in Settings, nothing reads it) | [ui.md](ui.md#decisions) B10, `br2-cert-error` |
| A certificate store (trusted roots on the phone, shared with Files' certificate viewer) | ⬜ (Servo uses webpki's built-in roots) | [files-app.md](../files-app.md) |
| Site info from the lock: TLS version, the certificate, cookies with Clear | ⬜ | `br2-siteinfo` |
| No connection page with Retry and Check Wi-Fi (1.9 `OPEN` of Settings › Wi-Fi) | ⬜ | `br2-offline` |
| Wi-Fi sign-in: Wi-Fi's "No access" gets a Sign in action that opens the portal in NEOWEB | ⬜ (`neoui/symbian/src/wifi.rs` still has the shortcut) | `br2-captive` |
| Cookies and site storage on C:, kept across restarts | 🟡 Clear data works (WB5); persistence not checked | [architecture.md](architecture.md) (storage) |
| The cookie rule (allow, block third-party) and the JavaScript switch applied | ⬜ (saved in Settings, Servo 0.8 has no switch) | `br2-settings` |
| Saving passwords: needs a secure store (B11), shared with Wi-Fi keys later | ⬜ (the Save password sheet shows; Save is disabled) | `br2-login-save` |
| Permission requests: deny by default | ⬜ | [ui.md](ui.md#architecture) |
| Redirects and signing in to real sites | ⬜ (not tested as a gate yet) | — |

The screens are UI5's: [ui-screens.md](ui-screens.md#ui5-safety-and-errors).
