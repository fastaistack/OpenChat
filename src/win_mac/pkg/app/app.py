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
    def __init__(self, window):
        self.window = window
    
    def open_url(self, url: str):
        import webbrowser
        log.info(f"打开外部链接：{url}")
        webbrowser.open(url)

    # def copy_to_clipboard(self, text: str):
    #     import pyperclip
    #     log.info(f"复制文本：{text}")
    #     pyperclip.copy(text)

    def save_blob_file(self, filename_hint: str, data: list[int]) -> bool:
        """
        弹出保存对话框：macOS 使用 AppleScript，其他平台使用 window.create_file_dialog。
        """
        import subprocess
        import os

        save_path = None

        try:
            if const.SYSTEM == const.MACOS:
                # ✅ macOS: 使用 AppleScript 弹出保存对话框
                applescript = f'''
                set filePath to POSIX path of (choose file name with prompt "保存文件为：" default name "{filename_hint}")
                return filePath
                '''
                print(applescript)
                result = subprocess.run(
                    ['osascript', '-e', applescript],
                    capture_output=True,
                    text=True,
                    env={**os.environ, 'LANG': 'zh_CN.UTF-8', 'LC_ALL': 'zh_CN.UTF-8'}
                )
                save_path = result.stdout.strip()
            else:
                # ✅ 其他平台: 使用窗口对象调用 create_file_dialog
                file_paths = self.window.create_file_dialog(
                    dialog_type=webview.SAVE_DIALOG,
                    save_filename=filename_hint
                )
                if isinstance(file_paths, list):
                    save_path = file_paths[0] if file_paths else None
                elif isinstance(file_paths, str):
                    save_path = file_paths

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

def run():
    log = Log()
    log.debug("app.run is called.")

    if const.SYSTEM == const.WINDOWS:
        try:
            import tkinter as tk
            root = tk.Tk()
            width = root.winfo_screenwidth()
            height= root.winfo_screenheight()
            root.destroy()
        except ImportError as e:
            print(e)
       
    else:
        width = 1200
        height= 800
    url = 'http://localhost:' + str(const.OPENCHAT_SERVER_PORT)
    webview.settings['ALLOW_DOWNLOADS'] = True
    global window
    window = webview.create_window(
        title= "OpenChat",
        url=url,
        width=width,
        height=height,
        confirm_close= True
    )
    window.events.closed += closed
    def expose_bridge():
        bridge = JsBridge(window)
        window.expose(bridge.open_url)
        window.expose(bridge.save_blob_file)
        # window.expose(bridge.copy_to_clipboard)  ##win无需添加


    # 启动 webview，并执行 expose_bridge 作为初始化
    webview.start(func=expose_bridge)
