from fastapi import APIRouter

from .auth import router as auth_router

from .oui import router as oui_router
from .user import router as user_router
from .vlan import router as vlan_router

api_v2_router = APIRouter(prefix="/api/v2")

api_v2_router.include_router(auth_router)
api_v2_router.include_router(oui_router)
api_v2_router.include_router(user_router)
api_v2_router.include_router(vlan_router)
