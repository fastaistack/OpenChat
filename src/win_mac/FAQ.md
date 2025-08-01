# FAQ

## 1.应用默认安装路径为C:Program Files\OpenChat，遇到创建知识库失败、上传PDF失败等问题?

请使用管理员身份运行OpenChat，授予OpenChat文件读写执行等权限。

## 2.在线更新失败，应用重启后仍提示更新?

请检查安装路径中是否存在download文件夹，并确认文件夹中是否有下载内容；
如果存在下载内容，尝试在高级系统设置->环境变量->系统变量中添加以下内容，重启电脑重新更新
```shell
%SystemRoot%\system32
%SystemRoot%
%SYSTEMROOT%\System32\WindowsPowerShell\v1.0\
%SystemRoot%\System32\Wbem
```

## 3.启动时失败？
报错import onnxruntime时，可以安装以下[安装包](https://aka.ms/vs/17/release/vc_redist.x64.exe)解决onnxruntime error。