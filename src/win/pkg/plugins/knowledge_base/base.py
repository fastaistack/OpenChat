import os.path
from abc import ABC, abstractmethod
# import torch
from langchain.docstore.document import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.embeddings import OllamaEmbeddings

from pkg.plugins.knowledge_base.utils import KnowledgeFile
from pkg.logger import Log
from typing import List, Dict
from pkg.plugins.knowledge_base.consts import (
    DEFAULT_EMBEDDING_CUDA,
    DEFAULT_K,
    DEFAULT_FETCH_K,
    DEFAULT_SEARCH_TYPE,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_OVERLAP_SIZE,
    DEFAULT_LAMBDA_MULT,
    DEFAULT_SCORE_THRESHOLD,
    DEFAULT_PROMPT_TEMPATE,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_DISTANCE_STRATEGY,
)
from pkg.server.process import process_setting

logger = Log()


# def normalize(embeddings: List[List[float]]) -> np.ndarray:
#     '''
#     sklearn.preprocessing.normalize 的替代（使用 L2），避免安装 scipy, scikit-learn
#     '''
#     norm = np.linalg.norm(embeddings, axis=1)
#     norm = np.reshape(norm, (norm.shape[0], 1))
#     norm = np.tile(norm, (1, len(embeddings[0])))
#     return np.divide(embeddings, norm)


class SupportedVSType:
    MILVUS = 'milvus'
    CHROMADB = 'chromadb'


class SearchType:
    SIMILARITY = 'similarity'
    SIMILARITY_SCORE_THRESHOLD = 'similarity_score_threshold'
    MMR = 'mmr'


class DistanceStrategy:
    EUCLIDEAN = "l2"
    COSINE = "cosine"
    MAX_INNER_PRODUCT = "inner"


# class SentenceTransformerEmbeddingsLoader:
#     _loaded_models = {}

#     @classmethod
#     def load_model(cls, model_path):
#         if model_path not in cls._loaded_models:
#             logger.debug(f"loading model: [{model_path}]...")
#             # 使用GPU或者CPU
#             DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#             # 默认使用CPU
#             # DEVICE = torch.device('cpu') 
#             # 加载并保存模型
#             cls._loaded_models[model_path] = SentenceTransformerEmbeddings(
#                 model_name=model_path,
#                 model_kwargs={'device': DEVICE},
#                 encode_kwargs={'normalize_embeddings': True},
#             )
#         return cls._loaded_models[model_path]


