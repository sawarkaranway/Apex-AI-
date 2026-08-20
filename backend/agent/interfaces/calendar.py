"""
Provider-Agnostic Calendar Interface for Chaitanya Karya.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class CalendarEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: Optional[str] = None
    title: str
    description: Optional[str] = ""
    start_time: datetime
    end_time: datetime
    attendees: List[str] = Field(default_factory=list)
    location: Optional[str] = ""
    meeting_url: Optional[str] = None
    provider_id: Optional[str] = "unknown"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CalendarEventFilter(BaseModel):
    model_config = ConfigDict(frozen=True)

    start_time: datetime
    end_time: datetime
    max_results: int = 50
    query: Optional[str] = None

class CalendarProvider(ABC):
    """
    Abstract Base Class for Calendar Providers (Google, Microsoft 365, In-Memory).
    """

    @abstractmethod
    def list_events(self, time_filter: CalendarEventFilter) -> List[CalendarEvent]:
        """Fetch normalized calendar events within the given timeframe."""
        pass

    @abstractmethod
    def create_event(self, event: CalendarEvent) -> CalendarEvent:
        """Create a new calendar event and return the persisted representation with its ID."""
        pass

    @abstractmethod
    def update_event(self, event_id: str, patch: Dict[str, Any]) -> CalendarEvent:
        """Update fields of an existing event."""
        pass

    @abstractmethod
    def delete_event(self, event_id: str) -> bool:
        """Delete an event by its ID. Returns True if successfully deleted."""
        pass
