import requests
import json
import re
from bs4 import BeautifulSoup
# from pkg.logger import Log

# log = Log()
class searXNGClient:
    def __init__(self, searxng_url=None):
        # Set up the URL for the SearXNG API
        self.url = searxng_url or "http://114.55.140.90:8080"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Accept-Encoding": "gzip, deflate, br",
            "sec-ch-ua": '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1"
        }

    def _contains_chinese(self, query: str):
        # Check if a string contains Chinese characters using a regular expression
        pattern = re.compile(r'[\u4e00-\u9fff]+')
        return bool(pattern.search(query))

    def searxng(self, query):
        # Configure the query parameters for SearXNG API
        self.input_text = query
        params = {
            "q": query,
            "format": "html"
        }

        # 打印完整的请求 URL
        full_url = f"{self.url}/search"
        # print(f"Request URL: {full_url}")
        # print(f"Request params: {params}")
        # print(f"Request headers: {self.headers}")

        # Perform the GET request to the SearXNG API and return the JSON response
        response = requests.get(full_url, params=params, headers=self.headers)
        
        # 打印响应状态码
        # print(f"Response status code: {response.status_code}")
        # print(f"searxng response: {response.text}")
        
        if params.get("format") == "json":
            results = response.json()
        if params.get("format") == "html":
            response.encoding = 'utf-8'
            html_doc = response.text
            soup = BeautifulSoup(html_doc, 'html.parser')
            results = soup.find("div", id="urls").find_all("article")
            # log.info(f"searxng response: {results}")
        return results

    def extract_components(self, searxng_response: dict):
        # Initialize lists to store the extracted components
        titles, links, snippets = [], [], []
        search_response = {}
        search_response['organic'] = []

        # Iterate through the 'results' section of the response and extract information
        if isinstance(searxng_response, dict):
            for item in searxng_response.get("results", []):
                link = item.get("url", "")
                if link in links:
                    continue
                titles.append(item.get("title", ""))
                links.append(link)
                snippets.append(item.get("content", ""))
                
                # Create a compatible item for the source_response
                organic_item = {
                    'link': link,
                    'title': item.get("title", ""),
                    'snippet': item.get("content", ""),
                    'site_name': item.get("parsed_url", "")[1],
                    'icon_url': item.get("img_src", "")
                }
                search_response['organic'].append(organic_item)

            # Retrieve additional information from the response
            query = searxng_response.get("query", "")
            count = searxng_response.get("number_of_results", len(links))
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
                "search_response": search_response
            }
        else:
            # If the response is in HTML format, parse it using BeautifulSoup
            for item in searxng_response:
                title = item.find("h3").text.strip()
                link = item.find("a")["href"]
                snippet = item.find("p").text.strip()
                # site_name = re.sub(r'^https?://(www\.)?|(\.\w+$)', '', item.find("span", class_="url_i1").text).split('.')[0]
                site_name = item.find("div", class_="engines").find("span").text.strip()
                base_url = link.split("//")[0] + "//" + link.split("//")[1].split("/")[0]
                icon_url = base_url + "/favicon.ico"

                titles.append(title)
                links.append(link)
                snippets.append(snippet)
                # Create a compatible item for the source_response
                organic_item = {
                    'link': link,
                    'title': title,
                    'snippet': snippet,
                    'site_name': site_name if site_name else "网页搜索",
                    'icon_url': None
                }
                search_response['organic'].append(organic_item)

            # Organize the extracted data into a dictionary and return
            output_dict = {
                "code": 200,
                "query": self.input_text,
                "language": "zh-cn",
                "count": len(links),
                "titles": titles,
                "links": links,
                "snippets": snippets,
                "search_response": search_response
            }
            # log.info(f"searxng response: {output_dict}")

        return output_dict


# Usage example
if __name__ == "__main__":
    client = searXNGClient("https://searx.foobar.vip/")
    query = "deepseek"
    response = client.searxng(query) 
    components = client.extract_components(response)
    # print(response)
    print(components)
