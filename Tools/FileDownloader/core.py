#!/usr/bin/env python3
"""
基于 rich 的多线程文件下载器
用法: python downloader.py <URL> [-o 输出文件名] [-t 线程数] [-r]
"""

import argparse
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

console = Console()


def get_filename_from_url(url: str, default: str = "downloaded_file") -> str:
    """从 URL 中提取文件名，若无效则返回默认值"""
    name = url.split("/")[-1]
    if not name or "?" in name or "=" in name:
        return default
    return name


class MultiThreadDownloader:
    def __init__(
        self,
        url: str,
        output_path: str,
        threads: int = 4,
        resume: bool = False,
        chunk_size: int = 1024 * 1024,  # 1MB
    ):
        self.url = url
        self.output_path = output_path
        self.threads = threads
        self.resume = resume
        self.chunk_size = chunk_size
        self.total_size = None
        self.supported_ranges = False
        self.temp_dir = None
        self.part_files = []  # 存储每个分片的临时文件路径

    def _get_file_info(self) -> bool:
        """获取文件大小及 Range 支持情况"""
        try:
            # 先发送 HEAD 请求获取信息
            resp_head = requests.head(self.url, timeout=10)
            resp_head.raise_for_status()
            self.total_size = int(resp_head.headers.get("content-length", 0))
            accept_ranges = resp_head.headers.get("accept-ranges", "").lower()
            self.supported_ranges = accept_ranges == "bytes" and self.total_size > 0
            return True
        except requests.exceptions.RequestException as e:
            console.print(f"[red]获取文件信息失败: {e}[/red]")
            return False

    def _prepare_temp_dir(self):
        """在输出文件同目录下创建临时目录存放分片"""
        base_dir = os.path.dirname(self.output_path) or "."
        self.temp_dir = os.path.join(base_dir, f".{os.path.basename(self.output_path)}.parts")
        os.makedirs(self.temp_dir, exist_ok=True)

    def _get_part_path(self, part_index: int) -> str:
        """获取第 part_index 个分片的临时文件路径"""
        return os.path.join(self.temp_dir, f"part-{part_index:04d}.tmp")

    def _calculate_parts(self) -> list:
        """计算每个分片的起始和结束字节（包含结束）"""
        part_size = (self.total_size + self.threads - 1) // self.threads  # 向上取整
        parts = []
        for i in range(self.threads):
            start = i * part_size
            end = min(start + part_size - 1, self.total_size - 1)
            if start <= end:
                parts.append((start, end))
            else:
                break
        return parts

    def _download_part(self, part_idx: int, start: int, end: int, progress, task_id) -> bool:
        """下载单个分片，支持断点续传，并更新进度"""
        part_path = self._get_part_path(part_idx)
        # 检查已下载大小
        downloaded = 0
        if os.path.exists(part_path):
            downloaded = os.path.getsize(part_path)
            # 若已完整，直接返回成功
            if downloaded >= (end - start + 1):
                return True

        # 构造 Range 头
        range_start = start + downloaded
        range_end = end
        headers = {"Range": f"bytes={range_start}-{range_end}"}
        try:
            # 使用 stream 方式下载
            with requests.get(self.url, headers=headers, stream=True, timeout=30) as resp:
                resp.raise_for_status()
                # 打开文件，追加模式
                with open(part_path, "ab") as f:
                    # 若文件已有部分，seek 到末尾
                    f.seek(0, os.SEEK_END)
                    for chunk in resp.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            # 更新进度（注意：多线程更新同一 task 需要原子操作，rich 内部是安全的）
                            progress.update(task_id, advance=len(chunk))
            return True
        except requests.exceptions.RequestException as e:
            console.print(f"[red]分片 {part_idx} 下载失败: {e}[/red]")
            return False

    def _merge_parts(self):
        """按顺序合并所有分片到目标文件，并删除临时文件"""
        try:
            with open(self.output_path, "wb") as out_f:
                for i in range(len(self.part_files)):
                    part_path = self._get_part_path(i)
                    if not os.path.exists(part_path):
                        raise FileNotFoundError(f"分片文件 {part_path} 缺失")
                    with open(part_path, "rb") as in_f:
                        while True:
                            data = in_f.read(1024 * 1024)  # 1MB 缓冲
                            if not data:
                                break
                            out_f.write(data)
                    os.remove(part_path)  # 合并后删除临时分片
            # 删除临时目录（如果为空）
            try:
                os.rmdir(self.temp_dir)
            except OSError:
                pass
        except Exception as e:
            console.print(f"[red]合并文件失败: {e}[/red]")
            # 可能部分合并，保留临时文件供续传
            raise

    def download(self) -> bool:
        """执行多线程下载，返回是否成功"""
        # 1. 获取文件信息
        if not self._get_file_info():
            return False

        if self.total_size == 0:
            console.print("[red]文件大小为 0，无法下载[/red]")
            return False

        # 检查是否支持 Range
        if not self.supported_ranges:
            console.print("[yellow]服务器不支持 Range，降级为单线程下载[/yellow]")
            # 调用单线程下载（原有逻辑）
            return download_single(self.url, self.output_path, self.resume)

        # 2. 若目标文件已存在且完整，则直接完成
        if os.path.exists(self.output_path):
            if os.path.getsize(self.output_path) == self.total_size:
                console.print(f"[green]文件已存在且完整: {self.output_path}[/green]")
                return True
            elif not self.resume:
                # 不续传且文件存在，询问覆盖
                console.print(f"[yellow]文件 {self.output_path} 已存在，大小不匹配[/yellow]")
                overwrite = console.input("是否覆盖？(y/n): ").strip().lower()
                if overwrite != "y":
                    console.print("[red]已取消下载[/red]")
                    return False

        # 3. 准备临时目录
        self._prepare_temp_dir()

        # 4. 计算分片
        parts = self._calculate_parts()
        self.threads = len(parts)  # 实际线程数可能小于指定值
        self.part_files = [self._get_part_path(i) for i in range(len(parts))]

        # 检查已有分片，计算已下载总量
        downloaded_total = 0
        for i, (start, end) in enumerate(parts):
            part_path = self._get_part_path(i)
            if os.path.exists(part_path):
                size = os.path.getsize(part_path)
                if size > (end - start + 1):
                    # 如果分片超过预期，可能是错误，截断？
                    # 实际通常不会，但为了安全，可截断
                    with open(part_path, "rb+") as f:
                        f.truncate(end - start + 1)
                    size = end - start + 1
                downloaded_total += size
            else:
                # 创建空文件以便记录
                open(part_path, "wb").close()

        # 5. 如果已下载总量等于总大小，直接合并
        if downloaded_total == self.total_size:
            console.print("[green]所有分片已完整，正在合并...[/green]")
            self._merge_parts()
            console.print(f"[green]✓ 下载完成: {self.output_path}[/green]")
            return True

        # 6. 创建进度条
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False,
        ) as progress:
            task_id = progress.add_task(
                f"[cyan]下载 {os.path.basename(self.output_path)}",
                total=self.total_size,
                start=True,
                completed=downloaded_total,
            )

            # 7. 并发下载未完成的分片
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = {}
                for i, (start, end) in enumerate(parts):
                    part_path = self._get_part_path(i)
                    # 检查该分片是否已完成
                    if os.path.exists(part_path) and os.path.getsize(part_path) >= (end - start + 1):
                        continue  # 已完整，跳过
                    future = executor.submit(
                        self._download_part, i, start, end, progress, task_id
                    )
                    futures[future] = i

                # 等待所有提交的任务完成
                for future in as_completed(futures):
                    part_idx = futures[future]
                    success = future.result()
                    if not success:
                        console.print(f"[red]分片 {part_idx} 下载失败，终止下载[/red]")
                        # 取消剩余任务
                        for f in futures:
                            f.cancel()
                        return False

            # 确保进度达到100%
            progress.update(task_id, completed=self.total_size)

        # 8. 合并分片
        console.print("[green]所有分片下载完成，正在合并...[/green]")
        self._merge_parts()
        console.print(f"[green]✓ 下载完成: {self.output_path}[/green]")
        return True


