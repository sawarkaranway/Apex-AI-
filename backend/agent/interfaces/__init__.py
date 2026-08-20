"""
Agent Interfaces Package.
"""

from .calendar import CalendarEvent, CalendarEventFilter, CalendarProvider
from .email import EmailRecipient, EmailDraft, EmailMessage, EmailProvider
from .storage import FileItem, FileContent, StorageProvider

__all__ = [
    "CalendarEvent",
    "CalendarEventFilter",
    "CalendarProvider",
    "EmailRecipient",
    "EmailDraft",
    "EmailMessage",
    "EmailProvider",
    "FileItem",
    "FileContent",
    "StorageProvider",
]