class KBService(ABC):

    def __init__(self, params_dict: Dict):
        import time
        start_time = time.perf_counter()
        self.kb_name = params_dict.get("kb_name", "")
        if not self.kb_name:
            raise ValueError("kb_name must provide in params_dict.")
        embed_model_name = params_dict["global_param"].get("embed_model") or DEFAULT_EMBEDDING_MODEL
        global_path = process_setting.get_system_default_path().config_value
        if not global_path.endswith(os.path.sep):
            global_path += os.path.sep
        embed_model_origin = os.path.join(global_path, "models", embed_model_name)
        # self.embed_model = os.path.normpath(embed_model_origin)
        # self.embeding_fn = SentenceTransformerEmbeddingsLoader.load_model(self.embed_model)
        self.embed_model = embed_model_name
        self.embeding_fn = OllamaEmbeddings(model=self.embed_model.split(':')[0])
        
        # from langchain_community.embeddings import OpenAIEmbeddings
        # print('class KBService(ABC):      使用硅基流动的embedding')
        # self.embed_model = "BAAI/bge-large-zh-v1.5"
        # self.embeding_fn = OpenAIEmbeddings(model = 'BAAI/bge-large-zh-v1.5', openai_api_base = 'https://api.siliconflow.cn/v1',openai_api_key = 'k-jyjrpgkwlitulmzgfpaabqmhaycobiuzkmvobrbhjsivdayc')
        
        end_time1 = time.perf_counter()
        logger.debug(f"After load embeding model time: {end_time1 - start_time} seconds")
        self.chunk_size = params_dict["storage_param"].get("chunk_size") or DEFAULT_CHUNK_SIZE
        self.overlap_size = params_dict["storage_param"].get("overlap_size") or DEFAULT_OVERLAP_SIZE
        self.distance_strategy = params_dict["storage_param"].get("distance_strategy") or DEFAULT_DISTANCE_STRATEGY
        self.k = params_dict["query_param"].get("k") or DEFAULT_K
        self.score_threshold = params_dict["query_param"].get("score_threshold") or DEFAULT_SCORE_THRESHOLD
        self.fetch_k = params_dict["query_param"].get("fetch_k") or DEFAULT_FETCH_K
        self.lambda_mult = params_dict["query_param"].get("lambda_mult") or DEFAULT_LAMBDA_MULT
        self.search_type = params_dict["query_param"].get("search_type") or DEFAULT_SEARCH_TYPE
        self.prompt_template = params_dict["query_param"].get("prompt_template") or DEFAULT_PROMPT_TEMPATE
        self.do_init()

        end_time2 = time.perf_counter()
        logger.debug(f"After init time: {end_time2 - start_time} seconds")

    def __repr__(self) -> str:
        return f"{self.vs_type()}:{self.kb_name} @ {self.embed_model}"

    @abstractmethod
    def do_init(self):
        pass

    @abstractmethod
    def vs_type(self) -> str:
        pass

    @abstractmethod
    def create_kb(self):
        """
        创建知识库
        """
        pass

    @abstractmethod
    def clear_vs(self):
        """
        删除向量库中所有内容
        """
        pass

    @abstractmethod
    def drop_kb(self):
        """
        删除知识库
        """
        pass

    @abstractmethod
    def add_files(self, kb_files: List[KnowledgeFile], **kwargs):
        """
        向知识库添加文件
        如果指定了docs，则不再将文本向量化
        """
        pass

    @abstractmethod
    def do_search(self,
                  query: str,
                  params: Dict,
                  ) -> List[Document]:
        """
        搜索知识库子类实自己逻辑
        """
        pass

    @abstractmethod
    def delete_file(self, kb_file: KnowledgeFile, **kwargs):
        """
        从知识库删除文件
        """
        pass

    def is_file_exist(self, kb_name: str, kb_file: KnowledgeFile):
        """
        判断知识库kb_name中是否存在文件kb_file
        :param kb_name: 知识库名称
        :param kb_file: 文件名
        :return:
        """
        pass

    def list_files(self, kb_name: str):
        """
        列出给定知识库kb_name中的所有文件名称
        :param kb_name: 知识库名称
        :return:
        """
        pass

    def count_files(self, kb_name: str):
        """
        统计知识库kb_name中的文件数
        :param kb_name: 知识库名称
        :return:
        """
        pass

    @classmethod
    def list_kbs(cls):
        pass

    def get_text_splitter(self):
        # ref: https://python.langchain.com/docs/modules/data_connection/document_transformers/recursive_text_splitter/#splitting-text-from-languages-without-word-boundaries
        text_splitter = RecursiveCharacterTextSplitter(
            separators=[
                "\n\n",
                "\n",
                " ",
                ".",
                ",",
                "\u200b",  # Zero-width space
                "\uff0c",  # Fullwidth comma
                "\u3001",  # Ideographic comma
                "\uff0e",  # Fullwidth full stop
                "\u3002",  # Ideographic full stop
                "",
            ],
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap_size,
        )
        return text_splitter


class KBServiceFactory:
    @staticmethod
    def get_service(params_dict: Dict) -> KBService:
        vs_type = params_dict.get("vs_type")
        if not vs_type:
            raise ValueError("vs_type must provide in params_dict.")
        if isinstance(params_dict.get("vs_type"), str):
            vs_type = getattr(SupportedVSType, vs_type.upper())
        # if SupportedVSType.MILVUS == vs_type:
        #     from pkg.plugins.knowledge_base.milvus_kb_service import MilvusKBService
        #     return MilvusKBService(params_dict)
        if SupportedVSType.CHROMADB == vs_type:
            from pkg.plugins.knowledge_base.chromadb_kb_service import ChromaKBService
            return ChromaKBService(params_dict)
        else:
            raise ValueError(f"vs_type of [{vs_type}] is not supported yet."
                             f"For now, only support [{vars(SupportedVSType).values()}]")


if __name__ == '__main__':
    svc = KBServiceFactory.get_service({
        "kb_name": "foo",
        "vs_type": "chromadb",
    })
    print(svc)