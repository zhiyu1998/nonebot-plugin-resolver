<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://s2.loli.net/2024/08/13/ZlwxWz3Sh2i1bNU.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-resolver

_✨ NoneBot2 链接分享解析器插件 ✨_


<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/owner/nonebot-plugin-resolver.svg" alt="license">
</a>
<a href="https://pypi.org/project/nonebot-plugin-resolver">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-resolver.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">

</div>

## 📖 介绍

适用于NoneBot2的解析视频、图片链接/小程序插件，tiktok、bilibili、twitter等实时发送！
## 💿 安装

1. 使用 nb-cli 安装，不需要手动添加入口，更新使用 pip

```sh
nb plugin install nonebot-plugin-resolver
```

2. 使用 pip 安装和更新，初次安装需要手动添加入口

```sh
pip install --upgrade nonebot-plugin-resolver
```
3. 🚀【高级 / 进阶 / 推荐】使用脚本进行安装，**优点就是及时更新** | ⚠️在可以执行`nb run`那个目录执行即可

```shell
curl -fsSL https://raw.gitmirror.com/zhiyu1998/nonebot-plugin-resolver/master/npr_install.sh > npr_install.sh && chmod 755 npr_install.sh && ./npr_install.sh
```

4. 【必要】安装必要组件 FFmpeg

```shell
# ubuntu
sudo apt-get install ffmpeg
# 其他linux参考（群友推荐）：https://gitee.com/baihu433/ffmpeg
# Windows 参考：https://www.jianshu.com/p/5015a477de3c
```
> [!IMPORTANT]
> 推荐两个ffmpeg全编译版本：
> - https://github.com/yt-dlp/FFmpeg-Builds
> - https://github.com/BtbN/FFmpeg-Builds

5. 抖音解析需要 JavaScript Runtime
```shell
sudo apt-get install nodejs
```
## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的可选配置

```
r_xhs_ck=''                      # 小红书 cookie
r_douyin_ck=''                   # douyin's cookie, 格式：odin_tt=xxx;passport_fe_beating_status=xxx;sid_guard=xxx;uid_tt=xxx;uid_tt_ss=xxx;sid_tt=xxx;sessionid=xxx;sessionid_ss=xxx;sid_ucp_v1=xxx;ssid_ucp_v1=xxx;passport_assist_user=xxx;ttwid=xxx;
r_bili_ck= ''                    # bilibili cookie, 必须含有 SESSDATA 项 填写后可附加: 总结
r_ytb_ck=''                      # youtube cookie, youtube 视频因人机检测下载失败，可填写
r_is_oversea=False               # 海外服务器部署，使用了透明代理，设置为 True
r_proxy='http://127.0.0.1:7890'  # 代理 r_is_oversea=False 时生效
r_video_duration_maximum=480     # 视频最大解析长度，默认480s为8分钟，计算公式为480s/60s=8mins
r_black_resolvers=[]             # 全局禁止的解析，示例 GLOBAL_RESOLVE_CONTROLLER=["bilibili", "douyin"] 表示禁止了哔哩哔哩和抖 bilibili,douyin,tiktok,acfun,twitter,xhs,ytb.ncm,kugou,weibo,kugou

## 🕹️ 开启 & 关闭解析

使用以下命令可以控制对当前群是否开启/关闭解析：
```shell
@机器人 开启解析
@机器人 关闭解析
查看关闭解析
```

## 🤳🏿 在线观看如何获取 Cookie

> 由群友 `@麦满分` 提供

https://github.com/user-attachments/assets/7ead6d62-a36c-4e8d-bb5d-6666749dfb26


## 🎉 使用 & 效果图
<img src="https://s2.loli.net/2024/08/12/l8ISa1Gv76OHuML.webp" width="50%" height="50%">
<img src="https://s2.loli.net/2024/08/12/Ojlh6Nr9SiRmvuB.webp" width="50%" height="50%">
<img src="https://s2.loli.net/2024/08/12/MF4xyhESYZBzcwL.webp" width="50%" height="50%">
<img src="https://s2.loli.net/2024/08/12/nDpB6Y9yHvmtKjU.webp" width="50%" height="50%">
<img src="https://s2.loli.net/2024/08/12/I5VWuASNFTmakw1.webp" width="50%" height="50%">

## 开发 && 发版

发版 Action:
```shell
git tag <tag_name>

git push origin --tags
```

## 贡献

同时感谢以下开发者对 `Nonebot - R插件` 作出的贡献：

<a href="https://github.com/zhiyu1998/nonebot-plugin-resolver/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=zhiyu1998/nonebot-plugin-resolver&max=1000" />
</a>
