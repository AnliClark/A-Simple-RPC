# coding:utf-8
import ipaddress
import socket
import pickle
import sys
import threading
import time

"""
说明：
    本文件为服务器存根，封装了ServerStub类，通过实例化该类，注册服务并启动，即可被发现
消息格式定义：
    均有2字节的头部，以大端形式存储消息长度
    
    client to server:
        request_data = {
            'method_name': String
            'params': ()
        }
        response_data ={
            'status': Bool  # 服务调用是否成功
            'result': Any
        }
        
    server to register:
        register:
            request_data{
                'type': String  # 'register'    
                'server_name': String  # 服务端名称
                'port': int  # 服务端监听端口
                'service_name': String  # 服务名称
            }
        heartbeat:
            request_data{
                'type': String    # 'heartbeat'
                'port': int  # 服务端监听端口
            }
        
        response_data{
            'status': Boolean
        }
"""


class ServerStub:
    """
    ServerStub有4个方法：
        register_service(service_dict): 注册服务
        handle_request(accept_socket): 处理客户端请求
        send_heartbeat(): 发送心跳
        run_server(): 运行服务
    服务端应用可通过调用register_service注册服务，并调用run_server运行服务
    之后服务端存根会自动发送心跳包并处理客户端请求
    """
    def __init__(self, ip, port, server_name):
        # 自己的地址与监听的端口号
        self.ip = ip
        self.port = port
        # 注册中心的地址
        self.center_ip = '192.168.1.20'
        self.center_port = 12000
        self.server_name = server_name  # 服务器的名字
        # 服务名称与服务函数的映射
        self.services = {}
        # 互斥锁（保证并发安全，主要用于保护self.services与输出信息）
        self.lock = threading.RLock()
        # 专门用于输出错误信息的锁(防止错误本身就是由self.lock引起的，同时保证输出不乱序)
        self.err_lock = threading.RLock()
        # 异常的标志位，标识是否已有过异常，对于小的异常，可以根据标识位决定是否要重试
        self.has_error = False

    def register_service(self, service_dict):
        """
        注册服务
        :param service_dict: 服务名与服务的字典
        :return:
        """
        for service_name, service in service_dict.items():
            # 创建套接字
            if ipaddress.ip_address(self.center_ip).version == 4:
                server_to_register_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            else:
                server_to_register_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            server_to_register_socket.settimeout(10)
            try:
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
                request_data = pickle.dumps(request_data)  # 序列化
                # 获取消息的长度来封装头部
                reqs_len = len(request_data)
                # 将长度转为字节流，以大端方式存储，并将长度作为头部，加在消息之前
                request_data = reqs_len.to_bytes(2, 'big', signed=False) + request_data

                # 发送请求
                server_to_register_socket.sendall(request_data)

                # 接收响应
                # 读取长度，按量取走缓冲区数据
                resp_len = server_to_register_socket.recv(2)
                resp_len = int.from_bytes(resp_len, 'big', signed=False)
                response_data = b''
                # 按照长度，从缓存区取走数据
                while resp_len != 0:
                    if resp_len >= 1024:
                        response_data += server_to_register_socket.recv(1024)
                        resp_len -= 1024
                    else:
                        response_data += server_to_register_socket.recv(resp_len)
                        resp_len = 0
                response_data = pickle.loads(response_data)   # 反序列化
                self.lock.acquire()
                if not response_data['status']:
                    raise Exception(f"服务{service_name}注册失败")
                if response_data is None:
                    raise Exception(f"服务{service_name}注册失败")
                print(f"服务{service_name}注册成功")
                self.lock.release()
                self.has_error = False  # 重置异常标志位
            except Exception as e:
                self.err_lock.acquire()
                print(e)
                self.err_lock.release()
                server_to_register_socket.close()
                if not self.has_error:  # 如果没有过异常，则重试
                    self.has_error = True
                    return self.register_service(service_dict)
                else:  # 如果已经有过异常，则直接返回None
                    self.has_error = False  # 重置标志位
                    return None
            finally:
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
            # 按照长度，从缓存区取走数据
            while requ_len != 0:
                if requ_len >= 1024:
                    request_data += accept_socket.recv(1024)
                    requ_len -= 1024
                else:
                    request_data += accept_socket.recv(requ_len)
                    requ_len = 0
            request_data = pickle.loads(request_data)  # 反序列化
            # 异常的请求消息
            if request_data is None:
                raise Exception(f"请求数据为空")
            # 封装消息
            # 调用的服务不在列表中
            if request_data['method_name'] not in self.services:
                response_data = {
                    'status': False,
                    'result': None
                }
            else:
                service_name = request_data['method_name']
                response_data = {
                    'status': True,
                    'result': self.services[service_name](*request_data['params'])
                }
            response_data = pickle.dumps(response_data)
            # 获取消息的长度来封装头部
            resp_len = len(response_data)
            # 将长度转为字节流，以大端方式存储，并将长度作为头部，加在消息之前
            response_data = resp_len.to_bytes(2, 'big', signed=False) + response_data
            # 发送给客户端
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
                # 创建套接字
                if ipaddress.ip_address(self.center_ip).version == 4:
                    heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                else:
                    heartbeat_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                heartbeat_socket.settimeout(10)
                heartbeat_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 设置端口重用
                heartbeat_socket.connect((self.center_ip, self.center_port))

                # 封装请求消息
                request_data = {"type": "heartbeat", "port": self.port}
                request_data = pickle.dumps(request_data)  # 序列化
                # 获取消息的长度来封装头部
                reqs_len = len(request_data)
                # 将长度转为字节流，以大端方式存储，并将长度作为头部，加在消息之前
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
                response_data = pickle.loads(response_data)  # 反序列化
                # 心跳响应失败，在注册中心端已经失效，需重新注册
                if not response_data['status']:
                    raise Exception(f"心跳检测失败，重新注册中")
                elif response_data is None:
                    raise Exception(f"注册中心返回空，重发心跳包")
                else:
                    self.lock.acquire()
                    print(f"心跳检测成功")
                    self.lock.release()

                # 刷新缓存行，便于测试
                self.lock.acquire()
                sys.stdout.flush()
                self.lock.release()

                self.err_lock.acquire()
                sys.stderr.flush()
                self.err_lock.release()

                self.lock.acquire()
                print('debug: 缓存行已清空')
                self.lock.release()

                time.sleep(30)  # 30s重传一次
            except Exception as e:
                self.err_lock.acquire()
                print(e)
                self.err_lock.release()
                if e == "注册中心返回空，重发心跳包":
                    pass
                elif e == "心跳检测失败，重新注册中":  # 该情况为注册中心已把服务器移除，故需重新注册
                    self.register_service(self.services)
                else:
                    time.sleep(5)  # 等待5秒，再次重传
            finally:
                heartbeat_socket.close()

    def run_server(self):
        """
        运行服务
        :return:
        """
        # 创建服务端socket并监听，接收客户端请求
        if ipaddress.ip_address(self.ip).version == 4:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 允许端口复用
        server_socket.bind((self.ip, self.port))
        server_socket.listen(15)
        print(f"服务器{self.server_name}开始运行")
        # 启动心跳
        hb_thead = threading.Thread(target=self.send_heartbeat)
        hb_thead.demon = True   # 设为守护子线程，主线程停止，则关闭心跳
        hb_thead.start()
        # 接收请求
        while True:
            accept_socket, addr = server_socket.accept()
            handle_thread = threading.Thread(target=self.handle_request, args=(accept_socket,))
            handle_thread.daemon = True  # 设为守护子线程，主线程停止，则关闭心跳
            handle_thread.start()
