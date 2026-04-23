"""DRF serializers for ``apps.notifications``.

Scope: serializers for Notification (in-app), Webhook (creation payload
returning one-time secret, plus read payload without secret), and
UserChannelPreference.
"""

from __future__ import annotations
