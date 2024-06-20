# coding:utf-8
import pickle
import socket
import sys, getopt

"""
定义服务器与客户端之间的消息格式:
client to server:
request_data = {
    method_name: String
    params: ()
}
response_data ={
    result: Any
}
"""


def get_args(argv):
    """
    处理命令行参数
    :param argv: sys.argv[1:]
    :return: ip地址和端口号
    """
    try:
        opts, args = getopt.getopt(argv, 'hi:p:')
    except getopt.GetoptError as err:
        print("错误！必须提供端口参数")
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


class ClientStub:
    def __init__(self, center_ip, center_port):
        self.center_ip = center_ip
        self.center_port = center_port

    def find_service(self, method_name):
        """
        从注册中心获取指定服务地址
        :param service_name: 请求的服务名称
        :return:服务地址(ip,port)或None（失败）
        """
        # 创建socket，连接到注册中心 todo ipv4 or ipv6
        client_to_register_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_to_register_socket.settimeout(10)
        client_to_register_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 允许重用端口
        client_to_register_socket.connect((self.center_ip, self.center_port))
        # 定义消息格式并序列化
        request_data = {
            'type': 'find',
            'method_name': method_name
        }
        request_data = pickle.dumps(request_data)  # todo 粘包需要解决吗
        # 发送请求
        client_to_register_socket.sendall(request_data)
        # 接收响应
        response_data = client_to_register_socket.recv(1024)
        response_data = pickle.loads(response_data)
        client_to_register_socket.close()
        if request_data is None:
            print("没有找到指定服务")
        return response_data['service_addr']

    def call_service(self, method_name, params):
        """
        调用服务
        :param method_name: 请求的方法名称
        :param params: 元组形式
        :return: 调用结果
        """
        # 从注册中心获取指定服务地址
        service_addr = self.find_service(method_name)
        if service_addr is None:
            return None
        # 创建连接到服务端的套接字
        client_to_service_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # todo ipv4 or ipv6
        # 设置超时
        client_to_service_socket.settimeout(10)
        client_to_service_socket.connect(service_addr)
        # 定义消息格式并序列化
        request_data = {
            'method_name': method_name,
            'params': params
        }
        request_data = pickle.dumps(request_data)  # todo 粘包需要解决吗
        client_to_service_socket.sendall(request_data)
        # 接收响应
        response_data = client_to_service_socket.recv(1024)
        response_data = pickle.loads(response_data)
        if response_data is None:
            print("error")
            exit(-1)
        client_to_service_socket.close()
        return response_data['result']

    def close(self):  #todo
        pass
