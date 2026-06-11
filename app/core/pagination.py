from math import ceil


def total_pages(total: int, page_size: int) -> int:
    if total == 0:
        return 0
    return ceil(total / page_size)


def normalize_page_size(value: int, max_value: int) -> int:
    return min(value, max_value)
