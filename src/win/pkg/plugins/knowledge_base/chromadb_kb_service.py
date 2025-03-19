import os
from typing import Any, Dict, List, Tuple

import chromadb
from chromadb.api.types import (
    GetResult,
)
from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from pkg.plugins.knowledge_base.base import (KBService, SupportedVSType, SearchType)
from pkg.plugins.knowledge_base.consts import (
    DEFAULT_VS_PATH,
    DEFAULT_K,
    DEFAULT_SEARCH_TYPE,
    DEFAULT_FETCH_K,
    DEFAULT_PROMPT_TEMPATE,
    DEFAULT_LAMBDA_MULT,
    DEFAULT_SCORE_THRESHOLD,
)
from pkg.logger import Log
from pkg.projectvar import Projectvar
from pkg.plugins.knowledge_base.utils import KnowledgeFile

logger = Log()
pj_vars = Projectvar()


def _get_result_to_documents(get_result: GetResult) -> List[Document]:
    if not get_result['documents']:
        return []

    _metadatas = get_result['metadatas'] if get_result['metadatas'] else [{}] * len(get_result['documents'])

    document_list = []
    for page_content, metadata in zip(get_result['documents'], _metadatas):
        document_list.append(Document(**{'page_content': page_content, 'metadata': metadata}))

    return document_list


