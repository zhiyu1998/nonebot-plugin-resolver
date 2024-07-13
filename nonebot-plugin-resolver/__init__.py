import asyncio
import json
import os.path
from typing import cast

from nonebot import on_regex, get_driver, logger
from nonebot.exception import ActionFailed, NetworkError
from nonebot.plugin import PluginMetadata
from nonebot.matcher import current_bot
from nonebot.adapters.onebot.v11 import Message, Event, Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, PrivateMessageEvent

from .common_utils import *
from .config import Config
from .bili23_utils import get_download_url, download_b_file, merge_file_to_mp4, get_dynamic, extra_bili_info
from .tiktok_utills import generate_x_bogus_url
from .acfun_utils import parse_url, download_m3u8_videos, parse_m3u8, merge_ac_file_to_mp4
from .ytdlp_utils import get_video_title, download_ytb_video
from .freyrjs import parse_freyr_log, execute_freyr_command
from .constants import URL_TYPE_CODE_DICT, BILI_VIDEO_INFO, DOUYIN_VIDEO, GENERAL_REQ_LINK, XHS_REQ_LINK

__plugin_meta__ = PluginMetadata(
    name="链接分享解析器",
    description="NoneBot2链接分享解析器插件。解析视频、图片链接/小程序插件，tiktok、bilibili、twitter等实时发送！",
    usage="分享链接即可体验到效果",
    type="application",
    homepage="https://github.com/zhiyu1998/nonebot-plugin-resolver",
    config=Config,
)

# 配置加载
global_config = Config.parse_obj(get_driver().config.dict())
# 🪜地址
resolver_proxy: str = getattr(global_config, "resolver_proxy", "http://127.0.0.1:7890")
# 是否是海外服务器
IS_OVERSEA: bool = bool(getattr(global_config, "is_oversea", False))
# 是否是拉格朗日引擎
IS_LAGRANGE: bool = bool(getattr(global_config, "is_lagrange", False))
# 哔哩哔哩限制的最大视频时长（默认8分钟），单位：秒
VIDEO_DURATION_MAXIMUM: int = int(getattr(global_config, "video_duration_maximum", 480))
# 代理加载
aiohttp_proxies = {
    'http': resolver_proxy,
    'https': resolver_proxy
}
httpx_proxies = {
    "http://": resolver_proxy,
    "https://": resolver_proxy,
}

bili23 = on_regex(
    r"(.*)(bilibili.com|b23.tv|BV[0-9a-zA-Z]{10})", priority=1
)
douyin = on_regex(
    r"(.*)(v.douyin.com)", priority=1
)
tik = on_regex(
    r"(.*)(www.tiktok.com)|(vt.tiktok.com)|(vm.tiktok.com)", priority=1
)
acfun = on_regex(r"(.*)(acfun.cn)")
twit = on_regex(
    r"(.*)(x.com)", priority=1
)
xhs = on_regex(
    r"(.*)(xhslink.com|xiaohongshu.com)", priority=1
)
y2b = on_regex(
    r"(.*)(youtube.com|youtu.be)", priority=1
)
freyr = on_regex(
    r"(.*)(music.apple.com|open.spotify.com)"
)

GLOBAL_NICKNAME = "R插件极速版"


