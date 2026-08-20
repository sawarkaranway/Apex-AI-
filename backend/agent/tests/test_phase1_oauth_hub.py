"""
Comprehensive Phase 1 Invariant & Integration Test Suite for Chaitanya Karya.
Tests OAuth2 lifecycle, AES-256-GCM credential vault security, AAD isolation,
transparent token refresh, provider adapters, typed tools, and REST endpoints.
"""

import os
import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from cryptography.exceptions import InvalidTag

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chaitanya_backend.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.test import APIClient
from api.models import Integration, OAuthGrant, EncryptedCredential, OAuthStateNonce
from agent.vault import CredentialVault
from agent.integrations.hub import (
    IntegrationHub,
    InvalidOAuthStateError,
    IntegrationNotConnectedError,
    TokenRefreshError,
    get_credential_vault
)
from agent.providers.google.client import GoogleOAuthProviderClient, GoogleOAuthError
from agent.providers.google.calendar_adapter import GoogleCalendarProvider
from agent.providers.google.gmail_adapter import GoogleGmailProvider
from agent.interfaces.calendar import CalendarEvent, CalendarEventFilter
from agent.interfaces.email import EmailMessage, EmailDraft
from agent.runtime.executor import step_executor
from agent.tools.calendar_tools import CalendarGetEventsInput, calendar_get_events_handler
from agent.tools.email_tools import GmailSearchInput, gmail_search_handler


# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def test_user(db):
    user, _ = User.objects.get_or_create(username="phase1_exec_user", email="exec@example.com")
    return user

@pytest.fixture
def second_user(db):
    user, _ = User.objects.get_or_create(username="phase1_other_user", email="other@example.com")
    return user

@pytest.fixture
def mock_google_client():
    client = GoogleOAuthProviderClient(client_id="mock-client-id", client_secret="mock-client-secret")
    client.exchange_code_for_tokens = MagicMock(return_value={
        "access_token": "ya29.mock_access_token_123",
        "refresh_token": "1//mock_refresh_token_456",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "openid email https://www.googleapis.com/auth/calendar.events"
    })
    client.refresh_access_token = MagicMock(return_value={
        "access_token": "ya29.refreshed_access_token_789",
        "expires_in": 3600,
        "token_type": "Bearer"
    })
    client.get_user_info = MagicMock(return_value={
        "email": "exec@example.com",
        "name": "Executive User",
        "picture": "https://example.com/photo.jpg"
    })
    client.revoke_token = MagicMock(return_value=True)
    return client

@pytest.fixture
def hub(mock_google_client):
    vault = CredentialVault(b"12345678901234567890123456789012")
    return IntegrationHub(vault=vault, google_client=mock_google_client)


# ══════════════════════════════════════════════════════════════
# 1. OAuth Lifecycle & State Invariant Tests
# ══════════════════════════════════════════════════════════════

@pytest.mark.django_db
def test_start_oauth_flow_generates_valid_state_and_url(hub, test_user):
    auth_url, state = hub.start_oauth_flow(
        user_id=test_user.id,
        provider_id="google",
        redirect_uri="http://localhost:5173/oauth/callback"
    )
    assert "https://accounts.google.com/o/oauth2/v2/auth" in auth_url
    assert f"state={state}" in auth_url
    assert "client_id=mock-client-id" in auth_url

    # Verify state nonce stored in DB
    nonce_record = OAuthStateNonce.objects.filter(user=test_user, provider="google", state_token=state).first()
    assert nonce_record is not None
    assert nonce_record.is_valid() is True

@pytest.mark.django_db
def test_oauth_callback_invalid_state_rejection(hub, test_user):
    with pytest.raises(InvalidOAuthStateError):
        hub.complete_oauth_flow(
            user_id=test_user.id,
            provider_id="google",
            code="mock_auth_code",
            state="invalid_state_token",
            redirect_uri="http://localhost:5173/oauth/callback"
        )

@pytest.mark.django_db
def test_oauth_callback_success_creates_grant_and_encrypted_credential(hub, test_user):
    _, state = hub.start_oauth_flow(
        user_id=test_user.id,
        provider_id="google",
        redirect_uri="http://localhost:5173/oauth/callback"
    )

    integration = hub.complete_oauth_flow(
        user_id=test_user.id,
        provider_id="google",
        code="mock_auth_code",
        state=state,
        redirect_uri="http://localhost:5173/oauth/callback"
    )

    assert integration.status == "CONNECTED"
    assert integration.account_email == "exec@example.com"
    assert integration.account_name == "Executive User"

    grant = integration.grant
    assert grant is not None
    assert "openid" in grant.scopes
    assert grant.is_expired() is False

    encrypted_cred = grant.encrypted_credential
    assert encrypted_cred is not None
    assert encrypted_cred.key_version == 1

    # Single-use consumption check: state nonce must be deleted
    assert OAuthStateNonce.objects.filter(state_token=state).count() == 0


