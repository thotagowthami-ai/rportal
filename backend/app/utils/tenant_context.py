from contextvars import ContextVar
from typing import Optional

_current_tenant_id: ContextVar[Optional[str]] = ContextVar("current_tenant_id", default=None)


def set_current_tenant_id(tenant_id: Optional[str]) -> None:
    _current_tenant_id.set(tenant_id)


def get_current_tenant_id() -> Optional[str]:
    return _current_tenant_id.get()
