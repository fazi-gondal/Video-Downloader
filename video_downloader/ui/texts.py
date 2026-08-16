"""All user-facing English strings, centralized.

Code/identifiers stay in English; every visible string lives here.
"""

from __future__ import annotations

from video_downloader.models.download import DownloadState

TEXTS: dict[str, str] = {
    # App / navigation
    "app_title": "Video Downloader",
    "nav_dashboard": "Home",
    "nav_downloads": "Downloads",
    "nav_converter": "Converter",
    "nav_settings": "Settings",
    "nav_history": "History",
    "nav_about": "About",
    "brand_subtitle": "Pro Studio Suite",
    "theme_toggle": "Theme",
    "window_minimize": "Minimize",
    "window_maximize": "Maximize / restore",
    "window_close": "Close",
    "ffmpeg_chip_ok": "ffmpeg: OK",
    "ffmpeg_chip_partial": "ffmpeg: partial",
    "ffmpeg_chip_missing": "ffmpeg: missing",
    # Dashboard
    "url_hint": "Paste a link and go…",
    "analyze": "Analyze",
    "analyzing": "Analyzing…",
    "hero_title_lead": "Extract. Convert. ",
    "hero_title_accent": "Master.",
    "hero_subtitle": (
        "The ultimate media capture suite. Paste a link from any "
        "supported platform to start downloading and processing."
    ),
    "supported_services": "Supported Services",
    "author": "Author",
    "duration": "Duration",
    "playlist_detected": "Playlist detected",
    "videos_found": "videos found",
    "select_all": "Select all",
    "selected_count": "selected",
    "continue": "Continue",
    "explore_formats": "View available formats",
    "hide_formats": "Hide formats",
    "loading_formats": "Fetching formats…",
    # Format table
    "fmt_id": "ID",
    "fmt_ext": "Ext",
    "fmt_resolution": "Resolution",
    "fmt_fps": "FPS",
    "fmt_vcodec": "Video Codec",
    "fmt_acodec": "Audio Codec",
    "fmt_bitrate": "Bitrate",
    "fmt_size": "Size",
    "fmt_type": "Type",
    "stream_video": "Video only",
    "stream_audio": "Audio only",
    "stream_muxed": "Video + Audio",
    # Download config
    "config_title": "Download Settings",
    "mode_video": "Video only",
    "mode_audio": "Audio only",
    "mode_video_audio": "Video + Audio",
    "container": "Format",
    "resolution": "Resolution",
    "fps": "FPS",
    "audio_format": "Audio format",
    "audio_quality": "Quality",
    "custom_bitrate": "Custom bitrate (kbps)",
    "destination": "Destination folder",
    "choose_folder": "Choose folder",
    "download": "Download",
    "download_all": "Download all",
    "manual_selection": "Manual format selection",
    "video_stream": "Video stream",
    "audio_stream": "Audio stream",
    "best_available": "Best available",
    "mode_section": "Extraction mode",
    "mode_video_audio_desc": "Original video and audio",
    "mode_video_desc": "No audio track",
    "mode_audio_desc": "Extract high quality audio track",
    "container_section": "Container format",
    "quality_section": "Video quality",
    "audio_section": "Audio options",
    "audio_tracks_section": "Audio tracks",
    "audio_tracks_mode_default": "Default audio",
    "audio_tracks_mode_all": "All audio tracks",
    "audio_tracks_mode_custom": "Select tracks",
    "select_audio_hint": "Select the audio tracks to embed into the video:",
    "subtitles_section": "Subtitles",
    "subtitles_mode_none": "None",
    "subtitles_mode_all": "All subtitles",
    "subtitles_mode_custom": "Select languages",
    "subtitles_custom_langs": "Languages (e.g. en, es, ar)",
    "select_subtitles_hint": "Select the subtitle languages to embed into the video:",
    "extras_section": "Extras",
    "destination_section": "Destination location",
    "recommended": "Recommended",
    # Downloads view
    "downloads_title": "Downloads",
    "no_downloads": "No downloads yet. Analyze a URL to get started.",
    "cancel": "Cancel",
    "retry": "Retry",
    "open_folder": "Open folder",
    "clear_finished": "Clear finished",
    "speed": "Speed",
    "eta": "ETA",
    "active_label": "active",
    "queued_label": "queued",
    "no_downloads_hint": "Paste a link in Home to get started.",
    # States
    "state_pending": "Queued",
    "state_preparing": "Preparing",
    "state_downloading": "Downloading",
    "state_processing": "Processing",
    "state_completed": "Completed",
    "state_error": "Error",
    "state_cancelled": "Cancelled",
    # Converter
    "converter_title": "Convert Files",
    "pick_file": "Choose file",
    "target_format": "Target format",
    "convert": "Convert",
    "remux_badge": "Remux (lossless)",
    "reencode_badge": "Re-encode",
    "conversion_done": "Conversion complete",
    "keep_original": "Keep original file",
    "converter_source": "Source file",
    "converter_queue": "Job queue",
    "no_conversions": "Conversions will appear here.",
    "converter_drop_hint": "Choose a local video or audio file",
    # Settings
    "settings_title": "System Settings",
    "settings_subtitle": "Appearance, downloads, network, and dependencies.",
    "section_appearance": "Appearance",
    "section_downloads": "Downloads",
    "section_network": "Network & Cookies",
    "section_conversion": "Conversion & Metadata",
    "section_dependencies": "Dependencies",
    "section_about": "About",
    "developed_by": "Developed by",
    "link_github": "GitHub",
    "link_linkedin": "LinkedIn",
    "link_website": "Website",
    "link_repo": "Source code",
    "link_issues": "Report an issue",
    "about_description": (
        "Advanced desktop multimedia download manager. Analyze, download, "
        "and convert video and audio from your favorite platforms."
    ),
    "about_tech_label": "Built with",
    "about_license": "License",
    "about_license_tooltip": "Open source software — view full license",
    "install_guide_tooltip": "How to install — open installation guide",
    "save_changes": "Save changes",
    "default_folder": "Default downloads folder",
    "max_concurrent": "Concurrent downloads",
    "proxy": "Proxy (http://user:pass@host:port)",
    "cookies_browser": "Browser cookies",
    "cookies_none": "Disabled",
    "custom_headers": "Custom headers (one per line, Name: value)",
    "rate_limit": "Rate limit (KB/s, 0 = unlimited)",
    "keep_originals": "Keep original files when converting",
    "subtitles": "Download subtitles",
    "subtitle_langs": "Subtitle languages",
    "subtitle_langs_hint": "all, en, es (use 'all' for all languages)",
    "multi_audio": "Download all audio tracks",
    "embed_thumbnail": "Embed thumbnail",
    "embed_metadata": "Embed metadata",
    "prefer_vp9_video": "Prefer VP9 video streams",
    "theme": "Theme",
    "theme_system": "System",
    "theme_light": "Light",
    "theme_dark": "Dark",
    "save": "Save",
    "saved": "Settings saved",
    "exported": "Settings exported",
    "imported": "Settings imported",
    "export_config": "Export settings",
    "import_config": "Import settings",
    "ffmpeg_status": "FFmpeg Status",
    "ffmpeg_system": "System FFmpeg",
    "ffmpeg_bundled_full": "Bundled FFmpeg and ffprobe (static-ffmpeg)",
    "ffmpeg_bundled": (
        "Bundled FFmpeg without ffprobe — MKV thumbnails disabled. "
        "Full version will be downloaded in the background."
    ),
    "ffmpeg_missing": "FFmpeg not available — conversions and merging disabled",
    "ffmpeg_ready": "Full FFmpeg installed — ffprobe is now available.",
    "js_runtime_status": "JavaScript Engine (YouTube)",
    "js_runtime_found": "Available for resolving YouTube JS challenges",
    "js_runtime_missing": (
        "No JavaScript engine found (deno/node). YouTube may not offer "
        "formats. Install with: brew install deno"
    ),
    # History
    "history_title": "Download History",
    "no_history": "Download history is empty.",
    "redownload": "Re-download",
    "delete_entry": "Remove from history",
    "history_filter_all": "All",
    "history_filter_video": "Video",
    "history_filter_audio": "Audio",
    "history_filter_error": "Error",
    "history_search_hint": "Search by title or URL…",
    "no_results": "No results found for this filter.",
    # Errors (keys referenced by AppError.user_message_key)
    "error_generic": "An unexpected error occurred. Check the log for details.",
    "error_analysis": "Could not analyze URL. Verify it is correct.",
    "error_unsupported_url": "The URL is invalid or unsupported.",
    "error_network": "Network error. Check your connection (or configured proxy).",
    "error_analysis_timeout": (
        "Analysis is taking too long. Check your internet connection "
        "and try again."
    ),
    "error_auth_required": (
        "This content requires authentication. "
        "Configure browser cookies in Settings."
    ),
    "error_geo_blocked": "This content is blocked in your region.",
    "error_live_content": "Live streams cannot be downloaded yet.",
    "error_download_failed": "Download failed. You can retry.",
    "error_postprocessing": "Download completed, but FFmpeg processing failed.",
    "error_format_unavailable": (
        "The requested format is unavailable. If this is a YouTube video, "
        "it is usually due to JavaScript challenges: install Deno (brew install deno) "
        "and try again."
    ),
    "error_ffmpeg_missing": "FFmpeg is not available. Install it or reinstall dependencies.",
    "error_conversion": "Conversion failed. Check the log for details.",
    # Notifications
    "notify_done_title": "Download complete",
}

STATE_LABELS: dict[DownloadState, str] = {
    DownloadState.PENDING: TEXTS["state_pending"],
    DownloadState.PREPARING: TEXTS["state_preparing"],
    DownloadState.DOWNLOADING: TEXTS["state_downloading"],
    DownloadState.PROCESSING: TEXTS["state_processing"],
    DownloadState.COMPLETED: TEXTS["state_completed"],
    DownloadState.ERROR: TEXTS["state_error"],
    DownloadState.CANCELLED: TEXTS["state_cancelled"],
}


def t(key: str) -> str:
    return TEXTS.get(key, key)
