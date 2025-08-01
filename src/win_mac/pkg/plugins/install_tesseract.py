import subprocess
import shutil
from pkg.logger import Log

log = Log()

def run_applescript(script: str) -> str:
    """运行 AppleScript 脚本并返回输出内容"""
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return result.stdout.strip()

def ask_user_install() -> bool:
    """弹出对话框询问用户是否安装 Tesseract"""
    script = '''
    tell application "System Events"
        activate
        display dialog "影印版 PDF 读取需要依赖 Tesseract OCR，当前系统未检测到。\\n\\n是否打开终端自动安装所需依赖？（安装完成后请手动重启应用）" buttons {"否", "是"} default button "是"
    end tell
    '''
    response = run_applescript(script)
    return "是" in response

def ask_user_install_brew():
    """提示并启动 Homebrew 安装流程"""
    # 弹窗提示
    script = '''
    tell application "System Events"
        activate
        display dialog "未检测到 Homebrew。\\n\\n将打开终端自动开始安装 Homebrew。" buttons {"确定"} default button "确定"
    end tell
    '''
    run_applescript(script)

    # 打开终端执行 brew 安装命令
    terminal_script = '''
    tell application "Terminal"
        activate
        do script "/bin/bash -c \\"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\\""
    end tell
    '''
    run_applescript(terminal_script)

def use_tuna_mirrors():
    """更换 Homebrew 镜像为清华源"""
    print("🔁 更换 Homebrew 镜像源为清华大学 TUNA...")
    mirror_script = '''
    git -C "$(brew --repo)" remote set-url origin https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git &&
    git -C "$(brew --repo homebrew/core)" remote set-url origin https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git &&
    git -C "$(brew --repo homebrew/cask)" remote set-url origin https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-cask.git &&
    brew update
    '''
    subprocess.run(["/bin/bash", "-c", mirror_script])

def install_tesseract():
    """
    主安装函数：
    - 检查 brew
    - 更换源
    - 打开终端执行安装命令
    """
    if not ask_user_install():
        log.info("🛑 用户取消安装。")
        return

    if shutil.which('brew') is None:
        ask_user_install_brew()
        return

    use_tuna_mirrors()

    log.info("🚀 打开终端开始安装 tesseract ...")
    terminal_script = '''
    tell application "Terminal"
        activate
        do script "brew install tesseract && brew install tesseract-lang"
    end tell
    '''
    run_applescript(terminal_script)
