import requests
import re
import json
# from pkg.logger import Log

# log = Log()

class SerperClient:
    def __init__(self, serper_api_key):
        # Load configuration from config.yaml file
        # config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
        # with open(config_path, 'r') as file:
        #     config = yaml.safe_load(file)

        # Set up the URL and headers for the Serper API
        self.url = "https://google.serper.dev/search"
        self.headers = {
            "X-API-KEY": "93e1794529eb157bd7da30cbdbd723e6c5a20bee",  # API key from config file
            "Content-Type": "application/json"
        }
        self.serper_api_key = serper_api_key
        self.session = requests.Session()

    def serper(self, query: str):
        # Configure the query parameters for Serper API
        # serper_settings = {"q": query, "page": 2}
        serper_settings = {"q": query, "page": 1}

        # Check if the query contains Chinese characters and adjust settings accordingly
        if self._contains_chinese(query):
            serper_settings.update({"gl": "cn", "hl": "zh-cn",})

        payload = json.dumps(serper_settings).encode('utf-8')

        # Perform the POST request to the Serper API and return the JSON response
        response = requests.request("POST", self.url, headers=self.headers, data=payload)

        # params = {
        #     "engine": "google",
        #     "q": query,
        #     "api_key": self.serper_api_key
        # }
        # response = requests.get("https://serpapi.com/search", params=params, verify=False)

        return response.json()

    def _contains_chinese(self, query: str):
        # Check if a string contains Chinese characters using a regular expression
        pattern = re.compile(r'[\u4e00-\u9fff]+')
        return bool(pattern.search(query))

    def extract_components(self, serper_response: dict):
        # Initialize lists to store the extracted components
        titles, links, snippets = [], [], []

        SITE_NAME_MAPPING = {
            "zhihu": "知乎",
            "baidu": "百度",
            "csdn": "CSDN",
            "jianshu": "简书",
            "sina": "新浪",
            "163": "网易",
            "qq": "腾讯",
            "weibo": "微博",
            "sohu": "搜狐",
            "bilibili": "哔哩哔哩",
            "douban": "豆瓣",
        }

        # Iterate through the 'organic' section of the response and extract information
        for item in serper_response.get("organic", []):
            link = item.get("link", "").replace("baike.baidu.hk", "baike.baidu.com")
            if link in links:
                continue

            # 获取网站图标和名称
            title = item.get("title", "")
            # log.info(f"title:{title}")
            icon_url, site_name = None, "网页搜索"
            # 获取网站名称
            try:
                # 从title中获取
                domain = title.split("-")[-1].strip() or title.split("_")[-1].strip() or title.split(" - ")[-1].strip() or title.split(" | ")[-1].strip()
                if len(domain) < 10:
                    site_name = domain
                        
                # 从URL获取
                else:
                    site_name = link.split("//")[1].split("/")[0].split(".")[1]
                    for part in site_name.split("."):
                        if part in SITE_NAME_MAPPING:
                            site_name = SITE_NAME_MAPPING[part]
                            break
                            
            except Exception:
                pass

            # 查找icon
            base_url = link.split("//")[0] + "//" + link.split("//")[1].split("/")[0]
            icon_url = base_url + "/favicon.ico"
            
            titles.append(item.get("title", ""))
            links.append(link)
            snippets.append(item.get("snippet", ""))
            # 在serper_response的每个item中添加site_name和icon_url
            item["site_name"] = site_name
            item["icon_url"] = icon_url
            # print('item:', item)

        # Retrieve additional information from the response
        query = serper_response.get("searchParameters", {}).get("q", "")
        count = len(links)
        language = "zh-cn" if self._contains_chinese(query) else "en-us"

        # Organize the extracted data into a dictionary and return
        # print('serper_response:', serper_response)
        output_dict = {
            'query': query, 
            'language': language, 
            'count': count, 
            'titles': titles, 
            'links': links, 
            'snippets': snippets,
            'search_response':serper_response
        }

        return output_dict

# Usage example
if __name__ == "__main__":
    client = SerperClient("")
    query = "What happened to Silicon Valley Bank"
    response = client.serper(query)
    # print(response)
    components = client.extract_components(response)
    # print(components)
