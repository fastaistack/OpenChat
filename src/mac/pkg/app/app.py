import webview


from ..projectvar import constants as const
from ..logger import Log
log = Log()

window = None
def closed(window):
    from pkg.server.router.knowledge import file_stop_analysis
    log.info("主窗口关闭，等待进程退出")
    file_stop_analysis()

class JsBridge:
    def open_url(self, url: str):
        import webbrowser
        log.info(f"打开外部链接：{url}")
        webbrowser.open(url)

    def copy_to_clipboard(self, text: str):
        import pyperclip
        log.info(f"复制文本：{text}")
        pyperclip.copy(text)

    def save_blob_file(self, filename_hint: str, data: list[int]) -> bool:
        """
        使用 AppleScript 弹出保存对话框，替代 webview.create_file_dialog
        """
        import subprocess
        import os
        import tempfile

        # 拼接 AppleScript，弹出保存对话框
        applescript = f'''
        set filePath to POSIX path of (choose file name with prompt "保存文件为：" default name "{filename_hint}")
        return filePath
        '''
        try:
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                env={**os.environ, 'LANG': 'zh_CN.UTF-8', 'LC_ALL': 'zh_CN.UTF-8'}  # ✅ 强制中文环境
            )

            save_path = result.stdout.strip()

            if not save_path:
                print("用户取消保存")
                return False

            with open(save_path, 'wb') as f:
                f.write(bytearray(data))

            print(f"文件已保存至: {save_path}")
            return True

        except Exception as e:
            print("保存失败:", e)
            return False

import os

def run():

    log = Log()
    log.debug("app.run is called.")
    url = 'http://localhost:' + str(const.OPENCHAT_SERVER_PORT)
    webview.settings['ALLOW_DOWNLOADS'] = True
    global window
    
    window = webview.create_window(
        title= "OpenChat",
        url=url,
        width=1600,
        height=1300,
        js_api=JsBridge(),
        # confirm_close= True
    )
    window.events.closed += closed
    webview.start()
    