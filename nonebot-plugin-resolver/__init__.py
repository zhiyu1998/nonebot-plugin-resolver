import asyncio
import json

from nonebot import on_regex, get_driver, logger
from nonebot.adapters.onebot.v11 import Message, Event, Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent

from .common_utils import *
from .bili23_utils import getDownloadUrl, downloadBFile, mergeFileToMp4, get_dynamic
from .tiktok_utills import get_id_video, generate_x_bogus_url, generate_random_str
from .acfun_utils import parse_url, download_m3u8_videos, parse_m3u8, merge_ac_file_to_mp4
from .twitter_utils import TweepyWithProxy

# 全局配置
global_config = get_driver().config
resolver_proxy = getattr(global_config, "resolver_proxy", "http://127.0.0.1:7890")

# twitter 代理地址
proxies = {
    'http': resolver_proxy,
    'https': resolver_proxy
}
httpx_proxies = {
    "http://": resolver_proxy,
    "https://": resolver_proxy,
}

# Twitter token
client = TweepyWithProxy(
    proxies,
    getattr(global_config, "bearer_token", ""))
bili23 = on_regex(
    r"(.*)(bilibili.com|b23.tv)", priority=1
)

GLOBAL_NICKNAME = "resolver"

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
    # 处理短号问题
    if 'b23.tv' in url:
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
            await bili23.send(Message(f"R助手极速版识别：B站动态，{dynamic_desc}"))
            paths = await asyncio.gather(*dynamic_src)
            await asyncio.gather(*[bili23.send(Message(f"[CQ:image,file=file:///{path}]")) for path in paths])
            # 刪除文件
            for temp in paths:
                # logger.info(f'{temp}')
                os.unlink(temp)
        # 跳出函数
        return

    # 获取视频信息
    base_video_info = "http://api.bilibili.com/x/web-interface/view"
    video_id = re.search(r"video\/[^\?\/ ]+", url)[0].split('/')[1]
    # logger.info(video_id)
    video_title = httpx.get(
        f"{base_video_info}?bvid={video_id}" if video_id.startswith(
            "BV") else f"{base_video_info}?aid={video_id}").json()[
        'data']['title']
    video_title = delete_boring_characters(video_title)
    # video_title = re.sub(r'[\\/:*?"<>|]', "", video_title)
    await bili23.send(Message(f"R助手极速版识别：B站，{video_title}"))
    # 获取下载链接
    video_url, audio_url = getDownloadUrl(url)
    # 下载视频和音频
    path = os.getcwd() + "/" + video_title
    await asyncio.gather(
        downloadBFile(video_url, f"{path}-video.m4s", logger.info),
        downloadBFile(audio_url, f"{path}-audio.m4s", logger.info))
    mergeFileToMp4(f"{video_title}-video.m4s", f"{video_title}-audio.m4s", f"{path}-res.mp4")
    # logger.info(os.getcwd())
    # 发送出去
    # logger.info(path)
    cqs = f"[CQ:video,file=file:///{path}-res.mp4]"
    await bili23.send(Message(cqs))
    # logger.info(f'{path}-res.mp4')
    # 清理文件
    os.unlink(f"{path}-res.mp4")
    os.unlink(f"{path}-res.mp4.jpg")


"""以下为抖音/TikTok类型代码/Type code for Douyin/TikTok"""
url_type_code_dict = {
    # 抖音/Douyin
    2: 'image',
    4: 'video',
    68: 'image',
    # TikTok
    0: 'video',
    51: 'video',
    55: 'video',
    58: 'video',
    61: 'video',
    150: 'image'
}

douyin = on_regex(
    r"(.*)(v.douyin.com)", priority=1
)