# ══════════════════════════════════════════════════════════════
# 2. Cryptographic Security & AAD Isolation Tests
# ══════════════════════════════════════════════════════════════

@pytest.mark.django_db
def test_no_plaintext_tokens_in_database(hub, test_user):
    _, state = hub.start_oauth_flow(user_id=test_user.id, provider_id="google", redirect_uri="http://localhost:5173/callback")
    integration = hub.complete_oauth_flow(test_user.id, "google", "code", state, "http://localhost:5173/callback")

    envelope_str = integration.grant.encrypted_credential.encrypted_envelope
    assert "ya29.mock_access_token_123" not in envelope_str
    assert "1//mock_refresh_token_456" not in envelope_str

    parsed_envelope = json.loads(envelope_str)
    assert "nonce" in parsed_envelope
    assert "ciphertext" in parsed_envelope
    assert "aad" in parsed_envelope
    assert parsed_envelope["aad"] == f"user:{test_user.id}:provider:google"

@pytest.mark.django_db
def test_cross_user_credential_isolation_tamper_rejection(hub, test_user, second_user):
    _, state = hub.start_oauth_flow(user_id=test_user.id, provider_id="google", redirect_uri="http://localhost:5173/callback")
    integration = hub.complete_oauth_flow(test_user.id, "google", "code", state, "http://localhost:5173/callback")
    envelope_str = integration.grant.encrypted_credential.encrypted_envelope

    # User 2 attempting to decrypt User 1's ciphertext with User 2's AAD
    user2_aad = CredentialVault.construct_aad(second_user.id, "google")
    with pytest.raises(InvalidTag):
        hub.vault.decrypt_secret(envelope_str, expected_associated_data=user2_aad)


# ══════════════════════════════════════════════════════════════
# 3. Transparent Token Refresh & Revocation Tests
# ══════════════════════════════════════════════════════════════

@pytest.mark.django_db
def test_transparent_token_refresh_on_expiration(hub, test_user):
    _, state = hub.start_oauth_flow(user_id=test_user.id, provider_id="google", redirect_uri="http://localhost:5173/callback")
    integration = hub.complete_oauth_flow(test_user.id, "google", "code", state, "http://localhost:5173/callback")

    # Force expiration of grant
    grant = integration.grant
    grant.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    grant.save()

    creds = hub.get_active_credential(test_user.id, "google")
    assert creds["access_token"] == "ya29.refreshed_access_token_789"
    hub.google_client.refresh_access_token.assert_called_once()

    # Verify DB was updated with new expiration
    grant.refresh_from_db()
    assert grant.expires_at > datetime.now(timezone.utc)

@pytest.mark.django_db
def test_disconnect_integration_cleans_credentials(hub, test_user):
    _, state = hub.start_oauth_flow(user_id=test_user.id, provider_id="google", redirect_uri="http://localhost:5173/callback")
    hub.complete_oauth_flow(test_user.id, "google", "code", state, "http://localhost:5173/callback")

    success = hub.disconnect_integration(test_user.id, "google")
    assert success is True

    integration = Integration.objects.get(user=test_user, provider="google")
    assert integration.status == "DISCONNECTED"
    assert not hasattr(integration, "grant")
    assert EncryptedCredential.objects.count() == 0


# ══════════════════════════════════════════════════════════════
# 4. Provider Adapter Contract Normalization Tests
# ══════════════════════════════════════════════════════════════

def test_google_calendar_adapter_contract():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "id": "gcal_evt_101",
                "summary": "Q3 Board Strategy Sync",
                "description": "Reviewing executive roadmap",
                "start": {"dateTime": "2026-08-25T10:00:00Z"},
                "end": {"dateTime": "2026-08-25T11:00:00Z"},
                "location": "Boardroom Alpha",
                "hangoutLink": "https://meet.google.com/xyz-abc-def",
                "attendees": [{"email": "board@corp.com"}]
            }
        ]
    }
    mock_session.get.return_value = mock_response

    adapter = GoogleCalendarProvider(access_token="test_token", http_session=mock_session)
    time_filter = CalendarEventFilter(
        start_time=datetime(2026, 8, 25, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 8, 25, 23, 59, tzinfo=timezone.utc)
    )
    events = adapter.list_events(time_filter)

    assert len(events) == 1
    event = events[0]
    assert isinstance(event, CalendarEvent)
    assert event.id == "gcal_evt_101"
    assert event.title == "Q3 Board Strategy Sync"
    assert event.meeting_url == "https://meet.google.com/xyz-abc-def"
    assert "board@corp.com" in event.attendees
    assert event.provider_id == "google"

