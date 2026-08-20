"""
Google OAuth2 Provider Client for Chaitanya Karya.
Handles raw HTTP communication with Google OAuth endpoints with error handling,
token refreshing, revocation, and user identity resolution.
"""

import os
import urllib.parse
from typing import Dict, Any, List, Optional
import requests

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Minimal default scopes for calendar and gmail capabilities
DEFAULT_GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GoogleOAuthError(Exception):
    """Base exception for Google OAuth errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class GoogleOAuthProviderClient:
    """
    Low-level provider client for Google OAuth2 and API invocation.
    Does not store secrets or access tokens internally; receives them as explicit parameters.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        http_session: Optional[requests.Session] = None
    ):
        self.client_id = client_id or os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
        self.session = http_session or requests.Session()

    def get_authorization_url(
        self,
        state: str,
        redirect_uri: str,
        scopes: Optional[List[str]] = None,
        access_type: str = "offline",
        prompt: str = "consent"
    ) -> str:
        """
        Generates the Google OAuth2 consent URL with state nonce.
        """
        if not self.client_id:
            raise GoogleOAuthError("GOOGLE_OAUTH_CLIENT_ID is not configured.")

        selected_scopes = scopes or DEFAULT_GOOGLE_SCOPES
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(selected_scopes),
            "access_type": access_type,
            "prompt": prompt,
            "state": state,
            "include_granted_scopes": "true",
        }
        return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchanges the authorization code for access and refresh tokens.
        """
        if not self.client_id or not self.client_secret:
            raise GoogleOAuthError("Google OAuth client credentials are not configured.")

        payload = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        resp = self.session.post(GOOGLE_TOKEN_URL, data=payload, timeout=10)
        data = resp.json()

        if resp.status_code != 200 or "access_token" not in data:
            error_desc = data.get("error_description") or data.get("error") or "Token exchange failed"
            raise GoogleOAuthError(f"OAuth code exchange failed: {error_desc}", status_code=resp.status_code, response_data=data)

        return data

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Obtains a new access token using a valid refresh token.
        """
        if not self.client_id or not self.client_secret:
            raise GoogleOAuthError("Google OAuth client credentials are not configured.")

        payload = {
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }

        resp = self.session.post(GOOGLE_TOKEN_URL, data=payload, timeout=10)
        data = resp.json()

        if resp.status_code != 200 or "access_token" not in data:
            error_desc = data.get("error_description") or data.get("error") or "Token refresh failed"
            raise GoogleOAuthError(f"OAuth token refresh failed: {error_desc}", status_code=resp.status_code, response_data=data)

        return data

    def revoke_token(self, token: str) -> bool:
        """
        Revokes an access or refresh token at Google's revocation endpoint.
        """
        resp = self.session.post(GOOGLE_REVOKE_URL, params={"token": token}, timeout=10)
        return resp.status_code == 200

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Queries user profile information from Google userinfo endpoint.
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = self.session.get(GOOGLE_USERINFO_URL, headers=headers, timeout=10)
        if resp.status_code != 200:
            raise GoogleOAuthError("Failed to fetch Google userinfo profile", status_code=resp.status_code)
        return resp.json()
