"""
Google Calendar Provider Adapter for Chaitanya Karya.
Implements the provider-agnostic CalendarProvider ABC, mapping raw Google Calendar API
payloads into pure CalendarEvent domain models.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import requests
from agent.interfaces.calendar import CalendarProvider, CalendarEvent, CalendarEventFilter

GOOGLE_CALENDAR_BASE_URL = "https://www.googleapis.com/calendar/v3"


class GoogleCalendarProvider(CalendarProvider):
    """
    Google Calendar API v3 Adapter conforming to CalendarProvider interface.
    """

    def __init__(self, access_token: str, calendar_id: str = "primary", http_session: Optional[requests.Session] = None):
        self.access_token = access_token
        self.calendar_id = calendar_id
        self.session = http_session or requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def list_events(self, time_filter: CalendarEventFilter) -> List[CalendarEvent]:
        """
        Queries Google Calendar API for events in timeframe, mapped to CalendarEvent models.
        """
        url = f"{GOOGLE_CALENDAR_BASE_URL}/calendars/{self.calendar_id}/events"
        params = {
            "timeMin": time_filter.start_time.isoformat(),
            "timeMax": time_filter.end_time.isoformat(),
            "maxResults": time_filter.max_results,
            "singleEvents": "true",
            "orderBy": "startTime",
        }
        if time_filter.query:
            params["q"] = time_filter.query

        resp = self.session.get(url, headers=self._get_headers(), params=params, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"Google Calendar API list_events failed ({resp.status_code}): {resp.text}")

        data = resp.json()
        items = data.get("items", [])
        events: List[CalendarEvent] = []

        for item in items:
            event = self._map_to_calendar_event(item)
            if event:
                events.append(event)

        return events

    def create_event(self, event: CalendarEvent) -> CalendarEvent:
        """
        Creates an event in Google Calendar and returns the normalized CalendarEvent.
        """
        url = f"{GOOGLE_CALENDAR_BASE_URL}/calendars/{self.calendar_id}/events"
        payload = {
            "summary": event.title,
            "description": event.description or "",
            "start": {"dateTime": event.start_time.isoformat()},
            "end": {"dateTime": event.end_time.isoformat()},
            "location": event.location or "",
            "attendees": [{"email": email} for email in event.attendees],
        }

        resp = self.session.post(url, headers=self._get_headers(), json=payload, timeout=10)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Google Calendar API create_event failed ({resp.status_code}): {resp.text}")

        created_item = resp.json()
        return self._map_to_calendar_event(created_item)

    def update_event(self, event_id: str, patch: Dict[str, Any]) -> CalendarEvent:
        """
        Updates an existing event in Google Calendar.
        """
        url = f"{GOOGLE_CALENDAR_BASE_URL}/calendars/{self.calendar_id}/events/{event_id}"
        google_patch: Dict[str, Any] = {}
        if "title" in patch:
            google_patch["summary"] = patch["title"]
        if "description" in patch:
            google_patch["description"] = patch["description"]
        if "start_time" in patch:
            google_patch["start"] = {"dateTime": patch["start_time"].isoformat() if isinstance(patch["start_time"], datetime) else patch["start_time"]}
        if "end_time" in patch:
            google_patch["end"] = {"dateTime": patch["end_time"].isoformat() if isinstance(patch["end_time"], datetime) else patch["end_time"]}
        if "location" in patch:
            google_patch["location"] = patch["location"]
        if "attendees" in patch:
            google_patch["attendees"] = [{"email": email} for email in patch["attendees"]]

        resp = self.session.patch(url, headers=self._get_headers(), json=google_patch, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"Google Calendar API update_event failed ({resp.status_code}): {resp.text}")

        updated_item = resp.json()
        return self._map_to_calendar_event(updated_item)

    def delete_event(self, event_id: str) -> bool:
        """
        Deletes an event from Google Calendar.
        """
        url = f"{GOOGLE_CALENDAR_BASE_URL}/calendars/{self.calendar_id}/events/{event_id}"
        resp = self.session.delete(url, headers=self._get_headers(), timeout=10)
        return resp.status_code in (200, 204)

    def _map_to_calendar_event(self, item: Dict[str, Any]) -> CalendarEvent:
        """
        Converts raw Google Calendar item dictionary to clean CalendarEvent domain model.
        """
        start_raw = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
        end_raw = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")

        try:
            start_time = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
        except Exception:
            start_time = datetime.now(timezone.utc)

        try:
            end_time = datetime.fromisoformat(end_raw.replace("Z", "+00:00"))
        except Exception:
            end_time = start_time

        attendees = [att.get("email") for att in item.get("attendees", []) if att.get("email")]

        return CalendarEvent(
            id=item.get("id"),
            title=item.get("summary", "Untitled Event"),
            description=item.get("description", ""),
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            location=item.get("location", ""),
            meeting_url=item.get("hangoutLink") or item.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri"),
            provider_id="google",
            metadata={
                "google_html_link": item.get("htmlLink", ""),
                "google_status": item.get("status", ""),
                "google_etag": item.get("etag", ""),
            }
        )
