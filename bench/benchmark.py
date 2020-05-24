import hszinc
import os
import timeit

from pyzinc import pyzinc


def get_abspath(relpath):
    return os.path.join(os.path.dirname(__file__), relpath)


def read_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# 16 cols, 287 rows
SMALL_FILENAME = get_abspath("small_example.zinc")

# 32 cols, 287 rows
MEDIUM_FILENAME = get_abspath("medium_example.zinc")


small_example = read_file(SMALL_FILENAME)
medium_example = read_file(MEDIUM_FILENAME)

print(f"parsing {SMALL_FILENAME} with pyzinc...")
pyzinc_total = timeit.timeit(
    lambda: pyzinc.parse(SMALL_FILENAME), number=10)
print(f"parsing with pyzinc took {pyzinc_total / 10} seconds, avg of 10")

print(f"parsing {SMALL_FILENAME} with hszinc...")
hszinc_total = timeit.timeit(lambda: hszinc.parse(small_example), number=5)
print(f"parsing with hszinc took {hszinc_total / 5} seconds, avg of 5")

print(f"parsing {MEDIUM_FILENAME} with pyzinc...")
pyzinc_total = timeit.timeit(
    lambda: pyzinc.parse(MEDIUM_FILENAME), number=10)
print(f"parsing with pyzinc took {pyzinc_total / 10} seconds, avg of 10")

print(f"parsing {MEDIUM_FILENAME} with hszinc...")
hszinc_total = timeit.timeit(lambda: hszinc.parse(medium_example), number=5)
print(f"parsing with hszinc took {hszinc_total / 5} seconds, avg of 5")
