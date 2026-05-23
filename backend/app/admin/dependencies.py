from typing import Annotated

from fastapi import Depends

from app.admin.constants import ERR_ADMIN_FORBIDDEN
from app.auth.constants import UserRole
from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser, raise_auth_error


async def require_admin(
    current: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if current.role != UserRole.ADMIN:
        raise_auth_error(
            code=ERR_ADMIN_FORBIDDEN,
            message="admin access required",
            http_status=403,
        )
    return current
