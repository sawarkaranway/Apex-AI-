"""
Typed Email Tools for Chaitanya Karya.
Enforces provider-agnostic execution resolving through IntegrationHub.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from agent.interfaces.email import EmailDraft, EmailMessage, EmailProvider
from agent.providers import default_email_provider
from agent.integrations.hub import integration_hub

class GmailSearchInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    query: str = Field(default="", description="Search query string (e.g. sender, subject, keywords)")
    max_results: int = Field(default=10, description="Max number of results to return")

class GmailDraftInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    to: List[str] = Field(default_factory=list, description="Recipient email addresses")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Body text content")
    cc: List[str] = Field(default_factory=list, description="Carbon copy recipients")

class GmailSendInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    to: List[str] = Field(..., min_length=1, description="Recipient email addresses")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Body text content")
    cc: List[str] = Field(default_factory=list, description="Carbon copy recipients")

def _resolve_email_provider(user_id: Optional[int] = None) -> EmailProvider:
    if user_id is not None:
        return integration_hub.get_email_provider(user_id)
    return default_email_provider

def gmail_search_handler(args: GmailSearchInput, user_id: Optional[int] = None) -> List[EmailMessage]:
    provider = _resolve_email_provider(user_id)
    return provider.search_messages(args.query, args.max_results)

def gmail_draft_handler(args: GmailDraftInput, user_id: Optional[int] = None) -> EmailDraft:
    provider = _resolve_email_provider(user_id)
    draft = EmailDraft(
        to=args.to,
        cc=args.cc,
        subject=args.subject,
        body_text=args.body,
        provider_id="google" if user_id else "in_memory"
    )
    return provider.create_draft(draft)

def gmail_send_handler(args: GmailSendInput, user_id: Optional[int] = None) -> EmailMessage:
    provider = _resolve_email_provider(user_id)
    draft = EmailDraft(
        to=args.to,
        cc=args.cc,
        subject=args.subject,
        body_text=args.body,
        provider_id="google" if user_id else "in_memory"
    )
    return provider.send_message(draft)
