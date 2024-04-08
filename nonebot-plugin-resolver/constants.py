"""
哔哩哔哩视频信息链接
"""
BILI_VIDEO_INFO = "https://api.bilibili.com/x/web-interface/view"

"""
dy视频信息
"""
DOUYIN_VIDEO = "https://www.douyin.com/aweme/v1/web/aweme/detail/?device_platform=webapp&aid=6383&channel=channel_pc_web&aweme_id={}&pc_client_type=1&version_code=190500&version_name=19.5.0&cookie_enabled=true&screen_width=1344&screen_height=756&browser_language=zh-CN&browser_platform=Win32&browser_name=Firefox&browser_version=118.0&browser_online=true&engine_name=Gecko&engine_version=109.0&os_name=Windows&os_version=10&cpu_core_num=16&device_memory=&platform=PC"

"""
tiktok视频信息
"""
TIKTOK_VIDEO = "https://api22-normal-c-alisg.tiktokv.com/aweme/v1/feed/"

"""
通用解析
"""
GENERAL_REQ_LINK = "http://47.99.158.118/video-crack/v2/parse?content={}"

"""
小红书下载链接
"""
XHS_REQ_LINK = "https://www.xiaohongshu.com/explore/"

"""以下为抖音/TikTok类型代码/Type code for Douyin/TikTok"""
URL_TYPE_CODE_DICT = {
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