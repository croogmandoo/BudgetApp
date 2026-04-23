"""Django admin registration for ``apps.core`` models.

Deliberately minimal: the audit log must never expose a delete path, and
attachments are referenced indirectly from domain apps. Admin UI polish
(list displays, filters) lands later.
"""

from __future__ import annotations