@douyin.handle()
async def dy(bot: Bot, event: Event) -> None:
    """
        抖音解析
    :param event:
    :return:
    """
    # 消息
    msg: str = str(event.message).strip()
    # 正则匹配
    reg = r"(http:|https:)\/\/v.douyin.com\/[A-Za-z\d._?%&+\-=\/#]*"
    dou_url = re.search(reg, msg, re.I)[0]
    dou_url_2 = httpx.get(dou_url).headers.get('location')
    reg2 = r".*video\/(\d+)\/(.*?)"
    # 获取到ID
    dou_id = re.search(reg2, dou_url_2, re.I)[1]
    # logger.info(dou_id)
    # 一些后续要用到的参数
    headers = {
            'accept-encoding': 'gzip, deflate, br',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'referer': 'https://www.douyin.com/',
            'cookie': "s_v_web_id=verify_leytkxgn_kvO5kOmO_SdMs_4t1o_B5ml_BUqtWM1mP6BF;"
    }
    # API
    api_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?device_platform=webapp&aid=6383&channel=channel_pc_web&aweme_id={dou_id}&pc_client_type=1&version_code=190500&version_name=19.5.0&cookie_enabled=true&screen_width=1344&screen_height=756&browser_language=zh-CN&browser_platform=Win32&browser_name=Firefox&browser_version=110.0&browser_online=true&engine_name=Gecko&engine_version=109.0&os_name=Windows&os_version=10&cpu_core_num=16&device_memory=&platform=PC&webid=7158288523463362079&msToken=abL8SeUTPa9-EToD8qfC7toScSADxpg6yLh2dbNcpWHzE0bT04txM_4UwquIcRvkRb9IU8sifwgM1Kwf1Lsld81o9Irt2_yNyUbbQPSUO8EfVlZJ_78FckDFnwVBVUVK"
    api_url = generate_x_bogus_url(api_url, headers)# 如果请求失败直接返回
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers, timeout=10) as response:
            detail = await response.json()
            if detail is None:
                await douyin.send(Message(f"R助手极速版识别：抖音，解析失败！"))
                return
            # 获取信息
            detail = detail['aweme_detail']
            # 判断是图片还是视频
            url_type_code = detail['aweme_type']
            url_type = url_type_code_dict.get(url_type_code, 'video')
            await douyin.send(Message(f"R助手极速版识别：抖音，{detail.get('desc')}"))
            # 根据类型进行发送
            if url_type == 'video':
                # 识别播放地址
                player_addr = detail.get("video").get("play_addr").get("url_list")[0]
                # 发送视频
                # id = str(event.get_user_id())
                # cqs = f"[CQ:video,file={player_addr}]"
                # await douyin.send(MessageSegment.at(id)+Message(cqs))
                logger.info(player_addr)
                await douyin.send(Message(MessageSegment.video(player_addr)))
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
                                                   content=Message(f"[CQ:image,file={i['url_list'][0]}]"))
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


tik = on_regex(
    r"(.*)(www.tiktok.com)|(vt.tiktok.com)|(vm.tiktok.com)", priority=1
)


@tik.handle()
async def tiktok(event: Event) -> None:
    """
        tiktok解析
    :param event:
    :return:
    """
    # 消息
    url: str = str(event.message).strip()

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
    # strip是防止vm开头的tiktok解析出问题
    id_video = get_id_video(url).strip("/")
    logger.info(id_video)
    API_URL = f'https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aweme_id={id_video}&version_code=262&app_name=musical_ly&channel=App&device_id=null&os_version=14.4.2&device_platform=iphone&device_type=iPhone13'

    api_resp = httpx.get(API_URL, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Mobile Safari/537.36",
        "Content-Type": "application/json", "Accept-Encoding": "gzip,deflate,compress"}, proxies=httpx_proxies).json()
    data = api_resp['aweme_list'][0]
    await tik.send(Message(f"R助手极速版识别：tiktok, {data['desc']}"))
    path = await download_video_random(data['video']['play_addr']['url_list'][0])
    await tik.send(Message(f"[CQ:video,file=file:///{path}]"))
    # 清除文件
    os.unlink(f"{path}")
    os.unlink(f"{path}.jpg")


