from server_stub import *
from server_function import *

"""
说明：
    本文件与server_application1.py都为服务器应用，仅在服务器名上有差别
    详细可见sever_application1.py
"""

if __name__ == '__main__':
    # 处理命令行参数
    ip, port = get_args(sys.argv[1:])
    port = int(port)
    server_name = 'server2'
    # 创建服务端
    server = ServerStub(ip, port, server_name)
    # 服务端注册服务（服务器提供的服务与server_dict在sever_function.py中定义，）
    server.register_service(service_dict)
    # 启动服务端
    server.run_server()