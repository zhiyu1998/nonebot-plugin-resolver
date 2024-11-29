import os
import shutil

from nonebot import get_driver, logger, require
from nonebot.plugin import PluginMetadata
from bilibili_api import Credential

from .handlers import resolvers, controllers
from .config import *
from .cookie import *

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

__plugin_meta__ = PluginMetadata(
    name="链接分享解析器",
    description="NoneBot2链接分享解析器插件。解析视频、图片链接/小程序插件，tiktok、bilibili、twitter等实时发送！",
    usage="分享链接即可体验到效果",
    type="application",
    homepage="https://github.com/zhiyu1998/nonebot-plugin-resolver",
    config=Config,
    supported_adapters={ "~onebot.v11" }
)

@get_driver().on_startup
async def _():
    if RCONFIG.r_bili_ck:
        pass
        # cookie_dict = cookies_str_to_dict(RCONFIG.r_bili_ck)
        # if cookie_dict["SESSDATA"]:
        #     logger.info(f"bilibili credential format sucess from cookie")
        # else:
        #     logger.error(f"配置的 bili_ck 未包含 SESSDATA 项，可能无效")
        # save_cookies_to_netscape(RCONFIG.bili_ck, bili_cookies_file, 'bilibili.com')
    if RCONFIG.r_ytb_ck:
        save_cookies_to_netscape(RCONFIG.r_ytb_ck, YTB_COOKIES_FILE, 'youtube.com')
    # 处理黑名单 resovler
    for resolver in RCONFIG.r_black_resolvers:
        if matcher := resolvers[resolver]:
            matcher.destroy()
            logger.info(f"解析器 {resolver} 已销毁")

@scheduler.scheduled_job(
    "cron",
    hour=0,
    minute=0,
)
async def _():
    temp_path = RPATH / "temp"
    if not os.path.exists(temp_path):
        logger.error(f"The folder {temp_path} does not exist.")
        return
    for filename in os.listdir(temp_path):
        file_path = os.path.join(temp_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # 删除文件或链接
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # 递归删除文件夹
        except Exception as e:
            logger.error(f"Failed to delete {file_path}. Reason: {e}")
    logger.info(f"{temp_path.absolute()} 已清理")
