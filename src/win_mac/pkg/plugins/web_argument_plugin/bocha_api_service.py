import requests
import json
import re
from pkg.logger import Log

log = Log()
class BochaClient:
    def __init__(self, bocha_api_key):
        # Set up the URL and headers for the bocha API
        self.url = "https://api.bochaai.com/v1/web-search"
        self.headers = {
            'Authorization': 'Bearer ' + bocha_api_key,
            'Content-Type': 'application/json'
        }
        self.bocha_api_key = bocha_api_key

    def _contains_chinese(self, query: str):
        # Check if a string contains Chinese characters using a regular expression
        pattern = re.compile(r'[\u4e00-\u9fff]+')
        return bool(pattern.search(query))

    def bocha(self, query):
        # Configure the query parameters for bocha API
        payload = json.dumps({
            "query": query,
            "count": 20,
            "summary": True,
            "answer": True,
            "stream": False
        }).encode('utf-8')

        # Perform the POST request to the bocha API and return the JSON response
        response = requests.request("POST", self.url, headers=self.headers, data=payload)
        return response.json()

    def extract_components(self, bocha_response: dict):
        if bocha_response.get("code", -1) != 200:
            return bocha_response  # api 调用失败，直接返回

        # Initialize lists to store the extracted components
        titles, links, snippets, summarys = [], [], [], []
        source_response = {}
        source_response['organic'] = []

        # Iterate through the 'organic' section of the response and extract information
        for item in bocha_response.get("data", {}).get("webPages",{}).get("value", []):
            link = item.get("url", "").replace("baike.baidu.hk", "baike.baidu.com")
            if link in links:
                continue
            titles.append(item.get("name", ""))
            links.append(link)
            snippets.append(item.get("snippet", ""))
            summarys.append(item.get("summary", ""))
            item['link'] = link
            item['site_name'] = item.get("siteName", "网页搜索")
            item['icon_url'] = item.get("siteIcon", "")
            log.info(f"icon_url:{item['icon_url']}")
            source_response['organic'].append(item)

        # Retrieve additional information from the response
        query = bocha_response.get("data", {}).get("queryContext", {}).get("originalQuery", "")
        count = len(links)
        language = "zh-cn" if self._contains_chinese(query) else "en-us"

        # Organize the extracted data into a dictionary and return
        output_dict = {
            "code": 200,
            "query": query,
            "language": language,
            "count": count,
            "titles": titles,
            "links": links,
            "snippets": snippets,
            "summarys": summarys,  #当非深度搜索时，直接使用该值
            "search_response": source_response
        }

        return output_dict


# Usage example
if __name__ == "__main__":
    client = BochaClient("sk-f0faa083bfc04e5da6e1d9abb3c67281")
    query = "今天济南天气"
    response = client.bocha(query)
    components = client.extract_components(response)
    # print(components)
    for item in components.get("search_response",{}).get("organic_results", []):
        print(item.get("site_name"), item.get("site_icon"))
