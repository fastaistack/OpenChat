# -*- coding: utf-8  -*-

# 检验是否不含有标点，不含标点返回True，含有返回False
def isnot_punctuation(strs):
    en_punc = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    ch_punc = '＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､\u3000、〃〈〉《》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏﹑﹔·！？｡。'
    allPun = en_punc + ch_punc

    for _char in strs:
        if _char in allPun:
            return False
    return True


def modify_dict(dictionary):
    """
    修改字典中所有字符串值，所有str中"用\\"替换
    Args:
        dictionary: 返回UI字典

    Returns:
        字典中所有str中"用\\"替换
    """
    for key in dictionary.keys():
        if isinstance(dictionary[key], dict):
            # 如果当前值为字典类型，则进行递归调用
            modify_dict(dictionary[key])
        elif isinstance(dictionary[key], str):
            # 对于非字典类型的值，直接进行修改操作
            dictionary[key] = dictionary[key].replace('"', '\\"')
        elif isinstance(dictionary[key], list):
            for i in range(len(dictionary[key])):
                if isinstance(dictionary[key][i], dict):
                    # 如果当前值为字典类型，则进行递归调用
                    modify_dict(dictionary[key][i])
                elif isinstance(dictionary[key][i], str):
                    # 对于非字典类型的值，直接进行修改操作
                    dictionary[key][i] = dictionary[key][i].replace('"', '\\"')

    return dictionary



