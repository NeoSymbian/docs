<!-- SPDX-License-Identifier: Apache-2.0 -->
# UFS on SDM845: what mainline Linux does (reference for the 6T's UFS driver)

Part of [Hardware](../README.md) · Status: reference · Updated: 2026-11-27

This page lists facts read from mainline Linux (torvalds/master, 2026-11): `drivers/ufs/core/ufshcd.c`,
`drivers/ufs/host/ufs-qcom.c`, `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c`, `drivers/clk/qcom/gcc-sdm845.c`,
`arch/arm64/boot/dts/qcom/sdm845*.dtsi`, `drivers/interconnect/qcom/sdm845.c`. It records register offsets, values
and the order of operations. **No code is copied:** Linux is GPL-2.0, and our driver is written from these facts
(Apache-2.0). Values marked *unverified* need checking on the phone. Parent: [fajita.md](fajita.md) (OP6, U1–U6).

## Addresses

| Block | Base |
|---|---|
| UFS host (UFSHCI 2.1 + Qualcomm registers) | 0x01d84000, size 0x2500; SPI 265 (INTID 297), level |
| QMP UFS PHY v3 | 0x01d87000; serdes +0x000, tx lane 0 +0x400, rx lane 0 +0x600, tx lane 1 +0x800, rx lane 1 +0xa00, pcs +0xc00 |
| ICE | 0x01d90000 (not used: Linux without UFS crypto never touches it) |
| SMMU | stream 0x100, mask 0xf |

## Power, clocks, resets

- **Supplies (live DT, downstream):**
  - vcc = l20 (2.95 V)
  - vccq2 = s4 (1.8 V)
  - PHY vdda-phy = l1 (0.88 V), vdda-pll = l26 (1.2 V)
  - reference-clock supply = l2 (1.2 V)
  - Mainline's OnePlus DT has no vccq2.
- **GDSC:** `ufs_phy_gdsc`, GDSCR 0x177004.
- **Core reset:** GCC_UFS_PHY_BCR 0x177000 bit 0. Assert, wait 200 µs, deassert, wait 1 ms.
- **Device reset:** `ufs_reset` pad (mainline: "gpio 150"), active low. Hold 10 µs, release, wait 10 µs.

**Clocks** (CBCR bit 31 = off; bit 0 = enable):

| Linux name | GCC branch | RCG | Rate Linux sets |
|---|---|---|---|
| core_clk | UFS_PHY_AXI 0x17700c | 0x17701c | 200 MHz (GPLL0 / 3) |
| bus_aggr_clk | AGGRE_UFS_PHY_AXI 0x182024 | — | — |
| iface_clk | UFS_PHY_AHB 0x177010 | — | — |
| core_clk_unipro | UFS_PHY_UNIPRO_CORE 0x177054 | 0x177074 | 150 MHz (GPLL0 / 4) |
| ice_core_clk | UFS_PHY_ICE_CORE 0x177058 | 0x17705c | 300 MHz |
| tx_lane0_sync | UFS_PHY_TX_SYMBOL_0 0x177014 | — | — (no halt check) |
| rx_lane0_sync | UFS_PHY_RX_SYMBOL_0 0x177018 | — | — |
| rx_lane1_sync | UFS_PHY_RX_SYMBOL_1 0x1770a8 | — | — |
| PHY ref_aux | UFS_PHY_PHY_AUX 0x17708c | 0x177090 | XO |
| PHY qref | UFS_MEM_CLKREF 0x18c000 | — | — |

## Host registers

| Group | Offset | Register |
|---|---|---|
| UFSHCI | 0x00 | CAP (NUTRS [4:0] + 1, NUTMRS [18:16] + 1, AH8 bit 23) |
| UFSHCI | 0x08 | VER |
| UFSHCI | 0x18 | AHIT |
| UFSHCI | 0x20 | IS |
| UFSHCI | 0x24 | IE |
| UFSHCI | 0x30 | HCS (DP 0, UTRLRDY 1, UTMRLRDY 2, UCRDY 3, UPMCRS [10:8]) |
| UFSHCI | 0x34 | HCE |
| UFSHCI | 0x38–0x48 | UECPA / UECDL / UECN / UECT / UECDME |
| UFSHCI | 0x4c | UTRIACR |
| UFSHCI | 0x50 / 0x54 | UTRLBA / UTRLBAU |
| UFSHCI | 0x58 | UTRLDBR |
| UFSHCI | 0x5c | UTRLCLR (write 0 to clear a slot) |
| UFSHCI | 0x60 | UTRLRSR |
| UFSHCI | 0x70–0x80 | the task list's base, doorbell, clear and run-stop |
| UFSHCI | 0x90–0x9c | UICCMD, ARG1–3 |
| Qualcomm | 0xdc | UFS_CFG1 (bit 0 QUNIPRO_SEL, bit 1 PHY soft reset, bit 26 device reference clock enable) |
| Qualcomm | 0xe0 | UFS_CFG2 |
| Qualcomm | 0xe4 | HW_VERSION (major [31:28]; SDM845 3, *unverified*) |
| Qualcomm | 0xfc | UFS_AH8_CFG |

