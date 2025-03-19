import webview


from ..projectvar import constants as const
from ..logger import Log
log = Log()

def closed(window):
    from pkg.server.router.knowledge import file_stop_analysis
    log.info("主窗口关闭，等待进程退出")
    file_stop_analysis()

def run():
    log = Log()
    log.debug("app.run is called.")

    # root = tk.Tk()
    # width = root.winfo_screenwidth()
    # height= root.winfo_screenheight()
    # root.destroy()
    url = 'http://localhost:' + str(const.YUAN_SERVER_PORT)
    webview.settings['ALLOW_DOWNLOADS'] = True
    window = webview.create_window(
        title= "OpenChat",
        url=url,
        width=1200,
        height=900,
        confirm_close= True
    )
    window.events.closed += closed
    webview.start()