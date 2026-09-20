# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Entries reference the commit (or, going forward, the pull request) that
introduced each change.

## [Unreleased]

### Added

- In-app SnackBar notifications when downloads complete or fail, and when media conversions finish or fail.

### Fixed

- Notifications not appearing on download or conversion completion: wired terminal download states (`TaskStateChanged`) and conversion events (`ConversionFinished`) to trigger in-app SnackBars, and upgraded `show_toast` to use native Flet 1.0 `ft.SnackBar` (`page.show_dialog()`).

## [1.2.1] - 2026-09-17

### Added

- Maximum-compression `.zip` release archives (`VideoDownloader-windows-x64-setup.zip`)
  generated in GitHub Actions CI for portable distribution of the installer.

### Updated

- Release packaging pipeline updated to distribute `.zip` installer archives.
- Installation documentation (`README.md`) updated with `.zip` instructions.

## [1.2.0] - 2026-09-17

### Added

- Video to MP3 conversion: Added direct `mp3` choice to video container chips
  in the Converter view, enabling one-click audio extraction at 320 kbps (`libmp3lame`).
- Conversion mode badge: Dynamic UI indicator showing whether the selected conversion
  performs lossless remuxing, video re-encoding, or high-bitrate audio extraction.
- Bundled FFmpeg toolchain: Support for detecting and prioritizing bundled FFmpeg/ffprobe
  binaries under `assets/bin/windows-x64/` with automatic PATH injection and license notices.

### Updated

- Upgraded Flet framework to `v1.0.0` (`flet[cli,desktop]>=1.0.0`).
- FFmpeg resolution hierarchy: bundled binaries take priority over system PATH,
  `static-ffmpeg`, and `imageio-ffmpeg` fallbacks.
- FFmpeg service improvements for media probing and conversion process management.

### Fixed

- Handled conversion edge cases and process termination gracefully in FFmpeg service.
- Fixed container and codec mapping when converting heterogeneous media files.

## [1.1.0] - 2026-08-24

### Added

- Concurrent fragments slider: Configurable multi-fragment downloading
  (`concurrent_fragments`) in Settings to accelerate DASH and HLS stream downloads.
- Enhanced format selection: Smart codec matching prioritizing VP9 video and Opus audio
  streams when WebM/MKV containers are selected.
- Subtitle and multi-audio track metadata pass-through from full media analysis.
- Structured playlist subdirectories: Automatically group playlist downloads into
  dedicated folders.
- Comprehensive test coverage for configuration view, format builder, and settings.

### Updated

- Startup performance: Deferred heavy service resolution and initializations to
  `after_first_paint` for a significantly faster cold startup.

### Fixed

- Resolved Ruff lint errors (`F821`, `I001`) across UI and service modules.

## [1.0.0] - 2026-08-16

### Added

- Complete multi-audio track support: Detect, select, and merge multiple audio tracks
  using yt-dlp and FFmpeg.
- Resilient download manager with concurrency throttling, live progress, speed, ETA,
  and task cancellation.
- Media converter for remuxing and transcoding local audio and video files.
- Modern desktop UI powered by Flet with Nocturnal Studio dark and light themes,
  custom frameless window controls, and responsive navigation.
- SQLite-backed download history with filtering and search capabilities.
- Advanced settings: browser cookie extraction (Chrome, Firefox, Edge, etc.), proxy
  configuration, and custom request headers.
- Native Windows x64 Inno Setup installer packaging.
- Startup error diagnostics displaying helpful GUI error dialogs upon fatal boot failure.

### Updated

- Upgraded Flet to v0.86.5.

## [0.1.3] - 2026-07-15

### Added

