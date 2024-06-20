# coding:utf-8
from socket import *
import threading
import pickle

# todo password
"""
说明：本文件为注册中心的文件
规定发送的消息都具有2 bytes，大端存储的头部，用于存储消息长度
规定server发送给注册中心的消息的格式为：
request_data{
    'type': String  # 'register' or 'unregister'      
    'server_name': String  # 服务端名称
    'service_name': String  # 服务名称
    'service_addr': (String, int)  # (ip, port)
}
返回的消息格式为：
response_data{
    'status': Boolean
}
规定client发送给注册中心的消息的格式为：
request_data{
    'type': String  # 'find'
    'method_name': String
}
返回的消息格式为：
response_data{
    'service_addr': (String, int)  # (ip, port) 也可能返回None(失败)
}
"""
# 已注册的服务器的名称与地址的映射
server_addr_dict = {}
# 提供的服务与服务器的映射
service_server_dict = {}


def register_service(server_name, service_name, service_addr):
    server_addr_dict[server_name] = service_addr
    if service_name in service_server_dict:
        service_server_dict[service_name].append(server_name)
    else:
        service_server_dict[service_name] = [server_name]
    return True


def find_service(service_name):
    if service_name not in service_server_dict:
        service_addr = None
    else:
        server_names = service_server_dict[service_name]
        service_addr = server_addr_dict[server_names[0]]   # todo 负载均衡
    return service_addr


def handle_request(acceptSocket):
    try:
        request_data = acceptSocket.recv(1024)
        requ_len = int.from_bytes(request_data[:2], 'big', signed=False)
        request_data = pickle.loads(request_data)
        if request_data['type'] == 'register':
            server_name = request_data['server_name']
            service_name = request_data['service_name']
            service_addr = request_data['service_addr']
            response_data = {'status': register_service(server_name, service_name, service_addr)}
        elif request_data['type'] == 'find':
            service_name = request_data['method_name']
            service_addr = find_service(service_name)
            response_data = {'service_addr': service_addr}
        response_data = pickle.dumps(response_data)
        resp_len = len(response_data)
        response_data = resp_len.to_bytes(2, 'big', signed=False) + response_data
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
    # centerSocket.setblocking(0)
    # 绑定端口并开启监听
    centerSocket.bind((centerName, centerPort))
    centerSocket.listen(5)
    print("注册中心已启动")
    while True:
        # 等待接收客户端连接
        acceptSocket, addr = centerSocket.accept()   # 接收rpc服务端与客户端连接
        acceptSocket.settimeout(10)  # todo
        threading.Thread(target=handle_request, args=(acceptSocket,)).start()





