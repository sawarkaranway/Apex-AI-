import json
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from rest_framework_simplejwt.tokens import RefreshToken
from dj_rest_auth.views import PasswordResetConfirmView
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://localhost:5173/oauth/callback"
    client_class = OAuth2Client

class GitHubLogin(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    callback_url = "http://localhost:5173/oauth/callback"
    client_class = OAuth2Client

def oauth_success_callback(request):
    """
    Renders an HTML response that stores JWT tokens into localStorage and redirects back to the React app with token.
    Syncs active Google OAuth credentials into IntegrationHub AES-256-GCM vault.
    """
    if not request.user.is_authenticated:
        return HttpResponse("Authentication failed. Please return to Chaitanya Karya.", status=401)
    
    # Sync Google Token to Integration Hub & Vault
    try:
        from allauth.socialaccount.models import SocialToken
        from api.models import Integration, OAuthGrant, EncryptedCredential
        from agent.vault import CredentialVault
        from agent.integrations.hub import get_credential_vault
        from django.utils import timezone as dj_timezone
        from datetime import timedelta

        st = SocialToken.objects.filter(account__user=request.user, account__provider='google').first()
        if st and st.token:
            vault = get_credential_vault()
            aad = CredentialVault.construct_aad(request.user.id, "google")
            secret_payload = {
                "access_token": st.token,
                "refresh_token": st.token_secret or "",
                "token_type": "Bearer",
            }
            encrypted_envelope = vault.encrypt_secret(secret_payload, associated_data=aad)
            
            integ, _ = Integration.objects.update_or_create(
                user=request.user,
                provider="google",
                defaults={
                    "status": "CONNECTED",
                    "account_email": request.user.email,
                    "account_name": f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                    "last_successful_auth": dj_timezone.now(),
                }
            )
            grant, _ = OAuthGrant.objects.update_or_create(
                integration=integ,
                defaults={
                    "scopes": ["profile", "email", "https://www.googleapis.com/auth/calendar.events"],
                    "token_type": "Bearer",
                    "expires_at": st.expires_at or (dj_timezone.now() + timedelta(hours=1)),
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
    except Exception as e:
        print("[OAuth Sync Warning]", e)

    refresh = RefreshToken.for_user(request.user)
    access_token = str(refresh.access_token)
    user_json = json.dumps({
        'pk': request.user.pk,
        'username': request.user.username,
        'email': request.user.email,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name
    })

    redirect_url = f"http://localhost:5173/#/?token={access_token}"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Chaitanya Karya - Login Successful</title>
    <style>
        body {{
            background: #0B0F19;
            color: #F8FAFC;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }}
        .card {{
            background: #1E293B;
            padding: 32px 48px;
            border-radius: 12px;
            border: 1px solid #334155;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        .spinner {{
            width: 36px;
            height: 36px;
            border: 3px solid #334155;
            border-top-color: #38BDF8;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 16px;
        }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <div class="card">
        <div class="spinner"></div>
        <h2 style="color: #38BDF8; margin-bottom: 8px;">Authentication Successful</h2>
        <p style="color: #94A3B8; margin: 0;">Connecting your Google account to Chaitanya Karya...</p>
    </div>
    <script>
        try {{
            localStorage.setItem('auth_token', '{access_token}');
        }} catch (e) {{}}
        window.location.replace('{redirect_url}');
    </script>
</body>
</html>"""
    return HttpResponse(html, content_type="text/html")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/profile/', oauth_success_callback, name='oauth_profile_callback'),
    path('api/auth/oauth/success/', oauth_success_callback, name='oauth_success_callback'),
    path('api/', include('api.urls')),
    path('api/auth/password/reset/confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/', include('allauth.socialaccount.providers.google.urls')),
    path('api/auth/', include('allauth.socialaccount.providers.github.urls')),
    path('api/auth/google/rest/', GoogleLogin.as_view(), name='google_rest_login'),
    path('api/auth/github/rest/', GitHubLogin.as_view(), name='github_rest_login'),
    path('api/auth/social/', include('allauth.socialaccount.urls')),
]
