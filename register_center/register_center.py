# coding:utf-8
import sys
import time
from socket import *
import threading
import pickle

"""
说明：
    本文件为注册中心的文件，可以登记服务器的服务，并为客户端提供服务的地址，
    同时还会通过心跳机制保障服务端的存活，且会保证负载均衡
消息格式定义：
    均有2字节的头部，以大端形式存储消息长度
    
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
        
    client to register:
        request_data = {
            'type': String # 'find'
            'method_name': String  # 请求的方法名称
        }
        response_data = {
           'service_addr': (ip,port) or None  # 服务地址或None（失败）
        }
"""


class RegisterCenter:
    """
    RegisterCenter类，用于实现注册中心的功能，实例化后，只需调用run()方法即可启动注册中心
    RegisterCenter有6个方法：
        register_service: 注册服务
        find_service: 查找服务
        handle_request: 处理请求
        heartbeat_check: 心跳检测
        load_fresh: 负载均衡
        run: 启动注册中心

    """
    def __init__(self):
        # 已注册的服务器的地址与名称的映射
        self.addr_server_dict = {}
        # 提供的服务与服务器地址列表的映射（一对多）
        self.service_addr_dict = {}
        # 服务器地址与心跳的元组映射
        self.hb_dict = {}
        # 负载与服务器地址的二元列表的列表  [[load, addr],]
        self.load_list = []
        # 互斥锁，保证并发安全
        self.lock = threading.RLock()
        # 专门用于输出错误信息的锁(防止错误本身就是由self.lock引起的，同时保证输出不乱序)
        self.err_lock = threading.RLock()

    def register_service(self, server_name, service_name, service_addr):
        """
        注册服务
        :param server_name: 服务器名称
        :param service_name: 服务名称
        :param service_addr: 服务器地址(ip,addr)
        :return:
        """
        # 获取锁
        self.lock.acquire()
        # 如果注册中心中没有记录过服务器，更新负载列表
        if service_addr not in self.service_addr_dict:
            self.load_list.append([0, service_addr])
        # 添加服务器地址与名称的映射
        self.addr_server_dict[service_addr] = server_name
        # 添加服务名称与服务器地址的映射
        if service_name in self.service_addr_dict:
            self.service_addr_dict[service_name].append(service_addr)
        else:
            self.service_addr_dict[service_name] = [service_addr]
        # 添加心跳
        self.hb_dict[service_addr] = time.time()
        # 释放锁
        self.lock.release()
        return True

    def find_service(self, service_name):
        """
        根据服务名称查找服务地址，并实现负载均衡
        :param service_name: 服务的名称
        :return: (ip, port) 或 None(失败)
        """
        # 获取锁
        self.lock.acquire()
        service_addr = None
        if service_name in self.service_addr_dict:
            # 根据名字获取地址列表
            service_addrs = self.service_addr_dict[service_name]
            # 选择可以提供服务的服务器中负载最小的
            self.load_list.sort(key=lambda x: x[0])
            i = 0
            for load, addr in self.load_list:
                if addr in service_addrs:
                    service_addr = addr
                    # 更新负载
                    self.load_list[i] = [self.load_list[i][0] + 1, service_addr]
                    break
                i += 1
        # 释放锁
        self.lock.release()
        return service_addr

    def handle_request(self, acceptSocket, addr):
        """
        处理各类请求
        :param acceptSocket:
        :param addr:
        :return:
        """

        try:
            # 接收消息
            # 读取头部长度，按量取走缓冲区数据
            requ_len = acceptSocket.recv(2)
            requ_len = int.from_bytes(requ_len, 'big', signed=False)
            request_data = b''
            while requ_len != 0:
                if requ_len >= 1024:
                    request_data += acceptSocket.recv(1024)
                    requ_len -= 1024
                else:
                    request_data += acceptSocket.recv(requ_len)
                    requ_len = 0
            request_data = pickle.loads(request_data)  # 序列化

            # 注册服务类型
            if request_data['type'] == 'register':
                server_name = request_data['server_name']
                server_port = request_data['port']
                service_name = request_data['service_name']
                service_addr = (addr[0], server_port)
                response_data = {'status': self.register_service(server_name, service_name, service_addr)}
            # 心跳包类型
            elif request_data['type'] == 'heartbeat':
                self.lock.acquire()
                if (addr[0], request_data['port']) in self.hb_dict:
                    self.hb_dict[(addr[0], request_data['port'])] = time.time()
                    response_data = {'status': True}
                # 处理服务器端已经失效，但是服务器端仍不知道，并继续发送心跳的事件
                else:
                    response_data = {'status': False}
                self.lock.release()
            # 发现服务类型
            elif request_data['type'] == 'find':
                service_name = request_data['method_name']
                service_addr = self.find_service(service_name)
                response_data = {'service_addr': service_addr}

            # 处理要返回的消息
            response_data = pickle.dumps(response_data)
            # 读取消息长度，并附加到消息头部
            resp_len = len(response_data)
            response_data = resp_len.to_bytes(2, 'big', signed=False) + response_data

            acceptSocket.sendall(response_data)
        except Exception as e:
            self.err_lock.acquire()
            print(e)
            self.err_lock.release()
        finally:
            acceptSocket.close()

    def heartbeat_check(self):
        """
        心跳机制，每隔5s，检查是否有服务器已经40s未有心跳
        :return:
        """
        while True:
            time.sleep(5)
            self.lock.acquire()
            for server_addr in list(self.hb_dict.keys()):
                heartbeat_time = self.hb_dict[server_addr]
                if time.time() - heartbeat_time > 40:
                    print(f"服务器 {server_addr} 超时，已移除")
                    # 将映射全部删除
                    del self.addr_server_dict[server_addr]
                    del self.hb_dict[server_addr]
                    for service_name, service_addr_list in list(self.service_addr_dict.items()):
                        if server_addr in service_addr_list:
                            service_addr_list.remove(server_addr)
                            if len(service_addr_list) == 0:
                                del self.service_addr_dict[service_name]
                    for load, addr in self.load_list:
                        if addr == server_addr:
                            self.load_list.remove([load, addr])
                            break
            self.lock.release()

    def load_fresh(self):
        """
        用于定时清空负载记录：
            防止新加入的服务器在短时内收到大量负载
            防止记录的负载数量过大
        :return:
        """
        while True:
            time.sleep(60)
            self.lock.acquire()
            for load in self.load_list:
                load[0] = 0
            self.lock.release()

            # 刷新缓存区，便于测试
            self.lock.acquire()
            sys.stdout.flush()
            self.lock.release()
            self.err_lock.acquire()
            sys.stderr.flush()
            self.err_lock.release()


    def run(self):
        """
        启动注册中心
        :return:
        """
        # 创建注册中心套接字
        centerName = '192.168.1.20'
        centerPort = 12000
        centerSocket = socket(AF_INET, SOCK_STREAM)
        centerSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # 设置端口重用，以便服务能迅速重启
        # 绑定端口并开启监听
        centerSocket.bind((centerName, centerPort))
        centerSocket.listen(5)
        print("注册中心已启动")
        # 启动心跳检测
        hb_thread = threading.Thread(target=self.heartbeat_check)
        hb_thread.dameon = True
        hb_thread.start()
        # 启动负载均衡
        load_thread = threading.Thread(target=self.load_fresh)
        load_thread.dameon = True
        load_thread.start()
        # 接收客户端连接
        while True:
            # 等待接收客户端连接
            acceptSocket, addr = centerSocket.accept()  # 接收rpc服务端与客户端连接
            acceptSocket.settimeout(10)
            threading.Thread(target=self.handle_request, args=(acceptSocket, addr,)).start()


if __name__ == '__main__':
    register_center = RegisterCenter()
    # 启动注册中心
    register_center.run()





