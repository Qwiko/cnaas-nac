from fastapi import APIRouter


from .auth import router as auth_router
from .assignment_rule import router as assignment_rule_router
from .logs import router as logs_router
from .nas_port import router as nas_port_router
from .rbac import router as rbac_router
from .user import router as user_router
from .vlan import router as vlan_router

api_v2_router = APIRouter(prefix="/api/v2")

api_v2_router.include_router(auth_router)
api_v2_router.include_router(assignment_rule_router)
api_v2_router.include_router(logs_router)
api_v2_router.include_router(nas_port_router)
api_v2_router.include_router(rbac_router)
api_v2_router.include_router(user_router)
api_v2_router.include_router(vlan_router)
