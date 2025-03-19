import os
from typing import Any, Dict, List
from pkg.plugins.knowledge_base.consts import DEFAULT_PROMPT_TEMPATE

this_dir = os.path.dirname(__file__)

AS_HOME_DIR = os.path.abspath(os.path.join(this_dir, '../../'))
AS_LOG_HOME = os.path.join(AS_HOME_DIR, 'logs')   # 日志记录位置
if not os.path.exists(AS_LOG_HOME):
    os.mkdir(AS_LOG_HOME)

AS_ASSETS_DIR = os.path.join(AS_HOME_DIR, 'assets/')

# 超参数结构体
setting = {"do_sample":True, "response_length":512, "top_p":0.8, "temperature":1, "top_k":5, "repeat_penalty":1.0,  #模型生成相关参数，UI设置
           "multi_turn":0, #UI设置，多轮对话轮数，为0表示关闭多轮对话
           "stream": True, #UI设置，是否采用流式输出，默认采用
           "device":'', #UI设置，模型推理所在设备，默认为空表示根据设备自动识别
           "web_retrieve_args":{ #web检索相关参数
               "retrieve_topk":3, "template":"说明：您是一位认真的研究者。使用提供的网络搜索结果，对给定的问题写一个全面而详细的回复。", "embedding_model_path":"", "web_api_key":"",  #UI设置
               "style_search":"serper",
               "formatted_relevant_docs":"", "relevant_docs_list":"", "web_response":{}   #中间插件产生
                },
           "knowledge_base_args": {  # 知识库相关参数
               "kb_name": "kb_test1",
               "vs_type": "chromadb",
               "global_param": {
                   "embed_model": "text2vec-base-chinese",
               },
               "storage_param": {
                   "chunk_size": 1000,
                   "overlap_size": 120,
                   "distance_strategy": "l2",
               },
               "query_param": {
                   "k": 5,
                   "score_threshold": 0.5,
                   "fetch_k": 20,
                   "lambda_mult": 0.5,
                   "distance_strategy": "cosine",
                   "search_type": "similarity",
                   "prompt_template": DEFAULT_PROMPT_TEMPATE,
               },  # 以上为UI设置
               "relevant_docs_list": List[str],
               "context": "",
               "final_prompt": ""  # 中间插件产生
           },
           "sensitive_filter_args":{
               "style_filter_list": ["local_words"],
               "is_end": False,
               "local_words": {"interval_tokens":10},
               "baidu_api": {"interval_tokens":20, "api_key":"", "secret_key":""},
               "local_model": {"interval_tokens":20, "filter_model_list":[]}  #"filter_model_list"格式[{"type":"politic", "threshold":0.8}, {"type":"porn", "threshold":0.8}]
           },
           "input_prompt": "",
           "output_answer":"" #中间插件产生，输出答案
           }
