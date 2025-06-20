
from langchain_community.document_loaders.unstructured import UnstructuredFileLoader
from typing import List
import os
import shutil
import tempfile
import html2text
from shutil import rmtree
from mobi.kindleunpack import unpackBook
from pkg.logger import Log

logger = Log()


class CustomMobiLoader(UnstructuredFileLoader):
    def _get_elements(self) -> List:
        def mobi2text(file_path):
            """Extract mobi file and return path to epub file"""

            tempdir = tempfile.mkdtemp(prefix="mobiex")
            text_content = ""
            logger.info(f'tempdir: {tempdir}')
            if hasattr(file_path, "fileno"):
                tempname = next(tempfile._get_candidate_names()) + ".mobi"
                pos = file_path.tell()
                file_path.seek(0)
                with open(os.path.join(tempdir, tempname), "wb") as outfile:
                    shutil.copyfileobj(file_path, outfile)
                file_path.seek(pos)
                file_path = os.path.join(tempdir, tempname)

            logger.debug("file: %s" % file_path)
            fname_out_html = "book.html"
            unpackBook(file_path, tempdir, epubver="A")
            html_filepath = os.path.join(tempdir, "mobi7", fname_out_html)
            # pdf_filepath = os.path.join(output_base, fname_out_pdf)
            if os.path.exists(html_filepath):
                with open(html_filepath, 'r', encoding='utf-8') as file:
                    html_content = file.read()
                text_content = html2text.html2text(html_content)

                extract_flag = True
            else:
                # raise ValueError(f"Coud not extract from {file_path}")
                extract_flag = False

            if os.path.exists(tempdir):
                rmtree(tempdir)

            return extract_flag, text_content

        # flag, text = mobi2text(self.file_path)

        try:
            logger.info(f'process {self.file_path}')
            # file_name = '.'.join(os.path.basename(self.file_path).split('.')[:-1])
            extract_flag, text = mobi2text(self.file_path)
            if extract_flag:
                logger.info(f'Extracting file_name: [{self.file_path}] done!!!')
            else:
                logger.error(f'Coud not extract from [{self.file_path}]')
                raise ValueError(f'Coud not extract from [{self.file_path}]')
        except Exception as e:
            logger.error(f"Error happened while extract file [{self.file_path}], error message: [{e}]")
            raise ValueError(f"Error happened while extract file [{self.file_path}], error message: [{e}]")

        from unstructured.partition.text import partition_text
        return partition_text(text=text, **self.unstructured_kwargs)


if __name__ == '__main__':
    loader = CustomMobiLoader(file_path="../tests/人工智能时代与人类未来.mobi")
    docs = loader.load()
    print(docs)
