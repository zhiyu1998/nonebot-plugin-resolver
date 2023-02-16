<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-resolver

_✨ NoneBot2 解析视频链接/小程序插件 ✨_


<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/owner/nonebot-plugin-example.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-example">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-example.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">

</div>

## 📖 介绍

这是一个 nonebot2 插件，解析视频链接/小程序插件，发送 tiktok、bilibili、twitter等可以让QQ发送响应的图片、视频

## 💿 安装

<details>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-resolver

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-resolver
</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-resolver
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-resolver
</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-resolver
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot-plugin-resolver"]

</details>

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

```
# twitter的token和本地代理
bearer_token = ""
resolver_proxy = "http://127.0.0.1:7890"
```

## 🎉 使用 & 效果图
![help](./img/example.png)
![help](./img/example2.png)
![help](./img/example3.png)
![help](./img/example4.png)
![help](./img/example5.png)

