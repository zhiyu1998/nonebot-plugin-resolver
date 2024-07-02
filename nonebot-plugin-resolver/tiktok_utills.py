import httpx
import json
import time
import random
import execjs
import urllib.parse
import os
from nonebot import logger

header = {
    'User-Agent': "Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36 Edg/87.0.664.66"
}


def get_id_video(url: str) -> str:
    """
        获取tiktok的视频id
    :param url:
    :return:
    """
    if "/video/" not in url:
        return ""

    id_video = url[url.index("/video/") + 7:len(url)]
    return id_video[:id_video.index("?")] if len(id_video) > 19 else id_video


def get_douyin_json(dou_id: str):
    """
        解析出抖音链接
    :param dou_id:
    :return:
    """
    url = f'https://www.iesdouyin.com/aweme/v1/web/aweme/detail/?aweme_id={dou_id}&aid=1128&version_name=23.5.0&device_platform=android&os_version=2333&Github=Evil0ctal&words=FXXK_U_ByteDance'
    retries = 3
    backoff_factor = 1
    with httpx.Client(transport=httpx.HTTPTransport(retries=3)) as client:
        for i in range(retries):
            try:
                response = client.get(url, headers=header, timeout=10)
                response.raise_for_status()
                return json.loads(response.content)["aweme_detail"]
            except httpx.HTTPError:
                if i == retries - 1:
                    raise
                else:
                    time.sleep(backoff_factor * (i + 1))

def generate_x_bogus_url(url, headers):
    """
            生成抖音X-Bogus签名
            :param url: 视频链接
            :return: 包含X-Bogus签名的URL
            """
    # 调用JavaScript函数
    query = urllib.parse.urlparse(url).query
    abogus_file_path = f'{os.path.dirname(os.path.abspath(__file__))}/a-bogus.js'
    with open(abogus_file_path, 'r', encoding='utf-8') as abogus_file:
        abogus_file_path_transcoding = abogus_file.read()
    abogus = execjs.compile(abogus_file_path_transcoding).call('generate_a_bogus', query, headers['User-Agent'])
    # logger.info('生成的A-Bogus签名为: {}'.format(abogus))
    return url + "&a_bogus=" + abogus

def generate_random_str(self, randomlength=16):
    """
    根据传入长度产生随机字符串
    param :randomlength
    return:random_str
    """
    random_str = ''
    base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789='
    length = len(base_str) - 1
    for _ in range(randomlength):
        random_str += base_str[random.randint(0, length)]
    return random_str