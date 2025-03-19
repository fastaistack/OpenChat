# -*- coding: utf-8 -*-

import time
import base64
import requests
import json
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
from pkg.logger import Log

log = Log()


"""  TOKEN start """
TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'

# 图像、文本审核url
IMAGE_CENSOR = "https://aip.baidubce.com/rest/2.0/solution/v1/img_censor/v2/user_defined"
TEXT_CENSOR = "https://aip.baidubce.com/rest/2.0/solution/v1/text_censor/v2/user_defined"

"""
    获取token
"""
def fetch_token(API_KEY, SECRET_KEY):
    url = f"{TOKEN_URL}?grant_type=client_credentials&client_id={API_KEY}&client_secret={SECRET_KEY}"
    payload = ""
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    result = response.json()

    if 'access_token' in result:
        return True, result['access_token']
    else:
        return False, "您输入的API Key或Secret Key不正确，请重新检查输入"

# try:
#     ACCESS_TOKEN = fetch_token()  #服务启动时，初始化获取access token
# except Exception as e:
#     log.info('\nbaidu filtering error: {0}'.format(e))


"""
    调用文本审核接口
    text: 待审核文本
"""
def text_request(text, ACCESS_TOKEN):
    # 获取access token
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # 拼接图像审核url
    text_url = f"{TEXT_CENSOR}?access_token={ACCESS_TOKEN}"
    body = {'text': text}

    response = requests.post(text_url, headers=headers, data=body, timeout=2)
    content = response.content.decode("UTF-8")
    return json.loads(content)


"""
    读取文件
    image_path：图片算在路径
"""
def read_file(image_path):
    f = None
    try:
        f = open(image_path, 'rb')
        return f.read()
    except:
        print('read image file fail')
        return None
    finally:
        if f:
            f.close()


"""
    调用图像审核接口
    img_path：图片算在路径
"""
def image_request(img_path, ACCESS_TOKEN):

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # 拼接图像审核url
    request_url = f"{IMAGE_CENSOR}?access_token={ACCESS_TOKEN}"

    # 以二进制方式打开图文件
    # 参数image：图像base64编码
    # 下面图片路径请自行切换为自己环境的绝对路径
    file_content = read_file(img_path)
    image = base64.b64encode(file_content)

    body = {"image": image, "imgType":0}

    response = requests.post(request_url, headers=headers, data=body, timeout=5)
    content = response.content.decode("UTF-8")
    return json.loads(content)


"""
    图像审核并行接口--多进程
"""
def request_pool_image(imgs_list, total_session=2):
    pool = Pool(processes=total_session)   #并发调用数目
    all_results = pool.map(image_request, imgs_list)
    pool.close()
    pool.join()

    return all_results


"""
    图像审核并发接口--多线程
"""
def request_thread_image(imgs_list, total_session=2):
    with ThreadPoolExecutor(max_workers=total_session) as pool1:
        result = pool1.map(image_request, imgs_list, timeout=10)

    return list(result)


"""
    文本审核并发接口--多线程
"""
def request_thread_text(txt_list, total_session=2):
    with ThreadPoolExecutor(max_workers=total_session) as pool1:
        result = pool1.map(text_request, txt_list, timeout=10)

    return list(result)


# if __name__ == '__main__':
    # start = time.time()
    # result = text_request('你是谁')
    # print(result)
    #
    # end = time.time()
    # print(f"Running time: {(end-start):.2f} Seconds")

    # fetch_token(API_KEY="", SECRET_KEY="")

