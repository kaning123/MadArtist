import requests, os
from tqdm import tqdm
import colorama
colorama.init()
red = colorama.Fore.RED
green = colorama.Fore.GREEN
BAR_DEFAULT_FORMAT = '{desc}:{percentage:3.0f}%[{bar}][{n_fmt}/{total_fmt} eta:{remaining}, speed:{rate_fmt}{postfix}]'
def download(url, file, chunk=1024*1024,timeout=100,bar_format=BAR_DEFAULT_FORMAT):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }
    done = 0
    if os.path.exists(file):
        done = os.path.getsize(file)
        headers['Range'] = f'bytes={done}-'
    with requests.get(url, headers=headers, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        total = int(r.headers.get('Content-Length', 0)) + done
        with open(file, 'ab') as f, tqdm(total=total, initial=done,desc="Downloading",ascii=f'——~',
                                         unit='B', unit_scale=True,bar_format=bar_format) as bar:
            for blk in r.iter_content(chunk):
                if blk:
                    f.write(blk)
                    bar.update(len(blk))
