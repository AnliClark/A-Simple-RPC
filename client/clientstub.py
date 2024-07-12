# coding:utf-8
import ipaddress
import pickle
import socket
import sys, getopt
import time

"""
说明：
    本文件为客户端存根，封装了ClientStub类，通过实例化该类，即可通过实例实现以本地形式调用远程服务
    客户端实例化时仅需提供注册中心ip与端口号即可
消息格式定义:
    均有2字节的头部，以大端形式存储消息长度
    client to register:
        request_data = {
            'type': String # 'find'
            'method_name': String  # 请求的方法名称
        }
        response_data = {
           'service_addr': (ip,port) or None  # 服务地址或None（失败）
        }
    client to server:
        request_data = {
            'method_name': String
            'params': ()
        }
        response_data ={
            'status': Bool  # 服务调用是否成功
            'result': Any
        }
"""


class ClientStub:
    """
    ClientStub有两个方法：
        find_service(method_name)：与注册中心连接，获取服务地址
        call_service(method_name, params)：调用find_service，获取服务端地址，与服务端连接，并获取服务
    这两个方法并不会被显式调用，客户端应用在调用远程服务时，会自动进入到本类的__getattr__方法中，并调用call_service得到方法
    """
    def __init__(self, center_ip, center_port):
        # 注册中心的地址
        self.center_ip = center_ip
        self.center_port = center_port
        # 异常的标志位，标识是否已有过异常，对于小的异常，可以根据标识位决定是否要重试
        self.has_error = False

    def find_service(self, method_name):
        """
        发现服务
        从注册中心获取能提供指定方法的服务器的地址
        :param method_name: 请求的方法名称
        :return:服务地址(ip,port)或None（失败）
        """
        # 创建socket，连接到注册中心
        if ipaddress.ip_address(self.center_ip).version == 4:  # ipv4
            client_to_register_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:   # ipv6
            client_to_register_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        # 设置超时时间，防止注册中心挂死
        client_to_register_socket.settimeout(10)
        client_to_register_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # 允许重用端口
        try:
            client_to_register_socket.connect((self.center_ip, self.center_port))

            # 封装消息
            # 定义消息格式并序列化
            request_data = {
                'type': 'find',
                'method_name': method_name
            }
            request_data = pickle.dumps(request_data)  # 使用pickle序列化
            # 获取消息的长度来封装头部
            reqs_len = len(request_data)
            # 将长度转为字节流，以大端方式存储，并将长度作为头部，加在消息之前
            request_data = reqs_len.to_bytes(2, 'big', signed=False) + request_data

            # 发送请求
            client_to_register_socket.sendall(request_data)

            # 接收响应
            # 读取长度，按量取走缓冲区数据
            resp_len = client_to_register_socket.recv(2)
            resp_len = int.from_bytes(resp_len, 'big', signed=False)
            response_data = b''
            # 按照长度，从缓存区取走数据
            while resp_len != 0:
                if resp_len >= 1024:
                    response_data += client_to_register_socket.recv(1024)
                    resp_len -= 1024
                else:
                    response_data += client_to_register_socket.recv(resp_len)
                    resp_len = 0
            response_data = pickle.loads(response_data)  # 反序列化
            self.has_error = False  # 正常运行至最后

        except Exception as e:
            print(f"连接注册中心失败：{e}")
            client_to_register_socket.close()
            if not self.has_error:  # 如果没有过异常，则等待5s后重试
                self.has_error = True
                time.sleep(5)
                return self.find_service(method_name)
            else:  # 如果已经有过异常，则直接返回None
                self.has_error = False  # 重置标志位
                return None
        finally:
            client_to_register_socket.close()  # 关闭连接

        if response_data['service_addr'] is None:
            print("没有找到指定服务")
        return response_data['service_addr']

    def call_service(self, method_name, params):
        """
        用于调用远程服务
        :param method_name: 请求的方法名称
        :param params: 方法参数（元组形式）
        :return: 调用结果
        """
        # 如果已经连接了服务器，尝试使用
        # 从注册中心获取指定服务地址
        service_addr = self.find_service(method_name)
        if service_addr is None:  # 没有找到服务
            return None
        print(service_addr)  # 用于测试负载均衡

        # 创建连接到服务端的套接字
        if ipaddress.ip_address(service_addr[1]).version == 4:  # ipv4
            client_to_service_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:  # ipv6
            client_to_service_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        # 设置超时
        client_to_service_socket.settimeout(10)

        try:
            client_to_service_socket.connect(service_addr)  # 连接服务器

            # 封装消息
            # 定义消息格式并序列化
            request_data = {
                'method_name': method_name,
                'params': params
            }
            request_data = pickle.dumps(request_data)
            # 获取消息的长度来封装头部
            reqs_len = len(request_data)
            # 将长度转为字节流，以大端方式存储，并将长度作为头部，加在消息之前
            request_data = reqs_len.to_bytes(2, 'big', signed=False) + request_data

            client_to_service_socket.sendall(request_data)  # 发送

            # 接收响应
            # 读取长度，按量取走缓冲区数据
            resp_len = client_to_service_socket.recv(2)
            resp_len = int.from_bytes(resp_len, 'big', signed=False)
            response_data = b''
            # 按照长度，从缓存区取走数据
            while resp_len != 0:
                if resp_len >= 1024:
                    response_data += client_to_service_socket.recv(1024)
                    resp_len -= 1024
                else:
                    response_data += client_to_service_socket.recv(resp_len)
                    resp_len = 0
            response_data = pickle.loads(response_data)  # 反序列化

            if response_data is None:
                raise Exception("error: 服务端返回空")

            # 服务调用失败（一般是由于注册中心还没有更新心跳，等待5s后重新向注册中心申请新的服务器）
            if response_data['status'] is False:
                if not self.has_error:  # 如果没有过异常，则等待5s，在异常处理中重试
                    time.sleep(5)
                raise Exception("error: 服务调用失败")

            self.has_error = False  # 正常运行至最后

        except Exception as e:
            print(e)
            client_to_service_socket.close()
            if not self.has_error:  # 如果没有过异常，则等待5s后重试
                self.has_error = True
                return self.call_service(method_name, params)
            else:  # 如果已经有过异常，则直接返回None
                self.has_error = False  # 重置标志位
                return None
        finally:
            client_to_service_socket.close()
        return response_data['result']

    def __getattr__(self, method_name):
        """
        用于动态调用函数
        :param method_name: 试图调用的方法名称
        :return:
        """
        def call_method(*params):
            """
            :param params:
            :return:
            """
            return self.call_service(method_name, params)  # 调用远程服务
        return call_method

