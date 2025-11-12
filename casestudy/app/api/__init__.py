from fastapi import APIRouter

from casestudy.app.api.v1.routes import auth, cases

api_router = APIRouter()
api_router.include_router(cases.router)
api_router.include_router(auth.router)
