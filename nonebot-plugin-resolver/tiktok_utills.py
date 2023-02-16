def get_id_video(url: str) -> str:
    """
        获取tiktok的视频id
    :param url:
    :return:
    """
    if "/video/" not in url:
        return ""

    id_video = url[url.index("/video/") + 7 :len(url)]
    return id_video[:id_video.index("?")] if len(id_video) > 19 else id_video
