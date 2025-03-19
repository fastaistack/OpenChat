# -*- coding: utf-8  -*-
from pkg.plugins.web_argument_plugin.utils import citation_correction
from pkg.logger import Log
from pkg.database.schemas import ChatMessageInfo
log = Log()


def get_default_settings():
    settings = {
        "retrieve_topk": 3,
        "template": "说明：您是一位认真的研究者。使用提供的网络搜索结果，对给定的问题写一个全面而详细的回复。",
        "embedding_model_id": None,
        "embedding_model_path": "",
        "web_api_key": "",
        "style_search": ""
    }

    return settings


def call(reqeust:ChatMessageInfo, setting:dict, content_setting:dict):
    """
   web检索后处理插件，将模型答案加入引用标号
    Args:
        reqeust: ChatMessageInfo对象，从中获取待检测信息
        setting：输入超参数，包括检索相关超参数，包括 output_answer: llm生成初始答案, relevant_docs_list/serper_response: 检索前处理生成结果
    Returns:
        {"flag": False表示有检索异常情况，返回result异常信息至UI；True表示正常，继续代码
        "result"：返回UI提示，flag为False时输出报错信息
        "setting"：参数结构体，包括"content": 返回UI最终答案, "refs": 参考链接及摘要, "peopleAlsoAsk": 感兴趣话题
        }
    """
    input_query = reqeust.message
    output_answer = content_setting.get("output_answer", "")
    relevant_docs_list = content_setting.get("web_retrieve_args", {}).get("relevant_docs_list", [])
    web_response = content_setting.get("web_retrieve_args", {}).get("web_response", {})

    # 感兴趣相关话题
    peopleAlsoAsk = web_response.get("search_response",{}).get("peopleAlsoAsk", [])
    if peopleAlsoAsk == []:
        relatedSearches = web_response.get("search_response",{}).get("relatedSearches",[])
        for d in relatedSearches:
            if d.get("query"):
                peopleAlsoAsk.append({'question': d.get("query")})

    # 只选topN的相关参考文档，去重
    refs = []
    for i in range(len(relevant_docs_list)):
        ref = {}
        try:
            ref['url'] = (relevant_docs_list[i].metadata)['url']
            ref['text'] = relevant_docs_list[i].page_content
        except:
            ref['url'] = relevant_docs_list[i].get("metadata",{}).get("url")
            ref['text'] = relevant_docs_list[i].get("page_content")

        try:
            ref['title'] = web_response.get("titles")[web_response['links'].index(ref['url'])]
        except:
            ref['title'] = ref.get("text", "").split('。')[0]
        if ref['url']==None or ref['text']==None or ref['title']=="":
            continue
        else:
            ref['text'] = ref['text'].replace(" ", "") #去除解析的常见特殊字符
            ref['title'] = ref['title'].replace(" ", "")

        if refs == []:
            refs.append(ref)
        else:
            if ref['url'] == refs[-1]['url'] and ref['text'] != refs[-1]['text']:
                refs[-1]['text'] += ref['text']
            elif ref['url'] != refs[-1]['url']:
                refs.append(ref)

    # 引用校正
    answer = citation_correction(output_answer, [ref.get("text", "") for ref in refs])
    out_dict = {"content": answer.strip(), "refs": refs, "recommend_question": peopleAlsoAsk}
    log.info('\nweb retriever postprocess output')
    content_setting["output_answer"] = answer

    return {"flag": True, "result": out_dict, "content_setting": content_setting}


