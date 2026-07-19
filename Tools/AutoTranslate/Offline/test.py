import os
import logging
from rich.logging import RichHandler
import argostranslate.package
import argostranslate.translate
import fast_langdetect

# ---------- 配置 Rich 日志 ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("offline-translator")

# ---------- 更新翻译包索引 ----------
logger.info("正在更新 argostranslate 包索引...")
try:
    argostranslate.package.update_package_index()
    logger.info("包索引更新完成")
except Exception as e:
    logger.exception("更新包索引时发生异常")

# ---------- 原有函数（添加日志） ----------
def get_all_langs() -> tuple[set, set]:
    """获取所有支持的语言（源语言和目标语言）"""
    logger.debug("调用 get_all_langs")
    try:
        from_langs = set()
        to_langs = set()
        for lang in argostranslate.package.get_available_packages():
            from_langs.add(lang.from_name)
            to_langs.add(lang.to_name)
        logger.debug(f"获取到 {len(from_langs)} 种源语言，{len(to_langs)} 种目标语言")
        return from_langs, to_langs
    except Exception as e:
        logger.exception("获取语言列表时发生异常")
        raise

def get_all_lang_pairs() -> list[tuple[str, str]]:
    """获取所有支持的语言对 (源语言, 目标语言)"""
    logger.debug("调用 get_all_lang_pairs")
    try:
        ret = []
        for lang in argostranslate.package.get_available_packages():
            ret.append((lang.from_name, lang.to_name))
        logger.debug(f"获取到 {len(ret)} 个语言对")
        return ret
    except Exception as e:
        logger.exception("获取语言对时发生异常")
        raise

def detect_lang(text: str) -> str:
    """检测文本语言（ISO 639-1 代码）"""
    logger.debug(f"检测语言，文本长度: {len(text)}")
    try:
        result = fast_langdetect.detect(text, model='lite', k=1)
        lang = result[0]['lang']
        logger.info(f"检测到语言: {lang}")
        return lang
    except Exception as e:
        logger.exception("语言检测失败")
        raise

def translate_text(text: str, from_lang: str = 'auto', to_lang: str = "zh") -> str:
    """翻译单个文本"""
    logger.debug(f"翻译文本，长度: {len(text)}，源语言: {from_lang}，目标语言: {to_lang}")
    try:
        if from_lang == 'auto':
            detected = detect_lang(text)
            logger.info(f"自动检测源语言: {detected}")
            from_lang = detected
        translated = argostranslate.translate.translate(text, from_lang, to_lang)
        logger.info(f"翻译完成，结果长度: {len(translated)}")
        return translated
    except Exception as e:
        logger.exception("翻译文本时发生异常")
        raise

def translate_texts(texts: list[str], from_lang: str = 'auto', to_lang: str = "zh") -> list[str]:
    """批量翻译多个文本"""
    logger.info(f"批量翻译，数量: {len(texts)}，源语言: {from_lang}，目标语言: {to_lang}")
    ret = []
    for idx, text in enumerate(texts, 1):
        logger.debug(f"翻译第 {idx}/{len(texts)} 条")
        try:
            ret.append(translate_text(text, from_lang, to_lang))
        except Exception as e:
            logger.exception(f"第 {idx} 条翻译失败，跳过")
            ret.append("")   # 或根据需求抛出异常
    logger.info(f"批量翻译完成，成功 {len(ret)} 条")
    return ret