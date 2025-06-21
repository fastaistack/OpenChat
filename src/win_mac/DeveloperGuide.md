# Developer Guide

### 1. 项目目录结构

```shell
.
├── assets     # 项目依赖文件（UI文件、静态数据文件等）
│   ├── config
│   │   └── config.json # 本地默认权限加载文件
│   └── dist # UI文件
├── pkg # 模块目录
│   ├── __init__.py
│   ├── app # 客户端模块
│   │   ├── __init__.py
│   │   └── app.py # 客户端主文件
│   ├── database # 数据库模块
│   │   ├── __init__.py
│   │   ├── crud.py # 增删改查封装文件
│   │   ├── database.py # 数据库句柄
│   │   └── models.py # 表结构定义文件
│   ├── plugins #插件模块
│   │   ├── __init__.py
│   │   └── demo.py # 插件文件
│   ├── projectvar #全局变量模块
│   │   ├── __init__.py
│   │   ├── constants.py #静态数据文件
│   │   └── projectvar.py #全局变量对象（单例）
│   └── server # fastapi模块
│       ├── __init__.py
│       ├── router # 功能模块目录
│       │   ├── __init__.py
│       │   └── demo.py # 功能模块接口
│       └── server.py #fastapi主逻辑
└── yuanchat.py        #入口文件
```

## 2. Log模块

```python
# demo.py 与yuanchat.py同级
from pkg.logger import Log

log = Log()
log.debug("this is a debug message.")
log.info("this file name is {}", __file__)

# exception 用法

def test():
  try:
    	xxx()
  except:
    	log.exception("Exception:")
```

## 3. http.Headers
### 客户端
除 `/login` 请求外，其他接口的请求，均需要在 `http.header` 中增加 `Authorization` 字段，内容为登陆产生的 `token`

### 服务端
服务端 `server` 模块，新增一个 `authorization` 中间件，会对 `request.header` 中的 `token` 进行统一鉴权，如果鉴权成功，会在 `request.header` 中增加 `user-id`, `user-role`, `user-name` 三个属性。如果鉴权失败则直接返回错误。

***各个接口无需再鉴权***。

接口开发参考 `pkg/server/router/demo.py`

```python
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel

from ...projectvar import Projectvar
from ...projectvar import constants as const
from ..depends import get_headers #依赖
import os

gvar = Projectvar()

router = APIRouter(
    prefix = "/demo",
    tags=["demo"],
    responses={404: {"description": "Not found"}},
)

class Demo(BaseModel):
    demo: str

@router.post("/hello")
async def hello(demo: Demo, headers=Depends(get_headers)):
    print(headers)
    print(headers[const.HTTP_HEADER_USER_ID])
    print(headers[const.HTTP_HEADER_USER_NAME])
    print(headers[const.HTTP_HEADER_ROLE_ID])
    print(headers[const.HTTP_HEADER_ROLE_NAME])
    return {"result": "hello" + demo.demo}
```

## 4. 账户管理说明
### 权限添加
在 `assets/config/config.json` 文件中添加本地加载权限。格式如下：  
{"role_name":"admin","perm_uri":"/account/permission/create","perm_name":"权限创建"}  
`role_name`：角色名。admin代表管理员，owner代表拥有者；  
`perm_url`: 权限路径；  
`perm_name`：权限名。  

### 登录
http://127.0.0.1:5050/account/login  
-X 'POST'  
-H 'accept: application/json'   
-H 'Content-Type: application/x-www-form-urlencoded'  
-d 'grant_type=&username=hello&password=hello&scope=&client_id=&client_secret='  
`username`：为用户名  
`password`：为密码  
grant_type、scope、client_id、client_secret等其他参数可以为空，暂时不使用。  
内置用户`hello:hello`，角色为root。内置用户`world:world`，角色为admin。新创建用户默认角色为owner。  
登录成功：  
```json
{
  "flag": true,
  "errCode": 0,
  "errMsg": "success",
  "resData": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJoZWxsbyIsImV4cCI6MTcyMDkzMzUzOH0.AgwoCuL7YACKIUO0vEvM-_3iVL03Y-J7_bTbKiN81D0",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX25hbWUiOiJoZWxsbyIsInN1YiI6InJlZnJlc2gifQ.pCl2TWF4mV_Z0lENmmIJ9sHtQRqwLKz690S4qTyMBMo",
    "token_type": "bearer"
  }
}
```
`access_token`： 为登录成功返回的token值。  
`refresh_token`： 为token超时后，调用/account/refresh，传递的参数。暂时不用。  
`token_type`： token类型，默认为bearer，其他方式暂时不支持。  
登录失败：  
```json
{
  "flag": false,
  "errCode": 19,
  "errMsg": "用户名或密码错误",
  "resData": None
}
```

### Token使用
以/account/user/role/list为例，在调用该接口时，添加`-H 'Authorization: Bearer access_token'`  
`access_token`：为登录接口返回access_token，调用demo如下：  
http://127.0.0.1:5050/account/user/role/list  
-X 'GET'  
-H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJoZWxsbyIsImV4cCI6MTcyMDkzMzUzOH0.AgwoCuL7YACKIUO0vEvM-_3iVL03Y-J7_bTbKiN81D0'  
-d ''  