@bili23.handle()
async def bilibili(event: Event) -> None:
    """
        哔哩哔哩解析
    :param event:
    :return:
    """
    header = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'referer': 'https://www.bilibili.com',
    }
    # 消息
    url: str = str(event.message).strip()
    # 正则匹配
    url_reg = "(http:|https:)\/\/www.bilibili.com\/[A-Za-z\d._?%&+\-=\/#]*"
    b_short_rex = "(http:|https:)\/\/b23.tv\/[A-Za-z\d._?%&+\-=\/#]*"
    # BV处理
    if re.match(r'^BV[1-9a-zA-Z]{10}$', url):
        url = 'https://www.bilibili.com/video/' + url
    # 处理短号、小程序问题
    if 'b23.tv' in url or ('b23.tv' and 'QQ小程序' in url):
        b_short_url = re.search(b_short_rex, url)[0]
        resp = httpx.get(b_short_url, headers=header, follow_redirects=True)
        url: str = str(resp.url)
    else:
        url: str = re.search(url_reg, url)[0]
    # 发现解析的是动态，转移一下
    if 't.bilibili.com' in url:
        # 去除多余的参数
        if '?' in url:
            url = url[:url.index('?')]
        dynamic_id = re.search(r'[^/]+(?!.*/)', url)[0]
        dynamic_desc, dynamic_src = get_dynamic(dynamic_id)
        if len(dynamic_src) > 0:
            await bili23.send(Message(f"{GLOBAL_NICKNAME}识别：B站动态，{dynamic_desc}"))
            paths = await asyncio.gather(*dynamic_src)
            await asyncio.gather(*[bili23.send(Message(f"[CQ:image,file=file:///{path}]")) for path in paths])
            # 刪除文件
            for temp in paths:
                # logger.info(f'{temp}')
                os.unlink(temp)
        # 跳出函数
        return

    # 获取视频信息
    # logger.error(url)
    video_id = re.search(r"video\/[^\?\/ ]+", url)[0].split('/')[1]
    # logger.error(video_id)
    video_info = httpx.get(
        f"{BILI_VIDEO_INFO}?bvid={video_id}" if video_id.startswith(
            "BV") else f"{BILI_VIDEO_INFO}?aid={video_id}", headers=header)
    # logger.info(video_info)
    video_info = video_info.json()['data']
    if video_info is None:
        await bili23.send(Message(f"{GLOBAL_NICKNAME}识别：B站，出错，无法获取数据！"))
        return
    video_title, video_cover, video_desc, video_duration = video_info['title'], video_info['pic'], video_info['desc'], video_info['duration']

    video_title = delete_boring_characters(video_title)
    # video_title = re.sub(r'[\\/:*?"<>|]', "", video_title)
    # 截断下载时间比较长的视频
    if video_duration <= VIDEO_DURATION_MAXIMUM:
        await bili23.send(Message(MessageSegment.image(video_cover)) + Message(
            f"\n{GLOBAL_NICKNAME}识别：B站，{video_title}\n{extra_bili_info(video_info)}\n简介：{video_desc}"))
    else:
        return await bili23.finish(
            Message(MessageSegment.image(video_cover)) + Message(
                f"\n{GLOBAL_NICKNAME}识别：B站，{video_title}\n{extra_bili_info(video_info)}\n简介：{video_desc}\n---------\n⚠️ 当前视频时长 {video_duration // 60} 分钟，超过管理员设置的最长时间 {VIDEO_DURATION_MAXIMUM // 60} 分钟！"))
    # 获取下载链接
    video_url, audio_url = get_download_url(url)
    # 下载视频和音频
    path = os.getcwd() + "/" + video_id
    try:
        await asyncio.gather(
            download_b_file(video_url, f"{path}-video.m4s", logger.info),
            download_b_file(audio_url, f"{path}-audio.m4s", logger.info))
        merge_file_to_mp4(f"{video_id}-video.m4s", f"{video_id}-audio.m4s", f"{path}-res.mp4")
    finally:
        remove_res = remove_files([f"{video_id}-video.m4s", f"{video_id}-audio.m4s"])
        logger.info(remove_res)
    # logger.info(os.getcwd())
    # 发送出去
    # logger.info(path)
    # await bili23.send(Message(MessageSegment.video(f"{path}-res.mp4")))
    await auto_video_send(event, f"{path}-res.mp4", IS_LAGRANGE)
    # logger.info(f'{path}-res.mp4')

