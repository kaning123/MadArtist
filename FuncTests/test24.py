import egrpc

@egrpc.method
if __name__ == "__main__":
    egrpc.connect("localhost", 12345)
    print(test())
    egrpc.disconnect()