acfun = on_regex(r"(.*)(acfun.cn)")


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
    await acfun.send(Message(f"R助手极速版识别：猴山，{video_name}"))
    m3u8_full_urls, ts_names, output_folder_name, output_file_name = parse_m3u8(url_m3u8s)
    # logger.info(output_folder_name, output_file_name)
    await asyncio.gather(*[download_m3u8_videos(url, i) for i, url in enumerate(m3u8_full_urls)])
    merge_ac_file_to_mp4(ts_names, output_file_name)
    await acfun.send(Message(f"[CQ:video,file=file:///{os.getcwd()}/{output_file_name}]"))
    os.unlink(output_file_name)
    os.unlink(output_file_name + ".jpg")


twit = on_regex(
    r"(.*)(twitter.com)", priority=1
)


@twit.handle()
async def twitter(bot:Bot, event: Event):
    """
        推特解析
    :param event:
    :return:
    """
    msg: str = str(event.message).strip()
    reg = r"https?:\/\/twitter.com\/[0-9-a-zA-Z_]{1,20}\/status\/([0-9]*)"
    id = re.search(reg, msg)[1]

    tweet = client.get_tweet(id=id,
                             media_fields="duration_ms,height,media_key,preview_image_url,public_metrics,type,url,width,alt_text,variants".split(
                                 ","),
                             expansions=[
                                 'entities.mentions.username',
                                 'attachments.media_keys',
                             ])
    await twit.send(Message(f"R助手极速版识别：小蓝鸟学习版，{tweet.data.text}"))
    # logger.info(tweet)
    # 主要内容
    tweet_json = tweet.includes
    aio_task = []
    # 逐个判断是照片还是视频
    # logger.info(tweet_json)
    for tweet_single in tweet_json['media']:
        # 图片
        if tweet_single['type'] == "photo":
            # logger.info(tweet_single.url)
            aio_task.append(download_img_with_proxy(tweet_single.url))
            # await twit.send(Message(f"[CQ:image,file=file:///{path}]"))
            # os.unlink(f"{path}")
        # 视频
        elif tweet_single['type'] == "video":
            # logger.info(tweet_single['variants'][0]['url'])
            aio_task.append(download_video_with_proxy(tweet_single['variants'][0]['url']))
            # logger.info(path)
            # await twit.send(Message(f"[CQ:video,file=file:///{path}]"))
            # os.unlink(f"{path}")
    path_res = await asyncio.gather(*aio_task)
    aio_task_res = [how_to_send_msg(int(bot.self_id), path) for path in path_res]

    # 发送异步后的数据
    if isinstance(event, GroupMessageEvent):
        await bot.send_group_forward_msg(group_id=event.group_id, messages=aio_task_res)
    else:
        await bot.send_private_forward_msg(user_id=event.user_id, messages=aio_task_res)

    # 清除垃圾
    for path in path_res:
        os.unlink(path)


xhs = on_regex(
    r"(.*)(xhslink.com|xiaohongshu.com)", priority=1
)


