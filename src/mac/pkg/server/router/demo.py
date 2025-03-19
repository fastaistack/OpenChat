from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel

from ...projectvar import Projectvar
from ...projectvar import constants as const
from ..depends import get_headers
import os

gvar = Projectvar()

router = APIRouter(
    prefix = "/demo",
    tags=["demo"],
    responses={404: {"description": "Not found"}},
)

class Demo(BaseModel):
    demo: str

@router.post("/hello")
async def hello(demo: Demo, headers=Depends(get_headers)):
    print(headers)
    print(headers[const.HTTP_HEADER_USER_ID])
    print(headers[const.HTTP_HEADER_USER_ROLE])
    return {"result": "hello" + demo.demo}