- **IS bits:**
  - UTRCS 0x1, UE 0x4, UPMS 0x10, UHXS 0x20, UHES 0x40, ULLS 0x80;
  - UTMRCS 0x200, UCCS 0x400, DFES 0x800, UTPES 0x1000;
  - HCFES 0x10000, SBFES 0x20000, CEFES 0x40000.

## Bring-up order (Linux, for this v3 core)

1. **Power up:**
   1. Turn on vcc, set the clock rates (AXI 200 MHz, unipro 150 MHz), and enable every host clock.
   2. Vote the bus: `ufs-ddr` 7643136 KB/s peak, `cpu-ufs` 819200.
   3. Pulse the device reset.
2. **HCE off:** if HCE is 1, write 0 and poll for 0 (1 ms).
3. **Vendor pre-change** (`ufs_qcom_power_up_sequence`):
   1. Pulse the GCC BCR.
   2. Power the PHY off, then on: supplies, the ref / ref_aux / qref clocks, then PCS+0x004 |= 1.
   3. Calibrate:
      1. UFS_CFG1 |= bit 1, wait 1 ms.
      2. Write the tables below in order: serdes, tx, rx, tx lane 1, rx lane 1, pcs, then the HS-B overlay.
      3. UFS_CFG1 &= ~bit 1, wait 1 ms.
      4. PCS+0x000 |= 1 (start).
      5. Poll PCS+0x160 bit 0 every 200 µs, for up to 10 ms.
   4. UFS_CFG1 |= bit 0, then enable the lane clocks (tx0, rx0, rx1).
4. **HCE on:** write 1, wait 1 ms, poll for 1 (50 ms). Then IE |= 0x470.
5. **Vendor post-change:**
   1. Poll DME_GET 0x0041 (TX FSM state, selector 0) until it reads 1, i.e. HIBERN8 (100 ms).
   2. UFS_CFG2 |= 0xff.
   3. DME read-modify-writes: 0xa00b |= 0x3ff, 0x9004 |= 0x1ff, 0xd002 |= bit 9.
6. **Link startup**, up to 4 tries; each failure re-runs steps 2–5:
   1. Pre:
      - DME 0xd002: bits [7:0] = 150, clear bit 8;
      - DME_SET 0x155e (PA_LOCAL_TX_LCC_ENABLE) = 0.
   2. Send the UIC command DME_LINKSTARTUP (0x16). It completes on IS.UCCS; ARG2[7:0] = 0 means success. Then HCS.DP
      must be set.
   3. Check PA_CONNECTEDTX/RXDATALANES (0x1561 / 0x1581) = 2.
   4. Post: UFS_AH8_CFG |= 0x3c if CAP.AH8. Read UECPA once.
7. **Operational:**
   1. IE = 0x71ef5.
   2. UTRIACR = 0.
   3. Write the list bases.
   4. Require HCS 0xe, then set both run-stop registers to 1.
8. **Device:**
   1. NOP OUT (10 tries, 50 ms each).
   2. Query SET_FLAG fDeviceInit (idn 1).
   3. Poll READ_FLAG fDeviceInit until it reads 0 (1.5 s).
9. **Descriptors:**
   - device (idn 0): manufacturer ID at 0x18, spec at 0x10, LUN count at 0x06;
   - geometry (idn 7);
   - power (idn 8).
10. **Gear up to HS-G3, Rate B, 2 lanes:**
    1. UFS_CFG1 |= bit 26.
    2. The device's quirks (below).
    3. The DME_SETs in the next table, in order.
    4. DME_SET PA_PWRMODE 0x1571 = 0x11. It completes on IS 0x70 (UPMS), not UCCS. Then HCS.UPMCRS must equal 1
       (PWR_LOCAL).
    5. Vote the bus down: `ufs-ddr` 1492582 KB/s, `cpu-ufs` 204800.

| Attribute | ID | Value |
|---|---|---|
| PA_RXGEAR | 0x1583 | 3 |
| PA_ACTIVERXDATALANES | 0x1580 | 2 |
| PA_RXTERMINATION | 0x1584 | 1 |
| PA_TXGEAR | 0x1568 | 3 |
| PA_ACTIVETXDATALANES | 0x1560 | 2 |
| PA_TXTERMINATION | 0x1569 | 1 |
| PA_HSSERIES | 0x156a | 2 |
| PA_PWRMODEUSERDATA0–5 | 0x15b0–0x15b5 | 8191, 65535, 32767, 8191, 65535, 32767 |
| DME_LocalFC0ProtectionTimeOutVal | 0xd041 | 8191 |
| DME_LocalTC0ReplayTimeOutVal | 0xd042 | 65535 |
| DME_LocalAFC0ReqTimeOutVal | 0xd043 | 32767 |

