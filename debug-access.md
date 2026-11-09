<!-- SPDX-License-Identifier: Apache-2.0 -->
# Debug access: shell, files and logs from the Mac over USB

Written 2026-11-09. **Status: design (DA0). Nothing below is built yet.**

The goal is what `adb` gives an Android developer: a shell, pushing and pulling files, launching programs and
reading logs, from the Mac through the USB cable. NeoSymbian gets it from Symbian's own 2010 tools, unchanged.
There is no TCP/IP, no SSH and no comms framework (c32) in the first stages.

Remote access with standard `ssh`/`scp` is a separate, later goal ([remote-access.md](remote-access.md), and the
proposed revision in `remote-access.md.draft`).

## What exists today

**The kernel debug monitor.** The phone's USB already carries one CDC-ACM serial port, owned by the kernel.
- **Commands:** `A64Mon_Line` in `kernel/baseport/arm64/common/specific/a64_dbgmon.cpp`, plus the telephony words in
  `sdm670_assp/qcom_telmon.cpp`. They cover the log ring and the previous boot's log, registers, block I/O, slots,
  input, screenshots, threads, CPUs, USB, and the telephony subsystems.
- **Mac side:** `kernel/baseport/arm64/tools/phone.py` (`run`, `cmd`, `dump`, `put`, `shot`, `console`).
- **Speed:** a SHA-256-checked `blk dump` runs at 2.0 MB/s ([telephony C0](telephony.md#c0-recon-and-backups)).
- **Limits:**
  - input lines are 160 bytes, and longer ones are cut silently;
  - output lines are 256 bytes, and longer ones fault the kernel;
  - `type` can lose the end of a line ([known issues](known-issues.md));
  - binary data travels raw between a text header and a SHA-256 trailer.

The monitor stays: it is the **kernel and bring-up channel**, and it works when the user side is dead. This design adds
a **user-side channel** next to it.

**When USB runs.** `A64StartUsbConsole` (`sdm670_assp/qcom_dwc3_acm.cpp`) starts USB only when ABL left it powered
(fastboot RAM boots) or in dev mode. Normal-boot USB power is parked
([known issues](known-issues.md#phone-usb-power-on-a-normal-boot-doesnt-work-yet-parked-2026-11-08)). Until that is
fixed, every stage below works on RAM boots only.

## Symbian's own tools

Symbian had all of this, and the sources are in the SymbianSource repos (EPL):

| Tool | What it gives | What it needs | Stage |
|---|---|---|---|
| **fshell**, text-shell build (`oss.FCL.sf.os.fshell`, `build/sf/3tshell/`) | a shell with about 80 commands, `ymodem`/`xmodem` file transfer (binary, batches, names kept; `core/builtins/`), `hash`, `base64`, starts any EXE | 2010 user-side libraries: ecom, estor, bafl, charconv, featmgr, dbms, centralrepository, abclient (`fshell_platform.iby`). Some are not in our ROM yet | DA1–DA4 |
| **`vt100busdevcons.dll`**, an fshell console (`plugins/consoles/vt100cons/`) | a VT100 console over `RBusDevComm` | `ECOMM.LDD` and a serial PDD. **No c32** | DA2–DA4 |
| fshell `memoryaccess-fshell.ldd` (`libraries/memoryaccess/`) | `top`, `objinfo`, `getstack`, `heaptrace`, `fdb`, built-in `reboot` | a port of its ARM-specific parts (`hwbreak.cia`, `fdebuggerkernel.cpp`) to our kernel | later |
| **TRK**, text-shell build (`oss.FCL.sftools.dev.devicedbgsrvs`, `dbgagents/trkagent/`) | files, process start and lists, the debugger; Mac client Qt 4.8 `tools/runonphone` (LGPL) | the c32 serial stack (c32, c32root, c32exe, c32start, commsdat, ecuart or ecacm) and `TrkDriver.ldd` (`eka2driver/`, ARM-specific; TRK refuses to start without it) | later |
| OST TraceCore + `dbgtrccomm` (`oss.FCL.sf.os.osrndtools` `tracesrv/`) | Symbian's "logcat": traces over USB | c32 and a USB ACM CSY | later |
| coredumpserver (`devicedbgsrvs/dbgsrv/coredumpserver`) | crash dumps to a file | run-mode debug (`rm_debug`, ARM-specific) | later |
| MTP (`oss.FCL.sf.mw.remoteconn`) | a file browser on the Mac | the Symbian USB stack (usbman, usbc) | not planned |

The key fact: **fshell with `vt100busdevcons` and `ymodem` gives a shell and file transfer with only a serial
driver**. fshell's own `core/group/comm.script` starts it this way on boards like the NaviEngine:
`--console vt100busdevcons --console-title pdd=euart1,ldd=ecomm,port=1,rate=115200`.

## Design

### Kernel (C++, new)

- **`ECOMM.LDD`**, Symbian's serial channel, built unchanged from `kernel/kernel/eka/drivers/ecomm/d_comm.cpp`.
- **A serial PDD per board** (a `DComm`, `kernel/kernel/eka/include/drivers/comm.h`). The models are
  `symbian-qemu/baseport/syborg/serial/syborg_serial.cpp` and `kernel/kernel/eka/drivers/ecomm/uart16550.cpp`.
  - **bonito:** a PDD over a **second CDC-ACM function** in the USB composite gadget.
    - It reuses the endpoint, DMA ownership and queue code of the USB rework (`qcom_dwc3_acm.cpp`,
      `common/inc/a64_usb_dma.h`, `a64_usb_control.h`, `a64_usbnet_queue.h`), with ACM descriptors instead of ECM.
    - `DComm` is shaped for a UART (characters moved from interrupt handlers), so the PDD bridges to the USB queues
      through a DFC.
  - **QEMU:** a PDD for a second serial device, so CI can test the user side. Our `virt` board has one PL011, used
    by the kernel console (`qemu_variant/specific/qemu_virt.cpp`); which second device to use is open (DA2).
- The first ACM port stays the monitor, unchanged.

### Phone user side (2010 C++, unchanged)

- **fshell's text-shell build**, from a new NeoSymbian fork of `oss.FCL.sf.os.fshell`:
  - pinned in `build/sources.lock`;
  - built through `build/emitter/components.py` like the other 2010 packages;
  - with its `.cif` command descriptions in the ROM.
- **Started on demand**, by SYSSTART or a monitor command, as
  `fshell --console vt100busdevcons --console-title pdd=<ours>,ldd=ecomm,port=<n>`.
- **`econs.dll` stays.** No `FSHELL_REPLACE_ECONS`: eshell and the Terminal use the real console.
- **Missing libraries:** those on fshell's list that our ROM lacks are added from the 2010 sources, or the feature
  that needs them is turned off in fshell's `platform.mmh`.

### Mac

- **`screen /dev/cu.usbmodem<…>`** on the shell's port gives the shell with no new tools.
- **New `phone.py` verbs:**
  - `sh` (interactive, or one command and its output);
  - `push` and `pull` (ymodem in a small Python implementation, then fshell's `hash` to compare SHA-256);
  - port selection: the monitor port and the shell port are told apart by their USB interface number.

### Security

- **Physical USB only:** the same model as the monitor today. There is no network exposure.
- **No new exposure on installed boots:** USB starts only on RAM boots and in dev mode.
- **Revisit at DA6,** before an installed boot offers the shell.

## Stages

| Stage | Exit test |
|---|---|
| DA0 design | This document. |
| DA1 fshell runs | fshell builds unchanged and runs on the phone's screen through `econs`, and on QEMU. Missing libraries are listed, then added or turned off. |
| DA2 serial, QEMU | `ECOMM.LDD` and a QEMU serial PDD; fshell answers on the second serial device; a CI boot runs `ls`, `hash` and a `ymodem` transfer. |
| DA3 serial, phone | Second ACM function and its PDD on bonito. The Mac sees two `cu.usbmodem` ports. The monitor still works (`phone.py cmd log`, `dump`, `shot`), and fshell answers on the other port. |
| DA4 files and programs | `phone.py push`/`pull` round-trips a binary file and a Unicode-named file with matching SHA-256; an EXE pushed to `C:` starts from the shell. Speed is measured against the 2 MB/s baseline. |
| DA5 robustness | Unplug and replug, RAM reboot, and a long transfer while the shell is used all work, and the monitor never goes away. The USB rework's halt-timeout and quarantine findings ([remote-access.md.draft](remote-access.md.draft)) are fixed first. |
| DA6 installed boot | Needs the normal-boot USB power fix, shared with remote access and FS6. |
| Later | memoryaccess LDD port (`top`, `objinfo`, `fdb`); TRK with c32, a `TrkDriver` port and `runonphone`; OST traces; coredumps. |

## Risks and open questions

- **fshell's library closure** against our minimal ROM (DA1). This may pull in more 2010 packages than its list
  suggests.
- **The second serial device on QEMU** (DA2): a second PL011 if our QEMU's `virt` offers one, or another device.
- **The USB PDD:** `DComm`'s UART model over bulk USB endpoints needs a DFC bridge and flow control (DA3).
- **macOS naming of two ACM functions** on one device, which decides how `phone.py` finds each port (DA3).
- **ymodem speed:** 1 KB blocks, each acknowledged. If it is far below 2 MB/s, a bulk mode can follow (DA4).

## References

- SymbianSource: `oss.FCL.sf.os.fshell`, `oss.FCL.sftools.dev.devicedbgsrvs`, `oss.FCL.sf.os.osrndtools`,
  `oss.FCL.sf.os.commsfw` (serial server, `serialserver/`), `oss.FCL.sf.os.usb`.
- Qt 4.8 `tools/runonphone` (TRK and CODA client, LGPL).
- [sources.md](sources.md): the FShell rows.
