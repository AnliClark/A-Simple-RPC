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


class ServerStub:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.services = {}


    def register_service():


    def run_server(self):