import zipfile
from pathlib import Path
from langchain_core.documents import Document

from langchain_community.document_loaders.base import BaseLoader

from langchain_community.document_loaders import UnstructuredXMLLoader


class CustomOFDLoader(BaseLoader):

    def __init__(self, file_path: str):
        self.file_path = Path(file_path).resolve()
    def load(self) -> Document:
        # TODO: load custom ofd file
        #将ofd文件解压成xml文件，利用xml解析器进行解析
        with zipfile.ZipFile(self.file_path, "r") as zip_ref:
            for file in zip_ref.namelist():
                zip_ref.extract(file, r"./extracted")

        loader=UnstructuredXMLLoader(r"./extracted/OFD.xml")

        return loader.load()