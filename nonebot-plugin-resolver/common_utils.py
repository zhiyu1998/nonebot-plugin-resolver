import aiohttp
import httpx
import random
import os
import re
import time

# twitter 代理地址
proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
}

# httpx 代理地址格式
httpx_proxies = {
    "http://": "http://127.0.0.1:7890",
    "https://": "http://127.0.0.1:7890",
}
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36'}


async def download_video_random(url):
    """
        异步下载视频
    :param url:
    :return:
    """
    # 获取文件名
    path = os.getcwd() + "/" + f"{str(random.randint(1, 100))}.mp4"
    # 下载文件
    async with httpx.AsyncClient(proxies=httpx_proxies) as client2:
        async with client2.stream("GET", url, headers=header) as resp:
            with open(path, "wb") as f:
                async for chunk in resp.aiter_bytes():
                    f.write(chunk)
    return path

async def download_video_with_proxy(url):
    """
        异步下载视频
    :param url:
    :return:
    """
    # 获取文件名
    path = os.getcwd() + "/" + f"{str(random.randint(1, 100))}.mp4"
    # 下载文件
    async with httpx.AsyncClient(proxies=httpx_proxies) as client2:
        async with client2.stream("GET", url, headers=header) as resp:
            with open(path, "wb") as f:
                async for chunk in resp.aiter_bytes():
                    f.write(chunk)
    return path

async def download_img(url: str, path='') -> str:
    """
        异步下载网络图片（eg. https://pbs.twimg.com/media/FoQVwyxacAEIRdS.jpg）
    :param path:
    :param url:
    :return:
    """
    if path == '':
        path = os.getcwd() + "/" + url.split('/').pop()
    # print(path)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.read()
                with open(path, 'wb') as f:
                    f.write(data)
    return path

async def download_img_with_proxy(url: str) -> str:
    """
        异步下载网络图片（eg. https://pbs.twimg.com/media/FoQVwyxacAEIRdS.jpg）
    :param url:
    :return:
    """
    path = os.getcwd() + "/" + url.split('/').pop()
    # print(path)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxies.get("http")) as response:
            if response.status == 200:
                data = await response.read()
                with open(path, 'wb') as f:
                    f.write(data)
    return path

def delete_boring_characters(sentence):
    """
        去除标题的特殊字符
    :param sentence:
    :return:
    """
    return re.sub('[0-9’!"∀〃#$%&\'()*+,-./:;<=>?@，。?★、…【】《》？“”‘’！[\\]^_`{|}~～\s]+', "", sentence)