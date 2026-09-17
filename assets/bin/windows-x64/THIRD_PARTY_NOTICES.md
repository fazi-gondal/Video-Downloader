# Bundled Runtime Notices

Production Windows release builds download these binaries during CI and place
them in this folder before packaging:

- `deno.exe` from the Deno project: https://github.com/denoland/deno
- `ffmpeg.exe` and `ffprobe.exe` from FFmpeg Windows builds.

The executable files are intentionally not committed to the repository. Keep
the GitHub Actions workflow pins and download URLs in sync with this notice.