@douyin.handle()
async def dy(bot: Bot, event: Event) -> None:
    """
        抖音解析
    :param event:
    :return:
    """
    # 消息
    msg: str = str(event.message).strip()
    logger.info(msg)
    # 正则匹配
    reg = r"(http:|https:)\/\/v.douyin.com\/[A-Za-z\d._?%&+\-=#]*"
    dou_url = re.search(reg, msg, re.I)[0]
    dou_url_2 = httpx.get(dou_url).headers.get('location')
    # logger.error(dou_url_2)
    reg2 = r".*(video|note)\/(\d+)\/(.*?)"
    # 获取到ID
    dou_id = re.search(reg2, dou_url_2, re.I)[2]
    # logger.info(dou_id)
    # 如果没有设置dy的ck就结束，因为获取不到
    douyin_ck = getattr(global_config, "douyin_ck", "")
    if douyin_ck == "":
        logger.error(global_config)
        await douyin.send(Message(f"{GLOBAL_NICKNAME}识别：抖音，无法获取到管理员设置的抖音ck！"))
        return
    # API、一些后续要用到的参数
    headers = {
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'referer': f'https://www.douyin.com/video/{dou_id}',
        'cookie': douyin_ck
    }
    api_url = DOUYIN_VIDEO.replace("{}", dou_id)
    api_url = generate_x_bogus_url(api_url, headers)  # 如果请求失败直接返回
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers, timeout=10) as response:
            detail = await response.json()
            if detail is None:
                await douyin.send(Message(f"{GLOBAL_NICKNAME}识别：抖音，解析失败！"))
                return
            # 获取信息
            detail = detail['aweme_detail']
            # 判断是图片还是视频
            url_type_code = detail['aweme_type']
            url_type = URL_TYPE_CODE_DICT.get(url_type_code, 'video')
            await douyin.send(Message(f"{GLOBAL_NICKNAME}识别：抖音，{detail.get('desc')}"))
            # 根据类型进行发送
            if url_type == 'video':
                # 识别播放地址
                player_addr_list = detail.get("video").get("play_addr").get("url_list")
                player_addr = player_addr_list[len(player_addr_list) - 1]
                # 发送视频
                # logger.info(player_addr)
                # await douyin.send(Message(MessageSegment.video(player_addr)))
                await auto_video_send(event, player_addr, IS_LAGRANGE)
            elif url_type == 'image':
                # 无水印图片列表/No watermark image list
                no_watermark_image_list = []
                # 有水印图片列表/With watermark image list
                watermark_image_list = []
                # 遍历图片列表/Traverse image list
                for i in detail['images']:
                    # 无水印图片列表
                    # no_watermark_image_list.append(i['url_list'][0])
                    no_watermark_image_list.append(
                        MessageSegment.node_custom(user_id=int(bot.self_id), nickname=GLOBAL_NICKNAME,
                                                   content=Message(MessageSegment.image(i['url_list'][0])))
                    )
                    # 有水印图片列表
                    # watermark_image_list.append(i['download_url_list'][0])
                # 异步发送
                # logger.info(no_watermark_image_list)
                # imgList = await asyncio.gather([])
                if isinstance(event, GroupMessageEvent):
                    await bot.send_group_forward_msg(group_id=event.group_id, messages=no_watermark_image_list)
                else:
                    await bot.send_private_forward_msg(user_id=event.user_id, messages=no_watermark_image_list)


@tik.handle()
async def tiktok(event: Event) -> None:
    """
        tiktok解析
    :param event:
    :return:
    """
    # 消息
    url: str = str(event.message).strip()

    # 海外服务器判断
    proxy = None if IS_OVERSEA else httpx_proxies
    # logger.info(proxy)

    url_reg = r"(http:|https:)\/\/www.tiktok.com\/[A-Za-z\d._?%&+\-=\/#@]*"
    url_short_reg = r"(http:|https:)\/\/vt.tiktok.com\/[A-Za-z\d._?%&+\-=\/#]*"
    url_short_reg2 = r"(http:|https:)\/\/vm.tiktok.com\/[A-Za-z\d._?%&+\-=\/#]*"

    if "vt.tiktok" in url:
        temp_url = re.search(url_short_reg, url)[0]
        temp_resp = httpx.get(temp_url, follow_redirects=True, proxies=httpx_proxies)
        url = temp_resp.url
    elif "vm.tiktok" in url:
        temp_url = re.search(url_short_reg2, url)[0]
        temp_resp = httpx.get(temp_url, headers={"User-Agent": "facebookexternalhit/1.1"}, follow_redirects=True,
                              proxies=httpx_proxies)
        url = str(temp_resp.url)
        # logger.info(url)
    else:
        url = re.search(url_reg, url)[0]
    title = get_video_title(url, IS_OVERSEA, resolver_proxy)

    await tik.send(Message(f"{GLOBAL_NICKNAME}识别：TikTok，{title}\n"))

    target_tik_video_path = await download_ytb_video(url, IS_OVERSEA, os.getcwd(), resolver_proxy, 'tiktok')

    await auto_video_send(event, target_tik_video_path, IS_LAGRANGE)


