<!-- SPDX-License-Identifier: Apache-2.0 -->
# Developer tools

Part of [the docs](../README.md) · Status: done · Updated: 2026-11-27

The debug path from the Mac to the phone over the USB cable: the kernel debug monitor (logs, the previous boot's log,
memory, block I/O, screenshots), and next to it fshell on a second USB serial port, with `phone.py` on the Mac for a
shell, file push and pull, and running programs. It works on fastboot RAM boots; installed boots wait for USB power
on a normal boot ([known issues](../known-issues.md)). The kernel drivers behind it are in NeoSymbian/kernel's
`baseport/arm64`.

## Documents

| Doc | What | Status |
|---|---|---|
| [debug-access.md](debug-access.md) | The design: Symbian's own tools, the kernel and user-side pieces, security, stages | done |
| [debug-access-roadmap.md](debug-access-roadmap.md) | The tasks that built it, each with its acceptance and PRs | record |
