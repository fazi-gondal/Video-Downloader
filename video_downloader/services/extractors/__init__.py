"""Custom extractors registered with yt-dlp."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yt_dlp.extractor.common import InfoExtractor

logger = logging.getLogger(__name__)

_REGISTERED = False


def register_custom_extractors() -> None:
    """Register custom extractors into yt-dlp's extractor registry.

    This ensures custom extractors take precedence before generic fallback.
    """
    global _REGISTERED
    if _REGISTERED:
        return

    try:
        import yt_dlp.extractor
        from video_downloader.services.extractors.aryplus import AryPlusIE, AryPlusSeriesIE

        yt_dlp.extractor.import_extractors()
        extractors_map = yt_dlp.extractor._extractors_context.value

        custom_ies: list[type[InfoExtractor]] = [AryPlusIE, AryPlusSeriesIE]
        new_map: dict[str, type[InfoExtractor]] = {}
        for ie in custom_ies:
            new_map[ie.__name__] = ie
        new_map.update(extractors_map)

        extractors_map.clear()
        extractors_map.update(new_map)
        _REGISTERED = True
        logger.debug("Registered %d custom extractors with yt-dlp", len(custom_ies))
    except Exception as exc:
        logger.warning("Could not register custom extractors with yt-dlp: %s", exc)
