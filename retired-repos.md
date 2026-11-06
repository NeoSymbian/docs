# Retired repositories

On 2026-11-06, after the restructure into `kernel`, `build` and `docs`, these 91 repositories were deleted from the
NeoSymbian organization: nothing builds from them any more. This page keeps what is needed to bring any of them back.

## Restoring one

- **A fork with no commits of ours** (most of them): fork it again and, if a build needs it, pin the commit below.
  ```sh
  gh repo fork <upstream> --org NeoSymbian --clone=false
  ```
- **`core`, `pdk`** (our commits are in [`retired/`](retired)): fork Phorepoc's repo again and put our commits
  on a branch (the bundle holds `refs/remotes/origin/main`, our `main` when it was deleted); make that branch the
  default, or move `main` to it, in the repository's settings:
  ```sh
  gh repo fork Phorepoc/core --org NeoSymbian --clone=true && cd core
  git fetch ../docs/retired/core.bundle refs/remotes/origin/main:neosymbian
  git push origin neosymbian
  ```
- **`symbian-pixel`** (the whole history, tag `pre-restructure`): `git clone docs/retired/symbian-pixel.bundle symbian-pixel`.
- **Pins:** [`retired/core-sources.lock`](retired/core-sources.lock) is core's `sources.lock`, the commit of every
  SymbianSource package the Phorepoc build used (trees `symbian-2010` = master, `symbian-rcl3` = BRANCH_RCL_3).

## Our own and Phorepoc's

| Repository | Forked from | Our commits | What it was |
|---|---|---|---|
| `adaptation-a64` | Phorepoc/adaptation-a64 | none | Phorepoc's ARMv8 (AArch32) port: a reference while porting |
| `adaptation-x86-64` | Phorepoc/adaptation-x86-64 | none | Phorepoc's x86-64 port: the template for the arm64 port |
| `core` | Phorepoc/core | 5 (`retired/core.bundle`) | Phorepoc's component registry and modern-GCC shims; replaced by NeoSymbian/build |
| `pdk` | Phorepoc/pdk | 4 (`retired/pdk.bundle`) | Phorepoc's phe, emitter, rombuild, PhoneLab/phedbg; rombuild --section now in kernel/baseport/arm64/tools |
| `symbian-pixel` | — | all (`retired/symbian-pixel.bundle`) | the port's first home; code -> NeoSymbian/kernel, docs -> NeoSymbian/docs, zimaos -> NeoSymbian/build |

## SymbianSource packages (no commits of ours)

Used only by Phorepoc's full Symbian^3 build (core's registry); NeoSymbian/build pins its own 12.

