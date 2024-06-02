import re
import os
import subprocess


async def parse_freyr_log(log):
    title_match = re.search(r'Title: (.*)', log)
    album_match = re.search(r'Album: (.*)', log)
    artist_match = re.search(r'Artist: (.*)', log)

    title = title_match.group(1) if title_match else 'N/A'
    album = album_match.group(1) if album_match else 'N/A'
    artist = artist_match.group(1) if artist_match else 'N/A'

    return {'title': title, 'album': album, 'artist': artist}

async def execute_freyr_command(music_link: str, music_save_path: str):
    # 找到R插件保存目录
    current_working_directory = os.path.abspath(music_save_path)
    # 如果没有文件夹就创建一个
    os.makedirs(os.path.join(current_working_directory), exist_ok=True)
    # 执行命令
    return subprocess.run(['freyr', '-d', os.path.join(current_working_directory), 'get', music_link],
                            capture_output=True)