"""
Provider-Agnostic Email Interface for Chaitanya Karya.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr

class EmailRecipient(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: Optional[str] = ""
    email: str

class EmailDraft(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: Optional[str] = None
    to: List[str] = Field(default_factory=list)
    cc: List[str] = Field(default_factory=list)
    bcc: List[str] = Field(default_factory=list)
    subject: str
    body_text: str
    body_html: Optional[str] = None
    thread_id: Optional[str] = None
    provider_id: Optional[str] = "unknown"

class EmailMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    thread_id: Optional[str] = None
    sender: str
    to: List[str] = Field(default_factory=list)
    cc: List[str] = Field(default_factory=list)
    subject: str
    body_preview: str
    body_full: Optional[str] = None
    sent_at: Optional[datetime] = None
    is_unread: bool = False
    provider_id: Optional[str] = "unknown"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EmailProvider(ABC):
    """
    Abstract Base Class for Email Providers (Gmail, Microsoft Outlook, In-Memory).
    """

    @abstractmethod
    def search_messages(self, query: str, max_results: int = 10) -> List[EmailMessage]:
        """Search inbox messages matching query."""
        pass

    @abstractmethod
    def get_message(self, message_id: str) -> Optional[EmailMessage]:
        """Fetch full details of a specific email."""
        pass

    @abstractmethod
    def create_draft(self, draft: EmailDraft) -> EmailDraft:
        """Create an email draft and return it with assigned ID."""
        pass

    @abstractmethod
    def send_message(self, draft: EmailDraft) -> EmailMessage:
        """Send an email message and return the sent message object."""
        pass
