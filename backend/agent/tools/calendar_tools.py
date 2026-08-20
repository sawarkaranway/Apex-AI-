"""
Typed Calendar Tools for Chaitanya Karya.
Enforces provider-agnostic execution resolving through IntegrationHub.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, ConfigDict
from agent.interfaces.calendar import CalendarEvent, CalendarEventFilter, CalendarProvider
from agent.providers import default_calendar_provider
from agent.integrations.hub import integration_hub

class CalendarGetEventsInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    date_str: Optional[str] = Field(default=None, description="ISO date or 'YYYY-MM-DD'")
    days_ahead: int = Field(default=1, description="Number of days to search ahead")
    query: Optional[str] = Field(default=None, description="Optional search query filter")

class CalendarCreateEventInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    title: str = Field(..., description="Event title")
    start_time: datetime = Field(..., description="Start datetime in ISO format")
    end_time: datetime = Field(..., description="End datetime in ISO format")
    description: Optional[str] = Field(default="", description="Event description")
    attendees: List[str] = Field(default_factory=list, description="List of attendee email addresses")
    location: Optional[str] = Field(default="", description="Location or virtual meet link")

class CalendarDeleteEventInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    event_id: str = Field(..., description="Unique event identifier to delete")

def _resolve_calendar_provider(user_id: Optional[int] = None) -> CalendarProvider:
    if user_id is not None:
        return integration_hub.get_calendar_provider(user_id)
    return default_calendar_provider

def calendar_get_events_handler(args: CalendarGetEventsInput, user_id: Optional[int] = None) -> List[CalendarEvent]:
    if args.date_str:
        try:
            parsed = datetime.fromisoformat(args.date_str)
            start_dt = parsed.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt + timedelta(days=args.days_ahead, hours=23, minutes=59)
        except Exception:
            start_dt = datetime.now(timezone.utc)
            end_dt = start_dt + timedelta(days=args.days_ahead)
    else:
        start_dt = datetime.now(timezone.utc)
        end_dt = start_dt + timedelta(days=args.days_ahead)

    time_filter = CalendarEventFilter(start_time=start_dt, end_time=end_dt, query=args.query)
    provider = _resolve_calendar_provider(user_id)
    return provider.list_events(time_filter)

def calendar_create_event_handler(args: CalendarCreateEventInput, user_id: Optional[int] = None) -> CalendarEvent:
    provider = _resolve_calendar_provider(user_id)
    event = CalendarEvent(
        title=args.title,
        description=args.description,
        start_time=args.start_time,
        end_time=args.end_time,
        attendees=args.attendees,
        location=args.location,
        provider_id="google" if user_id else "in_memory"
    )
    return provider.create_event(event)

def calendar_delete_event_handler(args: CalendarDeleteEventInput, user_id: Optional[int] = None) -> bool:
    provider = _resolve_calendar_provider(user_id)
    return provider.delete_event(args.event_id)
