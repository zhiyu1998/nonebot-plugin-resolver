import httpx
import re
import json
import subprocess
import os

from .common_utils import download_img

header = {
    'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    'referer': 'https://www.bilibili.com',
}


def getDownloadUrl(url: str):
    """
        爬取下载链接
    :param url:
    :return:
    """
    with httpx.Client(follow_redirects=True) as client:
        resp = client.get(url, headers=header)
        info = re.search(r"<script>window\.__playinfo__=({.*})<\/script><script>", resp.text)[1]
        res = json.loads(info)
        videoUrl = res["data"]["dash"]["video"][0]["baseUrl"] or res["data"]["dash"]["video"][0]["backupUrl"][0]
        audioUrl = res["data"]["dash"]["audio"][0]["baseUrl"] or res["data"]["dash"]["audio"][0]["backupUrl"][0]
        if videoUrl != "" and audioUrl != "":
            return videoUrl, audioUrl


async def downloadBFile(url, fullFileName, progressCallback):
    """
        下载视频文件和音频文件
    :param url:
    :param fullFileName:
    :param progressCallback:
    :return:
    """
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url, headers=header) as resp:
            currentLen = 0
            totalLen = int(resp.headers['content-length'])
            print(totalLen)
            with open(fullFileName, "wb") as f:
                async for chunk in resp.aiter_bytes():
                    currentLen += len(chunk)
                    f.write(chunk)
                    progressCallback(currentLen / totalLen)


def mergeFileToMp4(vFullFileName: str, aFullFileName: str, outputFileName: str, shouldDelete=True):
    """
        合并视频文件和音频文件
    :param vFullFileName:
    :param aFullFileName:
    :param outputFileName:
    :param shouldDelete:
    :return:
    """
    # 调用ffmpeg
    subprocess.call(f'ffmpeg -y -i "{vFullFileName}" -i "{aFullFileName}" -c copy "{outputFileName}"', shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    )
    # 删除临时文件
    if shouldDelete:
        os.unlink(vFullFileName)
        os.unlink(aFullFileName)


def get_dynamic(dynamic_id: str):
    """
        获取哔哩哔哩动态
    :param dynamic_id:
    :return:
    """
    dynamic_api = f'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail?dynamic_id={dynamic_id}'
    resp = httpx.get(dynamic_api, headers=header)

    dynamic_json = json.loads(resp.content)['data']['card']
    card = json.loads(dynamic_json['card'])
    dynamic_origin = card['item']

    dynamic_desc = dynamic_origin['description']
    dynamic_src = []
    for pic in dynamic_origin['pictures']:
        dynamic_src.append(download_img(pic['img_src']))

    return dynamic_desc, dynamic_src


def extra_bili_info(video_info):
    """
        格式化视频信息
    """
    video_state = video_info['stat']
    video_like, video_coin, video_favorite, video_share, video_view, video_danmaku, video_reply = video_state['like'], \
        video_state['coin'], video_state['favorite'], video_state['share'], video_state['view'], video_state['danmaku'], \
        video_state['reply']

    video_data_map = {
        "点赞": video_like,
        "硬币": video_coin,
        "收藏": video_favorite,
        "分享": video_share,
        "总播放量": video_view,
        "弹幕数量": video_danmaku,
        "评论": video_reply
    }

    video_info_result = ""
    for key, value in video_data_map.items():
        if int(value) > 10000:
            formatted_value = f"{value / 10000:.1f}万"
        else:
            formatted_value = value
        video_info_result += f"{key}: {formatted_value} | "

    return video_info_result