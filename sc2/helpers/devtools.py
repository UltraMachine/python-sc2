from time import perf_counter_ns
from contextlib import contextmanager


@contextmanager
def time_this(label):
    start = perf_counter_ns()
    try:
        yield
    finally:
        end = perf_counter_ns()
        print(f"TIME {label}: {(end-start)/1000000000} sec")


# Use like this
if __name__ == "__main__":
    loops = 10 ** 6

    with time_this("square star"):
        for n in range(loops):
            x = n * n

    with time_this("square stars"):
        for n in range(loops):
            x = n ** 2

    with time_this("square pow"):
        for n in range(loops):
            x = pow(n, 2)

    from math import pow as mpow
    with time_this("square math pow"):
        for n in range(loops):
            x = mpow(n, 2)


# returns:
# TIME square star: 0.1963639 sec
# TIME square stars: 0.6601347 sec
# TIME square pow: 0.9462023 sec
# TIME square math pow: 0.4652565 sec
