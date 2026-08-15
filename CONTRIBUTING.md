# Contributing to Video Downloader

Thanks for your interest in contributing! This document explains how to set
up the project, the conventions we follow and how to get your changes
merged.

## Getting started

The only tool you need is [uv](https://docs.astral.sh/uv/) — it manages
Python 3.13 and every dependency automatically:

```bash
git clone https://github.com/Wachu985/Video-Downloader.git
cd Video-Downloader
uv sync
uv run python main.py          # desktop app
uv run flet run --web main.py  # browser mode (handy while developing)
```

See [INSTALL.md](INSTALL.md) for runtime dependencies (Deno for YouTube,
optional FFmpeg).

## Project layout

```
video_downloader/
├── config/     # constants, presets and settings persistence (JSON)
├── core/       # errors, typed events, event bus (threads → UI) and logging
├── models/     # media/download/conversion dataclasses
├── services/   # yt-dlp, FFmpeg, format_builder, download manager, history
├── utils/      # formatting, URL validation, paths
└── ui/         # Flet shell, views, components, theme and texts (Spanish)
```

Key design rules — please keep them intact:

- **yt-dlp is blocking**: it runs on worker threads; never touch a Flet
  control from those threads. Events cross into the UI loop through the
  `EventBus` (`core/event_bus.py`).
- **`format_builder` is pure** (UI options → `ydl_opts`) and is where most
  of the test suite lives. New download options belong there, with tests.
- **All user-facing strings are Spanish** and live in `ui/texts.py` — no
  hardcoded strings in views. Code, comments and commits are in English.
- **Interactive analysis must fail fast** (see `build_analysis_opts`);
  generous retries are for downloads only.
- The UI follows the "Nocturnal Studio" design system (`ui/theme.py`):
  use the theme helpers and `ft.Colors` roles (e.g. `ON_SURFACE`) so both
  dark and light modes work. Every `ft.Text` needs an explicit color.

## Quality checks

CI runs these on every pull request (and again before any release build) —
a PR cannot merge unless they pass, so run them locally first:

```bash
uv run pytest              # test suite
uv run ruff check .        # lint
uv run mypy video_downloader
```

## Pull requests

1. Fork the repo and create a branch from `main`
   (`feat/...`, `fix/...`, `docs/...`).
2. Make your changes, with tests when they touch `services/`, `models/`,
   `utils/` or `config/`.
3. Add an entry to `CHANGELOG.md` under `## [Unreleased]`
   (sections: Added / Updated / Fixed) referencing your PR.
4. Use [Conventional Commits](https://www.conventionalcommits.org/) for
   commit messages: `feat(ui): ...`, `fix(analysis): ...`, `docs: ...`.
5. Open the pull request against `main` with a short description of the
   problem and the approach.

## Reporting bugs and requesting features

Open an [issue](https://github.com/Wachu985/Video-Downloader/issues) with:

- What you did, what you expected and what happened.
- Your OS and app version (shown in the About screen).
- Relevant log lines if possible (macOS:
  `~/Library/Logs/VideoDownloader/`).

## Releases (maintainer only)

Handled by the maintainer: bump `[project] version` in `pyproject.toml`
(and `APP_VERSION` in `video_downloader/config/constants.py`), move the
`Unreleased` entries to a new version section in `CHANGELOG.md`, then tag
`vX.Y.Z` — GitHub Actions builds and attaches the installers for macOS,
Windows and Linux automatically.

## License

By contributing, you agree that your contributions will be licensed under
the [MIT License](LICENSE).
