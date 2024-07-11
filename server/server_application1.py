# coding:utf-8
from server_stub import *
from server_function import *

if __name__ == '__main__':
    # 处理命令行参数
    # ip, port = get_args(sys.argv[1:])  # todo
    # port = int(port)
    ip = '192.168.1.20'
    port = 8800
    server_name = 'server1'
    # 创建服务端
    server = ServerStub(ip, port, server_name)
    # 服务端注册服务（服务器提供的服务在sever_function.py中定义）
    server.register_service(service_dict)
    # 启动服务端
    server.run_server()
