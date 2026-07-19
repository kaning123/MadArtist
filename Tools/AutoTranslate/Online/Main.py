import asyncio
import logging
from typing import List, Optional

import aiohttp
import fast_langdetect
import translators as ts
from rich.logging import RichHandler

# ---------- 配置 Rich 日志 ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("translator")

# ---------- 语言检测（增强日志与异常处理） ----------
def detect_lang(text: str) -> str:
    """检测文本语言，返回 ISO 639-1 代码"""
    logger.debug(f"检测语言，文本长度: {len(text)}")
    try:
        result = fast_langdetect.detect(text, model='lite', k=1)
        lang = result[0]['lang']
        logger.info(f"检测到语言: {lang}")
        return lang # type: ignore
    except Exception as e:
        logger.exception("语言检测失败")
        raise

# ---------- 翻译函数（添加日志、异常处理、批量进度） ----------
def translate(
    texts: List[str],
    to: str,
    from_lang: str = 'auto',
    threads: int = 10
) -> List[str]:
    """
    批量翻译文本
    :param texts: 待翻译文本列表
    :param to: 目标语言代码
    :param from_lang: 源语言代码，默认 'auto' 表示自动检测（基于第一条文本）
    :param threads: 并发线程数（传递给 translators 库）
    :return: 翻译后的文本列表
    """
    logger.info(f"开始批量翻译，共 {len(texts)} 条，目标语言: {to}，源语言: {from_lang}，并发线程数: {threads}")

    # 自动检测源语言（基于第一条文本）
    if from_lang == 'auto':
        if not texts:
            logger.error("文本列表为空，无法自动检测源语言")
            return []
        try:
            from_lang = detect_lang(texts[0])
            logger.info(f"自动检测源语言为: {from_lang}")
        except Exception as e:
            logger.error("自动检测源语言失败，将使用默认值 'auto' 继续（但 translators 可能不支持）")
            # 保留 'auto'，但某些翻译器可能不支持，此处做降级
            from_lang = 'auto'

    results = []
    total = len(texts)

    for idx, text in enumerate(texts, start=1):
        logger.debug(f"翻译第 {idx}/{total} 条，文本预览: {text[:50]}...")
        try:
            # 调用异步翻译（注意：这里每个文本单独创建事件循环，可能影响性能）
            logger.debug(f"调用 translators 翻译: from={from_lang}, to={to}")
            translated = asyncio.run(
                ts.translate_text(
                    text,
                    from_language=from_lang,
                    to_language=to,
                    if_use_async=True,
                    threads=threads
                ) # type: ignore
            )
            logger.info(f"第 {idx} 条翻译成功，结果预览: {translated[:50]}...")
            results.append(translated)
        except Exception as e:
            logger.exception(f"第 {idx} 条翻译失败，错误: {e}")
            # 根据需求决定是否保留空字符串或重抛异常，这里保留空字符串并继续
            results.append("")

    success_count = len([r for r in results if r])
    logger.info(f"批量翻译完成，成功 {success_count}/{total} 条")
    return results

# ---------- 测试入口 ----------
if __name__ == "__main__":
    sample_texts = [
        "Hello, world!",
        "How are you?",
    ]
    logger.info("执行测试样例")
    translated = translate(sample_texts, "zh", threads=10)
    for original, translated_text in zip(sample_texts, translated):
        logger.info(f"原文: {original} -> 译文: {translated_text}")