@acfun.handle()
async def ac(event: Event) -> None:
    """
        acfun解析
    :param event:
    :return:
    """
    # 消息
    inputMsg: str = str(event.message).strip()

    # 短号处理
    if "m.acfun.cn" in inputMsg:
        inputMsg = f"https://www.acfun.cn/v/ac{re.search(r'ac=([^&?]*)', inputMsg)[1]}"

    url_m3u8s, video_name = parse_url(inputMsg)
    await acfun.send(Message(f"{GLOBAL_NICKNAME}识别：猴山，{video_name}"))
    m3u8_full_urls, ts_names, output_folder_name, output_file_name = parse_m3u8(url_m3u8s)
    # logger.info(output_folder_name, output_file_name)
    await asyncio.gather(*[download_m3u8_videos(url, i) for i, url in enumerate(m3u8_full_urls)])
    merge_ac_file_to_mp4(ts_names, output_file_name)
    # await acfun.send(Message(MessageSegment.video(f"{os.getcwd()}/{output_file_name}")))
    await auto_video_send(event, f"{os.getcwd()}/{output_file_name}", IS_LAGRANGE)

@twit.handle()
async def twitter(bot: Bot, event: Event):
    """
        推特解析
    :param event:
    :return:
    """
    msg: str = str(event.message).strip()
    x_url = re.search(r"https?:\/\/x.com\/[0-9-a-zA-Z_]{1,20}\/status\/([0-9]*)", msg)[0]

    logger.debug(GENERAL_REQ_LINK.replace("{}", x_url))
    x_resp = httpx.get(GENERAL_REQ_LINK.replace("{}", x_url), headers={
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive',
        'Pragma': 'no-cache', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1', 'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36', })
    x_url: str = x_resp.json()['data']['url']
    logger.info(x_url)

    await twit.send(Message(f"{GLOBAL_NICKNAME}识别：小蓝鸟学习版"))
    # 主要内容
    aio_task = []

    # 图片
    if x_url.endswith(".jpg") or x_url.endswith(".png"):
        # logger.info(tweet_single.url)
        aio_task.append(download_img(x_url))
    else:
        # 视频
        aio_task.append(download_video(x_url))
    path_res = await asyncio.gather(*aio_task)
    aio_task_res = [auto_determine_send_type(int(bot.self_id), path) for path in path_res]

    # 发送异步后的数据
    if isinstance(event, GroupMessageEvent):
        await bot.send_group_forward_msg(group_id=event.group_id, messages=aio_task_res)
    else:
        await bot.send_private_forward_msg(user_id=event.user_id, messages=aio_task_res)

    # 清除垃圾
    for path in path_res:
        os.unlink(path)


@xhs.handle()
async def xiaohongshu(bot: Bot, event: Event):
    """
        小红书解析
    :param event:
    :return:
    """
    msg_url = re.search(r"(http:|https:)\/\/(xhslink|(www\.)xiaohongshu).com\/[A-Za-z\d._?%&+\-=\/#@]*",
                        str(event.message).strip())[0]
    # 请求头
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'cookie': '',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.4098.3 Safari/537.36',
    }
    if "xhslink" in msg_url:
        msg_url = httpx.get(msg_url, headers=headers, follow_redirects=True).url
        msg_url = str(msg_url)
    xhs_id = re.search(r'/explore/(\w+)', msg_url) or re.search(r'/discovery/item/(\w+)', msg_url)
    xhs_id = xhs_id[1]

    html = httpx.get(f'{XHS_REQ_LINK}{xhs_id}', headers=headers).text
    response_json = re.findall('window.__INITIAL_STATE__=(.*?)</script>', html)[0]
    response_json = response_json.replace("undefined", "null")
    response_json = json.loads(response_json)
    note_data = response_json['note']['noteDetailMap'][xhs_id]['note']
    type = note_data['type']
    note_title = note_data['title']
    note_desc = note_data['desc']
    await xhs.send(Message(
        f"{GLOBAL_NICKNAME}识别：小红书，{note_title}\n{note_desc}"))

    aio_task = []
    if type == 'normal':
        image_list = note_data['imageList']
        # 批量下载
        async with aiohttp.ClientSession() as session:
            for index, item in enumerate(image_list):
                aio_task.append(asyncio.create_task(
                    download_img(item['urlDefault'], f'{os.getcwd()}/{str(index)}.jpg', session=session)))
            links_path = await asyncio.gather(*aio_task)
    elif type == 'video':
        video_url = note_data['video']['media']['stream']['h264'][0]['masterUrl']
        path = await download_video(video_url)
        # await xhs.send(Message(MessageSegment.video(path)))
        await auto_video_send(event, path, IS_LAGRANGE)
        return
    # 发送图片
    links = [MessageSegment.node_custom(user_id=int(bot.self_id), nickname=GLOBAL_NICKNAME,
                                        content=Message(MessageSegment.image(f"file://{link}"))) for link in links_path]
    # 发送异步后的数据
    if isinstance(event, GroupMessageEvent):
        await bot.send_group_forward_msg(group_id=event.group_id, messages=links)
    else:
        await bot.send_private_forward_msg(user_id=event.user_id, messages=links)
    # 清除图片
    for temp in links_path:
        os.unlink(temp)


@y2b.handle()
async def youtube(bot: Bot, event: Event):
    msg_url = re.search(
        r"(?:https?:\/\/)?(www\.)?youtube\.com\/[A-Za-z\d._?%&+\-=\/#]*|(?:https?:\/\/)?youtu\.be\/[A-Za-z\d._?%&+\-=\/#]*",
        str(event.message).strip())[0]

    title = get_video_title(msg_url, IS_OVERSEA, resolver_proxy)

    await y2b.send(Message(f"{GLOBAL_NICKNAME}识别：油管，{title}\n"))

    target_ytb_video_path = await download_ytb_video(msg_url, IS_OVERSEA, os.getcwd(), resolver_proxy)

    await auto_video_send(event, target_ytb_video_path, IS_LAGRANGE)


@freyr.handle()
async def freyrjs(bot: Bot, event: Event):
    # 过滤参数
    message = str(event.message).replace("&ls", "")
    # 匹配名字
    freyr_name = "Spotify" if "spotify" in message else "Apple Music"
    # 下载地址
    music_download_path = os.path.join(os.getcwd(), "am")
    # 执行下载命令
    result = await execute_freyr_command(message, music_download_path)
    logger.info(result.stdout.decode())
    # 获取信息
    parsed_result = await parse_freyr_log(result.stdout.decode())
    await freyr.send(
        Message(f"识别：{freyr_name}，{parsed_result['title']}--{parsed_result['artist']}\n{parsed_result['album']}"))
    # 检查目录是否存在
    music_path = os.path.join(music_download_path, parsed_result['artist'], parsed_result['album'])
    if os.path.exists(music_path):
        logger.info('目录存在。正在获取.m4a文件...')

        # 读取目录中的所有文件和文件夹
        files = os.listdir(music_path)
        # 过滤出以.m4a结尾的文件
        m4a_files = [file for file in files if os.path.splitext(file)[1].lower() == '.m4a']

        # 打印出所有.m4a文件
        logger.info('找到以下.m4a文件:')
        for file in m4a_files:
            await auto_video_send(event, os.path.join(music_path, file), IS_LAGRANGE)
    else:
        await freyr.send(Message(f"下载失败！没有找到{freyr_name}下载下来文件！"))


def auto_determine_send_type(user_id: int, task: str):
    """
        判断是视频还是图片然后发送最后删除
    :param user_id:
    :param task:
    :return:
    """
    if task.endswith("jpg") or task.endswith("png"):
        return MessageSegment.node_custom(user_id=user_id, nickname=GLOBAL_NICKNAME,
                                          content=Message(MessageSegment.image(task)))
    elif task.endswith("mp4"):
        return MessageSegment.node_custom(user_id=user_id, nickname=GLOBAL_NICKNAME,
                                          content=Message(MessageSegment.video(task)))


async def upload_data_file(bot: Bot, event: Event, data_path: str):
    """
    上传群文件
    :param bot:
    :param event:
    :param data_path:
    :return:
    """
    if isinstance(event, GroupMessageEvent):
        await upload_group_file(bot, group_id=event.group_id, file=data_path)
    elif isinstance(event, PrivateMessageEvent):
        await upload_private_file(bot, user_id=event.user_id, file=data_path)


async def upload_group_file(bot: Bot, group_id: int, file: str):
    try:
        await bot.upload_group_file(group_id=group_id, file=file, name="{:.0f}.mp4".format(time.time()))
    except (ActionFailed, NetworkError) as e:
        logger.error(e)
        if isinstance(e, ActionFailed) and e.info["wording"] == "server" \
                                                                " requires unsupported ftn upload":
            await bot.send_group_msg(group_id=group_id, message=Message(MessageSegment.text(
                "[ERROR]  文件上传失败\r\n[原因]  机器人缺少上传文件的权限\r\n[解决办法]  "
                "请将机器人设置为管理员或者允许群员上传文件")))
        elif isinstance(e, NetworkError):
            await bot.send_group_msg(group_id=group_id,
                                     message=Message(MessageSegment.text("[ERROR]文件上传失败\r\n[原因]  "
                                                                         "上传超时(一般来说还在传,建议等待五分钟)")))


async def upload_private_file(bot: Bot, user_id: int, file: str):
    try:
        await bot.upload_private_file(user_id=user_id, file=file, name="{:.0f}.mp4".format(time.time()))
    except (ActionFailed, NetworkError) as e:
        logger.error(e)
        if isinstance(e, NetworkError):
            await bot.send_private_msg(user_id=user_id, message=Message(MessageSegment.text(
                "[ERROR]  文件上传失败\r\n[原因]  上传超时(一般来说还在传,建议等待五分钟)")))


async def auto_video_send(event: Event, data_path: str, is_lagrange: bool = False):
    """
    拉格朗日自动转换成上传
    :param event:
    :param data_path:
    :param is_lagrange:
    :return:
    """
    try:
        bot: Bot = cast(Bot, current_bot.get())

        # 如果data以"http"开头，先下载视频
        if data_path.startswith("http"):
            data_path = await download_video(data_path)

        # 如果是Lagrange，则上传数据文件
        if is_lagrange:
            await upload_data_file(bot=bot, event=event, data=data_path)
        else:
            # 根据事件类型发送不同的消息
            if isinstance(event, GroupMessageEvent):
                await bot.send_group_msg(group_id=event.group_id, message=Message(MessageSegment.video(f'file://{data_path}')))
            elif isinstance(event, PrivateMessageEvent):
                await bot.send_private_msg(user_id=event.user_id, message=Message(MessageSegment.video(f'file://{data_path}')))
    except Exception as e:
        logger.error(f"下载出现错误，具体为\n{e}")
    finally:
        # 删除临时文件
        if os.path.exists(data_path):
            os.unlink(data_path)
        if os.path.exists(data_path + '.jpg'):
            os.unlink(data_path + '.jpg')