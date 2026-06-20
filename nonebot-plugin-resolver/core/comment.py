import os
import json
import urllib.parse
import execjs
import httpx
import aiohttp
import asyncio
import time
import random
from PIL import Image, ImageSequence
import io
import re
from nonebot import logger
from typing import List, Dict, Any
from nonebot.adapters.onebot.v11 import Message, MessageSegment

# 动态尝试引入 html_to_pic
try:
    from nonebot_plugin_htmlrender import html_to_pic

    HTML_RENDER_AVAILABLE = True
except ImportError:
    HTML_RENDER_AVAILABLE = False
    logger.warning("[Comment] 未检测到 nonebot_plugin_htmlrender，图片模式将失效并自动降级为文字模式")

from .tiktok import generate_x_bogus_url

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "douyin-comment.html")
BILI_TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "bilibili-comment.html")
COMMENT_TEMPLATE_CACHE = None
BILI_TEMPLATE_CACHE = None

# ==================== 1. HTML 模板定义 ====================

# 抖音自适应主题模板 (默认 dark，通过 html.light 覆盖白天模式)
DEFAULT_HTML_TEMPLATE = """<!DOCTYPE html>
<html class="{{theme_class}}">
<head>
    <meta charset="utf-8">
    <style>
        :root {
            --bg-color: #161823;
            --text-color: #f1f1f1;
            --border-color: #2f303c;
            --username-color: rgba(255, 255, 255, 0.7);
            --meta-color: rgba(255, 255, 255, 0.4);
            --reply-border: #2f303c;
            --reply-text-color: #e1e1e1;
            --reply-user-color: rgba(255, 255, 255, 0.6);
        }
        html.light {
            --bg-color: #ffffff;
            --text-color: #18191c;
            --border-color: #e3e8ec;
            --username-color: rgba(0, 0, 0, 0.7);
            --meta-color: rgba(0, 0, 0, 0.4);
            --reply-border: #e3e8ec;
            --reply-text-color: #333333;
            --reply-user-color: rgba(0, 0, 0, 0.6);
        }
        body { margin: 0; padding: 30px; background-color: var(--bg-color); color: var(--text-color); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; width: 750px; }
        .container { background-color: var(--bg-color); border-radius: 12px; }
        .header { font-size: 20px; font-weight: bold; margin-bottom: 25px; border-bottom: 1px solid var(--border-color); padding-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
        .header .title { max-width: 500px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .comment-item { display: flex; margin-bottom: 24px; }
        .avatar { width: 48px; height: 48px; border-radius: 50%; margin-right: 14px; object-fit: cover; }
        .comment-body { flex: 1; }
        .username { font-size: 14px; color: var(--username-color); font-weight: 600; margin-bottom: 4px; display: inline-flex; align-items: center; gap: 6px; }
        .badge-author { background-color: #ff2c55; color: #ffffff; font-size: 11px; font-weight: bold; padding: 2px 6px; border-radius: 4px; margin-left: 6px; display: inline-block; line-height: 1.2; }
        .comment-text { font-size: 15px; line-height: 1.5; color: var(--text-color); margin-bottom: 8px; word-break: break-all; }
        .comment-image { max-width: 240px; max-height: 240px; border-radius: 8px; margin-top: 8px; display: block; object-fit: contain; border: 1px solid var(--border-color); }
        .comment-sticker { max-width: 120px; max-height: 120px; margin-top: 8px; display: block; object-fit: contain; }
        .comment-footer { display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: var(--meta-color); margin-top: 6px; }
        .footer-left { display: flex; align-items: center; gap: 8px; }
        .footer-right { display: flex; align-items: center; gap: 4px; color: var(--meta-color); }
        .heart-icon { color: #ff2c55; font-size: 14px; }
        .replies { margin-top: 12px; padding-left: 12px; border-left: 2px solid var(--reply-border); }
        .reply-item { display: flex; margin-top: 12px; }
        .reply-avatar { width: 28px; height: 28px; border-radius: 50%; margin-right: 10px; object-fit: cover; }
        .reply-body { flex: 1; }
        .reply-username { font-size: 13px; color: var(--reply-user-color); font-weight: 600; margin-bottom: 2px; display: inline-flex; align-items: center; gap: 6px; }
        .reply-text { font-size: 14px; color: var(--reply-text-color); line-height: 1.4; word-break: break-all; }
        .reply-footer { font-size: 11px; color: var(--meta-color); margin-top: 4px; display: flex; gap: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="title">💬 《{{title}}》热门评论</span>
            <span style="font-size: 14px; color: var(--meta-color);">共 {{total_comments}} 条</span>
        </div>
        <div class="comments-list">
            {{comments}}
        </div>
    </div>
</body>
</html>
"""

