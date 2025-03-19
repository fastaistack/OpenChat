import threading
import time
import re
from pkg.plugins.web_argument_plugin.web_crawler import WebScraper
from pkg.plugins.web_argument_plugin.serper_service import SerperClient
from pkg.plugins.web_argument_plugin.bing_bs4_service import BingBs4Client


class WebContentFetcher:
    def __init__(self, query, serper_api_key):
        # Initialize the fetcher with a search query
        self.query = query
        self.web_contents = []  # Stores the fetched web contents
        self.error_urls = []  # Stores URLs that resulted in an error during fetching
        self.web_contents_lock = threading.Lock()  # Lock for thread-safe operations on web_contents
        self.error_urls_lock = threading.Lock()  # Lock for thread-safe operations on error_urls
        self.serper_api_key = serper_api_key

    def _web_crawler_thread(self, thread_id: int, urls: list):
        # Thread function to crawl each URL
        try:
            print(f"Starting web crawler thread {thread_id}")
            start_time = time.time()

            url = urls[thread_id]
            scraper = WebScraper()
            # content = scraper.scrape_url(url, 0)
            content = scraper.scrape_url_trafilatura(url)  #采用trafilatura剔除网页干扰信息，实际与bs4解析效果差不多

            # # If the scraped content is too short, try extending the crawl rules
            ## 该扩充会带来很多段落重复，因此慎用
            # if 0 < len(content) < 800:
            #     content = scraper.scrape_url(url, 1)

            # If the content length is sufficient, add it to the shared list
            # if len(content) > 300:  #英文检索要求字数比较多
            # if len(content) > 100:  #更适用中文
            #     with self.web_contents_lock:
            #         self.web_contents.append({"url": url, "content": content})

            # 全部获取，然后再根据字数筛选，若字数不满足，用snippets填充
            with self.web_contents_lock:
                 #页面解码错误，非英文、数字、中文、空格字符太多，改为空
                content_filter = re.sub(r'([^a-zA-Z0-9\u4E00-\u9FA5 ])', r'', content)
                if len(content) > 2*len(content_filter):
                    content = ''
                self.web_contents.append({"url": url, "content": content})

            end_time = time.time()
            print(f"Thread {thread_id} completed! Time consumed: {end_time - start_time:.2f}s")

        except Exception as e:
            # Handle any exceptions, log the error, and store the URL
            with self.error_urls_lock:
                self.error_urls.append(url)
            self.web_contents.append({"url": url, "content": ""})
            print(f"Thread {thread_id}: Error crawling {url}: {e}")

    def _serper_launcher(self):
        # Function to launch the Serper client and get search results
        serper_client = SerperClient(self.serper_api_key)
        serper_results = serper_client.serper(self.query)
        return serper_client.extract_components(serper_results)

    def _bing_bs4_launcher(self):
        # Function to launch the Serper client and get search results
        bing_bs4_client = BingBs4Client()
        results = bing_bs4_client.bing_search(self.query)
        return bing_bs4_client.extract_components(results)

    def _crawl_threads_launcher(self, url_list):
        # Create and start threads for each URL in the list
        threads = []
        for i in range(len(url_list)):
            thread = threading.Thread(target=self._web_crawler_thread, args=(i, url_list))
            threads.append(thread)
            thread.start()
        # Wait for all threads to finish execution
        for thread in threads:
            thread.join()

    def fetch(self, style_search):
        # Main method to fetch web content based on the query
        if style_search == "serper":
            search_response = self._serper_launcher()
        elif style_search == "bing_api":
            search_response = {}
        else:
            search_response = self._bing_bs4_launcher()
            if search_response.get("search_response").get("organic", []) == []:
                return [], "网络检索结果为空，请检查网络是否通畅或检查拼写或尝试其他关键字"

        if search_response:
            url_list = search_response["links"]
            self._crawl_threads_launcher(url_list)
            # Reorder the fetched content to match the order of URLs
            ordered_contents = [
                next((item['content'] for item in self.web_contents if item['url'] == url), '')
                for url in url_list
            ]

            # 检索结果为空或字数较少的url，用api获取的snippets替代
            for i in range(len(ordered_contents)):
                if len(ordered_contents[i]) < len(search_response['snippets'][i]):
                    ordered_contents[i] = search_response['snippets'][i]

            return ordered_contents, search_response
        return [], {}


# # Example usage
# if __name__ == "__main__":
#     fetcher = WebContentFetcher("What happened to Silicon Valley Bank", "")
#     contents, serper_response = fetcher.fetch()
#
#     print(serper_response)
#     print(contents, '\n\n')
    