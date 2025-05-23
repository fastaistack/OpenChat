import requests
import os
from tqdm import tqdm
import shutil
from pkg.projectvar import Projectvar

gvar = Projectvar()

class FileDownloadClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def list_files(self):
        """获取可下载文件列表"""
        response = requests.get(f"{self.base_url}/files")
        response.raise_for_status()
        return response.json()["files"]
    
    def download_file(self, url, payload = {},download_dir=None, chunk_size=1024*1024):
        """
        下载文件（支持分片下载）
        :param filename: 要下载的文件名
        :param save_path: 保存路径，默认为当前目录
        :param chunk_size: 分片大小（字节）
        """
        # if save_path is None:
        #     save_path = filename
        # elif os.path.isdir(save_path):
        #     save_path = os.path.join(save_path, filename)
        
        # 首次请求获取文件大小
        response = requests.head(url=url,json=payload,verify=False)
        response.raise_for_status()
        
        file_size = int(response.headers.get("Content-Length", 0))
        supports_range = response.headers.get("Accept-Ranges") == "bytes"
        
        if not supports_range or file_size <= chunk_size:
            # 不支持分片或文件太小，直接下载
            self._simple_download(url, payload, download_dir, file_size)
            return response
        else:
            # 分片下载
            self._chunked_download(url,payload, download_dir, file_size, chunk_size)
            return response
    
    def _simple_download(self, request_url,payload, download_dir, file_size):
        """普通下载"""
        response = requests.get(url=request_url,json=payload,verify=False,stream=True)
        response.raise_for_status()
        temp_file = os.path.join(download_dir, "download.temp")
        with open(temp_file, "wb") as f, tqdm(
            total=file_size, unit="B", unit_scale=True, desc='ceshi'
        ) as pbar:
            for chunk in response.iter_content(chunk_size=4096):
                f.write(chunk)
                pbar.update(len(chunk))
        os.rename(temp_file, os.path.join(download_dir,'download.zip'))
    
    def _chunked_download(self, request_url, payload, download_dir, file_size, chunk_size):
        """分片下载"""
        temp_file = os.path.join(download_dir, "download.temp")
        downloaded = 0
        
        # 检查是否有未完成的下载
        if os.path.exists(temp_file):
            downloaded = os.path.getsize(temp_file)
        
        with open(temp_file, "ab") as f, tqdm(
            initial=downloaded,
            total=file_size,
            unit="B",
            unit_scale=True,
            desc='ceshi'
        ) as pbar:
            while downloaded < file_size:
                end = min(downloaded + chunk_size - 1, file_size - 1)
                headers = {"Range": f"bytes={downloaded}-{end}"}
                response = requests.get(
                    url=request_url,
                    headers=headers,
                    json=payload,
                    verify=False,
                    stream=True)
                if response.status_code == 416:  # 范围无效
                    break
                
                response.raise_for_status()
                
                for chunk in response.iter_content(chunk_size=4096):
                    f.write(chunk)
                    pbar.update(len(chunk))
                    # print(f"\rProgress: {100 * pbar.n / pbar.total:.2f}%", end="")
                # 写入全局变量用于获取
                gvar.set_update_progress(f"{100 * pbar.n / pbar.total:.2f}")

                downloaded = end + 1
        # # 覆盖
        # shutil.move(temp_file, download_dir)
        # 下载完成后重命名临时文件
        # os.rename(temp_file, os.path.join(download_dir,'download.zip')) # win
        os.rename(temp_file, os.path.join(download_dir,'OpenChat.dmg')) # Mac

# if __name__ == "__main__":
#     client = FileDownloadClient()
    
#     # 列出文件
#     print("Available files:")
#     files = client.list_files()
#     for i, file_info in enumerate(files, 1):
#         print(f"{i}. {file_info['name']} ({file_info['size'] / 1024:.2f} KB)")
    
#     # 选择要下载的文件
#     if files:
#         choice = input("Enter file number to download (or 0 to exit): ")
#         try:
#             choice = int(choice)
#             if 1 <= choice <= len(files):
#                 filename = files[choice-1]["name"]
#                 print(f"Downloading {filename}...")
#                 client.download_file(filename, chunk_size=2*1024*1024)  # 2MB chunks
#                 print("Download completed!")
#         except ValueError:
#             print("Invalid input")