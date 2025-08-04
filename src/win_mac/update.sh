#!/bin/bash

set -e
set -u

echo "正在执行 OpenChat 更新操作..."

# ---------------- 杀掉后台进程 ----------------
echo "正在终止后台进程..."

if pgrep -f "/MacOS/OpenChat" >/dev/null; then
    echo "杀掉 OpenChat"
    pkill -f "/MacOS/OpenChat" || true
else
    echo "OpenChat 未运行"
fi

if pgrep -f "/MacOS/Ollama" >/dev/null; then
    echo "杀掉 Ollama"
    pkill -f "/MacOS/Ollama" || true
else
    echo "Ollama 未运行"
fi

sleep 5

# ---------------- 准备路径变量 ----------------
DMG_PATH="$HOME/openchat/download/OpenChat.dmg"
MOUNT_DIR="/Volumes/OpenChatUpdate"
APP_NAME="OpenChat.app"
DB_DIR="$HOME/openchat"
SOURCE_DB="$DB_DIR/openchat.db"
TARGET_DB="$DB_DIR/openchat_old.db"
FOUND_APP=""

# ---------------- 安装新版本 App ----------------
if [ -f "$DMG_PATH" ]; then
    echo "检测到更新包，开始挂载..."
    hdiutil attach "$DMG_PATH" -mountpoint "$MOUNT_DIR" -nobrowse -quiet

    MOUNTED_APP="$MOUNT_DIR/$APP_NAME"
    if [ ! -d "$MOUNTED_APP" ]; then
        echo "挂载失败:未找到 $APP_NAME"
        hdiutil detach "$MOUNT_DIR" -quiet
        exit 1
    fi

    echo "查找旧版 OpenChat.app..."
    FOUND_APP=$(find /Applications "$HOME/Applications"  -name "$APP_NAME" 2>/dev/null | head -n 1)

    if [ -z "$FOUND_APP" ]; then
        echo "未找到旧版本 App 默认安装到 /Applications"
        FOUND_APP="/Applications/$APP_NAME"
    fi

    echo "执行安装操作（单次授权）..."
    osascript <<EOF
do shell script "
rm -rf '$FOUND_APP' &&
cp -R '$MOUNTED_APP' '$FOUND_APP' &&
xattr -rd com.apple.quarantine '$FOUND_APP'
" with administrator privileges with prompt "OpenChat 正在更新，需要管理员权限"
EOF

    echo "卸载挂载点..."
    hdiutil detach "$MOUNT_DIR" -quiet

    echo "应用更新完成:$FOUND_APP"

    echo "清理下载目录..."
    rm -rf "$(dirname "$DMG_PATH")"
else
    echo "未检测到 DMG 文件，跳过 App 更新"
fi

# ---------------- 数据库备份 ----------------
if [ -f "$SOURCE_DB" ]; then
    TIMESTAMP=$(date "+%Y%m%d-%H%M")

    if [ -f "$TARGET_DB" ]; then
        echo "存在旧备份，移动为带时间戳版本..."
        mv "$TARGET_DB" "$DB_DIR/openchat_old_${TIMESTAMP}.db"
    fi

    echo "重命名数据库..."
    mv "$SOURCE_DB" "$TARGET_DB"
    echo "数据库已备份:$TARGET_DB"
else
    echo "未找到数据库:$SOURCE_DB 跳过备份"
fi

# ---------------- 可选自动启动 ----------------
 echo "正在启动 OpenChat..."
 open "$FOUND_APP"

echo "更新流程完成"