def test_google_gmail_adapter_contract():
    mock_session = MagicMock()
    
    # Mock search messages list
    search_resp = MagicMock()
    search_resp.status_code = 200
    search_resp.json.return_value = {"messages": [{"id": "msg_001"}]}

    # Mock get message details
    detail_resp = MagicMock()
    detail_resp.status_code = 200
    detail_resp.json.return_value = {
        "id": "msg_001",
        "threadId": "th_001",
        "snippet": "Please find attached the signed contract...",
        "labelIds": ["INBOX", "UNREAD"],
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Signed Agreement"},
                {"name": "From", "value": "counsel@legal.com"},
                {"name": "To", "value": "exec@corp.com"}
            ]
        }
    }

    mock_session.get.side_effect = [search_resp, detail_resp]

    adapter = GoogleGmailProvider(access_token="test_token", http_session=mock_session)
    results = adapter.search_messages(query="is:unread", max_results=5)

    assert len(results) == 1
    msg = results[0]
    assert isinstance(msg, EmailMessage)
    assert msg.id == "msg_001"
    assert msg.subject == "Signed Agreement"
    assert msg.sender == "counsel@legal.com"
    assert msg.is_unread is True
    assert msg.provider_id == "google"


# ══════════════════════════════════════════════════════════════
# 5. End-to-End Pipeline Execution via Policy Gate
# ══════════════════════════════════════════════════════════════

@pytest.mark.django_db
def test_e2e_calendar_and_email_pipeline_execution(test_user):
    # Test calendar get events via StepExecutor
    res = step_executor.execute_step(
        tool_name="calendar_get_events",
        raw_arguments={"days_ahead": 3},
        schema_cls=CalendarGetEventsInput,
        handler_func=calendar_get_events_handler,
        task_id="task-oauth-1",
        step_id="step-oauth-1",
        user_id=test_user.id,
        skip_policy_check=False
    )
    assert res.is_successful() is True

    # Test email search messages via StepExecutor
    email_res = step_executor.execute_step(
        tool_name="gmail_search",
        raw_arguments={"query": "urgent", "max_results": 5},
        schema_cls=GmailSearchInput,
        handler_func=gmail_search_handler,
        task_id="task-oauth-2",
        step_id="step-oauth-2",
        user_id=test_user.id,
        skip_policy_check=False
    )
    assert email_res.is_successful() is True


# ══════════════════════════════════════════════════════════════
# 6. REST API Endpoints Verification
# ══════════════════════════════════════════════════════════════

@pytest.mark.django_db
def test_integrations_rest_api_endpoints(test_user):
    client = APIClient()
    client.force_authenticate(user=test_user)

    # 1. GET /api/integrations/
    list_resp = client.get('/api/integrations/')
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert "integrations" in data
    assert any(i["provider"] == "google" for i in data["integrations"])

    # 2. GET /api/integrations/google/connect/
    with patch.object(GoogleOAuthProviderClient, 'get_authorization_url', return_value="https://accounts.google.com/mock-auth"):
        connect_resp = client.get('/api/integrations/google/connect/')
        assert connect_resp.status_code == 200
        conn_data = connect_resp.json()
        assert "authorization_url" in conn_data
        assert "state" in conn_data
        state_token = conn_data["state"]

    # 3. POST /api/integrations/google/callback/
    with patch.object(GoogleOAuthProviderClient, 'exchange_code_for_tokens', return_value={
        "access_token": "ya29.api_mock_token",
        "refresh_token": "1//api_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "openid email"
    }), patch.object(GoogleOAuthProviderClient, 'get_user_info', return_value={"email": "api@test.com", "name": "API User"}):
        cb_resp = client.post('/api/integrations/google/callback/', {
            "code": "test_code_123",
            "state": state_token
        }, format='json')
        assert cb_resp.status_code == 200
        assert cb_resp.json()["status"] == "CONNECTED"

    # 4. POST /api/integrations/google/disconnect/
    disc_resp = client.post('/api/integrations/google/disconnect/')
    assert disc_resp.status_code == 200
    assert "Successfully disconnected" in disc_resp.json()["message"]
