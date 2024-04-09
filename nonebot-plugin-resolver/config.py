from pydantic import BaseModel, Extra
from typing import Optional


class Config(BaseModel, extra=Extra.ignore):
    douyin_ck: Optional[str] = ''
    is_oversea: Optional[bool] = False
    is_lagrange: Optional[bool] = False
    resolver_proxy: Optional[str] = 'http://127.0.0.1:7890'