import os
import argostranslate.package
import argostranslate.translate
import fast_langdetect

argostranslate.package.update_package_index()

def get_all_langs() -> tuple[set, set]:
    from_langs = set()
    to_langs = set()
    for lang in argostranslate.package.get_available_packages():
        from_langs.add(lang.from_name)
        to_langs.add(lang.to_name)
    return from_langs, to_langs

def get_all_lang_pairs() -> list[tuple[str, str]]:
    ret = []
    for lang in argostranslate.package.get_available_packages():
        ret.append((lang.from_name, lang.to_name))
    return ret

def detect_lang(text: str) -> str:
    result = fast_langdetect.detect(text, model='lite', k=1)
    return result[0]['lang']

def translate_text(text: str, from_lang: str = 'auto', to_lang: str = "zh") -> str:
    if from_lang == 'auto':
        from_lang = detect_lang(text)
    translate = argostranslate.translate.translate(text, from_lang, to_lang)
    return translate

def translate_texts(texts: list[str], from_lang: str = 'auto', to_lang: str = "zh") -> list[str]:
    ret = []
    for text in texts:
        ret.append(translate_text(text, from_lang, to_lang))
    return ret

