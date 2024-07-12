# coding:utf-8
import getopt

"""
说明：
    本文件为客户端应用提供基础的功能函数
"""


def get_args(argv):
    """
    处理命令行参数
    :param argv: sys.argv[1:]
    :return: ip地址和端口号
    """
    try:
        # 获取命令行参数，指定ip和端口选项必须提供参数
        opts, args = getopt.getopt(argv, 'hi:p:')
    except getopt.GetoptError as err:
        print("错误！ip和端口必须提供参数")
        exit(-1)
    ip = ''
    port = ''
    # 处理命令行参数
    for opt, arg in opts:
        if opt == '-h':
            print('用法：')
            print('    python [name].py -options [arg]')
            print('参数说明：')
            print('     -h       : 显示帮助信息')
            print('     -i ip    : 注册中心的ip地址，可为IPv4或IPv6，不得为空，如需运行文件，必须提供该参数')
            print('     -p port  : 注册中心的端口，不得为空，如需运行文件，必须提供该参数')
            print('其中，[name].py如不在当前目录下，需指定相对路径或绝对路径')
            print('示例：')
            print('    >python client_application1.py -i 192.168.1.21 -p 8080')
            print('    >python client_application2.py -h')
            exit(0)
        elif opt == '-i':  # ip
            ip = arg
        elif opt == '-p':  # port
            port = arg
        else:
            print('错误: 无法识别或不完整的命令行')
            print('用法：')
            print('    python [name].py -options [arg]')
            print('参数说明：')
            print('     -h       : 显示帮助信息')
            print('     -i ip    : 注册中心的ip地址，可为IPv4或IPv6，不得为空，如需运行文件，必须提供该参数')
            print('     -p port  : 注册中心的端口，不得为空，如需运行文件，必须提供该参数')
            print('其中，[name].py如不在当前目录下，需指定相对路径或绝对路径')
            print('示例：')
            print('    >python client/client_application1.py -i 192.168.1.21 -p 8080')
            print('    >python client/client_application2.py -h')
            exit(-1)

    # 处理提供参数不完整的情况
    if ip == '' or port == '':
        print('错误：ip和端口必须提供参数')
        exit(-1)

    return ip, port