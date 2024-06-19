# coding:utf-8
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
        server_to_register_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #todo iptype
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
        # 发送请求
        server_to_register_socket.sendall(request_data)
        # 接收响应
        response_data = server_to_register_socket.recv(1024)
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
            request_data = accept_socket.recv(1024)
            request_data = pickle.loads(request_data)
            if request_data['method_name'] not in self.services:
                response_data = None
            else:
                response_data = request_data['method_name'](request_data['params'])
            response_data = pickle.loads(response_data)
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
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # todo
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 允许端口复用
        server_socket.bind((self.ip, self.port))
        server_socket.listen(15)
        server_socket.settimeout(10)
        print(f"服务器{self.server_name}开始运行")
        while True:
            accept_socket, addr = server_socket.accept()
            threading.Thread(target=self.handle_request, args=(accept_socket,)).start()