def _results_to_docs_and_scores(results: Any) -> List[Tuple[Document, float]]:
    """
    from langchain_community.vectorstores.chroma import Chroma
    """
    return [
        # TODO: Chroma can do batch querying,
        (Document(page_content=result[0], metadata=result[1] or {}), result[2])
        for result in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


class ChromaKBService(KBService):
    client = None
    collection = None
    vs_path = str
    vs = Chroma

    def vs_type(self) -> str:
        return SupportedVSType.CHROMADB

    def do_init(self) -> None:
        # 向量库数据存储在cache_path目录下, 如果vs_path目录不存在，则新建一个
        self.vs_path = os.path.join(pj_vars.get_cache_path(), "chromadb")
        os.makedirs(self.vs_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=self.vs_path or DEFAULT_VS_PATH)
        # self.client = chromadb.PersistentClient(DEFAULT_VS_PATH)
        self.collection = self.client.get_or_create_collection(
            self.kb_name,
            metadata={"hnsw:space": self.distance_strategy.lower()}
        )
        self.vs = Chroma(
            collection_name=self.kb_name,
            embedding_function=self.embeding_fn,
            client=self.client,
        )

    def create_kb(self) -> None:
        '''
        通过client创建知识库
        :return:
        '''
        # In ChromaDB, creating a Knowledge base is equivalent to creating a collection
        self.collection = self.client.get_or_create_collection(
            self.kb_name,
            metadata={"hnsw:space": self.distance_strategy.lower()}
        )

    def drop_kb(self):
        '''
        删除知识库，不存在则报错
        :return:
        '''
        # Dropping a KB is equivalent to deleting a collection in ChromaDB
        try:
            self.client.delete_collection(self.kb_name)
        except ValueError as e:
            if not str(e) == f"Collection {self.kb_name} does not exist.":
                raise e

    def is_file_exist(self, kb_name: str, kb_file: KnowledgeFile):
        result = self.collection.get(where={"source": kb_file.file_name})
        if len(result["ids"]) == 0:
            return False
        else:
            return True

    def add_files(self, kb_files: List[KnowledgeFile], **kwargs):
        '''
        给定知识库中添加文件，可以添加一个或者多个
        :param kb_files:
        :param kwargs:
        :return:
        '''
        import time
        start_time = time.perf_counter()

        doc_infos = []
        for kb_file in kb_files:
            if not self.is_file_exist(kb_file.kb_name, kb_file):
                kb_file_docs = []
                data = kb_file.load_file()
                if kb_file.file_name.endswith(".pdf"):
                    for i in range(len(data)):
                        if len(data[i].page_content.replace(" ", "").replace("\n", "")) <= 10:    ##直接文字提取失败；则提取图片内容                
                            logger.info("启用OCR识别文本")
                            import pytesseract
                            from PIL import Image
                            from io import BytesIO
                            from PyPDF2 import PdfReader

                            pdf_file = kb_file.file_name
                            # inputpdf = PdfReader(open(pdf_file, "rb"))
                            with open(pdf_file, "rb") as file: # 保证文件读写完毕后可以正常释放资源
                                inputpdf = PdfReader(file)
                                page = inputpdf.pages[i]
                                    # text = page.extract_text()
                                    # print(text)
                                for item in page.images:##从图片提取内容
                                    datas = BytesIO()
                                    datas.write(item.data)
                                    image = Image.open(datas)
                                    text = pytesseract.image_to_string(image,lang='chi_sim')
                                    data[i].page_content += text.replace('\n','').replace('\n\n','').replace(" ",'')
                                    image.close()
                                    datas.close()
                                if len(data[i].page_content.replace(" ", "").replace("\n", "").replace("\n\n", ""))<=10:  ##如果不存在图片信息则将PDF转换为图片然后提取PDF内容
                                    from pdf2image import convert_from_path
                                    poppler_path = r"./_internal/poppler-0.89.0/bin"
                                    local_time = time.time()
                                    images = convert_from_path(pdf_path=pdf_file,first_page=i+1, last_page=i+1, poppler_path=poppler_path)
                                    print("Time taken to convert pdf to images: ", time.time() - local_time)
                                    for image in images:
                                        text = pytesseract.image_to_string(image, lang='chi_sim')
                                        data[i].page_content += text.replace('\n','').replace('\n\n','').replace(" ",'')

                logger.debug(f"load file [{kb_file.file_name}], get [{len(data)}] documents.")
                # for doc in data:
                #     # 创建一个新的 metadata 字典
                #     new_metadata = {k: v for k, v in doc.metadata.items() if k in DEFAULT_METADATAS}
                #     # 将新的 metadata 字典赋值给 doc.metadata
                #     doc.metadata = new_metadata
                #     doc.metadata['file_id'] = kb_file.file_id
                #     doc.metadata['file_name'] = kb_file.file_name
                #     kb_file_docs.append(doc)
                logger.debug("Start split documents...")
                documents = kb_file.split_documents(
                    data,
                    chunk_size=self.chunk_size,
                    overlap_size=self.overlap_size,
                )
                if len(documents) == 0:
                    raise ValueError(
                        f"Cannot load data from file {kb_file.file_name}, please check the file type or format.")
                logger.debug(f"After split documents, get [{len(documents)}] documents...")
                doc_infos.extend(documents)
            else:
                logger.warning(f"File [{kb_file.file_name}] exist already. Skipped.")

        end_time1 = time.perf_counter()
        logger.debug(f"After load files time: {end_time1 - start_time} seconds")
        if len(doc_infos) == 0:
            return

        # doc_infos = [doc.metadata.update({
        #     "file_id": kb_file.file_id,
        #     "file_name": kb_file.file_name,
        # }) for kb_file in kb_files for doc in kb_file.file2docs()
        # ]

        # text_splitter = self.get_text_splitter()
        # documents = text_splitter.split_documents(doc_infos)
        # if len(documents) == 0:
        #     raise ValueError(f"Cannot load data from file {kb_files[0].file_name}, maybe it's a photocopied file.")
        end_time2 = time.perf_counter()
        logger.debug(f"After split time: {end_time2 - start_time} seconds")

        self.vs = Chroma.from_documents(
            doc_infos,
            embedding=self.embeding_fn,
            collection_name=self.kb_name,
            client=self.client,
        )
        end_time3 = time.perf_counter()
        logger.debug(f"After add_documents [{len(doc_infos)}] docs, spent time: {end_time3 - start_time} seconds")
        return self.vs

    def get_doc_by_ids(self, ids: List[str]) -> List[Document]:
        get_result: GetResult = self.collection.get(ids=ids)
        return _get_result_to_documents(get_result)

    def del_doc_by_ids(self, ids: List[str]) -> bool:
        self.collection.delete(ids=ids)
        return True

    def clear_vs(self):
        # Clearing the vector store might be equivalent to dropping and recreating the collection
        self.drop_kb()

    def delete_file(self, kb_file: KnowledgeFile, **kwargs):
        return self.collection.delete(where={"file_id": kb_file.file_id})

    def do_search(self, query: str, params: Dict) -> List[Document]:
        logger.debug(f"start searching kb_name [{self.kb_name}] with params: [{params}]")

        if not params:
            logger.error(f"No params found in params_dict: [{params}].")
            raise ValueError("No params found in params_dict.")

        k = params["query_param"].get("k") or DEFAULT_K
        score_threshold = params["query_param"].get("score_threshold") or DEFAULT_SCORE_THRESHOLD
        fetch_k = params["query_param"].get("fetch_k") or DEFAULT_FETCH_K
        lambda_mult = params["query_param"].get("lambda_mult") or DEFAULT_LAMBDA_MULT
        search_type = params["query_param"].get("search_type") or DEFAULT_SEARCH_TYPE
        search_kwargs = {
            "k": k,
        }

        file_id = params["query_param"]["file_id"]
        if file_id:
            # 如果有file_id，说明是针对文件问答
            logger.info(f"chat with file: [{file_id}]")
            search_kwargs.update({
                "filter": {"file_id": file_id}
            })

        search_type = getattr(SearchType, search_type.upper())
        if SearchType.MMR == search_type:
            search_kwargs.update({
                "fetch_k": fetch_k,
                "lambda_mult": lambda_mult,
            })
        elif SearchType.SIMILARITY_SCORE_THRESHOLD == search_type:
            search_kwargs.setdefault("score_threshold", score_threshold)

        logger.info(f"search args: [{search_kwargs}]")

        retriever = self.vs.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )

        result = retriever.get_relevant_documents(query)
        return result


