from watchfiles import watch

# 监控当前目录
for changes in watch('.'):
    for change_type, file_path in changes:
        print(f"Change: {change_type}, Path: {file_path}")