# coding:utf-8
from server_stub import *
from server_function import *

"""
说明：
    本文件与server_application2.py都为服务器应用，仅在服务器名上有差别
    服务端应用创建存根实例后，即可调用reigster_service()方法注册服务，然后再通过run_server()方法启动服务
    服务端应用启动后，即可被客户端发现
依赖文件：
    服务端存根在server_stub.py中，
    此外，获取命令行参数的方法、服务端能提供的服务以及服务名与服务的映射都封装在了serer_function.py中
运行说明：
    必须提供自身监听的端口号才能运行，输入格式如下：
        python server_application1.py -p [port] (-l [ip]) 
    其中，ip格式支持ipv4和ipv6
    如需更多说明，可输入：
        python server_application1.py -h
"""

if __name__ == '__main__':
    # 处理命令行参数
    ip, port = get_args(sys.argv[1:])
    port = int(port)
    server_name = 'server1'
    # 创建服务端
    server = ServerStub(ip, port, server_name)
    # 服务端注册服务（服务器提供的服务与server_dict在sever_function.py中定义，）
    server.register_service(service_dict)
    # 启动服务端
    server.run_server()
    asyncio.run(server.run_server())
