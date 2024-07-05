# coding:utf-8
import ipaddress
import sys, getopt
import socket
import pickle
import threading






class ServerStub:
    def __init__(self, ip, port, server_name):
        self.ip = ip
        self.port = port
        self.center_ip = '127.0.0.1'  # 注册中心的地址
        self.center_port = 12000
        self.server_name = server_name
        self.services = {}


    def register_service(self, service_name, service):
        """
        注册服务
        :param service_name:
        :param service:
        :return:
        """
        # 映射到自身的存储中
        self.services[service_name] = service
        # 创建与注册中心的连接
        if ipaddress.ip_address(self.center_ip).version == 4:
            server_to_register_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            server_to_register_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        server_to_register_socket.settimeout(10)
        server_to_register_socket.connect((self.center_ip, self.center_port))
        # 定义消息格式并序列化
        request_data = {
            'type': 'register',
            'server_name': self.server_name,
            'service_name': service_name,
            'service_addr': (self.ip, self.port)
        }
        request_data = pickle.dumps(request_data)
        reqs_len = len(request_data)
        request_data = reqs_len.to_bytes(2, 'big', signed=False) + request_data
        # 发送请求
        server_to_register_socket.sendall(request_data)
        # 接收响应
        # 读取长度，按量取走缓冲区数据  # todo 并发安全
        resp_len = server_to_register_socket.recv(2)
        resp_len = int.from_bytes(resp_len, 'big', signed=False)
        response_data = b''
        while resp_len != 0:
            if resp_len >= 1024:
                response_data += server_to_register_socket.recv(1024)
                resp_len -= 1024
            else:
                response_data += server_to_register_socket.recv(resp_len)
                resp_len = 0
        response_data = pickle.loads(response_data)
        if not response_data['status']:
            print("服务注册失败")
            exit(-1)    # todo
        print("服务注册成功")


    def handle_request(self, accept_socket):
        """
        处理请求
        :param accept_socket:
        :return:
        """
        try:
            # 接收数据并反序列化
            # 读取头部长度，按量取走缓冲区数据  # todo 并发安全
            requ_len = accept_socket.recv(2)
            requ_len = int.from_bytes(requ_len, 'big', signed=False)
            request_data = b''
            while requ_len != 0:
                if requ_len >= 1024:
                    request_data += accept_socket.recv(1024)
                    requ_len -= 1024
                else:
                    request_data += accept_socket.recv(requ_len)
                    requ_len = 0
            request_data = pickle.loads(request_data)
            if request_data['method_name'] not in self.services:
                response_data = None
            else:
                service_name = request_data['method_name']
                response_data = {
                    'result': self.services[service_name](*request_data['params'])
                }
            response_data = pickle.dumps(response_data)
            resp_len = len(response_data)
            response_data = resp_len.to_bytes(2, 'big', signed=False) + response_data
            accept_socket.sendall(response_data)
        except Exception as e:
            print(e)
        finally:
            accept_socket.close()



    def run_server(self):
        """
        运行服务
        :return:
        """
        # 创建服务端socket并监听
        if ipaddress.ip_address(self.ip).version == 4:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 允许端口复用
        server_socket.bind((self.ip, self.port))
        server_socket.listen(15)
        # server_socket.settimeout(10)
        print(f"服务器{self.server_name}开始运行")
        while True:
            accept_socket, addr = server_socket.accept()
            threading.Thread(target=self.handle_request, args=(accept_socket,)).start()

