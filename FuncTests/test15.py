# 示例：pypinyin + jieba 处理多音字
import jieba
from pypinyin import pinyin, lazy_pinyin, Style

text = "他银行里的存折，行吗？"

# 1. 先用 jieba 进行精确分词
seg_list = jieba.lcut(text) # jieba.lcut 返回 list
print(seg_list) # 输出: ['他', '银行', '里', '的', '存折', '，', '行吗', '？']

# 2. 将分词后的列表传给 pypinyin，它会根据词组智能匹配拼音
pinyin_list = pinyin(seg_list, style=Style.TONE)
# 将每个词的拼音列表合并成字符串
result = ' '.join([p[0] for p in pinyin_list])
print(result)