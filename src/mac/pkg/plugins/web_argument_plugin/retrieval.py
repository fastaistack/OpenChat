from pkg.plugins.web_argument_plugin.fetch_web_content import WebContentFetcher
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
# from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
import time
# import torch
from langchain_community.embeddings import OllamaEmbeddings,OpenAIEmbeddings
embeddings_model = any

class EmbeddingRetriever:
    # TOP_K = 3  # Number of top K documents to retrieve

    def __init__(self, paras_dict):
        self.retrieve_topk = paras_dict.get("retrieve_topk", 3)
        self.embeddings_model_path = paras_dict.get("embedding_model_path")
        self.TOP_K = 3
        # Initialize the text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=0
        )

    # def retrieve_embeddings(self, contents_list: list, link_list: list, query: str):
    #     # Retrieve embeddings for a given list of contents and a query
    #     metadatas = [{'url': link} for link in link_list]
    #     texts = self.text_splitter.create_documents(contents_list, metadatas=metadatas)

    #     # Create a Chroma database from the documents using specific embeddings
    #     db = Chroma.from_documents(
    #         texts,

    #         # Select one of the models from OpenAIEmbeddings and text2vec-base-chinese to suit your needs:
            
    #         # OpenAIEmbeddings(model='text-embedding-ada-002', openai_api_key=self.config["openai_api_key"])
    #         SentenceTransformerEmbeddings(model_name=self.embeddings_model_path)
    #     )

    #     # Create a retriever from the database to find relevant documents
    #     # retriever = db.as_retriever(search_kwargs={"k": self.TOP_K})
    #     retriever = db.as_retriever()
    #     return retriever.get_relevant_documents(query) # Retrieve and return the relevant documents


    def retrieve_embeddings_noreapt(self, contents_list: list, link_list: list, query: str):
        t1 = time.time()
        # Retrieve embeddings for a given list of contents and a query
        metadatas = [{'url': link} for link in link_list]
        texts = self.text_splitter.create_documents(contents_list, metadatas=metadatas)
        global embeddings_model
        # print(f"self.embeddings_model_path:----------------------------{self.embeddings_model_path}-------------------------------")
        try:
            # raise ValueError(1)
            # if 'client' not in dir(embeddings_model):  #若模型未加载
            #     DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            #     embeddings_model = SentenceTransformerEmbeddings(model_name=self.embeddings_model_path, model_kwargs={'device': DEVICE})
            # Create a Chroma database from the documents using specific embeddings
            # embedding = OpenAIEmbeddings(model = 'BAAI/bge-large-zh-v1.5',
            #                              openai_api_base = 'https://api.siliconflow.cn/v1',
            #                              openai_api_key = 'k-jyjrpgkwlitulmzgfpaabqmhaycobiuzkmvobrbhjsivdayc',
            #                              )
            db = Chroma.from_documents(
                texts,

                # Select one of the models from OpenAIEmbeddings and text2vec-base-chinese to suit your needs:
                # OpenAIEmbeddings(model='text-embedding-ada-002', openai_api_key=self.config["openai_api_key"])
                # embeddings_model
                OllamaEmbeddings(model=self.embeddings_model_path)
                # embedding
            )

            # Create a retriever from the database to find relevant documents
            retriever = db.as_retriever(search_kwargs={"k": len(texts)})
            all_docs = retriever.get_relevant_documents(query)
        except Exception as e:
            print(e)
            all_docs = texts[: len(texts)]  #方法一：直接选取

            # # 方法二，通过加载模型，计算相似度，速度也很慢
            # from similarities import BertSimilarity
            # model = BertSimilarity(model_name_or_path=self.embeddings_model_path)
            #
            # corpus = []
            # for doc in texts:
            #     corpus.append(str(doc.page_content))
            # model.add_corpus(corpus)
            # res = model.most_similar(queries=query, topn=len(texts))
            # all_docs = [texts[key] for key in res[0].keys()]

        # 去重
        relevant_docs_list = []
        relevant_urls_list = []
        for doc in all_docs:
            url = doc.metadata.get("url")  #保证参考文本来着不同URL
            if doc not in relevant_docs_list and url not in relevant_urls_list:
                relevant_docs_list.append(doc)
                relevant_urls_list.append(url)

        self.TOP_K = min(self.retrieve_topk, len(relevant_docs_list))
        print('\nretrieve_embeddings use time:', time.time()-t1)
        return relevant_docs_list[:self.TOP_K]


    # Example usage
if __name__ == "__main__":
    query = "What happened to Silicon Valley Bank"

    # Create a WebContentFetcher instance and fetch web contents
    web_contents_fetcher = WebContentFetcher(query, serper_api_key="")
    web_contents, serper_response = web_contents_fetcher.fetch("serper")

    # Create an EmbeddingRetriever instance and retrieve relevant documents
    paras_dict = {}
    retriever = EmbeddingRetriever(paras_dict)
    relevant_docs_list = retriever.retrieve_embeddings(web_contents, serper_response['links'], query)

    print("\n\nRelevant Documents from VectorDB:\n", relevant_docs_list)
    