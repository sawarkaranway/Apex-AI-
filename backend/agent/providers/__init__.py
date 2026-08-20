"""
Providers Package for Chaitanya Karya.
"""

from .in_memory.calendar import InMemoryCalendarProvider
from .in_memory.email import InMemoryEmailProvider
from .local.storage_local import LocalStorageProvider

# Default provider registry instances
default_calendar_provider = InMemoryCalendarProvider()
default_email_provider = InMemoryEmailProvider()
default_storage_provider = LocalStorageProvider()

__all__ = [
    "InMemoryCalendarProvider",
    "InMemoryEmailProvider",
    "LocalStorageProvider",
    "default_calendar_provider",
    "default_email_provider",
    "default_storage_provider",
]
