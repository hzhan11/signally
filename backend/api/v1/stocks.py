from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/list")
async def get_list():
    return ["002594","Stock2","Stock3","Stock4"]


