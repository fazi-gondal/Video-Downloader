# Video Downloader

Advanced desktop media download manager built with [Flet](https://flet.dev)
(Flutter-powered UI), [yt-dlp](https://github.com/yt-dlp/yt-dlp) (download
engine) and FFmpeg (media processing).


## Screenshots

### Main window
| | |
|---|---|
<img width="100%"  alt="Captura de pantalla 2026-08-02 a las 1 27 58 a  m" src="https://github.com/user-attachments/assets/87021dc9-8654-439a-9178-2a54f88d7823" /> | <img width="100%"  alt="Captura de pantalla 2026-08-02 a las 1 28 18 a  m" src="https://github.com/user-attachments/assets/470b6573-70de-4364-904d-73cea637f4f8" /> |

### Download Selection
| | |
|---|---|
<img width="100%"   alt="Captura de pantalla 2026-08-02 a las 1 28 48 a  m" src="https://github.com/user-attachments/assets/518d887b-2418-4342-87fd-6fef44edcab1" /> | <img width="100%"   alt="Captura de pantalla 2026-08-02 a las 1 28 51 a  m" src="https://github.com/user-attachments/assets/9f55ddd8-4183-4772-a72f-6defd18160a4" /> |


### Format explorer
| | |
|---|---|
<img width="100%"   alt="Captura de pantalla 2026-08-02 a las 1 28 03 a  m" src="https://github.com/user-attachments/assets/e5611565-c517-4ef2-80d0-db28ef1bbfa1" /> | <img width="100%"   alt="Captura de pantalla 2026-08-02 a las 1 28 23 a  m" src="https://github.com/user-attachments/assets/fd39055b-93e0-4dee-91f2-cbf97434799f" /> |

### Settings
| | |
|---|---|
<img width="100%"   alt="Captura de pantalla 2026-08-02 a las 1 28 14 a  m" src="https://github.com/user-attachments/assets/b14db297-1dd2-4b0c-adbe-87d036d01d76" /> | <img width="100%"   alt="Captura de pantalla 2026-08-02 a las 1 28 51 a  m" src="https://github.com/user-attachments/assets/d2bb536f-11f5-42c5-94fa-17f6c30adb4d" /> |


## Installation

> 📖 Detailed step-by-step guide: [INSTALL.md](INSTALL.md) — the app's
> dependency status cards (Settings → Dependencies) deep-link straight to
> the relevant section when something is missing.

### 1. Download the file for your platform

Grab it from the [latest release](../../releases/latest):

| Platform | Download | Install |
|---|---|---|
| 🍎 macOS (Apple Silicon) | `VideoDownloader-macos-arm64.dmg` | Open the DMG and drag **Video Downloader** to Applications. Unsigned build: the first time, **right-click → Open**. |
| 🍎 macOS (Intel) | `VideoDownloader-macos-x86_64.dmg` | Same as above. |
| 🪟 Windows (x64) | `VideoDownloader-windows-x64-setup.exe` | Run the installer. If SmartScreen warns: **More info → Run anyway**. |
| 🪟 Windows (ARM) | `VideoDownloader-windows-arm64-setup.exe` | Same as above. |
| 🐧 Linux Debian/Ubuntu (x86_64) | `VideoDownloader-linux-amd64.deb` | `sudo apt install ./VideoDownloader-linux-amd64.deb` |
| 🐧 Linux Debian/Ubuntu (ARM) | `VideoDownloader-linux-arm64.deb` | `sudo apt install ./VideoDownloader-linux-arm64.deb` |
| 🐧 Linux any distro (x86_64) | `VideoDownloader-linux-x86_64.AppImage` | `chmod +x VideoDownloader-linux-x86_64.AppImage` and run. |
| 🐧 Linux any distro (ARM) | `VideoDownloader-linux-aarch64.AppImage` | `chmod +x VideoDownloader-linux-aarch64.AppImage` and run. |

Everything is bundled: you do **not** need Python, yt-dlp or FFmpeg
installed to use the app.

### 2. Required: a JavaScript engine (for YouTube)

YouTube requires solving JavaScript challenges; without a JS engine most
YouTube downloads fail. Install [Deno](https://deno.land) (recommended;
Node.js or Bun also work):

| Platform | Command |
|---|---|
| macOS | `brew install deno` |
| Windows | `winget install deno` |
| Linux | `sudo snap install deno` (or your distro's package) |

### 3. Optional (better experience)

- **FFmpeg on the system** — the app ships a fallback FFmpeg and can
  download a full toolchain on first run, but a system install is the most
  reliable: `brew install ffmpeg` / `winget install ffmpeg` /
  `sudo apt install ffmpeg`.
- **AppImage users only**: GTK 3 and libmpv must be present —
  `sudo apt install libmpv2` / `sudo dnf install mpv-libs`. (The `.deb`
  installs these automatically.)
- **Windows on a very clean machine**: the
  [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
  may be needed if the app doesn't start.

The **Settings** screen shows a live status of FFmpeg and the JS engine,
so you can verify what the app detected. For age-restricted or private
content, set **Settings → Browser cookies**.

## Features

- URL analysis: single videos, playlists and channels.
- Format explorer: resolution, FPS, codecs, bitrate and estimated size.
- Download modes: video only, audio only (MP3/M4A/AAC/FLAC/OPUS/WAV), or
  video+audio with automatic merging via FFmpeg.
- Post-download conversion with lossless remux vs re-encode detection.
- Concurrent downloads with queue, live progress, speed, ETA and cancellation.
- Advanced settings: proxy, browser cookies, custom headers, rate limiting,
  subtitles, thumbnails and metadata embedding.
- Custom "Nocturnal Studio" design system: frameless window with in-app
  controls, dark/light themes, custom sidebar and live download badge.

## Run from source

The only tool you need is [uv](https://docs.astral.sh/uv/) — it manages
Python 3.13 and all dependencies automatically. The FFmpeg/Deno notes from
[Installation](#installation) apply here too (the app resolves FFmpeg in
this order: system `PATH` → downloaded `static-ffmpeg` toolchain →
bundled `imageio-ffmpeg` fallback without ffprobe).

```bash
uv sync
uv run python main.py          # desktop app
uv run flet run --web main.py  # browser mode (development)
```

## Tests and quality

```bash
uv run pytest
uv run ruff check .
uv run mypy video_downloader
```

## Building executables

`flet build` packages the app with Flutter and **only compiles for the OS it
runs on** (there is no cross-compilation). Branding comes from the repo:

- Product name: `[tool.flet] product` in [pyproject.toml](pyproject.toml)
  (`Video Downloader`).
- App icon: [assets/icon.png](assets/icon.png) — flet generates every
  platform-specific icon size from it (.icns, .ico, etc.).
- App version: `[project] version` in [pyproject.toml](pyproject.toml).

### Local build (current OS only)

```bash
# On macOS   → build/macos/Video Downloader.app
uv run flet build macos --yes

# On Windows → build/windows/  (Video Downloader.exe + support files)
uv run flet build windows --yes

# On Linux   → build/linux/
uv run flet build linux --yes
```

Notes:

- `--yes` lets flet download the exact Flutter SDK version it requires
  (~1 GB the first time; cached afterwards). The Flutter version is
  determined by the pinned flet release in `uv.lock`, so builds are
  reproducible.
- Linux needs build dependencies first:
  `sudo apt-get install ninja-build libgtk-3-dev libmpv-dev mpv`.
- Windows needs Visual Studio Build Tools with the "Desktop development
  with C++" workload.

### Release builds for all three platforms (GitHub Actions)

The workflow [.github/workflows/build.yml](.github/workflows/build.yml)
builds macOS, Windows and Linux in parallel on GitHub-hosted runners.
Since `flet build` cannot cross-compile, each architecture is built on
its own native runner: macOS arm64 + x86_64, Windows x64 + arm64 and
Linux amd64 + arm64 (six jobs in total).

**To publish a release:**

```bash
# 1. Bump [project] version in pyproject.toml (e.g. 0.2.0), commit, then:
git tag v0.2.0
git push origin v0.2.0

# 2. Create the GitHub release for that tag (or let the workflow create it):
gh release create v0.2.0 --title "v0.2.0" --generate-notes
```

Pushing the `v*` tag triggers the workflow, which builds every
platform/architecture pair and attaches native installers to the release
for that tag:

- `VideoDownloader-macos-{arm64,x86_64}.dmg` — mount and drag
  **Video Downloader.app** to Applications.
- `VideoDownloader-windows-{x64,arm64}-setup.exe` — Inno Setup installer
  with Start Menu / desktop shortcuts.
- `VideoDownloader-linux-{amd64,arm64}.deb` — installable with
  `sudo apt install ./VideoDownloader-linux-<arch>.deb` (adds a menu entry
  and icon). Debian/Ubuntu.
- `VideoDownloader-linux-{x86_64,aarch64}.AppImage` — portable,
  distro-agnostic: `chmod +x` and run. Requires GTK 3 and libmpv on the
  system.

What end users need on their machine is covered in
[Installation](#installation) — everything else ships inside the package.

CI caching: the Flutter SDK that flet downloads (`~/flutter`, ~1 GB) and
the pub cache are cached between runs keyed on `uv.lock` and the runner
architecture; Python packages are cached by setup-uv. First run per
platform/arch is slow, following runs are much faster.

You can also run it manually from the **Actions** tab (workflow_dispatch);
manual runs upload the binaries as workflow artifacts instead of attaching
them to a release.

**Version pinning policy:** everything in the workflow is pinned on purpose —
GitHub Actions by exact tag, the uv version, Python from `.python-version`,
project dependencies via `uv sync --frozen` (installs exactly what `uv.lock`
records, never re-resolves), and the Flutter SDK via the pinned flet release.
Nothing updates by itself; bump versions manually when you decide to.

## Architecture

```
video_downloader/
├── config/     # constants, presets and settings persistence (JSON)
├── core/       # errors, typed events, event bus (threads → UI) and logging
├── models/     # MediaInfo/FormatInfo/PlaylistInfo, DownloadTask/Request, conversion
├── services/   # ytdlp_service, ffmpeg_service, format_builder, download_manager
├── utils/      # human formatting, URL validation, paths
└── ui/         # Flet shell, views, components, theme and texts (Spanish)
```

Key design rules:

- yt-dlp is blocking: it runs on `DownloadManager` worker threads; no Flet
  control is ever touched from those threads. Events cross into the UI loop
  through the `EventBus`.
- `format_builder` is pure (UI options → `ydl_opts`) and concentrates the
  test suite.
- The UI only shows Spanish messages mapped from the error taxonomy; the
  technical detail goes to the log (`~/Library/Logs/VideoDownloader/`).

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for the
project setup, conventions and pull-request workflow.

## License

This project is open source under the [MIT License](LICENSE).
