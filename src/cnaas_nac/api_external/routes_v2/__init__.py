from fastapi import APIRouter


from .auth import router as auth_router
from .endpoint import router as endpoint_router
from .endpoint_group import router as endpoint_group_router
from .logs import router as logs_router
from .nas_port import router as nas_port_router
from .policy import router as policy_router
from .rbac import router as rbac_router
from .vlan import router as vlan_router

api_v2_router = APIRouter(prefix="/api/v2")

api_v2_router.include_router(auth_router)
api_v2_router.include_router(endpoint_router)
api_v2_router.include_router(endpoint_group_router)
api_v2_router.include_router(logs_router)
api_v2_router.include_router(nas_port_router)
api_v2_router.include_router(policy_router)
api_v2_router.include_router(rbac_router)
api_v2_router.include_router(vlan_router)
