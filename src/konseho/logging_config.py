"""Logging configuration utilities for Konseho."""
from __future__ import annotations

import logging
import sys


def configure_logging(level: str='INFO', show_api_calls: bool=True,
    api_call_format: (str | None)=None) -> None:
    """Configure logging for Konseho applications.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        show_api_calls: Whether to show API calls to model providers
        api_call_format: Custom format for API call logs
    """
    logging.basicConfig(level=getattr(logging, level.upper()), format=
        '%(asctime)s - %(name)s - %(message)s', datefmt='%H:%M:%S', stream=
        sys.stdout)
    if show_api_calls and api_call_format:
        configure_api_logging(api_call_format)
    elif not show_api_calls:
        logging.getLogger('httpx').setLevel(logging.WARNING)


def configure_api_logging(format_string: str='simple') -> None:
    """Configure API call logging with different formats.

    Args:
        format_string: One of "simple", "detailed", "count"
    """
    httpx_logger = logging.getLogger('httpx')


    class APICallFormatter(logging.Formatter):

        def __init__(self) -> None:
            super().__init__()
            self.api_call_count = 0
            self.tool_use_count = 0

        def format(self, record: logging.LogRecord) -> str:
            msg = record.getMessage()
            if 'POST https://api.anthropic.com' in msg:
                self.api_call_count += 1
                if format_string == 'simple':
                    return f'🤖 API Call #{self.api_call_count}'
                elif format_string == 'detailed':
                    if self.api_call_count > 1:
                        self.tool_use_count += 1
                        return (
                            f'🔧 Tool Use #{self.tool_use_count} (API Call #{self.api_call_count})'
                            )
                    else:
                        return (
                            f'💭 Initial Request (API Call #{self.api_call_count})'
                            )
                elif format_string == 'count':
                    return f'[{self.api_call_count}]'
            return super().format(record)
    formatter = APICallFormatter()
    for handler in httpx_logger.handlers:
        handler.setFormatter(formatter)


def use_minimal_logging() -> None:
    """Minimal logging - only warnings and errors."""
    configure_logging(level='WARNING', show_api_calls=False)


def use_clean_logging() -> None:
    """Clean logging - simple API call indicators."""
    configure_logging(level='INFO', show_api_calls=True, api_call_format=
        'simple')


def use_detailed_logging() -> None:
    """Detailed logging - shows tool use vs initial requests."""
    configure_logging(level='INFO', show_api_calls=True, api_call_format=
        'detailed')


def use_debug_logging() -> None:
    """Debug logging - shows everything."""
    configure_logging(level='DEBUG', show_api_calls=True, api_call_format=
        'detailed')
