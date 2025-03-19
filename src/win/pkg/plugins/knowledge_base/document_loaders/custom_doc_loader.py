# import os

from win32com.client import Dispatch

import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, Optional, Union, List

from langchain_core.documents import Document

from langchain_community.document_loaders.base import BaseLoader

##导入doc文档，返回Document对象

class CustomdocLoader(BaseLoader):
    def __init__(self, file_path: Union[str, Path],):
        self.file_path = Path(file_path).resolve()

    def load(self) -> Document:
        doc = Document()
        word = Dispatch("Word.Application")
        content = ""
        docs = word.Documents.Open(FileName=str(self.file_path))
        for para in docs.paragraphs:
            content += para.Range.Text

        doc.page_content = content
        doc.metadata = self.file_path

        return doc




# current_dir = os.path.dirname(os.path.abspath(__file__))





# doc = word.Documents.Open(FileName=os.path.join(current_dir, "data/test_doc.doc"))

# for para in doc.paragraphs:
#     print(para.Range.Text)