def parse_text(text):
    return text.split(" ")

def parse_txts(txts):
    ret = []
    for txt in txts:
        ret.append(f"{parse_text(txt)},")
    return ret