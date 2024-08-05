<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
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

```
nb plugin install nonebot-plugin-resolver
```

2. 使用 pip 安装和更新，初次安装需要手动添加入口

```
pip install --upgrade nonebot-plugin-resolver
```
3. 【必要】安装必要组件 FFmpeg
```shell
# ubuntu
sudo apt-get install ffmpeg
# 其他linux参考（群友推荐）：https://gitee.com/baihu433/ffmpeg
# Windows 参考：https://www.jianshu.com/p/5015a477de3c
```
4. 【可选】安装`am`&`Spotify`解析必要的依赖
```shell
npm install -g freyr
# 或者你有yarn的话可以使用
yarn global add freyr
# 接着安装它的依赖
apt-get install atomicparsley
```
5. 【可选】安装`TK`&`YB`解析必要依赖 不建议直接使用`apt`不是最新版
```shell
# debian 海外
curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o ~/.local/bin/yt-dlp
chmod a+rx ~/.local/bin/yt-dlp
# debian 国内
curl -L https://ghproxy.net/https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o ~/.local/bin/yt-dlp
chmod a+rx ~/.local/bin/yt-dlp

# 将/home/YtDlpHome/yt-dlp添加到环境变量（下面二选一）
vim ~/.bashrc  # 如果你使用 bash
vim ~/.zshrc   # 如果你使用 zsh
# 添加到最后一行
export PATH="/home/YtDlpHome:$PATH"

# 刷新环境变量即可
source ~/.bashrc  # 如果你使用 bash
source ~/.zshrc   # 如果你使用 zsh
```
## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的可选配置

```
XHS_CK='' #xhs cookie
DOUYIN_CK='' # douyin's cookie, 格式：odin_tt=xxx;passport_fe_beating_status=xxx;sid_guard=xxx;uid_tt=xxx;uid_tt_ss=xxx;sid_tt=xxx;sessionid=xxx;sessionid_ss=xxx;sid_ucp_v1=xxx;ssid_ucp_v1=xxx;passport_assist_user=xxx;ttwid=xxx;
IS_OVERSEA=False # 是否是海外服务器部署
IS_LAGRANGE=False # 是否是拉格朗日（https://github.com/KonataDev/Lagrange.Core）
RESOLVER_PROXY = "http://127.0.0.1:7890" # 代理
R_GLOBAL_NICKNAME = "R插件极速版" # 解析前缀名
```

## 🤳🏿 在线观看如何获取 Cookie

> 由群友 `@麦满分` 提供

https://github.com/user-attachments/assets/7ead6d62-a36c-4e8d-bb5d-6666749dfb26

## 🤺 交流群

<img src="./img/group.JPG" width="30%" height="30%">

## 🎉 使用 & 效果图
<img src="./img/example.webp" width="50%" height="50%">
<img src="./img/example2.webp" width="50%" height="50%">
<img src="./img/example3.webp" width="50%" height="50%">
<img src="./img/example4.webp" width="50%" height="50%">
<img src="./img/example5.webp" width="50%" height="50%">

## 贡献

同时感谢以下开发者对 `Nonebot - R插件` 作出的贡献：

<a href="https://github.com/zhiyu1998/nonebot-plugin-resolver/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=zhiyu1998/nonebot-plugin-resolver&max=1000" />
</a>
