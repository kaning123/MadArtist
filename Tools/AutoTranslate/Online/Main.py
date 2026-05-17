import translators as ts
import asyncio 
import aiohttp
import fast_langdetect

def detect_lang(text):
    lang = fast_langdetect.detect(text, model='lite', k=1)
    return lang[0]['lang']

def translate(texts, to, from_lang='auto', threads=10):
    if from_lang == 'auto':
        from_lang = detect_lang(texts[0])  # Assuming all texts are in the same language
    for text in texts:
            print(f"to: {to}, from: {from_lang}, text: {text}")
            result = asyncio.run(ts.translate_text(text,
                                                   from_language=from_lang,
                                                   to_language=to,
                                                   if_use_async = True,
                                                   threads=threads))
            print(f"{text} -> {result}")

if __name__ == "__main__":
    sample_texts = [
        "Hello, world!",
        "How are you?",
    ]
    translate(sample_texts, "zh", threads=10)