| Package | Forked from | Pinned in core (tree `commit`) |
|---|---|---|
| `oss.API_REF.Public_API` | SymbianSource/oss.API_REF.Public_API | symbian-2010 `c8cfcfafc0` |
| `oss.FCL.examples.WebRT` | SymbianSource/oss.FCL.examples.WebRT | symbian-2010 `ebb0d1b55f` |
| `oss.FCL.sf.adapt.codecs.aricent` | SymbianSource/oss.FCL.sf.adapt.codecs.aricent | symbian-2010 `26ce2bf921` |
| `oss.FCL.sf.adapt.NokiaGraphics` | SymbianSource/oss.FCL.sf.adapt.NokiaGraphics | symbian-2010 `eb80018528` |
| `oss.FCL.sf.adapt.NokiaMMAudioReference` | SymbianSource/oss.FCL.sf.adapt.NokiaMMAudioReference | symbian-2010 `835faa284b` |
| `oss.FCL.sf.adapt.stubs` | SymbianSource/oss.FCL.sf.adapt.stubs | symbian-2010 `6682e8c27b` |
| `oss.FCL.sf.app.camera` | SymbianSource/oss.FCL.sf.app.camera | symbian-rcl3 `0de394c23d` |
| `oss.FCL.sf.app.commonemail` | SymbianSource/oss.FCL.sf.app.commonemail | symbian-2010 `6a784f9441` |
| `oss.FCL.sf.app.contacts` | SymbianSource/oss.FCL.sf.app.contacts | symbian-rcl3 `22bf872e5e` |
| `oss.FCL.sf.app.files` | SymbianSource/oss.FCL.sf.app.files | symbian-rcl3 `c2b26f14b1` |
| `oss.FCL.sf.app.helps` | SymbianSource/oss.FCL.sf.app.helps | symbian-rcl3 `9239cc69fd` |
| `oss.FCL.sf.app.homescreen` | SymbianSource/oss.FCL.sf.app.homescreen | symbian-rcl3 `aa623cf29e` |
| `oss.FCL.sf.app.iptelephony` | SymbianSource/oss.FCL.sf.app.iptelephony | symbian-rcl3 `8279c5f6a2` |
| `oss.FCL.sf.app.JRT` | SymbianSource/oss.FCL.sf.app.JRT | symbian-2010 `0822c2dcfb` |
| `oss.FCL.sf.app.messaging` | SymbianSource/oss.FCL.sf.app.messaging | symbian-2010 `7ecf4269c5`, symbian-rcl3 `2c5503f308` |
| `oss.FCL.sf.app.mmsharinguis` | SymbianSource/oss.FCL.sf.app.mmsharinguis | symbian-2010 `9054f87d8e` |
| `oss.FCL.sf.app.musicplayer` | SymbianSource/oss.FCL.sf.app.musicplayer | symbian-rcl3 `c953c47942` |
| `oss.FCL.sf.app.organizer` | SymbianSource/oss.FCL.sf.app.organizer | symbian-2010 `e15734d194`, symbian-rcl3 `cb3eae4e74` |
| `oss.FCL.sf.app.phone` | SymbianSource/oss.FCL.sf.app.phone | symbian-2010 `e52263e6b7`, symbian-rcl3 `17f1eec5d5` |
| `oss.FCL.sf.app.photos` | SymbianSource/oss.FCL.sf.app.photos | symbian-2010 `e61097591e`, symbian-rcl3 `f3385bf8f9` |
| `oss.FCL.sf.app.profile` | SymbianSource/oss.FCL.sf.app.profile | symbian-rcl3 `5294c6ae39` |
| `oss.FCL.sf.app.radio` | SymbianSource/oss.FCL.sf.app.radio | symbian-2010 `ebab77d7c8`, symbian-rcl3 `2510696f77` |
| `oss.FCL.sf.app.recents` | SymbianSource/oss.FCL.sf.app.recents | symbian-2010 `28243f08d7` |
| `oss.FCL.sf.app.screensaver` | SymbianSource/oss.FCL.sf.app.screensaver | symbian-rcl3 `e14e0c211c` |
| `oss.FCL.sf.app.settingsuis` | SymbianSource/oss.FCL.sf.app.settingsuis | symbian-rcl3 `904d7655dc` |
| `oss.FCL.sf.app.utils` | SymbianSource/oss.FCL.sf.app.utils | symbian-rcl3 `18752ab088` |
| `oss.FCL.sf.app.videoplayer` | SymbianSource/oss.FCL.sf.app.videoplayer | symbian-2010 `9a98fb6eaa` |
| `oss.FCL.sf.app.voicerec` | SymbianSource/oss.FCL.sf.app.voicerec | symbian-2010 `dd70927648`, symbian-rcl3 `0880f972c6` |
| `oss.FCL.sf.app.webuis` | SymbianSource/oss.FCL.sf.app.webuis | symbian-rcl3 `e89af2df07` |
| `oss.FCL.sf.incubator.stemkit` | SymbianSource/oss.FCL.sf.incubator.stemkit | symbian-2010 `90fe5d80cd` |
| `oss.FCL.sf.mw.accesssec` | SymbianSource/oss.FCL.sf.mw.accesssec | symbian-2010 `a962f00c1a`, symbian-rcl3 `8a1dd8bb44` |
| `oss.FCL.sf.mw.appinstall` | SymbianSource/oss.FCL.sf.mw.appinstall | symbian-2010 `760927eba6`, symbian-rcl3 `8262df3e5a` |
| `oss.FCL.sf.mw.appsupport` | SymbianSource/oss.FCL.sf.mw.appsupport | symbian-2010 `3efd2b6c5a`, symbian-rcl3 `aba0c0bd07` |
| `oss.FCL.sf.mw.btservices` | SymbianSource/oss.FCL.sf.mw.btservices | symbian-2010 `f6a4b12b2d`, symbian-rcl3 `4cafb2cb6f` |
| `oss.FCL.sf.mw.camerasrv` | SymbianSource/oss.FCL.sf.mw.camerasrv | symbian-2010 `e9e363d474` |
| `oss.FCL.sf.mw.classicui` | SymbianSource/oss.FCL.sf.mw.classicui | symbian-2010 `dcea899751`, symbian-rcl3 `c8e3af2baa` |
| `oss.FCL.sf.mw.dlnasrv` | SymbianSource/oss.FCL.sf.mw.dlnasrv | symbian-2010 `276d76e32f` |
| `oss.FCL.sf.mw.drm` | SymbianSource/oss.FCL.sf.mw.drm | symbian-2010 `43dc91f0ed`, symbian-rcl3 `9beef8e9bb` |
| `oss.FCL.sf.mw.gsprofilesrv` | SymbianSource/oss.FCL.sf.mw.gsprofilesrv | symbian-2010 `bcc69d3ba5`, symbian-rcl3 `9c9185f1b4` |
| `oss.FCL.sf.mw.hapticsservices` | SymbianSource/oss.FCL.sf.mw.hapticsservices | symbian-2010 `c7de8cb68b`, symbian-rcl3 `385e5617a8` |
| `oss.FCL.sf.mw.hb` | SymbianSource/oss.FCL.sf.mw.hb | symbian-2010 `dae755d5c5` |
| `oss.FCL.sf.mw.helix` | SymbianSource/oss.FCL.sf.mw.helix | symbian-2010 `6d11df7b9f` |
| `oss.FCL.sf.mw.homescreensrv` | SymbianSource/oss.FCL.sf.mw.homescreensrv | symbian-2010 `e60a802a17`, symbian-rcl3 `b4a062c403` |
| `oss.FCL.sf.mw.imghandling` | SymbianSource/oss.FCL.sf.mw.imghandling | symbian-2010 `f81ed9b070` |
| `oss.FCL.sf.mw.imsrv` | SymbianSource/oss.FCL.sf.mw.imsrv | symbian-2010 `9f988dd051` |
| `oss.FCL.sf.mw.inputmethods` | SymbianSource/oss.FCL.sf.mw.inputmethods | symbian-2010 `51e877bef2`, symbian-rcl3 `508e00db21` |
| `oss.FCL.sf.mw.ipappprotocols` | SymbianSource/oss.FCL.sf.mw.ipappprotocols | symbian-2010 `62e4b48a47` |
| `oss.FCL.sf.mw.ipconnmgmt` | SymbianSource/oss.FCL.sf.mw.ipconnmgmt | symbian-2010 `7c6f294faf`, symbian-rcl3 `a8e3d39df1` |
| `oss.FCL.sf.mw.legacypresence` | SymbianSource/oss.FCL.sf.mw.legacypresence | symbian-2010 `4806876911` |
| `oss.FCL.sf.mw.locationsrv` | SymbianSource/oss.FCL.sf.mw.locationsrv | symbian-2010 `282094c09b` |
| `oss.FCL.sf.mw.mds` | SymbianSource/oss.FCL.sf.mw.mds | symbian-2010 `6a33672726` |
| `oss.FCL.sf.mw.messagingmw` | SymbianSource/oss.FCL.sf.mw.messagingmw | symbian-2010 `7af85768c2`, symbian-rcl3 `5d75e70160` |
| `oss.FCL.sf.mw.metadatasrv` | SymbianSource/oss.FCL.sf.mw.metadatasrv | symbian-2010 `4fcbe46aad` |
| `oss.FCL.sf.mw.mmappfw` | SymbianSource/oss.FCL.sf.mw.mmappfw | symbian-2010 `f6d6d94e16` |
| `oss.FCL.sf.mw.mmmw` | SymbianSource/oss.FCL.sf.mw.mmmw | symbian-2010 `038ca7403b` |
| `oss.FCL.sf.mw.mmuifw` | SymbianSource/oss.FCL.sf.mw.mmuifw | symbian-rcl3 `9a14a84466` |
| `oss.FCL.sf.mw.netprotocols` | SymbianSource/oss.FCL.sf.mw.netprotocols | symbian-2010 `cc43765893` |
| `oss.FCL.sf.mw.phonesrv` | SymbianSource/oss.FCL.sf.mw.phonesrv | symbian-2010 `fae51ff53b`, symbian-rcl3 `44089abe39` |
| `oss.FCL.sf.mw.qtmobility` | SymbianSource/oss.FCL.sf.mw.qtmobility | symbian-2010 `a462a7d949` |
| `oss.FCL.sf.mw.remoteconn` | SymbianSource/oss.FCL.sf.mw.remoteconn | symbian-2010 `dc4c3e82a6` |
| `oss.FCL.sf.mw.remotemgmt` | SymbianSource/oss.FCL.sf.mw.remotemgmt | symbian-2010 `6a5ae0a1c1`, symbian-rcl3 `68234299a8` |
| `oss.FCL.sf.mw.remotestorage` | SymbianSource/oss.FCL.sf.mw.remotestorage | symbian-2010 `faf0a1c4ee`, symbian-rcl3 `1940cc962f` |
| `oss.FCL.sf.mw.searchsrv` | SymbianSource/oss.FCL.sf.mw.searchsrv | symbian-2010 `c32bf1f2c3` |
| `oss.FCL.sf.mw.securitysrv` | SymbianSource/oss.FCL.sf.mw.securitysrv | symbian-2010 `c9e2e54cd8`, symbian-rcl3 `88db46027e` |
| `oss.FCL.sf.mw.serviceapi` | SymbianSource/oss.FCL.sf.mw.serviceapi | symbian-rcl3 `c9f9eee5f5` |
| `oss.FCL.sf.mw.serviceapifw` | SymbianSource/oss.FCL.sf.mw.serviceapifw | symbian-rcl3 `ed6dbc4997` |
| `oss.FCL.sf.mw.srvdiscovery` | SymbianSource/oss.FCL.sf.mw.srvdiscovery | symbian-2010 `aee61f178f` |
| `oss.FCL.sf.mw.svgt` | SymbianSource/oss.FCL.sf.mw.svgt | symbian-2010 `a6e9f61716` |
| `oss.FCL.sf.mw.uiaccelerator` | SymbianSource/oss.FCL.sf.mw.uiaccelerator | symbian-2010 `773fc5e215` |
| `oss.FCL.sf.mw.uitools` | SymbianSource/oss.FCL.sf.mw.uitools | symbian-2010 `32b8b16c02` |
| `oss.FCL.sf.mw.usbservices` | SymbianSource/oss.FCL.sf.mw.usbservices | symbian-2010 `ea7d525c67` |
| `oss.FCL.sf.mw.videoutils` | SymbianSource/oss.FCL.sf.mw.videoutils | symbian-2010 `c70acb1c67` |
| `oss.FCL.sf.mw.vpnclient` | SymbianSource/oss.FCL.sf.mw.vpnclient | symbian-2010 `bc2c6ceb96` |
| `oss.FCL.sf.mw.web` | SymbianSource/oss.FCL.sf.mw.web | symbian-2010 `50303e652d`, symbian-rcl3 `1be4845a2c` |
| `oss.FCL.sf.mw.websrv` | SymbianSource/oss.FCL.sf.mw.websrv | symbian-2010 `b7e97dc133` |
| `oss.FCL.sf.mw.wirelessacc` | SymbianSource/oss.FCL.sf.mw.wirelessacc | symbian-rcl3 `512c918663` |
| `oss.FCL.sf.os.bt` | SymbianSource/oss.FCL.sf.os.bt | symbian-2010 `ba9e7d24a7` |
| `oss.FCL.sf.os.cellularsrv` | SymbianSource/oss.FCL.sf.os.cellularsrv | symbian-2010 `d33b71b9b4` |
| `oss.FCL.sf.os.commsfw` | SymbianSource/oss.FCL.sf.os.commsfw | symbian-2010 `bc8ac1a6d5` |
| `oss.FCL.sf.os.imagingext` | SymbianSource/oss.FCL.sf.os.imagingext | symbian-2010 `b09b4dba96` |
| `oss.FCL.sf.os.lbs` | SymbianSource/oss.FCL.sf.os.lbs | symbian-2010 `7190b98a3d` |
| `oss.FCL.sf.os.networkingsrv` | SymbianSource/oss.FCL.sf.os.networkingsrv | symbian-2010 `b283ce17f2` |
| `oss.FCL.sf.os.usb` | SymbianSource/oss.FCL.sf.os.usb | symbian-2010 `34b79e372c` |
| `oss.FCL.sf.os.wlan` | SymbianSource/oss.FCL.sf.os.wlan | symbian-2010 `7d13c530be`, symbian-rcl3 `d97d09fbe5` |
| `oss.FCL.sf.os.xmlsrv` | SymbianSource/oss.FCL.sf.os.xmlsrv | symbian-2010 `333ed3d1a8` |
| `oss.FCL.sftools.dev.ui` | SymbianSource/oss.FCL.sftools.dev.ui | symbian-2010 `969ab3746b` |
