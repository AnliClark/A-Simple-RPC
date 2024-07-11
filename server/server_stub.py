# coding:utf-8
import ipaddress
import socket
import pickle
import sys
import threading
import time


class ServerStub:
    def __init__(self, ip, port, server_name):
        self.ip = ip
        self.port = port
        self.center_ip = '192.168.1.20'  # 注册中心的地址  127.0.0.1 or 192.168.1.20 todo
        self.center_port = 12000
        self.server_name = server_name
        # 服务名称与服务函数的映射
        self.services = {}
        # 互斥锁
        self.lock = threading.RLock()
        # 专门用于输出错误信息的锁(防止错误本身就是由self.lock引起的，同时保证输出不乱序)
        self.err_lock = threading.RLock()

    def register_service(self, service_dict):
        """
        注册服务
        :param service_dict: 服务名与服务的键值对
        :return:
        """
        for service_name, service in service_dict.items():
            # 创建与注册中心的连接
            if ipaddress.ip_address(self.center_ip).version == 4:
                server_to_register_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            else:
                server_to_register_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            server_to_register_socket.settimeout(10)
            server_to_register_socket.connect((self.center_ip, self.center_port))
            # 映射到自身的存储中
            if service_name not in self.services:
                self.services[service_name] = service
            elif self.services[service_name] != service:
                self.services[service_name] = service
            # 定义消息格式并序列化
            request_data = {
                'type': 'register',
                'server_name': self.server_name,
                'port': self.port,
                'service_name': service_name,
            }
            request_data = pickle.dumps(request_data)
            reqs_len = len(request_data)
            request_data = reqs_len.to_bytes(2, 'big', signed=False) + request_data
            # 发送请求
            server_to_register_socket.sendall(request_data)
            # 接收响应
            # 读取长度，按量取走缓冲区数据
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
            self.lock.acquire()
            if not response_data['status']:
                print(f"服务{service_name}注册失败")
                exit(-1)    # todo
            print(f"服务{service_name}注册成功")
            self.lock.release()
            server_to_register_socket.close()

    def handle_request(self, accept_socket):
        """
        处理请求
        :param accept_socket:
        :return:
        """
        try:
            # 接收数据并反序列化
            # 读取头部长度，按量取走缓冲区数据
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
            self.err_lock.acquire()
            print(f"服务{self.server_name}处理请求失败: {e}")
            self.err_lock.release()
        finally:
            accept_socket.close()

    def send_heartbeat(self):
        """
        发送心跳，心跳发送失败则重新注册
        :return:
        """
        while True:
            try:
                heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                heartbeat_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 设置端口重用
                heartbeat_socket.connect((self.center_ip, self.center_port))

                # 封装请求消息
                request_data = {"type": "heartbeat"}
                request_data = pickle.dumps(request_data)
                reqs_len = len(request_data)
                request_data = reqs_len.to_bytes(2, 'big', signed=False) + request_data

                # 发送请求
                heartbeat_socket.sendall(request_data)

                # 接收响应
                # 读取长度，按量取走缓冲区数据
                resp_len = heartbeat_socket.recv(2)
                resp_len = int.from_bytes(resp_len, 'big', signed=False)
                response_data = b''
                while resp_len != 0:
                    if resp_len >= 1024:
                        response_data += heartbeat_socket.recv(1024)
                        resp_len -= 1024
                    else:
                        response_data += heartbeat_socket.recv(resp_len)
                        resp_len = 0
                response_data = pickle.loads(response_data)
                # 心跳响应失败，在注册中心端已经失效，需重新注册
                if not response_data['status']:
                    self.lock.acquire()
                    print(f"心跳检测失败，重新注册中")
                    self.lock.release()
                    self.register_service(self.services)
                else:
                    self.lock.acquire()
                    print(f"心跳检测成功")
                    self.lock.release()

                self.lock.acquire()
                sys.stdout.flush()
                self.lock.release()

                self.err_lock.acquire()
                sys.stderr.flush()
                self.err_lock.release()

                time.sleep(60)  # 60s重传一次
            except Exception as e:
                self.err_lock.acquire()
                print(f"心跳检测失败: {e}")
                self.err_lock.release()
                time.sleep(5)  # 等待5秒，再次重传
            finally:
                heartbeat_socket.close()

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
        # 启动心跳
        hb_thead = threading.Thread(target=self.send_heartbeat)
        hb_thead.demon = True
        hb_thead.start()
        # 接收请求
        while True:
            accept_socket, addr = server_socket.accept()
            threading.Thread(target=self.handle_request, args=(accept_socket,)).start()

