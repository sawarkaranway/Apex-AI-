import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chaitanya_backend.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

site, _ = Site.objects.get_or_create(id=1, defaults={'domain': '127.0.0.1:8000', 'name': 'Chaitanya Karya'})
site.domain = '127.0.0.1:8000'
site.name = 'Chaitanya Karya'
site.save()

client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '')

app, created = SocialApp.objects.get_or_create(
    provider='google',
    defaults={'name': 'Google OAuth', 'client_id': client_id, 'secret': client_secret}
)
if not created:
    app.client_id = client_id
    app.secret = client_secret
    app.save()

app.sites.add(site)
print(f"Successfully configured Google SocialApp with Client ID: {client_id[:25]}...")