**UIC command encoding:**
- ARG1 = attr << 16 | selector; ARG3 = the value.
- Opcodes: DME_GET 0x01, DME_SET 0x02, DME_PEER_GET 0x03, DME_PEER_SET 0x04, DME_LINKSTARTUP 0x16.

**The bus path:**
- `ufs-ddr` runs through BCMs SN9, SN0, SH0 and MC0/ACV;
- `cpu-ufs` runs through SN12, SN3 and CN0.

## PHY tables (SDM845, written as 32-bit words; offset = value)

| Table | Base | Entries |
|---|---|---|
| serdes | +0x000 | 03c=02 034=04 00c=0a 048=07 15c=06 080=d5 088=20 138=30 13c=00 090=01 0ec=00 154=00 0f0=04 164=05 104=ff 108=00 0b0=82 060=06 068=16 070=36 0d8=3f 0dc=00 0f4=da 0f8=01 098=ff 09c=0c 0b4=98 064=06 06c=16 074=36 0e0=3f 0e4=00 0fc=c1 100=00 0a4=32 0a8=0f |
| tx | +0x400, then +0x800 | 08c=06 044=04 048=07 |
| rx | +0x600, then +0xa00 | 108=24 104=0f 10c=1e 11c=40 030=0b 07c=5b 0d4=06 0d8=04 0dc=1b 024=04 028=04 02c=04 034=4b 044=81 03c=80 164=59 |
| pcs | +0xc00 | 140=6e 02c=0a 034=02 134=03 1bc=43 13c=0f 138=9a 1c4=02 |
| HS-B overlay (last) | serdes | 0f0=44 |

## Descriptors and UPIUs (UPIU fields are big-endian)

- **UTRD**, 32 bytes, little-endian:
  - DW0 = 1 << 28 | DD << 25 | I << 24, where DD is 0 (none), 1 (host to device) or 2 (device to host);
  - DW2 = OCS, set to 0x0f before issuing;
  - DW4 = the UCD's physical address;
  - DW6 = response offset << 16 | response length, both in dwords;
  - DW7 = PRDT offset << 16 | PRDT entries.
- **PRDT entry:** the address; DW3 = bytes − 1, at most 256 KB, a multiple of 4.
- **UPIU header:**
  - [0] transaction code, [1] flags, [2] LUN, [3] tag;
  - [5] query function, [6] response, [7] status;
  - [10..11] data segment length.
- **COMMAND** 0x01:
  - flags 0x40 = read, 0x20 = write;
  - [12..15] the expected transfer length;
  - [16..31] the CDB.
  - Answered by RESPONSE 0x21, with sense data at 32: a 2-byte length, then the data.
- **QUERY** 0x16:
  - [5] = 0x01 read / 0x81 write;
  - [12] opcode, [13] idn, [14] index, [15] selector, [18..19] length, [20..23] value;
  - opcodes: 1 READ_DESC, 2 WRITE_DESC, 3 READ_ATTR, 4 WRITE_ATTR, 5 READ_FLAG, 6 SET_FLAG, 7 CLEAR_FLAG;
  - the answer is 0x36, with [6] = 0 on success, the flag value in [23] bit 0, and descriptor data from offset 32.
- **NOP OUT** 0x00 is answered by NOP IN 0x20.
- **CDBs:**
  - WRITE(10): `2a 00 LBA[4] 00 len[2] 00`
  - SYNCHRONIZE CACHE(10): `35`
  - UNMAP: `42 … 00 18 00`, with a 24-byte parameter list: `00 16 00 10 00000000 LBA(be64) count(be32) 00000000`
- **Completion:** Linux takes `~UTRLDBR & outstanding` (no interrupt aggregation), then each slot's OCS.

## Errors (Linux, reduced)

- **The error IS bits:** UE 0x4 (then read the UEC* registers), DFES, HCFES, SBFES, CEFES, ULLS, UTPES.
- **A full reset** ("host reset and restore", up to 5 tries):
  1. Pulse the device reset.
  2. HCE off.
  3. Fail everything outstanding.
  4. The bring-up steps 2–8 and step 10.
- **Aborting one request:** clear its doorbell bit through UTRLCLR = ~(1 << slot), then wait for the bit to drop
  (1 s).

## Device quirks (by manufacturer ID)

| Vendor | ID | Quirks Linux applies |
|---|---|---|
| Samsung | 0x1ce | peer DME_SET 0x1552 (PA_TXHSG1SYNCLENGTH) = 0x4a; DME_SET 0x0037 (TX_HS_EQUALIZER) = 0 on both lanes before the gear change; PA_TACTIVATE 0x15a8 from the host/peer granularity; PA_HIBERN8TIME 0x15a7 + 1 |
| SK hynix | 0x1ad | DME 0x9000 \|= bit 12 |
| Toshiba | 0x198 | PA_TACTIVATE = 10 (some parts) |
| Micron | 0x12c | — |
| WDC | 0x145 | the host's PA_TACTIVATE |
