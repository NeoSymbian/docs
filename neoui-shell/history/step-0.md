<!-- SPDX-License-Identifier: Apache-2.0 -->
# Step 0: know who is calling (the 2026-11-09 design)

Part of [neoui shell](../README.md) · Status: record · Updated: 2026-11-27

Step 0 of the shell-services design, moved out of the hub ([README.md](../README.md)) on 2026-11-27 and kept as
written below. **Where it went:**
- `Message::client_sid()` and the SID check on `SETTING_SET` were built in [SE0](../settings.md#the-settings-app-neoset)
  (e32-rs#16, neoui#38, 2026-11-26); only `NEOSET.EXE` (SID 0xE0002007) gets `Caller::Settings`.
- TP2a (protocol 1.18) checks NOTIFY, NOTIFY_CLEAR and BADGE against the app's EXE ([top-panel.md](../top-panel.md#tp2-plan-2026-11-26)).
- Protocol 1.19 added background services as `APPS` entries with no screen that the shell starts (DTSRV), not the
  `SERVICES` table below; protocol 1.20 binds each session by SID and the spawned process id
  ([protocol.md](../protocol.md)).
- The version bump below is void: minors are assigned in merge order ([protocol.md](../protocol.md)).

## The design (2026-11-09; update of 2026-11-25)

**Update 2026-11-25:** [settings.md](../settings.md#the-settings-app-neoset) SE0 builds the first half: `Message::client_sid()` and a
check on `SETTING_SET`, so that only `NEOSET.EXE` (SID 0xE0002007) gets `Caller::Settings` and its allowlist of
user-editable keys. Binding every session by SID at `connect` and `SERVICES` stay as designed below. The version
bump below is void: NeoUi is 1.12, and minors are assigned in merge order ([protocol.md](../protocol.md)).

**Problem.** `Host::connect` (`symbian/src/host.rs`) binds each new session to "the newest launched app without a
session" (marked `shortcut:` there). Two things follow:
- a process the shell didn't launch (a background service) is refused;
- the server can't verify which app a message comes from, so per-app rights (settings namespaces, notification keys)
  can't be enforced.

**Design.**
- Add `Message::client_sid() -> Result<u32, i32>` to `e32::server`. Use the `MessageClient` exec call (number from
  `execs.rs`) to open the client thread, then read its process's secure ID, and close the handle.
- Extend `APPS` to `(key, exe, uid3)`. The UID3 is the SID; take it from `symbian/exes.txt`.
- On `connect`, look up the app by SID.
  - A launched app gets its app record, as today.
  - A SID listed in a new table `SERVICES: &[(sid, &[keys])]` gets a **service session**: no surface or events, but it
    may post notifications and widget content under the keys listed for it.
  - Any other SID is refused with `KErrPermissionDenied`.
- Keep "the newest app without a session" only as the fallback when `client_sid` fails.
- Bump `ipc::VERSION` to (1, 1). The new opcodes and events are additive, so apps built for 1.0 still connect (only
  the major version is checked).

**Not needed at first for phone notifications.** The shell already talks to `NeoModem`, so it can post missed-call
and SMS notifications itself from modem events. Step 0 is needed for third-party apps and other background services.
