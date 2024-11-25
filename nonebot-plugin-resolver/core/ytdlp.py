import subprocess
from nonebot import logger


def get_video_title(url: str, is_oversea: bool, my_proxy=None) -> str:
    # 构建命令
    command = ["yt-dlp", "--get-title", url]
    if not is_oversea and my_proxy:
        command += ["--proxy", my_proxy]
    if "youtube" in url:
      command.insert(1, "--cookies")
      command.insert(2, "ytb_cookies.txt")
    # 执行命令并捕获输出
    result = subprocess.run(command, capture_output=True, text=True) #, encoding='utf-8'

    # 检查是否有错误
    if result.returncode != 0:
        logger.error("Error:", result.stderr)
        return '-'

    # 返回输出结果（视频标题）
    if result.stdout is None:
        return '-'
    return result.stdout.strip()


async def download_ytb_video(url, is_oversea, path, my_proxy=None, video_type='youtube'):
    # 构建命令
    command = []
    if video_type == 'youtube':
        command = ["yt-dlp", "--cookies", "ytb_cookies.txt", "-P", path, "-o", "temp.%(ext)s", "--merge-output-format", "mp4", url]
    elif video_type == 'tiktok':
        command = ["yt-dlp", "-P", path, "-o", "temp.%(ext)s", url]

    if not is_oversea and my_proxy:
        command.insert(1, "--proxy")
        command.insert(2, my_proxy)

    # 执行命令
    result = subprocess.run(command, capture_output=True, text=True)

    # 检查是否有错误
    if result.returncode != 0:
        print("Error:", result.stderr)
        return None

    # 成功下载
    return path + "/" + "temp.mp4"
  