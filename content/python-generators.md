+++
title = "Python Generators"
weight = 2
date = 2017-05-01

[taxonomies]
tags = ["python"]
categories = ["tech"]
+++

One of Python's strengths is its powerful generators.  Even a basic understand
of them unlocks the the ability to elegantly handle even huge datasets.  But
they hold some suprises in what is executed when -- understand them at a deeper
level allows you to use and debug them more effectively.

<!-- more -->

## Iterables and Iterators

First, some basics.  An _iterable_ is an object like a list or a tuple
that can be iterated over in a `for` loop.  We will see shortly that there are
other types of iterables.

```python
a = [1, 2, 3]
for i in a:
    print(i)
# 1
# 2
# 3
```

An _iterator_ `itr` is an object with an `__next()__` method which yields the
next object to be iterated over. If there are no more objects, `next()` will
instead raise a `StopIteration` exception. The pythonic way to do this is the
builtin `next` function: `next(itr)`. There is a deep connection between
iterables and iterators; part of the iterable contract is that an iterable
must expose an `__iter__()` method which returns an iterator. The pythonic
way to call this is using the builtin `iter()` method: `iter(a)`

```python
a = [1, 2]
itr = iter(a)
print(next(itr))
# 1
print(next(itr))
# 2
print(next(itr))
# StopIteration
```

In fact, the `for` loop over an iterable `a` can be implemented as:
```python
# Vanilla for loop
for x in a:
  f(x)

# or the iterator version
itr = iter(a)
while True:
  try:
    x = next(itr)
  except StopIteration:
    break
  f(x)
```

To make life slightly easier, _iterators must also be iterables_; i.e. they
must expose the `__iter__` method, which in this case will just return
themselves:

```python
iter([1, 2, 3]) is [1, 2, 3]
# False
itr = iter([1, 2, 3])
iter(itr) is itr
# True
```

One important difference between iterators and most iterables is that
iterators are always one-shot, while iterables might be able to be consumed
more than once. If call `next` on an iterator (in a for loop or otherwise),
you are consuming one iteration, and it can't be consumed again. When you
iterate over most iterables (like lists, etc), you create a new iterator,
which starts from the beginning.

```python
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
```


In fact, for many iterables, you can create multiple independent iterators:

```python
a = [1, 2, 3]
b = iter(a)
c = iter(a)
next(b)
# 1
next(c)
# 1
next(c)
# 2
next(c)
# 3
next(c)
# StopIteration
next(b)
# 2
next(b)
# 3
next(b)
# StopIteration
```


To summarize, an iterable is something that exposes an iterator via `iter`, and
an iterator is something that you can call `next` on.

Generators
----------

If you use the `yield` keyword in a function, it does not return a normal value,
but instead returns a generator.

```python
def f():
  yield 1

g = f()
type(g)
# <type 'generator'>
```

Generators are in fact iterators.

```python
print(next(g))
# 1
print(next(g))
# StopIteration
```

Each time you call the function, you'll get a new, independent, iterator.

```python
def f():
  yield 1

g1 = f()
g2 = f()
print(next(g1))
# 1
print(next(g1))
# StopIteration
print(next(g2))
# 1
print(next(g2))
# StopIteration
```

One of the most important features of a generator is that it lazily yields
values. Between `next` calls, it suspends execution, but maintains its
internal state. The classic example is the infinite counter, which lazily
produces an infinite sequence of integers.

```python
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
```

This will never raise a `StopIteration`; it will continue to count forever.  Be
careful not to iterate it in a `for` loop without a `break` statement!

Let's examine the sequence of operations of this simple generator more closely.

```python
def counter():
    print('Starting counter')
    c = 0
    while True:
        yield c
        c += 1
        print('Incremented counter to', c)

count = counter()
y = next(count)
# Starting counter
print('Counted', y)
# Counted 0
y = next(count)
# Incremented counter to 1
print('Counted', y)
# Counted 1
```

Let's examine the flow:

