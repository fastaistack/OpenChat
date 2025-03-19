# from typing import List, Dict

# from langchain.schema import Document
# from langchain.vectorstores.milvus import Milvus
# from pymilvus import (
#     MilvusClient,
#     Collection,
# )

# from pkg.plugins.knowledge_base.utils import KnowledgeFile
# from pkg.plugins.knowledge_base.base import (KBService, SupportedVSType, SearchType)
# from pkg.plugins.knowledge_base.consts import (
#     DEFAULT_MILVUS_HOST,
#     DEFAULT_MILVUS_PORT,
#     DEFAULT_MILVUS_USER,
#     DEFAULT_MILVUS_PASSWORD,
#     DEFAULT_DB_NAME,
#     DEFAULT_METRIC_TYPE,
#     DEFAULT_INDEX_TYPE,
#     DEFAULT_K,
#     DEFAULT_SEARCH_TYPE,
#     DEFAULT_FETCH_K,
#     DEFAULT_PROMPT_TEMPATE,
#     DEFAULT_LAMBDA_MULT,
#     DEFAULT_SCORE_THRESHOLD,
# )
# from pkg.logger import Log

# logger = Log()

# DEFAULT_METADATAS = ['source', 'file_id', 'file_name', 'text', 'vector', 'pk']


# class MetricType:
#     L2 = "L2"
#     COSINE = "COSINE"
#     IP = "IP"


# class IndexType:
#     FLAT = "FLAT"
#     IVF_FLAT = "IVF_FLAT"
#     IVF_SQ8 = "IVF_SQ8"
#     IVF_PQ = "IVF_PQ"
#     GPU_IVF_FLAT = "GPU_IVF_FLAT"
#     GPU_IVF_PQ = "GPU_IVF_PQ"
#     HNSW = "HNSW"


# class MilvusKBService(KBService):

#     def __init__(self, params_dict: Dict):
#         super().__init__(params_dict)
#         self.milvus_db_host = params_dict["global_param"].get("milvus_db_host") or DEFAULT_MILVUS_HOST
#         self.milvus_db_port = params_dict["global_param"].get("milvus_db_port") or DEFAULT_MILVUS_PORT
#         self.milvus_db_user = params_dict["global_param"].get("milvus_db_user") or DEFAULT_MILVUS_USER
#         self.milvus_db_password = params_dict["global_param"].get("milvus_db_password") or DEFAULT_MILVUS_PASSWORD
#         self.connection_args = {
#             "host": self.milvus_db_host,
#             "port": self.milvus_db_port,
#             "user": self.milvus_db_user,
#             "password": self.milvus_db_password,
#             "db_name": DEFAULT_DB_NAME,
#             "secure": False,
#         }

#         self.client = MilvusClient(
#             uri=f"http://{self.milvus_db_host}:{self.milvus_db_port}",
#             user=self.milvus_db_user,
#             password=self.milvus_db_password,
#             db_name=DEFAULT_DB_NAME,
#         )

#         self.metric_type = params_dict["storage_param"].get("metric_type") or DEFAULT_METRIC_TYPE
#         self.index_type = params_dict["storage_param"].get("index_type") or DEFAULT_INDEX_TYPE
#         self.index_params = {
#             'metric_type': self.metric_type,
#             'index_type': self.index_type,
#             'params': {
#                 'nlist': 1024,
#             },
#         }

#         self.search_params = {
#             "metric_type": self.metric_type,
#             "params": {
#                 "nprobe": 10,
#             },
#         }

#         self.embeding_dim = len(self.embeding_fn.embed_query(''))

#         logger.debug(f"embedding model [{self.embed_model}] dimenson: [{self.embeding_dim}]")

#         self.vs = Milvus(
#             embedding_function=self.embeding_fn,
#             collection_name=self.kb_name,
#             connection_args=self.connection_args,
#             index_params=self.index_params,
#             search_params=self.search_params,
#         )

#     def do_init(self):
#         pass

#     def vs_type(self) -> str:
#         return SupportedVSType.MILVUS

#     def get_collection(self):
#         return Collection(self.kb_name)

