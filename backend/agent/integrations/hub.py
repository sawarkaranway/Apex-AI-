"""
Integration Hub & Encrypted Credential Security Manager for Chaitanya Karya.
Enforces the chain:
User -> Integration -> OAuthGrant -> EncryptedCredential -> ProviderClient -> ProviderAdapter
"""

import os
import secrets
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timezone, timedelta
from django.db import transaction
from django.utils import timezone as dj_timezone
from django.contrib.auth.models import User

from api.models import Integration, OAuthGrant, EncryptedCredential, OAuthStateNonce
from agent.vault import CredentialVault
from agent.providers.google.client import GoogleOAuthProviderClient, GoogleOAuthError, DEFAULT_GOOGLE_SCOPES
from agent.providers.google.calendar_adapter import GoogleCalendarProvider
from agent.providers.google.gmail_adapter import GoogleGmailProvider
from agent.interfaces.calendar import CalendarProvider
from agent.interfaces.email import EmailProvider
from agent.providers import default_calendar_provider, default_email_provider


class IntegrationError(Exception):
    """Base error for integration and credential operations."""
    pass


class InvalidOAuthStateError(IntegrationError):
    """Raised when an OAuth state token is missing, expired, or invalid."""
    pass


class IntegrationNotConnectedError(IntegrationError):
    """Raised when attempting an operation on an inactive or disconnected integration."""
    pass


class TokenRefreshError(IntegrationError):
    """Raised when token refresh fails and re-authentication is required."""
    pass


# Default 256-bit vault key for development / testing if not provided in environment
DEV_DEFAULT_VAULT_KEY = b"01234567890123456789012345678901"  # 32 bytes


def get_credential_vault() -> CredentialVault:
    """Returns initialized CredentialVault instance using configured master key."""
    hex_key = os.getenv("CREDENTIAL_VAULT_MASTER_KEY_HEX")
    if hex_key:
        return CredentialVault.from_hex(hex_key)
    raw_key = os.getenv("CREDENTIAL_VAULT_MASTER_KEY", "").encode("utf-8")
    if len(raw_key) == 32:
        return CredentialVault(raw_key)
    return CredentialVault(DEV_DEFAULT_VAULT_KEY)