# from fastapi import FastAPI
# import asyncio
# app = FastAPI()
# @app.post("/items1/")
# def create_item(item: ChatMessageInfo):
#     setting = {}
#     content_setting = {
#         "web_retrieve_args": {
#             "retrieve_topk": 3,
#             "template": "说明：您是一位认真的研究者。使用提供的网络搜索结果，对给定的问题写一个全面而详细的回复。",
#             "embedding_model_path": "D:\\E\\Code\\NLP\\yuan_checkpoints\\text2vec-base-chinese",
#             "web_api_key": "",
#             "style_search": "serper",
#             "formatted_relevant_docs": "\nWebpage[1], url: https://download.cntv.cn/travel/guide/travel_cntv_cn/2013-07-29/4225_taishan_20130729_0.pdf:\n泰山：五岳独尊. 一、泰山简介及门票信息. (图片由网友@木棉花提供). 泰山，通常指我国的五岳之首，有“天下第一山”之美誉，又称东岳，中国最美的、令人震撼的. 十大名山之 ...\n\nWebpage[2], url: http://travel.sina.com.cn/taian_taishan-basicinfo-lvyou/:\n泰山简介\n东岳泰山，初名岱山，亦名岱宗，为我国五岳之首，号称“天下第一山”。它拔地通天，巍然屹立于山东东部，总面积426平方千米，最高峰玉皇顶海拔1545米。1987年5月被联合国定为世界自然文化遗产。泰山巍峨，雄奇，沉浑，峻秀的自然景观常令世人慨叹，更有数不清的名胜古迹，摩崖碑碣，使泰山成了世界少有的历史文化游览胜地。\n泰山节庆\n泰山国际登山节举办时间：每年9月中旬主要活动：泰山登山比赛、环泰山万人马拉松比赛、泰山乡村金秋采摘活动，宁阳蟋蟀节、泰山金秋摄影大赛和部分展览活动。泰山国际登山节从举办至今，已成功举办21届，每次登山节都有来自中、英、法、美、韩、日等多个国家的登山爱好者参加。目前，\n\nWebpage[3], url: http://www.intotaishan.com/html/2006/0828/70.html:\n气势磅礴的泰山，是中华民族的象征，从司马迁的名言：“人固有一死，或重于泰山，或轻于鸿毛。”到“有眼不识泰山”， “泰山压顶不弯腰”……，都在不断加深着我们对泰山的向往。登临泰山，犹如攀登长城一样，成为许多中国人的梦想。\n泰山最引人入胜的地方就是泰山是中国历史上唯一受过皇帝封禅的名山。同时泰山也是佛、道两教兴盛之地，是历代帝王朝拜之山。历代帝王所到之处，建庙塑像，刻石题字，留下了众多文物古迹。历代名人宗师对泰山亦仰慕备至，纷纷到此游览。历代赞颂泰山的诗词、歌赋多达一千余首。\n走进泰山，就是走进历史。从泰城西南祭地的社首山、蒿里山至告天的玉皇顶，数不胜数的名胜古迹、摩崖碑碣遍布山中。岱庙内，汉武帝\n\n",
#             "relevant_docs_list": [
#                 {
#                     "page_content": "泰山：五岳独尊. 一、泰山简介及门票信息. (图片由网友@木棉花提供). 泰山，通常指我国的五岳之首，有“天下第一山”之美誉，又称东岳，中国最美的、令人震撼的. 十大名山之 ...",
#                     "metadata": {"url": "https://download.cntv.cn/travel/guide/travel_cntv_cn/2013-07-29/4225_taishan_20130729_0.pdf"},
#                 },
#                 {
#                     "page_content": "泰山简介\n东岳泰山，初名岱山，亦名岱宗，为我国五岳之首，号称“天下第一山”。它拔地通天，巍然屹立于山东东部，总面积426平方千米，最高峰玉皇顶海拔1545米。1987年5月被联合国定为世界自然文化遗产。泰山巍峨，雄奇，沉浑，峻秀的自然景观常令世人慨叹，更有数不清的名胜古迹，摩崖碑碣，使泰山成了世界少有的历史文化游览胜地。\n泰山节庆\n泰山国际登山节举办时间：每年9月中旬主要活动：泰山登山比赛、环泰山万人马拉松比赛、泰山乡村金秋采摘活动，宁阳蟋蟀节、泰山金秋摄影大赛和部分展览活动。泰山国际登山节从举办至今，已成功举办21届，每次登山节都有来自中、英、法、美、韩、日等多个国家的登山爱好者参加。目前，泰山国际登山节已成为国家体委向全民推荐的健身项目，受到国内外登山爱好者的喜爱。市内乘坐1、2、3、4、5、6、7、8、10、11、12、13、14、15、16、18、19、20、21、30、31、32、40路公交车，或高新区101环线车，均可",
#                     "metadata": { "url": "http://travel.sina.com.cn/taian_taishan-basicinfo-lvyou/"}
#                 },
#                 {
#                     "page_content": "气势磅礴的泰山，是中华民族的象征，从司马迁的名言：“人固有一死，或重于泰山，或轻于鸿毛。”到“有眼不识泰山”， “泰山压顶不弯腰”……，都在不断加深着我们对泰山的向往。登临泰山，犹如攀登长城一样，成为许多中国人的梦想。\n泰山最引人入胜的地方就是泰山是中国历史上唯一受过皇帝封禅的名山。同时泰山也是佛、道两教兴盛之地，是历代帝王朝拜之山。历代帝王所到之处，建庙塑像，刻石题字，留下了众多文物古迹。历代名人宗师对泰山亦仰慕备至，纷纷到此游览。历代赞颂泰山的诗词、歌赋多达一千余首。\n走进泰山，就是走进历史。从泰城西南祭地的社首山、蒿里山至告天的玉皇顶，数不胜数的名胜古迹、摩崖碑碣遍布山中。岱庙内，汉武帝植下的柏树翠影婆娑；红门宫前，孔子“登泰山小天下”的感慨，余音缭绕；回马山上，唐玄宗勒马而回的怯懦，神态尤现；云步桥畔，秦始皇敕封的五大夫松，瘦骨昂藏；十八盘道，李白、杜甫历代文人“笑拍红崖咏新作”，墨意未尽，豪风犹在；碧霞祠里，隆重的封禅仪式绰绰伊始。此外还有岱庙、普照寺、王母池、经石峪、碧霞祠、日观峰、南天门、玉皇顶等主要名胜古迹。\n泰山的自然风光更是泰山引人之处，泰山高峰峻拔，雄伟多姿，既是“天然山岳公园”，又是“东方历史文化缩影”。泰山山谷幽深，松柏漫山，著名风景名胜有天柱峰、日观峰、百丈崖、仙人桥、五大夫松、望人松、龙潭飞瀑、云桥飞瀑、三潭飞瀑等。\n游泰山要看四个奇观：泰山日出、云海玉盘、晚霞夕照、黄河金带。",
#                     "metadata": {"url": "http://www.intotaishan.com/html/2006/0828/70.html"}
#                 }
#             ],
#             "web_response": {
#                 "query": "泰山简介",
#                 "language": "zh-cn",
#                 "count": 9,
#                 "titles": [
#                     "泰山_百度百科",
#                     "泰山风景名胜区景区介绍- 欢迎光临五岳独尊的泰山",
#                     "泰山简介 - 新浪旅游",
#                     "[PDF] 泰山：五岳独尊",
#                     "泰山- 維基百科，自由的百科全書",
#                     "泰山旅游景点介绍 - 知乎专栏",
#                     "泰山介绍- 群助手444 - 简书",
#                     "泰山旅游攻略泰山景点介绍 - 景区售票系统",
#                     "泰山风景名胜区_百度百科"
#                 ],
#                 "links": [
#                     "https://baike.baidu.com/item/%E6%B3%B0%E5%B1%B1/5447",
#                     "http://www.intotaishan.com/html/2006/0828/70.html",
#                     "http://travel.sina.com.cn/taian_taishan-basicinfo-lvyou/",
#                     "https://download.cntv.cn/travel/guide/travel_cntv_cn/2013-07-29/4225_taishan_20130729_0.pdf",
#                     "https://zh.wikipedia.org/wiki/%E6%B3%B0%E5%B1%B1",
#                     "https://zhuanlan.zhihu.com/p/547620851",
#                     "https://www.jianshu.com/p/5e2ccaa438c6",
#                     "https://www.1230t.com/blog/lvyougonglue/207.html",
#                     "https://baike.baidu.com/item/%E6%B3%B0%E5%B1%B1%E9%A3%8E%E6%99%AF%E5%90%8D%E8%83%9C%E5%8C%BA/710701"
#                 ],
#                 "snippets": [],
#                 "search_response": {
#                     "organic": [
#                         {
#                             "title": "泰山_百度百科",
#                             "link": "https://baike.baidu.com/item/%E6%B3%B0%E5%B1%B1/5447",
#                             "snippet": "泰山，又名岱山、岱宗、岱岳、东岳、泰岳，为五岳之一，有“五岳之首”“天下第一山”之称。位于山东省中部，隶属于泰安市，绵亘于泰安、济南、淄博三市之间，总面积25000 ...",
#                         },
#                         {
#                             "title": "泰山风景名胜区景区介绍- 欢迎光临五岳独尊的泰山",
#                             "link": "http://www.intotaishan.com/html/2006/0828/70.html",
#                             "snippet": "泰山地处山东中部，现代科学测定，生成于25亿年前的地球造山运动，由于山前出现造山断裂带，所以山势陡峭山形集中，加上周围地势相对较低，从而使先人对泰山产生雄大、厚重 ...",
#                         },
#                         {
#                             "title": "泰山简介 - 新浪旅游",
#                             "link": "http://travel.sina.com.cn/taian_taishan-basicinfo-lvyou/",
#                             "snippet": "东岳泰山，初名岱山，亦名岱宗，为我国五岳之首，号称“天下第一山”。它拔地通天，巍然屹立于山东东部，总面积426平方千米，最高峰玉皇顶海拔1545米。1987年5月被联合国 ...",
#                         },
#                         {
#                             "title": "[PDF] 泰山：五岳独尊",
#                             "link": "https://download.cntv.cn/travel/guide/travel_cntv_cn/2013-07-29/4225_taishan_20130729_0.pdf",
#                             "snippet": "泰山：五岳独尊. 一、泰山简介及门票信息. (图片由网友@木棉花提供). 泰山，通常指我国的五岳之首，有“天下第一山”之美誉，又称东岳，中国最美的、令人震撼的. 十大名山之 ...",
#                         },
#                         {
#                             "title": "泰山- 維基百科，自由的百科全書",
#                             "link": "https://zh.wikipedia.org/wiki/%E6%B3%B0%E5%B1%B1",
#                             "snippet": "泰山，是中國五嶽之首，古名岱山，又稱岱宗、天孫，位於山東省中部，泰安市境內，矗立在魯中群山間；主峰玉皇頂，海拔1532.7公尺。",
#                         },
#                         {
#                             "title": "泰山旅游景点介绍 - 知乎专栏",
#                             "link": "https://zhuanlan.zhihu.com/p/547620851",
#                             "snippet": "泰山，又名岱山、岱宗、岱岳、东岳、泰岳，为五岳之一，有“五岳之首”、“天下第一山”之称。位于山东省中部，隶属于泰安市，绵亘于泰安、济南、淄博三市 ...",
#                         },
#                         {
#                             "title": "泰山介绍- 群助手444 - 简书",
#                             "link": "https://www.jianshu.com/p/5e2ccaa438c6",
#                             "snippet": "泰山是我国的“五岳”之首，又称岱山、岱宗、岱岳、东岳、泰岳等。名称之多，实为全国名山之冠。春秋时改称泰山。泰山前邻孔子故里曲阜，背依泉城济南， ...",
#                         },
#                         {
#                             "title": "泰山旅游攻略泰山景点介绍 - 景区售票系统",
#                             "link": "https://www.1230t.com/blog/lvyougonglue/207.html",
#                             "snippet": "泰山，古名岱山，又称岱宗，位于山东省中部的泰安市，方圆426平方千米，其主峰玉皇顶海拔1532.7米。泰山是“五岳”之首，素有“中华国山”、“天下第一山” ...",
#                         },
#                         {
#                             "title": "泰山风景名胜区_百度百科",
#                             "link": "https://baike.baidu.com/item/%E6%B3%B0%E5%B1%B1%E9%A3%8E%E6%99%AF%E5%90%8D%E8%83%9C%E5%8C%BA/710701",
#                             "snippet": "泰山风景名胜区，AAAAA级风景区，位于山东省泰安市泰山 ... 泰山风景名胜以泰山主峰为中心，呈放射状分布，由自然景观与人文景观融合而成。泰山 ... 编辑概述图册. 编辑文本.",
#                         }
#                     ],
#                     "peopleAlsoAsk": [{"question": "为什么泰山被称为五岳之首？"},{"question": "泰山门票多少钱？"}]
#                 }
#             }
#         },
#         "input_prompt": "Web搜索结果：\nWebpage[1], url: https://download.cntv.cn/travel/guide/travel_cntv_cn/2013-07-29/4225_taishan_20130729_0.pdf:\n泰山：五岳独尊. 一、泰山简介及门票信息. (图片由网友@木棉花提供). 泰山，通常指我国的五岳之首，有“天下第一山”之美誉，又称东岳，中国最美的、令人震撼的. 十大名山之 ...\n\nWebpage[2], url: http://travel.sina.com.cn/taian_taishan-basicinfo-lvyou/:\n泰山简介\n东岳泰山，初名岱山，亦名岱宗，为我国五岳之首，号称“天下第一山”。它拔地通天，巍然屹立于山东东部，总面积426平方千米，最高峰玉皇顶海拔1545米。1987年5月被联合国定为世界自然文化遗产。泰山巍峨，雄奇，沉浑，峻秀的自然景观常令世人慨叹，更有数不清的名胜古迹，摩崖碑碣，使泰山成了世界少有的历史文化游览胜地。\n泰山节庆\n泰山国际登山节举办时间：每年9月中旬主要活动：泰山登山比赛、环泰山万人马拉松比赛、泰山乡村金秋采摘活动，宁阳蟋蟀节、泰山金秋摄影大赛和部分展览活动。泰山国际登山节从举办至今，已成功举办21届，每次登山节都有来自中、英、法、美、韩、日等多个国家的登山爱好者参加。目前，\n\nWebpage[3], url: http://www.intotaishan.com/html/2006/0828/70.html:\n气势磅礴的泰山，是中华民族的象征，从司马迁的名言：“人固有一死，或重于泰山，或轻于鸿毛。”到“有眼不识泰山”， “泰山压顶不弯腰”……，都在不断加深着我们对泰山的向往。登临泰山，犹如攀登长城一样，成为许多中国人的梦想。\n泰山最引人入胜的地方就是泰山是中国历史上唯一受过皇帝封禅的名山。同时泰山也是佛、道两教兴盛之地，是历代帝王朝拜之山。历代帝王所到之处，建庙塑像，刻石题字，留下了众多文物古迹。历代名人宗师对泰山亦仰慕备至，纷纷到此游览。历代赞颂泰山的诗词、歌赋多达一千余首。\n走进泰山，就是走进历史。从泰城西南祭地的社首山、蒿里山至告天的玉皇顶，数不胜数的名胜古迹、摩崖碑碣遍布山中。岱庙内，汉武帝\n\n说明：您是一位认真的研究者。使用提供的网络搜索结果，对给定的问题写一个全面而详细的回复。\n问题：泰山简介\n答案：",
#         "output_answer":"泰山，通常指我国的五岳之首，有“天下第一山”之美誉，又称东岳，中国最美的、令人震撼的."
#     }
#     result = asyncio.run(call(item, setting, content_setting))
#     return result
#
#
# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=2000)

