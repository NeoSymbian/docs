<!-- SPDX-License-Identifier: Apache-2.0 -->
# Debug access: shell, files and logs from the Mac over USB

Written 2026-11-09, revised 2026-11-10. **Status: design (DA0). Work list: [debug-access-roadmap.md](debug-access-roadmap.md) (T1–T12).**

The goal is what `adb` gives an Android developer: a shell, pushing and pulling files, launching programs and
reading logs, from the Mac through the USB cable. NeoSymbian gets it from Symbian's own 2010 tools, unchanged.
There is no TCP/IP, no SSH and no comms framework (c32) in the first stages.

**This is the only access route (owner, 2026-11-10).** The USB SSH work was dropped and archived; what it taught and
what was kept is in `remote-access.md.draft`.

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

**When USB runs.** `A64StartUsbConsole` (`sdm670_assp/qcom_dwc3.cpp`) starts USB only when ABL left it powered
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

- **`ECOMM.LDD`**, Symbian's serial channel, from `kernel/kernel/eka/drivers/ecomm/d_comm.cpp` (one marked fix: a pointer
  compared with `< 0`). It is linked into the kernel and installed at boot with the board PDD
  (`common/specific/a64_ecomm.cpp`), so `RBusDevComm::Open(1)` works; `User::Load*Device("ecomm"/"euart1")` needs the
  loader aliases (T7).
- **A PDD must call ECOMM from interrupt context (T5 finding).** ECOMM's `RxComplete`, drain and `TxComplete` complete
  requests inline unless `NKern::CurrentContext()==EInterrupt`; from a thread they self-deadlock on ECOMM's spinlock.
  A polled PDD cannot work. The bonito ACM PDD (T8) needs the same: call the `...Isr` functions from a real or
  pended interrupt.
- **A serial PDD per board** (a `DComm`, `kernel/kernel/eka/include/drivers/comm.h`). The models are
  `symbian-qemu/baseport/syborg/serial/syborg_serial.cpp` and `kernel/kernel/eka/drivers/ecomm/uart16550.cpp`.
  - **bonito:** a PDD over a **second CDC-ACM function** in the USB composite gadget.
    - **USB driver layering (T2, kernel `96f60d6`):** a controller core (`sdm670_assp/qcom_dwc3.cpp`: bring-up,
      events, EP0, endpoint DMA buffers) runs function drivers through `common/inc/a64_usb_function.h`. Today there is
      one, the monitor ACM (`common/specific/a64_usb_acm_monitor.cpp`); the debug ACM that this PDD sits on comes in
      T8. **T3 (kernel `b7133e2`)** added, without ECM: endpoint DMA ownership (a stop frees a buffer only on its
      ENDTRANSFER command-complete event; failures quarantine), SET_CONFIGURATION deferred until its stops end, a
      controller restart (halt, core reset, bring-up) as the only recovery for a live control transfer or a quarantine,
      and the UTMI/PIPE clock mux restore that `usb cold` needs (a GCC reset leaves QSCRATCH GENERAL_CFG at 04, not
      0d). Verified on bonito: `usb cold 7`, replug, Mac sleep/wake, a 5-minute soak. The queue code comes in T4.
    - Later, a DWC3 controller driver for Symbian's own USB client framework (`kernel/eka/drivers/usbcc`,
      `usbc.ldd`) gives the standard `RDevUsbcClient` for usbman and MTP (roadmap L1).
    - `DComm` is shaped for a UART (characters moved from interrupt handlers), so the PDD bridges to the USB queues
      through a DFC.
  - **QEMU:** a PDD for virt's second PL011 (`VIRT_UART1` at `0x09040000`, `symbian-qemu/qemu/hw/arm/virt.c:206`),
    so CI can test the user side; UART0 stays the kernel console. Done in T5 (kernel `326fffc`,
    `virt_assp/a64_pl011_comm.cpp`, SPI 8): QEMU's PL011 raises TX only after a DR write and RX only when the FIFO crosses
    its trigger, so the PDD pends its own SPI (GICD_ISPENDR) to start TX and to drain leftovers.
    `run-qemu.sh SERIAL1=<chardev>`; test `NEOCOM.EXE` + `tools/test-serial-qemu.py`.
- The first ACM port stays the monitor, unchanged.

### Phone user side (2010 C++, unchanged)

- **fshell's text-shell build**, from a new NeoSymbian fork of `oss.FCL.sf.os.fshell`:
  - pinned in `build/sources.lock`;
  - built through `build/emitter/components.py` like the other 2010 packages;
  - with its `.cif` command descriptions in the ROM.
- **Started on demand**, by SYSSTART or a monitor command, as
  `fshell --console vt100busdevcons --console-title pdd=<ours>,ldd=ecomm,port=<n>`.
- **`econs.dll` stays.** No `FSHELL_REPLACE_ECONS`: eshell and the Terminal use the real console.
- **fshell on the serial port (T7):** `fshell --console vt100busdevcons --console-title
  pdd=euart1,ldd=ecomm,port=1,rate=115200,sizedetect=0` (QEMU; the loader aliases `ecomm`/`euart1` name the built-in
  drivers). The host client is kernel `tools/fshell_link.py`: wait for fshell's prompt before each command (earlier
  input loses its first bytes), and put `$?` straight into the END record (`export X $?` reads a negative status as an
  option). Every builtin needs its `.cif` in the ROM.
- **fshell on econs (T6, build `faf8f8c`):** fshell's default console is `defcons` (it picks econs on a text
  configuration), so `defcons.dll` must be in the ROM. The minigui console (`econswserv`, the QEMU/window-server
  `ECONS.DLL`) didn't complete a cancelled read; fshell's consoleproxy waits for that on every console mode change,
  so fshell stopped after one command. Fixed in graphics `9513de1`. Check `econs_twin` (the neoui UI ROM's console)
  for the same before fshell runs on the phone's screen.
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
| DA5 robustness | Unplug and replug, RAM reboot, and a long transfer while the shell is used all work, and the monitor never goes away. Quarantine recovery, resume refresh after Mac sleep and `Bringup`'s stop on a failed halt come from roadmap T3/T4. |
| DA6 installed boot | Needs the normal-boot USB power fix, shared with FS6. The USB rework's wrapper-clock fix (`qcom,select-utmi-as-pipe-clk`, tested with the monitor's `usb cold`) is its first step. |
| Later | memoryaccess LDD port (`top`, `objinfo`, `fdb`); TRK with c32, a `TrkDriver` port and `runonphone`; OST traces; coredumps. |

## Risks and open questions

- **fshell's library closure** against our minimal ROM (DA1). This may pull in more 2010 packages than its list
  suggests.
- **The USB PDD:** `DComm`'s UART model over bulk USB endpoints needs a DFC bridge and flow control (DA3).
- **macOS naming of two ACM functions** on one device, which decides how `phone.py` finds each port (DA3).
- **ymodem speed:** 1 KB blocks, each acknowledged. If it is far below 2 MB/s, a bulk mode can follow (DA4). The USB rework found transfers bound by idle CPU clocks; its
  activity boost (`a64_usb_activity.h`) took SSH from 0.66 to 2.67 MB/s.

## References

- SymbianSource: `oss.FCL.sf.os.fshell`, `oss.FCL.sftools.dev.devicedbgsrvs`, `oss.FCL.sf.os.osrndtools`,
  `oss.FCL.sf.os.commsfw` (serial server, `serialserver/`), `oss.FCL.sf.os.usb`.
- Qt 4.8 `tools/runonphone` (TRK and CODA client, LGPL).
- [sources.md](sources.md): the FShell rows.
