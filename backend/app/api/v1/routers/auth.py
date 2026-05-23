from fastapi import APIRouter



from app.auth.router import agent_router, auth_router, users_router



router = APIRouter()

router.include_router(auth_router)

router.include_router(users_router)

router.include_router(agent_router)

