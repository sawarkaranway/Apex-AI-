"""
Contract-Conforming In-Memory Email Provider for Chaitanya Karya.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from agent.interfaces.email import EmailProvider, EmailMessage, EmailDraft
from agent.domain.errors import ProviderError

class InMemoryEmailProvider(EmailProvider):
    """
    In-memory email provider with full contract conformance.
    """

    def __init__(self):
        self._messages: Dict[str, EmailMessage] = {}
        self._drafts: Dict[str, EmailDraft] = {}
        self._seed_default_emails()

    def _seed_default_emails(self):
        now = datetime.now(timezone.utc)
        msg_id = "msg-1"
        self._messages[msg_id] = EmailMessage(
            id=msg_id,
            thread_id="th-101",
            sender="sarah.vp@example.com",
            to=["arman@example.com"],
            subject="Urgent: Board Review Preparation",
            body_preview="Hi Arman, please ensure the executive deck is ready by 3 PM today.",
            body_full="Hi Arman,\n\nPlease ensure the executive deck and Q3 metrics are compiled and ready for review by 3 PM today.\n\nBest,\nSarah",
            sent_at=now,
            is_unread=True,
            provider_id="in_memory"
        )

    def search_messages(self, query: str, max_results: int = 10) -> List[EmailMessage]:
        results = []
        q = query.lower().strip()
        for msg in self._messages.values():
            if not q or q in msg.subject.lower() or q in msg.body_preview.lower() or q in msg.sender.lower():
                results.append(msg)
        return sorted(results, key=lambda m: m.sent_at or datetime.min, reverse=True)[:max_results]

    def get_message(self, message_id: str) -> Optional[EmailMessage]:
        return self._messages.get(message_id)

    def create_draft(self, draft: EmailDraft) -> EmailDraft:
        if not draft.to and not draft.cc:
            raise ProviderError(
                message="Cannot create draft without at least one recipient.",
                provider="in_memory_email",
                is_business_failure=True
            )
        draft_id = draft.id or f"draft-{uuid.uuid4().hex[:8]}"
        saved_draft = EmailDraft(
            id=draft_id,
            to=draft.to,
            cc=draft.cc,
            bcc=draft.bcc,
            subject=draft.subject,
            body_text=draft.body_text,
            body_html=draft.body_html,
            thread_id=draft.thread_id,
            provider_id="in_memory"
        )
        self._drafts[draft_id] = saved_draft
        return saved_draft

    def send_message(self, draft: EmailDraft) -> EmailMessage:
        if not draft.to:
            raise ProviderError(
                message="Cannot send email without recipient 'to' address.",
                provider="in_memory_email",
                is_business_failure=True
            )
        msg_id = f"sent-{uuid.uuid4().hex[:8]}"
        sent_msg = EmailMessage(
            id=msg_id,
            thread_id=draft.thread_id or f"th-{uuid.uuid4().hex[:6]}",
            sender="arman@example.com",
            to=draft.to,
            cc=draft.cc,
            subject=draft.subject,
            body_preview=draft.body_text[:100],
            body_full=draft.body_text,
            sent_at=datetime.now(timezone.utc),
            is_unread=False,
            provider_id="in_memory"
        )
        self._messages[msg_id] = sent_msg
        if draft.id and draft.id in self._drafts:
            del self._drafts[draft.id]
        return sent_msg
