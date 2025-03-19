from __future__ import annotations

import ast
import os
import re
import importlib
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    HTMLHeaderTextSplitter,
)
from pkg.plugins.knowledge_base.text_splitters import CustomRecursiveJsonSplitter
from pathlib import Path
import json
from typing import (
    Callable,
    Dict,
    Generator,
    List,
)
from concurrent.futures import ThreadPoolExecutor, as_completed

import chardet

from pkg.logger import Log

logger = Log()


def run_in_thread_pool(
        func: Callable,
        params: List[Dict] = [],
) -> Generator:
    '''
    在线程池中批量运行任务，并将运行结果以生成器的形式返回。
    请确保任务中的所有操作是线程安全的，任务函数请全部使用关键字参数。
    '''
    tasks = []
    with ThreadPoolExecutor() as pool:
        for kwargs in params:
            thread = pool.submit(func, **kwargs)
            tasks.append(thread)

        for obj in as_completed(tasks):
            yield obj.result()

DEFAULT_METADATAS = ['source', 'file_id', 'file_name', 'text', 'vector', 'pk']

LOADER_DICT = {
    "BSHTMLLoader": ['.html', '.htm'],
    # "MHTMLLoader": ['.mhtml'],
    "UnstructuredMarkdownLoader": ['.md'],
    "CustomJSONLoader": [".json", ".jsonl"],
    # "CSVLoader": [".csv"],
    # "FilteredCSVLoader": [".csv"], 如果使用自定义分割csv
    "PyMuPDFLoader": [".pdf"],  # 解决PyPDFLoader报错：https://github.com/py-pdf/pypdf/issues/1756; 影印版暂不支持
    "UnstructuredFileLoader": ['.docx'],  # using CustomDoc2txtLoader for doc in linux
    # "RapidOCRPPTLoader": ['.ppt', '.pptx', ],
    # "RapidOCRLoader": ['.png', '.jpg', '.jpeg', '.bmp'],
    "TextLoader": ['.txt'],
    # "UnstructuredEmailLoader": ['.eml', '.msg'],
    "UnstructuredEPubLoader": ['.epub'],
    "CustomMobiLoader": ['.mobi'],  # mobi，陈曦
    # "UnstructuredExcelLoader": ['.xlsx', '.xls', '.xlsd'],
    # "NotebookLoader": ['.ipynb'],
    # "UnstructuredODTLoader": ['.odt'],
    # "PythonLoader": ['.py'],
    # "UnstructuredRSTLoader": ['.rst'],
    # "UnstructuredRTFLoader": ['.rtf'],
    # "SRTLoader": ['.srt'],
    # "TomlLoader": ['.toml'],
    # "UnstructuredTSVLoader": ['.tsv'],
    # "UnstructuredWordDocumentLoader": ['.docx', '.doc'],
    "UnstructuredXMLLoader": ['.xml'],
    "UnstructuredPowerPointLoader": ['.pptx'],
    # "EverNoteLoader": ['.enex'],
}
SUPPORTED_EXTS = [ext for sublist in LOADER_DICT.values() for ext in sublist]


# patch json.dumps to disable ensure_ascii
def _new_json_dumps(obj, **kwargs):
    kwargs["ensure_ascii"] = False
    return _origin_json_dumps(obj, **kwargs)


if json.dumps is not _new_json_dumps:
    _origin_json_dumps = json.dumps
    json.dumps = _new_json_dumps


def get_LoaderClass(file_extension):
    for LoaderClass, extensions in LOADER_DICT.items():
        if file_extension in extensions:
            return LoaderClass


def get_loader(loader_name: str, file_path: str, loader_kwargs: Dict = None):
    '''
    根据loader_name和文件路径或内容返回文档加载器, 后续可扩展。
    '''
    loader_kwargs = loader_kwargs or {}
    try:
        if loader_name in ["CustomMobiLoader", "CustomJSONLoader"]:
            document_loaders_module = importlib.import_module('pkg.plugins.knowledge_base.document_loaders')
        else:
            document_loaders_module = importlib.import_module('langchain_community.document_loaders')
        DocumentLoader = getattr(document_loaders_module, loader_name)
    except Exception as e:
        msg = f"Extract file [{file_path}] using loader [{loader_name}] failed, error message：[{e}]"
        logger.error(f'{e.__class__.__name__}: {msg}')
        document_loaders_module = importlib.import_module('langchain_community.document_loaders')
        DocumentLoader = getattr(document_loaders_module, "UnstructuredFileLoader")

    if loader_name == "UnstructuredFileLoader":
        loader_kwargs.setdefault("autodetect_encoding", True)
    elif loader_name in ["TextLoader", "CSVLoader"]:
        if not loader_kwargs.get("encoding"):
            # 如果未指定 encoding，自动识别文件编码类型，避免langchain loader 加载文件报编码错误
            with open(file_path, 'rb') as struct_file:
                encode_detect = chardet.detect(struct_file.read())
            if encode_detect is None:
                encode_detect = {"encoding": "utf-8"}
            loader_kwargs["encoding"] = encode_detect["encoding"]
    elif loader_name in ["BSHTMLLoader"]:
        if not loader_kwargs.get("open_encoding"):
            # 如果未指定 encoding，自动识别文件编码类型，避免langchain loader 加载文件报编码错误
            with open(file_path, 'rb') as struct_file:
                encode_detect = chardet.detect(struct_file.read())
            if encode_detect is None:
                encode_detect = {"encoding": "utf-8"}
            loader_kwargs["open_encoding"] = encode_detect["encoding"]

    elif loader_name == "CustomJSONLoader":
        if os.path.splitext(file_path)[-1].lower() == ".jsonl":
            loader_kwargs.setdefault("json_lines", True)

        # loader_kwargs.setdefault("text_content", False)

    loader = DocumentLoader(file_path, **loader_kwargs)
    return loader


