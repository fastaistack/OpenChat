from langchain.schema.vectorstore import VectorStoreRetriever
from langchain.schema.document import Document
from langchain.callbacks.manager import (
    CallbackManagerForRetrieverRun,
    AsyncCallbackManagerForRetrieverRun,
)
from typing import List
from pkg.plugins.knowledge_base.base import SearchType


# solve milvus retriever.get_relevant_documents when using "similarity_score_threshold"
# ref: https://github.com/langchain-ai/langchain/issues/19106
class CustomRetriever(VectorStoreRetriever):

    def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:

        if SearchType.SIMILARITY == self.search_type:
            docs = self.vectorstore.similarity_search(query, **self.search_kwargs)
        elif SearchType.SIMILARITY_SCORE_THRESHOLD == self.search_type:
            # the core code is here
            docs_and_similarities = self.vectorstore.similarity_search_with_score(query)

            # you can extend code here, e.g. using `score` variable to filter docs under specific threshold
            threshold = self.search_kwargs.get("score_threshold", 0)
            return [doc for doc, score in docs_and_similarities if score > threshold]
        elif SearchType.MMR == self.search_type:
            docs = self.vectorstore.max_marginal_relevance_search(
                query, **self.search_kwargs
            )
        else:
            raise ValueError(f"search_type of {self.search_type} not allowed.")
        return docs

    async def _aget_relevant_documents(
            self, query: str, *, run_manager: AsyncCallbackManagerForRetrieverRun
    ) -> List[Document]:

        if SearchType.SIMILARITY == self.search_type:
            docs = await self.vectorstore.asimilarity_search(
                query, **self.search_kwargs
            )
        elif SearchType.SIMILARITY_SCORE_THRESHOLD == self.search_type:
            # the core code is here
            docs_and_similarities = (
                await self.vectorstore.asimilarity_search_with_score(query)
            )

            # you can extend code here, e.g. using `score` variable to filter docs under specific threshold
            threshold = self.search_kwargs.get("score_threshold", 0)
            return [doc for doc, score in docs_and_similarities if score > threshold]
        elif SearchType.MMR == self.search_type:
            docs = await self.vectorstore.amax_marginal_relevance_search(
                query, **self.search_kwargs
            )
        else:
            raise ValueError(f"search_type of {self.search_type} not allowed.")
        return docs

