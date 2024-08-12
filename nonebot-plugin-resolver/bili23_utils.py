import httpx
import subprocess

from nonebot import logger

header = {
    'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
    'referer': 'https://www.bilibili.com',
}

async def download_b_file(url, full_file_name, progress_callback):
    """
        下载视频文件和音频文件
    :param url:
    :param full_file_name:
    :param progress_callback:
    :return:
    """
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url, headers=header) as resp:
            current_len = 0
            total_len = int(resp.headers['content-length'])
            print(total_len)
            with open(full_file_name, "wb") as f:
                async for chunk in resp.aiter_bytes():
                    current_len += len(chunk)
                    f.write(chunk)
                    progress_callback(f'下载进度：{round(current_len / total_len, 2)}')


def merge_file_to_mp4(v_full_file_name: str, a_full_file_name: str, output_file_name: str):
    """
        合并视频文件和音频文件
    :param v_full_file_name:
    :param a_full_file_name:
    :param output_file_name:
    :return:
    """
    logger.info(f'正在合并：{[output_file_name]}')
    # 调用ffmpeg
    subprocess.call(f'ffmpeg -y -i "{v_full_file_name}" -i "{a_full_file_name}" -c copy "{output_file_name}"',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    )

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