#     def create_kb(self) -> None:
#         '''
#         通过创建知识库
#         :return:
#         '''
#         # # 添加字段
#         # fields = [
#         #     FieldSchema("id", DataType.INT64, is_primary=True, auto_id=True),
#         #     FieldSchema("source", DataType.VARCHAR),
#         #     FieldSchema("file_id", DataType.VARCHAR),
#         #     FieldSchema("file_name", DataType.VARCHAR),
#         #     FieldSchema("text", DataType.VARCHAR),
#         #     FieldSchema("vector", DataType.FLOAT_VECTOR, dim=self.embeding_dim),
#         # ]
#         #
#         # # 添加schema
#         # schema = CollectionSchema(
#         #     fields,
#         #     enable_dynamic_field=True,
#         # )
#         # # 创建collection
#         # self.vs.col = Collection(self.kb_name, schema)
#         #
#         # # 创建index
#         # self.vs.col.create_index(
#         #     field_name="vector",
#         #     index_params = self.index_params,
#         # )

#         # schema = self.client.create_schema(
#         #     enable_dynamic_field=True,
#         # )
#         # schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, auto_id=True)
#         # schema.add_field(field_name="source", datatype=DataType.VARCHAR, max_length=2048)
#         # schema.add_field(field_name="file_id", datatype=DataType.VARCHAR, max_length=2048)
#         # schema.add_field(field_name="file_name", datatype=DataType.VARCHAR, max_length=2048)
#         # schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=40960)
#         # schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=self.embeding_dim)
#         # index_params = self.client.prepare_index_params()
#         # index_params.add_index(
#         #     field_name="id"
#         # )
#         # index_params.add_index(
#         #     field_name="vector",
#         #     index_type=self.index_type,
#         #     metric_type=self.metric_type,
#         # )
#         # index_params.add_index(
#         #     field_name="text"
#         # )
#         #
#         # self.client.create_collection(
#         #     collection_name=self.kb_name,
#         #     schema=schema,
#         #     index_params=index_params
#         # )

#         self.vs = Milvus(
#             embedding_function=self.embeding_fn,
#             collection_name=self.kb_name,
#             connection_args=self.connection_args,
#             index_params=self.index_params,
#             search_params=self.search_params,
#         )

#     def drop_kb(self):
#         '''
#         删除知识库，不存在则报错
#         :return:
#         '''
#         # Dropping a KB is equivalent to deleting a collection
#         try:
#             if self.vs.col:
#                 self.vs.col.release()
#                 self.vs.col.drop()
#             else:
#                 logger.info(f"Collection {self.kb_name} does not exist.")
#         except ValueError as e:
#             if not str(e) == f"Collection {self.kb_name} does not exist.":
#                 raise e

#     def is_file_exist(self, kb_name: str, kb_file: KnowledgeFile):
#         try:
#             if self.vs.col:
#                 id_list = [item.get("pk") for item in
#                            self.vs.col.query(expr=f'file_id == "{kb_file.file_id}"', output_fields=["pk"])]
#                 if len(id_list) == 0:
#                     return False
#                 else:
#                     return True
#         except Exception as e:
#             logger.debug(f"Cannot connect to collection [{kb_name}], add file anyway.")
#             return False


#     def add_files(self, kb_files: List[KnowledgeFile], **kwargs):
#         '''
#         给定知识库中添加文件，可以添加一个或者多个
#         :param kb_files:
#         :param kwargs:
#         :return:
#         '''
#         import time
#         start_time = time.perf_counter()