def pre_process_docs(s):
    # 将2个以上的连续\n替换成\n\n
    s = re.sub(r'\n{2,}', '\n\n', s)
    # 将\t替换成空格
    s = s.replace('\t', ' ')
    return s


class KnowledgeFile:
    def __init__(
            self,
            kb_name: str,
            file_name: str,
            file_id: str,
            loader_kwargs: Dict = {},
    ):
        """
        对应知识库目录中的文件，接收到的文件都是文件路径。
        """
        self.kb_name = kb_name
        self.file_name = str(Path(file_name).as_posix())
        self.file_id = file_id
        self.file_ext = os.path.splitext(file_name)[-1].lower()
        if self.file_ext not in SUPPORTED_EXTS:
            raise ValueError(f"暂未支持的文件格式 [{self.file_name}]")
        self.loader_kwargs = loader_kwargs
        self.docs = None
        self.splitted_docs = None
        self.document_loader_name = get_LoaderClass(self.file_ext)
        self.text_splitter_name = RecursiveCharacterTextSplitter

    def load_file(self, refresh: bool = False):
        if self.docs is None or refresh:
            logger.info(f"[{self.document_loader_name}] used for [{self.file_name}]")
            loader = get_loader(
                loader_name=self.document_loader_name,
                file_path=self.file_name,
                loader_kwargs=self.loader_kwargs
            )
            self.docs = loader.load()
        # logger.debug(f"After load: [{self.docs}]")
        return self.docs

    def post_process_docs(self, docs):
        new_docs = []
        for doc in docs:
            # 创建一个新的 metadata 字典
            new_metadata = {k: v for k, v in doc.metadata.items() if k in DEFAULT_METADATAS}
            # 将新的 metadata 字典赋值给 doc.metadata
            doc.metadata = new_metadata
            doc.metadata['source'] = self.file_name
            doc.metadata['file_id'] = self.file_id
            doc.metadata['file_name'] = self.file_name
            new_docs.append(doc)
        return new_docs

    def split_documents(
            self,
            docs: List,
            chunk_size: int,
            overlap_size: int,
            refresh: bool = None,
    ):
        docs = docs
        if not docs:
            return []

        if self.file_ext == ".md":
            logger.info(f"Using MarkdownHeaderTextSplitter to split file [{self.file_name}]...")
            headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
                ("####", "Header 4"),
            ]

            markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on,
                strip_headers = False,
            )
            # MD splits
            docs = markdown_splitter.split_text(pre_process_docs(docs[0].page_content))

        elif self.file_ext in [".html", ".htm"]:
            logger.info(f"Using HTMLHeaderTextSplitter to split file [{self.file_name}]...")
            headers_to_split_on = [
                ("h1", "Header 1"),
                ("h2", "Header 2"),
                ("h3", "Header 3"),
                ("h4", "Header 4"),
            ]

            html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

            # html splitter
            docs = html_splitter.split_text(pre_process_docs(docs[0].page_content))

        elif self.file_ext in [".json", ".jsonl"]:
            logger.info(f"Using CustomRecursiveJsonSplitter to split file [{self.file_name}]...")
            all_docs = []
            for doc in docs:
                json_splitter = CustomRecursiveJsonSplitter(max_chunk_size=chunk_size)
                content = pre_process_docs(doc.page_content)
                # 判断是否是字典
                if isinstance(ast.literal_eval(content), dict):
                    logger.debug(f"[{self.file_name}] is a dict")
                    texts = [ast.literal_eval(content)]
                elif isinstance(ast.literal_eval(content), list):
                    logger.debug(f"[{self.file_name}] is a list")
                    texts = ast.literal_eval(content)
                else:
                    logger.warning(f"[{self.file_name}] is not a list or dict, please check file.")
                    texts = []
                # create_documents must receive a list as texts
                c_docs = json_splitter.create_documents(texts=texts)

                new_docs = self.post_process_docs(c_docs)
                all_docs.extend(new_docs)
            self.splitted_docs = all_docs

            logger.debug(f"文档切分示例：[{all_docs[0]}]")
            return self.splitted_docs

        else:
            logger.info(f"Using RecursiveCharacterTextSplitter to split file [{self.file_name}]...")
        ##按字符递归拆分
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
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
        )
        # Split
        docs = text_splitter.split_documents(docs)

        if not docs:
            return []

        new_docs = self.post_process_docs(docs)
        logger.debug(f"文档切分示例：[{new_docs[0]}]")
        self.splitted_docs = new_docs
        return self.splitted_docs

