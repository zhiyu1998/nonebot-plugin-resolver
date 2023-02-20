import httpx
import json

from typing import Union

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


def get_douyin_json(dou_id: str) -> Union[dict, None]:
    """
        解析出抖音链接
    :param dou_id:
    :return:
    """
    url = f'https://www.iesdouyin.com/aweme/v1/web/aweme/detail/?aweme_id={dou_id}&aid=1128&version_name=23.5.0&device_platform=android&os_version=2333&Github=Evil0ctal&words=FXXK_U_ByteDance'
    try:
        resp = httpx.get(url, headers=header, timeout=10)
        resp_json = json.loads(resp.content)
        return resp_json["aweme_detail"]
    except Exception as e:
        print(f"抖音解析错误：{e}")
        return None
