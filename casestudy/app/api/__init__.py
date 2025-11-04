from fastapi import APIRouter

from casestudy.app.api.v1.routes import cases

api_router = APIRouter()
api_router.include_router(cases.router)