if __name__ == '__main__':
    params_dict = {
        "kb_name": "kb_test_1_1",
        # "vs_type": "chromadb",
        "global_param": {
            "embed_model": "D:\\Program Files\\Python311\\workspace\\embeddings\\text2vec-base-chinese",
        },
        "storage_param": {
            "chunk_size": 200,
            "overlap_size": 20,
            "distance_strategy": "cosine",
        },
        "query_param": {
            "k": 5,
            "score_threshold": 0.5,
            "fetch_k": 20,
            "lambda_mult": 0.5,
            "search_type": "similarity",
            "prompt_template": DEFAULT_PROMPT_TEMPATE,
            "file_id": "txt_1",
        }
    }
    chromadb_kb = ChromaKBService(params_dict)

    chromadb_kb.create_kb()

    chromadb_kb.add_files(
        [
            # KnowledgeFile(
            #     kb_name="kb_test_1_1",
            #     file_name="./tests/人工智能.html",
            #     file_id="html_1",
            # ),
            # KnowledgeFile(
            #     kb_name="kb_test_1_1",
            #     file_name="./tests/中国地理.htm",
            #     file_id="htm_1",
            # ),
            KnowledgeFile(
                kb_name="kb_test_1_1",
                file_name="./tests/公司.jsonl",
                file_id="jsonl_1",
            ),
            KnowledgeFile(
                kb_name="kb_test_1_1",
                file_name="./tests/json.json",
                file_id="json_1",
            ),
            KnowledgeFile(
                kb_name="kb_test_1_1",
                file_name="./tests/demo.json",
                file_id="json_2",
            ),
            KnowledgeFile(
                kb_name="kb_test_1_1",
                file_name="./tests/yuan2_readme.md",
                file_id="md_1",
            ),
            KnowledgeFile(
                kb_name="kb_test_1_1",
                file_name="./tests/人工智能.pptx",
                file_id="pptx_1",
            ),
            KnowledgeFile(
                kb_name="kb_test_1_1",
                file_name="./tests/公司.xml",
                file_id="xml_1",
            ),
            KnowledgeFile(
                kb_name="kb_test_1_1",
                file_name="./tests/demo.mobi",
                file_id="mobi_1",
            ),
            KnowledgeFile(
                kb_name="kb_test_1_1",
                file_name="./tests/人工智能时代与人类未来.epub",
                file_id="epub_1",
            ),
            KnowledgeFile(
                kb_name="kb_test_1_1",
                file_name="./tests/苏轼.txt",
                file_id="txt_1",
            ),
            KnowledgeFile(
                kb_name="kb_test_1_1",
                file_name="./tests/苏轼.pdf",
                file_id="pdf_1",
            ),
            KnowledgeFile(
                kb_name="kb1_3",
                file_name="./tests/苏轼.docx",
                file_id="docx_1",
            )
        ]
    )

    result = chromadb_kb.do_search(
        query="苏轼的词风？",
        params=params_dict,
    )
    print(f"result: [{result}]")

    # chromadb_kb.drop_kb()
    print(f"Done!!!")
