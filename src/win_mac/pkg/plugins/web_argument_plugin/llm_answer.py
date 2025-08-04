import time
import re
from pkg.plugins.web_argument_plugin.fetch_web_content import WebContentFetcher
from pkg.plugins.web_argument_plugin.retrieval import EmbeddingRetriever


class LLMAnswer:
    # TOP_K = 3  # Top K documents to retrieve

    def __init__(self, paras_dict):
        # # old: Load configuration from a YAML file
        # config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
        # with open(config_path, 'r') as file:
        #     self.config = yaml.safe_load(file)
        # self.model_name = self.config["model_name"]
        # self.api_key = self.config["openai_api_key"]

        #从网页加载参数
        self.TOP_K = paras_dict.get("retrieve_topk", 3)    # Top K documents to retrieve
        self.model_name = ""
        self.template = paras_dict.get("template", "说明：您是一位认真的研究者。使用提供的网络搜索结果，对给定的问题写一个全面而详细的回复。")

    def _format_reference(self, relevant_docs_list, link_list):
        # Format the references from the retrieved documents for use in the prompt
        self.TOP_K = min(self.TOP_K, len(relevant_docs_list))
        reference_url_list = [(relevant_docs_list[i].metadata)['url'] for i in range(self.TOP_K)]
        reference_content_list = [relevant_docs_list[i].page_content for i in range(self.TOP_K)]

        # # 去除重复内容
        # reference_content_list_new = []
        # reference_url_list_new = []
        # for i in range(self.TOP_K):
        #     if reference_content_list[i] not in reference_content_list_new:
        #         reference_content_list_new.append(reference_content_list[i])
        #         reference_url_list_new.append(reference_url_list[i])
        # reference_url_list = reference_url_list_new
        # reference_content_list = reference_content_list_new

        try:
            reference_index_list = [link_list.index(link)+1 for link in reference_url_list]
            rearranged_index_list = self._rearrange_index(reference_index_list)
        except:
            rearranged_index_list = [i+1 for i in range(len(reference_url_list))]

        # Create a formatted string of references
        formatted_reference = "\n"
        for i in range(len(reference_url_list)):
            reference_content = re.sub(r"(\[(\d+)\])|(\[(\d+)-(\d+)\])", r'', reference_content_list[i])
            formatted_reference += ('Webpage[' + str(rearranged_index_list[i]) + '], url: ' + reference_url_list[i] + ':\n' + reference_content + '\n\n')
            # formatted_reference += ('Webpage[' + str(rearranged_index_list[i]) + '], url: ' + reference_url_list[i] + ':\n' + reference_content_list[i] + '\n\n\n')
        return formatted_reference

    def _rearrange_index(self, original_index_list):
        # Rearrange indices to ensure they are unique and sequential
        index_dict = {}
        rearranged_index_list = []
        for index in original_index_list:
            if index not in index_dict:
                index_dict.update({index: len(index_dict)+1})
                rearranged_index_list.append(len(index_dict))
            else:
                rearranged_index_list.append(index_dict[index])
        return rearranged_index_list


# Example usage
if __name__ == "__main__":
    paras_dict = {}
    content_processor = LLMAnswer(paras_dict)
    query = "What happened to Silicon Valley Bank"
    output_format = "" # User can specify output format
    profile = "" # User can define the role for LLM

    # Fetch web content based on the query
    web_contents_fetcher = WebContentFetcher(query)
    web_contents, serper_response = web_contents_fetcher.fetch()

    # Retrieve relevant documents using embeddings
    retriever = EmbeddingRetriever()
    relevant_docs_list = retriever.retrieve_embeddings(web_contents, serper_response['links'], query)
    formatted_relevant_docs = content_processor._format_reference(relevant_docs_list, serper_response['links'])
    print(formatted_relevant_docs)

    # Measure the time taken to get an answer from the LLM model
    start = time.time()