def download_single(url: str, output_path: str, resume: bool = False) -> bool:
    """原有的单线程下载逻辑（保留）"""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    headers = {}
    initial_pos = 0
    if resume and os.path.exists(output_path):
        initial_pos = os.path.getsize(output_path)
        headers["Range"] = f"bytes={initial_pos}-"
        console.print(f"[yellow]断点续传: 从 {initial_pos} 字节开始[/yellow]")

    try:
        response = requests.get(url, stream=True, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        console.print(f"[red]请求失败: {e}[/red]")
        return False

    total_size = int(response.headers.get("content-length", 0))

    if resume and initial_pos > 0 and "content-range" not in response.headers:
        console.print("[yellow]服务端不支持断点续传，将从头开始下载并覆盖已有文件[/yellow]")
        initial_pos = 0
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
        except requests.exceptions.RequestException as e:
            console.print(f"[red]请求失败: {e}[/red]")
            return False

    total = total_size if total_size > 0 else None
    mode = "ab" if resume and initial_pos > 0 else "wb"

    try:
        with open(output_path, mode) as f:
            if mode == "ab" and initial_pos > 0:
                f.seek(initial_pos)

            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=console,
                transient=False,
            ) as progress:
                task_id = progress.add_task(
                    f"[cyan]下载 {os.path.basename(output_path)}",
                    total=total,
                    start=True,
                )
                if initial_pos > 0:
                    progress.update(task_id, completed=initial_pos)

                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        progress.update(task_id, advance=len(chunk))

                if total is not None:
                    progress.update(task_id, completed=total)

        console.print(f"[green]✓ 下载完成: {output_path}[/green]")
        return True
    except IOError as e:
        console.print(f"[red]文件写入错误: {e}[/red]")
        return False


def main(url: str, output_path: str, threads: int = 4, resume: bool = False):
    # 确定输出路径
    if output_path:
        pass
    else:
        filename = get_filename_from_url(url)
        output_path = filename

    # 若文件已存在且未启用续传，询问覆盖（但多线程会做更细粒度的判断，此处先让下载器内部处理）
    # 若文件存在且完整，下载器会直接完成，若部分存在则根据 resume 决定。

    # 选择下载模式
    if threads > 1:
        downloader = MultiThreadDownloader(
            url=url,
            output_path=output_path,
            threads=threads,
            resume=resume,
        )
        success = downloader.download()
    else:
        # 单线程
        success = download_single(url, output_path, resume)

    #sys.exit(0 if success else 1)
    return success
