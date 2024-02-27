
def test1():
    raise NotImplementedError("Test1: NotImplementedError")

def test2():
    try:
        test1()
    except NotImplementedError as e:
        print("Test2", str(e))

    raise FileNotFoundError

def test3():
    try:
        test2()
    except Exception as e:
        print("Test3", str(e))

test3()