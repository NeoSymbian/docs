# Devices: which phones NeoSymbian can move to next

**Status: shortlist (2026-11-09). Only the Pixel 3a XL (bonito) is ported.** This page lists phones from the mobile
Linux device lists that NeoSymbian could boot on. They are phones with an unlockable (or no) bootloader, and with
mainline Linux support to read for register layouts. Each entry says what our port already covers and what would be
new.

## What a NeoSymbian phone needs

These come from the port's fixed decisions ([roadmap.md](roadmap.md), [port-map.md](port-map.md)):

| Need | Why | Effect on the list |
|---|---|---|
| **AArch64 cores that also run 32-bit code at EL0** | The 2010 user side runs unchanged as ARMv5TE code at AArch32 EL0 | Cortex-A53/A55/A72–A78 qualify. **Cortex-X2 and later, A715/A720 and A520 are AArch64-only** (most SoCs from 2022 on), so they are out |
| **A bootloader we can unlock**, or none at all | We boot our own `boot.img` (`fastboot boot` / `flash boot_x`) | Carrier-locked models are out (Verizon Pixels). Xiaomi makes you wait; Fairphone may need a code |
| **Mainline Linux support** | Mainline drivers and device trees are our register reference (read only, never copied) | The phone should be in Nura's `community` category, or in `testing` with a working device tree |
| GICv3 interrupt controller | `nkernsmp/arm64` implements GICv3 only | GICv2 phones (Allwinner A64) need a new interrupt back end first |
| Storage we can drive | `sdm670_assp` has SDHCI-msm (eMMC) | UFS phones need a new UFS host driver (UFSHC + its PHY) before `C:` and `Z:` work |
| A modem we can talk to | `telephony` speaks QMI over QRTR/GLINK (Qualcomm) | Qualcomm phones reuse it; a Quectel EG25 phone needs an AT-command path instead |

## Sources and how this was checked (2026-11-09)

