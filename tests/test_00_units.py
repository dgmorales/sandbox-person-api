import random

from personapi.store import SingletonMeta


def test_singleton():
    class TestSingleton(metaclass=SingletonMeta):
        def __init__(self):
            self.myid = random.randint(0, 1000)

    a = TestSingleton()
    b = TestSingleton()
    assert a == b
    assert a.myid == b.myid