1. `count = counter()`  initializes the generator, assigning to `count` an
iterator.  Notice it does not execute anything inside of counter.
2. `y = next(count)` iterates the iterator, executing the code in `counter` up
to the first time we yield.  It assigns the yielded value `0` to `y`.
3. `print 'Counted', y` prints the yielded value `0`.
4. `y = next(count)` executes the loop from the first `yield` to the second.  It
also assigns the yielded value `1` to `y`.
5. `print 'Counted', y` prints the yielded value `1`.

Sending
-------
This is a basic generator that you can use to iterate/etc. But `yield` also
has a special power; it can receive values from the outside the function and
assign them to variables inside. Let's make a basic consumer:

```python
def printer():
    print('Starting printer')
    while True:
        x = yield
        print('Printing', x)

p = printer()
y = next(p)
# Starting printer
print('Outside', y)
# Outside None
y = next(p)
# Printing None
print('Outside', y)
# Outside None
```

This creates a generator that doesn't yield anything.  Let's follow the flow.

1. `p = printer()` creates p, which does not do any execution.
2. `y = next(p)` executes `printer` up to the line `x = yield`, which
  waits for iteration.  Since we didn't specify anything to yield that's the
  equivalent of `yield None`, and `y` is assigned to `None`.
3. `print('Outside', y)` Since `y` is `None`, we print `Outside None`.
4. `y = next(p)` executes `printer` from the `yield`.  We assign the result of
  the `yield` expression to `x`.  This is also `None`, because we didn't `send`
  anything -- foreshadowing!  Since we are yet again not yielding anything,
  `None` is returned and assigned to `y`.
5. `print('Outside', y)` Since `y` is `None`, we print `Outside None`.

For `yield` to actually receive information, we need to use the `send` method
of the generator.  In the above example, we didn't send anything to `p`, because
we wanted to emphases that `printer` is just a normal generator, but that
`yield` actually returns a value that can be assigned to a variable.  Now let's
actually get to `send`:

```python
p = printer()
y = p.send(None)
# Starting printer
print('Outside', y)
# Outside None
y = p.send('a')
# Printing a
print('Outside', y)
# Outside None
p.send(2)
# Printing 2
```

Now we're sending things to the generator to be processed.  Let's follow the
flow.

1. `p = printer()` creates p, which does not do any execution.
2. `y = p.send(None)` starts the generators execution, exactly like `next(p)`
would.  In fact, you could replace this with `next(p)` and it would be the same.
You need to "prime" the generator in this way; if you try to send a non-`None`
value to a just-started generator, it will throw an error.
3. `print('Outside', y)` prints the value of `y`, which is `None`, because `send`
has no return value.
4. `y = p.send('a')` sends the value `'a'` to the generator.  The line
`x = yield` means that it will assign to `x` the value that is sent, in this
case `'a'`, and so that is printed before we loop around to the `yield`
statement again.
5. `print('Outside', y)` shows that `y` is still `None`, and will always be so.
6. `p.send(2)` sends the value `2`, which is printed as expected.


Now how do we tie these together?  Here's a very simple way:

```python
count = counter()
p = printer()
p.send(None)
for x in range(3)
    p.send(next(count))

# > Starting counter
# > Printing 0
# > Incremented counter to 1
# > Printing 1
# > Incremented counter to 2
# > Printing 2
```

We say that `count` is a producer (because it is yielding results to the
outside), and `p` is a consumer, because we are sending values to it. Of
course, we can have a generator that consumes a producer.

```python
def times2(gen):
    print('Starting times2')
    while True:
        x = next(gen)
        print('Multiplying %s by 2' % x)
        yield 2*x

count = counter()
t2 = times2(count)
next(t2)
# > Starting times2
# > Starting counter
# > Multiplying 0 by 2
# 0
next(t2)
# > Incremented counter to 1
# > Multiplying 1 by 2
# 2
```

The `while` statement above is actually just a cumbersome `for` loop. It
could be written as

```python
def times2(gen):
    for x in gen:
        yield 2*x
```

[tutorial1]:  https://www.jeffknupp.com/blog/2013/04/07/improve-your-python-yield-and-generators-explained/
[script]: /generators2.py