# B站自适应主题模板 (默认 light，通过 html.dark 覆盖暗黑模式)
DEFAULT_BILI_HTML_TEMPLATE = """<!DOCTYPE html>
<html class="{{theme_class}}">
<head>
    <meta charset="utf-8">
    <style>
        :root {
            --bg-color: #ffffff;
            --text-color: #18191c;
            --border-color: #e3e8ec;
            --item-border-color: #f1f2f3;
            --reply-bg: #f1f2f3;
            --username-color: #61666d;
            --meta-color: #9499a0;
        }
        html.dark {
            --bg-color: #18191c;
            --text-color: #f1f1f1;
            --border-color: #2f303c;
            --item-border-color: #2f303c;
            --reply-bg: #21232c;
            --username-color: #9499a0;
            --meta-color: rgba(255, 255, 255, 0.4);
        }
        body { margin: 0; padding: 30px; background-color: var(--bg-color); color: var(--text-color); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; width: 750px; }
        .container { background-color: var(--bg-color); border-radius: 12px; }
        .header { font-size: 20px; font-weight: bold; margin-bottom: 25px; border-bottom: 1px solid var(--border-color); padding-bottom: 15px; color: var(--text-color); display: flex; justify-content: space-between; align-items: center; }
        .comment-item { display: flex; margin-bottom: 24px; border-bottom: 1px solid var(--item-border-color); padding-bottom: 20px; }
        .avatar { width: 48px; height: 48px; border-radius: 50%; margin-right: 14px; object-fit: cover; }
        .comment-body { flex: 1; }
        .username { font-size: 13px; color: var(--username-color); font-weight: bold; margin-bottom: 6px; display: inline-flex; align-items: center; gap: 6px; }
        .username.is-up { color: #ff6699; }
        .level-badge { font-size: 9px; color: #ffffff; font-weight: bold; padding: 1px 4px; border-radius: 2px; }
        .up-badge { border: 1px solid #ff6699; color: #ff6699; font-size: 10px; padding: 1px 4px; border-radius: 3px; font-weight: bold; line-height: 1; }
        .comment-text { font-size: 15px; line-height: 1.6; color: var(--text-color); margin-bottom: 8px; word-break: break-all; }
        .comment-images { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; margin-bottom: 8px; }
        .comment-image { max-width: 200px; max-height: 200px; border-radius: 4px; object-fit: cover; }
        .comment-emojis { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
        .comment-emoji { width: 32px; height: 32px; object-fit: contain; }
        .comment-emoji-inline { width: 22px; height: 22px; vertical-align: middle; margin: 0 3px; display: inline-block; }
        .comment-footer { display: flex; font-size: 13px; color: var(--meta-color); gap: 15px; margin-top: 8px; }
        .footer-item { display: flex; align-items: center; gap: 4px; }
        .replies { margin-top: 12px; background-color: var(--reply-bg); border-radius: 8px; padding: 12px; }
        .reply-item { display: flex; margin-bottom: 12px; }
        .reply-item:last-child { margin-bottom: 0; }
        .reply-avatar { width: 24px; height: 24px; border-radius: 50%; margin-right: 10px; object-fit: cover; }
        .reply-body { flex: 1; }
        .reply-username { font-size: 12px; color: var(--username-color); font-weight: bold; margin-bottom: 2px; display: inline-flex; align-items: center; gap: 4px; }
        .reply-username.is-up { color: #ff6699; }
        .reply-text { font-size: 13.5px; color: var(--text-color); line-height: 1.5; word-break: break-all; }
        .reply-footer { font-size: 11px; color: var(--meta-color); margin-top: 4px; display: flex; gap: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span>💬 《{{title}}》热门评论</span>
            <span style="font-size: 14px; color: var(--meta-color);">共 {{total_comments}} 条</span>
        </div>
        <div class="comments-list">
            {{comments}}
        </div>
    </div>
</body>
</html>
"""


