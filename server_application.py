from server_stub import *
from server_function import *

if __name__ == '__main__':
    # 处理命令行参数
    ip, port = get_args(sys.argv[1:])
    # 创建服务端
    server = ServerStub(ip, port)
    # 服务端注册函数
    server.register_function(add)