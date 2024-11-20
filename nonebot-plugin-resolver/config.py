from pydantic import BaseModel, Extra
from typing import Optional


class Config(BaseModel, extra=Extra.ignore):
    xhs_ck: Optional[str] = ''
    douyin_ck: Optional[str] = ''
    is_oversea: Optional[bool] = False
    bili_sessdata: Optional[str] = ''
    r_global_nickname: Optional[str] = ''
    resolver_proxy: Optional[str] = 'http://127.0.0.1:7890'
    video_duration_maximum: Optional[int] = 480
    global_resolve_controller: Optional[str] = ""
