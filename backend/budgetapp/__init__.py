"""BudgetApp Django project package.

Importing the Celery app here ensures it is always registered when Django
starts, so ``@shared_task`` decorators find the correct broker.
"""

from __future__ import annotations

from .celery import app as celery_app

__all__ = ("celery_app",)