@xhs.handle()
async def redbook(bot:Bot, event: Event):
    """
        小红书解析
    :param event:
    :return:
    """
    msg_url = re.search(r"(http:|https:)\/\/(xhslink|xiaohongshu).com\/[A-Za-z\d._?%&+\-=\/#@]*",
                       str(event.message).strip())[0]
    # 请求头
    headers = {
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1 Edg/110.0.0.0",
        "cookie": "xhsTrackerId=7388abf6-2408-4e9a-8152-140ea8f5149f; xhsTrackerId.sig=Tpe1NCZ_pwRAXtm5IRfTK4Ie13LAhfn6cYScxV-IalE; a1=1866d900346b66jir33pjqgc03ropmfs02us1uchx10000135053; webId=f13d8bdb8bdc7da43646085bcc45045a; gid=yYKKfj88K082yYKKfj88qJ7S4KDKKV3FqqUV7xCAkS8qFMy8lU6iMy888yq282q8f2Y4S02J; gid.sign=bZspQsILDRcyjFKBcv/QLYXdSyo=; web_session=030037a4c042b15e5c1889508b244ad113e053; xhsTracker=url=noteDetail&xhsshare=WeixinSession; xhsTracker.sig=c7fp5QrY6HcoTDaS9n_cwgdBDxv0VfZzRSSSryslneA; extra_exp_ids=h5_2302011_origin,h5_1208_clt,h5_1130_clt,ios_wx_launch_open_app_exp,h5_video_ui_exp3,wx_launch_open_app_duration_origin,ques_clt2; extra_exp_ids.sig=CUGkGsXOyAfjUIy2Tj7J3xbdMjA_JzhGRdagzqYdnbg; webBuild=1.1.21; xsecappid=xhs-pc-web; websectiga=59d3ef1e60c4aa37a7df3c23467bd46d7f1da0b1918cf335ee7f2e9e52ac04cf; sec_poison_id=1249155d-9e9e-4392-8658-505c74a53135"
    }
    if "xhslink" in msg_url:
        msg_url = httpx.get(msg_url, headers=headers, follow_redirects=True).url
        msg_url = str(msg_url)
    video_id = re.search(r'/explore/(\w+)', msg_url) or re.search(r'/discovery/item/(\w+)', msg_url)
    video_id = video_id[1]

    html = httpx.get(f'https://www.xiaohongshu.com/discovery/item/{video_id}', headers=headers).text
    response_json = re.findall('window.__INITIAL_STATE__=(.*?)</script>', html)[0]
    response_json = re.sub(r'(\\u[a-zA-Z0-9]{4})', lambda x: x.group(1).encode("utf-8").decode("unicode-escape"),
                           response_json)
    response_json = json.loads(response_json)
    note_data = response_json['noteData']['data']['noteData']
    type = note_data['type']
    aio_task = []
    note_title = note_data['title']
    note_desc = note_data['desc']
    await xhs.send(Message(
        f"R助手极速版识别：小红书，{note_title}\n{note_desc}"))

    if type == 'normal':
        image_list = note_data['imageList']
        for i in range(len(image_list)):
            image_url = 'https:' + image_list[i]['url']
            aio_task.append(download_img(image_url, f'{os.getcwd()}/{str(i)}.jpg'))
    elif type == 'video':
        video_url = note_data['video']['url']
        path = await download_video_random(video_url)
        await tik.send(Message(f"[CQ:video,file=file:///{path}]"))
        os.unlink(path)
        return
    # 批量下载
    links_path = await asyncio.gather(*aio_task)
    # 发送图片
    links = [MessageSegment.node_custom(user_id=int(bot.self_id), nickname=GLOBAL_NICKNAME,
                                           content=Message(MessageSegment.image(f"file:///{link}"))) for link in links_path]
    # 发送异步后的数据
    if isinstance(event, GroupMessageEvent):
        await bot.send_group_forward_msg(group_id=event.group_id, messages=links)
    else:
        await bot.send_private_forward_msg(user_id=event.user_id, messages=links)
    # 清除图片
    for temp in links_path:
        os.unlink(temp)


def how_to_send_msg(user_id:int, task: str):
    """
        判断是视频还是图片然后发送最后删除
    :param user_id:
    :param task:
    :return:
    """
    if task.endswith("jpg") or task.endswith("png"):
        logger.info(f"file:///{task}]")
        return MessageSegment.node_custom(user_id=user_id, nickname=GLOBAL_NICKNAME,
                                   content=Message(MessageSegment.image(f"file:///{task}")))
    elif task.endswith("mp4"):
        return MessageSegment.node_custom(user_id=user_id, nickname=GLOBAL_NICKNAME,
                                          content=Message(MessageSegment.video(f"file:///{task}")))