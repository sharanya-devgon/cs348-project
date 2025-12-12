import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

app = get_asgi_application()
# test