"""
Contract-Conforming In-Memory Calendar Provider for Chaitanya Karya.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from agent.interfaces.calendar import CalendarProvider, CalendarEvent, CalendarEventFilter
from agent.domain.errors import ProviderError

class InMemoryCalendarProvider(CalendarProvider):
    """
    In-memory calendar provider with full contract conformance.
    Zero mock debt: implements exact models, validations, and error types.
    """

    def __init__(self):
        self._events: Dict[str, CalendarEvent] = {}
        self._seed_default_events()

    def _seed_default_events(self):
        now = datetime.now(timezone.utc)
        # Sample event
        evt_id = "evt-1"
        self._events[evt_id] = CalendarEvent(
            id=evt_id,
            title="Q3 Strategy & Executive Sync",
            description="Review roadmap, budget allocations, and key milestones",
            start_time=now.replace(hour=14, minute=0, second=0, microsecond=0),
            end_time=now.replace(hour=15, minute=0, second=0, microsecond=0),
            attendees=["arman@example.com", "sarah.vp@example.com", "lead.eng@example.com"],
            location="Room 402 / Google Meet",
            meeting_url="https://meet.google.com/abc-defg-hij",
            provider_id="in_memory"
        )

    def list_events(self, time_filter: CalendarEventFilter) -> List[CalendarEvent]:
        results = []
        for evt in self._events.values():
            if evt.start_time >= time_filter.start_time and evt.end_time <= time_filter.end_time:
                if time_filter.query:
                    q = time_filter.query.lower()
                    if q in evt.title.lower() or q in (evt.description or "").lower():
                        results.append(evt)
                else:
                    results.append(evt)
        return sorted(results, key=lambda e: e.start_time)[:time_filter.max_results]

    def create_event(self, event: CalendarEvent) -> CalendarEvent:
        if event.end_time <= event.start_time:
            raise ProviderError(
                message="End time must be after start time.",
                provider="in_memory_calendar",
                is_business_failure=True
            )

        new_id = event.id or f"evt-{uuid.uuid4().hex[:8]}"
        saved_event = CalendarEvent(
            id=new_id,
            title=event.title,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            attendees=event.attendees,
            location=event.location,
            meeting_url=event.meeting_url or f"https://meet.google.com/{uuid.uuid4().hex[:3]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:3]}",
            provider_id="in_memory",
            metadata=event.metadata
        )
        self._events[new_id] = saved_event
        return saved_event

    def update_event(self, event_id: str, patch: Dict[str, Any]) -> CalendarEvent:
        if event_id not in self._events:
            raise ProviderError(
                message=f"Event with ID '{event_id}' not found.",
                provider="in_memory_calendar",
                is_business_failure=True
            )
        current = self._events[event_id]
        updated_dict = current.model_dump()
        for k, v in patch.items():
            if k in updated_dict and v is not None:
                updated_dict[k] = v
        updated_event = CalendarEvent(**updated_dict)
        self._events[event_id] = updated_event
        return updated_event

    def delete_event(self, event_id: str) -> bool:
        if event_id in self._events:
            del self._events[event_id]
            return True
        return False
