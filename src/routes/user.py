from fastapi import FastAPI , APIRouter, Depends
import os
from helpers.config import get_settings, Settings
from fastapi import FastAPI , APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from .schemes import UserRequest

user_router =  APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)


@user_router.post("/upload/{user_id}")
async def add_user(request: Request, user_id: str, file: UploadFile, app_settings: Settings = Depends(get_settings)):
    pass