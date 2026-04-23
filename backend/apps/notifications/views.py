"""HTTP views for ``apps.notifications``.

Scope: in-app inbox listing + mark-read, webhook CRUD (creation returns
the plaintext secret exactly once), per-user channel preference
management, dead-letter queue inspection for admins. No handlers yet.
"""

from __future__ import annotations
