from fastapi import APIRouter

from app.api.v1.routers import admin, auth, deals, intents, matching, offers, wallets
from app.platform.router import router as platform_router
from app.shop.router import router as shop_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(shop_router)
api_router.include_router(offers.router)
api_router.include_router(intents.router)
api_router.include_router(matching.router)
api_router.include_router(deals.router)
api_router.include_router(wallets.router)
api_router.include_router(platform_router)
api_router.include_router(admin.router)
