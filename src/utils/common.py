import numpy as np


def is_empty(value):
    if value is None:
        return True
    if isinstance(value, float) and np.isnan(value):
        return True
    return False
