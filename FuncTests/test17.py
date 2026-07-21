import importlib
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ReloadHandler(FileSystemEventHandler):
    def __init__(self, module_name):
        self.module_name = module_name

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"检测到 {event.src_path} 变化，正在重载...")
            try:
                # 注意：这里需要确保模块已导入
                module = importlib.import_module(self.module_name)
                importlib.reload(module)
                print("重载成功")
            except Exception as e:
                print(f"重载失败: {e}")

if __name__ == "__main__":
    observer = Observer()
    # 监听当前目录，并绑定事件处理器
    observer.schedule(ReloadHandler("my_module"), path='.', recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()