鉴权通过，会在3. http.Headers，中添加const.HTTP_HEADER_USER_ID，const.HTTP_HEADER_USER_NAME，const.HTTP_HEADER_ROLE_ID，const.HTTP_HEADER_ROLE_NAME四个信息。


## 5. 插件管理说明
### 插件顺序和路径
```
目前设置插件的顺序（plugin_order）如下：
前处理插件：
插件名称：preprocess_check_input (输入合法性校验)          顺序：5     路径：pkg/plugins
插件名称：preprocess_sensitive_filter (敏感信息检测)       顺序：4     路径：pkg/plugins/sensitive_filter_plugin
插件名称：preprocess_web_argument (获取web检索结果)        顺序：3     路径：pkg/plugins/webargument
插件名称：retrivers (知识库)                               顺序：2     路径：pkg/plugins/knowledge_base
插件名称：longcode (代码分析)                              顺序：1     路径：pkg/plugins
插件名称：baichuan2_hf (代码分析)                          顺序：0     路径：pkg/plugins/chat_model_plugin
插件名称：chatglm3_hf (代码分析)                           顺序：0     路径：pkg/plugins/chat_model_plugin
插件名称：qwen_gguf (代码分析)                             顺序：0     路径：pkg/plugins/chat_model_plugin
插件名称：yuan2_gguf (代码分析)                            顺序：0     路径：pkg/plugins/chat_model_plugin
插件名称：yuan2_hf (代码分析)                              顺序：0     路径：pkg/plugins/chat_model_plugin

后处理插件：
插件名称：postprocess_sensitive_filter (敏感信息检测)      顺序：-1     路径：pkg/plugins/sensitive_filter_plugin
插件名称：postprocess_clean_specialchars (清理特殊字符)    顺序：-2     路径：pkg/plugins
插件名称：postprocess_formula_rendering (公式渲染)         顺序：-3     路径：pkg/plugins
插件名称：preprocess_web_argument (返回web检索结果)        顺序：-4     路径：pkg/plugins/webargument
```

### 创建插件
调用接口：http://0.0.0.0:5050/plugin/create
参数：
```json
{
  "name": "demo2",                 //插件名称
  "path": "pkg/plugins",           //插件路径
  "plugin_order": 0,               //插件执行顺序
  "plugin_type": "normal",         //插件类型，默认写normal
  "status": false                  //插件状态，默认false
}
```

创建成功返回：
```json
{
  "flag": true,
  "errCode": 0,
  "errMsg": "成功",
  "resData": {
    "name": "demo4",
    "path": "pkg/plugins/",
    "plugin_order": -1,
    "plugin_type": "normal",
    "status": false
  }
}
```

### 获取单个插件详情
调用接口：http://0.0.0.0:5050/plugin/get
参数：
```json
{
  "pluginName": "demo1"                 //插件名称
}
```

成功返回：
```json
{
  "flag": true,
  "errCode": 0,
  "errMsg": "成功",
  "resData": {
    "name": "demo1",
    "path": "pkg/plugins/",
    "plugin_order": 0,
    "plugin_type": "normal",
    "status": false
  }
}
```

### 插件使用
1、插件位置：
请把插件以 *.py 文件（或放在文件夹中）的形式放置在 'pkg/plugins/' 目录下

2、创建插件
调用接口：http://0.0.0.0:5050/plugin/create 来创建插件

#### 插件文件（*.py）规定：
每个 *.py 文件需要包含两个函数：一个命名为 call(args)， 另一个命名为 get_default_settings()。
其中call函数是插件的主要实现逻辑；get_default_settings 要把插件的默认值以一个列表的形式返回，其中每个参数都以字典的形式存在，
其中每个字段定义如下：
arg_name：参数名
arg_datatype：参数类型 （"number"、"bool"、"string"、"time"）
arg_precision：参数精度 (如果参数值是小数的话，精确到小数点后几位)
arg_value：参数值
arg_max：参数最大值
arg_min：参数最小值
arg_maxlen：最大长度 (如果参数类型是string的话，参数的最大长度)
具体如下：
```python
async def call(item, setting):
    print("demo1")
    return "demo1"

async def get_default_settings()->list:
    settings = list()
    setting = {"arg_name": "response_length", "arg_datatype":"number", "arg_precision":0, "arg_value":512, "arg_max":8000, "arg_min":0, "arg_maxlen":0}
    settings.append(setting)
    setting = {"arg_name": "top_p",           "arg_datatype":"number", "arg_precision":1, "arg_value":0.8, "arg_max":1, "arg_min":0, "arg_maxlen":0}
    settings.append(setting)
    setting = {"arg_name": "temperature",     "arg_datatype":"bool", "arg_precision":1, "arg_value":True, "arg_max":1, "arg_min":0, "arg_maxlen":0}
    settings.append(setting)
    setting = {"arg_name": "top_k",           "arg_datatype":"number", "arg_precision":0, "arg_value":5, "arg_max":50, "arg_min":0, "arg_maxlen":0}
    settings.append(setting)
    setting = {"arg_name": "repeat_penalty",  "arg_datatype":"number", "arg_precision":2, "arg_value":1, "arg_max":3, "arg_min":0.5, "arg_maxlen":0}
    settings.append(setting)
    
    return settings
```