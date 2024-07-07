# coding:utf-8

# 以下为服务端提供的函数
def my_add(x, y):
    return x + y


def my_sub(x, y):
    return x - y


def my_mul(x, y):
    return x * y


def my_div(x, y):
    return x / y


def my_pow(x, y):
    return x ** y


def my_abs(x):
    if x < 0:
        return -x
    return x


def my_sqrt(x):
    return x ** 0.5


def to_upper(s):
    return s.upper()


def to_lower(s):
    return s.lower()


def my_cat(s1, s2):
    return s1 + s2


def my_split(s, sep):
    return s.split(sep)


service_dict = {'my_add': my_add,
                'my_sub': my_sub,
                'my_mul': my_mul,
                'my_div': my_div,
                'my_pow': my_pow,
                'my_abs': my_abs,
                'my_sqrt': my_sqrt,
                'my_upper': to_upper,
                'my_lower': to_lower,
                'my_cat': my_cat,
                'my_split': my_split
                }
