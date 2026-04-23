"""HTTP views for ``apps.maintenance``.

Scope: MaintenanceTask CRUD, "mark done" action (advances next_due and
optionally creates a cost transaction), due/overdue list endpoints. No
handlers yet.
"""

from __future__ import annotations
