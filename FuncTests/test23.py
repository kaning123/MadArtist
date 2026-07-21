import egrpc

@egrpc.function
def test() -> int:
    print("Hello, World!")
    return 1

if __name__ == "__main__":
    egrpc.serve(port=12345)