#         doc_infos = []
#         for kb_file in kb_files:
#             if not self.is_file_exist(kb_file.kb_name, kb_file):
#                 kb_file_docs = []
#                 data = kb_file.load_file()
#                 logger.debug(f"load file [{kb_file.file_name}], get [{len(data)}] documents.")
#                 # for doc in data:
#                 #     # 创建一个新的 metadata 字典
#                 #     new_metadata = {k: v for k, v in doc.metadata.items() if k in DEFAULT_METADATAS}
#                 #     # 将新的 metadata 字典赋值给 doc.metadata
#                 #     doc.metadata = new_metadata
#                 #     doc.metadata['file_id'] = kb_file.file_id
#                 #     doc.metadata['file_name'] = kb_file.file_name
#                 #     kb_file_docs.append(doc)
#                 logger.debug("Start split documents...")
#                 documents = kb_file.split_documents(
#                     data,
#                     chunk_size=self.chunk_size,
#                     overlap_size=self.overlap_size,
#                 )
#                 if len(documents) == 0:
#                     raise ValueError(
#                         f"Cannot load data from file {kb_file.file_name}, please check the file type or format.")
#                 logger.debug(f"After split documents, get [{len(documents)}] documents...")
#                 doc_infos.extend(documents)
#             else:
#                 logger.warning(f"File [{kb_file.file_name}] exist already. Skipped.")

#         end_time1 = time.perf_counter()
#         logger.debug(f"After load files time: {end_time1 - start_time} seconds")
#         if len(doc_infos) == 0:
#             return

#         # text_splitter = self.get_text_splitter()
#         # documents = text_splitter.split_documents(doc_infos)
#         # if len(documents) == 0:
#         #     raise ValueError(f"Cannot load data from file {kb_files[0].file_name}, maybe it's a photocopied file.")
#         end_time2 = time.perf_counter()
#         logger.debug(f"After split time: {end_time2 - start_time} seconds")

#         self.vs = self.vs.from_documents(
#             doc_infos,
#             embedding=self.embeding_fn,
#             collection_name=self.kb_name,
#             connection_args=self.connection_args,
#             index_params=self.index_params,
#             search_params=self.search_params,
#         )
#         end_time3 = time.perf_counter()
#         logger.debug(f"After add_documents [{len(doc_infos)}] docs, spent time: {end_time3 - start_time} seconds")
#         return self.vs

#     def del_doc_by_ids(self, ids: List[str]) -> bool:
#         self.vs.col.delete(ids=ids)
#         return True

#     def clear_vs(self):
#         # Clearing the vector store might be equivalent to dropping and recreating the collection
#         self.drop_kb()

#     def delete_file(self, kb_file: KnowledgeFile, **kwargs):
#         if self.vs.col:
#             id_list = [item.get("pk") for item in
#                        self.vs.col.query(expr=f'file_id == "{kb_file.file_id}"', output_fields=["pk"])]
#             self.vs.col.delete(expr=f'pk in {id_list}')

#     def do_search(self, query: str, params: Dict) -> List[Document]:
#         logger.debug(f"start searching kb_name [{self.kb_name}] with params: [{params}]")

#         if not params:
#             logger.error(f"No params found in params_dict: [{params}].")
#             raise ValueError("No params found in params_dict.")

#         k = params["query_param"].get("k") or DEFAULT_K
#         score_threshold = params["query_param"].get("score_threshold") or DEFAULT_SCORE_THRESHOLD
#         fetch_k = params["query_param"].get("fetch_k") or DEFAULT_FETCH_K
#         lambda_mult = params["query_param"].get("lambda_mult") or DEFAULT_LAMBDA_MULT
#         search_type = params["query_param"].get("search_type") or DEFAULT_SEARCH_TYPE
#         search_kwargs = {
#             "k": k,
#         }

#         file_id = params["query_param"].get("file_id")
#         if file_id:
#             # 如果有file_id，说明是针对文件问答
#             logger.info(f"chat with file: [{file_id}]")
#             search_kwargs.update({
#                 "expr": f"file_id == '{file_id}'"
#             })

#         search_type = getattr(SearchType, search_type.upper())
#         if SearchType.MMR == search_type:
#             search_kwargs.update({
#                 "fetch_k": fetch_k,
#                 "lambda_mult": lambda_mult,
#             })
#         elif SearchType.SIMILARITY_SCORE_THRESHOLD == search_type:
#             # logger.error(f"search_type of {search_type} is not implement yet.")
#             # raise ValueError(f"search_type of {search_type} is not implement yet.")
#             search_kwargs.setdefault("score_threshold", score_threshold)

#         logger.info(f"search args: [{search_kwargs}]")

#         query_embedding = self.vs.embedding_func.embed_query(query)
#         logger.debug(f"query: [{query}]; embedding: [{query_embedding}]")

