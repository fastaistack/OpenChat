
DEFAULT_VS_PATH = "./chromadb"
# DEFAULT_EMBEDDING_MODEL = "/mnt/md0/wulixuan/models/bge-large-zh-v1.5/"
DEFAULT_EMBEDDING_MODEL = "D:\\Program Files\\Python311\\workspace\\text2vec-base-chinese"
DEFAULT_EMBEDDING_CUDA = "cuda:0"

# milvus settings
DEFAULT_MILVUS_HOST = "10.51.24.111"
DEFAULT_MILVUS_PORT = "19530"
DEFAULT_MILVUS_USER = ""
DEFAULT_MILVUS_PASSWORD = ""
DEFAULT_DB_NAME = "default"

DEFAULT_CHUNK_SIZE = 200
DEFAULT_OVERLAP_SIZE = 20
DEFAULT_METRIC_TYPE = "COSINE"
DEFAULT_INDEX_TYPE = "IVF_FLAT"
DEFAULT_DISTANCE_STRATEGY = "cosine"

DEFAULT_K = 1
DEFAULT_SCORE_THRESHOLD = 0.5
DEFAULT_FETCH_K = 20
DEFAULT_LAMBDA_MULT = 0.5
DEFAULT_SEARCH_TYPE = "similarity"
DEFAULT_PROMPT_TEMPATE = """
请根据检索到的背景信息，详细回答问题，答案要清晰有条理。如果背景信息为空，则直接答复'未检索到相关信息，无法回答该问题'。
"""
RENDER_TEMPLATE = """
背景信息: {contexts}
问题: {question}
"""