class IntegrationHub:
    """
    Central Manager for OAuth2 Integrations, AES-256-GCM Credential Vault,
    and Dynamic Provider Adapter Resolution.
    """

    def __init__(
        self,
        vault: Optional[CredentialVault] = None,
        google_client: Optional[GoogleOAuthProviderClient] = None
    ):
        self.vault = vault or get_credential_vault()
        self.google_client = google_client or GoogleOAuthProviderClient()

    def start_oauth_flow(
        self,
        user_id: int,
        provider_id: str,
        redirect_uri: str,
        scopes: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """
        Initiates OAuth authorization flow, generating and persisting a CSRF state token.
        Returns (authorization_url, state_token).
        """
        user = User.objects.get(id=user_id)
        state_token = secrets.token_urlsafe(32)
        expires_at = dj_timezone.now() + timedelta(minutes=15)

        # Clear existing pending states for user + provider
        OAuthStateNonce.objects.filter(user=user, provider=provider_id).delete()
        OAuthStateNonce.objects.create(
            user=user,
            provider=provider_id,
            state_token=state_token,
            redirect_uri=redirect_uri,
            expires_at=expires_at
        )

        if provider_id.lower() == "google":
            auth_url = self.google_client.get_authorization_url(
                state=state_token,
                redirect_uri=redirect_uri,
                scopes=scopes or DEFAULT_GOOGLE_SCOPES
            )
            return auth_url, state_token
        else:
            raise NotImplementedError(f"Provider '{provider_id}' is not yet supported in Phase 1.")

    def complete_oauth_flow(
        self,
        user_id: int,
        provider_id: str,
        code: str,
        state: str,
        redirect_uri: str
    ) -> Integration:
        """
        Completes OAuth flow: validates state, exchanges code for tokens,
        encrypts credentials with AES-256-GCM + AAD, and persists metadata.
        """
        user = User.objects.get(id=user_id)

        # 1. State Token Validation
        state_record = OAuthStateNonce.objects.filter(
            user=user,
            provider=provider_id,
            state_token=state
        ).first()

        if not state_record:
            raise InvalidOAuthStateError("Invalid or unrecognized OAuth state token.")

        if not state_record.is_valid():
            state_record.delete()
            raise InvalidOAuthStateError("OAuth state token has expired.")

        state_record.delete()  # Single-use consumption

        # 2. Token Exchange & User Info
        if provider_id.lower() == "google":
            token_data = self.google_client.exchange_code_for_tokens(code, redirect_uri)
            access_token = token_data.get("access_token", "")
            refresh_token = token_data.get("refresh_token", "")
            expires_in = token_data.get("expires_in", 3600)
            token_type = token_data.get("token_type", "Bearer")
            granted_scopes = token_data.get("scope", "").split()

            user_info = {}
            try:
                user_info = self.google_client.get_user_info(access_token)
            except Exception:
                pass

            account_email = user_info.get("email", "")
            account_name = user_info.get("name", "")
        else:
            raise NotImplementedError(f"Provider '{provider_id}' is not yet supported in Phase 1.")

        # 3. Encrypt Secrets with AES-256-GCM + AAD
        aad = CredentialVault.construct_aad(user_id, provider_id)
        secret_payload = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": token_type,
        }
        encrypted_envelope = self.vault.encrypt_secret(secret_payload, associated_data=aad)
        expires_at = dj_timezone.now() + timedelta(seconds=expires_in)

        # 4. Atomic Database Persistence
        with transaction.atomic():
            integration, _ = Integration.objects.update_or_create(
                user=user,
                provider=provider_id.lower(),
                defaults={
                    "status": "CONNECTED",
                    "account_email": account_email,
                    "account_name": account_name,
                    "last_successful_auth": dj_timezone.now(),
                }
            )

            grant, _ = OAuthGrant.objects.update_or_create(
                integration=integration,
                defaults={
                    "scopes": granted_scopes,
                    "token_type": token_type,
                    "expires_at": expires_at,
                    "revoked_at": None,
                }
            )

            EncryptedCredential.objects.update_or_create(
                grant=grant,
                defaults={
                    "encrypted_envelope": encrypted_envelope,
                    "key_version": 1,
                }
            )

        return integration

    def get_active_credential(self, user_id: int, provider_id: str) -> Dict[str, Any]:
        """
        Retrieves decrypted credential for user & provider.
        Automatically handles token refresh if expired.
        """
        integration = Integration.objects.filter(
            user_id=user_id,
            provider=provider_id.lower()
        ).first()

        if not integration or integration.status != "CONNECTED":
            raise IntegrationNotConnectedError(f"Integration '{provider_id}' is not connected for user {user_id}.")

        grant = getattr(integration, "grant", None)
        if not grant:
            raise IntegrationNotConnectedError(f"No OAuth grant found for integration '{provider_id}'.")

        encrypted_cred = getattr(grant, "encrypted_credential", None)
        if not encrypted_cred:
            raise IntegrationNotConnectedError(f"No encrypted credentials found for integration '{provider_id}'.")

        # Decrypt secret with AAD verification
        aad = CredentialVault.construct_aad(user_id, provider_id)
        secret_payload = self.vault.decrypt_secret(encrypted_cred.encrypted_envelope, expected_associated_data=aad)

        # Check for expiration (with 60s buffer)
        is_expired = False
        if grant.expires_at:
            is_expired = dj_timezone.now() >= (grant.expires_at - timedelta(seconds=60))

        if is_expired:
            refresh_token = secret_payload.get("refresh_token")
            if not refresh_token:
                integration.status = "REAUTH_REQUIRED"
                integration.save(update_fields=["status"])
                raise TokenRefreshError("Access token expired and no refresh token is available. Re-auth required.")

            # Perform refresh
            try:
                if provider_id.lower() == "google":
                    new_token_data = self.google_client.refresh_access_token(refresh_token)
                    new_access_token = new_token_data.get("access_token", "")
                    new_expires_in = new_token_data.get("expires_in", 3600)
                    new_refresh_token = new_token_data.get("refresh_token") or refresh_token

                    secret_payload["access_token"] = new_access_token
                    secret_payload["refresh_token"] = new_refresh_token

                    # Re-encrypt and update DB
                    new_envelope = self.vault.encrypt_secret(secret_payload, associated_data=aad)
                    with transaction.atomic():
                        grant.expires_at = dj_timezone.now() + timedelta(seconds=new_expires_in)
                        grant.save(update_fields=["expires_at"])
                        encrypted_cred.encrypted_envelope = new_envelope
                        encrypted_cred.save(update_fields=["encrypted_envelope"])
                        integration.last_successful_auth = dj_timezone.now()
                        integration.save(update_fields=["last_successful_auth"])
            except Exception as e:
                integration.status = "REAUTH_REQUIRED"
                integration.save(update_fields=["status"])
                raise TokenRefreshError(f"Failed to refresh OAuth token: {str(e)}") from e

        return secret_payload

    def disconnect_integration(self, user_id: int, provider_id: str) -> bool:
        """
        Revokes token with provider, wipes encrypted credentials, and updates status.
        """
        integration = Integration.objects.filter(
            user_id=user_id,
            provider=provider_id.lower()
        ).first()

        if not integration:
            return False

        try:
            grant = getattr(integration, "grant", None)
            if grant and hasattr(grant, "encrypted_credential"):
                aad = CredentialVault.construct_aad(user_id, provider_id)
                secret = self.vault.decrypt_secret(grant.encrypted_credential.encrypted_envelope, aad)
                token = secret.get("refresh_token") or secret.get("access_token")
                if token and provider_id.lower() == "google":
                    try:
                        self.google_client.revoke_token(token)
                    except Exception:
                        pass
        except Exception:
            pass

        with transaction.atomic():
            if hasattr(integration, "grant"):
                if hasattr(integration.grant, "encrypted_credential"):
                    integration.grant.encrypted_credential.delete()
                integration.grant.delete()
            integration.status = "DISCONNECTED"
            integration.save(update_fields=["status"])

        return True

    def get_calendar_provider(self, user_id: int) -> CalendarProvider:
        """
        Returns active provider adapter for calendar.
        If Google is connected, returns GoogleCalendarProvider; otherwise fallback in-memory.
        """
        try:
            creds = self.get_active_credential(user_id, "google")
            access_token = creds.get("access_token")
            if access_token:
                return GoogleCalendarProvider(access_token=access_token)
        except Exception:
            pass
        return default_calendar_provider

    def get_email_provider(self, user_id: int) -> EmailProvider:
        """
        Returns active provider adapter for email.
        If Google is connected, returns GoogleGmailProvider; otherwise fallback in-memory.
        """
        try:
            creds = self.get_active_credential(user_id, "google")
            access_token = creds.get("access_token")
            if access_token:
                return GoogleGmailProvider(access_token=access_token)
        except Exception:
            pass
        return default_email_provider


# Singleton instance
integration_hub = IntegrationHub()
