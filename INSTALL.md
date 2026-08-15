# Installation Guide — Video Downloader

Everything you need to install the application and its dependencies.
Every section has a direct link — the app itself brings you here when it
detects something is missing (Settings → Dependencies).

**Table of contents**

- [Download and install the app](#descargar)
  - [macOS](#macos) · [Windows](#windows) · [Linux (.deb)](#linux-deb) · [Linux (AppImage)](#linux-appimage)
- [Deno — JavaScript engine (required for YouTube)](#deno)
- [FFmpeg (optional, recommended)](#ffmpeg)
- [AppImage libraries (GTK 3 and libmpv)](#linux-libs)
- [Visual C++ Redistributable (Windows)](#vcpp)
- [Verify the installation](#verificar)

---

<a id="descargar"></a>

## Download and install the app

Download the file for your platform from the
[latest release](https://github.com/Wachu985/Video-Downloader/releases/latest).
Everything is bundled: you do **not** need Python, yt-dlp or FFmpeg
installed to use the app.

<a id="macos"></a>

### macOS

1. Download the DMG for your Mac: `VideoDownloader-macos-arm64.dmg`
   (Apple Silicon — M1 or newer) or `VideoDownloader-macos-x86_64.dmg`
   (Intel).
2. Open it and drag **Video Downloader** to the **Applications** folder.
3. The app is unsigned: the first time, **right-click → Open** and confirm
   the Gatekeeper dialog.

<a id="windows"></a>

### Windows

1. Download the installer for your CPU:
   `VideoDownloader-windows-x64-setup.exe` (most PCs) or
   `VideoDownloader-windows-arm64-setup.exe` (Windows on ARM devices).
2. Run the installer (it creates Start Menu shortcuts and, optionally, a
   desktop shortcut).
3. If SmartScreen shows a warning: **More info → Run anyway**.

<a id="linux-deb"></a>

### Linux — Debian/Ubuntu (.deb)

1. Download the package for your CPU: `VideoDownloader-linux-amd64.deb`
   (x86_64) or `VideoDownloader-linux-arm64.deb` (ARM, e.g. Raspberry Pi).
2. Install it (the GTK 3 and libmpv dependencies are installed
   automatically):

```bash
sudo apt install ./VideoDownloader-linux-amd64.deb   # or -arm64.deb
```

3. "Video Downloader" will appear in your applications menu.

<a id="linux-appimage"></a>

### Linux — any distro (AppImage)

1. Download the AppImage for your CPU:
   `VideoDownloader-linux-x86_64.AppImage` or
   `VideoDownloader-linux-aarch64.AppImage` (ARM).
2. Make it executable and run it:

```bash
chmod +x VideoDownloader-linux-x86_64.AppImage   # or -aarch64
./VideoDownloader-linux-x86_64.AppImage
```

> The AppImage needs GTK 3 and libmpv installed on the system —
> see [AppImage libraries](#linux-libs).

---

<a id="deno"></a>

## Deno — JavaScript engine (required for YouTube)

**Without this, most YouTube downloads fail.** YouTube requires solving
JavaScript challenges and the app needs a JS engine installed on your
system. We recommend [Deno](https://deno.land) (Node.js or Bun also work).

| Platform | Command |
|---|---|
| macOS | `brew install deno` |
| Windows | `winget install deno` or `irm https://deno.land/install.ps1 \| iex` |
| Linux | `sudo snap install deno` or `curl -fsSL https://deno.land/install.sh \| sh` |

After installing it, **restart the application**. In
**Settings → Dependencies** the "JavaScript engine (YouTube)" card should
turn green.

> Age-restricted or private content also requires
> **Settings → Browser cookies** (reuses your browser session).

---

<a id="ffmpeg"></a>

## FFmpeg (optional, recommended)

The app **works without installing FFmpeg**: it ships a fallback binary
and downloads the full toolchain (ffmpeg + ffprobe) in the background on
first run. Still, a system FFmpeg is the most reliable option and always
takes priority:

| Platform | Command |
|---|---|
| macOS | `brew install ffmpeg` |
| Windows | `winget install ffmpeg` |
| Linux | `sudo apt install ffmpeg` (or your distro's package) |

What each state of the "FFmpeg status" card in Settings means:

- 🟢 **System FFmpeg** or **full bundled toolchain** — everything
  available.
- 🟡 **Bundled without ffprobe** — functional; the full version is being
  downloaded in the background and the app notifies you when it's ready.
  If the notice never arrives (e.g. no connection), install FFmpeg with
  the command above.
- 🔴 **Not available** — install FFmpeg with the command above and
  restart the app.

---

<a id="linux-libs"></a>

## AppImage libraries (GTK 3 and libmpv)

Only needed when using the **AppImage** (the `.deb` installs these
automatically):

```bash
# Debian / Ubuntu
sudo apt install libgtk-3-0 libmpv2   # on Ubuntu 22.04: libmpv1

# Fedora
sudo dnf install gtk3 mpv-libs

# Arch
sudo pacman -S gtk3 mpv
```

---

<a id="vcpp"></a>

## Visual C++ Redistributable (Windows)

Only needed if the app **does not start** on a freshly installed Windows
(missing `vcruntime140.dll` or similar):

1. Download the
   [Microsoft Visual C++ Redistributable x64](https://aka.ms/vs/17/release/vc_redist.x64.exe).
2. Install it and open the app again.

---

<a id="verificar"></a>

## Verify the installation

Open the app and go to **Settings → Dependencies**:

- **FFmpeg status** green → conversions, video+audio merging and
  thumbnails available.
- **JavaScript engine (YouTube)** green → YouTube downloads working.

The `ffmpeg` chip in the sidebar shows the same status at all times. If a
card is amber or red, click it: it brings you straight to the matching
section of this guide.

Problems? [Open an issue](https://github.com/Wachu985/Video-Downloader/issues).
