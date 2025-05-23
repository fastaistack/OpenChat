import webview
import tkinter as tk

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

def run():
    log = Log()
    log.debug("app.run is called.")

    root = tk.Tk()
    width = root.winfo_screenwidth()
    height= root.winfo_screenheight()
    root.destroy()
    url = 'http://localhost:' + str(const.OPENCHAT_SERVER_PORT)
    webview.settings['ALLOW_DOWNLOADS'] = True
    global window
    window = webview.create_window(
        title= "OpenChat",
        url=url,
        width=width,
        height=height,
        js_api=JsBridge(),
        confirm_close= True
    )
    window.events.closed += closed
    webview.start()