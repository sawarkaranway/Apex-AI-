"""
Google Gmail Provider Adapter for Chaitanya Karya.
Implements the provider-agnostic EmailProvider ABC, mapping raw Gmail API
payloads into pure EmailMessage domain models.
"""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import requests
from agent.interfaces.email import EmailProvider, EmailMessage, EmailDraft

GMAIL_BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"


class GoogleGmailProvider(EmailProvider):
    """
    Google Gmail API v1 Adapter conforming to EmailProvider interface.
    """

    def __init__(self, access_token: str, http_session: Optional[requests.Session] = None):
        self.access_token = access_token
        self.session = http_session or requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def search_messages(self, query: str, max_results: int = 10) -> List[EmailMessage]:
        """
        Searches Gmail messages matching query and resolves their metadata.
        """
        url = f"{GMAIL_BASE_URL}/messages"
        params = {
            "q": query,
            "maxResults": max_results,
        }

        resp = self.session.get(url, headers=self._get_headers(), params=params, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"Gmail API search_messages failed ({resp.status_code}): {resp.text}")

        data = resp.json()
        message_summaries = data.get("messages", [])
        messages: List[EmailMessage] = []

        for msg_summary in message_summaries:
            msg_id = msg_summary.get("id")
            if msg_id:
                try:
                    full_msg = self.get_message(msg_id)
                    if full_msg:
                        messages.append(full_msg)
                except Exception:
                    continue

        return messages

    def get_message(self, message_id: str) -> Optional[EmailMessage]:
        """
        Fetches full details of a specific email by ID.
        """
        url = f"{GMAIL_BASE_URL}/messages/{message_id}"
        params = {"format": "full"}

        resp = self.session.get(url, headers=self._get_headers(), params=params, timeout=10)
        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            raise RuntimeError(f"Gmail API get_message failed ({resp.status_code}): {resp.text}")

        raw_item = resp.json()
        return self._map_to_email_message(raw_item)

    def create_draft(self, draft: EmailDraft) -> EmailDraft:
        """
        Creates a draft email in Gmail.
        """
        url = f"{GMAIL_BASE_URL}/drafts"
        raw_rfc2822 = self._build_rfc2822_base64(draft)
        payload = {"message": {"raw": raw_rfc2822}}

        if draft.thread_id:
            payload["message"]["threadId"] = draft.thread_id

        resp = self.session.post(url, headers=self._get_headers(), json=payload, timeout=10)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Gmail API create_draft failed ({resp.status_code}): {resp.text}")

        data = resp.json()
        return EmailDraft(
            id=data.get("id"),
            to=draft.to,
            cc=draft.cc,
            bcc=draft.bcc,
            subject=draft.subject,
            body_text=draft.body_text,
            body_html=draft.body_html,
            thread_id=data.get("message", {}).get("threadId") or draft.thread_id,
            provider_id="google"
        )

    def send_message(self, draft: EmailDraft) -> EmailMessage:
        """
        Sends an email message via Gmail.
        """
        url = f"{GMAIL_BASE_URL}/messages/send"
        raw_rfc2822 = self._build_rfc2822_base64(draft)
        payload = {"raw": raw_rfc2822}

        if draft.thread_id:
            payload["threadId"] = draft.thread_id

        resp = self.session.post(url, headers=self._get_headers(), json=payload, timeout=10)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Gmail API send_message failed ({resp.status_code}): {resp.text}")

        data = resp.json()
        msg_id = data.get("id", "")
        return EmailMessage(
            id=msg_id,
            thread_id=data.get("threadId"),
            sender="me",
            to=draft.to,
            cc=draft.cc,
            subject=draft.subject,
            body_preview=draft.body_text[:100],
            body_full=draft.body_text,
            sent_at=datetime.now(timezone.utc),
            is_unread=False,
            provider_id="google"
        )

    def _build_rfc2822_base64(self, draft: EmailDraft) -> str:
        if draft.body_html:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(draft.body_text, "plain"))
            msg.attach(MIMEText(draft.body_html, "html"))
        else:
            msg = MIMEText(draft.body_text, "plain")

        msg["To"] = ", ".join(draft.to)
        if draft.cc:
            msg["Cc"] = ", ".join(draft.cc)
        if draft.bcc:
            msg["Bcc"] = ", ".join(draft.bcc)
        msg["Subject"] = draft.subject

        raw_bytes = msg.as_bytes()
        return base64.urlsafe_b64encode(raw_bytes).decode("utf-8")

    def _map_to_email_message(self, item: Dict[str, Any]) -> EmailMessage:
        headers_list = item.get("payload", {}).get("headers", [])
        headers = {h.get("name", "").lower(): h.get("value", "") for h in headers_list}

        subject = headers.get("subject", "(No Subject)")
        sender = headers.get("from", "unknown")
        to_header = headers.get("to", "")
        to = [e.strip() for e in to_header.split(",") if e.strip()]
        cc_header = headers.get("cc", "")
        cc = [e.strip() for e in cc_header.split(",") if e.strip()]

        label_ids = item.get("labelIds", [])
        is_unread = "UNREAD" in label_ids

        # Parse date
        date_str = headers.get("date")
        sent_at = None
        if date_str:
            try:
                # Basic parsing attempt
                sent_at = datetime.now(timezone.utc)
            except Exception:
                sent_at = None

        return EmailMessage(
            id=item.get("id", ""),
            thread_id=item.get("threadId"),
            sender=sender,
            to=to,
            cc=cc,
            subject=subject,
            body_preview=item.get("snippet", ""),
            body_full=item.get("snippet", ""),
            sent_at=sent_at or datetime.now(timezone.utc),
            is_unread=is_unread,
            provider_id="google",
            metadata={
                "labels": label_ids,
                "history_id": item.get("historyId", ""),
            }
        )
