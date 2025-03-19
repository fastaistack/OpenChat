
from typing import List
from pkg.plugins.knowledge_base.base import KBServiceFactory
from pkg.plugins.knowledge_base.consts import (
    DEFAULT_PROMPT_TEMPATE,
    RENDER_TEMPLATE,
)
from pkg.database.schemas import ChatMessageInfo
from pkg.server.router.knowledge import get_knowledge_by_id
from pkg.logger import Log

logger = Log()

from typing import Optional


from typing import Optional, Tuple

def get_file_and_error(chat_message_info: ChatMessageInfo) -> Tuple[Optional[dict], Optional[str]]:
    """
    从 ChatMessageInfo 对象中获取 file_id 和错误信息(如果有的话)。
    返回一个元组,第一个元素是 file_id(如果找到),第二个元素是错误信息(如果有)。
    """
    reference_info = chat_message_info.reference_info
    error_message = None

    # 检查 reference_info 是否存在
    if not reference_info:
        return None, "reference_info does not exist."

    # 检查 reference_info 是否为字典类型
    if not isinstance(reference_info, dict):
        return None, "reference_info should be dict."

    # 检查 reference_info 中是否包含 "file" 键
    if "file" not in reference_info:
        return None, "no file in reference_info"

    files = reference_info["file"]

    # 检查 files 是否为列表类型
    if not isinstance(files, list):
        return None, f"'file' should be a list, got [{type(files)}]"

    # 如果 files 列表非空,返回第一个文件的 file_id
    if files:
        first_file = files[0]
        if isinstance(first_file, dict) and "file_id" in first_file:
            return first_file, ""

    # 如果没有找到 file_id,返回 None 和错误信息
    return None, f"can not find file_id in [{reference_info}]..."