def load_template(force_reload=False) -> str:
    """载入并缓存抖音模板 (若存在0字节、旧版、破损模板将自动复原修复)"""
    global COMMENT_TEMPLATE_CACHE
    if not force_reload and COMMENT_TEMPLATE_CACHE is not None:
        return COMMENT_TEMPLATE_CACHE
    if not os.path.exists(TEMPLATE_DIR):
        os.makedirs(TEMPLATE_DIR)

    # 自动识别空模板与旧版本模板 (无昼夜切换 class 属性的模板) 强制重写
    need_reset = False
    if not os.path.exists(TEMPLATE_PATH) or os.path.getsize(TEMPLATE_PATH) == 0:
        need_reset = True
    else:
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        if "{{theme_class}}" not in content:
            need_reset = True

    if need_reset:
        with open(TEMPLATE_PATH, "w", encoding="utf-8") as f:
            f.write(DEFAULT_HTML_TEMPLATE)
        COMMENT_TEMPLATE_CACHE = DEFAULT_HTML_TEMPLATE
    else:
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            COMMENT_TEMPLATE_CACHE = f.read()
    return COMMENT_TEMPLATE_CACHE


def load_bili_template(force_reload=False) -> str:
    """载入并缓存B站模板 (若存在0字节、旧版、破损模板将自动复原修复)"""
    global BILI_TEMPLATE_CACHE
    if not force_reload and BILI_TEMPLATE_CACHE is not None:
        return BILI_TEMPLATE_CACHE
    if not os.path.exists(TEMPLATE_DIR):
        os.makedirs(TEMPLATE_DIR)

    # 自动识别空模板与旧版本模板强制重写
    need_reset = False
    if not os.path.exists(BILI_TEMPLATE_PATH) or os.path.getsize(BILI_TEMPLATE_PATH) == 0:
        need_reset = True
    else:
        with open(BILI_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        if "{{theme_class}}" not in content:
            need_reset = True

    if need_reset:
        with open(BILI_TEMPLATE_PATH, "w", encoding="utf-8") as f:
            f.write(DEFAULT_BILI_HTML_TEMPLATE)
        BILI_TEMPLATE_CACHE = DEFAULT_BILI_HTML_TEMPLATE
    else:
        with open(BILI_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            BILI_TEMPLATE_CACHE = f.read()
    return BILI_TEMPLATE_CACHE


# ==================== 2. 公共工具 ====================

def get_theme_class() -> str:
    """根据当前服务器时钟判定昼夜主题模式 (晚上8点到早上8点为 dark 护眼模式，其余时间为 light 明亮模式)"""
    current_hour = time.localtime().tm_hour
    return "dark" if (current_hour >= 20 or current_hour < 8) else "light"


def format_comment_time(timestamp: int) -> str:
    if not timestamp: return ""
    now = int(time.time())
    diff = now - timestamp
    if diff < 60:
        return "刚刚"
    elif diff < 3600:
        return f"{diff // 60}分钟前"
    elif diff < 86400:
        return f"{diff // 3600}小时前"
    elif diff < 2592000:
        return f"{diff // 86400}天前"
    else:
        return time.strftime("%m-%d", time.localtime(timestamp))


def escape_html(text: str) -> str:
    if not text: return ""
    return text.replace("&", "&amp;") \
        .replace("<", "&lt;") \
        .replace(">", "&gt;") \
        .replace('"', "&quot;") \
        .replace("'", "&#039;")


def get_level_color(level: int) -> str:
    if level >= 6:
        return '#ff0000'
    elif level >= 5:
        return '#ff8c00'
    elif level >= 4:
        return '#ffd700'
    elif level >= 3:
        return '#32cd32'
    elif level >= 2:
        return '#00bfff'
    return '#9499a0'


# ==================== 3. 抖音评论模块 ====================

async def download_and_convert_comment_img(session: aiohttp.ClientSession, url: str) -> bytes:
    if not url: return None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    if "douyinpic.com" in url:
        headers.pop("Referer", None)

    try:
        async with session.get(url, headers=headers, timeout=10) as resp:
            if resp.status != 200:
                return None
            data = await resp.read()
            img = Image.open(io.BytesIO(data))
            is_animated = getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1

            output = io.BytesIO()
            if is_animated:
                frames = []
                for frame in ImageSequence.Iterator(img):
                    f_rgba = frame.convert("RGBA")
                    f_p = f_rgba.convert("P", palette=Image.Palette.ADAPTIVE)
                    frames.append(f_p)
                duration = img.info.get('duration', 100) or 100
                frames[0].save(
                    output,
                    format='GIF',
                    save_all=True,
                    append_images=frames[1:],
                    loop=0,
                    duration=duration,
                    disposition=2
                )
            else:
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    alpha = img.convert('RGBA')
                    background = Image.new('RGB', alpha.size, (255, 255, 255))
                    background.paste(alpha, mask=alpha.split()[3])
                    img = background
                else:
                    img = img.convert('RGB')
                img.save(output, format='JPEG', quality=90)

            return output.getvalue()
    except Exception as e:
        logger.debug(f"[Comment] 评论多媒体转换异常: {e}")
        return None


async def get_douyin_comments(session: aiohttp.ClientSession, aweme_id: str, headers: dict,
                              author_sec_uid: str = None) -> List[Dict[str, Any]]:
    try:
        msToken = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789=_", k=107))
        params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "aweme_id": aweme_id,
            "cursor": "0",
            "count": "10",
            "item_type": "0",
            "pc_client_type": "1",
            "version_code": "170400",
            "version_name": "17.4.0",
            "msToken": msToken
        }
        query_str = urllib.parse.urlencode(params)
        final_api_url = generate_x_bogus_url(f"https://www.douyin.com/aweme/v1/web/comment/list/?{query_str}", headers)
        if not final_api_url:
            return []

        async with session.get(final_api_url, headers=headers) as resp:
            text_data = await resp.text()
            if not text_data.strip():
                return []

            data = json.loads(text_data)
            comments = data.get("comments") or []
            parsed_comments = []

            for c in comments:
                user = c.get("user", {})
                user_sec_uid = user.get("sec_uid")
                target_author_sec_uid = author_sec_uid or c.get("author_sec_uid")
                is_author = bool(user_sec_uid and target_author_sec_uid and user_sec_uid == target_author_sec_uid)

                # 配图
                c_image = ""
                image_list = c.get("image_list") or []
                if image_list:
                    img_node = image_list[0]
                    origin_urls = img_node.get("origin_url", {}).get("url_list") or []
                    fallback_urls = img_node.get("url", {}).get("url_list") or []
                    c_image = (origin_urls[0] if origin_urls else "") or \
                              (fallback_urls[0] if fallback_urls else "") or \
                              img_node.get("uri", "")

                # 大表情
                c_sticker = ""
                sticker_node = c.get("sticker") or {}
                if sticker_node:
                    animate_urls = sticker_node.get("animate_url", {}).get("url_list") or []
                    if animate_urls:
                        c_sticker = animate_urls[0]

                # 高亮 @艾特
                content = c.get("text", "")
                text_extra = c.get("text_extra") or []
                mentions = set()
                for extra in text_extra:
                    start = extra.get("start")
                    end = extra.get("end")
                    if start is not None and end is not None:
                        mention_text = content[start:end]
                        if mention_text.startswith("@"):
                            mentions.add(mention_text)

                content_html = escape_html(content).replace("\n", "<br>")
                for at in mentions:
                    escaped_at = escape_html(at)
                    content_html = content_html.replace(
                        escaped_at,
                        f'<span style="color:#ff2c55;font-weight:600;">{escaped_at}</span>'
                    )

                # 子评论
                replies = c.get("reply_comment") or []
                parsed_replies = []
                for r in replies[:3]:
                    r_user = r.get("user", {})
                    r_user_sec_uid = r_user.get("sec_uid")
                    r_is_author = bool(
                        r_user_sec_uid and target_author_sec_uid and r_user_sec_uid == target_author_sec_uid)

                    r_content = r.get("text", "")
                    r_extra = r.get("text_extra") or []
                    r_mentions = set()
                    for rextra in r_extra:
                        rs = rextra.get("start")
                        re_ = rextra.get("end")
                        if rs is not None and re_ is not None:
                            r_at = r_content[rs:re_]
                            if r_at.startswith("@"): r_mentions.add(r_at)

                    r_content_html = escape_html(r_content).replace("\n", "<br>")
                    for r_at in r_mentions:
                        r_escaped_at = escape_html(r_at)
                        r_content_html = r_content_html.replace(
                            r_escaped_at,
                            f'<span style="color:#ff2c55;font-weight:600;">{r_escaped_at}</span>'
                        )

                    # 增加子评论头像的安全提取判定
                    r_avatar_list = r_user.get("avatar_thumb", {}).get("url_list")
                    r_avatar = r_avatar_list[0] if r_avatar_list else ""

                    parsed_replies.append({
                        "username": r_user.get("nickname", "未知"),
                        "avatar": r_avatar,  # 使用安全过滤后的变量
                        "content": r_content_html,
                        "like": r.get("digg_count", 0),
                        "time": format_comment_time(r.get("create_time", 0)),
                        "is_author": r_is_author
                    })

                # 增加空列表判断，防止 avatar_thumb 存在但 url_list 为空列表时触发 IndexError
                avatar_list = user.get("avatar_thumb", {}).get("url_list")
                avatar = avatar_list[0] if avatar_list else ""

                parsed_comments.append({
                    "username": user.get("nickname", "未知"),
                    "avatar": avatar,
                    "content": content_html,
                    "like": c.get("digg_count", 0),
                    "time": format_comment_time(c.get("create_time", 0)),
                    "location": c.get("ip_location", ""),
                    "image": c_image,
                    "sticker": c_sticker,
                    "image_bytes": None,
                    "sticker_bytes": None,
                    "is_author": is_author,
                    "replies": parsed_replies
                })

            # 异步并发转码
            async def process_media_bytes(item):
                tasks = []
                if item["image"]:
                    tasks.append(download_and_convert_comment_img(session, item["image"]))
                else:
                    tasks.append(asyncio.sleep(0, result=None))

                if item["sticker"]:
                    tasks.append(download_and_convert_comment_img(session, item["sticker"]))
                else:
                    tasks.append(asyncio.sleep(0, result=None))

                img_res, stk_res = await asyncio.gather(*tasks)
                item["image_bytes"] = img_res
                item["sticker_bytes"] = stk_res

            if parsed_comments:
                await asyncio.gather(*[process_media_bytes(item) for item in parsed_comments])

            return parsed_comments
    except Exception as e:
        logger.error(f"[Comment] 获取评论 API 失败: {e}")
        return []


def build_comments_html(comments: list) -> str:
    """生成抖音评论列表的 HTML 块"""
    html_parts = []
    default_avatar = "https://p3.douyinpic.com/aweme/100x100/default-avatar.png"
    for item in comments:
        avatar = item.get("avatar") or default_avatar
        username = item.get("username", "未知")
        content = item.get("content", "")
        like = item.get("like", 0)
        time_str = item.get("time", "")
        location = item.get("location", "")
        is_author = item.get("is_author", False)

        author_badge = '<span class="badge-author">作者</span>' if is_author else ""

        media_html = ""
        image = item.get("image")
        sticker = item.get("sticker")
        if image:
            media_html += f'<img class="comment-image" src="{image}" />'
        if sticker:
            media_html += f'<img class="comment-sticker" src="{sticker}" />'

        replies_html = ""
        replies = item.get("replies") or []
        if replies:
            r_parts = []
            for r in replies:
                r_avatar = r.get("avatar") or default_avatar
                r_username = r.get("username", "未知")
                r_content = r.get("content", "")
                r_like = r.get("like", 0)
                r_time = r.get("time", "")
                r_is_author = r.get("is_author", False)

                r_author_badge = '<span class="badge-author" style="font-size: 9px; padding: 1px 4px; margin-left: 4px;">作者</span>' if r_is_author else ""
                r_like_str = f"🤍 {r_like}" if r_like > 0 else ""
                r_parts.append(f"""
                <div class="reply-item">
                    <img class="reply-avatar" src="{r_avatar}" />
                    <div class="reply-body">
                        <div class="reply-username">{r_username}{r_author_badge}</div>
                        <div class="reply-text">{r_content}</div>
                        <div class="reply-footer">
                            <span>{r_time}</span>
                            <span>{r_like_str}</span>
                        </div>
                    </div>
                </div>
                """)
            replies_html = f'<div class="replies">{"".join(r_parts)}</div>'

        loc_str = f" • {location}" if location else ""

        html_parts.append(f"""
        <div class="comment-item">
            <img class="avatar" src="{avatar}" />
            <div class="comment-body">
                <div class="username">{username}{author_badge}</div>
                <div class="comment-text">{content}</div>
                {media_html}
                <div class="comment-footer">
                    <div class="footer-left">
                        <span>{time_str}{loc_str}</span>
                    </div>
                    <div class="footer-right">
                        <span class="heart-icon">🤍</span>
                        <span>{like}</span>
                    </div>
                </div>
                {replies_html}
            </div>
        </div>
        """)
    return "".join(html_parts)


async def render_comments_image(comments: list, title: str) -> bytes:
    """抖音评论图渲染 (自适应模式切换 + 视口自适应缩短)"""
    if not HTML_RENDER_AVAILABLE:
        raise ImportError("nonebot_plugin_htmlrender 不可用")
    template = load_template()
    if not template or not template.strip():
        template = DEFAULT_HTML_TEMPLATE
    comments_html = build_comments_html(comments)

    # 动态判定注入昼夜主题 CSS 类
    theme_class = get_theme_class()
    final_html = template.replace("{{theme_class}}", theme_class) \
        .replace("{{title}}", title) \
        .replace("{{total_comments}}", str(len(comments))) \
        .replace("{{comments}}", comments_html)

    # 通过将初始视口高度设置为 100px 并配合 full_page，使 Playwright 智能截取元素滚动上限，自适应长度
    return await html_to_pic(final_html, viewport={"width": 810, "height": 100})


# ==================== 4. 哔哩哔哩评论模块 ====================

async def get_bilibili_comments(session: aiohttp.ClientSession, aid: int, sessdata: str, bvid: str = None,
                                up_mid: int = None) -> List[Dict[str, Any]]:
    """
    抓取并解析哔哩哔哩评论
    """
    try:
        url = "https://api.bilibili.com/x/v2/reply/main"
        params = {
            "oid": str(aid),
            "type": "1",
            "mode": "3",  # 热评模式
            "ps": "10",  # 抓取10条
            "pn": "1"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": f"https://www.bilibili.com/video/{bvid or ('av' + str(aid))}"
        }
        if sessdata:
            headers["Cookie"] = f"SESSDATA={sessdata}"

        async with session.get(url, params=params, headers=headers, timeout=10) as resp:
            data = await resp.json()
            if data.get("code") != 0:
                logger.warning(f"[Comment] B站评论 API 报错: {data.get('message')}")
                return []

            replies = data.get("data", {}).get("replies") or []
            parsed_comments = []

            for item in replies:
                member = item.get("member", {})
                content_node = item.get("content", {})

                commenter_mid = member.get("mid")
                is_up = bool(commenter_mid and up_mid and int(commenter_mid) == int(up_mid))

                # 评论内置图片
                images = []
                pictures = content_node.get("pictures") or []
                for p in pictures:
                    img_url = p.get("img_src") or p.get("url")
                    if img_url:
                        images.append(img_url.replace("http:", "https:"))

                # 评论内置表情并缓存到映射字典
                emojis = []
                emote_map = {}
                emote = content_node.get("emote") or {}
                if emote:
                    for key, val in emote.items():
                        e_url = val.get("url") or val.get("gif_url")
                        e_text = val.get("text") or key
                        if e_url:
                            url_https = e_url.replace("http:", "https:")
                            emojis.append(url_https)
                            emote_map[e_text] = url_https

                # 二级回复
                sub_replies = item.get("replies") or []
                parsed_replies = []
                for r in sub_replies[:3]:
                    r_member = r.get("member", {})
                    r_content_node = r.get("content", {})
                    r_mid = r_member.get("mid")
                    r_is_up = bool(r_mid and up_mid and int(r_mid) == int(up_mid))

                    r_emojis = []
                    r_emote_map = {}
                    r_emote = r_content_node.get("emote") or {}
                    if r_emote:
                        for k, v in r_emote.items():
                            re_url = v.get("url") or v.get("gif_url")
                            re_text = v.get("text") or k
                            if re_url:
                                url_https = re_url.replace("http:", "https:")
                                r_emojis.append(url_https)
                                r_emote_map[re_text] = url_https

                    parsed_replies.append({
                        "username": r_member.get("uname", "未知"),
                        "avatar": r_member.get("avatar", "").replace("http:", "https:"),
                        "content": escape_html(r_content_node.get("message", "")).replace("\n", "<br>"),
                        "like": r.get("like", 0),
                        "time": format_comment_time(r.get("ctime", 0)),
                        "is_up": r_is_up,
                        "emojis": r_emojis,
                        "emote_map": r_emote_map
                    })

                level = member.get("level_info", {}).get("current_level", 0)

                parsed_comments.append({
                    "username": member.get("uname", "未知"),
                    "avatar": member.get("avatar", "").replace("http:", "https:"),
                    "content": escape_html(content_node.get("message", "")).replace("\n", "<br>"),
                    "like": item.get("like", 0),
                    "time": format_comment_time(item.get("ctime", 0)),
                    "images": images,
                    "emojis": emojis,
                    "emote_map": emote_map,
                    "level": level,
                    "is_up": is_up,
                    "image_bytes": [],  # 预留用于文字模式合并转发转码
                    "emoji_bytes": [],
                    "replies": parsed_replies
                })

            # 高并发转换B站的多媒体表情和评论大图 (防 PC 裂图)
            async def process_bili_media_bytes(item):
                img_tasks = [download_and_convert_comment_img(session, url) for url in item["images"]]
                emo_tasks = [download_and_convert_comment_img(session, url) for url in item["emojis"]]

                img_results = await asyncio.gather(*img_tasks) if img_tasks else []
                emo_results = await asyncio.gather(*emo_tasks) if emo_tasks else []

                item["image_bytes"] = [b for b in img_results if b is not None]
                item["emoji_bytes"] = [b for b in emo_results if b is not None]

            if parsed_comments:
                await asyncio.gather(*[process_bili_media_bytes(item) for item in parsed_comments])

            return parsed_comments
    except Exception as e:
        logger.error(f"[Comment] 获取B站评论 API 失败: {e}")
        return []


def build_bili_comments_html(comments: list) -> str:
    """生成B站评论列表的 HTML 块 (支持表情符号占位符行内精准替换，移除下方赘余展示)"""
    html_parts = []
    default_avatar = "https://i0.hdslb.com/bfs/face/moface.jpg"
    for item in comments:
        avatar = item.get("avatar") or default_avatar
        username = item.get("username", "未知")
        content = item.get("content", "")
        like = item.get("like", 0)
        time_str = item.get("time", "")
        level = item.get("level", 0)
        is_up = item.get("is_up", False)

        username_class = "username is-up" if is_up else "username"
        badges = ""
        if level > 0:
            color = get_level_color(level)
            badges += f'<span class="level-badge" style="background-color: {color}">LV{level}</span>'
        if is_up:
            badges += '<span class="up-badge">UP</span>'

        # 精准替换行内表情占位符并赋予其 CSS 样式 (保留 inline styling 避免本地老模板缓存导致白排版)
        emote_map = item.get("emote_map") or {}
        for placeholder, url in emote_map.items():
            content = content.replace(
                placeholder,
                f'<img class="comment-emoji-inline" src="{url}" style="width: 22px; height: 22px; vertical-align: middle; margin: 0 3px; display: inline-block;" />'
            )

        # 仅保留用户上传的自定义大图，评论内置的表情图已移至行内
        media_html = ""
        images = item.get("images") or []
        if images:
            img_html = "".join([f'<img class="comment-image" src="{img}" />' for img in images])
            media_html += f'<div class="comment-images">{img_html}</div>'

        replies_html = ""
        replies = item.get("replies") or []
        if replies:
            r_parts = []
            for r in replies:
                r_avatar = r.get("avatar") or default_avatar
                r_username = r.get("username", "未知")
                r_content = r.get("content", "")
                r_like = r.get("like", 0)
                r_time = r.get("time", "")
                r_is_up = r.get("is_up", False)

                r_username_class = "reply-username is-up" if r_is_up else "reply-username"
                r_up_badge = ' <span class="up-badge">UP</span>' if r_is_up else ""

                # 替换二级回复里的表情
                r_emote_map = r.get("emote_map") or {}
                for r_placeholder, r_url in r_emote_map.items():
                    r_content = r_content.replace(
                        r_placeholder,
                        f'<img class="comment-emoji-inline" src="{r_url}" style="width: 22px; height: 22px; vertical-align: middle; margin: 0 3px; display: inline-block;" />'
                    )

                r_like_str = f"🤍 {r_like}" if r_like > 0 else ""
                r_parts.append(f"""
                <div class="reply-item">
                    <img class="reply-avatar" src="{r_avatar}" />
                    <div class="reply-body">
                        <div class="reply-username {r_username_class}">{r_username}{r_up_badge}</div>
                        <div class="reply-text">{r_content}</div>
                        <div class="reply-footer">
                            <span>{r_time}</span>
                            <span>{r_like_str}</span>
                        </div>
                    </div>
                </div>
                """)
            replies_html = f'<div class="replies">{"".join(r_parts)}</div>'

        html_parts.append(f"""
        <div class="comment-item">
            <img class="avatar" src="{avatar}" />
            <div class="comment-body">
                <div class="{username_class}">{username}{badges}</div>
                <div class="comment-text">{content}</div>
                {media_html}
                <div class="comment-footer">
                    <span class="footer-item">👍 {like}</span>
                    <span class="footer-item">🕐 {time_str}</span>
                </div>
                {replies_html}
            </div>
        </div>
        """)
    return "".join(html_parts)


async def render_bili_comments_image(comments: list, title: str) -> bytes:
    """B站评论图渲染 (自适应模式切换 + 视口自适应缩短)"""
    if not HTML_RENDER_AVAILABLE:
        raise ImportError("nonebot_plugin_htmlrender 不可用")
    template = load_bili_template()
    # 终极防护：如果是空字符串或读失败，直接使用内存默认模板防止生成白图
    if not template or not template.strip():
        template = DEFAULT_BILI_HTML_TEMPLATE
    comments_html = build_bili_comments_html(comments)

    # 动态判定注入昼夜主题 CSS 类
    theme_class = get_theme_class()
    final_html = template.replace("{{theme_class}}", theme_class) \
        .replace("{{title}}", title) \
        .replace("{{total_comments}}", str(len(comments))) \
        .replace("{{comments}}", comments_html) \
        .replace("{{page_indicator}}", "")

    # 通过将初始视口高度设置为 100px 并配合 full_page，使 Playwright 智能截取元素实际最大滚动长度，自适应长度
    return await html_to_pic(final_html, viewport={"width": 810, "height": 100})


def format_bili_comments_to_nodes(bot_id, comments: list, title: str, nickname: str) -> list:
    """B站评论区合并转发封装 (数据级多媒体字节流推送，解决裂图与静止)"""
    nodes = []
    nodes.append(MessageSegment.node_custom(
        user_id=bot_id,
        nickname=nickname,
        content=Message(f"💬 《{title}》 热门评论")
    ))
    for c in comments:
        raw_text = re.sub(r'<br\s*/?>', '\n', c['content'])
        raw_text = re.sub(r'<[^>]+>', '', raw_text)

        up_tag = " (UP主)" if c.get("is_up") else ""
        text_line = f"👤 {c['username']}{up_tag} (LV{c['level']} | 👍{c['like']})：\n{raw_text}"

        if c.get("time"):
            text_line += f"\n🕐 {c['time']}"

        replies = c.get("replies") or []
        if replies:
            text_line += "\n\n  --- 回复 ---"
            for r in replies:
                clean_r_content = re.sub(r'<[^>]+>', '', r['content'])
                r_up_tag = " (UP主)" if r.get("is_up") else ""
                text_line += f"\n  💬 {r['username']}{r_up_tag}: {clean_r_content}"

        node_msg = Message(MessageSegment.text(text_line))

        if c.get("image_bytes"):
            for b in c["image_bytes"]: node_msg.append(MessageSegment.image(b))
        elif c.get("images"):
            for img in c["images"]: node_msg.append(MessageSegment.image(img))

        if c.get("emoji_bytes"):
            for b in c["emoji_bytes"]: node_msg.append(MessageSegment.image(b))
        elif c.get("emojis"):
            for emo in c["emojis"]: node_msg.append(MessageSegment.image(emo))

        nodes.append(MessageSegment.node_custom(
            user_id=bot_id,
            nickname=nickname,
            content=node_msg
        ))
    return nodes


def format_comments_to_nodes(bot_id, comments: List[Dict[str, Any]], title: str, nickname: str) -> list:
    """
    格式化为文字合并转发包 (包含真实图片与表情 bytes 字节，自适应动静图)
    """
    nodes = []

    # 1. 头部卡片
    nodes.append(MessageSegment.node_custom(
        user_id=bot_id,
        nickname=nickname,
        content=Message(f"💬 《{title}》 热门评论")
    ))

    # 2. 逐条解析
    for c in comments:
        # 去除 HTML 的 <br> 并替换回普通文本
        raw_text = re.sub(r'<br\s*/?>', '\n', c['content'])
        raw_text = re.sub(r'<[^>]+>', '', raw_text)  # 移除艾特高亮的 span

        author_tag = " (作者)" if c.get("is_author") else ""
        text_line = f"👤 {c['username']}{author_tag} (👍{c['like']})：\n{raw_text}"

        # 组装时间与属地
        text_footer = []
        if c.get("location"):
            text_footer.append(f"📍 {c['location']}")
        if c.get("time"):
            text_footer.append(f"🕐 {c['time']}")

        if text_footer:
            text_line += f"\n({' | '.join(text_footer)})"

        # 组装回复
        replies = c.get("replies") or []
        if replies:
            text_line += "\n\n  --- 回复 ---"
            for r in replies:
                clean_r_content = re.sub(r'<[^>]+>', '', r['content'])
                r_author_tag = " (作者)" if r.get("is_author") else ""
                text_line += f"\n  💬 {r['username']}{r_author_tag}: {clean_r_content}"

        # 组装混合消息
        node_msg = Message(MessageSegment.text(text_line))

        # 动静态多媒体字节流推送，解决 PC 裂图与静止问题
        if c.get("image_bytes"):
            node_msg.append(MessageSegment.image(c["image_bytes"]))
        elif c.get("image"):
            node_msg.append(MessageSegment.image(c["image"]))

        if c.get("sticker_bytes"):
            node_msg.append(MessageSegment.image(c["sticker_bytes"]))
        elif c.get("sticker"):
            node_msg.append(MessageSegment.image(c["sticker"]))

        # 封包
        nodes.append(
            MessageSegment.node_custom(
                user_id=bot_id,
                nickname=nickname,
                content=node_msg
            )
        )
    return nodes
