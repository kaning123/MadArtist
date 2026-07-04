import argparse
import requests
import os
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # 可选，用于进度条显示（若没有可注释掉，或执行 pip install tqdm 安装）

# 禁用 requests 警告
# requests.packages.urllib3.disable_warnings()

class MultiThreadDownloader:
    def __init__(self, url, save_path=None, thread_num=5, timeout=30):
        self.url = url
        self.thread_num = thread_num
        self.timeout = timeout
        self.file_size = 0
        self.temp_files = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # 确定保存路径
        if save_path:
            self.save_path = save_path
        else:
            # 从 URL 提取文件名
            self.save_path = self.url.split('/')[-1].split('?')[0]
            # 处理空文件名情况
            if not self.save_path:
                self.save_path = 'download_file'

    def get_file_size(self):
        """获取文件大小并检查是否支持断点续传"""
        try:
            response = self.session.head(self.url, timeout=self.timeout, allow_redirects=True, verify=False)
            response.raise_for_status()
            
            # 获取文件大小
            if 'Content-Length' in response.headers:
                self.file_size = int(response.headers['Content-Length'])
            else:
                raise Exception("无法获取文件大小，服务器未返回 Content-Length 头")
            
            # 检查是否支持断点续传
            accept_ranges = response.headers.get('Accept-Ranges', 'none')
            if accept_ranges != 'bytes':
                print(f"警告：服务器不支持断点续传（Accept-Ranges: {accept_ranges}），将使用单线程下载")
                self.thread_num = 1
            
            return True
        except Exception as e:
            print(f"获取文件信息失败：{e}")
            return False

    def download_chunk(self, start, end, chunk_index):
        """下载单个文件块"""
        temp_file = f"{self.save_path}.part{chunk_index}"
        self.temp_files.append(temp_file)
        
        # 如果临时文件已存在，检查大小并续传
        if os.path.exists(temp_file):
            downloaded_size = os.path.getsize(temp_file)
            start += downloaded_size
        
        if start >= end:
            return True
        
        headers = {'Range': f'bytes={start}-{end}'}
        try:
            response = self.session.get(
                self.url, 
                headers=headers, 
                stream=True, 
                timeout=self.timeout, 
                verify=False
            )
            response.raise_for_status()
            
            with open(temp_file, 'ab') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            print(f"\n块 {chunk_index} 下载失败：{e}")
            return False

    def merge_chunks(self):
        """合并所有文件块"""
        try:
            with open(self.save_path, 'wb') as f:
                for temp_file in sorted(self.temp_files, key=lambda x: int(x.split('part')[-1])):
                    if os.path.exists(temp_file):
                        with open(temp_file, 'rb') as tf:
                            f.write(tf.read())
                        os.remove(temp_file)
            print(f"\n文件已保存至：{os.path.abspath(self.save_path)}")
            return True
        except Exception as e:
            print(f"合并文件块失败：{e}")
            return False

    def download(self):
        """开始多线程下载"""
        # 获取文件信息
        if not self.get_file_size():
            return False
        
        if self.file_size == 0:
            print("文件大小为0，无需下载")
            return False
        
        print(f"开始下载：{self.url}")
        print(f"文件大小：{self._format_size(self.file_size)}")
        print(f"线程数：{self.thread_num}")
        
        # 计算每个块的大小
        chunk_size = math.ceil(self.file_size / self.thread_num)
        
        # 创建线程池并下载
        futures = []
        with ThreadPoolExecutor(max_workers=self.thread_num) as executor:
            for i in range(self.thread_num):
                start = i * chunk_size
                end = min((i + 1) * chunk_size - 1, self.file_size - 1)
                futures.append(executor.submit(self.download_chunk, start, end, i))
            
            # 显示下载进度
            with tqdm(total=self.file_size, unit='B', unit_scale=True, desc=self.save_path) as pbar:
                completed = 0
                for future in as_completed(futures):
                    if future.result():
                        # 计算已完成的大小
                        for temp_file in self.temp_files:
                            if os.path.exists(temp_file):
                                completed += os.path.getsize(temp_file)
                        pbar.update(completed - pbar.n)
        
        # 检查是否所有块都下载完成
        all_completed = all(future.result() for future in futures)
        if all_completed:
            return self.merge_chunks()
        else:
            print("\n部分文件块下载失败，请检查网络后重试")
            return False

    @staticmethod
    def _format_size(size):
        """格式化文件大小显示"""
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        return f"{size:.2f} {units[unit_index]}"

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='多线程文件下载器')
    parser.add_argument('url', help='要下载的文件URL')
    parser.add_argument('-o', '--output', help='保存路径/文件名（可选）')
    parser.add_argument('-t', '--threads', type=int, default=5, help='下载线程数（默认5）')
    parser.add_argument('-T', '--timeout', type=int, default=30, help='请求超时时间（默认30秒）')
    
    args = parser.parse_args()
    
    # 创建下载器并开始下载
    downloader = MultiThreadDownloader(
        url=args.url,
        save_path=args.output,
        thread_num=args.threads,
        timeout=args.timeout
    )
    success = downloader.download()
    
    exit(0 if success else 1)

if __name__ == '__main__':
    main()