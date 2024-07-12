import subprocess

def get_video_title(url, is_oversea, my_proxy=None):
    # 构建命令
    command = ["yt-dlp", "--get-title", url]
    if not is_oversea and my_proxy:
        command += ["--proxy", my_proxy]

    # 执行命令并捕获输出
    result = subprocess.run(command, capture_output=True, text=True)

    # 检查是否有错误
    if result.returncode != 0:
        print("Error:", result.stderr)
        return None

    # 返回输出结果（视频标题）
    return result.stdout.strip()


async def download_ytb_video(url, is_oversea, path, my_proxy=None, video_type='youtube'):
    # 构建命令
    command = []
    if video_type == 'youtube':
        command = ["yt-dlp", "-P", path, "-o", "temp.%(ext)s", "-f", "best[height<=720][ext=mp4]",
                   "--merge-output-format",
                   "mp4", url]
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