from datetime import datetime

import numpy as np


def is_empty(value):
    if value is None:
        return True
    if isinstance(value, float) and np.isnan(value):
        return True
    return False


def check_date_format(date_str, format_str) -> bool:
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False
