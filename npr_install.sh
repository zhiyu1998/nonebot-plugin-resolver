#!/bin/bash

# 检查src目录是否存在
if [ -d "src" ]; then
    cd src
    # 检查src下的plugins目录是否存在
    if [ ! -d "plugins" ]; then
        echo "src目录下没有plugins目录，检查当前目录..."
        cd ..
        if [ ! -d "plugins" ]; then
            echo "当前目录下也没有plugins目录，脚本结束。"
            exit 1
        else
            echo "在当前目录下找到plugins目录。"
        fi
    else
        echo "在src目录下找到plugins目录。"
    fi
else
    echo "当前目录下没有src目录，检查是否有plugins目录..."
    if [ ! -d "plugins" ]; then
        echo "当前目录下也没有plugins目录，脚本结束。"
        exit 1
    fi
fi

# 进入plugins目录
cd plugins

# 检查并删除已存在的nonebot-plugin-resolver文件夹
if [ -d "nonebot-plugin-resolver" ]; then
    echo "[nonebot-plugin-resolver] 存在已存在的nonebot-plugin-resolver文件夹，正在删除..."
    rm -rf nonebot-plugin-resolver
fi

# 使用git clone下载指定的GitHub仓库
echo "[nonebot-plugin-resolver] 开始克隆GitHub仓库..."
git clone https://githubfast.com/zhiyu1998/nonebot-plugin-resolver.git

# 进入下载的仓库文件夹
cd nonebot-plugin-resolver

# 删除除了nonebot-plugin-resolver文件夹以外的所有文件
echo "[nonebot-plugin-resolver] 删除不需要的文件..."
find . -maxdepth 1 ! -name 'nonebot-plugin-resolver' -type f -exec rm -f {} +

# 将nonebot-plugin-resolver文件夹中的内容移动到当前目录
echo "[nonebot-plugin-resolver] 移动文件..."
mv nonebot-plugin-resolver/* ./
rmdir nonebot-plugin-resolver

# 返回之前的目录
cd ..

echo "[nonebot-plugin-resolver] 安装完成，请使用nb run启动Nonebot!"
