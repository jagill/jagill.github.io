a = [1, 2, 3]
for i in a:
    print(i)
# 1
# 2
# 3

a = [1, 2]
itr = iter(a)
print(next(itr))
# 1
print(next(itr))
# 2
print(next(itr))
# StopIteration

a = [1, 2]
b = iter([1, 2])


def print1(itbl):
    for x in itbl:
        print(x)
        break


print1(a)
# 1
print1(a)
# 1
print1(a)
# 1
print1(b)
# 1
print1(b)
# 2
print1(b)
# Nothing!  We have exhausted b already.


def f():
    yield 1
    return


g = f()
print(type(g))
print(next(g))
print(next(g))


def f2():
    yield 1


g1 = f2()
g2 = f2()
print(next(g1))
# 1
print(next(g1))
# Sto(Iteration
print(next(g2))
# 1
print(next(g2))
# StopIteration


def counter():
    c = 0
    while True:
        yield c
        c += 1


count = counter()
print(next(count))
# 0
print(next(count))
# 1
