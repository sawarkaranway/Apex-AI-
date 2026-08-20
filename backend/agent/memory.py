"""
Memory System Architecture:
- Working Memory (LangGraph turn state)
- Episodic Memory (TaskExecutions & Messages in Django DB)
- Semantic Memory (Qdrant semantic_memory vector collection & KnowledgeDocument)
- Procedural / Preference Memory (Structured UserPreference table with active flags and conflict resolution)
"""

import re
import datetime
from typing import Dict, List, Any, Optional
from api.models import UserPreference, KnowledgeDocument

class MemorySystem:
    def get_active_preferences(self, category: Optional[str] = None) -> Dict[str, str]:
        """Fetch active user preferences, optionally filtered by category."""
        try:
            qs = UserPreference.objects.filter(is_active=True)
            if category:
                qs = qs.filter(category=category)
            return {p.key: p.value for p in qs}
        except Exception:
            return {}

    def save_preference(
        self,
        key: str,
        value: str,
        category: str = "general",
        confidence: float = 1.0,
        source: str = "user_statement"
    ) -> str:
        """
        Stores a user preference with conflict resolution.
        Deactivates existing records for the same key and creates a new active entry.
        """
        try:
            # Deactivate previous active records for this key
            UserPreference.objects.filter(key=key, is_active=True).update(is_active=False)

            # Create new active preference
            pref = UserPreference.objects.create(
                key=key,
                value=value,
                category=category,
                confidence=confidence,
                is_active=True,
                source=source
            )
            return f"Preference '{key}' updated to '{value}'."
        except Exception as e:
            return f"Error saving preference '{key}': {e}"

    def extract_and_store_preference(self, user_input: str) -> Optional[str]:
        """Extract explicit user preferences from input text."""
        lower = user_input.lower().strip()

        # Rule 1: Meeting start time preference
        time_match = re.search(r'(?:prefer|like|want)\s+meetings?\s+(?:after|at|before)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', lower)
        if time_match:
            time_val = time_match.group(1).strip()
            self.save_preference("preferred_meeting_time", time_val, category="schedule")
            return f"Extracted schedule preference: preferred meeting time '{time_val}'"

        # Rule 2: Tone preference
        if "prefer" in lower and ("concise" in lower or "brief" in lower or "detailed" in lower):
            tone = "concise" if "concise" in lower or "brief" in lower else "detailed"
            self.save_preference("preferred_tone", tone, category="communication")
            return f"Extracted tone preference: '{tone}'"

        return None

    def query_semantic_memory(self, query: str) -> List[Dict[str, Any]]:
        """Query semantic memory from KnowledgeDocument store."""
        try:
            docs = KnowledgeDocument.objects.filter(content__icontains=query)[:3]
            return [{"title": d.title, "content": d.content[:200]} for d in docs]
        except Exception:
            return []

memory_system = MemorySystem()

