import httpx
import json
import time

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