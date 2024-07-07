# coding:utf-8
import ipaddress
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
        # 创建socket，连接到注册中心
        if ipaddress.ip_address(self.center_ip).version == 4:
            client_to_register_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            client_to_register_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        # 设置超时
        client_to_register_socket.settimeout(10)
        client_to_register_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 允许重用端口
        client_to_register_socket.connect((self.center_ip, self.center_port))
        # 定义消息格式并序列化
        request_data = {
            'type': 'find',
            'method_name': method_name
        }
        request_data = pickle.dumps(request_data)
        reqs_len = len(request_data)
        request_data = reqs_len.to_bytes(2, 'big', signed=False) + request_data
        # 发送请求
        client_to_register_socket.sendall(request_data)
        # 接收响应
        # 读取长度，按量取走缓冲区数据  # todo 并发安全
        resp_len = client_to_register_socket.recv(2)
        resp_len = int.from_bytes(resp_len, 'big', signed=False)
        response_data = b''
        while resp_len != 0:
            if resp_len >= 1024:
                response_data += client_to_register_socket.recv(1024)
                resp_len -= 1024
            else:
                response_data += client_to_register_socket.recv(resp_len)
                resp_len = 0
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
        print(service_addr)  # todo 调试用
        # 创建连接到服务端的套接字
        if ipaddress.ip_address(service_addr[1]).version == 4:
            client_to_service_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            client_to_service_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        # 设置超时
        client_to_service_socket.settimeout(10)
        client_to_service_socket.connect(service_addr)
        # 定义消息格式并序列化
        request_data = {
            'method_name': method_name,
            'params': params
        }
        request_data = pickle.dumps(request_data)
        reqs_len = len(request_data)
        request_data = reqs_len.to_bytes(2, 'big', signed=False) + request_data
        client_to_service_socket.sendall(request_data)
        # 接收响应
        # 读取长度，按量取走缓冲区数据  # todo 并发安全
        resp_len = client_to_service_socket.recv(2)
        resp_len = int.from_bytes(resp_len, 'big', signed=False)
        response_data = b''
        while resp_len != 0:
            if resp_len >= 1024:
                response_data += client_to_service_socket.recv(1024)
                resp_len -= 1024
            else:
                response_data += client_to_service_socket.recv(resp_len)
                resp_len = 0
        response_data = pickle.loads(response_data)
        if response_data is None:
            print("error")
            exit(-1)
        client_to_service_socket.close()
        return response_data['result']

    def close(self):  #todo
        pass

    # 用于动态调用函数
    def __getattr__(self, method_name):
        """
        试图访问不存在的属性时，会调用该函数
        :param method_name: 试图调用的方法名称
        :return: 一个方法
        """
        def call_method(*params):
            """
            即将被__getattr__返回的方法，以元组形式接收可变数量的参数
            :param params:
            :return:
            """
            return self.call_service(method_name, params)
        return call_method

