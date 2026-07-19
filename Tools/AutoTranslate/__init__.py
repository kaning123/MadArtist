from .Online import Main as MainOnline
from .Offline import Main as MainOffline
from . import web_check

def detect_lang(text):
    return MainOffline.detect_lang(text)

def translate(texts, to, from_lang='auto', threads=10):
    if web_check.check_internet():
        return MainOnline.translate(texts, to, from_lang, threads)
    else:
        return MainOffline.translate_texts(texts, from_lang, to)

def get_all_langs():
    return MainOffline.get_all_langs()