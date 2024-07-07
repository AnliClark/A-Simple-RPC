# coding:utf-8
import time
from socket import *
import threading
import pickle

# todo password
"""
说明：本文件为注册中心的文件
规定发送的消息都具有2 bytes的，大端存储的头部，用于存储消息长度
规定server发送给注册中心的消息的格式为：
request_data{
    'type': String  # 'register' or 'unregister'      
    'server_name': String  # 服务端名称
    'service_name': String  # 服务名称
}
或是type为heartbeat:
request_data{
    'type': String  # 'register' or 'unregister'      
    'server_name': String  # 服务端名称
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

class RegisterCenter:
    def __init__(self):
        # 已注册的服务器的地址与名称的映射
        self.addr_server_dict = {}
        # 提供的服务与服务器地址列表的映射（一对多）
        self.service_addr_dict = {}
        # 服务器地址与心跳的元组映射
        self.hb_dict = {}
        # 负载与服务器地址的元组列表
        self.load_list = []
        # 互斥锁，保证并发安全
        self.lock = threading.RLock()

    def register_service(self, server_name, service_name, service_addr):
        # 获取锁
        self.lock.acquire()
        self.addr_server_dict[service_addr] = server_name
        if service_name in self.service_addr_dict:
            self.service_addr_dict[service_name].append(service_addr)
        else:
            self.service_addr_dict[service_name] = [service_addr]
        self.hb_dict[service_addr] = time.time()
        self.load_list.append((0, service_addr))
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
            for _, addr in self.load_list.sort:
                if addr in service_addrs:
                    service_addr = addr
                    # 更新负载
                    self.load_list[0] = (self.load_list[0][0] + 1, service_addr)
                    break
        # 释放锁
        self.lock.release()
        return service_addr

    def heartbeat_check(self):
        """
        心跳机制，每隔5s，检查是否有服务器已经70s未有心跳
        :return:
        """
        while True:
            time.sleep(5)
            with self.lock:
                for server_addr, heartbeat_time in self.hb_dict:
                    if time.time() - heartbeat_time > 70:
                        print(f"Server {server_addr} removed due to timeout")
                        # 将映射全部删除
                        del self.addr_server_dict[server_addr]
                        del self.hb_dict[server_addr]
                        for service_name, service_addr_list in self.service_addr_dict.items():
                            if server_addr in service_addr_list:
                                service_addr_list.remove(server_addr)
                                if len(service_addr_list) == 0:
                                    del self.service_addr_dict[service_name]
                        for load, addr in self.load_list:
                            if addr == server_addr:
                                self.load_list.remove((load, server_addr))
                                break

    def load_fresh(self):
        """
        用于定时清空负载记录，防止记录的负载数量过大
        :return:
        """
        while True:
            self.lock.acquire()
            for load in self.load_list:
                load[0] = 0
            self.lock.release()
            time.sleep(240)

    def handle_request(self, acceptSocket, addr):
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
            request_data = pickle.loads(request_data)
            if request_data['type'] == 'register':
                server_name = request_data['server_name']
                service_name = request_data['service_name']
                service_addr = addr
                response_data = {'status': self.register_service(server_name, service_name, service_addr)}
            if request_data['type'] == 'heartbeat':
                with self.lock:
                    if addr in self.hb_dict:
                        self.hb_dict[addr] = time.time()
                        print(f"Heartbeat received from {addr}")
                        response_data = {'status': True}
                    # 处理服务器端已经失效，但是服务器端仍不知道，并继续发送心跳的事件
                    else:
                        response_data = {'status': False}

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
            print(e)
        finally:
            acceptSocket.close()

    def run(self):
        """
        启动注册中心
        :return:
        """
        # 创建注册中心套接字
        centerName = '192.168.1.20'  # 127.0.0.1 or 192.168.1.20 todo
        centerPort = 12000
        centerSocket = socket(AF_INET, SOCK_STREAM)
        centerSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # 设置端口重用，以便服务能迅速重启
        # 绑定端口并开启监听
        centerSocket.bind((centerName, centerPort))
        centerSocket.listen(5)
        print("注册中心已启动")
        # 启动心跳检测
        threading.Thread(target=self.heartbeat_check).start()
        # 启动负载均衡
        threading.Thread(target=self.load_fresh).start()
        # 接收客户端连接
        while True:
            # 等待接收客户端连接
            acceptSocket, addr = centerSocket.accept()  # 接收rpc服务端与客户端连接
            acceptSocket.settimeout(10)  # todo
            threading.Thread(target=self.handle_request, args=(acceptSocket, addr,)).start()


if __name__ == '__main__':
    register_center = RegisterCenter()
    register_center.run()





