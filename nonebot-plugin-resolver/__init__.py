import asyncio
import functools
import os
import re

import httpx
import json

from bs4 import BeautifulSoup

from nonebot import on_regex, get_driver
from nonebot.adapters.onebot.v11 import Message, Event, Bot, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent

from .common_utils import *
from .bili23_utils import getDownloadUrl, downloadBFile, mergeFileToMp4, get_dynamic
from .tiktok_utills import get_id_video, get_douyin_json
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
                # print(f'{temp}')
                os.unlink(temp)
        # 跳出函数
        return

    # 获取视频信息
    base_video_info = "http://api.bilibili.com/x/web-interface/view"
    video_id = re.search(r"video\/[^\?\/ ]+", url)[0].split('/')[1]
    # print(video_id)
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
        downloadBFile(video_url, f"{path}-video.m4s", print),
        downloadBFile(audio_url, f"{path}-audio.m4s", print))
    mergeFileToMp4(f"{video_title}-video.m4s", f"{video_title}-audio.m4s", f"{path}-res.mp4")
    # print(os.getcwd())
    # 发送出去
    # print(path)
    cqs = f"[CQ:video,file=file:///{path}-res.mp4]"
    await bili23.send(Message(cqs))
    # print(f'{path}-res.mp4')
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
    # print(dou_id)
    # 请求抖音
    detail = get_douyin_json(dou_id)
    if detail is None:
        await douyin.send(Message(f"R助手极速版识别：抖音，解析失败！"))
        return
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
        cqs = f"[CQ:video,file={player_addr}]"
        # await douyin.send(MessageSegment.at(id)+Message(cqs))
        await douyin.send(Message(cqs))
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
        # print(no_watermark_image_list)
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
        # print(url)
    else:
        url = re.search(url_reg, url)[0]
    # strip是防止vm开头的tiktok解析出问题
    id_video = get_id_video(url).strip("/")
    print(id_video)
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
    # print(output_folder_name, output_file_name)
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
    # print(tweet)
    # 主要内容
    tweet_json = tweet.includes
    aio_task = []
    # 逐个判断是照片还是视频
    # print(tweet_json)
    for tweet_single in tweet_json['media']:
        # 图片
        if tweet_single['type'] == "photo":
            # print(tweet_single.url)
            aio_task.append(download_img_with_proxy(tweet_single.url))
            # await twit.send(Message(f"[CQ:image,file=file:///{path}]"))
            # os.unlink(f"{path}")
        # 视频
        elif tweet_single['type'] == "video":
            # print(tweet_single['variants'][0]['url'])
            aio_task.append(download_video_with_proxy(tweet_single['variants'][0]['url']))
            # print(path)
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
    msgUrl = re.search(r"(http:|https:)\/\/(xhslink|xiaohongshu).com\/[A-Za-z\d._?%&+\-=\/#@]*",
                       str(event.message).strip())
    url = f"https://dlpanda.com/zh-CN/xhs?url={msgUrl}"

    resp = httpx.get(url, headers={
        "User-Agent":
            "Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Mobile Safari/537.36",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip,deflate,compress"
    })
    soup = BeautifulSoup(resp.text, 'lxml')
    urls = soup.findAll("img", attrs={"style": "max-width: none; max-height: none;"})
    title = soup.findAll("h5")
    desc = soup.findAll("p")
    # print(title)
    # print(desc[2])
    # urls: list[str] = re.findall(r'<img(.*)src="\/\/ci\.xiaohongshu\.com(.*?)"', resp.text)
    # title_desc = re.findall(r'<a href="https:\/\/www\.xiaohongshu\.com\/discovery\/item\/(.*)<\/p>', resp.text)
    await xhs.send(Message(
        f"R助手极速版识别：小红书，{''.join([str(tit.string) for tit in title[:2]])}" + "\n" + f"{str(desc[2].string)}"))

    aio_task = []
    for u in urls:
        # print(u.get("src"))
        link = f'https:{u.get("src")}'
        aio_task.append(download_img(link, os.getcwd() + "/" + re.search(r"com\/(.*)\?", link)[1] + ".jpg"))
    links_path: tuple[str] = await asyncio.gather(*aio_task)
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
        print(f"file:///{task}]")
        return MessageSegment.node_custom(user_id=user_id, nickname=GLOBAL_NICKNAME,
                                   content=Message(MessageSegment.image(f"file:///{task}")))
    elif task.endswith("mp4"):
        return MessageSegment.node_custom(user_id=user_id, nickname=GLOBAL_NICKNAME,
                                          content=Message(MessageSegment.video(f"file:///{task}")))