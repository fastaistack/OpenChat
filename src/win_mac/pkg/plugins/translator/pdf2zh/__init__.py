import logging
from pkg.plugins.translator.pdf2zh.high_level import translate, translate_stream, download_remote_fonts

log = logging.getLogger(__name__)

__all__ = ["translate", "translate_stream"]
