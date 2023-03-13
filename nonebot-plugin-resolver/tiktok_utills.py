import httpx
import json
import time
import requests
from urllib.parse import urlencode, unquote, parse_qsl

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


def generate_ttwid() -> str:
    """生成请求必带的ttwid
    param :None
    return:ttwid
    """
    url = 'https://ttwid.bytedance.com/ttwid/union/register/'
    data = '{"region":"cn","aid":1768,"needFid":false,"service":"www.ixigua.com","migrate_info":{"ticket":"","source":"node"},"cbUrlProtocol":"https","union":true}'
    r = httpx.post(url, data=data)
    return r.cookies['ttwid']


def getXbogus(url):
    headers = {
        "cookie": None,
        "referer": "https://www.douyin.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
    }
    response = {}
    try:
        if isinstance(url, dict):
            params = eval(unquote(url, 'utf-8'))
            url = urlencode(params, safe="=")
            response = json.loads(requests.post(
                'http://47.115.200.238/xg/dict/?params=' + url,
                headers=headers).text)
        if isinstance(url, str):
            url = url.replace('&', '%26')
            response = json.loads(requests.post(
                'http://47.115.200.238/xg/path?url=' + url,
                headers=headers, timeout=5).text)
        else:
            print('[  提示  ]:传入的参数有误')
    except Exception as e:
        print('[  错误  ]:%s' % e)
    params = response["result"][0]["paramsencode"]
    xb = response["result"][0]["X-Bogus"]["0"]
    # print('[  调试  ]:%s' % self.params)
    return (params, xb)
