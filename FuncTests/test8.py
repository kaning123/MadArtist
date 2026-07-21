import asyncio
from typing import List, Union
from translators import AsyncTranslator

async def translate_async(
    texts: Union[str, List[str]],
    to: str,
    from_lang: str = "auto",
    max_concurrent: int = 10
) -> List[str]:
    if isinstance(texts, str):
        texts = [texts]
    semaphore = asyncio.Semaphore(max_concurrent)
    async with AsyncTranslator() as translator:
        async def translate_one(text: str) -> str:
            async with semaphore:
                try:
                    if from_lang != "auto" and from_lang == to:
                        print(f"[跳过] 源语言和目标语言相同 ({from_lang})，不翻译: {text}")
                        return text
                    # ⭐ 调用官方提供的异步 API
                    result = await translator.translate_text(
                        text, from_language=from_lang, to_language=to
                    )
                    return result
                except Exception as e:
                    print(f"[翻译失败] {text} -> {e}")
                    return text
        tasks = [translate_one(text) for text in texts]
        return await asyncio.gather(*tasks)

# 外部调用接口保持不变
def translate(texts, to, from_lang='auto', threads=10):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(
        translate_async(texts, to, from_lang, max_concurrent=threads)
    )

# 使用示例
if __name__ == "__main__":
    sample_texts = [
        "Hello, world!",
        "Python is a powerful programming language.",
        "异步编程可以提高效率。",
    ]
    translated = translate(sample_texts, to="zh", threads=5)
    for orig, trans in zip(sample_texts, translated):
        print(f"{orig} -> {trans}")