import getopt


def get_args(argv):
    """
    处理命令行参数
    :param argv: sys.argv[1:]
    :return: ip地址和端口号
    """
    try:
        opts, args = getopt.getopt(argv, 'hi:p:')
    except getopt.GetoptError as err:
        print("错误！必须提供端口和ip参数")
        exit(-1)
    for opt, arg in opts:
        if opt == '-h':
            print('参数说明：')
            print('-i ip    : 客户端需要发送的服务端ip地址，可为IPv4或IPv6，可以为空，默认为0.0.0.0')
            print('-p port  : 客户端需要发送的服务端端口，不得为空')
            exit(0)
        elif opt == '-i':
            ip = arg
        elif opt == '-p':
            port = arg
        else:
            print('invalid option')
    return ip, port