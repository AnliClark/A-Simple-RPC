# coding:utf-8
import sys, getopt
def get_args(argv):
    """
    处理命令行参数
    :param argv: sys.argv[1:]
    :return: ip地址和端口号
    """
    try:
        opts, args = getopt.getopt(argv, 'hlp:')
    except getopt.GetoptError as err:
        print("错误！必须提供端口参数")
        exit(-1)
    ip = '0.0.0.0'
    for opt, arg in opts:
        if opt == '-h':
            print('参数说明：')
            print('-l ip[optional]  : 服务端监听的ip地址，可为IPv4或IPv6，可以为空，默认为0.0.0.0')
            print('-p port          : 服务端监听的端口号，不得为空')
            exit(0)
        elif opt == '-l':
            if arg is None:
                ip = '0.0.0.0'
            else:
                ip = arg
        elif opt == '-p':
            port = arg
        else:
            print('invalid option')
    return ip, port


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
