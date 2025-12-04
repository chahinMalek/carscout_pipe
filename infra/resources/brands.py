import csv
from typing import Generator

from core.entities.brand import Brand


def read_brands(path: str) -> Generator[Brand, None, None]:
    brands = []
    file = open(path, 'r')
    try:
        reader = csv.DictReader(file)
        for row in reader:
            brands.append(Brand(**row))
        yield brands
    finally:
        file.close()
