"""ASGI entrypoint for BudgetApp.

The production container runs ``uvicorn budgetapp.asgi:application`` on port
8000. See the project ``Dockerfile`` and root ``docker-compose.yml``.
"""

from __future__ import annotations

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "budgetapp.settings")

application = get_asgi_application()
