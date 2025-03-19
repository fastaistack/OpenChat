# coding=utf8

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode


class BingBs4Client:
    def __init__(self):
        self.url_pre = 'https://cn.bing.com/search?'
        self.url_post = '&form=ANNNB1&refig=ce14eca2b3514d39a87ccd154e7b8462&sp=1&lq=0&qs=HS&sk=PRES1&sc=7-0&cvid=ce14eca2b3514d39a87ccd154e7b8462'
        self.headers = {
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }

    def bing_search(self, input_text):
        self.input_text = input_text
        self.query = urlencode({"q": self.input_text})
        self.url = self.url_pre + self.query + self.url_post
        html = requests.get(self.url, headers=self.headers)
        html.encoding = 'utf-8'
        html_doc = html.text
        soup = BeautifulSoup(html_doc, 'html.parser')
        results = soup.find("ol", id="b_results").find_all("li")
        return results

    def extract_components(self, results):
        # Initialize lists to store the extracted components
        titles, links, snippets = [], [], []
        search_data = []

        # print('len(results):',len(results))
        for i in range(len(results)):
            row = results[i]
            if len(row.find_all("h2")) == 0:
                continue

            h2 = row.find("h2")
            title = h2.text
            title = title.strip()
            link = h2.find("a").get("href").replace("baike.baidu.hk", "baike.baidu.com")
            if link in links:
                continue
            # print(type(row))
            content = row.find("p")
            if content is None:
                continue
            content_format = content.text

            titles.append(title)
            links.append(link)
            snippets.append(content_format)
            search_data.append({"snippet": content_format, "title": title, "link": link})

        # Organize the extracted data into a dictionary and return
        output_dict = {
            'query': self.input_text,
            'language':"zh-cn",
            'count': len(links),
            'titles': titles,
            'links': links,
            'snippets': snippets,
            'search_response': {"organic":search_data, "searchParameters": {"q": self.input_text, "type": "search", "page": 1, "engine": "bing_bs4"}}
        }
        return output_dict


if __name__ == "__main__":
    bing_bs4 = BingBs4Client()
    results = bing_bs4.bing_search('故宫简介')
    output_dict = bing_bs4.extract_components(results)
    print(output_dict)