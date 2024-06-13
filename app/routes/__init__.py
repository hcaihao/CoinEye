from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from functools import wraps

from typing import Any
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

LocationType = Union[str, Sequence, None]


def admin_required(optional: bool = False, fresh: bool = False, refresh: bool = False, locations: LocationType = None, verify_type: bool = True):
    """管理权限装饰器"""

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request(optional, fresh, refresh, locations, verify_type)
            claims = get_jwt()
            if claims["is_admin"]:
                return fn(*args, **kwargs)
            else:
                return {"code": 1, "msg": "权限不足。"}

        return decorator

    return wrapper


def user_required(optional: bool = False, fresh: bool = False, refresh: bool = False, locations: LocationType = None, verify_type: bool = True):
    """用户权限装饰器"""

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request(optional, fresh, refresh, locations, verify_type)
            claims = get_jwt()
            if not claims["is_admin"]:
                return fn(*args, **kwargs)
            else:
                return {"code": 1, "msg": "权限不足。"}

        return decorator

    return wrapper
