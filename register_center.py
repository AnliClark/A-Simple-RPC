# coding:utf-8
from socket import *
import threading
import pickle

# todo password
"""
说明：本文件为注册中心的文件
规定server发送给注册中心的消息的格式为：
request_data{
    type: String  # 'register' or 'unregister'      
    server_name: String  # 服务端名称
    service_name: String  # 服务名称
    service_addr: (String, int)  # (ip, port)
}
返回的消息格式为：
response_data{
    status: Boolean
}
规定client发送给注册中心的消息的格式为：
request_data{
    type: String  # 'find'
    method_name: String
}
返回的消息格式为：
response_data{
    service_addr: (String, int)  # (ip, port) 也可能返回None(失败)
}
"""
# 已注册的服务器的名称与地址的映射
service_dict = {}
def rpc_init_server(port):
    """
    初始化服务端
    :param port: 端口号
    :return: 服务端状态，返回None则表示错误
    """


def register_service(service_name, service_addr):
    service_dict[service_name] = service_addr


def handle_request(acceptSocket):
    try:
        request_data = acceptSocket.recv(1024)
        request_data = pickle.loads(request_data)
        if request_data['type'] == 'register':
            service_name = request_data['service_name']
            service_addr = request_data['service_addr']
            response_data = {'status': register_service(service_name, service_addr)}
        else:
            pass # todo
        response_data = pickle.dumps(response_data)
        acceptSocket.sendall(response_data)
    except Exception as e:
        print(e)
    finally:
        acceptSocket.close()


if __name__ == '__main__':
    # 创建注册中心套接字
    centerName = '127.0.0.1'
    centerPort = 12000
    centerSocket = socket(AF_INET, SOCK_STREAM)
    centerSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # 设置端口重用，以便服务能迅速重启
    # 设置为非阻塞模式  # todo
    centerSocket.setblocking(0)
    # 绑定端口并开启监听
    centerSocket.bind((centerName, centerPort))
    centerSocket.listen(5)
    print("注册中心已启动")
    while True:
        # 等待接收客户端连接
        acceptSocket, addr = centerSocket.accept()   # 接收rpc服务端与客户端连接
        acceptSocket.settimeout(10)  # todo
        threading.Thread(target=handle_request, args=acceptSocket)





