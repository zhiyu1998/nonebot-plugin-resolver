import yt_dlp, asyncio

from nonebot import logger

async def get_video_title(url: str, is_oversea: bool, my_proxy=None, video_type='youtube') -> str:
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'force_generic_extractor': True,
    }
    if not is_oversea and my_proxy:
        ydl_opts['proxy'] = my_proxy
    if video_type == 'youtube':
        ydl_opts['cookiefile'] = 'ytb_cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = await asyncio.to_thread(ydl.extract_info, url, download=False)
            return info_dict.get('title', '-')
    except Exception as e:
        logger.error(f"Error: {e}")
        return '-'

async def download_ytb_video(url, is_oversea, path, my_proxy=None, video_type='youtube'):
    ydl_opts = {
        'outtmpl': f'{path}/temp.%(ext)s',
        'merge_output_format': 'mp4',
    }
    if video_type == 'youtube':
        ydl_opts['cookiefile'] = 'ytb_cookies.txt'
        if not 'shorts' in url:
            ydl_opts['format'] = 'bv*[width=1280][height=720]+ba'
    if not is_oversea and my_proxy:
        ydl_opts['proxy'] = my_proxy

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])
        return f"{path}/temp.mp4"
    except Exception as e:
        print(f"Error: {e}")
        return None


  