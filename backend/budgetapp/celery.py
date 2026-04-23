"""Celery application for BudgetApp.

Background jobs in v1 (SPEC §5 / §9):
    - Recurring bill materialization.
    - Maintenance reminder dispatch.
    - Import file parsing.
    - Outbound webhook delivery (with retry + exponential backoff, SPEC §3.7).

The worker and beat are started from the root ``docker-compose.yml`` as
separate services sharing this image.
"""

from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "budgetapp.settings")

app = Celery("budgetapp")

# Pull every ``CELERY_*`` key off the Django settings module.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover ``tasks.py`` in each installed app.
app.autodiscover_tasks()
