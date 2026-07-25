import jieba
import pypinyin

def parse_text(text):
    words = jieba.lcut(text)
    pinyin_list = pypinyin.pinyin(words, style=pypinyin.Style.TONE)
    res = ",".join([i[0] for i in pinyin_list])
    return res

def parse_texts(txts):
    ret = []
    for txt in txts:
        ret.append(parse_text(txt))
    return ret