- Multi-architecture release builds: the release workflow now compiles
  every platform on native runners for each CPU — macOS arm64 (Apple
  Silicon) + x86_64 (Intel), Windows x64 + arm64, Linux amd64 + arm64 —
  since `flet build` cannot cross-compile. Artifacts and packages are
  now arch-suffixed (`.dmg` per arch, `.deb` amd64/arm64, AppImage
  x86_64/aarch64, Inno Setup installer x64/arm64 with proper
  `ArchitecturesAllowed` gating), and the Flutter SDK cache is keyed per
  runner architecture. (#2)

### Updated

- Faster startup: `.py` sources are pre-compiled to bytecode at build time
  (`tool.flet.compile`), removing first-launch bytecode compilation and
  reducing antivirus churn on Windows; `yt_dlp` (the heaviest import) is
  now loaded lazily off the startup path and warmed up in a background
  thread right after the window is revealed. (#3)

### Fixed

- Packaged (Release) app no longer flashes a bare native window with the
  OS title bar for several seconds before the real frameless UI appears:
  `tool.flet.app.hide_window_on_start` keeps the window hidden until the
  Python side reveals it, matching the dev-mode `FLET_APP_HIDDEN`
  behavior that already worked with `flet run`. (#3)

## [0.1.2] - 2026-07-14

### Added

- About screen with its own sidebar entry: app logo, version, description,
  developer credit (Fazi Gondal), tech stack chips and clickable links to the
  GitHub profile, LinkedIn, personal website, source repository and issue
  tracker (LinkedIn/website buttons appear once their URLs are set in
  `config/constants.py`).
- Open-source licensing: MIT `LICENSE` and `CONTRIBUTING.md` (setup,
  conventions and PR workflow); the About screen shows a clickable
  "© 2026 Faizan Gondal · MIT License" notice linking to the license on GitHub.
- Pull request template with a quality checklist, and a CI workflow that
  runs the full test suite, ruff and mypy (with uv caching) on every PR
  and push to main; the release workflow now gates the platform builds
  behind the same checks, so no version ships with failing tests.
- Installation guide (`INSTALL.md`) with URL anchors per section;
  the dependency status cards in Settings become clickable when FFmpeg or
  the JavaScript engine is missing/partial and deep-link to the matching
  section of the guide on GitHub.

### Updated

### Fixed

- Packaged app: the UI now updates live when the full FFmpeg toolchain
  finishes downloading in the background — sidebar chip and Settings
  dependency card refresh, and a toast confirms ffprobe is available.
  Previously the "downloading in the background" notice stayed until the
  app was restarted.
- Startup flash: the window now launches hidden and is revealed only once
  the frameless UI is fully built, removing the ugly transition where the
  native title bar and an empty canvas were visible for an instant.
- URL analysis no longer spins forever when there is no internet: analysis
  options now fail fast (socket timeout + capped retries) so network
  errors surface in seconds, and the Home/format-table loaders have a hard
  75s timeout with a clear "check your connection" message as a safety
  net.

## [0.1.0] - 2026-07-13

### Added

- Initial repository setup and `.gitignore` (`f123894`, `08bc8b8`).
- Project structure: `config/`, `core/`, `models/`, `services/`, `utils/`,
  `ui/` packages (`165a971`).
- Configuration and settings modules: constants, quality/format presets and
  JSON settings persistence with export/import (`5030a27`).
- Core infrastructure: error taxonomy, typed events, thread-to-UI event bus
  and logging configuration (`6d33d82`).
- Models for download requests/tasks, media metadata (video, playlist,
  format) and conversions (`80051eb`).
- Services: yt-dlp integration, FFmpeg resolution with bundled fallbacks,
  pure `format_builder`, concurrent download manager, conversion queue,
  download history (SQLite) and desktop notifications (`77e2e3f`).
- Utility modules: environment/PATH handling, human-readable formatting,
  URL validation and path helpers (`fd2c4cf`).
- Flet UI: app shell with navigation and views for home/analysis, download
  configuration, downloads queue, converter, history and settings
  (`8ee5728`).
- Comprehensive test suite for services, models and utilities (`9689ce5`).
- **Nocturnal Studio design system** — full UI/UX redesign from Google
  Stitch mockups (`793ee0d`):
  - Graphite/coral/teal palettes with full dark & light themes and live
    theme switching (sidebar toggle synced with Settings).
  - Space Grotesk + Inter typography bundled as offline assets.
  - Custom sidebar (brand, active-item accent bar, live downloads badge,
    ffmpeg status chip, theme toggle, collapsible on narrow windows).
  - Home hero screen with skeleton loading state.
  - Download config screen: mode cards, chip groups for container/quality/
    FPS, manual format table, live summary bottom bar.
  - Downloads view: progress-tinted task cards, status pills, live
    "active · queued" summary.
  - Converter (teal accent), History with type/state filters and text
    search, bento-style Settings with dependency status cards.
  - Custom toast notifications (Flet's SnackBar renders nothing in 0.85).
- Frameless window: native title bar hidden, in-app traffic-light window
  controls (minimize / maximize / close) and drag areas (`138d59d`).
- App icon (Nocturnal Studio brand mark) generated at
  `assets/icon.png` (`d9090b7`).
- Packaging metadata: `[tool.flet]` product name **Video Downloader**,
  org, company and copyright (`d9090b7`).
- GitHub Actions release workflow building macOS, Windows and Linux on
  tag push, with pinned action/tool versions (`d9090b7`).
- Native release packages: macOS `.dmg`, Windows Inno Setup installer,
  Debian `.deb` (`787cb3b`) and Linux AppImage (`7b77f21`).
- CI caching for the Flutter SDK, pub cache and uv packages (`7b77f21`).
- README: English rewrite with an Installation section (what to download
  per platform, required Deno, optional FFmpeg/libmpv/VC++), local and CI
  build instructions and version-pinning policy (`9caf1f4`).

### Updated

- Entry point initializes environment hardening and logging before
  starting the app (`148c265`).

### Fixed

- Windows CI: force UTF-8 so flet's Unicode progress output doesn't crash
  on the cp1252 console (`630b4ff`).
- Release uploads: grant `contents: write` to the workflow token; locate
  the macOS `.app` bundle dynamically before packaging (`787cb3b`).
- AppImage packaging: `appimagetool` moved repositories; pinned to release
  1.9.1 (`7b77f21`).

[Unreleased]: https://github.com/fazi-gondal/Video-Downloader/compare/v1.2.1...HEAD
[1.2.1]: https://github.com/fazi-gondal/Video-Downloader/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/fazi-gondal/Video-Downloader/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/fazi-gondal/Video-Downloader/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/fazi-gondal/Video-Downloader/compare/v0.1.3...v1.0.0