- **Nura**, formerly postmarketOS: the project renamed itself in September 2026 ([announcement](https://nura.eco/blog/2026/09/27/nura-rename/)); `wiki.postmarketos.org` and `gitlab.postmarketos.org` now redirect to `*.nura.eco`.
  - The **category** and the **device tree name** (which names the SoC) of each phone below are taken from `pmaports`
    (`device/<category>/device-<codename>/deviceinfo`), read through the GitLab API at `gitlab.nura.eco` on
    2026-11-09.
  - The wiki pages (`wiki.nura.eco`) block automated readers, so per-device feature tables (calls, SMS, data, Wi-Fi)
    have **not** been read. Check them in a browser before choosing a device.
- **Ubuntu Touch** progress figures are from https://devices.ubuntu-touch.io on 2026-11-09. Most Ubuntu Touch ports
  run on Android kernels (Halium), not mainline, so a high figure says the hardware is well understood, not that
  mainline drivers exist. The PinePhones are the exception: they run native.
- **Fairphone unlock rules:** from https://www.fairphone.com/bootloader-unlocking-code-for-fairphone, which disagrees
  with the shop version of that page (details in the FP5 row).
- **Unverified:** CPU core types, storage type (UFS or eMMC), RAM and the modem are taken from public spec sheets as
  remembered, not checked today. Check each against the device tree (`ufshc@`/`sdhci@`, `cpu@` `compatible`)
  before porting.

## The shortlist

### Same SoC as ours

| Phone (codename) | SoC, cores | Nura | UT | Bootloader | Reuse | New work |
|---|---|---|---|---|---|---|
| **Google Pixel 3a (sargo)** | SDM670 (`qcom/sdm670-google-sargo`), Kryo 360 = A75 + A55 | community | 97.3% | Unlockable (`fastboot flashing unlock`), except Verizon | `sdm670_assp` entirely, the modem firmware layout and the whole `telephony` stack | A `sargo_variant`: its panel, touch controller, DTB and partition table. **Days, not weeks** |

### SDM845 family (2018–2020): our closest relatives

Our docs already use the Linux sdm845 drivers as a reference (`gcc-sdm845.c`, the `sdm845_mss` modem flow, IPA
v3.5.1). All of these have **UFS** storage (unverified), so a UFS driver is the main cost of the whole family.

| Phone (codename) | SoC | Nura | UT | Bootloader | Notes |
|---|---|---|---|---|---|
| **OnePlus 6 (enchilada)** | SDM845 (`qcom/sdm845-oneplus-enchilada`), A75 + A55 | community | 93.8% | `fastboot oem unlock`, no wait | Best-supported SDM845 phone in mainline Linux. Cheap used |
| **OnePlus 6T (fajita)** | SDM845 (`qcom/sdm845-oneplus-fajita`) | community | 93.8% | As OnePlus 6 | Same board as the 6 with a different panel and an optical fingerprint reader. One port covers both |
| **Xiaomi Poco F1 (beryllium)** | SDM845 | community | 91.2% | Xiaomi Mi Unlock: account binding and a waiting period | Two panel variants (Tianma, EBBG) |
| **SHIFT6mq (axolotl)** | SDM845 (`qcom/sdm845-shift-axolotl`) | community | 82.1% | Unlockable | Small maker, fewer units around |
| **Google Pixel 3 (blueline)** | SDM845 (`qcom/sdm845-google-blueline`) | testing | — | Unlockable, except Verizon | Mainline support behind the OnePlus 6 |

### Newer Qualcomm (2020–2024): still AArch32-capable

| Phone (codename) | SoC | Nura | UT | Bootloader | Notes |
|---|---|---|---|---|---|
| **Fairphone 4 (fp4)** | SM7225 (`qcom/sm7225-fairphone-fp4`), A76 + A55 | community | 97.3% | Official; may need a Fairphone code (see FP5) | Repairable, long support. UFS; newer clock and power blocks |
| **Fairphone 5 (fp5)** | QCM6490 (`qcom/qcm6490-fairphone-fp5`), A78 + A55 | testing | 97.4% | Official. Fairphone is dropping the unlock code ("enable it in Developer options"), but the shop page still offers codes for FP4/FP5 and says the change so far covers the FP3 only. **Has anti-rollback: never relock with our image** | The best long-term daily phone. UFS. Shares QCM6490 with the SHIFTphone 8 |
| **SHIFTphone 8 (otter)** | QCM6490 (`qcom/qcm6490-shift-otter`) | testing | — | Unlockable | Same SoC as the FP5: one `qcm6490_assp` would serve both |
| **Nothing Phone (1) (spacewar)** | SM7325 (`qcom/sm7325-nothing-spacewar`), A78 + A55 | testing | 95.6% | Unlockable | A close relative of the QCM6490 (both are Kodiak/SC7280 family) |
| **OnePlus 8T (kebab), 8 Pro (instantnoodlep)** | SM8250, A77 + A55 | testing | — | Unlockable | Flagship-class SoC; more blocks to bring up |

### Open by default (no bootloader lock at all)

| Phone (codename) | SoC | Nura | UT | Reuse | New work |
|---|---|---|---|---|---|
| **PinePhone Pro (pinephonepro)** | RK3399 (`rockchip/rk3399-pinephone-pro`), A72 + A53 | community | 69% (native) | GICv3 (GIC-500); eMMC on a standard SDHCI (Arasan), so the generic parts of our SDHCI code carry over | A new `rk3399_assp` (clocks, I2C, display). The **Quectel EG25-G** modem is driven by AT commands (unverified: over UART and USB), not QMI |
| **PinePhone (pinephone)** | Allwinner A64 (`allwinner/sun50i-a64-pinephone-1.x`), A53 | **testing** (was main) | 67.3% (native) | Phorepoc already has an A64 board bootstrap (`os/src/phorepoc-arm/a64/bootstrap`, [sources.md](sources.md)) | **GICv2 (GIC-400)**: a new interrupt back end; a slow CPU; 2–3 GB RAM; EG25-G modem |
| **Purism Librem 5 (librem5)** | i.MX8MQ (`freescale/imx8mq-librem5-r2..r4`), A53 | community | — | GICv3; eMMC (uSDHC) | A new SoC; slow; expensive; the modem is a plug-in M.2 card |

## Out, and why

- **Fairphone (Gen. 6)** (`qcom/milos-fairphone-fp6`, Nura testing): its Snapdragon 7s Gen 3 has Cortex-A720 + A520
  cores, which are AArch64-only (unverified), so the 32-bit user side can't run.
- **Most phones from 2022 on** (Snapdragon 8 Gen 1 and later, Dimensity 9000 and later): the big cores, and often all
  cores, are AArch64-only. A big.LITTLE phone with some 32-bit-capable cores would need the scheduler to keep every
  user thread on them; that isn't worth it.
- **MediaTek and Exynos phones:** mainline Linux support is thin, so there is little register reference to read.
  Ubuntu Touch runs them on Android kernels.
- **Carrier-locked models** (Verizon Pixels, many US OnePlus carrier units): the bootloader can't be unlocked.

## Recommendation

1. **Pixel 3a (sargo):** a second board for almost no work. It proves that the board/SoC split in
   `kernel/baseport/arm64` holds and gives us a cheap spare test phone.
2. **OnePlus 6 / 6T:** the second SoC (`sdm845_assp`). Build the **UFS driver** here; it then serves every later
   Qualcomm phone. `telephony` carries over mostly unchanged.
3. **Fairphone 5** (or SHIFTphone 8, same SoC): the long-term daily phone. It reuses the UFS driver and the QMI stack.
4. **PinePhone Pro:** only if "open hardware, no bootloader lock" matters more than reuse. It means a new SoC and an
   AT-command modem path.

## Adding a device

- **Kernel:** a new `kernel/baseport/arm64/<board>_variant` (+ `<soc>_assp` for a new SoC), as in the baseport
  README. Keep the phone's DTB out of git, like `private/bonito.dtb`.
- **Before buying:** check the Nura wiki page's feature table in a browser, and the exact model number (carrier lock,
  regional variant).
- **When a port lands:** move its row to a "Ported" table here, and update [roadmap.md](roadmap.md) and the org
  profile.
