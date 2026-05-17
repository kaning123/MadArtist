import requests

def check_internet(url="https://www.baidu.com", timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        # 状态码 200 表示成功
        return response.status_code == 200
    except requests.ConnectionError:
        return False

if __name__ == "__main__":
    if check_internet():
        print("✅ 互联网连接正常")
    else:
        print("❌ 无法访问互联网")