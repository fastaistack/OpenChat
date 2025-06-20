#!/bin/bash
# install_tesseract.sh

# 用户确认是否安装 Tesseract
response=$(osascript <<EOF
tell application "System Events"
    activate
    display dialog "影印版 PDF 读取需要依赖 Tesseract OCR，当前系统未检测到。\n\n是否打开终端自动安装所需依赖？（安装完成后请手动重启应用）" buttons {"否", "是"} default button "是"
end tell
EOF
)

# 用户选择“否”就退出
if [[ "$response" != *"button returned:是"* ]]; then
    echo "用户取消了安装。"
    exit 0
fi

# 检查 Homebrew 是否已安装
if ! command -v brew >/dev/null 2>&1; then
    osascript <<EOF
tell application "System Events"
    activate
    display dialog "未检测到 Homebrew。\n\n将打开终端自动开始安装 Homebrew。" buttons {"确定"} default button "确定"
end tell
EOF

    # 启动 Homebrew 安装（用户需手动确认授权）
    osascript <<EOF
tell application "Terminal"
    activate
    do script "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
end tell
EOF

    exit 0  # 提示用户安装完后再次运行本脚本
fi

# 替换清华源函数
function use_tuna_mirrors() {
    echo "更换 Homebrew 镜像源为清华大学 TUNA..."
    git -C "\$(brew --repo)" remote set-url origin https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git
    git -C "\$(brew --repo homebrew/core)" remote set-url origin https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git
    git -C "\$(brew --repo homebrew/cask)" remote set-url origin https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-cask.git
    brew update
}

# ✅ 切换源
use_tuna_mirrors

# ✅ 安装 Tesseract 和语言包
osascript <<EOF
tell application "Terminal"
    activate
    do script "brew install tesseract && brew install tesseract-lang"
end tell
EOF

