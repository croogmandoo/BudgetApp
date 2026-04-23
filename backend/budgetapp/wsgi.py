"""WSGI entrypoint for BudgetApp.

Kept for management commands and any operator who prefers a sync server.
The primary runtime is ASGI + uvicorn (see ``asgi.py``).
"""

from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "budgetapp.settings")

application = get_wsgi_application()
