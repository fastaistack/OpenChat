import re
from langchain.utilities.bing_search import BingSearchAPIWrapper
# Bing 搜索必备变量
# 使用 Bing 搜索需要使用 Bing Subscription Key,需要在azure port中申请试用bing search
# 具体申请方式请见
# https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/create-bing-search-service-resource
# 使用python创建bing api 搜索实例详见:
# https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/quickstarts/rest/python
# 注意不是bing Webmaster Tools的api key，
# 此外，如果是在服务器上，报Failed to establish a new connection: [Errno 110] Connection timed out，是因为服务器加了防火墙，需要联系管理员加白名单


class BingAPIClient:
    def __init__(self, bing_subscription_key):
        self.bing_search_url = "https://api.bing.microsoft.com/v7.0/search"
        self.bing_subscription_key = bing_subscription_key

    def _contains_chinese(self, query: str):
        # Check if a string contains Chinese characters using a regular expression
        pattern = re.compile(r'[\u4e00-\u9fff]+')
        return bool(pattern.search(query))

    def bing_search(self, input_text, result_len=10):
        self.input_text = input_text
        self.language = "zh-cn" if self._contains_chinese(self.input_text) else "en-us"
        self.params = {'mkt': self.language}
        search = BingSearchAPIWrapper(bing_subscription_key=self.bing_subscription_key,
                                      bing_search_url=self.bing_search_url,
                                      search_kwargs=self.params)
        return search.results(input_text, result_len)

    def extract_components(self, bing_response):
        # Initialize lists to store the extracted components
        titles, links, snippets = [], [], []

        # Iterate through the 'organic' section of the response and extract information
        for item in bing_response:
            link = item.get("link", "").replace("baike.baidu.hk", "baike.baidu.com")
            if link == "" or link in links:
                continue
            titles.append(item.get("title", ""))
            links.append(link)
            snippets.append(item.get("snippet", ""))

        # Organize the extracted data into a dictionary and return
        output_dict = {
            'query': self.input_text,
            'language': self.language,
            'count': len(links),
            'titles': titles,
            'links': links,
            'snippets': snippets,
            'search_response': {"organic":bing_response, "searchParameters": {"q": self.input_text, "type": "search", "page": 1, "engine": "bing_bs4"}}
        }

        return output_dict


if __name__ == "__main__":
    # 输出结构如下
    # [{
    #      'snippet': 'Lady Alice. Pink Lady <b>apples</b> aren’t the only lady in the apple family. Lady Alice <b>apples</b> were discovered growing, thanks to bees pollinating, in Washington. They are smaller and slightly more stout in appearance than other varieties. Their skin color appears to have red and yellow stripes running from stem to butt.',
    #      'title': '25 Types of Apples - Jessica Gavin',
    #      'link': 'https://www.jessicagavin.com/types-of-apples/'},
    #  {
    #      'snippet': '<b>Apples</b> can do a lot for you, thanks to plant chemicals called flavonoids. And they have pectin, a fiber that breaks down in your gut. If you take off the apple’s skin before eating it, you won ...',
    #      'title': 'Apples: Nutrition &amp; Health Benefits - WebMD',
    #      'link': 'https://www.webmd.com/food-recipes/benefits-apples'}]

    bing_api = BingAPIClient(bing_subscription_key="")
    results = bing_api.bing_search('故宫简介')
    output_dict = bing_api.extract_components(results)
    print(output_dict)