#         # Cannot support similarity_score_threshold, change to use custom_retriever
#         # retriever = self.vs.as_retriever(
#         #     search_type=search_type,
#         #     search_kwargs=search_kwargs
#         # )
#         # result = retriever.get_relevant_documents(query)

#         from pkg.plugins.knowledge_base.custom_retriever import CustomRetriever
#         custom_retriever = CustomRetriever(
#             vectorstore=self.vs,
#             search_type=search_type,
#             search_kwargs=search_kwargs,
#         )

#         result = custom_retriever.get_relevant_documents(query)

#         return result


# if __name__ == '__main__':

#     params_dict = {
#         "kb_name": "kb_test_1_2",
#         # "vs_type": "milvus",
#         "global_param": {
#             "embed_model": "D:\\Program Files\\Python311\\workspace\\embeddings\\text2vec-base-chinese",
#         },
#         "storage_param": {
#             "chunk_size": 200,
#             "overlap_size": 20,
#             "distance_strategy": "cosine",
#         },
#         "query_param": {
#             "k": 5,
#             "score_threshold": 0.5,
#             "fetch_k": 20,
#             "lambda_mult": 0.5,
#             "search_type": "similarity",
#             "prompt_template": DEFAULT_PROMPT_TEMPATE,
#             "file_id": "docx_3",
#         }
#     }
#     milvus_kb = MilvusKBService(params_dict)

#     milvus_kb.create_kb()

#     milvus_kb.add_files(
#         [
#             KnowledgeFile(
#                 kb_name="kb_test_1_2",
#                 file_name="./tests/人工智能.html",
#                 file_id="htm_1",
#             ),
#             # KnowledgeFile(
#             #     kb_name="kb_test_1_1",
#             #     file_name="./tests/中国地理.htm",
#             #     file_id="html_1",
#             # ),
#             # KnowledgeFile(
#             #     kb_name="kb_test_1_1",
#             #     file_name="./tests/公司.jsonl",
#             #     file_id="jsonl_1",
#             # ),
#             # KnowledgeFile(
#             #     kb_name="kb_test_1_1",
#             #     file_name="./tests/中国地理.json",
#             #     file_id="json_1",
#             # ),
#             # KnowledgeFile(
#             #     kb_name="kb_test_1_1",
#             #     file_name="./tests/yuan2_readme.md",
#             #     file_id="md_1",
#             # ),
#             # KnowledgeFile(
#             #     kb_name="kb_test_1_1",
#             #     file_name="./tests/人工智能.pptx",
#             #     file_id="pptx_1",
#             # ),
#             # KnowledgeFile(
#             #     kb_name="kb_test_1_1",
#             #     file_name="./tests/公司.xml",
#             #     file_id="xml_1",
#             # ),
#             # KnowledgeFile(
#             #     kb_name="kb_test_1_1",
#             #     file_name="./tests/demo.mobi",
#             #     file_id="mobi_1",
#             # ),
#             # KnowledgeFile(
#             #     kb_name="kb_test_1_1",
#             #     file_name="./tests/人工智能时代与人类未来.epub",
#             #     file_id="epub_1",
#             # ),
#             # KnowledgeFile(
#             #     kb_name="kb_test_1_1",
#             #     file_name="./tests/苏轼.txt",
#             #     file_id="txt_1",
#             # ),
#             # KnowledgeFile(
#             #     kb_name="kb_test_1_1",
#             #     file_name="./tests/苏轼.pdf",
#             #     file_id="pdf_1",
#             # ),
#             # KnowledgeFile(
#             #     kb_name="kb1_3",
#             #     file_name="./tests/苏轼.docx",
#             #     file_id="docx_1",
#             # )
#         ]
#     )

#     result = milvus_kb.do_search(
#         query="苏轼的词风？",
#         params=params_dict,
#     )

#     milvus_kb.delete_file(
#         KnowledgeFile(
#             kb_name="kb1_2",
#             file_name="./tests/苏轼.docx",
#             file_id="docx_3",
#         )
#     )

#     milvus_kb.drop_kb()
#     print("Done!")