def call(
        request: ChatMessageInfo,
        setting: dict,
        content_setting: dict = {},
):
    """
    知识库检索前处理：对输入request进行合法性检验
    Args:
        reqeust: ChatMessageInfo对象，从中获取knowledge_id/file_id等信息
        setting：是插件参数列表，包含session中文档对话对应的知识库的参数dict，直接使用，禁止修改,
        content_setting：插件产生的中间变量，透传即可
    Returns:
        {
            "flag": False表示有不合法情况，返回"result"至UI；True表示正常，继续代码
            "result"：返回{"content": "", "refs": [], "recommend question": []}，
                      如果flag为False，content会记录错误信息。
            "content_setting"：插件产生的中间变量，透传即可
        }
    """
    logger.debug(f"chat files query params: request: [{request.dict().items()}]; setting: [{setting.items()}]")
    # get question
    question = request.message
    knowledge_id = request.reference_info.get("knowledge_id", "")
    file, err_msg = get_file_and_error(request)
    if not file:
        logger.error(err_msg)
        raise ValueError(err_msg)
    file_id = file.get("file_id")
    file_name = file.get("file_name")
    logger.debug(f"request with knowledge_id: [{knowledge_id}]; file_id: [{file_id}]; file_name: [{file_name}]")

    # 从插件管理中获取知识库参数
    params_dict = setting
    if not params_dict or knowledge_id not in params_dict.keys():
        # 若插件管理中没有参数，则使用知识库中的默认参数
        logger.error(f"Cannot get params from setting with knowledge_id: [{knowledge_id}]; "
                     f"session_id: [{request.session_id}]; setting: [{setting.items()}]."
                     f"Using default setting.")
        knowledge_params_dict = get_knowledge_by_id(knowledge_id)

        # out_dict = {"content": "", "refs": [], "recommend_question": []}
        # content_setting["knowledge_base_args"] = {}
        # content_setting["knowledge_base_args"]["relevant_docs_list"] = []
        # content_setting["knowledge_base_args"]["context"] = ""
        # content_setting["knowledge_base_args"]["final_prompt"] = ""
        # content_setting["input_prompt"] = question
        # plugin_result = {
        #     "flag": True,
        #     "result": out_dict,
        #     "content_setting": content_setting,
        # }
        # logger.debug(f"chat files retriever plugin return: [{plugin_result}]")
        # return plugin_result
    else:
        knowledge_params_dict = params_dict[knowledge_id]
    try:
        # 针对文件对话, 需要指定file_id进行检索
        knowledge_params_dict["query_param"]["file_id"] = file_id
        logger.debug(f"knowledge base [{knowledge_id}] params from plugin management module: [{knowledge_params_dict}]")

        kb_svc = KBServiceFactory.get_service(knowledge_params_dict)

        # GET CONTEXT
        result = kb_svc.do_search(question, params=knowledge_params_dict)

        docs_list = []
        for data in result:
            docs_list.append(data.page_content)

        contexts = "\n\n".join(docs_list)

        prompt_template = knowledge_params_dict["query_param"].get("prompt_template") or DEFAULT_PROMPT_TEMPATE
        if prompt_template == DEFAULT_PROMPT_TEMPATE:
            logger.warning("No prompt_template found in params_dict['query_param']. Using default template instead.")

        final_prompt = RENDER_TEMPLATE.format(contexts=contexts, question=question).strip("\n")
        final_prompt = prompt_template + "\n" + final_prompt
    except Exception as e:
        logger.error(f"Error happened in chat files plugin with request [{request.dict().items()}], error: [{e}]")
        out_dict = {"content": str(e), "refs": [], "recommend_question": []}
        content_setting["knowledge_base_args"] = knowledge_params_dict
        content_setting["knowledge_base_args"]["relevant_docs_list"] = []
        content_setting["knowledge_base_args"]["context"] = ""
        content_setting["knowledge_base_args"]["final_prompt"] = ""
        content_setting["input_prompt"] = ""
        plugin_result = {
            "flag": False,
            "result": out_dict,
            "content_setting": content_setting,
        }
        logger.debug(f"knowledge base retriever plugin return: [{plugin_result}]")
        return plugin_result
    # setting["knowledge_base_args"]["prompt_template"] = params_dict.get("prompt_template", DEFAULT_PROMPT_TEMPATE)
    content_setting["knowledge_base_args"] = knowledge_params_dict
    content_setting["knowledge_base_args"]["relevant_docs_list"] = docs_list
    content_setting["knowledge_base_args"]["context"] = contexts
    content_setting["knowledge_base_args"]["final_prompt"] = ""
    content_setting["input_prompt"] = final_prompt

    out_dict = {"content": "", "refs": [], "recommend_question": []}
    plugin_result = {
        "flag": True,
        "result": out_dict,
        "content_setting": content_setting,
    }
    logger.debug(f"chat files retriever plugin return: [{plugin_result}]")
    return plugin_result


def get_default_settings() -> List:
    return []


if __name__ == '__main__':
    request = ChatMessageInfo(
        message = "苏东坡是谁？",
        session_id = "xxxx",
        knowledge_id = "xxx",
    )

    setting = {
        "do_sample":True, "response_length":512, "top_p":0.8, "temperature":1, "top_k":5, "repeat_penalty":1.0,  #模型生成相关参数，UI设置
        "multi_turn":0, #UI设置，多轮对话轮数，为0表示关闭多轮对话
        "stream": True, #UI设置，是否采用流式输出，默认采用
        "device":'', #UI设置，模型推理所在设备，默认为空表示根据设备自动识别
        "web_retrieve_args":{ #web检索相关参数
            "retrieve_topk":3, "template":"", "embedding_model_path":"", "serper_key":"",  #UI设置
            "formatted_relevant_docs":"","relevant_docs_list":"", "serper_response":{}   #中间插件产生
             },
        "knowledge_base_args": {  # 知识库相关参数
            "kb_name": "kb_test1",
            "vs_type": "chromadb",
            "global_param": {
                "embed_model": "D:\\Program Files\\Python311\\workspace\\text2vec-base-chinese",
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
        "input_prompt": "",
        "output_answer":"" #中间插件产生，输出答案
    }

    call(request, None)