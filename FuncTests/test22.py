def a():
    yield 1
    yield 2
    yield 3

if __name__ == "__main__":
    for x in a():
        print(x)