import re


def merge_dicts(a, b):
    return {**a, **b}


def del_dup_whitespace(string):
    return re.sub(' +', ' ', string)


def del_tabs_newlines(string):
    return re.sub(r'[\n\t]', ' ', string)


def strip(string):
    return del_dup_whitespace(del_tabs_newlines(string.strip()))


def quote_value_array_values(match):
    s = match.group()
    qvalues = [f'"{value}"' for value in s.split(r", ")]
    return ", ".join(qvalues)


def java_to_json(s):
    s = re.sub(r"(?<==\[)[^{\[\]]+(?=\])", quote_value_array_values, s)
    s = re.sub(r'(?<={)([^"=]+)[=:](?!{|\[)([^,}]+)', r'"\1":"\2"', s)
    s = re.sub(r'(?<=, )([^"=]+)[=:](?!{|\[)([^,}]+)', r'"\1":"\2"', s)
    s = re.sub(r'(?<={)([^"=]+)=(?!")', r'"\1":', s)
    s = re.sub(r'(?<=, )([^"=]+)=(?!")', r'"\1":', s)
    return s
